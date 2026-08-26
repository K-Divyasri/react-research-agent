"""Tests for the offline corpus search and read."""

from __future__ import annotations

import pytest

from research_agent import corpus


def test_all_pages_load():
    pages = corpus.load_pages()
    assert len(pages) == 8
    # Titles are the first line of each file, not the filename.
    assert any(p.title == "Causes of Coral Bleaching" for p in pages)


def test_search_ranks_relevant_pages_first(question):
    hits = corpus.search(question, k=3)
    top_ids = {h.id for h in hits}
    # The three genuinely on-topic pages should be the top three.
    assert top_ids == {
        "01_what_is_coral_bleaching.txt",
        "02_causes_of_bleaching.txt",
        "03_effects_on_reefs.txt",
    }


def test_unrelated_page_scores_low(question):
    hits = corpus.search(question, k=8)
    ids = [h.id for h in hits]
    # The caffeine page mentions "coral" once, so it may appear, but always last.
    if "08_caffeine_and_sleep.txt" in ids:
        assert ids[-1] == "08_caffeine_and_sleep.txt"


def test_search_is_deterministic(question):
    assert [h.id for h in corpus.search(question, 5)] == [h.id for h in corpus.search(question, 5)]


def test_get_page_and_missing():
    page = corpus.get_page("02_causes_of_bleaching.txt")
    assert "temperature" in page.text.lower()
    with pytest.raises(KeyError):
        corpus.get_page("does_not_exist.txt")
