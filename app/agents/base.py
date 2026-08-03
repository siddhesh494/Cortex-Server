from abc import ABC, abstractmethod
import logging
import time
from typing import Any

from langchain_groq import ChatGroq

from app.agents.types import AgentInput, AgentOutput
from app.config import settings

logger = logging.getLogger("fastapi-backend")


class Agent(ABC):
    """
    Common agent interface.

    Subclasses declare name / model / system_prompt and implement execute().
    Model and temperature can be overridden via constructor or settings —
    swap models without rewriting agent logic.
    """

    name: str = "agent"
    model: str = settings.MODEL_NAME
    system_prompt: str = ""
    temperature: float = 0.0

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        if model is not None:
            self.model = model
        if temperature is not None:
            self.temperature = temperature

        self.llm = ChatGroq(
            model=self.model,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=self.temperature,
        )
        self.log("initialized", model=self.model, temperature=self.temperature)

    @abstractmethod
    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Run the agent for one turn. Subclasses must implement this."""

    def log(self, message: str, **extra: Any) -> None:
        details = " ".join(f"{key}={value}" for key, value in extra.items())
        suffix = f" | {details}" if details else ""
        logger.info(f"[{self.name}] {message}{suffix}")

    def log_error(self, message: str, **extra: Any) -> None:
        details = " ".join(f"{key}={value}" for key, value in extra.items())
        suffix = f" | {details}" if details else ""
        logger.error(f"[{self.name}] {message}{suffix}")

    def evaluate(
        self,
        agent_input: AgentInput,
        agent_output: AgentOutput,
        latency_ms: float,
    ) -> None:
        """
        Lightweight evaluation hook.

        Override per agent to score outputs (length, schema validity, etc.).
        """
        self.log(
            "evaluation",
            latency_ms=round(latency_ms, 2),
            model=self.model,
            output_type=type(agent_output.content).__name__,
        )

    def timed(self) -> float:
        return time.perf_counter()

    def elapsed_ms(self, started_at: float) -> float:
        return (time.perf_counter() - started_at) * 1000
