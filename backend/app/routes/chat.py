from fastapi import APIRouter
from ..models.api import ChatRequest, ChatResponse
from ..services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def post_chat_message(request: ChatRequest):
    return await chat_service.handle_chat(request)
