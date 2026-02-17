# Phase 2: Repository Basic Folder Structure Setup

## Goal
Create a clean, maintainable repository structure that separates backend, frontend, ingestion, API, MCP tools, and tests from day one.

## Inputs From Master Plan
- Root split into `backend/`, `frontend/`, `docs/`, and root orchestration files
- Backend app folders: `api`, `models`, `services`
- Frontend source and container setup

## Scope
- Standardized folder tree
- Package/module boundaries
- Test folder placement and naming conventions
- Build, lint, and test command entrypoints
- Developer onboarding README per major component

## Development Plan
1. Create top-level folders:
   - `backend/`
   - `frontend/`
   - `docs/dev/`
   - `scripts/`
2. Define backend package layout:
   - `backend/app/main.py`
   - `backend/app/config.py`
   - `backend/app/api/`
   - `backend/app/models/`
   - `backend/app/services/`
   - `backend/app/tasks/`
   - `backend/app/mcp/`
   - `backend/tests/`
3. Define frontend layout:
   - `frontend/src/`
   - `frontend/src/pages/`
   - `frontend/src/components/`
   - `frontend/src/api/`
   - `frontend/tests/`
4. Add shared conventions docs:
   - naming patterns
   - module dependency direction
   - where to place unit vs integration tests
5. Add Makefile or script commands for bootstrapping, test, and lint.
6. Add placeholder README files for backend and frontend with run/test commands.

## Unit Testing Plan
1. Add import-path smoke tests to ensure core modules load without circular imports.
2. Add tests for config module discovery from expected paths.
3. Add command checks (script-level tests) ensuring test and lint commands execute in correct directories.

## Manual Testing Plan
1. Clone into a clean directory and run bootstrap steps from documentation.
2. Validate developers can locate API, tasks, models, and UI code quickly from documented structure.
3. Confirm IDE indexing and test discovery work out of the box.
4. Confirm no ambiguous duplicate directories (for example, `service` vs `services`).

## Exit Criteria
- Folder structure is complete and documented.
- Test discovery works for backend and frontend.
- Team can onboard using only repository docs.

## Deliverables
- Full repository scaffold
- Component README files
- Command runner (Makefile or scripts)
- Structure conventions documentation
