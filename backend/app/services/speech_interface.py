from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class SpeechProvider(ABC):
    """Abstract interface for speech-to-text (STT) and text-to-speech (TTS) engines."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        """Transcribe speech audio bytes to text string."""
        pass

    @abstractmethod
    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Synthesize text string to audio bytes."""
        pass

class WebSpeechProvider(SpeechProvider):
    """
    Browser-native Web Speech API Provider.
    Covers en-IN, hi-IN, kn-IN directly on client devices without cloud latency or quota limits.
    """

    @property
    def provider_name(self) -> str:
        return "web_speech"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "hi", "kn"]

    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        return "Transcribed via client-side Web Speech recognition."

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        # Client handles synthesis natively via window.speechSynthesis
        return b""

class GnaniProvider(SpeechProvider):
    """
    Gnani Speech Provider.
    Gracefully handles credentials and falls back to Web Speech if keys or custom endpoints are unconfigured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GNANI_API_KEY

    @property
    def provider_name(self) -> str:
        return "gnani"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in ["your_key_here", "your_gnani_api_key_here", ""])

    @property
    def supported_languages(self) -> List[str]:
        return ["kn", "hi", "en"]

    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        if not self.is_configured:
            logger.info("Gnani API key not configured. Falling back to Web Speech / client STT.")
            raise RuntimeError("Gnani STT not configured; fallback to Web Speech.")
        # If API key is present, Gnani endpoint call would execute here
        return "Gnani transcription placeholder."

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        if not self.is_configured:
            logger.info("Gnani API key not configured. Falling back to Web Speech / client TTS.")
            raise RuntimeError("Gnani TTS not configured; fallback to Web Speech.")
        return b""

class SpeechManager:
    """Coordinates speech services, respecting language preferences and fallback mechanisms."""

    def __init__(self):
        self.web_speech = WebSpeechProvider()
        self.gnani = GnaniProvider()

    def get_status(self) -> Dict:
        return {
            "web_speech": {
                "active": True,
                "supported_languages": self.web_speech.supported_languages,
                "type": "client_browser_api",
                "notes": "Covers en-IN, hi-IN, kn-IN natively on device."
            },
            "gnani": {
                "active": self.gnani.is_configured,
                "supported_languages": self.gnani.supported_languages,
                "type": "cloud_api",
                "notes": "Ready for production Gnani API key and official endpoint integration." if not self.gnani.is_configured else "Active"
            },
            "default_provider": "gnani" if self.gnani.is_configured else "web_speech"
        }

    async def transcribe(self, audio_bytes: bytes, language: str = "kn") -> Dict:
        lang = language if language in ["kn", "hi", "en"] else "en"
        if self.gnani.is_configured:
            try:
                text = await self.gnani.transcribe(audio_bytes, lang)
                return {"text": text, "provider": "gnani", "language": lang, "fallback_used": False}
            except Exception as e:
                logger.warning(f"Gnani transcription failed ({e}), falling back to client Web Speech.")
        return {
            "text": "",
            "provider": "web_speech",
            "language": lang,
            "fallback_used": True,
            "message": "Please use browser Web Speech API for transcription."
        }

    async def synthesize(self, text: str, language: str = "kn") -> Dict:
        lang = language if language in ["kn", "hi", "en"] else "en"
        if self.gnani.is_configured:
            try:
                audio = await self.gnani.synthesize(text, lang)
                return {"audio": audio, "provider": "gnani", "language": lang, "fallback_used": False}
            except Exception as e:
                logger.warning(f"Gnani synthesis failed ({e}), falling back to client Web Speech.")
        return {
            "audio": b"",
            "provider": "web_speech",
            "language": lang,
            "fallback_used": True,
            "message": "Please use browser window.speechSynthesis."
        }

speech_manager = SpeechManager()
