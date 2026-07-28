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
        user_context = self._format_chat_summary(chat_summary)
        chat_history = self._build_chat_history(previous_messages)

        messages = [
            SystemMessage(content=PROMPT_FOR_CHAT_RESPONSE),
            *(
                [SystemMessage(content=user_context)]
                if user_context
                else []
            ),
            *chat_history,
            HumanMessage(content=userMessage),
        ]

        response = self.llmAPI.invoke(messages)
        return response.content

    @staticmethod
    def _build_chat_history(
        previous_messages: list | None,
    ) -> list:
        if not previous_messages:
            return []

        chat_history = []

        for message in previous_messages:
            role = message.get("role")
            content = message.get("message", "")

            if role == "user":
                chat_history.append(HumanMessage(content=content))
            elif role == "assistant":
                chat_history.append(AIMessage(content=content))

        return chat_history

    @staticmethod
    def _format_chat_summary(chat_summary: dict | None) -> str | None:
        if not chat_summary:
            return None

        summary = str(chat_summary.get("summary", "")).strip()
        key_points = chat_summary.get("key_points") or []

        if not summary and not key_points:
            return None

        parts = [
            "Use this summary of earlier conversation for context:",
        ]

        if summary:
            parts.append(summary)

        if key_points:
            parts.append("Key points:")
            parts.extend(f"- {point}" for point in key_points)

        return "\n".join(parts)


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