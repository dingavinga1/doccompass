# Documentation MCP Gateway

## Infrastructure Phase (Phase 1)

### Prerequisites
- Docker + Docker Compose
- `uv` (for local Python workflow)

### Quick Start
1. Copy env file:
   - `cp .env.example .env`
2. Start stack:
   - `docker compose up --build`
3. Verify services:
   - Backend health: `http://localhost:8000/health`
   - Frontend placeholder: `http://localhost:3000`

### Backend Unit Tests
- `cd backend && uv run pytest`

### Notes
- Postgres uses `pgvector/pgvector:pg16` and enables extension via `db/init/01-create-pgvector.sql`.
- Celery worker uses Redis as broker and result backend.
