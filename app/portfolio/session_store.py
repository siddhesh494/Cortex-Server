"""Temporary conversation memory for portfolio chats.

In-process store with a 30-minute sliding TTL.
The about-me system prompt is written once when a session is created and
reused from session memory on later turns (not rebuilt each request).
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import Lock

from app.core.logger import logger

SESSION_TTL_SECONDS = 30 * 60  # 30 minutes
MAX_MESSAGES_PER_SESSION = 40


@dataclass
class PortfolioMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class PortfolioSession:
    session_id: str
    messages: list[PortfolioMessage] = field(default_factory=list)
    expires_at: float = 0.0

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) >= self.expires_at


def _trim_messages(messages: list[PortfolioMessage]) -> list[PortfolioMessage]:
    """Keep the system prompt pinned; trim oldest user/assistant turns."""
    if len(messages) <= MAX_MESSAGES_PER_SESSION:
        return messages

    system = [m for m in messages if m.role == "system"]
    rest = [m for m in messages if m.role != "system"]
    keep = max(0, MAX_MESSAGES_PER_SESSION - len(system))
    return system + rest[-keep:]


class PortfolioSessionStore(ABC):
    """Abstract session memory with 30-minute expiry."""

    @abstractmethod
    def create_session(self, system_prompt: str) -> str:
        """Create a session and seed it with the system prompt (once)."""

    @abstractmethod
    def get_messages(self, session_id: str) -> list[PortfolioMessage] | None:
        """Return messages, or None if the session is missing/expired."""

    @abstractmethod
    def append_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> bool:
        """Append a turn and refresh TTL. False if session is gone."""

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        ...


class InMemoryPortfolioSessionStore(PortfolioSessionStore):
    """Process-local dict store; free after 30 min idle."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, PortfolioSession] = {}
        self._lock = Lock()

    def create_session(self, system_prompt: str) -> str:
        self._purge_expired()
        session_id = str(uuid.uuid4())
        now = time.time()
        with self._lock:
            self._sessions[session_id] = PortfolioSession(
                session_id=session_id,
                messages=[
                    PortfolioMessage(role="system", content=system_prompt),
                ],
                expires_at=now + self._ttl,
            )
        return session_id

    def get_messages(self, session_id: str) -> list[PortfolioMessage] | None:
        self._purge_expired()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.is_expired():
                self._sessions.pop(session_id, None)
                return None
            session.expires_at = time.time() + self._ttl
            return list(session.messages)

    def append_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> bool:
        self._purge_expired()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.is_expired():
                self._sessions.pop(session_id, None)
                return False

            session.messages.append(
                PortfolioMessage(role="user", content=user_message)
            )
            session.messages.append(
                PortfolioMessage(role="assistant", content=assistant_message)
            )
            session.messages = _trim_messages(session.messages)
            session.expires_at = time.time() + self._ttl
            return True

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def _purge_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, session in self._sessions.items()
                if session.is_expired(now)
            ]
            for sid in expired:
                del self._sessions[sid]
            if expired:
                logger.info(
                    "[portfolio_session] purged expired sessions | count=%s",
                    len(expired),
                )


def build_session_store() -> PortfolioSessionStore:
    return InMemoryPortfolioSessionStore()
