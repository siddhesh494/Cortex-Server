from typing import Any

from app.core.logger import logger
from app.rag.retrieval_service import RagRetrievalService
from app.tools.base import BaseTool, ToolResult


class RAGRetrievalTool(BaseTool):
    """
    Retrieve relevant chunks from the session's indexed document.

    Does not generate the final answer — only returns document context
    for the ResponseAgent.
    """

    name = "rag_retrieval"
    description = (
        "Retrieve relevant passages from the document already uploaded and "
        "indexed in this chat session (rag_summary present). Use for questions "
        "about that document: summary, description, details, parties, dates, "
        "costs, terms, deliverables, etc. Also use when the user says they "
        "uploaded a document/PDF and asks about it. Do NOT use for greetings "
        "or questions clearly unrelated to the uploaded document. Prefer this "
        "over web search when the answer should come from the user's document."
    )
    parameters = {
        "query": {
            "type": "string",
            "description": (
                "Focused retrieval query derived from the user message, "
                "optimized for finding relevant document passages."
            ),
            "required": True,
        }
    }

    def __init__(self, retrieval_service: RagRetrievalService | None = None) -> None:
        self._retrieval = retrieval_service or RagRetrievalService()

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query") or "").strip()
        session_id = str(kwargs.get("session_id") or "").strip()
        user_id = str(kwargs.get("user_id") or "").strip()

        logger.info(
            "[rag_retrieval_tool] execute | query=%s | session=%s",
            query,
            session_id,
        )

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error="Retrieval query is empty.",
            )

        if not session_id or not user_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error="session_id and user_id are required for RAG retrieval.",
            )

        try:
            results = self._retrieval.retrieve(
                query=query,
                session_id=session_id,
                user_id=user_id,
            )
        except Exception as exc:
            error = f"RAG retrieval failed: {exc}"
            logger.error("[rag_retrieval_tool] %s", error)
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"query": query, "results": []},
                error=error,
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "query": query,
                "results": results,
            },
        )
