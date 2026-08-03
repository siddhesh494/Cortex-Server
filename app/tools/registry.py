from app.tools.base import BaseTool
from app.tools.search_tool import SearchTool


class ToolRegistry:
    """
    Central registry of callable tools.

    DecisionAgent uses catalog() to know what tools exist.
    Conversation Manager uses get() to execute the chosen tool.
    Add future tools by registering them here (or at startup).
    """

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools if tools is not None else self._default_tools():
            self.register(tool)

    @staticmethod
    def _default_tools() -> list[BaseTool]:
        return [
            SearchTool(),
            # Future: WeatherTool(), CalculatorTool(), etc.
        ]

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def catalog(self) -> list[dict]:
        return [tool.to_catalog_entry() for tool in self._tools.values()]


# Shared default registry used by DecisionAgent and ChatService
default_tool_registry = ToolRegistry()
