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
   - This runs the one-shot `migrations` service first, then starts `backend` and `celery_worker` after migrations succeed.
3. Verify services:
   - Backend health: `http://localhost:8000/health`
   - Backend readiness: `http://localhost:8000/ready`
   - Frontend placeholder: `http://localhost:3000`

### Migration Operations
- Run migrations only:
  - `docker compose up migrations`
- Re-run migrations as an idempotent one-shot job:
  - `docker compose run --rm migrations`
- Inspect migration logs:
  - `docker compose logs migrations`
- Make target:
  - `make migrate`

### Backend Unit Tests
- `cd backend && uv run pytest`

### Notes
- Postgres uses `pgvector/pgvector:pg16` and enables extension via `db/init/01-create-pgvector.sql`.
- Celery worker uses Redis as broker and result backend.
