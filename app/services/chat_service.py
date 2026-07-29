from datetime import datetime, timezone
from typing import AsyncGenerator

from app.core.exceptions import ChatNotFoundException
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatDetailResponse,
    ChatHistoryItemResponse,
    ChatRequestSchema,
)
from app.services.llm_service import LLMService


class ChatService:

    SUMMARY_WINDOW_SIZE = 10
    SUMMARY_TRIGGER_BUFFER = 2

    def __init__(self):

        self.chat_repository = ChatRepository()
        self.llm_service = LLMService()

    async def chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):

        if body.chatSessionId:
            return await self._continue_chat(
                user_id,
                body
            )

        return await self._create_new_chat(
            user_id,
            body
        )

    async def chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ) -> AsyncGenerator[dict, None]:
        if body.chatSessionId:
            async for event in self._continue_chat_stream(user_id, body):
                yield event
            return

        async for event in self._create_new_chat_stream(user_id, body):
            yield event

    async def get_chat_history(
        self,
        user_id: str,
    ):
        sessions = await self.chat_repository.get_user_session_list(
            user_id
        )

        return [
            ChatHistoryItemResponse.from_mongo(session)
            for session in sessions
        ]

    async def get_chat_by_id(
        self,
        user_id: str,
        chat_session_id: str,
    ) -> ChatDetailResponse:
        session = await self.chat_repository.find_by_id_and_user(
            chat_session_id,
            user_id,
        )

        if session is None:
            raise ChatNotFoundException()

        return ChatDetailResponse.from_mongo(session)

    async def _create_new_chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):

        title = await self.llm_service.generate_chat_title(
            body.message
        )

        ai_response = await self.llm_service.generate_response(body.message)

        now = datetime.now(timezone.utc)

        document = {

            "user_id": user_id,

            "chat_session_name": title,

            "chat_summary": {},

            "recent_messages": [

                {
                    "role": "user",
                    "message": body.message,
                    "created_at": now
                },

                {
                    "role": "assistant",
                    "message": ai_response,
                    "created_at": now
                }

            ],

            "created_at": now,
            "updated_at": now

        }

        session_id = await self.chat_repository.create_session(
            document
        )

        return {
            "chatSessionId": session_id,
            "response": ai_response
        }

    async def _continue_chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):

        session = await self.chat_repository.find_by_id_and_user(
            body.chatSessionId,
            user_id
        )

        if session is None:
            raise ChatNotFoundException()

        messages = session["recent_messages"]
        chat_summary = session.get("chat_summary") or {}
        summarized_count = int(chat_summary.get("summarized_message_count") or 0)

        # Only send messages not already covered by the summary to the LLM.
        previous_messages = list(messages[summarized_count:])

        now = datetime.now(timezone.utc)

        messages.append(
            {
                "role": "user",
                "message": body.message,
                "created_at": now
            }
        )

        ai_response = await self.llm_service.generate_response(
            body.message,
            previous_messages=previous_messages,
            chat_summary=chat_summary,
        )

        messages.append(
            {
                "role": "assistant",
                "message": ai_response,
                "created_at": now
            }
        )

        messages_for_summary = self._extract_messages_for_summary(
            messages,
            summarized_count,
        )

        if messages_for_summary:
            chat_summary = await self.llm_service.generate_summary(
                messages_for_summary,
                existing_summary=chat_summary,
            )
            chat_summary["summarized_message_count"] = (
                summarized_count + self.SUMMARY_WINDOW_SIZE
            )

        await self.chat_repository.update_session(
            body.chatSessionId,
            {
                "recent_messages": messages,
                "chat_summary": chat_summary,
                "updated_at": now
            }
        )

        return {
            "chatSessionId": body.chatSessionId,
            "response": ai_response
        }

    async def _create_new_chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ) -> AsyncGenerator[dict, None]:
        title = await self.llm_service.generate_chat_title(
            body.message
        )

        now = datetime.now(timezone.utc)
        document = {
            "user_id": user_id,
            "chat_session_name": title,
            "chat_summary": {},
            "recent_messages": [
                {
                    "role": "user",
                    "message": body.message,
                    "created_at": now,
                }
            ],
            "created_at": now,
            "updated_at": now,
        }

        session_id = await self.chat_repository.create_session(document)

        yield {
            "type": "meta",
            "chatSessionId": session_id,
        }

        ai_response = ""
        async for token in self.llm_service.stream_response(body.message):
            ai_response += token
            yield {
                "type": "token",
                "content": token,
            }

        now = datetime.now(timezone.utc)
        await self.chat_repository.update_session(
            session_id,
            {
                "recent_messages": [
                    {
                        "role": "user",
                        "message": body.message,
                        "created_at": now,
                    },
                    {
                        "role": "assistant",
                        "message": ai_response,
                        "created_at": now,
                    },
                ],
                "updated_at": now,
            },
        )

        yield {
            "type": "done",
            "chatSessionId": session_id,
        }

    async def _continue_chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ) -> AsyncGenerator[dict, None]:
        session = await self.chat_repository.find_by_id_and_user(
            body.chatSessionId,
            user_id,
        )

        if session is None:
            raise ChatNotFoundException()

        messages = session["recent_messages"]
        chat_summary = session.get("chat_summary") or {}
        summarized_count = int(chat_summary.get("summarized_message_count") or 0)
        previous_messages = list(messages[summarized_count:])

        now = datetime.now(timezone.utc)
        messages.append(
            {
                "role": "user",
                "message": body.message,
                "created_at": now,
            }
        )

        yield {
            "type": "meta",
            "chatSessionId": body.chatSessionId,
        }

        ai_response = ""
        async for token in self.llm_service.stream_response(
            body.message,
            previous_messages=previous_messages,
            chat_summary=chat_summary,
        ):
            ai_response += token
            yield {
                "type": "token",
                "content": token,
            }

        messages.append(
            {
                "role": "assistant",
                "message": ai_response,
                "created_at": now,
            }
        )

        messages_for_summary = self._extract_messages_for_summary(
            messages,
            summarized_count,
        )

        if messages_for_summary:
            chat_summary = await self.llm_service.generate_summary(
                messages_for_summary,
                existing_summary=chat_summary,
            )
            chat_summary["summarized_message_count"] = (
                summarized_count + self.SUMMARY_WINDOW_SIZE
            )

        await self.chat_repository.update_session(
            body.chatSessionId,
            {
                "recent_messages": messages,
                "chat_summary": chat_summary,
                "updated_at": datetime.now(timezone.utc),
            },
        )

        yield {
            "type": "done",
            "chatSessionId": body.chatSessionId,
        }

    def _extract_messages_for_summary(
        self,
        messages: list,
        summarized_message_count: int,
    ) -> list | None:
        """
        Return the next completed window of messages to fold into the summary.

        Windows are summarized only after a small buffer of newer messages exists:
        - at length 12 → summarize messages[0:10]
        - at length 22 → summarize messages[10:20]
        - at length 32 → summarize messages[20:30]
        and so on.
        """
        next_window_end = summarized_message_count + self.SUMMARY_WINDOW_SIZE

        if len(messages) < next_window_end + self.SUMMARY_TRIGGER_BUFFER:
            return None

        return messages[summarized_message_count:next_window_end]
