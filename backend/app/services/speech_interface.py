from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

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
        # Web Speech operates natively in the browser JavaScript runtime.
        return "Web Speech STT operates directly in client browser."

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        # Web Speech synthesis operates natively in browser window.speechSynthesis.
        return b""

class GnaniProvider(SpeechProvider):
    """
    Gnani API Speech Provider.
    Full implementation scheduled for Phase 7 once official Gnani docs are placed in /docs/gnani_notes.md.
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "gnani"

    @property
    def supported_languages(self) -> List[str]:
        # Pending confirmation in Phase 7 docs
        return ["en", "hi", "kn"]

    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        raise NotImplementedError("Gnani STT will be enabled in Phase 7 upon doc upload.")

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        raise NotImplementedError("Gnani TTS will be enabled in Phase 7 upon doc upload.")

class SpeechManager:
    """Coordinates speech services, respecting language preferences and fallback mechanisms."""

    def __init__(self):
        self.web_speech = WebSpeechProvider()
        self.gnani = GnaniProvider()
        # Default preference ordering per language
        self.language_provider_order: Dict[str, List[str]] = {
            "kn": ["gnani", "web_speech"],
            "hi": ["gnani", "web_speech"],
            "en": ["gnani", "web_speech"],
        }

    def get_supported_languages(self) -> Dict[str, List[str]]:
        return {
            "web_speech": self.web_speech.supported_languages,
            "gnani": self.gnani.supported_languages,
        }
