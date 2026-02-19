from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .crawler import CrawledPage

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
NON_ALNUM = re.compile(r"[^a-z0-9\-\s]")
MULTI_DASH = re.compile(r"-+")

# Minimum token count (whitespace-split words) per section chunk.
#
# Small pages (total < threshold):  one flat section at root_path.
#
# Large pages (total >= threshold):
#   1. A mandatory *root section* is emitted at root_path (parent_path=None).
#      Its content is any introductory text before the first heading plus the
#      page title derived from the first H1 (or the URL path stem).
#   2. The remaining content is split at every H1-H3 boundary into "candidate"
#      sections.  Consecutive candidates whose combined token count is still
#      below the threshold are then *merged* so that every emitted child
#      section contains at least MIN_SECTION_TOKENS tokens.
#   3. Every child section has parent_path = root_path, ensuring the UI tree
#      always has a visible anchor node for the page.
#
# Raise or lower this constant to tune section granularity.
MIN_SECTION_TOKENS: int = 1500

# Only H1-H3 are used as candidate split-points for the large-page chunker.
_SPLIT_LEVELS: frozenset[int] = frozenset({1, 2, 3})


@dataclass(slots=True)
class ParsedSection:
    path: str
    parent_path: str | None
    title: str
    summary: str
    content: str
    level: int
    url: str
    token_count: int
    checksum: str


def slugify(value: str) -> str:
    lowered = value.strip().lower().replace("_", " ")
    cleaned = NON_ALNUM.sub("", lowered)
    dashed = cleaned.replace(" ", "-")
    dashed = MULTI_DASH.sub("-", dashed).strip("-")
    return dashed or "section"


def _clean_heading(raw: str) -> str:
    """Strip markdown links and permalink symbols from a heading string."""
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    return cleaned.replace("¶", "").strip()


def _checksum(title: str, content: str, level: int, url: str) -> str:
    payload = f"{title}\n{content.strip()}\n{level}\n{url}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _make_section(
    *,
    path: str,
    parent_path: str | None,
    title: str,
    content: str,
    level: int,
    url: str,
) -> ParsedSection:
    content = content.strip()
    return ParsedSection(
        path=path,
        parent_path=parent_path,
        title=title,
        summary=content[:240],
        content=content,
        level=level,
        url=url,
        token_count=len(content.split()),
        checksum=_checksum(title=title, content=content, level=level, url=url),
    )


def parse_sections(pages: list[CrawledPage]) -> list[ParsedSection]:
    sections: list[ParsedSection] = []

    for page in pages:
        # ── Root path from URL ───────────────────────────────────────────
        parsed_url = urlparse(page.url)
        raw_path = parsed_url.path
        if not raw_path.startswith("/"):
            raw_path = "/" + raw_path
        root_path = raw_path.rstrip("/") or "/"

        lines = page.markdown.splitlines()
        total_tokens = len(page.markdown.split())

        # ── Empty page ───────────────────────────────────────────────────
        if not lines or total_tokens == 0:
            empty_path = f"{root_path}/content" if root_path != "/" else "/content"
            sections.append(
                _make_section(
                    path=empty_path,
                    parent_path=root_path,
                    title=page.url,
                    content="",
                    level=1,
                    url=page.url,
                )
            )
            continue

        # ── Small-page guard (<MIN_SECTION_TOKENS) ───────────────────────
        # Entire page → one flat section at root_path (no splitting, no parent).
        if total_tokens < MIN_SECTION_TOKENS:
            flat_title: str = root_path.split("/")[-1] or "home"
            for line in lines:
                m = HEADING_PATTERN.match(line)
                if m and len(m.group(1)) == 1:  # first H1 only
                    flat_title = _clean_heading(m.group(2))
                    break

            sections.append(
                _make_section(
                    path=root_path,
                    parent_path=None,
                    title=flat_title,
                    content=page.markdown,
                    level=1,
                    url=page.url,
                )
            )
            continue

        # ── Large-page (>=MIN_SECTION_TOKENS): root node + merged children ──
        #
        # Step 1 ─ walk lines and collect:
        #   • intro_lines  : everything before the first H1-H3 heading
        #   • page_title   : from the first H1 found, else from URL path stem
        #   • heading_lines: first index of the first H1-H3 (chunker starts here)
        #
        page_title: str = root_path.split("/")[-1] or "home"
        intro_lines: list[str] = []
        first_heading_idx: int = len(lines)  # default: no heading found

        for idx, line in enumerate(lines):
            m = HEADING_PATTERN.match(line)
            if m and len(m.group(1)) in _SPLIT_LEVELS:
                if len(m.group(1)) == 1:
                    page_title = _clean_heading(m.group(2))
                first_heading_idx = idx
                break
            intro_lines.append(line)

        # Step 2 ─ emit the root section (the page anchor in the tree)
        intro_content = "\n".join(intro_lines).strip()
        sections.append(
            _make_section(
                path=root_path,
                parent_path=None,
                title=page_title,
                content=intro_content,
                level=1,
                url=page.url,
            )
        )

        # If the page had NO headings, everything was intro — we're done.
        if first_heading_idx == len(lines):
            continue

        # Step 3 ─ collect one "candidate" per H1-H3, starting from the first heading.
        #
        # A candidate = (title, level, lines[]).  All lines between headings
        # belong to the preceding candidate.
        candidates: list[tuple[str | None, int, list[str]]] = []
        c_title: str | None = None
        c_level: int = 1
        c_lines: list[str] = []

        for line in lines[first_heading_idx:]:
            m = HEADING_PATTERN.match(line)
            if m and len(m.group(1)) in _SPLIT_LEVELS:
                if c_lines or c_title is not None:
                    candidates.append((c_title, c_level, c_lines))
                c_title = _clean_heading(m.group(2))
                c_level = len(m.group(1))
                c_lines = [line]
            else:
                c_lines.append(line)

        if c_lines or c_title is not None:
            candidates.append((c_title, c_level, c_lines))  # flush last

        # Step 4 ─ merge consecutive candidates until the accumulated token
        #           count reaches MIN_SECTION_TOKENS, then start a new chunk.
        #
        # This ensures every emitted section is wide enough to be semantically
        # useful while still respecting heading boundaries.
        chunks: list[tuple[str | None, int, list[str]]] = []
        m_title: str | None = None
        m_level: int = 1
        m_lines: list[str] = []
        m_tokens: int = 0

        for cand_title, cand_level, cand_lines in candidates:
            cand_tokens = sum(len(ln.split()) for ln in cand_lines)

            if m_tokens >= MIN_SECTION_TOKENS:
                # Current accumulation hit the threshold — flush it.
                chunks.append((m_title, m_level, m_lines))
                m_title = cand_title
                m_level = cand_level
                m_lines = list(cand_lines)
                m_tokens = cand_tokens
            else:
                # Not enough yet — absorb this candidate into the current chunk.
                if m_title is None:
                    m_title = cand_title
                    m_level = cand_level
                m_lines.extend(cand_lines)
                m_tokens += cand_tokens

        if m_lines or m_title is not None:
            chunks.append((m_title, m_level, m_lines))  # flush last

        # Step 5 ─ emit each merged chunk as a child of root_path.
        slug_counters: dict[str, int] = {}
        for raw_title, level, chunk_lines in chunks:
            title = raw_title if raw_title is not None else (root_path.split("/")[-1] or "home")
            slug = slugify(title)
            slug_counters[slug] = slug_counters.get(slug, 0) + 1
            suffix = "" if slug_counters[slug] == 1 else f"-{slug_counters[slug]}"
            section_path = (
                f"/{slug}{suffix}" if root_path == "/" else f"{root_path}/{slug}{suffix}"
            )
            content = "\n".join(chunk_lines)
            sections.append(
                _make_section(
                    path=section_path,
                    parent_path=root_path,
                    title=title,
                    content=content,
                    level=level,
                    url=page.url,
                )
            )

    return sections
