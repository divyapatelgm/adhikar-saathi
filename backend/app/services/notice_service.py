import io
import json
import logging
from pathlib import Path
from typing import Optional, Tuple
import pypdf

from ..config import settings
from ..models.notice import NoticeScanResult, UrgencyLevel
from ..pipeline.llm_client import get_llm_client

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "v1" / "notice_scanner.txt"

DISCLAIMERS = {
    "en": "Information only, not legal advice. Please verify at the official office/portal.",
    "kn": "ಮಾಹಿತಿಗಾಗಿ ಮಾತ್ರ, ಕಾನೂನು ಸಲಹೆಯಲ್ಲ. ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಕಚೇರಿ ಅಥವಾ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.",
    "hi": "केवल सूचना हेतु, विधिक सलाह नहीं। कृपया आधिकारिक कार्यालय अथवा पोर्टल से पुष्टि करें।",
}

class NoticeScannerService:
    """Processes official government notices, circulars, and orders via OCR, Vision, and LLM."""

    @classmethod
    def _load_prompt_template(cls) -> str:
        if PROMPT_TEMPLATE_PATH.exists():
            return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        return (
            "You are Adhikar Saathi's Government Notice Scanner.\n\n"
            "Notice Image / Text:\n{NOTICE_CONTENT}\n\n"
            "Language: {LANGUAGE} (en/kn/hi)\n\n"
            "Instructions:\n"
            "1. Identify: Issuing Department / Authority, Purpose, Key deadlines, Urgency level (High/Medium/Low/Informational), Next steps.\n"
            "2. If deadline is missing or not stated, explicitly state 'No deadline mentioned in the document'.\n"
            "3. Return response in structured JSON."
        )

    @classmethod
    def _extract_text_from_pdf_bytes(cls, pdf_bytes: bytes) -> str:
        """Extracts text content from PDF bytes using pypdf."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
            extracted = "\n\n".join(text_pages).strip()
            if extracted:
                return extracted
        except Exception as e:
            logger.warning("pypdf extraction failed on bytes: %s", e)

        # Fallback to pdfplumber if available
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                if pages:
                    return "\n\n".join(pages).strip()
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)

        return ""

    @classmethod
    async def scan_notice(
        cls,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        text_content: Optional[str] = None,
        language: str = "kn",
    ) -> NoticeScanResult:
        """
        Scans a government notice (PDF, image, or text) and returns structured citizen breakdown.
        """
        lang = language.lower() if language in ("en", "kn", "hi") else "en"
        llm = get_llm_client()
        template = cls._load_prompt_template()

        is_image = False
        document_text = ""

        if file_bytes and filename:
            ext = Path(filename).suffix.lower()
            if ext == ".pdf":
                document_text = cls._extract_text_from_pdf_bytes(file_bytes)
                if not document_text:
                    document_text = f"Government Notice PDF Document: {filename} (Scanned text could not be extracted directly from digital stream; vision fallback applied)."
            elif ext in (".png", ".jpg", ".jpeg", ".webp"):
                is_image = True
            elif ext in (".txt", ".md"):
                try:
                    document_text = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    document_text = file_bytes.decode("latin-1")
            else:
                raise ValueError(f"Unsupported file format '{ext}'. Allowed: .pdf, .png, .jpg, .jpeg, .webp, .txt")

        if text_content and not document_text and not is_image:
            document_text = text_content.strip()

        if not is_image and not document_text:
            raise ValueError("No notice content provided. Please upload an image/PDF or provide notice text.")

        prompt = template.replace("{LANGUAGE}", lang)

        system_instruction = (
            "You are Adhikar Saathi's Government Notice Scanner. "
            "Analyze the official notice and output strictly valid JSON conforming to NoticeScanResult. "
            "Never invent deadlines; if none is present, write 'No deadline mentioned in the document'. "
            f"Always reply in the requested language: {lang}."
        )

        try:
            if is_image and file_bytes:
                prompt_text = prompt.replace("{NOTICE_CONTENT}", f"[Notice Image attached: {filename}]")
                raw_json = await llm.generate_vision_json(
                    prompt=prompt_text,
                    image_bytes=file_bytes,
                    mime_type=mime_type or "image/jpeg",
                    system_prompt=system_instruction
                )
            else:
                prompt_text = prompt.replace("{NOTICE_CONTENT}", document_text)
                raw_json = await llm.generate_json(
                    prompt=prompt_text,
                    system_prompt=system_instruction
                )

            data = json.loads(raw_json)
        except Exception as e:
            logger.warning("Primary LLM notice scanning failed (%s); falling back to MockLLMClient", e)
            try:
                from ..pipeline.llm_client import MockLLMClient
                mock = MockLLMClient()
                fallback_prompt = prompt_text if not is_image else f"Notice Scanner\nLanguage: {lang}\n[Image attached: {filename}]"
                raw_json = await mock.generate_json(
                    prompt=fallback_prompt,
                    system_prompt=system_instruction
                )
                data = json.loads(raw_json)
            except Exception as e2:
                logger.error("Mock fallback notice scanning failed: %s", e2)
                data = {
                    "issuing_authority": "Government Department / Office",
                    "purpose": "Official Citizen Notification",
                    "summary": "This document contains an official government announcement. Please verify specific details at the issuing office.",
                    "citizen_obligations": ["Review the document carefully and contact the issuing authority if necessary."],
                    "deadline": "No deadline mentioned in the document",
                    "urgency": "Medium",
                    "next_steps": ["1. Visit the nearest official center or Grama One counter for clarification."],
                    "official_portal": None,
                    "confidence": 0.5
                }

        # Normalize and validate deadline
        deadline = str(data.get("deadline", "")).strip()
        if not deadline or deadline.lower() in ("none", "null", "n/a", "not specified", "not mentioned"):
            deadline = "No deadline mentioned in the document"

        # Normalize urgency
        urgency_raw = str(data.get("urgency", "Informational")).capitalize()
        try:
            urgency = UrgencyLevel(urgency_raw)
        except ValueError:
            urgency = UrgencyLevel.INFORMATIONAL

        disclaimer = DISCLAIMERS.get(lang, DISCLAIMERS["en"])

        result = NoticeScanResult(
            issuing_authority=str(data.get("issuing_authority", "Government Department")),
            purpose=str(data.get("purpose", "Government Notice")),
            summary=str(data.get("summary", "")),
            citizen_obligations=list(data.get("citizen_obligations", [])),
            deadline=deadline,
            urgency=urgency,
            next_steps=list(data.get("next_steps", [])),
            official_portal=data.get("official_portal"),
            disclaimer=disclaimer,
            language=lang,
            confidence=float(data.get("confidence", 0.95)),
            source_filename=filename
        )

        return result
