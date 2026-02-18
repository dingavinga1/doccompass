from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from pydantic_ai import Embedder

from app.config import settings

if TYPE_CHECKING:
    import uuid

logger = logging.getLogger(__name__)

# Module-level embedder singleton — initialised once from config.
_embedder: Embedder | None = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder(settings.embedding_model)
    return _embedder


async def embed_sections(
    texts: list[str],
    *,
    doc_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
) -> list[list[float]]:
    """Embed a list of texts in batches, with retry and dimension validation.

    Returns vectors in the same order as the input texts.
    """
    embedder = _get_embedder()
    batch_size = settings.embedding_batch_size
    max_retries = settings.embedding_max_retries
    expected_dim = settings.embedding_dimension

    all_vectors: list[list[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = start + batch_size
        batch = texts[start:end]

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                t0 = time.monotonic()
                result = await embedder.embed_documents(batch)
                duration = time.monotonic() - t0

                logger.info(
                    "Embedding batch %d/%d completed",
                    batch_idx + 1,
                    total_batches,
                    extra={
                        "doc_id": str(doc_id) if doc_id else None,
                        "job_id": str(job_id) if job_id else None,
                        "batch_size": len(batch),
                        "duration_s": round(duration, 3),
                    },
                )

                vectors = [list(v) for v in result.embeddings]

                # Dimension validation
                for i, vec in enumerate(vectors):
                    if len(vec) != expected_dim:
                        raise ValueError(
                            f"Dimension mismatch at index {start + i}: "
                            f"got {len(vec)}, expected {expected_dim}"
                        )

                all_vectors.extend(vectors)
                last_error = None
                break

            except ValueError:
                raise  # Dimension mismatch is terminal

            except Exception as exc:
                last_error = exc
                logger.error(
                    "Embedding batch %d/%d attempt %d/%d failed: %s",
                    batch_idx + 1,
                    total_batches,
                    attempt,
                    max_retries,
                    exc,
                    extra={
                        "doc_id": str(doc_id) if doc_id else None,
                        "job_id": str(job_id) if job_id else None,
                    },
                    exc_info=True,
                )

        if last_error is not None:
            raise RuntimeError(
                f"Embedding batch {batch_idx + 1}/{total_batches} failed after "
                f"{max_retries} retries: {last_error}"
            ) from last_error

    return all_vectors


async def embed_query(text: str) -> list[float]:
    """Embed a single query string for search-time use."""
    embedder = _get_embedder()
    result = await embedder.embed_query(text)
    vector = list(result.embeddings[0])

    if len(vector) != settings.embedding_dimension:
        raise ValueError(
            f"Query embedding dimension mismatch: got {len(vector)}, "
            f"expected {settings.embedding_dimension}"
        )

    return vector
