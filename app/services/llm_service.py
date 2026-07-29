import json
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from app.config import settings
from app.prompts.system_prompts import (
    PROMPT_FOR_CHAT_TITLE,
    PROMPT_FOR_CHAT_RESPONSE,
    PROMPT_FOR_CHAT_SUMMARY,
)


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
        messages = self._build_response_messages(
            userMessage,
            previous_messages,
            chat_summary,
        )
        response = self.llmAPI.invoke(messages)
        return response.content

    async def stream_response(
        self,
        userMessage: str,
        previous_messages: list | None = None,
        chat_summary: dict | None = None,
    ):
        messages = self._build_response_messages(
            userMessage,
            previous_messages,
            chat_summary,
        )

        async for chunk in self.llmAPI.astream(messages):
            content = chunk.content
            if not content:
                continue

            if isinstance(content, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            else:
                text = str(content)

            if text:
                yield text

    def _build_response_messages(
        self,
        userMessage: str,
        previous_messages: list | None = None,
        chat_summary: dict | None = None,
    ) -> list:
        user_context = self._format_chat_summary(chat_summary)
        chat_history = self._build_chat_history(previous_messages)

        return [
            SystemMessage(content=PROMPT_FOR_CHAT_RESPONSE),
            *(
                [SystemMessage(content=user_context)]
                if user_context
                else []
            ),
            *chat_history,
            HumanMessage(content=userMessage),
        ]

    async def generate_summary(
        self,
        recent_messages: list,
        existing_summary: dict | None = None,
    ) -> dict:
        conversation = self._format_messages_for_summary(recent_messages)
        previous_summary = self._format_existing_summary(existing_summary)

        content_parts = []
        if previous_summary:
            content_parts.append(previous_summary)
        content_parts.append("New messages to incorporate:")
        content_parts.append(conversation)

        messages = [
            SystemMessage(content=PROMPT_FOR_CHAT_SUMMARY),
            HumanMessage(content="\n\n".join(content_parts)),
        ]

        response = self.llmAPI.invoke(messages)
        parsed = self._parse_summary_response(response.content)

        return {
            "summary": parsed.get("summary", ""),
            "key_points": parsed.get("key_points") or [],
            "user_preference": parsed.get("user_preference", ""),
            "last_updated": datetime.now(timezone.utc),
        }

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
        user_preference = str(chat_summary.get("user_preference", "")).strip()

        if not summary and not key_points and not user_preference:
            return None

        parts = [
            "Use this summary of earlier conversation for context:",
        ]

        if summary:
            parts.append(summary)

        if key_points:
            parts.append("Key points:")
            parts.extend(f"- {point}" for point in key_points)

        if user_preference:
            parts.append("User preference:")
            parts.append(user_preference)
            parts.append("Adapt your response style to match these preferences.")

        return "\n".join(parts)

    @staticmethod
    def _format_existing_summary(existing_summary: dict | None) -> str | None:
        if not existing_summary:
            return None

        summary = str(existing_summary.get("summary", "")).strip()
        key_points = existing_summary.get("key_points") or []
        user_preference = str(existing_summary.get("user_preference", "")).strip()

        if not summary and not key_points and not user_preference:
            return None

        parts = ["Existing conversation summary:"]

        if summary:
            parts.append(summary)

        if key_points:
            parts.append("Existing key points:")
            parts.extend(f"- {point}" for point in key_points)

        if user_preference:
            parts.append("Existing user preference:")
            parts.append(user_preference)

        return "\n".join(parts)

    @staticmethod
    def _format_messages_for_summary(recent_messages: list) -> str:
        lines = []

        for message in recent_messages:
            role = str(message.get("role", "unknown")).capitalize()
            content = str(message.get("message", "")).strip()

            if content:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    @staticmethod
    def _parse_summary_response(content: str) -> dict:
        raw = content.strip()

        if raw.startswith("```"):
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "summary": content.strip(),
                "key_points": [],
                "user_preference": "",
            }

        if not isinstance(parsed, dict):
            return {
                "summary": content.strip(),
                "key_points": [],
                "user_preference": "",
            }

        key_points = parsed.get("key_points") or []
        if not isinstance(key_points, list):
            key_points = []

        return {
            "summary": str(parsed.get("summary", "")).strip(),
            "key_points": [str(point).strip() for point in key_points if str(point).strip()],
            "user_preference": str(parsed.get("user_preference", "")).strip(),
        }