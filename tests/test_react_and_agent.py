"""End-to-end tests of the loop and the public research() function (offline)."""

from __future__ import annotations

import re

from research_agent.agent import research
from research_agent.schema import Report


def test_research_returns_a_valid_report(question):
    report = research(question)
    assert isinstance(report, Report)
    assert report.question == question
    assert report.answer
    assert report.sources


def test_loop_searches_then_reads_then_finishes(question):
    report = research(question)
    actions = [s.action for s in report.steps]
    assert actions[0] == "search"       # always reason+search first
    assert "read" in actions            # it reads pages
    assert actions[-1] == "finish"      # and knows when to stop


def test_answer_only_cites_real_sources(question):
    report = research(question)
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", report.answer)}
    source_numbers = {s.n for s in report.sources}
    assert cited == source_numbers      # no dangling or invented citations


def test_it_reads_the_relevant_pages_not_the_distractors(question):
    report = research(question, max_reads=3)
    read = {s.locator for s in report.sources}
    assert "08_caffeine_and_sleep.txt" not in read
    assert "06_precious_coral_jewellery.txt" not in read


def test_reflection_pulls_an_extra_source_when_thin(question):
    # With max_reads=1 the first draft has one source; reflection should add a second.
    report = research(question, max_reads=1)
    assert len(report.sources) == 2
    assert any("reflection" in s.thought.lower() for s in report.steps)


def test_max_steps_is_respected(question):
    report = research(question, max_steps=2, reflect=False)
    assert len(report.steps) <= 2


def test_report_format_is_readable(question):
    text = research(question).format()
    assert "Sources:" in text
    assert "[1]" in text
