import pytest
from unittest.mock import MagicMock


@pytest.fixture
def fake_free_service(monkeypatch):
    """Provide a mocked FreeEmbeddingService instance."""
    fake_service = MagicMock()
    fake_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
    fake_service.generate_query_embedding.return_value = [0.4, 0.5, 0.6]
    fake_service.process_document_for_embedding.return_value = [
        {
            "content_text": "nota fiscal de teste",
            "embedding": [0.1] * 768,
            "metadata": {"document_id": "doc-123", "chunk_number": 0, "total_chunks": 1},
        }
    ]

    monkeypatch.setattr(
        "backend.services.fallback_embedding_service.FreeEmbeddingService",
        MagicMock(return_value=fake_service),
    )
    return fake_service


def test_fallback_embedding_service_uses_free_provider(fake_free_service):
    from backend.services.fallback_embedding_service import FallbackEmbeddingService

    service = FallbackEmbeddingService()

    embedding = service.generate_embedding("documento fiscal")
    query_embedding = service.generate_embedding("busca por produtos")
    chunks = service.process_document_for_embedding({"id": "doc-123"})
    info = service.get_service_info()

    assert embedding == [0.1, 0.2, 0.3]
    assert query_embedding == [0.1, 0.2, 0.3]
    assert chunks[0]["metadata"]["document_id"] == "doc-123"
    assert info["primary_service"] == "free"
    assert info["fallback_service"] is None
    assert fake_free_service.generate_embedding.call_args_list == [
        (("documento fiscal",), {}),
        (("busca por produtos",), {}),
    ]


def test_fallback_embedding_service_initialization_error(monkeypatch):
    monkeypatch.setattr(
        "backend.services.fallback_embedding_service.FreeEmbeddingService",
        MagicMock(side_effect=RuntimeError("failed to load model")),
    )

    from backend.services.fallback_embedding_service import FallbackEmbeddingService

    with pytest.raises(RuntimeError):
        FallbackEmbeddingService()
