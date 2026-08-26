"""The ReAct loop itself: reason, act, observe -- repeat, then write up.

This is the engine. It owns the transcript and calls the tools, but it makes no
research decisions of its own: every "what next?" comes from the planner, and
every fact comes from a tool. Read `run_loop` top to bottom and you have seen how
essentially every LLM agent works.

The shape of one turn:

    1. ask the planner for a Decision   (reason)
    2. if it's 'finish', stop           (know when to quit)
    3. otherwise run the tool           (act)
    4. record what came back            (observe)

After the loop, the planner composes a cited answer, and -- if reflection is on --
criticises that draft once and may pull in one more source before finalising.
"""

from __future__ import annotations

from .planner import LoopState
from .schema import Report, Step
from .tools import Tools

SEARCH_K = 5  # how many results a search returns (the planner reads only the best few)


def run_loop(question, planner, tools: Tools, *, max_steps: int = 8, reflect: bool = True) -> Report:
    """Run the agent to completion and return a Report.

    `planner` decides; `tools` acts. `max_steps` is a hard stop so a confused agent
    can never loop forever -- a small but essential guard rail.
    """
    state = LoopState(question=question)

    for i in range(1, max_steps + 1):
        decision = planner.next_action(state)

        if decision.action == "finish":
            state.steps.append(Step(
                n=i, thought=decision.thought, action="finish",
                action_input="", observation="Ready to write the answer.",
            ))
            break

        if decision.action == "search":
            results = tools.search(decision.action_input, k=SEARCH_K)
            state.last_results = results
            obs = f"{len(results)} results: " + "; ".join(f"{r.locator} ({r.title})" for r in results)
            state.steps.append(Step(
                n=i, thought=decision.thought, action="search",
                action_input=decision.action_input, observation=obs,
            ))

        elif decision.action == "read":
            obs, page = _safe_read(tools, decision.action_input)
            if page is not None:
                state.gathered.append(page)
                state.read_locators.add(page.locator)
            state.steps.append(Step(
                n=i, thought=decision.thought, action="read",
                action_input=decision.action_input, observation=obs,
            ))
        else:  # an action we don't recognise -- stop rather than spin
            break

    answer, sources = planner.compose(question, state.gathered)
    reflection = None

    if reflect:
        critique, want_more = planner.reflect(question, answer, sources)
        reflection = critique
        # The stretch goal in action: if the critique says the draft is thin, read
        # one more unread source and rewrite -- but only if we have budget left.
        if want_more and len(state.steps) < max_steps:
            unread = [r for r in state.last_results if r.locator not in state.read_locators]
            if unread:
                obs, page = _safe_read(tools, unread[0].locator)
                if page is not None:
                    state.gathered.append(page)
                    state.read_locators.add(page.locator)
                state.steps.append(Step(
                    n=len(state.steps) + 1,
                    thought="My reflection flagged too few sources, so I'll read one more.",
                    action="read", action_input=unread[0].locator, observation=obs,
                ))
                answer, sources = planner.compose(question, state.gathered)
                reflection, _ = planner.reflect(question, answer, sources)

    return Report(question=question, answer=answer, sources=sources,
                  steps=state.steps, reflection=reflection)


def _safe_read(tools: Tools, locator: str):
    """Read a page, turning a failure into an observation instead of a crash."""
    try:
        page = tools.read(locator)
    except Exception as exc:  # noqa: BLE001  (a bad locator shouldn't kill the run)
        return f"Could not read {locator!r}: {exc}", None
    return f"Read '{page.title}' ({len(page.text)} characters).", page
