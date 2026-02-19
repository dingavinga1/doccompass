from app.services.crawler import CrawledPage
from app.services.parser import parse_sections


def test_parse_sections_builds_hierarchy_and_stable_paths():
    pages = [
        CrawledPage(
            url="https://docs.example.com/guide",
            markdown="# Intro\nWelcome\n## Install\nDo this\n## Install\nDo that",
            html=None,
            depth=0,
        )
    ]

    sections = parse_sections(pages)
    paths = [section.path for section in sections]

    # New logic uses URL path as root. 
    # url path for https://docs.example.com/guide is /guide
    assert "/guide/intro" in paths
    assert "/guide/intro/install" in paths
    assert "/guide/intro/install-2" in paths

    install = next(section for section in sections if section.path.endswith("/install"))
    assert install.parent_path == "/guide/intro"
    assert install.token_count > 0
    assert len(install.checksum) == 64
