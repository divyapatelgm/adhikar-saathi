import hashlib
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentReader:
    """Reads PDF and text documents from local filesystem and computes content hashes."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    @classmethod
    def compute_hash(cls, file_path: Path) -> str:
        """Computes SHA-256 hash of file bytes."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def read_document(cls, file_path: Path) -> Tuple[str, str]:
        """
        Reads document text and returns (text, sha256_hash).
        Raises ValueError if file doesn't exist, is unsupported, or is empty.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {cls.SUPPORTED_EXTENSIONS}")

        content_hash = cls.compute_hash(file_path)

        if ext == ".pdf":
            text = cls._read_pdf(file_path)
        else:
            text = cls._read_text(file_path)

        clean_text = text.strip()
        if not clean_text:
            raise ValueError(f"Extracted document text is empty: {file_path}")

        return clean_text, content_hash

    @classmethod
    def _read_pdf(cls, file_path: Path) -> str:
        """Extracts text from PDF using pdfplumber with fallback to pypdf."""
        extracted_pages = []

        # Try pdfplumber first
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append(page_text)
            if extracted_pages:
                return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.warning("pdfplumber reading failed on %s: %s; falling back to pypdf", file_path, e)

        # Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.error("pypdf reading failed on %s: %s", file_path, e)
            raise ValueError(f"Could not extract text from PDF {file_path}: {e}")

    @classmethod
    def _read_text(cls, file_path: Path) -> str:
        """Reads plain text / markdown file with encoding fallback."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
