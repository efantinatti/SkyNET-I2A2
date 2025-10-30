import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.chat_agent import ChatResponse
from backend.agents.chat_coordinator import ChatCoordinator


class StubChatAgent:
    def __init__(self, storage):
        self.storage = storage
        self.saved_messages = []
        self.history = [{'role': 'user', 'content': 'Olá'}]
        self.session_counter = 0

    async def create_session(self, session_name: str = None) -> str:
        self.session_counter += 1
        return f"session-{self.session_counter}"

    async def save_message(self, session_id: str, message_type: str, content: str, metadata: dict = None):
        self.saved_messages.append((session_id, message_type, content, metadata or {}))

    async def generate_response(self, session_id: str, query: str, context: dict = None) -> ChatResponse:
        return ChatResponse(content=f"Resposta para {query}", metadata={'tokens_used': 5}, cached=False, tokens_used=5)

    async def get_conversation_history(self, session_id: str):
        return list(self.history)


@pytest.fixture
async def coordinator(monkeypatch):
    storage = MagicMock()
    storage.save_chat_message = AsyncMock()
    storage.get_chat_messages = MagicMock(return_value=[{'role': 'user', 'content': 'Olá'}])

    monkeypatch.setattr('backend.agents.chat_coordinator.ChatAgent', StubChatAgent)
    monkeypatch.setattr('backend.agents.chat_coordinator.DocumentAnalysisTool', MagicMock())
    monkeypatch.setattr('backend.agents.chat_coordinator.CSVAnalysisTool', MagicMock())
    monkeypatch.setattr('backend.agents.chat_coordinator.InsightGenerator', MagicMock())

    return ChatCoordinator(storage), storage


def test_initialize_session_uses_chat_agent(coordinator):
    chat_coord, _ = coordinator
    session_id = asyncio.run(chat_coord.initialize_session('teste'))
    assert session_id.startswith('session-')


def test_process_query_success(coordinator):
    chat_coord, storage = coordinator

    result = asyncio.run(chat_coord.process_query('session-1', 'Preciso de um resumo'))

    assert result['success'] is True
    assert 'Resposta para' in result['response']
    assert result['tokens_used'] == 5
    storage.save_chat_message.assert_called_once()


def test_process_query_handles_error(coordinator):
    chat_coord, storage = coordinator
    chat_coord.chat_agent.generate_response = AsyncMock(side_effect=RuntimeError('falha'))

    result = asyncio.run(chat_coord.process_query('session-1', 'Erro por favor'))

    assert result['success'] is False
    assert 'falha' in result['error']


def test_save_message_wraps_chat_agent(coordinator):
    chat_coord, _ = coordinator
    chat_coord.chat_agent.save_message = AsyncMock()

    asyncio.run(chat_coord.save_message('session-2', 'assistant', 'Olá'))

    chat_coord.chat_agent.save_message.assert_awaited_once()


def test_save_message_propagates_error(coordinator):
    chat_coord, _ = coordinator
    chat_coord.chat_agent.save_message = AsyncMock(side_effect=RuntimeError('falha ao salvar'))

    with pytest.raises(RuntimeError):
        asyncio.run(chat_coord.save_message('session-3', 'assistant', 'Olá'))


def test_get_session_history_success(coordinator):
    chat_coord, _ = coordinator
    history = asyncio.run(chat_coord.get_session_history('session-1'))
    assert history[0]['content'] == 'Olá'


def test_get_session_history_error_returns_empty(coordinator):
    chat_coord, _ = coordinator
    chat_coord.chat_agent.get_conversation_history = AsyncMock(side_effect=RuntimeError('falha'))
    history = asyncio.run(chat_coord.get_session_history('session-1'))
    assert history == []


@pytest.mark.parametrize(
    'query,expected_type',
    [
        ('Quero um resumo', 'document_analysis'),
        ('Análise de CSV', 'csv_analysis'),
        ('Quero um insight financeiro', 'financial_analysis'),
        ('Encontrar erros e validações', 'validation_analysis'),
        ('Pergunta genérica', 'general'),
    ],
)
def test_enhance_context_sets_query_type(coordinator, query, expected_type):
    chat_coord, _ = coordinator
    context = asyncio.run(chat_coord._enhance_context(query, None))
    assert context['query_type'] == expected_type


def test_enhance_context_preserves_existing_context(coordinator):
    chat_coord, _ = coordinator
    context = asyncio.run(chat_coord._enhance_context('Quero CSV', {'limit': 5}))
    assert context['query_type'] == 'csv_analysis'
    assert context['limit'] == 5
