# Phase 1: Infrastructure Setup

## Goal
Establish a reproducible local and CI-ready runtime stack for backend services, worker processing, caching, database, and environment configuration.

## Inputs From Master Plan
- FastAPI + FastMCP backend
- Redis + Celery queueing
- Postgres + PGVector
- `uv` package management
- Docker Compose orchestration
- Required environment variables and service topology

## Scope
- Docker Compose baseline with service health checks
- Backend runtime image setup
- Worker runtime setup
- Redis and Postgres with persisted volumes
- Environment variable strategy (`.env.example`, local `.env`)
- Dependency lock and install flow with `uv`

## Development Plan
1. Create `backend/pyproject.toml` and lock dependencies with `uv.lock`.
2. Add `backend/Dockerfile` for API and worker image reuse.
3. Add root `docker-compose.yml` services: `backend`, `celery_worker`, `redis`, `db`, `frontend` (frontend can be stubbed initially).
4. Add `db` initialization for PGVector extension.
5. Define Compose networks, persistent volumes, restart policies, and health checks.
6. Add `.env.example` with all required variables and safe defaults for local development.
7. Add startup docs in `docs/dev/` for local run, logs, and service verification.
8. Add CI bootstrap script to spin infrastructure for integration tests.

## Unit Testing Plan
1. Add tests validating environment loading and required variable checks.
2. Add tests for settings parsing (invalid URL formats, missing secrets, default overrides).
3. Add tests for dependency container wiring (DB session, Redis client, Celery app initialization).
4. Add smoke tests for app startup with mocked infrastructure clients.

## Manual Testing Plan
1. Run `docker compose up --build` and verify all services reach healthy state.
2. Confirm backend responds on `/health` and DB connectivity is successful.
3. Confirm worker registers with broker and can receive a dummy task.
4. Restart services and verify persisted Postgres volume survives restart.
5. Validate `.env` overrides by changing a non-critical variable and observing runtime behavior.

## Exit Criteria
- All required containers start cleanly and remain healthy.
- Backend can connect to Postgres and Redis.
- Worker can receive and execute a minimal task.
- Configuration is documented and reproducible by another developer.

## Deliverables
- `docker-compose.yml`
- `backend/Dockerfile`
- `.env.example`
- PGVector initialization script
- Infrastructure setup documentation
