import resend

from app.core.settings import settings
from app.models.feedback import FeedbackResponse, FeedbackRequest

class FeedbackService:
    def __init__(self):
        pass

    def send_feedback(self, feedback: FeedbackRequest):
        """
        Send feedback appreciation email to the user and admin
        """
        resend.api_key = settings.RESEND_API_KEY

        params: resend.Emails.SendParams = {
            "from": "Airpods Assistant <onboarding@resend.dev>",
            "to": [settings.RESEND_FEEDBACK_EMAIL],
            "subject": "Thank you for your feedback!",
            "html": f"<h3>Thank you for your feedback! I really value your feedback and it helps me improve the product quality.</h3><p></p><p><b>Rating:</b> {feedback.rating}</p><p><b>Feedback:</b> {feedback.message}</p>",
        }

        email = resend.Emails.send(params)
        return FeedbackResponse(
            message="Feedback sent successfully", 
            rating=feedback.rating
        )

    