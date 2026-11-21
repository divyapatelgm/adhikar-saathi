from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Response
from pydantic import BaseModel
from ..services.speech_interface import speech_manager

router = APIRouter(prefix="/api", tags=["Speech & Voice"])

class TTSRequest(BaseModel):
    text: str
    language: str = "kn"

class TTSResponse(BaseModel):
    text: str
    language: str
    provider: str
    fallback_used: bool
    message: str

class STTResponse(BaseModel):
    text: str
    language: str
    provider: str
    fallback_used: bool
    message: Optional[str] = None

@router.get("/speech/providers")
def get_speech_providers():
    """Returns the operational status and supported languages for each speech engine."""
    return speech_manager.get_status()

@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: Optional[UploadFile] = File(None),
    language: str = Form("kn"),
):
    """
    Transcribes audio bytes to text using Gnani STT with automatic fallback to Web Speech.
    Accepts multipart audio file.
    """
    audio_bytes = b""
    if audio:
        audio_bytes = await audio.read()
    
    result = await speech_manager.transcribe(audio_bytes=audio_bytes, language=language)
    return STTResponse(**result)

@router.post("/tts")
async def text_to_speech(payload: TTSRequest):
    """
    Synthesizes text into spoken regional language audio using Gnani or Web Speech fallback instructions.
    """
    result = await speech_manager.synthesize(text=payload.text, language=payload.language)
    if result.get("audio"):
        return Response(content=result["audio"], media_type="audio/mpeg")
    return TTSResponse(
        text=payload.text,
        language=result["language"],
        provider=result["provider"],
        fallback_used=result["fallback_used"],
        message=result.get("message", "Use Web Speech API for playback."),
    )
