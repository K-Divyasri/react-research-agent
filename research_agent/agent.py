"""The one function most people call: research(question) -> Report.

This ties the three pieces together -- a planner (the brain), the tools (search and
read), and the loop that runs them -- and hides the wiring. Offline by default, so
it just works with no key; pass real=True to use a live model and real web search.
"""

from __future__ import annotations

from .planner import OfflinePlanner, RealPlanner
from .react import run_loop
from .schema import Report
from .tools import make_tools


def research(
    question: str,
    *,
    real: bool = False,
    model: str | None = None,
    max_steps: int = 8,
    max_reads: int = 3,
    reflect: bool = True,
    corpus_dir: str | None = None,
) -> Report:
    """Answer `question` with a cited Report.

    real=False (default) runs the deterministic offline agent over the local corpus.
    real=True uses a language model (LiteLLM) and real web search (Tavily) -- needs
    API keys; see .env.example.

    max_reads   how many sources the offline agent reads before finishing.
    max_steps   a hard cap on loop turns, so the agent can never run forever.
    reflect     whether to run the self-critique pass at the end.
    """
    tools = make_tools(real=real, corpus_dir=corpus_dir)
    planner = RealPlanner(model=model) if real else OfflinePlanner(max_reads=max_reads)
    return run_loop(question, planner, tools, max_steps=max_steps, reflect=reflect)
