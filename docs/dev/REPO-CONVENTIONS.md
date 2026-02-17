# Repository Conventions

## Folder Boundaries
- `backend/app/api`: HTTP routers and request/response schemas only.
- `backend/app/services`: business logic and orchestration.
- `backend/app/models`: SQLModel and persistence models.
- `backend/app/tasks`: Celery tasks and asynchronous job entrypoints.
- `backend/app/mcp`: MCP tool wrappers and server wiring.
- `frontend/src/pages`: route-level views.
- `frontend/src/components`: reusable UI units.
- `frontend/src/api`: API layer and typed transport utilities.
- `scripts`: developer and CI helper scripts.

## Dependency Direction
- `api` can depend on `services` and schema modules.
- `services` can depend on `models` and external clients.
- `models` must not depend on `api`.
- `tasks` can depend on `services`.
- `mcp` can depend on `services`.

## Test Placement
- Backend unit tests: `backend/tests`.
- Frontend tests: `frontend/tests`.
- Integration/e2e tests (later phase): `tests/integration` at repository root.

## Naming
- Modules and files: `snake_case`.
- Class names: `PascalCase`.
- Constants/env vars: `UPPER_SNAKE_CASE`.
