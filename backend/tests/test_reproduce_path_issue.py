
from app.services.parser import parse_sections, MIN_SECTION_TOKENS
from app.services.crawler import CrawledPage


def test_reproduce_path_issue():
    """URL path is used as root — no protocol/domain slugs appear in paths."""
    url = "https://fastapi.tiangolo.com/fastapi/dependencies/without-standard-dependencies/"
    markdown = """
# Dependencies

## Without Standard Dependencies

Some content here.
    """

    page = CrawledPage(
        url=url,
        markdown=markdown,
        html="",
        depth=1,
    )

    sections = parse_sections([page])

    for section in sections:
        # Path must NOT contain the protocol/domain slug
        assert "httpsfastapi" not in section.path, (
            f"Path '{section.path}' contains redundant URL parts."
        )

        # Path must start with the URL path root
        expected_root = "/fastapi/dependencies/without-standard-dependencies"
        assert section.path.startswith(expected_root), (
            f"Path '{section.path}' does not start with expected root '{expected_root}'"
        )


def test_reproduce_permalink_issue():
    """Permalink symbols and markdown links are stripped from H1 titles.

    This is a small page (< MIN_SECTION_TOKENS), so it becomes a single flat
    section at root_path = '/tutorial/dependencies'.
    """
    url = "https://fastapi.tiangolo.com/tutorial/dependencies/"
    markdown = """
# Dependencies[\u00b6](https://fastapi.tiangolo.com/#dependencies)

Some content.
    """

    assert len(markdown.split()) < MIN_SECTION_TOKENS, (
        "This test assumes the page is below MIN_SECTION_TOKENS so the flat-section path applies"
    )

    page = CrawledPage(
        url=url,
        markdown=markdown,
        html="",
        depth=1,
    )

    sections = parse_sections([page])
    section = sections[0]

    # Title must be clean — no permalink, no markdown link syntax
    assert section.title == "Dependencies"

    # Small page → single flat section keyed by URL path
    assert section.path == "/tutorial/dependencies", (
        f"Expected '/tutorial/dependencies' (flat-section path) but got '{section.path}'"
    )
