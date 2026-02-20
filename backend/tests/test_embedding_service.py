"""Unit tests for the embedding service (app/services/embedding.py)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── embed_sections ─────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_embedder():
    """Reset module-level embedder singleton between tests."""
    import app.services.embedding as mod

    mod._embedder = None
    yield
    mod._embedder = None


def _make_embedding_result(vectors: list[list[float]]):
    """Create a mock result matching Pydantic AI EmbedResult interface."""
    result = MagicMock()
    result.embeddings = vectors
    return result


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_single_batch(mock_embedder_cls, mock_settings):
    """Test embedding a small number of texts in a single batch."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 10
    mock_settings.embedding_max_retries = 3
    mock_settings.embedding_dimension = 4

    vectors = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(return_value=_make_embedding_result(vectors))
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_sections

    result = await embed_sections(["text1", "text2"], doc_id=uuid.uuid4())

    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3, 0.4]
    assert result[1] == [0.5, 0.6, 0.7, 0.8]
    mock_instance.embed_documents.assert_called_once()


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_multiple_batches(mock_embedder_cls, mock_settings):
    """Test that texts are split into batches correctly."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 2
    mock_settings.embedding_max_retries = 1
    mock_settings.embedding_dimension = 3

    batch1 = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    batch2 = [[0.7, 0.8, 0.9]]

    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(
        side_effect=[_make_embedding_result(batch1), _make_embedding_result(batch2)]
    )
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_sections

    result = await embed_sections(["t1", "t2", "t3"])

    assert len(result) == 3
    assert mock_instance.embed_documents.call_count == 2


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_dimension_mismatch(mock_embedder_cls, mock_settings):
    """Test that a dimension mismatch raises ValueError."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 10
    mock_settings.embedding_max_retries = 1
    mock_settings.embedding_dimension = 4

    wrong_dim = [[0.1, 0.2, 0.3]]  # expected 4, got 3
    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(return_value=_make_embedding_result(wrong_dim))
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_sections

    with pytest.raises(ValueError, match="Dimension mismatch"):
        await embed_sections(["text"])


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_retry_on_transient_error(mock_embedder_cls, mock_settings):
    """Test that transient errors are retried."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 10
    mock_settings.embedding_max_retries = 3
    mock_settings.embedding_dimension = 2

    good_result = _make_embedding_result([[0.1, 0.2]])
    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(
        side_effect=[ConnectionError("network error"), good_result]
    )
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_sections

    result = await embed_sections(["text"])

    assert len(result) == 1
    assert mock_instance.embed_documents.call_count == 2  # 1 failure + 1 success


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_max_retries_exhausted(mock_embedder_cls, mock_settings):
    """Test that RuntimeError is raised after all retries are exhausted."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 10
    mock_settings.embedding_max_retries = 2
    mock_settings.embedding_dimension = 2

    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(
        side_effect=ConnectionError("network error")
    )
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_sections

    with pytest.raises(RuntimeError, match="failed after 2 retries"):
        await embed_sections(["text"])


# ─── embed_query ─────────────────────────────────────────────────


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_query_success(mock_embedder_cls, mock_settings):
    """Test single query embedding."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_dimension = 3

    result_obj = MagicMock()
    result_obj.embeddings = [[0.1, 0.2, 0.3]]

    mock_instance = MagicMock()
    mock_instance.embed_query = AsyncMock(return_value=result_obj)
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_query

    result = await embed_query("test query")
    assert result == [0.1, 0.2, 0.3]


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_query_dimension_mismatch(mock_embedder_cls, mock_settings):
    """Test that a query embedding with wrong dimensions raises ValueError."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_dimension = 4

    result_obj = MagicMock()
    result_obj.embeddings = [[0.1, 0.2, 0.3]]  # expected 4, got 3

    mock_instance = MagicMock()
    mock_instance.embed_query = AsyncMock(return_value=result_obj)
    mock_embedder_cls.return_value = mock_instance

    from app.services.embedding import embed_query

    with pytest.raises(ValueError, match="Query embedding dimension mismatch"):
        await embed_query("test")


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_truncation(mock_embedder_cls, mock_settings):
    """Test that extremely long texts are truncated before embedding."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 1
    mock_settings.embedding_max_retries = 1
    mock_settings.embedding_dimension = 2
    mock_settings.embedding_token_limit = 8192

    # Expected max_chars = int(8192 * 3.0) - 2000 = 22576
    expected_max_chars = 22576

    result_mock = MagicMock()
    result_mock.embeddings = [[0.1, 0.2]]
    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(return_value=result_mock)
    mock_embedder_cls.return_value = mock_instance

    long_text = "a" * 30000
    expected_truncated = "a" * expected_max_chars

    from app.services.embedding import embed_sections

    await embed_sections([long_text])

    # Verify the embedder was called with the truncated text
    mock_instance.embed_documents.assert_called_once()
    call_args = mock_instance.embed_documents.call_args[0][0]
    assert len(call_args) == 1
    assert len(call_args[0]) == expected_max_chars
    assert call_args[0] == expected_truncated


@patch("app.services.embedding.settings")
@patch("app.services.embedding.Embedder")
@pytest.mark.anyio
async def test_embed_sections_truncation_custom_limit(mock_embedder_cls, mock_settings):
    """Test truncation with a custom token limit (e.g. 4096 for smaller models)."""
    mock_settings.embedding_model = "test-model"
    mock_settings.embedding_batch_size = 1
    mock_settings.embedding_max_retries = 1
    mock_settings.embedding_dimension = 2
    mock_settings.embedding_token_limit = 4096

    # Expected max_chars = int(4096 * 3.0) - 2000 = 10288
    expected_max_chars = 10288

    result_mock = MagicMock()
    result_mock.embeddings = [[0.1, 0.2]]
    mock_instance = MagicMock()
    mock_instance.embed_documents = AsyncMock(return_value=result_mock)
    mock_embedder_cls.return_value = mock_instance

    long_text = "a" * 15000

    from app.services.embedding import embed_sections

    await embed_sections([long_text])

    mock_instance.embed_documents.assert_called_once()
    call_args = mock_instance.embed_documents.call_args[0][0]
    assert len(call_args) == 1
    assert len(call_args[0]) == expected_max_chars

