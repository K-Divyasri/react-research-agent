"""Tests for the tool layer (offline backend)."""

from __future__ import annotations

from research_agent.tools import OfflineTools, PageContent, SearchResult, make_tools


def test_offline_search_returns_search_results(question):
    results = make_tools(real=False).search(question, k=3)
    assert len(results) == 3
    assert all(isinstance(r, SearchResult) for r in results)
    # locator offline is the corpus id, which is what you `read` next.
    assert results[0].locator.endswith(".txt")


def test_offline_read_returns_page_content():
    page = OfflineTools().read("01_what_is_coral_bleaching.txt")
    assert isinstance(page, PageContent)
    assert page.title == "What Is Coral Bleaching?"
    assert "zooxanthellae" in page.text.lower()


def test_make_tools_defaults_to_offline():
    assert isinstance(make_tools(), OfflineTools)
