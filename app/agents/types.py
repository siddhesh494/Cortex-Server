from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentInput:
    """Shared input envelope for all agents."""

    message: str = ""
    previous_messages: list | None = None
    chat_summary: dict | None = None
    tool_context: str | None = None
    recent_messages: list | None = None
    existing_summary: dict | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Shared output envelope for all agents."""

    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
