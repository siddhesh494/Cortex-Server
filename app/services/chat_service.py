from datetime import datetime, timezone

from app.core.exceptions import ChatNotFoundException
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatDetailResponse,
    ChatHistoryItemResponse,
    ChatRequestSchema,
)
from app.services.llm_service import LLMService


class ChatService:

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
        previous_messages = list[any](messages)

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
            chat_summary=session.get("chat_summary"),
        )

        messages.append(
            {
                "role": "assistant",
                "message": ai_response,
                "created_at": now
            }
        )

        if len(messages) > 10:

            session["chat_summary"] = (
                await self.llm_service.generate_summary(
                    messages[0:12]
                )
            )

            # messages = messages[-10:]
        
        await self.chat_repository.update_session(
            body.chatSessionId,
            {
                "recent_messages": messages,
                "chat_summary": session["chat_summary"],
                "updated_at": now
            }
        )

        return {
            "chatSessionId": body.chatSessionId,
            "response": ai_response
        }