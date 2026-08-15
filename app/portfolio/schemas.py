"""Request / response schemas for the public portfolio Q&A API."""

from pydantic import BaseModel, Field


class PortfolioAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    sessionId: str | None = Field(
        default=None,
        description="Optional session id. Omit to start a new 30-minute session.",
    )


class PortfolioAskResponse(BaseModel):
    sessionId: str
    response: str
