# Phase 4: API Endpoint Setup

## Goal
Expose stable REST endpoints for ingestion control and documentation/section retrieval, including tree navigation and keyword-search fallback.

## Inputs From Master Plan
- Ingestion endpoints:
  - `POST /documentation/ingestion`
  - `GET /documentation/ingestion/:id`
  - `POST /documentation/ingestion/stop`
- Documentation endpoints:
  - `GET /documentation`
  - `GET /documentation/:id`
  - `DELETE /documentation/:id`
  - `GET /documentation/:id/sections/{path}`
  - `GET /documentation/:id/tree`
  - `GET /documentation/:id/search`

## Scope
- Request/response schema definitions
- Pagination and filtering behavior
- Input validation and consistent error models
- Phase-4 search fallback using keyword ranking (`search_mode=keyword_fallback`) until embedding phase is complete
- API-level authentication hook points (documented only; not enforced in this phase)

## Development Plan
1. Create router modules for ingestion and documentation APIs.
2. Define Pydantic request/response schemas with explicit examples.
3. Implement endpoint handlers delegating to service layer only (thin controllers).
4. Add pagination support for section listing (`limit`, `offset`, `start_path`).
5. Implement section content retrieval via encoded `section_path`.
6. Implement keyword fallback search endpoint returning ranked results and scores.
7. Add delete behavior with cascade and consistent `404` for missing IDs.
8. Standardize API error responses (validation, not found, conflict, internal).
9. Generate OpenAPI docs and endpoint usage examples.

## Unit Testing Plan
1. Endpoint tests for happy paths with fixture data.
2. Validation tests for malformed payloads and parameter bounds.
3. Pagination tests (boundaries, empty pages, deterministic ordering).
4. Search tests for keyword relevance ranking and mode marker.
5. Delete tests confirming cascading data removal behavior.
6. Router import smoke test to ensure app starts with both routers.

## Manual Testing Plan
1. Use API client to create ingestion, poll status, and stop jobs.
2. Verify documentation listing and section listing with pagination.
3. Retrieve specific section content and compare with stored content.
4. Execute keyword search queries and spot-check relevance.
5. Delete a documentation record and confirm associated entities are removed.

## Exit Criteria
- All endpoints behave per contract with stable schema.
- Error handling is consistent and useful.
- Search and tree endpoints return correct, ordered data.

## Current Status (2026-02-18)
- Implemented and live: all ingestion + documentation Phase 4 endpoints.
- Search mode: `keyword_fallback` only.
- Auth: hook points remain out of enforcement for this phase.
- Verified manually against ingested FastAPI docs via host `curl`:
  - `/documentation`
  - `/documentation/{id}`
  - `/documentation/{id}/sections/{path}`
  - `/documentation/{id}/tree`
  - `/documentation/{id}/search`
  - `DELETE /documentation/{id}` (missing-id behavior)

## Deliverables
- API routers and schemas
- OpenAPI updates
- Endpoint-level unit tests
- API usage examples
