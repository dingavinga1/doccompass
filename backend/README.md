# Backend

## Run (local)
- `uv sync`
- `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Test
- `uv run pytest`

## Layout
- `app/api`: API layer
- `app/services`: business logic
- `app/models`: persistence models
- `app/tasks`: Celery task entrypoints
- `app/mcp`: MCP wrapper layer
