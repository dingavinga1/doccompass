
from app.services.parser import parse_sections
from app.services.crawler import CrawledPage

def test_reproduce_path_issue():
    # Mock a page with a URL that causes issues
    # The issue described was: Path: "/httpsfastapitiangolocom/fastapihttpsfastapitiangolocomfastapi/..."
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
        depth=1
    )
    
    sections = parse_sections([page])
    
    for section in sections:
        # Check for the redundancy issue in path
        # With the fix, the path should NOT contain the protocol/domain slug
        assert "httpsfastapi" not in section.path, f"Path '{section.path}' contains redundant URL parts."
        
        # Check for the expected clean path structure
        # Expected: /fastapi/dependencies/without-standard-dependencies/...
        # or /fastapi/dependencies/without-standard-dependencies (root matches)
        # Verify that it starts with the URL path
        expected_root = "/fastapi/dependencies/without-standard-dependencies"
        assert section.path.startswith(expected_root), f"Path '{section.path}' does not start with expected root '{expected_root}'"

        # Check for missing anchor in URL for subsections
        if section.title == "Without Standard Dependencies":
             assert section.url.endswith("#without-standard-dependencies"), f"URL '{section.url}' missing anchor for subsection."

def test_reproduce_permalink_issue():
    # Reproduce the specific issue where markdown headers contain links/permalinks
    # Example: # Dependencies[¶](https://fastapi.tiangolo.com/#dependencies)
    url = "https://fastapi.tiangolo.com/tutorial/dependencies/"
    markdown = """
# Dependencies[¶](https://fastapi.tiangolo.com/#dependencies)

Some content.
    """
    
    page = CrawledPage(
        url=url,
        markdown=markdown,
        html="",
        depth=1
    )
    
    sections = parse_sections([page])
    section = sections[0]
    
    # The title should be cleaned of the link
    # Current behavior (likely): "Dependencies[¶](https://fastapi.tiangolo.com/#dependencies)"
    # Desired behavior: "Dependencies"
    assert section.title == "Dependencies"
    
    # The path should be clean
    # Current behavior (likely): ".../dependencieshttpsfastapitiangolocomdependencies"
    # Desired behavior: "/tutorial/dependencies" (since it's level 1, it might just use root path)
    # Actually, the parser logic uses the slug for the path segment.
    # If the title is "Dependencies[¶](...)", the slug becomes "dependencieshttpsfastapitiangolocomdependencies"
    
    # Let's check the path
    assert section.path == "/tutorial/dependencies/dependencies"

