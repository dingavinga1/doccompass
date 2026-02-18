from __future__ import annotations

import asyncio
import fnmatch
import importlib
import inspect
from collections import deque
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse


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


def _matches_patterns(url: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(url, pattern) for pattern in patterns)


def _can_visit(url: str, include_patterns: list[str], exclude_patterns: list[str]) -> bool:
    if exclude_patterns and _matches_patterns(url, exclude_patterns):
        return False
    if include_patterns:
        return _matches_patterns(url, include_patterns)
    return True


def _extract_links(result: object, source_url: str) -> list[str]:
    links: list[str] = []
    raw_links = getattr(result, "links", None)
    if isinstance(raw_links, dict):
        values = []
        for _, items in raw_links.items():
            if isinstance(items, list):
                values.extend(items)
        raw_links = values

    if isinstance(raw_links, list):
        for item in raw_links:
            href = None
            if isinstance(item, str):
                href = item
            elif isinstance(item, dict):
                href = item.get("href") or item.get("url")
            if href:
                links.append(urljoin(source_url, href))

    return links


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


def _build_run_config(crawl4ai_module: object, timeout_seconds: int):
    CrawlerRunConfig = getattr(crawl4ai_module, "CrawlerRunConfig")
    CacheMode = getattr(crawl4ai_module, "CacheMode", None)

    kwargs: dict[str, object] = {}
    params = inspect.signature(CrawlerRunConfig).parameters

    if "cache_mode" in params and CacheMode is not None and hasattr(CacheMode, "BYPASS"):
        kwargs["cache_mode"] = CacheMode.BYPASS
    if "page_timeout" in params:
        kwargs["page_timeout"] = timeout_seconds * 1000
    elif "timeout" in params:
        kwargs["timeout"] = timeout_seconds

    return CrawlerRunConfig(**kwargs)


async def _crawl_one(crawler: object, url: str, run_config: object) -> object:
    arun = getattr(crawler, "arun")
    params = inspect.signature(arun).parameters
    if "config" in params:
        return await arun(url=url, config=run_config)
    return await arun(url=url)


async def crawl_site(
    start_url: str,
    max_depth: int = 3,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    max_pages: int = 500,
    timeout_seconds: int = 30,
    retries: int = 2,
) -> list[CrawledPage]:
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    crawl4ai_module = importlib.import_module("crawl4ai")
    AsyncWebCrawler = getattr(crawl4ai_module, "AsyncWebCrawler")
    run_config = _build_run_config(crawl4ai_module, timeout_seconds)

    start_url = normalize_url(start_url)
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    visited: set[str] = set()
    pages: list[CrawledPage] = []

    async with AsyncWebCrawler() as crawler:
        while queue and len(pages) < max_pages:
            url, depth = queue.popleft()
            normalized = normalize_url(url)
            if normalized in visited:
                continue
            if depth > max_depth:
                continue
            if not _can_visit(normalized, include_patterns, exclude_patterns):
                continue

            visited.add(normalized)

            last_error: Exception | None = None
            result = None
            for _ in range(retries + 1):
                try:
                    result = await _crawl_one(crawler, normalized, run_config)
                    break
                except Exception as exc:  # pragma: no cover - retry path
                    last_error = exc
                    await asyncio.sleep(0.25)

            if result is None:
                if last_error is not None:
                    raise last_error
                continue

            if hasattr(result, "success") and not getattr(result, "success"):
                continue

            markdown = _extract_markdown(result)
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None)

            pages.append(CrawledPage(url=normalized, markdown=markdown, html=html, depth=depth))

            if depth >= max_depth:
                continue

            for link in _extract_links(result, normalized):
                absolute = normalize_url(link)
                if absolute in visited:
                    continue
                if not _can_visit(absolute, include_patterns, exclude_patterns):
                    continue
                queue.append((absolute, depth + 1))

    return pages
