# Phase 1 Infrastructure Setup - Implementation Notes

## Implemented
- Backend service with FastAPI health endpoint (`/health`)
- Backend readiness endpoint with dependency checks (`/ready`)
- Redis connectivity health check
- Postgres connectivity health check
- PGVector extension readiness check
- Celery worker wiring with Redis broker/result backend
- One-shot `migrations` service in Compose (`uv run alembic upgrade head`)
- Docker Compose stack for backend, worker, Redis, Postgres (pgvector), and frontend placeholder
- `.env.example` with required config keys
- PGVector initialization SQL
- Basic backend unit tests for settings and health endpoint behavior

## Runbook
1. `cp .env.example .env`
2. `docker compose up --build`
3. Validate:
   - `curl http://localhost:8000/health`
   - `curl http://localhost:8000/ready`
   - Open `http://localhost:3000`
4. Run tests:
   - `cd backend && uv run pytest`

## Migration Runbook
1. Run migrations job only:
   - `docker compose up migrations`
2. Re-run migrations safely (idempotent):
   - `docker compose run --rm migrations`
3. Check migration logs:
   - `docker compose logs migrations`
4. Failure triage:
   - Confirm DB is healthy: `docker compose ps`
   - Confirm DB credentials in `.env` match Compose config.
   - Re-run migration job and inspect logs for Alembic revision or connection errors.
5. Safe re-run procedure:
   - Fix root cause (credentials/connectivity/revision mismatch), then run `docker compose run --rm migrations`.
   - Start stack with `docker compose up --build`.

## Manual Verification Checklist
- [ ] All containers become healthy
- [ ] `/health` returns `status=ok`
- [ ] `/ready` returns `status=ok`
- [ ] Celery worker starts and connects to Redis
- [ ] Postgres has vector extension enabled
- [ ] Stack restarts with persisted DB data volume
