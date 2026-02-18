import asyncio
from types import SimpleNamespace

from app.services import crawler


class FakeCrawlerRunConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeResult:
    def __init__(self, markdown: str, links: list[str], html: str = "", success: bool = True):
        self.success = success
        self.markdown = markdown
        self.links = [{"href": link} for link in links]
        self.html = html


class FakeAsyncWebCrawler:
    def __init__(self):
        self._results = {
            "https://example.com": FakeResult("# Home", ["/a", "/b"]),
            "https://example.com/a": FakeResult("# A", ["/c"]),
            "https://example.com/b": FakeResult("# B", []),
            "https://example.com/c": FakeResult("# C", []),
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def arun(self, url, config=None):
        return self._results[url]


def test_normalize_url_removes_fragment_and_query_and_trailing_slash():
    assert crawler.normalize_url("https://example.com/docs/?x=1#frag") == "https://example.com/docs"


def test_crawl_site_respects_depth_and_filters(monkeypatch):
    fake_module = SimpleNamespace(
        AsyncWebCrawler=FakeAsyncWebCrawler,
        CrawlerRunConfig=FakeCrawlerRunConfig,
        CacheMode=SimpleNamespace(BYPASS="bypass"),
    )
    monkeypatch.setattr(crawler.importlib, "import_module", lambda name: fake_module)

    pages = asyncio.run(
        crawler.crawl_site(
            start_url="https://example.com",
            max_depth=1,
            include_patterns=["https://example.com*"],
            exclude_patterns=["*example.com/b"],
        )
    )

    crawled_urls = {page.url for page in pages}
    assert "https://example.com" in crawled_urls
    assert "https://example.com/a" in crawled_urls
    assert "https://example.com/b" not in crawled_urls
    assert "https://example.com/c" not in crawled_urls
