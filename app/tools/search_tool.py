from typing import Any

from app.core.logger import logger
from app.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    """
    Web / knowledge search tool.

    Stub: logs the query and returns an empty result payload.
    Wire a real search provider later without changing DecisionAgent.
    """

    name = "search"
    description = (
        "Search for current information, facts, news, prices, events, or "
        "anything that needs up-to-date or external knowledge beyond the "
        "model's training data. Use when the user asks to look something up, "
        "search the web, or wants recent/live information."
    )
    parameters = {
        "query": {
            "type": "string",
            "description": "Clear, focused search query derived from the user message.",
            "required": True,
        }
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query") or "").strip()

        print(f"[search_tool] execute | query={query!r}")
        logger.info("[search_tool] execute | query=%s", query)

        # Empty stub response — ResponseAgent still receives structured context.
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "query": query,
                "results": [],
            },
        )
