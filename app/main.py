from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router
from app.api.feedback import feedback_router
from app.core.settings import settings
import os

app = FastAPI(title="Postcard App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(feedback_router)

os.environ["TAVILY_API_KEY"] = settings.WEB_SEARCH_API_KEY
os.environ["GOOGLE_API_KEY"] = settings.LLM_PROVIDER_API_KEY
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)