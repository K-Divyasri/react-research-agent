"""The agent's brain: decide the next action, then write the answer.

The loop in react.py handles the mechanics -- keeping the transcript, calling the
tools -- but it never decides anything itself. Every decision comes from a
`Planner`. That separation is deliberate: swap the planner and the same loop
becomes a different agent.

Two planners implement the same three methods:

    next_action(state)   look at the question and what's happened, choose search /
                         read / finish.
    compose(...)         turn the pages that were read into a cited answer.
    reflect(...)         criticise the draft; optionally ask for one more source.

  OfflinePlanner   a deterministic, rule-based policy. No model, no key. It plays
                   a sensible research strategy: search once, read the top few
                   hits, then finish -- and its reflection pass will pull an extra
                   source if the draft leans on too few.
  RealPlanner      a real language model via LiteLLM, prompted in the classic ReAct
                   "Thought / Action / Action Input" format and parsed back out.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from .schema import Source
from .tools import PageContent, SearchResult

# Reuse the corpus tokenizer so "best sentence" scoring matches search scoring.
from .corpus import _tokenize  # noqa: PLC2701  (internal but intentional reuse)


@dataclass
class Decision:
    """What the planner wants to do next."""

    thought: str
    action: str  # "search" | "read" | "finish"
    action_input: str = ""


@dataclass
class LoopState:
    """Everything the planner is allowed to look at when deciding.

    The loop fills this in as it goes and hands it to the planner each turn.
    """

    question: str
    steps: list = field(default_factory=list)  # list[schema.Step]
    last_results: list[SearchResult] = field(default_factory=list)
    gathered: list[PageContent] = field(default_factory=list)
    read_locators: set[str] = field(default_factory=set)


def best_sentence(text: str, question: str) -> str:
    """The single sentence in `text` that best matches the question's words.

    This is how a source gets quoted: pick its most on-topic sentence. Ties break
    to the earlier sentence, so the choice is deterministic.
    """
    q = set(_tokenize(question))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]
    if not sentences:
        return text.strip()
    best, best_score = sentences[0], -1
    for sent in sentences:
        overlap = len(set(_tokenize(sent)) & q)
        if overlap > best_score:
            best, best_score = sent, overlap
    return best


# --------------------------------------------------------------------------- #
#  Offline planner: a deterministic research strategy                         #
# --------------------------------------------------------------------------- #
class OfflinePlanner:
    """A rule-based ReAct policy. Predictable, keyless, good enough to teach on."""

    def __init__(self, max_reads: int = 3, min_sources: int = 2) -> None:
        self.max_reads = max_reads
        self.min_sources = min_sources

    def next_action(self, state: LoopState) -> Decision:
        searched = any(s.action == "search" for s in state.steps)
        if not searched:
            return Decision(
                thought="I don't know the answer yet, so I'll search for the question.",
                action="search",
                action_input=state.question,
            )
        unread = [r for r in state.last_results if r.locator not in state.read_locators]
        if len(state.gathered) < self.max_reads and unread:
            nxt = unread[0]
            return Decision(
                thought=f"'{nxt.title}' looks relevant. I'll read it to get the details.",
                action="read",
                action_input=nxt.locator,
            )
        return Decision(
            thought="I've read the most relevant pages. I have enough to write the answer.",
            action="finish",
        )

    def compose(self, question: str, gathered: list[PageContent]) -> tuple[str, list[Source]]:
        """Build a cited answer: one quoted sentence per source, numbered [1], [2]..."""
        parts: list[str] = []
        sources: list[Source] = []
        for i, page in enumerate(gathered, start=1):
            sent = best_sentence(page.text, question)
            parts.append(f"{sent} [{i}]")
            sources.append(Source(n=i, title=page.title, locator=page.locator, snippet=sent))
        answer = " ".join(parts) if parts else "I could not find anything relevant to the question."
        return answer, sources

    def reflect(self, question: str, answer: str, sources: list[Source]) -> tuple[str, bool]:
        """Critique the draft. Return (one-line critique, want_one_more_source)."""
        if len(sources) < self.min_sources:
            return (
                f"The draft rests on only {len(sources)} source. I should read one more "
                "to corroborate before finishing.",
                True,
            )
        cited = set(int(n) for n in re.findall(r"\[(\d+)\]", answer))
        if cited != {s.n for s in sources}:
            return ("Some claims aren't cited cleanly; the citations should match the sources.", False)
        return (
            f"The answer draws on {len(sources)} sources and every claim carries a citation. "
            "It holds up.",
            False,
        )


# --------------------------------------------------------------------------- #
#  Real planner: a language model via LiteLLM, in ReAct format                #
# --------------------------------------------------------------------------- #
DEFAULT_MODEL = os.environ.get("AGENT_MODEL", "gemini/gemini-1.5-flash")

_REACT_SYSTEM = """\
You are a research agent that answers a question by using tools. Work in a loop.
On each turn, output EXACTLY three lines and nothing else:

Thought: <your reasoning about what to do next>
Action: <one of: search, read, finish>
Action Input: <the search query, or the exact locator of a result to read, or empty to finish>

Use `search` to find pages, `read` to open one by its locator, and `finish` when
you have read enough to answer. Read at least two sources before finishing.
"""


class RealPlanner:
    """Drive the loop with a real LLM. Reasoning is the model's; parsing is ours."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or DEFAULT_MODEL

    def _complete(self, messages: list[dict]) -> str:
        from litellm import completion  # noqa: PLC0415  (lazy on purpose)

        resp = completion(model=self.model, messages=messages, temperature=0)
        return resp.choices[0].message.content or ""

    def next_action(self, state: LoopState) -> Decision:
        transcript = _render_transcript(state)
        messages = [
            {"role": "system", "content": _REACT_SYSTEM},
            {"role": "user", "content": f"Question: {state.question}\n\n{transcript}\nYour turn:"},
        ]
        return _parse_decision(self._complete(messages))

    def compose(self, question: str, gathered: list[PageContent]) -> tuple[str, list[Source]]:
        numbered = "\n\n".join(
            f"[{i}] {p.title} ({p.locator})\n{p.text}" for i, p in enumerate(gathered, start=1)
        )
        messages = [
            {"role": "system", "content": (
                "Write a short, accurate answer to the question using ONLY the numbered "
                "sources. Put a [n] citation after every claim, matching the source number. "
                "Do not invent facts.")},
            {"role": "user", "content": f"Question: {question}\n\nSources:\n{numbered}\n\nAnswer:"},
        ]
        answer = self._complete(messages).strip()
        sources = [
            Source(n=i, title=p.title, locator=p.locator, snippet=best_sentence(p.text, question))
            for i, p in enumerate(gathered, start=1)
        ]
        return answer, sources

    def reflect(self, question: str, answer: str, sources: list[Source]) -> tuple[str, bool]:
        messages = [
            {"role": "system", "content": (
                "You are a strict editor. In ONE sentence, say whether the answer is well "
                "supported by its citations. Start that sentence with either 'OK:' or 'WEAK:'.")},
            {"role": "user", "content": f"Question: {question}\nAnswer: {answer}"},
        ]
        critique = self._complete(messages).strip().splitlines()[0] if answer else "WEAK: empty answer"
        return critique, critique.upper().startswith("WEAK") and len(sources) < 3


def _render_transcript(state: LoopState) -> str:
    """Turn the steps so far into text the model can read as its own history."""
    if not state.steps:
        return "(no steps yet)"
    lines = []
    for s in state.steps:
        lines.append(f"Thought: {s.thought}\nAction: {s.action}\nAction Input: {s.action_input}")
        lines.append(f"Observation: {s.observation}")
    return "\n".join(lines)


def _parse_decision(raw: str) -> Decision:
    """Pull Thought / Action / Action Input out of the model's reply, with fallbacks."""
    thought = _grab(raw, "thought") or "(no thought given)"
    action = (_grab(raw, "action") or "finish").lower().strip()
    action = next((a for a in ("search", "read", "finish") if a in action), "finish")
    action_input = _grab(raw, "action input") or ""
    return Decision(thought=thought, action=action, action_input=action_input.strip())


def _grab(text: str, label: str) -> str | None:
    m = re.search(rf"{label}\s*:\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else None
