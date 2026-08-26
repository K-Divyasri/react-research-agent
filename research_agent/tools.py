"""The tools the agent can call: search the web, and read a page.

An "agent" is a language model plus a set of tools it is allowed to use. Here there
are exactly two, which is enough to do real research:

    search(query)     -> a ranked list of results (title + locator + preview)
    read(locator)     -> the full text of one result

The rest of the program never cares whether those tools hit a local folder or the
real internet. Both backends return the SAME two little objects -- `SearchResult`
and `PageContent` -- so the loop, the planner and the write-up work unchanged in
either mode. That uniform shape is the whole trick behind "runs offline, ships
online."

  OfflineTools   reads the bundled corpus (see corpus.py). No key, no network.
  RealTools      Tavily for search + trafilatura for page text. Needs API keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import corpus


@dataclass(frozen=True)
class SearchResult:
    """One search hit, backend-agnostic."""

    locator: str  # a corpus id offline, a URL online -- how you `read` it later
    title: str
    snippet: str


@dataclass(frozen=True)
class PageContent:
    """The text of one page."""

    locator: str
    title: str
    text: str


class Tools:
    """The interface both backends implement. The loop only knows about this."""

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        raise NotImplementedError

    def read(self, locator: str) -> PageContent:
        raise NotImplementedError


class OfflineTools(Tools):
    """Search and read against the local corpus. Deterministic, keyless, offline."""

    def __init__(self, corpus_dir: str | None = None) -> None:
        self.corpus_dir = corpus_dir

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        hits = corpus.search(query, k=k, corpus_dir=self.corpus_dir)
        return [SearchResult(locator=h.id, title=h.title, snippet=h.snippet) for h in hits]

    def read(self, locator: str) -> PageContent:
        page = corpus.get_page(locator, corpus_dir=self.corpus_dir)
        return PageContent(locator=page.id, title=page.title, text=page.text)


class RealTools(Tools):
    """Search the real web (Tavily) and read real pages (trafilatura).

    Everything here is imported lazily and only when you actually construct
    RealTools, so offline users never need tavily, trafilatura or httpx installed.
    Get a free Tavily key at https://tavily.com and put it in .env as TAVILY_API_KEY.
    """

    def __init__(self) -> None:
        if not os.environ.get("TAVILY_API_KEY"):
            raise RuntimeError(
                "RealTools needs TAVILY_API_KEY set (see .env.example). "
                "Use OfflineTools to run without a key."
            )

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        from tavily import TavilyClient  # noqa: PLC0415  (lazy on purpose)

        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        resp = client.search(query=query, max_results=k)
        out: list[SearchResult] = []
        for r in resp.get("results", []):
            out.append(
                SearchResult(
                    locator=r["url"],
                    title=r.get("title", r["url"]),
                    snippet=(r.get("content", "") or "")[:200],
                )
            )
        return out

    def read(self, locator: str) -> PageContent:
        import httpx  # noqa: PLC0415
        import trafilatura  # noqa: PLC0415

        html = httpx.get(locator, timeout=20, follow_redirects=True).text
        text = trafilatura.extract(html) or ""
        # trafilatura doesn't reliably give a title; fall back to the URL.
        return PageContent(locator=locator, title=locator, text=text.strip())


def make_tools(real: bool = False, corpus_dir: str | None = None) -> Tools:
    """Return the offline tools (default) or the real ones."""
    return RealTools() if real else OfflineTools(corpus_dir=corpus_dir)
