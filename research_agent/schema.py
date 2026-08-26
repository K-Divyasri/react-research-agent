"""The data shapes the agent produces, defined with pydantic.

An agent that just prints a paragraph is hard to trust and impossible to debug.
This project treats the agent's work as *structured data*: every step it takes,
every source it uses, and the final answer are typed objects. That gives you three
things at once -- a clean return value, automatic validation, and a full trace you
can inspect to see exactly why the agent said what it said.

  Step    one turn of the loop: a thought, the action taken, and what came back.
  Source  one page the agent cited, with the number used in the answer text.
  Report  the whole result: the question, the answer, the sources, the steps,
          and the one-line self-critique from the reflection pass.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from . import ACTIONS

Action = Literal["search", "read", "finish"]


class Step(BaseModel):
    """One turn of the ReAct loop: reason, then act, then observe."""

    n: int = Field(ge=1, description="Step number, starting at 1.")
    thought: str = Field(description="The agent's reasoning before it acted.")
    action: Action = Field(description="Which action it chose: search, read, or finish.")
    action_input: str = Field(default="", description="The query or the page id it acted on.")
    observation: str = Field(default="", description="A short summary of what the tool returned.")

    model_config = {"extra": "forbid"}


class Source(BaseModel):
    """A page the agent read and cited in its answer."""

    n: int = Field(ge=1, description="Citation number, matching the [n] markers in the answer.")
    title: str = Field(description="The page's title.")
    locator: str = Field(description="Where it came from: a corpus id offline, a URL for real search.")
    snippet: str = Field(default="", description="The sentence the agent pulled from this page.")

    model_config = {"extra": "forbid"}


class Report(BaseModel):
    """The finished piece of research."""

    question: str
    answer: str = Field(description="The cited summary, with [n] markers into `sources`.")
    sources: list[Source] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    reflection: Optional[str] = Field(
        default=None, description="The agent's one-line critique of its own draft."
    )

    model_config = {"extra": "forbid"}

    def format(self) -> str:
        """Render the report the way the CLI prints it: answer, then a source list."""
        lines = [self.answer.strip(), ""]
        if self.sources:
            lines.append("Sources:")
            for s in self.sources:
                lines.append(f"  [{s.n}] {s.title} ({s.locator})")
        if self.reflection:
            lines.append("")
            lines.append(f"Reflection: {self.reflection}")
        return "\n".join(lines)


# A tiny sanity check that the schema and the package agree on the action names.
assert set(Action.__args__) == set(ACTIONS)  # type: ignore[attr-defined]
