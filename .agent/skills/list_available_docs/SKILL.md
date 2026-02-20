---
name: list_available_documentations
description: Get a list of available framework documentations.
---

# List Available Documentations Skill

When listing available documentations, follow these steps:
* Fetch all documentations via `doccompass docs list` command.
* Use `--skip` and `--limit` options to paginate the results.
* Check if the documentation for the framework you need is available.
* If so, you may use the `id` of the documentation to fetch the content.
* If not, you must fall back to web search for relevant documentation.