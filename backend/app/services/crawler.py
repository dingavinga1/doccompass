from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter


@dataclass(slots=True)
class CrawledPage:
    url: str
    markdown: str
    html: str | None
    depth: int


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path
    if path == "/":
        path = ""
    elif path.endswith("/"):
        path = path.rstrip("/")
    cleaned = parsed._replace(fragment="", query="", path=path)
    return urlunparse(cleaned)


class _ExcludePatternFilter:
    """Filter that *rejects* URLs matching any of the given glob patterns.

    Crawl4AI's built-in ``URLPatternFilter`` is include-only (accept on
    match).  This thin wrapper inverts that logic so we can express
    ``exclude_patterns`` without a custom subclass.
    """

    def __init__(self, patterns: list[str]) -> None:
        self._patterns = patterns

    def apply(self, url: str) -> bool:  # noqa: D401
        """Return ``True`` (keep) when the URL does *not* match any pattern."""
        return not any(fnmatch.fnmatch(url, p) for p in self._patterns)


def _extract_markdown(result: object) -> str:
    markdown = getattr(result, "markdown", "")
    if isinstance(markdown, str):
        return markdown
    if markdown is None:
        return ""

    fit_markdown = getattr(markdown, "fit_markdown", None)
    raw_markdown = getattr(markdown, "raw_markdown", None)
    if isinstance(fit_markdown, str) and fit_markdown:
        return fit_markdown
    if isinstance(raw_markdown, str):
        return raw_markdown
    return str(markdown)


def _build_filter_chain(
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> FilterChain | None:
    """Build a Crawl4AI ``FilterChain`` from include/exclude glob lists."""
    filters: list[object] = []

    if include_patterns:
        filters.append(URLPatternFilter(patterns=include_patterns))
    if exclude_patterns:
        filters.append(_ExcludePatternFilter(patterns=exclude_patterns))

    return FilterChain(filters) if filters else None


async def crawl_site(
    start_url: str,
    max_depth: int | None = 3,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    max_pages: int | None = 500,
    timeout_seconds: int = 30,
    retries: int = 2,
) -> list[CrawledPage]:
    """Crawl a documentation site using Crawl4AI's BFS deep crawl strategy.

    Parameters
    ----------
    start_url:
        Root URL to begin crawling.
    max_depth:
        Maximum depth of links to follow (``None`` for unlimited).
    include_patterns:
        Glob patterns — only URLs matching at least one pattern are
        followed.
    exclude_patterns:
        Glob patterns — URLs matching any pattern are skipped.
    max_pages:
        Hard cap on total pages crawled (``None`` for unlimited).
    timeout_seconds:
        Per-page timeout in milliseconds (passed as ``page_timeout``).
    retries:
        Kept for backward compatibility; Crawl4AI handles retries
        internally.
    """
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    start_url = normalize_url(start_url)

    filter_chain = _build_filter_chain(include_patterns, exclude_patterns)

    # ── Strategy ────────────────────────────────────────────────────
    strategy_kwargs: dict[str, object] = {
        "max_depth": max_depth if max_depth is not None else 100,
        "include_external": False,
    }
    if max_pages is not None:
        strategy_kwargs["max_pages"] = max_pages
    if filter_chain is not None:
        strategy_kwargs["filter_chain"] = filter_chain

    strategy = BFSDeepCrawlStrategy(**strategy_kwargs)

    # ── Run config ──────────────────────────────────────────────────
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        page_timeout=timeout_seconds * 1000,
        stream=False,
    )

    # ── Crawl ───────────────────────────────────────────────────────
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(start_url, config=config)

    # Ensure we always work with a list (single-page fallback)
    if not isinstance(results, list):
        results = [results]

    pages: list[CrawledPage] = []
    for result in results:
        if hasattr(result, "success") and not getattr(result, "success"):
            continue

        markdown = _extract_markdown(result)
        html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)
        depth = 0
        if hasattr(result, "metadata") and isinstance(result.metadata, dict):
            depth = result.metadata.get("depth", 0)

        pages.append(
            CrawledPage(
                url=getattr(result, "url", start_url),
                markdown=markdown,
                html=html,
                depth=depth,
            )
        )

    return pages
