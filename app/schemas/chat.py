from pydantic import BaseModel, Field
from typing import Optional


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