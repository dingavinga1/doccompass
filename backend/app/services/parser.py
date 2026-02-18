from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .crawler import CrawledPage

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
NON_ALNUM = re.compile(r"[^a-z0-9\-\s]")
MULTI_DASH = re.compile(r"-+")


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


def _checksum(title: str, content: str, level: int, url: str) -> str:
    payload = f"{title}\n{content.strip()}\n{level}\n{url}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_sections(pages: list[CrawledPage]) -> list[ParsedSection]:
    sections: list[ParsedSection] = []

    for page in pages:
        page_slug = slugify(page.url)
        root_path = f"/{page_slug}"
        lines = page.markdown.splitlines()

        stack: list[dict[str, object]] = []
        counters: dict[tuple[str, str], int] = {}
        current: dict[str, object] | None = None

        def finalize_current() -> None:
            nonlocal current
            if current is None:
                return

            content = "\n".join(current["content_lines"]).strip()
            title = str(current["title"])
            level = int(current["level"])
            parent_path = current["parent_path"]
            path = str(current["path"])
            summary = content[:240]

            sections.append(
                ParsedSection(
                    path=path,
                    parent_path=parent_path if isinstance(parent_path, str) else None,
                    title=title,
                    summary=summary,
                    content=content,
                    level=level,
                    url=page.url,
                    token_count=len(content.split()),
                    checksum=_checksum(title=title, content=content, level=level, url=page.url),
                )
            )
            current = None

        intro_lines: list[str] = []

        for line in lines:
            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                finalize_current()

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                while stack and int(stack[-1]["level"]) >= level:
                    stack.pop()

                parent_path = str(stack[-1]["path"]) if stack else root_path
                slug = slugify(title)
                key = (parent_path, slug)
                counters[key] = counters.get(key, 0) + 1
                suffix = "" if counters[key] == 1 else f"-{counters[key]}"
                path = f"{parent_path}/{slug}{suffix}"

                current = {
                    "title": title,
                    "level": level,
                    "path": path,
                    "parent_path": parent_path,
                    "content_lines": [],
                }
                stack.append({"level": level, "path": path})
            else:
                if current is None:
                    intro_lines.append(line)
                else:
                    current["content_lines"].append(line)

        finalize_current()

        intro_content = "\n".join(intro_lines).strip()
        if intro_content:
            intro_path = f"{root_path}/intro"
            sections.append(
                ParsedSection(
                    path=intro_path,
                    parent_path=root_path,
                    title="Introduction",
                    summary=intro_content[:240],
                    content=intro_content,
                    level=1,
                    url=page.url,
                    token_count=len(intro_content.split()),
                    checksum=_checksum(title="Introduction", content=intro_content, level=1, url=page.url),
                )
            )

        if not lines:
            empty_path = f"{root_path}/content"
            sections.append(
                ParsedSection(
                    path=empty_path,
                    parent_path=root_path,
                    title=page.url,
                    summary="",
                    content="",
                    level=1,
                    url=page.url,
                    token_count=0,
                    checksum=_checksum(title=page.url, content="", level=1, url=page.url),
                )
            )

    return sections
