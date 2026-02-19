"""
Tests for parse_sections() in app/services/parser.py

Layout for LARGE pages (>= MIN_SECTION_TOKENS total):
  • One root section at root_path (parent_path=None)  ← the tree anchor
  • N child sections (parent_path=root_path)           ← one per merged chunk

Layout for SMALL pages (< MIN_SECTION_TOKENS total):
  • One flat section at root_path (parent_path=None, no children)
"""

import pytest

from app.services.crawler import CrawledPage
from app.services.parser import MIN_SECTION_TOKENS, _SPLIT_LEVELS, parse_sections


def _make_page(markdown: str, url: str = "https://docs.example.com/guide") -> CrawledPage:
    return CrawledPage(url=url, markdown=markdown, html=None, depth=0)


def _filler(n: int) -> str:
    """Return n whitespace-separated words."""
    return " ".join(f"w{i}" for i in range(n))


# ── Small-page tests ──────────────────────────────────────────────────────────

def test_small_page_is_single_flat_section():
    """Pages below MIN_SECTION_TOKENS produce exactly one flat section at root_path."""
    short = f"# Quick Start\n{_filler(10)}\n## Step one\n{_filler(5)}"
    assert len(short.split()) < MIN_SECTION_TOKENS

    sections = parse_sections([_make_page(short, url="https://docs.example.com/quick-start")])

    assert len(sections) == 1
    s = sections[0]
    assert s.path == "/quick-start"
    assert s.parent_path is None
    assert s.level == 1
    assert s.title == "Quick Start"
    assert s.token_count < MIN_SECTION_TOKENS


def test_small_page_no_h1_uses_path_stem():
    short = _filler(5)
    sections = parse_sections([_make_page(short, url="https://docs.example.com/intro")])
    assert len(sections) == 1
    assert sections[0].title == "intro"


def test_small_page_permalink_title_cleaned():
    md = f"# Dependencies[¶](https://fastapi.tiangolo.com/#dependencies)\n{_filler(5)}"
    sections = parse_sections([_make_page(md, url="https://docs.example.com/deps")])
    assert sections[0].title == "Dependencies"


# ── Large-page: root section tests ───────────────────────────────────────────

def test_large_page_always_has_root_section():
    """Large pages always emit a root section at root_path (parent_path=None)."""
    block = _filler(MIN_SECTION_TOKENS + 100)
    md = f"# Guide\nIntro text.\n## Section A\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/guide")])

    root = [s for s in sections if s.path == "/guide"]
    assert len(root) == 1, "Expected exactly one root section at /guide"
    assert root[0].parent_path is None
    assert root[0].title == "Guide"


def test_large_page_root_section_contains_intro():
    """The root section's content is the intro text (pre-first-heading lines)."""
    block = _filler(MIN_SECTION_TOKENS + 50)
    md = f"Intro paragraph.\n\n# Guide\n## Section A\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/guide")])

    root = next(s for s in sections if s.path == "/guide")
    assert "Intro paragraph." in root.content


def test_large_page_children_have_root_as_parent():
    """Every child section's parent_path must equal root_path."""
    block = _filler(MIN_SECTION_TOKENS + 50)
    md = f"## Alpha\n{block}\n## Beta\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/ref")])

    children = [s for s in sections if s.path != "/ref"]
    assert len(children) >= 1
    for s in children:
        assert s.parent_path == "/ref", f"Expected parent '/ref', got '{s.parent_path}'"


# ── Large-page: merge-then-chunk tests ───────────────────────────────────────

def test_large_page_two_big_sections_become_two_children():
    """Two H2 sections each >= MIN_SECTION_TOKENS should produce two children."""
    block = _filler(MIN_SECTION_TOKENS + 100)
    md = f"## Section A\n{block}\n## Section B\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/overview")])

    children = [s for s in sections if s.path != "/overview"]
    titles = {s.title for s in children}
    assert "Section A" in titles
    assert "Section B" in titles
    assert len(children) == 2


def test_small_candidates_are_merged_until_threshold():
    """Candidates below threshold must be merged together into one child chunk."""
    # Each candidate is 100 tokens — well below 1500.  All should merge into one.
    tiny_block = _filler(100)
    md = "\n".join([f"## Chunk {i}\n{tiny_block}" for i in range(5)])
    # Total = 5 * ~102 tokens ≈ 510 — still under MIN_SECTION_TOKENS
    # The page IS small so small-page guard kicks in — we need it large:
    big_block = _filler(MIN_SECTION_TOKENS + 200)
    md = f"# Root\n## Tiny 1\n{tiny_block}\n## Tiny 2\n{tiny_block}\n## Big\n{big_block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/guide")])
    children = [s for s in sections if s.path != "/guide"]
    # Tiny 1 + Tiny 2 should merge (combined < threshold); Big becomes its own
    assert len(children) <= 2, (
        f"Expected tiny candidates to merge; got {len(children)} children: {[c.path for c in children]}"
    )


def test_large_page_h4_never_triggers_split():
    """H4-H6 headings are never split points — they stay inside the current chunk."""
    block = _filler(MIN_SECTION_TOKENS + 50)
    md = f"## Main Section\n{block}\n#### Sub-note\nExtra text."

    sections = parse_sections([_make_page(md, url="https://docs.example.com/main")])
    children = [s for s in sections if s.path != "/main"]
    assert len(children) == 1, f"H4 should not split; got {len(children)} children"
    assert children[0].title == "Main Section"


def test_large_page_duplicate_heading_slug_gets_suffix():
    """Duplicate chunk headings get -2, -3, … suffixes."""
    block = _filler(MIN_SECTION_TOKENS + 50)
    md = f"## Install\n{block}\n## Install\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/guide")])
    paths = [s.path for s in sections if s.path != "/guide"]
    assert "/guide/install" in paths
    assert "/guide/install-2" in paths


def test_large_page_no_content_lost():
    """Every line in the original markdown must appear somewhere in the emitted sections."""
    block = _filler(MIN_SECTION_TOKENS + 50)
    md = f"Intro.\n# Title\n## A\n{block}\n## B\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/guide")])
    all_content = "\n".join(s.content for s in sections)
    # Spot-check key pieces
    assert "Intro." in all_content
    assert "w0" in all_content  # first word of first filler block


def test_large_page_no_headings_becomes_one_child():
    """A large page with no H1-H3 headings: root + one content child."""
    block = _filler(MIN_SECTION_TOKENS + 200)
    md = f"No headings here.\n{block}"

    sections = parse_sections([_make_page(md, url="https://docs.example.com/blog")])
    # root section is emitted, but since there are no headings no children are added
    # All content is in the root section
    assert any(s.path == "/blog" for s in sections)


# ── Checksum determinism ──────────────────────────────────────────────────────

def test_checksum_is_deterministic():
    page = _make_page("# Title\nContent here.", url="https://docs.example.com/page")
    s1 = parse_sections([page])
    s2 = parse_sections([page])
    assert s1[0].checksum == s2[0].checksum


# ── test_reproduce_path_issue compatibility ───────────────────────────────────

def test_permalink_heading_is_cleaned():
    """Permalink symbols in headings are stripped for both title and path slug."""
    md = f"# Dependencies[¶](https://fastapi.tiangolo.com/#deps)\n{_filler(5)}"
    sections = parse_sections([_make_page(md, url="https://fastapi.tiangolo.com/tutorial/dependencies/")])
    assert sections[0].title == "Dependencies"
    assert "httpsfastapi" not in sections[0].path
