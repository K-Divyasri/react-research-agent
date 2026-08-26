"""Tests for the offline planner's decisions and write-up."""

from __future__ import annotations

from research_agent.planner import LoopState, OfflinePlanner, best_sentence
from research_agent.schema import Source, Step
from research_agent.tools import PageContent, SearchResult


def test_first_move_is_always_search(question):
    planner = OfflinePlanner()
    decision = planner.next_action(LoopState(question=question))
    assert decision.action == "search"
    assert decision.action_input == question


def test_after_search_it_reads_the_top_hit(question):
    planner = OfflinePlanner()
    state = LoopState(question=question)
    state.steps.append(Step(n=1, thought="t", action="search", action_input=question, observation="o"))
    state.last_results = [
        SearchResult("a.txt", "A", "..."),
        SearchResult("b.txt", "B", "..."),
    ]
    decision = planner.next_action(state)
    assert decision.action == "read"
    assert decision.action_input == "a.txt"


def test_it_finishes_once_enough_is_read(question):
    planner = OfflinePlanner(max_reads=1)
    state = LoopState(question=question)
    state.steps.append(Step(n=1, thought="t", action="search", action_input=question, observation="o"))
    state.last_results = [SearchResult("a.txt", "A", "...")]
    state.gathered = [PageContent("a.txt", "A", "text")]
    state.read_locators = {"a.txt"}
    assert planner.next_action(state).action == "finish"


def test_compose_numbers_and_cites_every_source(question):
    planner = OfflinePlanner()
    gathered = [
        PageContent("02_causes_of_bleaching.txt", "Causes",
                    "The primary cause of coral bleaching is rising sea surface temperatures."),
        PageContent("03_effects_on_reefs.txt", "Effects",
                    "The main effects of coral bleaching are a loss of biodiversity."),
    ]
    answer, sources = planner.compose(question, gathered)
    assert "[1]" in answer and "[2]" in answer
    assert [s.n for s in sources] == [1, 2]
    assert all(isinstance(s, Source) for s in sources)


def test_reflection_flags_a_thin_draft(question):
    planner = OfflinePlanner(min_sources=2)
    _, want_more = planner.reflect(question, "Only one thing. [1]", [Source(n=1, title="A", locator="a")])
    assert want_more is True


def test_reflection_passes_a_well_cited_draft(question):
    planner = OfflinePlanner(min_sources=2)
    sources = [Source(n=1, title="A", locator="a"), Source(n=2, title="B", locator="b")]
    critique, want_more = planner.reflect(question, "Claim one [1]. Claim two [2].", sources)
    assert want_more is False
    assert "holds up" in critique


def test_best_sentence_picks_the_on_topic_one(question):
    text = "Bananas are yellow. The primary cause of coral bleaching is warm water."
    assert "coral bleaching" in best_sentence(text, question)
