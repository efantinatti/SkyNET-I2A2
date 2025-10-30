import asyncio
import hashlib
from datetime import datetime as real_datetime
from unittest.mock import MagicMock

from backend.agents.chat_agent import AnalysisCache


class FakeDateTime:
    """Minimal datetime stub returning a deterministic timestamp."""

    @classmethod
    def now(cls):
        return real_datetime(2025, 1, 1, 12, 0, 0)


def test_generate_cache_key_is_order_insensitive():
    storage = MagicMock()
    cache = AnalysisCache(storage)

    context_a = {"document_type": "NFe", "issuer": "12345678000195"}
    context_b = {"issuer": "12345678000195", "document_type": "NFe"}

    key_a = cache._generate_cache_key("Qual a última nota fiscal?", context_a)
    key_b = cache._generate_cache_key("Qual a última nota fiscal?", context_b)

    assert key_a == key_b
    assert len(key_a) == 64
    int(key_a, 16)  # raises ValueError if not valid hex


def test_get_cached_response_returns_entry(monkeypatch):
    storage = MagicMock()
    expected = {
        "content": "Resposta pronta",
        "metadata": {"model": "gemini"},
        "cached": True,
        "cached_session_id": "session-123",
    }
    storage.get_analysis_cache.return_value = expected

    cache = AnalysisCache(storage)
    context = {"query_type": "general"}

    result = asyncio.run(cache.get_cached_response("Pergunta?", context))

    storage.get_analysis_cache.assert_called_once()
    assert result == expected


def test_get_cached_response_handles_errors(monkeypatch):
    storage = MagicMock()
    storage.get_analysis_cache.side_effect = RuntimeError("boom")

    cache = AnalysisCache(storage)
    context = {"query_type": "general"}

    result = asyncio.run(cache.get_cached_response("Pergunta?", context))

    assert result is None


def test_cache_response_persists_data(monkeypatch):
    monkeypatch.setattr("backend.agents.chat_agent.datetime", FakeDateTime)

    storage = MagicMock()
    cache = AnalysisCache(storage)

    query = "Qual é o status do documento?"
    context = {"query_type": "analysis", "document_id": "doc-123"}
    response = "Aqui está o resumo do documento."
    metadata = {"model": "gemini", "tokens_used": 42}

    asyncio.run(
        cache.cache_response(
            query=query,
            context=context,
            response=response,
            metadata=metadata,
            query_type="analysis",
            session_id="session-xyz",
        )
    )

    assert storage.save_analysis_cache.called
    call_kwargs = storage.save_analysis_cache.call_args.kwargs

    expected_key = cache._generate_cache_key(query, context)
    assert call_kwargs["cache_key"] == expected_key
    assert call_kwargs["query_type"] == "analysis"
    assert call_kwargs["query_text"] == query
    assert call_kwargs["context_data"] == context
    assert call_kwargs["response_content"] == response
    assert call_kwargs["response_metadata"] == metadata
    assert call_kwargs["session_id"] == "session-xyz"
    assert call_kwargs["expires_at"].startswith("2025-01-08T12:00:00")
