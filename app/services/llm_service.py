from langchain_groq import ChatGroq
from app.config import settings
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from app.prompts.system_prompts import PROMPT_FOR_CHAT_TITLE, PROMPT_FOR_CHAT_RESPONSE
from typing import Optional



class LLMService:
    
    def __init__(self):
        self.llmAPI = ChatGroq(
            model=settings.MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0
        )

    async def generate_chat_title(
        self,
        first_message: str
    ) -> str:
        messages = [
            SystemMessage(content=PROMPT_FOR_CHAT_TITLE),
            HumanMessage(content=first_message)
        ]
        response = self.llmAPI.invoke(messages)
        return response.content

    async def generate_response(
        self,
        userMessage: str,
        previous_messages: list | None = None,
        chat_summary: dict | None = None,
    ) -> str:
        """
        Generate AI response.

        TODO:
        Replace this with Gemini/OpenAI.
        """
        messages = [
            SystemMessage(content=PROMPT_FOR_CHAT_RESPONSE),
            HumanMessage(content=userMessage)
        ]
        response = self.llmAPI.invoke(messages)
        return response.content


    async def generate_summary(
        self,
        recent_messages: list,
    ) -> dict:
        """
        Summarize conversation.

        TODO:
        Replace this with Gemini/OpenAI.
        """

        return {
            "summary": " this is demo summary",
            "key_points": [],
            "last_updated": None
        }