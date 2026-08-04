import json
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import Agent
from app.agents.types import AgentInput, AgentOutput
from app.config import settings
from app.prompts.system_prompts import PROMPT_FOR_CHAT_SUMMARY


class SummaryAgent(Agent):
    """Folds older messages into a durable conversation summary."""

    name = "summary_agent"
    model = settings.SUMMARY_MODEL
    temperature = 0.0
    system_prompt = PROMPT_FOR_CHAT_SUMMARY

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        started = self.timed()
        recent_messages = agent_input.recent_messages or []
        existing_summary = agent_input.existing_summary
        self.log(
            "generating summary",
            model=self.model,
            message_count=len(recent_messages),
        )

        conversation = self._format_messages_for_summary(recent_messages)
        previous_summary = self._format_existing_summary(existing_summary)

        content_parts = []
        if previous_summary:
            content_parts.append(previous_summary)
        content_parts.append("New messages to incorporate:")
        content_parts.append(conversation)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content="\n\n".join(content_parts)),
        ]

        response = self.llm.invoke(messages)
        parsed = self._parse_summary_response(response.content)

        result = {
            "summary": parsed.get("summary", ""),
            "key_points": parsed.get("key_points") or [],
            "user_preference": parsed.get("user_preference", ""),
            "last_updated": datetime.now(timezone.utc),
        }

        output = AgentOutput(
            content=result,
            metadata={"key_point_count": len(result["key_points"])},
        )
        latency_ms = self.elapsed_ms(started)
        self.evaluate(agent_input, output, latency_ms)
        self.log(
            "summary generated",
            latency_ms=round(latency_ms, 2),
            key_points=len(result["key_points"]),
        )
        return output

    def evaluate(
        self,
        agent_input: AgentInput,
        agent_output: AgentOutput,
        latency_ms: float,
    ) -> None:
        result = agent_output.content or {}
        self.log(
            "evaluation",
            latency_ms=round(latency_ms, 2),
            model=self.model,
            has_summary=bool(str(result.get("summary", "")).strip()),
            key_point_count=len(result.get("key_points") or []),
            schema_ok=isinstance(result.get("key_points"), list),
        )

    @staticmethod
    def _format_existing_summary(existing_summary: dict | None) -> str | None:
        if not existing_summary:
            return None

        summary = str(existing_summary.get("summary", "")).strip()
        key_points = existing_summary.get("key_points") or []
        user_preference = str(existing_summary.get("user_preference", "")).strip()

        if not summary and not key_points and not user_preference:
            return None

        parts = ["Existing conversation summary:"]

        if summary:
            parts.append(summary)

        if key_points:
            parts.append("Existing key points:")
            parts.extend(f"- {point}" for point in key_points)

        if user_preference:
            parts.append("Existing user preference:")
            parts.append(user_preference)

        return "\n".join(parts)

    @staticmethod
    def _format_messages_for_summary(recent_messages: list) -> str:
        lines = []
        for message in recent_messages:
            role = str(message.get("role", "unknown")).capitalize()
            content = str(message.get("message", "")).strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _parse_summary_response(content: str) -> dict:
        raw = content.strip()

        if raw.startswith("```"):
            raw = (
                raw.removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "summary": content.strip(),
                "key_points": [],
                "user_preference": "",
            }

        if not isinstance(parsed, dict):
            return {
                "summary": content.strip(),
                "key_points": [],
                "user_preference": "",
            }

        key_points = parsed.get("key_points") or []
        if not isinstance(key_points, list):
            key_points = []

        return {
            "summary": str(parsed.get("summary", "")).strip(),
            "key_points": [
                str(point).strip() for point in key_points if str(point).strip()
            ],
            "user_preference": str(parsed.get("user_preference", "")).strip(),
        }
