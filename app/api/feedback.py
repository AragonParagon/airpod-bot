from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.feedback import FeedbackRequest, FeedbackResponse
from app.service.feedback import FeedbackService

feedback_router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])

async def get_feedback_service() -> FeedbackService:
    return FeedbackService()
    

@feedback_router.post("/", response_model=FeedbackResponse)
async def feedback(
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    API to accept and send feedback appreciation email to the user and admin
    """
    return feedback_service.send_feedback(request)


    

