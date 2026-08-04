from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass
class ToolResult:
    """Result returned by a tool execute() call."""

    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None


class BaseTool(ABC):
    """
    Common tool interface.

    Register new tools with ToolRegistry — DecisionAgent reads the catalog
    automatically, so adding a tool does not require rewriting decision logic.
    """

    name: ClassVar[str] = "base_tool"
    description: ClassVar[str] = ""
    parameters: ClassVar[dict[str, Any]] = {}

    def to_catalog_entry(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Run the tool with args chosen by the DecisionAgent."""
