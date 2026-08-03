from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.base import Agent
from app.agents.types import AgentInput, AgentOutput
from app.config import settings
from app.prompts.system_prompts import (
    PROMPT_FOR_CHAT_TITLE,
    PROMPT_FOR_CHAT_TITLE_RETRY,
)

MAX_TITLE_WORDS = 5


class TitleAgent(Agent):
    """Generates a short sidebar-style title from the first user message."""

    name = "title_agent"
    model = settings.TITLE_MODEL
    temperature = 0.0
    system_prompt = PROMPT_FOR_CHAT_TITLE

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        started = self.timed()
        first_message = agent_input.message
        self.log("generating title", model=self.model)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=first_message),
        ]
        title = self.llm.invoke(messages).content.strip()

        if self._word_count(title) > MAX_TITLE_WORDS:
            self.log("title too long, retrying", word_count=self._word_count(title))
            messages.extend([
                AIMessage(content=title),
                HumanMessage(content=PROMPT_FOR_CHAT_TITLE_RETRY),
            ])
            title = self.llm.invoke(messages).content.strip()

        output = AgentOutput(
            content=title,
            metadata={"word_count": self._word_count(title)},
        )
        latency_ms = self.elapsed_ms(started)
        self.evaluate(agent_input, output, latency_ms)
        self.log("title generated", title=title, latency_ms=round(latency_ms, 2))
        return output

    def evaluate(
        self,
        agent_input: AgentInput,
        agent_output: AgentOutput,
        latency_ms: float,
    ) -> None:
        word_count = self._word_count(str(agent_output.content))
        self.log(
            "evaluation",
            latency_ms=round(latency_ms, 2),
            model=self.model,
            word_count=word_count,
            within_limit=word_count <= MAX_TITLE_WORDS,
        )

    @staticmethod
    def _word_count(text: str) -> int:
        return len(text.split())
