# Phase 8: Embedding and Vector Indexing Setup

## Goal

Replace the embedding/indexing stubs with a production-ready vector pipeline that writes real embeddings to PGVector and powers semantic retrieval.

## Inputs From Master Plan

- Ingestion lifecycle includes `EMBEDDING` and `INDEXING` states
- `documentation_section.embedding` vector column exists
- Delta logic already identifies changed/new sections by checksum

## Scope

- Embedding provider integration via provider-included model string from config
- Batch embedding generation for changed sections only
- Retry/backoff strategy for transient provider failures
- Vector upsert into `documentation_section.embedding`
- Re-embedding strategy when model/provider settings change
- Metrics and logs for embedding latency, throughput, and failures

## Configuration Contract

- Add provider-included embedding model string to `.env`:
  - `EMBEDDING_MODEL=bedrock:amazon.titan-embed-text-v2:0`
- Keep AWS auth/region configuration in environment (standard Bedrock credential chain).
- Initialize embedder from this single string (Pydantic AI quick-start pattern):
  - `embedder = Embedder(settings.embedding_model)`

## Development Plan

1. Add settings support for `EMBEDDING_MODEL` (provider-included string format).
2. Create embedder initialization from `settings.embedding_model` using `Embedder(...)`.
3. Add config keys for batch size, retries, timeout, and expected dimensions.
4. Build embedding service that accepts section payloads and returns vectors in stable order.
5. Integrate embedding stage into ingestion worker after parsing/delta detection.
6. Persist vectors only for changed/new sections; skip unchanged checksums.
7. Add indexing step that validates vector dimensions and records indexing status.
8. Add failure handling:
   - retry transient errors
   - fail job on terminal errors with actionable message
9. Add maintenance command for full re-embedding of a documentation set.
10. Add structured logging around batches (`doc_id`, `job_id`, batch size, duration, failures).

## Unit Testing Plan

1. Provider contract tests (ordering, dimension validation, error mapping).
2. Batch slicing tests for exact coverage and no duplicates.
3. Delta tests confirming unchanged sections skip embedding calls.
4. Retry tests for transient failures and terminal-failure cutoff.
5. Persistence tests for vector writes and model-dimension mismatches.
6. Re-embedding command tests for full dataset refresh behavior.

## Manual Testing Plan

1. Run ingestion on FastAPI docs and verify sections receive vectors.
2. Re-run ingestion with no content changes and verify minimal/no embedding API calls.
3. Change one page and verify embeddings regenerate only for affected sections.
4. Execute semantic search and confirm relevance improves versus keyword-only behavior.
5. Force provider failure (invalid AWS credentials or timeout) and verify job fails with useful diagnostics.

## Exit Criteria

- `EMBEDDING` and `INDEXING` are fully implemented and observable.
- Vectors are stored for changed/new sections with correct dimensions.
- Re-ingestion preserves checksum and embedding efficiency.
- Semantic search uses stored vectors and returns ranked results.

## Deliverables

- Embedding provider module(s)
- Embedding/indexing service integration in ingestion task
- Config and operational runbook for embedding settings
- Unit tests and manual verification checklist
