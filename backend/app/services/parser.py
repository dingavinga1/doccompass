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



from urllib.parse import urlparse, unquote

def parse_sections(pages: list[CrawledPage]) -> list[ParsedSection]:
    sections: list[ParsedSection] = []

    for page in pages:
        # Use the URL path as the root path, ensuring it starts with / and doesn't end with /
        parsed_url = urlparse(page.url)
        path = parsed_url.path
        if not path.startswith("/"):
            path = "/" + path
        root_path = path.rstrip("/")

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
            
            # Generate URL with anchor for specific sections
            url = page.url
            if level > 1:
                anchor = slugify(title)
                if anchor:
                    url = f"{page.url}#{anchor}"

            sections.append(
                ParsedSection(
                    path=path,
                    parent_path=parent_path if isinstance(parent_path, str) else None,
                    title=title,
                    summary=summary,
                    content=content,
                    level=level,
                    url=url,
                    token_count=len(content.split()),
                    checksum=_checksum(title=title, content=content, level=level, url=url),
                )
            )
            current = None

        intro_lines: list[str] = []

        for line in lines:
            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                finalize_current()

                level = len(heading_match.group(1))
                raw_title = heading_match.group(2).strip()
                # Remove markdown links (e.g. [Title](url)) or permalinks (e.g. Title[¶](url))
                # Simple link removal: [text](url) -> text
                # We also need to handle trailing permalinks like "Title[¶](url)" -> "Title"
                
                # First, remove generic markdown links: [text](url) -> text
                title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw_title)
                
                # Then specifically remove the permalink symbol often used: ¶
                title = title.replace("¶", "").strip()

                while stack and int(stack[-1]["level"]) >= level:
                    stack.pop()

                parent_path = str(stack[-1]["path"]) if stack else root_path
                slug = slugify(title)
                key = (parent_path, slug)
                counters[key] = counters.get(key, 0) + 1
                suffix = "" if counters[key] == 1 else f"-{counters[key]}"
                
                # Construct path by appending slug to parent path
                if parent_path == "/":
                     path = f"/{slug}{suffix}"
                else:
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
            # Intro path logic: append /intro to root path
            intro_path = f"{root_path}/intro" if root_path != "/" else "/intro"
            
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
            empty_path = f"{root_path}/content" if root_path != "/" else "/content"
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

