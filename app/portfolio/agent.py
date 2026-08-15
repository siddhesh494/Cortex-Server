"""Groq-backed agent that answers portfolio visitors about the owner."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.core.logger import logger
from app.portfolio.about_me import ABOUT_ME, AboutMeProfile
from app.portfolio.prompts import PORTFOLIO_SYSTEM_PROMPT
from app.portfolio.session_store import PortfolioMessage


class PortfolioAgent:
    """
    Public portfolio Q&A agent.

    About-me facts from AboutMeProfile are baked into the system prompt in
    __init__ and attached as a SystemMessage on every turn so answers stay
    grounded in personal details.
    """

    def __init__(
        self,
        about_me: AboutMeProfile | None = None,
        model: str | None = None,
        temperature: float = 0.3,
    ) -> None:
        self.about_me = about_me or ABOUT_ME
        self.model = model or settings.PORTFOLIO_MODEL
        self.temperature = temperature

        self.system_prompt = PORTFOLIO_SYSTEM_PROMPT.format(
            name=self.about_me.full_name,
            about_me=self.about_me.to_prompt_block(),
        )

        self.llm = ChatGroq(
            model=self.model,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=self.temperature,
        )
        logger.info(
            "[portfolio_agent] initialized | model=%s | name=%s",
            self.model,
            self.about_me.full_name,
        )

    async def answer(
        self,
        message: str,
        history: list[PortfolioMessage] | None = None,
    ) -> str:
        messages = self._build_messages(message, history or [])
        response = await self.llm.ainvoke(messages)
        content = response.content

        if isinstance(content, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        else:
            text = str(content)

        return text.strip()

    def _build_messages(
        self,
        message: str,
        history: list[PortfolioMessage],
    ) -> list:
        # Always ground the model in AboutMeProfile (not only on turn 1).
        messages: list = [SystemMessage(content=self.system_prompt)]

        for item in history:
            if item.role == "user":
                messages.append(HumanMessage(content=item.content))
            elif item.role == "assistant":
                messages.append(AIMessage(content=item.content))
            # Skip stored "system" entries — live prompt comes from AboutMeProfile.

        messages.append(HumanMessage(content=message))
        return messages
