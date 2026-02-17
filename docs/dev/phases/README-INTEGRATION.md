# Phase 6: Bind It All Together

## Goal
Integrate infrastructure, ingestion, API, and MCP layers into a cohesive system with reliability, observability, and release readiness.

## Inputs From Master Plan
- Security and reliability controls
- Dockerized multi-service runtime
- Acceptance criteria around ingesting FastAPI docs
- Delta update and stop-ingestion correctness

## Scope
- Service-to-service wiring and environment alignment
- End-to-end workflows from ingestion trigger to MCP retrieval
- Logging, metrics, retries, and failure visibility
- Integration test coverage across service boundaries

## Development Plan
1. Wire backend API, Celery worker, Redis, and Postgres using shared settings module.
2. Ensure migrations run automatically or through a documented startup step.
3. Add retry policies for crawl and embedding transient failures.
4. Add structured logs with correlation IDs (ingestion job id).
5. Add integration test harness using dockerized dependencies.
6. Implement startup checks for DB readiness, Redis connectivity, and PGVector availability.
7. Validate performance characteristics on medium documentation sets.
8. Finalize runbooks: incident handling, failed job triage, and safe re-run procedures.

## Unit Testing Plan
1. Service integration-unit tests with mocked external boundaries.
2. Retry/backoff logic tests for transient failure categories.
3. Startup dependency-check tests for missing services.
4. Config consistency tests across API and worker processes.

## Manual Testing Plan
1. Execute full flow: start ingestion -> wait for completion -> query via API and MCP.
2. Validate acceptance criteria using FastAPI docs as canonical source.
3. Interrupt ingestion mid-run and verify clean stop behavior.
4. Re-run ingestion and validate checksum-based delta updates.
5. Restart full stack and confirm resumed functionality with persisted data.

## Exit Criteria
- Full workflow is stable across multiple runs.
- Operational diagnostics are sufficient for troubleshooting.
- Acceptance criteria are satisfied end-to-end.

## Deliverables
- Integration wiring updates
- Reliability and observability additions
- End-to-end test scripts
- Operational runbook documentation
