"""ReAct Research Agent -- ask a question, get a cited answer.

Give this agent a research question and it works the way a careful person would:
it thinks about what to look up, searches, reads the promising pages, takes notes,
and -- when it has enough -- writes a short answer with numbered citations back to
the sources it actually used. Then it stops and criticises its own draft once.

The loop it follows has a name: ReAct, short for Reason + Act. Every turn is a
thought (reason), then a tool call (act), then the tool's result (observe). That
loop is the beating heart of almost every LLM "agent," which is why it's worth
building one by hand.

The public pieces:

    agent.research(question)   run the whole loop, return a Report
    schema.Report              the result: answer, sources, and every step taken
    tools                      the two tools the agent can call: search, read
    corpus                     the offline 'mini-web' the tools read from

Everything runs OFFLINE by default: a deterministic planner drives the loop over a
small local corpus, so notebooks, labs and tests need no API key and no network.
Pass real=True (and set a key) to swap in a real language model and real web search.
"""

from __future__ import annotations

__version__ = "1.0.0"

# The three actions the agent is allowed to take. "search" and "read" are tools;
# "finish" ends the loop and triggers the write-up.
ACTIONS = ("search", "read", "finish")
