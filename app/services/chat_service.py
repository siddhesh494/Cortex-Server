import json
from datetime import datetime, timezone
from typing import AsyncGenerator

from app.agents.decision_agent import DecisionAgent, ToolDecision
from app.agents.response_agent import ResponseAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.title_agent import TitleAgent
from app.agents.types import AgentInput
from app.core.exceptions import (
    ChatNotFoundException,
    DocumentAlreadyUploadedException,
)
from app.core.logger import logger
from app.rag.indexing_service import RagIndexingService
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatDetailResponse,
    ChatHistoryItemResponse,
    ChatRequestSchema,
    UploadedDocument,
)
from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry, default_tool_registry


class ChatService:
    """
    Conversation Manager.

    Orchestrates agents; does not own prompts or model configuration.
    Flow: Title → (optional RAG index) → Decision → Tool(s) → Response → Summary
    """

    SUMMARY_WINDOW_SIZE = 10
    SUMMARY_TRIGGER_BUFFER = 2

    def __init__(self, tool_registry: ToolRegistry | None = None):
        self.chat_repository = ChatRepository()
        self.tool_registry = tool_registry or default_tool_registry
        self.title_agent = TitleAgent()
        self.decision_agent = DecisionAgent(registry=self.tool_registry)
        self.response_agent = ResponseAgent()
        self.summary_agent = SummaryAgent()
        self.rag_indexing = RagIndexingService()

    async def chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):
        if body.chatSessionId:
            return await self._continue_chat(user_id, body)

        return await self._create_new_chat(user_id, body)

    async def chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
        document: UploadedDocument | None = None,
    ) -> AsyncGenerator[dict, None]:
        if body.chatSessionId:
            async for event in self._continue_chat_stream(user_id, body, document):
                yield event
            return

        async for event in self._create_new_chat_stream(user_id, body, document):
            yield event

    async def assert_document_allowed(
        self,
        user_id: str,
        chat_session_id: str | None,
    ) -> None:
        """Raise if the session already has an indexed document."""
        if not chat_session_id:
            return

        session = await self.chat_repository.find_by_id_and_user(
            chat_session_id,
            user_id,
        )
        if session is None:
            raise ChatNotFoundException()

        if session.get("rag_summary"):
            raise DocumentAlreadyUploadedException()

    async def get_chat_history(
        self,
        user_id: str,
    ):
        sessions = await self.chat_repository.get_user_session_list(user_id)

        return [
            ChatHistoryItemResponse.from_mongo(session)
            for session in sessions
        ]

    async def get_chat_by_id(
        self,
        user_id: str,
        chat_session_id: str,
    ) -> ChatDetailResponse:
        session = await self.chat_repository.find_by_id_and_user(
            chat_session_id,
            user_id,
        )

        if session is None:
            raise ChatNotFoundException()

        return ChatDetailResponse.from_mongo(session)

    async def _create_new_chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):
        message = self._normalize_message(body.message)
        title = (
            await self.title_agent.execute(AgentInput(message=message))
        ).content

        decision = (
            await self.decision_agent.execute(AgentInput(message=message))
        ).content
        tool_context = await self._resolve_tool_context(
            decision,
            user_id=user_id,
            session_id=None,
        )
        ai_response = (
            await self.response_agent.execute(
                AgentInput(message=message, tool_context=tool_context)
            )
        ).content

        now = datetime.now(timezone.utc)

        document = {
            "user_id": user_id,
            "chat_session_name": title,
            "chat_summary": {},
            "recent_messages": [
                {
                    "role": "user",
                    "message": message,
                    "created_at": now,
                },
                {
                    "role": "assistant",
                    "message": ai_response,
                    "created_at": now,
                },
            ],
            "created_at": now,
            "updated_at": now,
        }

        session_id = await self.chat_repository.create_session(document)

        return {
            "chatSessionId": session_id,
            "response": ai_response,
        }

    async def _continue_chat(
        self,
        user_id: str,
        body: ChatRequestSchema,
    ):
        session = await self.chat_repository.find_by_id_and_user(
            body.chatSessionId,
            user_id,
        )

        if session is None:
            raise ChatNotFoundException()

        message = self._normalize_message(body.message)
        messages = session["recent_messages"]
        chat_summary = session.get("chat_summary") or {}
        rag_summary = session.get("rag_summary")
        summarized_count = int(chat_summary.get("summarized_message_count") or 0)
        previous_messages = list(messages[summarized_count:])

        now = datetime.now(timezone.utc)

        messages.append(
            {
                "role": "user",
                "message": message,
                "created_at": now,
            }
        )

        decision = (
            await self.decision_agent.execute(
                AgentInput(
                    message=message,
                    previous_messages=previous_messages,
                    chat_summary=chat_summary,
                    rag_summary=rag_summary,
                )
            )
        ).content
        tool_context = await self._resolve_tool_context(
            decision,
            user_id=user_id,
            session_id=body.chatSessionId,
        )
        ai_response = (
            await self.response_agent.execute(
                AgentInput(
                    message=message,
                    previous_messages=previous_messages,
                    chat_summary=chat_summary,
                    tool_context=tool_context,
                )
            )
        ).content

        messages.append(
            {
                "role": "assistant",
                "message": ai_response,
                "created_at": now,
            }
        )

        messages_for_summary = self._extract_messages_for_summary(
            messages,
            summarized_count,
        )

        if messages_for_summary:
            chat_summary = (
                await self.summary_agent.execute(
                    AgentInput(
                        recent_messages=messages_for_summary,
                        existing_summary=chat_summary,
                    )
                )
            ).content
            chat_summary["summarized_message_count"] = (
                summarized_count + self.SUMMARY_WINDOW_SIZE
            )

        await self.chat_repository.update_session(
            body.chatSessionId,
            {
                "recent_messages": messages,
                "chat_summary": chat_summary,
                "updated_at": now,
            },
        )

        return {
            "chatSessionId": body.chatSessionId,
            "response": ai_response,
        }

    async def _create_new_chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
        document: UploadedDocument | None = None,
    ) -> AsyncGenerator[dict, None]:
        message = self._normalize_message(
            body.message,
            filename=document.filename if document else None,
        )

        now = datetime.now(timezone.utc)
        session_doc = {
            "user_id": user_id,
            "chat_session_name": "New Chat",
            "chat_summary": {},
            "recent_messages": [
                {
                    "role": "user",
                    "message": message,
                    "created_at": now,
                }
            ],
            "created_at": now,
            "updated_at": now,
        }

        session_id = await self.chat_repository.create_session(session_doc)

        rag_summary = None
        title_seed = message

        if document is not None:
            file_bytes = document.content
            document.content = b""
            indexing = await self.rag_indexing.index_document(
                file_bytes=file_bytes,
                filename=document.filename,
                session_id=session_id,
                user_id=user_id,
            )
            del file_bytes
            rag_summary = indexing.rag_summary
            title_seed = self._build_title_seed(message, indexing.excerpt)

        title = (
            await self.title_agent.execute(AgentInput(message=title_seed))
        ).content

        yield {
            "type": "meta",
            "chatSessionId": session_id,
        }

        decision = (
            await self.decision_agent.execute(
                AgentInput(message=message, rag_summary=rag_summary)
            )
        ).content
        tool_context = await self._resolve_tool_context(
            decision,
            user_id=user_id,
            session_id=session_id,
        )
        response_input = AgentInput(
            message=message,
            tool_context=tool_context,
        )

        ai_response = ""
        async for token in self.response_agent.stream(response_input):
            ai_response += token
            yield {
                "type": "token",
                "content": token,
            }

        now = datetime.now(timezone.utc)
        update_fields: dict = {
            "chat_session_name": title,
            "recent_messages": [
                {
                    "role": "user",
                    "message": message,
                    "created_at": now,
                },
                {
                    "role": "assistant",
                    "message": ai_response,
                    "created_at": now,
                },
            ],
            "updated_at": now,
        }
        if rag_summary is not None:
            update_fields["rag_summary"] = rag_summary
            update_fields["rag_document_id"] = indexing.document_id

        await self.chat_repository.update_session(session_id, update_fields)

        yield {
            "type": "done",
            "chatSessionId": session_id,
        }

    async def _continue_chat_stream(
        self,
        user_id: str,
        body: ChatRequestSchema,
        document: UploadedDocument | None = None,
    ) -> AsyncGenerator[dict, None]:
        session = await self.chat_repository.find_by_id_and_user(
            body.chatSessionId,
            user_id,
        )

        if session is None:
            raise ChatNotFoundException()

        if document is not None and session.get("rag_summary"):
            raise DocumentAlreadyUploadedException()

        message = self._normalize_message(
            body.message,
            filename=document.filename if document else None,
        )
        messages = session["recent_messages"]
        chat_summary = session.get("chat_summary") or {}
        rag_summary = session.get("rag_summary")
        rag_document_id = None
        summarized_count = int(chat_summary.get("summarized_message_count") or 0)
        previous_messages = list(messages[summarized_count:])

        if document is not None:
            file_bytes = document.content
            document.content = b""
            indexing = await self.rag_indexing.index_document(
                file_bytes=file_bytes,
                filename=document.filename,
                session_id=body.chatSessionId,
                user_id=user_id,
            )
            del file_bytes
            rag_summary = indexing.rag_summary
            rag_document_id = indexing.document_id

        now = datetime.now(timezone.utc)
        messages.append(
            {
                "role": "user",
                "message": message,
                "created_at": now,
            }
        )

        yield {
            "type": "meta",
            "chatSessionId": body.chatSessionId,
        }

        decision = (
            await self.decision_agent.execute(
                AgentInput(
                    message=message,
                    previous_messages=previous_messages,
                    chat_summary=chat_summary,
                    rag_summary=rag_summary,
                )
            )
        ).content
        logger.info(f"[chat_service] | decision: {decision}")
        tool_context = await self._resolve_tool_context(
            decision,
            user_id=user_id,
            session_id=body.chatSessionId,
        )
        response_input = AgentInput(
            message=message,
            previous_messages=previous_messages,
            chat_summary=chat_summary,
            tool_context=tool_context,
        )

        ai_response = ""
        async for token in self.response_agent.stream(response_input):
            ai_response += token
            yield {
                "type": "token",
                "content": token,
            }

        messages.append(
            {
                "role": "assistant",
                "message": ai_response,
                "created_at": now,
            }
        )

        messages_for_summary = self._extract_messages_for_summary(
            messages,
            summarized_count,
        )

        if messages_for_summary:
            chat_summary = (
                await self.summary_agent.execute(
                    AgentInput(
                        recent_messages=messages_for_summary,
                        existing_summary=chat_summary,
                    )
                )
            ).content
            chat_summary["summarized_message_count"] = (
                summarized_count + self.SUMMARY_WINDOW_SIZE
            )

        update_fields: dict = {
            "recent_messages": messages,
            "chat_summary": chat_summary,
            "updated_at": datetime.now(timezone.utc),
        }
        if rag_document_id is not None:
            update_fields["rag_summary"] = rag_summary
            update_fields["rag_document_id"] = rag_document_id

        await self.chat_repository.update_session(
            body.chatSessionId,
            update_fields,
        )

        yield {
            "type": "done",
            "chatSessionId": body.chatSessionId,
        }

    async def _resolve_tool_context(
        self,
        decision: ToolDecision,
        *,
        user_id: str,
        session_id: str | None,
    ) -> str | None:
        """
        Execute the chosen tool (if any) and format its result for ResponseAgent.
        """
        if not decision.needs_tool or not decision.tool_name:
            logger.info(
                "[conversation_manager] tool decision: skip tools | reason=%s",
                decision.reason,
            )
            return None

        tool = self.tool_registry.get(decision.tool_name)
        if tool is None:
            logger.warning(
                "[conversation_manager] tool not found | tool=%s",
                decision.tool_name,
            )
            return None

        tool_args = dict(decision.tool_args or {})
        if decision.tool_name == "rag_retrieval":
            tool_args["session_id"] = session_id
            tool_args["user_id"] = user_id

        logger.info(
            "[conversation_manager] executing tool | tool=%s | args=%s",
            decision.tool_name,
            {k: v for k, v in tool_args.items() if k != "user_id"},
        )

        try:
            result = await tool.execute(**tool_args)
        except Exception as exc:
            logger.error(
                "[conversation_manager] tool execution failed | tool=%s | error=%s",
                decision.tool_name,
                exc,
            )
            result = ToolResult(
                tool_name=decision.tool_name,
                success=False,
                data=None,
                error=str(exc),
            )

        return self._format_tool_context(decision, result)

    @staticmethod
    def _format_tool_context(decision: ToolDecision, result: ToolResult) -> str:
        payload = {
            "tool_name": decision.tool_name,
            "tool_args": decision.tool_args,
            "reason": decision.reason,
            "success": result.success,
            "error": result.error,
            "data": result.data,
        }

        if decision.tool_name == "rag_retrieval":
            return (
                "Retrieved document passages from the user's uploaded file. "
                "Ground your answer in these passages when relevant.\n"
                f"{json.dumps(payload, default=str, indent=2)}\n"
                "If data.results is empty, say you could not find relevant "
                "passages in the uploaded document and answer carefully "
                "without inventing document contents."
            )

        return (
            "Tool results are available. Use them when answering the user.\n"
            f"{json.dumps(payload, default=str, indent=2)}\n"
            "If data.results is empty, say search returned no results and "
            "answer from general knowledge without inventing sources."
        )

    def _extract_messages_for_summary(
        self,
        messages: list,
        summarized_message_count: int,
    ) -> list | None:
        """
        Return the next completed window of messages to fold into the summary.

        Windows are summarized only after a small buffer of newer messages exists:
        - at length 12 → summarize messages[0:10]
        - at length 22 → summarize messages[10:20]
        - at length 32 → summarize messages[20:30]
        and so on.
        """
        next_window_end = summarized_message_count + self.SUMMARY_WINDOW_SIZE

        if len(messages) < next_window_end + self.SUMMARY_TRIGGER_BUFFER:
            return None

        return messages[summarized_message_count:next_window_end]

    @staticmethod
    def _normalize_message(message: str, filename: str | None = None) -> str:
        cleaned = (message or "").strip()
        if cleaned:
            return cleaned
        if filename:
            return f"I've uploaded a document named {filename}."
        return "Hello"

    @staticmethod
    def _build_title_seed(message: str, document_excerpt: str) -> str:
        parts = []
        if message.strip():
            parts.append(f"User message: {message.strip()}")
        if document_excerpt.strip():
            parts.append(f"Document excerpt:\n{document_excerpt.strip()[:1500]}")
        return "\n\n".join(parts) if parts else "Uploaded Document"
