from aiohttp.web_middlewares import middleware
from app.core.settings import settings
from app.agent.tools import tavily_web_search_tool

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

class AirpodAgent:
    """
    Agent that helps users with any queries related to airpods
    """
    def __init__(self):
        self.model = settings.LLM_PROVIDER_MODEL
        self.system_prompt = settings.AGENT_SYSTEM_PROMPT
        self.web_search_enabled = settings.LLM_PROVIDER_API_KEY
        pass

    def get_model(self):
        """
        Retruns an instantiated chat model
        """
        return ChatGoogleGenerativeAI(
            model=self.model,
            api_key=settings.LLM_PROVIDER_API_KEY,
            include_thoughts=True,
            tools=[{"google_search": {}}],
            thinking_level="low"

        )

    def get_openai_model(self):
        """
        Retruns an instantiated chat model
        """
        return ChatOpenAI(
            model=self.model,
            api_key=settings.LLM_PROVIDER_API_KEY,
        )

    def get_agent(self):
        """
        Returns the agent object that will be invoked to generate responses
        """
        return create_agent(
            model=self.get_model(),
            system_prompt=self.system_prompt,
            tools = [{"google_search": {}}],
            middleware = [

                # Limits the model to 2 tool calls per user query
                ToolCallLimitMiddleware(
                    tool_name="tavily_web_search_tool",
                    thread_limit=10,
                    run_limit=10
                )
            ]
        )

