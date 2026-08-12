"""Generate a lightweight RAGSummary for DecisionAgent routing."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.core.logger import logger
from app.prompts.system_prompts import PROMPT_FOR_RAG_SUMMARY

_MAX_EXCERPT_CHARS = 6000


def generate_rag_summary(
    *,
    document_text: str,
    source_file_name: str,
) -> dict[str, Any]:
    excerpt = (document_text or "").strip()[:_MAX_EXCERPT_CHARS]
    if not excerpt:
        return _fallback_summary(source_file_name)

    llm = ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model=settings.SUMMARY_MODEL,
        temperature=0.0,
    )

    messages = [
        SystemMessage(content=PROMPT_FOR_RAG_SUMMARY),
        HumanMessage(
            content=(
                f"Source file name: {source_file_name}\n\n"
                f"Document excerpt:\n{excerpt}"
            )
        ),
    ]

    try:
        raw = llm.invoke(messages).content
        parsed = _parse_json(raw if isinstance(raw, str) else str(raw))
        return _normalize_summary(parsed, source_file_name)
    except Exception as exc:
        logger.warning(
            "[rag.summary] failed to generate RAGSummary; using fallback | error=%s",
            exc,
        )
        return _fallback_summary(source_file_name, excerpt)


def _parse_json(content: str) -> dict[str, Any]:
    raw = (content or "").strip()
    if raw.startswith("```"):
        raw = (
            raw.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("RAGSummary response is not an object")
    return parsed


def _normalize_summary(parsed: dict[str, Any], source_file_name: str) -> dict[str, Any]:
    def as_str_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    about = str(parsed.get("aboutDoc") or "").strip()
    if not about:
        about = f"Uploaded document: {source_file_name}"

    return {
        "aboutDoc": about,
        "keywords": as_str_list(parsed.get("keywords")),
        "topics": as_str_list(parsed.get("topics")),
        "entities": as_str_list(parsed.get("entities")),
        "documentType": str(parsed.get("documentType") or "Document").strip()
        or "Document",
        "sourceFileName": source_file_name,
    }


def _fallback_summary(
    source_file_name: str,
    excerpt: str = "",
) -> dict[str, Any]:
    about = f"Uploaded document: {source_file_name}"
    if excerpt:
        about = f"Document '{source_file_name}'. Preview: {excerpt[:240]}"

    return {
        "aboutDoc": about,
        "keywords": [],
        "topics": [],
        "entities": [],
        "documentType": "Document",
        "sourceFileName": source_file_name,
    }
