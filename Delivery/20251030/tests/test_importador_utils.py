import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from frontend.pages.importador_utils import process_single_file


def make_uploaded(name: str, buffer: bytes = b"data"):
    file = MagicMock()
    file.name = name
    file.getbuffer.return_value = buffer
    return file


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def dummy_tmp_dir(tmp_path):
    return tmp_path


class DummyCoordinator:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def run_task(self, task, payload):
        self.calls.append((task, payload))
        if isinstance(self.responses[task], Exception):
            raise self.responses[task]
        return self.responses[task]


@pytest.fixture(autouse=True)
def patch_coordinator(monkeypatch):
    dummy = DummyCoordinator(
        {
            "extract": {"document_type": "NFe", "numero": "1", "total": 100},
            "classify": {"categoria": "venda", "validacao": {"status": "success"}},
        }
    )
    monkeypatch.setitem(sys.modules, "backend.agents.coordinator", dummy)
    yield dummy
    sys.modules.pop("backend.agents.coordinator", None)
@pytest.fixture
def streamlit_state(monkeypatch):
    import tests.conftest as conf

    st = conf.streamlit
    st.session_state.clear()

    def session_getattr(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    monkeypatch.setattr(type(st.session_state), "__getattr__", session_getattr, raising=False)

    def immediate_task(coro):
        if asyncio.iscoroutine(coro):
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        return coro

    monkeypatch.setattr(asyncio, "create_task", immediate_task)
    return st


def test_process_single_file_xml_success(monkeypatch, dummy_tmp_dir, streamlit_state):
    storage = MagicMock()
    storage.save_fiscal_document.return_value = {"id": "doc-1"}
    storage.get_fiscal_documents.return_value = SimpleNamespace(items=[{"id": "doc-1"}])

    async def dummy_process(document):
        return {"success": True}

    rag_service = MagicMock()
    rag_service.process_document_for_rag = MagicMock(side_effect=lambda doc: dummy_process(doc))
    streamlit_state.session_state["rag_service"] = rag_service
    streamlit_state.rag_service = rag_service

    prepare = MagicMock(return_value={"document_type": "NFe", "validation_status": "success"})
    validate = MagicMock(return_value=True)

    uploaded = make_uploaded("nota.xml")

    result = process_single_file(uploaded, storage, dummy_tmp_dir, prepare, validate)

    assert result["success"] is True
    prepare.assert_called_once()
    storage.save_fiscal_document.assert_called_once()
    storage.get_fiscal_documents.assert_called_once_with(id="doc-1", page=1, page_size=1)


def test_process_single_file_invalid_xml(monkeypatch, dummy_tmp_dir):
    storage = MagicMock()
    prepare = MagicMock()
    validate = MagicMock(return_value=False)

    uploaded = make_uploaded("nota.xml")

    result = process_single_file(uploaded, storage, dummy_tmp_dir, prepare, validate)

    assert result["success"] is False
    assert result["error"] == "Dados inválidos após extração do XML"
    storage.save_fiscal_document.assert_not_called()


def test_process_single_file_image_with_failed_ocr(monkeypatch, dummy_tmp_dir):
    responses = {
        "extract": {"raw_text": ""},
        "classify": {},
    }
    dummy = DummyCoordinator(responses)
    monkeypatch.setitem(sys.modules, "backend.agents.coordinator", dummy)

    storage = MagicMock()
    prepare = MagicMock()
    validate = MagicMock(return_value=True)

    uploaded = make_uploaded("nota.png")

    result = process_single_file(uploaded, storage, dummy_tmp_dir, prepare, validate)

    assert result["success"] is False
    assert "Tipo de arquivo não suportado" in result["error"]
    prepare.assert_not_called()
    storage.save_fiscal_document.assert_not_called()


def test_process_single_file_handles_exceptions(monkeypatch, dummy_tmp_dir):
    faulty_storage = MagicMock()
    faulty_storage.save_fiscal_document.side_effect = RuntimeError("db down")

    prepare = MagicMock(return_value={"document_type": "NFe"})
    validate = MagicMock(return_value=True)

    uploaded = make_uploaded("nota.xml")

    result = process_single_file(uploaded, faulty_storage, dummy_tmp_dir, prepare, validate)

    assert result["success"] is False
    assert "db down" in result["error"]
    faulty_storage.save_fiscal_document.assert_called_once()
