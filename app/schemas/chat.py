from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class ChatResponse(BaseModel):
    id: str
    title: str
    user_id: str


class ChatRequestSchema(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )
    chatSessionId: str | None = None


class ChatMessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    message: str
    created_at: datetime | None = None


class ChatDetailResponse(BaseModel):
    id: str
    title: str
    messages: list[ChatMessageResponse]

    @classmethod
    def from_mongo(cls, session: dict) -> "ChatDetailResponse":
        return cls(
            id=str(session["_id"]),
            title=session["chat_session_name"],
            messages=[
                ChatMessageResponse(
                    role=message["role"],
                    message=message["message"],
                    created_at=message.get("created_at"),
                )
                for message in session.get("recent_messages", [])
            ],
        )


class ChatHistoryItemResponse(BaseModel):
    id: str
    title: str

    @classmethod
    def from_mongo(cls, session: dict) -> "ChatHistoryItemResponse":
        return cls(
            id=str(session["_id"]),
            title=session["chat_session_name"],
        )