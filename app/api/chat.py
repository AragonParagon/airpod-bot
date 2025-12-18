from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.service.chat import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

async def get_chat_service() -> ChatService:
    return ChatService()
    

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with the agent
    """
    return chat_service.chat(request)


@router.post("/stream")
async def stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with the agent
    """
    return StreamingResponse(
        chat_service.stream(request),
        media_type="text/event-stream"
    )
    

