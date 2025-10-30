import numpy as np
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def vector_store(monkeypatch):
    from backend.services.vector_store_service import VectorStoreService

    monkeypatch.setattr(VectorStoreService, "_initialize_connection", lambda self: None)

    store = VectorStoreService()
    store._connection = MagicMock()
    return store


def test_save_document_chunks_success(vector_store, monkeypatch):
    chunk_metadata = {"document_id": "doc-789", "chunk_number": 0}
    chunks = [
        {
            "content_text": "Nota fiscal emitida",
            "embedding": np.ones(768).tolist(),
            "metadata": chunk_metadata,
        }
    ]

    execute_calls = [
        {"id": "doc-789"},  # document exists check
        {"id": "chunk-123"},  # insert returning id
    ]

    vector_store._execute_query = MagicMock(side_effect=execute_calls)

    saved_ids = vector_store.save_document_chunks(chunks)

    assert saved_ids == ["chunk-123"]
    vector_store._execute_query.assert_called()


def test_update_document_embedding_status(vector_store):
    vector_store._execute_query = MagicMock(return_value=1)

    status = vector_store.update_document_embedding_status("doc-123", "processing")

    assert status is True
    vector_store._execute_query.assert_called_once()


def test_update_document_embedding_status_failure(vector_store):
    vector_store._execute_query = MagicMock(return_value=0)

    status = vector_store.update_document_embedding_status("doc-123", "processing")

    assert status is False


def test_search_similar_chunks_returns_context(vector_store):
    base_result = [
        {
            "id": "chunk-1",
            "fiscal_document_id": "doc-abc",
            "chunk_number": 0,
            "content_text": "Produtos vendidos",
            "embedding": [0.1] * 768,
            "metadata": {"document_id": "doc-abc"},
            "created_at": "2024-01-01T00:00:00Z",
            "similarity_score": 0.85,
        }
    ]
    doc_result = {
        "file_name": "nota.pdf",
        "document_type": "NFe",
        "document_number": "12345",
        "issuer_cnpj": "12345678000199",
        "extracted_data": {},
        "validation_status": "validated",
        "classification": {},
    }

    vector_store._execute_query = MagicMock(side_effect=[base_result, doc_result])

    chunks = vector_store.search_similar_chunks([0.1] * 768, similarity_threshold=0.5, max_results=5)

    assert len(chunks) == 1
    assert chunks[0]["fiscal_document_id"] == "doc-abc"
    assert vector_store._execute_query.call_count == 2
