from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class SummaryModel(BaseModel):
    title: str
    total_messages: int = 0
    last_updated: datetime


class RecentMessageModel(BaseModel):
    role: str
    message: str
    timestamp: datetime

class ChatSessionModel(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: ObjectId = Field(alias="userID")
    chat_session_name: str = Field(alias="chatSessionName")
    summary: SummaryModel
    recent_messages: list[RecentMessageModel] = Field(
        default_factory=list,
        alias="recentMessage"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )
