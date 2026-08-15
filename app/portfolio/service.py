"""Orchestrates portfolio Q&A: sessions + grounded Groq replies."""

from __future__ import annotations

from app.core.exceptions import PortfolioSessionNotFoundException
from app.core.logger import logger
from app.portfolio.agent import PortfolioAgent
from app.portfolio.schemas import PortfolioAskRequest, PortfolioAskResponse
from app.portfolio.session_store import (
    PortfolioSessionStore,
    build_session_store,
)


class PortfolioService:
    """Public (unauthenticated) ask-about-me conversation manager."""

    def __init__(
        self,
        agent: PortfolioAgent | None = None,
        session_store: PortfolioSessionStore | None = None,
    ) -> None:
        self.agent = agent or PortfolioAgent()
        self.session_store = session_store or build_session_store()

    async def ask(self, body: PortfolioAskRequest) -> PortfolioAskResponse:
        message = body.message.strip()
        if not message:
            raise ValueError("message is required.")

        session_id = body.sessionId
        history: list = []

        if session_id:
            history = self.session_store.get_messages(session_id)
            if history is None:
                raise PortfolioSessionNotFoundException()
        else:
            # Seed about-me system prompt once for this session; later turns reuse it.
            session_id = self.session_store.create_session(
                system_prompt=self.agent.system_prompt,
            )
            history = self.session_store.get_messages(session_id) or []

        logger.info(
            "[portfolio_service] ask | session=%s | history=%s | chars=%s",
            session_id,
            len(history),
            len(message),
        )

        answer = await self.agent.answer(message=message, history=history)

        saved = self.session_store.append_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
        )

        # Safety net: if the session expired between get and append, start fresh.
        if not saved:
            session_id = self.session_store.create_session(
                system_prompt=self.agent.system_prompt,
            )
            self.session_store.append_exchange(
                session_id=session_id,
                user_message=message,
                assistant_message=answer,
            )

        return PortfolioAskResponse(sessionId=session_id, response=answer)
