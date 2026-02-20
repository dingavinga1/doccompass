---
name: search_documentation
description: Search within a documentation set based on a query
---

# Search Documentation Skill

## Prerequisites
* The documentation must be available via `doccompass docs list` command.

## Steps
* (OPTIONAL) Get the documentation tree for a particular documentation set using `doccompass docs tree <documentation_id>`. DO THIS ONLY IF ABSOLUTELY NECESSARY AS THIS CONSUMES A LOT OF TOKENS.
* Search the documentation semantically with a query using `doccompass docs search <documentation_id> <query>`. Use an actual query for better results instead of just keywords. E.g. "Websocket implementation in FastAPI"
* Finally, use the path of the section to get the content for the section using `doccompass docs content <documentation_id> <section_path>`