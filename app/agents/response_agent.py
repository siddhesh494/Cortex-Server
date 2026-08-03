from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.base import Agent
from app.agents.types import AgentInput, AgentOutput
from app.config import settings
from app.prompts.system_prompts import PROMPT_FOR_CHAT_RESPONSE


class ResponseAgent(Agent):
    """Produces the user-facing chat reply (sync or streamed)."""

    name = "response_agent"
    model = settings.RESPONSE_MODEL
    temperature = 0.0
    system_prompt = PROMPT_FOR_CHAT_RESPONSE

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        started = self.timed()
        self.log("generating response", model=self.model)

        messages = self._build_messages(agent_input)
        response = self.llm.invoke(messages)
        content = response.content

        output = AgentOutput(
            content=content,
            metadata={"chars": len(content)},
        )
        latency_ms = self.elapsed_ms(started)
        self.evaluate(agent_input, output, latency_ms)
        self.log(
            "response generated",
            latency_ms=round(latency_ms, 2),
            chars=len(content),
        )
        return output

    async def stream(self, agent_input: AgentInput):
        """Stream tokens for the same input shape as execute()."""
        started = self.timed()
        self.log("streaming response", model=self.model)
        char_count = 0

        messages = self._build_messages(agent_input)

        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if not content:
                continue

            if isinstance(content, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            else:
                text = str(content)

            if text:
                char_count += len(text)
                yield text

        latency_ms = self.elapsed_ms(started)
        self.evaluate(
            agent_input,
            AgentOutput(content=f"<streamed {char_count} chars>"),
            latency_ms,
        )
        self.log(
            "stream complete",
            latency_ms=round(latency_ms, 2),
            chars=char_count,
        )

    def _build_messages(self, agent_input: AgentInput) -> list:
        user_context = self._format_chat_summary(agent_input.chat_summary)
        chat_history = self._build_chat_history(agent_input.previous_messages)

        messages = [SystemMessage(content=self.system_prompt)]

        if user_context:
            messages.append(SystemMessage(content=user_context))

        if agent_input.tool_context:
            messages.append(SystemMessage(content=agent_input.tool_context))

        messages.extend(chat_history)
        messages.append(HumanMessage(content=agent_input.message))
        return messages

    def evaluate(
        self,
        agent_input: AgentInput,
        agent_output: AgentOutput,
        latency_ms: float,
    ) -> None:
        text = str(agent_output.content or "")
        self.log(
            "evaluation",
            latency_ms=round(latency_ms, 2),
            model=self.model,
            output_chars=len(text),
            non_empty=bool(text.strip()),
        )

    @staticmethod
    def _build_chat_history(previous_messages: list | None) -> list:
        if not previous_messages:
            return []

        chat_history = []
        for message in previous_messages:
            role = message.get("role")
            content = message.get("message", "")

            if role == "user":
                chat_history.append(HumanMessage(content=content))
            elif role == "assistant":
                chat_history.append(AIMessage(content=content))

        return chat_history

    @staticmethod
    def _format_chat_summary(chat_summary: dict | None) -> str | None:
        if not chat_summary:
            return None

        summary = str(chat_summary.get("summary", "")).strip()
        key_points = chat_summary.get("key_points") or []
        user_preference = str(chat_summary.get("user_preference", "")).strip()

        if not summary and not key_points and not user_preference:
            return None

        parts = ["Use this summary of earlier conversation for context:"]

        if summary:
            parts.append(summary)

        if key_points:
            parts.append("Key points:")
            parts.extend(f"- {point}" for point in key_points)

        if user_preference:
            parts.append("User preference:")
            parts.append(user_preference)
            parts.append("Adapt your response style to match these preferences.")

        return "\n".join(parts)
