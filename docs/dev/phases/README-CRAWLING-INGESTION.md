# Phase 3: Crawling and Ingestion Setup

## Goal

Implement a reliable ingestion pipeline that crawls documentation sites, parses hierarchical content, stores normalized sections, and supports incremental updates.

## Inputs From Master Plan

- Ingestion job lifecycle: `PENDING -> CRAWLING -> PARSING -> EMBEDDING -> INDEXING -> COMPLETED/FAILED/STOPPED`
- Endpoints to start, stop, and list ingestion jobs
- Delta updates based on checksums
- Optional raw page persistence

## Scope

- `documentation`, `documentation_section`, `ingestion_job`, `raw_page` data model implementation
- Celery task orchestration and cancellation handling
- Crawl4AI integration for URL discovery/content fetch (MUST USE CRAWL4AI. First check the official documentation for implementation instructions)
- Section parser for hierarchy and metadata extraction
- Checksum-based change detection

## Development Plan

1. Implement SQLModel models and migrations for all ingestion tables.
2. Build ingestion service to create jobs and enqueue Celery workflows.
3. Implement crawler adapter:
   - Use `BFSDeepCrawlStrategy` for native depth control and page limits.
   - Implement `FilterChain` with `URLPatternFilter` for include patterns.
   - Add custom exclusion logic for exclude patterns.
   - Leverage native Crawl4AI retry/backoff.
4. Implement raw page persistence pipeline (`raw_page`) behind a feature flag.
5. Build parser for heading-based section tree with stable path generation.
   - **Path Strategy**: Use the URL path as the root (e.g. `/fastapi/dependencies`) instead of slugifying the full URL.
   - **Title Cleaning**: Strip markdown links and permalinks from headers to ensure clean titles and paths.
6. Compute per-section checksums and upsert changed sections only.
7. Update ingestion progress fields and state transitions consistently.
8. Add stop/cancel flow and graceful task interruption points.
9. Add structured logging and failure diagnostics at each stage.

## Unit Testing Plan

1. Model tests for constraints and relationships (cascade behavior, unique URL).
2. Crawler adapter tests with mocked HTML pages and link graphs.
3. Parser tests for nested heading extraction and deterministic paths.
4. Delta update tests verifying unchanged sections are skipped.
5. Job lifecycle tests for all status transitions including `FAILED` and `STOPPED`.
6. Cancellation tests ensuring in-flight tasks stop and status persists.

## Manual Testing Plan

1. Start ingestion for FastAPI docs with depth 2-3 and monitor progress updates.
2. Verify raw pages and sections are inserted and linked correctly.
3. Trigger re-ingestion after changing one page in a controlled test source and verify only changed sections update.
4. Stop an active ingestion and verify status changes to `STOPPED` with no additional writes.
5. Simulate crawl failure (invalid URL or timeout) and verify error handling and job status.

## Exit Criteria

- End-to-end ingestion runs to completion.
- Section tree and metadata are persisted correctly.
- Incremental updates avoid unnecessary rewrites.
- Cancellation and failure behavior is predictable and observable.

## Deliverables

- DB models and migrations
- Celery ingestion workflow
- Crawler + parser services
- Checksum/delta logic
- Ingestion test suite
