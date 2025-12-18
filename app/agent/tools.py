from langchain_tavily import TavilySearch
from app.core.settings import settings


tavily_web_search_tool = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=settings.WEB_SEARCH_API_KEY
)

