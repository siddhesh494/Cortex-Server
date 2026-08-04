import json
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import Agent
from app.agents.types import AgentInput, AgentOutput
from app.config import settings
from app.prompts.system_prompts import PROMPT_FOR_TOOL_DECISION
from app.tools.registry import ToolRegistry, default_tool_registry


@dataclass
class ToolDecision:
    needs_tool: bool
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class DecisionAgent(Agent):
    """
    Chooses whether to call a tool for the current turn.

    Tool catalog comes from ToolRegistry — register new tools there and this
    agent will include them in its decision prompt automatically.
    """

    name = "decision_agent"
    model = settings.DECISION_MODEL
    temperature = 0.0
    system_prompt = PROMPT_FOR_TOOL_DECISION

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(model=model, temperature=temperature)
        self.registry = registry or default_tool_registry

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        started = self.timed()
        self.log("deciding tool use", model=self.model)

        messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=self._build_user_payload(agent_input)),
        ]

        raw = self.llm.invoke(messages).content
        decision = self._parse_decision(raw)
        decision = self._validate_against_registry(decision)

        output = AgentOutput(
            content=decision,
            metadata={
                "available_tools": self.registry.names(),
                "raw_response": raw if isinstance(raw, str) else str(raw),
            },
        )
        latency_ms = self.elapsed_ms(started)
        self.evaluate(agent_input, output, latency_ms)
        self.log(
            "decision made",
            needs_tool=decision.needs_tool,
            tool_name=decision.tool_name,
            reason=decision.reason,
            latency_ms=round(latency_ms, 2),
        )
        return output

    def _build_system_prompt(self) -> str:
        catalog = json.dumps(self.registry.catalog(), indent=2)
        return (
            f"{self.system_prompt.strip()}\n\n"
            f"Available tools:\n{catalog}\n"
        )

    def _build_user_payload(self, agent_input: AgentInput) -> str:
        parts: list[str] = []

        if agent_input.chat_summary:
            summary = str(agent_input.chat_summary.get("summary", "")).strip()
            if summary:
                parts.append(f"Conversation summary:\n{summary}")

        if agent_input.previous_messages:
            recent = agent_input.previous_messages[-4:]
            lines = []
            for message in recent:
                role = str(message.get("role", "unknown")).capitalize()
                content = str(message.get("message", "")).strip()
                if content:
                    lines.append(f"{role}: {content}")
            if lines:
                parts.append("Recent messages:\n" + "\n".join(lines))

        parts.append(f"Latest user message:\n{agent_input.message}")
        return "\n\n".join(parts)

    def _parse_decision(self, content: str) -> ToolDecision:
        raw = (content or "").strip()

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
            self.log_error("failed to parse decision JSON; defaulting to no tool")
            return ToolDecision(
                needs_tool=False,
                reason="Could not parse decision output; answering directly.",
            )

        if not isinstance(parsed, dict):
            return ToolDecision(
                needs_tool=False,
                reason="Invalid decision shape; answering directly.",
            )

        needs_tool = bool(parsed.get("needs_tool"))
        tool_name = parsed.get("tool_name")
        tool_args = parsed.get("tool_args") or {}
        reason = str(parsed.get("reason") or "").strip()

        if not isinstance(tool_args, dict):
            tool_args = {}

        if tool_name is not None:
            tool_name = str(tool_name).strip() or None

        if not needs_tool:
            return ToolDecision(
                needs_tool=False,
                tool_name=None,
                tool_args={},
                reason=reason or "No tool required.",
            )

        return ToolDecision(
            needs_tool=True,
            tool_name=tool_name,
            tool_args=tool_args,
            reason=reason or "Tool selected by decision agent.",
        )

    def _validate_against_registry(self, decision: ToolDecision) -> ToolDecision:
        if not decision.needs_tool:
            return decision

        if not decision.tool_name or not self.registry.has(decision.tool_name):
            self.log(
                "unknown or missing tool; falling back to no tool",
                tool_name=decision.tool_name,
            )
            return ToolDecision(
                needs_tool=False,
                tool_name=None,
                tool_args={},
                reason=(
                    f"Requested tool '{decision.tool_name}' is not registered; "
                    "answering directly."
                ),
            )

        return decision

    def evaluate(
        self,
        agent_input: AgentInput,
        agent_output: AgentOutput,
        latency_ms: float,
    ) -> None:
        decision: ToolDecision = agent_output.content
        self.log(
            "evaluation",
            latency_ms=round(latency_ms, 2),
            model=self.model,
            needs_tool=decision.needs_tool,
            tool_name=decision.tool_name,
            has_reason=bool(decision.reason),
            known_tool=(
                decision.tool_name is None
                or self.registry.has(decision.tool_name)
            ),
        )
