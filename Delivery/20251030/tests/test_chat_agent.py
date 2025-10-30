import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.chat_agent import (
    AnalysisCache,
    ChatAgent,
    ChatResponse,
    DocumentSearchEngine,
)


@pytest.fixture
def chat_agent(monkeypatch):
    storage = MagicMock()

    # Always assume Gemini is available to exercise cache logic
    monkeypatch.setattr("backend.agents.chat_agent.GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr("backend.agents.chat_agent.ChatGoogleGenerativeAI", MagicMock(return_value=MagicMock(name="gemini")))

    # Stub DocumentAnalyzer to avoid hitting real storage
    fake_analyzer = AsyncMock()
    fake_analyzer.get_all_documents_summary.return_value = {"total_documents": 0}
    monkeypatch.setattr("backend.agents.chat_agent.DocumentAnalyzer", MagicMock(return_value=fake_analyzer))

    agent = ChatAgent(storage)
    agent.document_analyzer = fake_analyzer

    return agent, storage


@pytest.fixture
async def session(chat_agent):
    agent, storage = chat_agent
    storage.create_chat_session.return_value = {"id": "session-1"}
    return agent, storage, await agent.create_session("teste")


def test_generate_response_same_session_cache(monkeypatch, chat_agent):
    agent, storage = chat_agent

    # Configure cache to return hit for same session
    cached_payload = {
        "content": "Resposta anterior",
        "metadata": {"model": "gemini"},
        "cached": True,
        "cached_session_id": "session-abc",
        "cached_at": "2025-01-01T12:00:00Z",
    }
    agent.cache.get_cached_response = AsyncMock(return_value=cached_payload)
    agent.save_message = AsyncMock()

    response: ChatResponse = asyncio.run(
        agent.generate_response("session-abc", "Qual a análise?", context={"query_type": "analysis"})
    )

    agent.cache.get_cached_response.assert_awaited_once()
    agent.save_message.assert_awaited_once()
    assert response.cached is True
    assert "Pergunta repetida" in response.content
    assert response.metadata["reused_in_session"] is True
    assert response.metadata["tokens_used"] == 0


def test_generate_response_cache_other_session(monkeypatch, chat_agent):
    agent, storage = chat_agent

    # Cache hit belongs to another session – should ignore and continue pipeline

    cached_payload = {
        "content": "Resposta prévia",
        "metadata": {"model": "gemini"},
        "cached": True,
        "cached_session_id": "session-xyz",
        "cached_at": "2025-01-01T12:00:00Z",
    }
    agent.cache.get_cached_response = AsyncMock(return_value=cached_payload)

    # Avoid hitting Gemini for the test
    agent._handle_specific_search = AsyncMock(return_value=ChatResponse("Resposta nova", {"tokens_used": 10}))

    response = asyncio.run(
        agent.generate_response("session-abc", "Preciso da análise", context={"query_type": "analysis"})
    )

    agent.cache.get_cached_response.assert_awaited_once()
    agent._handle_specific_search.assert_awaited_once()
    assert response.cached is False
    assert response.content == "Resposta nova"


def test_generate_response_no_cache(monkeypatch, chat_agent):
    agent, storage = chat_agent

    agent.cache.get_cached_response = AsyncMock(return_value=None)
    agent._handle_count_request = AsyncMock(return_value=ChatResponse("Total", {}))

    response = asyncio.run(agent.generate_response("session", "Qual a quantidade total?", context={}))

    agent.cache.get_cached_response.assert_not_awaited()
    agent._handle_count_request.assert_awaited_once()
    assert response.content == "Total"


def test_generate_response_missing_model(chat_agent):
    agent, storage = chat_agent
    agent.model = None
    agent.save_message = AsyncMock()

    response = asyncio.run(agent.generate_response("session", "Olá", context=None))

    agent.save_message.assert_awaited_once()
    assert response.cached is False
    assert "API do Google Gemini" in response.content
    assert response.metadata["error"] is True


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Quero um resumo dos documentos fiscais", True),
        ("Quantos documentos temos?", False),
        ("Liste todos os documentos", False),
    ],
)
def test_is_summary_request(chat_agent, query, expected):
    agent, _ = chat_agent
    assert agent._is_summary_request(query) is expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Liste todos os documentos", False),
        ("Quais são as notas mais recentes?", True),
        ("Quero uma análise completa", True),
        ("Mostre o total", False),
    ],
)
def test_is_list_request(chat_agent, query, expected):
    agent, _ = chat_agent
    assert agent._is_list_request(query) is expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Qual a quantidade total de documentos?", True),
        ("Quantos documentos temos?", True),
        ("Mostre os documentos", False),
    ],
)
def test_is_count_request(chat_agent, query, expected):
    agent, _ = chat_agent
    assert agent._is_count_request(query) is expected


def test_handle_count_request_formats_summary(chat_agent):
    agent, _ = chat_agent

    summary_data = {
        "total_documents": 2,
        "total_value": 150.0,
        "by_type": {"NFe": 1, "NFCe": 1},
        "by_issuer": {"Empresa A": 1, "Empresa B": 1},
    }

    agent._get_all_documents_summary = AsyncMock(return_value=summary_data)
    agent.model = MagicMock()
    agent.model.invoke.return_value = SimpleNamespace(content="Resposta formatada")
    agent.model_name = "gemini-2.0-flash-exp"
    agent.save_message = AsyncMock()

    response = asyncio.run(agent._handle_count_request("session", "Quantos documentos?"))

    agent._get_all_documents_summary.assert_awaited_once()
    agent.save_message.assert_awaited_once()
    assert "Resposta" in response.content
    assert response.metadata["query_type"] == "count"
    assert response.tokens_used > 0


def test_analysis_cache_roundtrip():
    storage = MagicMock()
    storage.get_analysis_cache.return_value = {
        "content": "cached",
        "metadata": {"model": "gemini"},
        "cached_session_id": "session-1",
        "cached_at": "2025-01-01T00:00:00",
    }
    storage.save_analysis_cache.return_value = None

    cache = AnalysisCache(storage)

    cached = asyncio.run(cache.get_cached_response("pergunta", {"foo": "bar"}))
    assert cached["content"] == "cached"

    asyncio.run(cache.cache_response("pergunta", {"foo": "bar"}, "resp", {"model": "gemini"}))
    storage.save_analysis_cache.assert_called_once()


def test_document_search_engine_filters_results():
    class DummyStorage:
        async def get_fiscal_documents(self, **_kwargs):
            return SimpleNamespace(
                items=[
                    {
                        "id": "1",
                        "file_name": "nota1.xml",
                        "document_number": "123",
                        "extracted_data": {
                            "emitente": {"razao_social": "Empresa A"},
                            "destinatario": {"razao_social": "Cliente B"},
                        },
                    },
                    {
                        "id": "2",
                        "file_name": "nota2.xml",
                        "document_number": "456",
                        "extracted_data": {
                            "emitente": {"razao_social": "Outro"},
                            "destinatario": {"razao_social": "Cliente C"},
                        },
                    },
                ]
            )

    search_engine = DocumentSearchEngine(DummyStorage())
    context = asyncio.run(search_engine.search_documents("Empresa A", limit=5))

    assert len(context.documents) == 1
    assert context.documents[0]["file_name"] == "nota1.xml"


@pytest.mark.parametrize(
    "query,handler_attr",
    [
        ("Quero um resumo dos documentos", "_handle_summary_request"),
        ("Liste os documentos recentes", "_handle_list_request"),
        ("Preciso de detalhes do documento 123", "_handle_specific_search"),
    ],
)
def test_generate_response_dispatch(monkeypatch, chat_agent, query, handler_attr):
    agent, storage = chat_agent
    agent.cache.get_cached_response = AsyncMock(return_value=None)

    handler = AsyncMock(return_value=ChatResponse("ok", {}))
    monkeypatch.setattr(agent, handler_attr, handler)

    response = asyncio.run(agent.generate_response("session", query, context={}))

    handler.assert_awaited_once()
    assert response.content == "ok"
