import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import crawler


class FakeResult:
    def __init__(
        self,
        url: str,
        markdown: str,
        html: str = "",
        success: bool = True,
        depth: int = 0,
    ):
        self.url = url
        self.success = success
        self.markdown = markdown
        self.html = html
        self.metadata = {"depth": depth}


def test_normalize_url_removes_fragment_and_query_and_trailing_slash():
    assert crawler.normalize_url("https://example.com/docs/?x=1#frag") == "https://example.com/docs"


def test_crawl_site_returns_crawled_pages():
    """Ensure crawl_site maps Crawl4AI results to CrawledPage objects."""
    fake_results = [
        FakeResult(url="https://example.com", markdown="# Home", depth=0),
        FakeResult(url="https://example.com/a", markdown="# A", depth=1),
    ]

    fake_crawler = MagicMock()
    fake_crawler.__aenter__ = AsyncMock(return_value=fake_crawler)
    fake_crawler.__aexit__ = AsyncMock(return_value=False)
    fake_crawler.arun = AsyncMock(return_value=fake_results)

    with patch.object(crawler, "AsyncWebCrawler", return_value=fake_crawler):
        pages = asyncio.run(
            crawler.crawl_site(
                start_url="https://example.com",
                max_depth=1,
            )
        )

    assert len(pages) == 2
    assert pages[0].url == "https://example.com"
    assert pages[0].markdown == "# Home"
    assert pages[0].depth == 0
    assert pages[1].url == "https://example.com/a"
    assert pages[1].depth == 1


def test_crawl_site_skips_unsuccessful_results():
    """Results with success=False should not appear in output."""
    fake_results = [
        FakeResult(url="https://example.com", markdown="# Home", depth=0),
        FakeResult(url="https://example.com/bad", markdown="", depth=1, success=False),
    ]

    fake_crawler = MagicMock()
    fake_crawler.__aenter__ = AsyncMock(return_value=fake_crawler)
    fake_crawler.__aexit__ = AsyncMock(return_value=False)
    fake_crawler.arun = AsyncMock(return_value=fake_results)

    with patch.object(crawler, "AsyncWebCrawler", return_value=fake_crawler):
        pages = asyncio.run(
            crawler.crawl_site(start_url="https://example.com")
        )

    assert len(pages) == 1
    assert pages[0].url == "https://example.com"


def test_crawl_site_optional_max_depth_and_max_pages():
    """max_depth=None and max_pages=None should not pass those to strategy."""
    fake_results = [
        FakeResult(url="https://example.com", markdown="# Home", depth=0),
    ]

    fake_crawler = MagicMock()
    fake_crawler.__aenter__ = AsyncMock(return_value=fake_crawler)
    fake_crawler.__aexit__ = AsyncMock(return_value=False)
    fake_crawler.arun = AsyncMock(return_value=fake_results)

    with patch.object(crawler, "AsyncWebCrawler", return_value=fake_crawler):
        pages = asyncio.run(
            crawler.crawl_site(
                start_url="https://example.com",
                max_depth=None,
                max_pages=None,
            )
        )

    assert len(pages) == 1


def test_exclude_pattern_filter():
    """_ExcludePatternFilter should reject matching URLs."""
    f = crawler._ExcludePatternFilter(patterns=["*example.com/b*"])
    assert f.apply("https://example.com/a") is True
    assert f.apply("https://example.com/b") is False
    assert f.apply("https://example.com/b/deep") is False


def test_build_filter_chain_returns_none_when_no_patterns():
    assert crawler._build_filter_chain([], []) is None


def test_build_filter_chain_with_include_patterns():
    chain = crawler._build_filter_chain(["*docs*"], [])
    assert chain is not None


def test_build_filter_chain_with_exclude_patterns():
    chain = crawler._build_filter_chain([], ["*old*"])
    assert chain is not None


def test_build_filter_chain_with_both_patterns():
    chain = crawler._build_filter_chain(["*docs*"], ["*old*"])
    assert chain is not None
