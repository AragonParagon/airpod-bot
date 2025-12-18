from pydantic import BaseModel
from typing import List

class FeedbackRequest(BaseModel):
    message: str
    email: str
    rating: int

class FeedbackResponse(BaseModel):
    message: str
    rating: int