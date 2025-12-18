from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

class ChatResponse(BaseModel):
    message: str
    citations: List[str]
    conversation_id: str    