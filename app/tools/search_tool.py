from typing import Any

import httpx

from app.config import settings
from app.core.logger import logger
from app.tools.base import BaseTool, ToolResult

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 5


class SearchTool(BaseTool):
    """
    Web / knowledge search via Tavily.

    DecisionAgent selects this tool; results are passed to ResponseAgent.
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

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error="Search query is empty.",
            )

        try:
            payload = await self._search_tavily(query)
        except httpx.HTTPStatusError as exc:
            error = f"Tavily HTTP {exc.response.status_code}: {exc.response.text}"
            logger.error("[search_tool] %s", error)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error=error,
            )
        except Exception as exc:
            error = f"Tavily search failed: {exc}"
            logger.error("[search_tool] %s", error)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error=error,
            )

        results = self._normalize_results(payload.get("results") or [])
        answer = payload.get("answer")

        logger.info(
            "[search_tool] success | query=%s | result_count=%s",
            query,
            len(results),
        )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "query": query,
                "answer": answer,
                "results": results,
            },
        )

    async def _search_tavily(self, query: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.TAVILY_API_KEY}",
        }
        body = {
            "query": query,
            "max_results": DEFAULT_MAX_RESULTS,
            "include_answer": True,
            "search_depth": "basic",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Unexpected Tavily response shape")

        return data

    @staticmethod
    def _normalize_results(raw_results: list) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            content = str(item.get("content") or "").strip()
            score = item.get("score")

            if not (title or url or content):
                continue

            entry: dict[str, Any] = {
                "title": title,
                "url": url,
                "content": content,
            }
            if score is not None:
                entry["score"] = score

            normalized.append(entry)

        return normalized
