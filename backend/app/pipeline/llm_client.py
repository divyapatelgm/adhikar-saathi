import asyncio
import base64
import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import httpx

from ..config import settings

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    """Abstract interface for LLM extraction and conversational agents."""

    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates structured JSON string response from LLM."""
        pass

    @abstractmethod
    async def generate_vision_json(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        system_prompt: Optional[str] = None
    ) -> str:
        """Generates structured JSON from multimodal vision input."""
        pass

class GeminiLLMClient(LLMClient):
    """
    Gemini API client supporting structured JSON generation
    with exponential backoff on 429 rate limit errors.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL or "gemini-2.5-flash"
        self.max_retries = 4
        self.base_delay = 1.0  # seconds

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Invokes Gemini API with exponential backoff retry on 429 / 503 errors."""
        if not self.api_key or self.api_key in ("your_key_here", "your_gemini_api_key_here"):
            raise ValueError("GEMINI_API_KEY is not configured or is a placeholder.")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow the instructions and output valid JSON."}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            }
        }

        delay = self.base_delay
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    response = await client.post(endpoint, json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise ValueError("Gemini API returned no candidates in response.")
                        raw_text = candidates[0]["content"]["parts"][0]["text"]
                        return self._clean_json_text(raw_text)

                    elif response.status_code in (429, 503):
                        logger.warning(
                            "Gemini API returned %d (attempt %d/%d). Retrying in %.1fs...",
                            response.status_code, attempt, self.max_retries, delay
                        )
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        await asyncio.sleep(delay)
                        delay *= 2.0  # Exponential backoff

                    else:
                        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

            except httpx.RequestError as e:
                logger.warning("Network request error (attempt %d/%d): %s", attempt, self.max_retries, e)
                last_error = str(e)
                await asyncio.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"Exceeded max retries for Gemini API. Last error: {last_error}")

    async def generate_vision_json(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        system_prompt: Optional[str] = None
    ) -> str:
        """Invokes Gemini Multimodal Vision API with image data + prompt and exponential backoff."""
        if not self.api_key or self.api_key in ("your_key_here", "your_gemini_api_key_here"):
            raise ValueError("GEMINI_API_KEY is not configured or is a placeholder.")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        parts = [
            {"inline_data": {"mime_type": mime_type, "data": b64_data}},
            {"text": prompt}
        ]

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow the instructions and output valid JSON."}]})

        contents.append({"role": "user", "parts": parts})

        payload = {
            "contents": contents,
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            }
        }

        delay = self.base_delay
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(endpoint, json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise ValueError("Gemini API returned no candidates in response.")
                        raw_text = candidates[0]["content"]["parts"][0]["text"]
                        return self._clean_json_text(raw_text)

                    elif response.status_code in (429, 503):
                        logger.warning(
                            "Gemini Vision API returned %d (attempt %d/%d). Retrying in %.1fs...",
                            response.status_code, attempt, self.max_retries, delay
                        )
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        await asyncio.sleep(delay)
                        delay *= 2.0

                    else:
                        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

            except httpx.RequestError as e:
                logger.warning("Network request error (attempt %d/%d): %s", attempt, self.max_retries, e)
                last_error = str(e)
                await asyncio.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"Exceeded max retries for Gemini Vision API. Last error: {last_error}")

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """Strips markdown code fence ```json ... ``` if present."""
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
        return clean.strip()

class MockLLMClient(LLMClient):
    """
    Deterministic offline Mock LLM client for tests, dry-runs, and local environments
    without requiring external Gemini network calls.
    """

    def __init__(self, predefined_response: Optional[str] = None):
        self.predefined_response = predefined_response

    async def generate_vision_json(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        system_prompt: Optional[str] = None
    ) -> str:
        if self.predefined_response:
            return self.predefined_response
        return await self.generate_json(prompt, system_prompt)

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.predefined_response:
            return self.predefined_response

        # Check if this is a Government Notice Scanner request
        if "Notice Scanner" in prompt or "notice_scanner" in (system_prompt or ""):
            # Check requested language
            lang = "en"
            if "Language: kn" in prompt:
                lang = "kn"
            elif "Language: hi" in prompt:
                lang = "hi"

            # Check if deadline is missing in the document content (ignore instructions)
            content_part = prompt
            if "Notice Image / Text:" in prompt:
                content_part = prompt.split("Notice Image / Text:", 1)[1]
                if "Language:" in content_part:
                    content_part = content_part.split("Language:", 1)[0]

            has_no_deadline = (
                "no deadline" in content_part.lower()
                or "without deadline" in content_part.lower()
                or "missing deadline" in content_part.lower()
            )
            deadline_val = "No deadline mentioned in the document" if has_no_deadline else "December 31, 2026"

            if lang == "kn":
                return json.dumps({
                    "issuing_authority": "ಆಹಾರ, ನಾಗರಿಕ ಸರಬರಾಜು ಮತ್ತು ಗ್ರಾಹಕರ ವ್ಯವಹಾರಗಳ ಇಲಾಖೆ, ಕರ್ನಾಟಕ ಸರ್ಕಾರ",
                    "purpose": "ಪಡಿತರ ಚೀಟಿ ರದ್ದಾಗುವುದನ್ನು ತಡೆಯಲು ಕಡ್ಡಾಯ ಬಯೋಮೆಟ್ರಿಕ್ ಇ-ಕೆವೈಸಿ (e-KYC) ನವೀಕರಣ",
                    "summary": "ಎಲ್ಲಾ ಆದ್ಯತಾ (BPL/PHH) ಮತ್ತು ಅಂತ್ಯೋದಯ ಪಡಿತರ ಚೀಟಿದಾರರು ಮಾಸಿಕ ಉಚಿತ ಆಹಾರ ಧಾನ್ಯ ಪಡೆಯುವುದನ್ನು ಮುಂದುವರಿಸಲು ನಿಗದಿತ ದಿನಾಂಕದೊಳಗೆ e-KYC ಪೂರ್ಣಗೊಳಿಸಬೇಕು.",
                    "citizen_obligations": [
                        "ಪಡಿತರ ಚೀಟಿಯಲ್ಲಿರುವ ಪ್ರತಿಯೊಬ್ಬ ಕುಟುಂಬದ ಸದಸ್ಯರು ನ್ಯಾಯಬೆಲೆ ಅಂಗಡಿಗೆ ತೆರಳಿ ಬಯೋಮೆಟ್ರಿಕ್ ನೀಡಬೇಕು",
                        "ಮೂಲ ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಪಡಿತರ ಚೀಟಿಯನ್ನು ಕಡ್ಡಾಯವಾಗಿ ಹಾಜರುಪಡಿಸಬೇಕು"
                    ],
                    "deadline": deadline_val,
                    "urgency": "High",
                    "next_steps": [
                        "1. ನಿಮ್ಮ ನಿಯೋಜಿತ ನ್ಯಾಯಬೆಲೆ ಅಂಗಡಿ (ಪಡಿತರ ಅಂಗಡಿ) ಅಥವಾ ಗ್ರಾಮ ಒನ್ ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ",
                        "2. ಬೆರಳಚ್ಚು ಅಥವಾ ಕಣ್ಣಿನ ಸ್ಕ್ಯಾನ್ ಮೂಲಕ e-KYC ಮಾಡಿಸಿ",
                        "3. ಉಚಿತ ಇ-ಕೆವೈಸಿ ಪೂರ್ಣಗೊಂಡ ನಂತರ ಮುದ್ರಿತ ರಸೀದಿಯನ್ನು ಪಡೆದುಕೊಳ್ಳಿ"
                    ],
                    "official_portal": "https://ahara.kar.nic.in",
                    "disclaimer": "ಮಾಹಿತಿಗಾಗಿ ಮಾತ್ರ, ಕಾನೂನು ಸಲಹೆಯಲ್ಲ. ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಕಚೇರಿ ಅಥವಾ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.",
                    "language": "kn",
                    "confidence": 0.98
                })
            elif lang == "hi":
                return json.dumps({
                    "issuing_authority": "खाद्य, नागरिक आपूर्ति एवं उपभोक्ता मामले विभाग, कर्नाटक सरकार",
                    "purpose": "राशन कार्ड रद्द होने से बचाने के लिए अनिवार्य बायोमेट्रिक ई-केवाईसी (e-KYC) प्रमाणीकरण",
                    "summary": "सभी प्राथमिकता (BPL/PHH) और अंत्योदय राशन कार्ड धारकों को मासिक सब्सिडी वाले राशन का लाभ जारी रखने के लिए निर्धारित समयसीमा से पहले ई-केवाईसी पूरा करना आवश्यक है।",
                    "citizen_obligations": [
                        "राशन कार्ड में दर्ज प्रत्येक सदस्य को उचित मूल्य की दुकान पर जाकर बायोमेट्रिक सत्यापन कराना होगा",
                        "मूल आधार कार्ड एवं राशन कार्ड साथ ले जाना अनिवार्य है"
                    ],
                    "deadline": deadline_val,
                    "urgency": "High",
                    "next_steps": [
                        "1. अपनी उचित मूल्य दुकान (राशन दुकान) या ग्राम वन केंद्र पर जाएं",
                        "2. फिंगरप्रिंट या आइरिस स्कैन द्वारा ई-केवाईसी पूरा करें",
                        "3. प्रक्रिया पूर्ण होने के बाद पावती पर्ची अवश्य प्राप्त करें"
                    ],
                    "official_portal": "https://ahara.kar.nic.in",
                    "disclaimer": "केवल सूचना हेतु, विधिक सलाह नहीं। कृपया आधिकारिक कार्यालय अथवा पोर्टल से पुष्टि करें।",
                    "language": "hi",
                    "confidence": 0.98
                })
            else:
                return json.dumps({
                    "issuing_authority": "Department of Food, Civil Supplies and Consumer Affairs, Government of Karnataka",
                    "purpose": "Mandatory biometric e-KYC authentication for Priority and Antyodaya ration cardholders",
                    "summary": "All Priority (BPL/PHH) and Antyodaya (AAY) ration cardholders must complete biometric e-KYC authentication to avoid card suspension and ensure uninterrupted food grain distribution.",
                    "citizen_obligations": [
                        "Every family member listed on the ration card must visit the fair price shop for biometric verification",
                        "Bring original Aadhaar cards and the physical ration card"
                    ],
                    "deadline": deadline_val,
                    "urgency": "High",
                    "next_steps": [
                        "1. Visit your assigned Fair Price Shop (ration shop) or Grama One center",
                        "2. Provide biometric authentication (fingerprint or iris scan) for each family member",
                        "3. Collect the printed official confirmation receipt free of charge"
                    ],
                    "official_portal": "https://ahara.kar.nic.in",
                    "disclaimer": "Information only, not legal advice. Please verify at the official office/portal.",
                    "language": "en",
                    "confidence": 0.98
                })

        # Check if the prompt contains the synthetic sample dairy grant
        if "Synthetic Dairy Farmer Incentive Grant" in prompt or "SDFIG" in prompt:
            return json.dumps({
                "id": "synthetic-dairy-farmer-incentive-grant",
                "tier": "extracted",
                "status": "unverified",
                "confidence": 0.95,
                "is_placeholder": False,
                "names": {
                    "en": "Synthetic Dairy Farmer Incentive Grant",
                    "kn": "ಸಿಂಥೆಟಿಕ್ ಹೈನುಗಾರಿಕೆ ರೈತರ ಪ್ರೋತ್ಸಾಹ ಧನ",
                    "hi": "सिंथेटिक डेयरी किसान प्रोत्साहन अनुदान"
                },
                "level": "state",
                "state": "Karnataka",
                "department": "Department of Synthetic Welfare",
                "category": ["agriculture"],
                "target_groups": ["farmer"],
                "summary_en": "Financial support to synthetic smallholder dairy farmers to purchase organic cattle fodder.",
                "benefit": {
                    "type": "cash",
                    "description": "Cash incentive of ₹50,000 direct bank transfer annually.",
                    "amount_text": "₹50,000"
                },
                "eligibility": {
                    "criteria": [
                        {
                            "field": "occupation",
                            "op": "in",
                            "value": ["farmer", "agricultural labourer"],
                            "text_en": "Occupation must be farmer or agricultural labourer",
                            "source_quote": "Occupation must be farmer or agricultural labourer."
                        },
                        {
                            "field": "age",
                            "op": "between",
                            "value": [21, 65],
                            "text_en": "Age must be between 21 and 65 years",
                            "source_quote": "Age must be between 21 and 65 years."
                        },
                        {
                            "field": "annual_income",
                            "op": "lte",
                            "value": 250000.0,
                            "text_en": "Annual household income must not exceed ₹2,50,000",
                            "source_quote": "Annual household income must not exceed 250000 rupees."
                        },
                        {
                            "field": "land_acres",
                            "op": "between",
                            "value": [0.5, 5.0],
                            "text_en": "Land holding must be between 0.5 and 5.0 acres",
                            "source_quote": "Land holding must be between 0.5 and 5.0 acres."
                        }
                    ],
                    "exclusions": [
                        {
                            "field": "land_acres",
                            "op": "gte",
                            "value": 10.0,
                            "text_en": "Citizens owning more than 10 acres are ineligible",
                            "source_quote": "Citizens owning more than 10 acres of land or earning more than 300000 rupees are ineligible."
                        }
                    ],
                    "notes": "Extracted from synthetic sample notice"
                },
                "documents_required": [
                    "Synthetic Identity Card",
                    "Land RTC / Pahani document",
                    "Bank passbook copy"
                ],
                "how_to_apply": {
                    "steps": [
                        "Apply online via portal or Grama One center",
                        "Submit RTC and passbook copies"
                    ],
                    "mode": "both",
                    "portal_url": "https://example.gov.test/sdfig"
                },
                "deadline_text": "March 31, 2027",
                "official_url": "https://example.gov.test/sdfig",
                "source_name": "Department of Synthetic Welfare",
                "source_document": "sample_test_scheme.txt",
                "last_verified": "2026-11-01",
                "extracted_at": "2026-11-17T10:00:00Z",
                "reviewed_by": None
            })

        # Generic fallback extraction
        return json.dumps({
            "id": "extracted-generic-scheme",
            "tier": "extracted",
            "status": "unverified",
            "confidence": 0.8,
            "is_placeholder": False,
            "names": {"en": "Extracted Generic Welfare Scheme"},
            "level": "state",
            "state": "Karnataka",
            "department": "Welfare Department",
            "category": ["general"],
            "target_groups": ["citizen"],
            "summary_en": "Generic welfare scheme extracted from document.",
            "benefit": {"type": "service", "description": "General welfare service"},
            "eligibility": {"criteria": [], "exclusions": []},
            "documents_required": ["Aadhaar"],
            "how_to_apply": {"steps": ["Apply at Grama One"], "mode": "offline"},
            "official_url": "https://karnataka.gov.in",
            "source_name": "Gov of Karnataka",
            "source_document": None,
            "last_verified": "2026-11-01"
        })

def get_llm_client() -> LLMClient:
    """Returns GeminiLLMClient if a valid API key and model are configured, otherwise MockLLMClient."""
    key = settings.GEMINI_API_KEY
    model = settings.LLM_MODEL

    # Normalize placeholder model string if needed
    if not model or model.startswith("<") or ">" in model:
        model = "gemini-2.5-flash"

    is_dummy_key = not key or any(placeholder in key.lower() for placeholder in ("your_key", "your_gemini", "placeholder", "test_key"))
    if not is_dummy_key and not key.startswith("<"):
        return GeminiLLMClient(api_key=key, model=model)
    return MockLLMClient()
