"""The offline 'mini-web': load the local corpus and search it.

This module stands in for the entire internet when the agent runs offline. It
loads the eight text files under `data/corpus/`, and offers two things the tools
need: a keyword `search` that ranks pages by how well they match a query, and
`get_page` to fetch one page's full text.

The search is deliberately simple -- it counts how many of the query's words appear
in each page, weighting rarer words higher -- but simple is the point. You can read
it, predict what it will return, and it is completely deterministic: the same query
always ranks the same pages in the same order. That is what lets the tests assert
exact behaviour. A real search engine is far cleverer; the *shape* (a query in, a
ranked list of results out) is identical.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Where the corpus lives. Resolved relative to this file so it works no matter
# what directory you run from.
CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "corpus"

# Words too common to be worth matching on. Keeping this list short and visible
# beats pulling in a big NLP dependency for a teaching project.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "is", "are", "was",
    "for", "with", "what", "why", "how", "does", "do", "it", "its", "that",
    "this", "as", "at", "by", "from", "be", "can", "you", "your", "about",
    "main", "into", "their", "they", "which",
}


@dataclass(frozen=True)
class Page:
    """One document in the corpus."""

    id: str  # the filename, e.g. "02_causes_of_bleaching.txt"
    title: str  # the first line of the file
    text: str  # the body


@dataclass(frozen=True)
class SearchHit:
    """One search result: which page, how well it scored, and a preview."""

    id: str
    title: str
    score: float
    snippet: str


def _tokenize(text: str) -> list[str]:
    """Lower-case, split into words of 3+ letters, drop stopwords."""
    words = re.findall(r"[a-z]{3,}", text.lower())
    return [w for w in words if w not in _STOPWORDS]


@lru_cache(maxsize=1)
def load_pages(corpus_dir: str | None = None) -> tuple[Page, ...]:
    """Load every .txt file in the corpus, sorted by filename (so order is fixed).

    Cached, because the corpus never changes during a run. The first line of each
    file is its title; the rest is the body.
    """
    directory = Path(corpus_dir) if corpus_dir else CORPUS_DIR
    pages: list[Page] = []
    for path in sorted(directory.glob("*.txt")):
        raw = path.read_text(encoding="utf-8").strip()
        title, _, body = raw.partition("\n")
        pages.append(Page(id=path.name, title=title.strip(), text=body.strip()))
    return tuple(pages)


def _idf(pages: tuple[Page, ...]) -> dict[str, float]:
    """Inverse document frequency: rare words score higher than common ones.

    A word that appears in one page is a strong signal; a word in every page tells
    you nothing. idf = log(total_pages / pages_containing_word) captures that.
    """
    n = len(pages)
    doc_tokens = [set(_tokenize(p.title + " " + p.text)) for p in pages]
    idf: dict[str, float] = {}
    vocab = set().union(*doc_tokens) if doc_tokens else set()
    for word in vocab:
        containing = sum(1 for toks in doc_tokens if word in toks)
        idf[word] = math.log((n + 1) / (containing + 1)) + 1.0
    return idf


def _best_snippet(page: Page, query_tokens: set[str]) -> str:
    """Return the sentence in `page` that overlaps the query the most.

    This is also how the agent later quotes a source: the single most on-topic
    sentence. Ties break toward the earlier sentence, keeping it deterministic.
    """
    sentences = re.split(r"(?<=[.!?])\s+", page.text.replace("\n", " "))
    best, best_score = sentences[0] if sentences else page.title, -1
    for sent in sentences:
        overlap = len(set(_tokenize(sent)) & query_tokens)
        if overlap > best_score:
            best, best_score = sent.strip(), overlap
    return best.strip()


def search(query: str, k: int = 3, corpus_dir: str | None = None) -> list[SearchHit]:
    """Return the top `k` pages for `query`, best first.

    Score = sum over the query's words of (times the word appears in the page)
    times (how rare the word is). Pages that match none of the query words are
    dropped entirely -- that's how the caffeine page stays out of a coral search.
    """
    pages = load_pages(corpus_dir)
    idf = _idf(pages)
    q_tokens = _tokenize(query)
    q_set = set(q_tokens)

    scored: list[SearchHit] = []
    for page in pages:
        counts = _tokenize(page.title + " " + page.text)
        score = sum(counts.count(w) * idf.get(w, 1.0) for w in q_set)
        if score <= 0:
            continue
        scored.append(SearchHit(page.id, page.title, round(score, 3), _best_snippet(page, q_set)))

    # Sort by score (high to low), tie-break by id so the order is fully fixed.
    scored.sort(key=lambda h: (-h.score, h.id))
    return scored[:k]


def get_page(page_id: str, corpus_dir: str | None = None) -> Page:
    """Fetch one page by its id. Raises KeyError if there's no such page."""
    for page in load_pages(corpus_dir):
        if page.id == page_id:
            return page
    raise KeyError(f"No page with id {page_id!r} in the corpus.")
