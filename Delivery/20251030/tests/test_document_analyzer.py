import asyncio
import json
from datetime import datetime

import pytest

from backend.services.document_analyzer import DocumentAnalyzer


class DummyResult:
    def __init__(self, items):
        self.items = items


class DummyDB:
    def __init__(self, items=None, raise_error=False):
        self.items = items or []
        self.raise_error = raise_error
        self.calls = []

    async def get_fiscal_documents(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        if self.raise_error:
            raise RuntimeError("db error")
        return DummyResult(list(self.items))


def run(coro):
    return asyncio.run(coro)


def test_get_all_documents_summary_basic():
    docs = [
        {
            "id": "doc-1",
            "file_name": "nota123.xml",
            "document_type": "NFe",
            "issuer_cnpj": "11111111000100",
            "created_at": "2025-01-01T00:00:00Z",
            "validation_status": "success",
            "extracted_data": {"total": "100.50"},
        },
        {
            "id": "doc-2",
            "file_name": "mdfe001.xml",
            "document_type": "MDFE",
            "issuer_cnpj": "22222222000100",
            "created_at": "2025-01-02T00:00:00Z",
            "validation_status": "warning",
            "extracted_data": json.dumps({"valor_total": 50}),
        },
        {
            "id": "doc-3",
            "file_name": "nota-sem-tipo.xml",
            "document_type": "",
            "issuer_cnpj": "11111111000100",
            "created_at": "2025-01-03T00:00:00Z",
            "validation_status": "pending",
            "extracted_data": {"mod": "65", "total": 25},
        },
    ]

    db = DummyDB(docs)
    analyzer = DocumentAnalyzer(db=db)

    summary = run(analyzer.get_all_documents_summary())

    assert summary["total_documents"] == 3
    assert summary["by_type"]["NF-e"] == 1
    assert summary["by_type"]["MDF-e"] == 1
    assert summary["by_type"]["NFC-e"] == 1
    assert summary["by_issuer"]["11111111000100"] == 2
    assert pytest.approx(summary["total_value"], 0.01) == 175.5

    # Ensure documents list preserves categorization information
    categorized = {doc["id"]: doc["categorized_type"] for doc in summary["documents"]}
    assert categorized["doc-1"] == "NF-e"
    assert categorized["doc-2"] == "MDF-e"
    assert categorized["doc-3"] == "NFC-e"


def test_get_all_documents_summary_with_filter():
    docs = [{"id": "doc-1", "document_type": "NFE", "issuer_cnpj": "1"}]
    db = DummyDB(docs)
    analyzer = DocumentAnalyzer(db=db)

    time_filter = datetime(2025, 1, 1, 12, 0, 0)
    run(analyzer.get_all_documents_summary(time_filter=time_filter))

    assert db.calls
    kwargs = db.calls[0]["kwargs"]
    assert "created_after" in kwargs
    assert kwargs["created_after"].startswith("2025-01-01T12:00:00")


def test_get_all_documents_summary_error_returns_defaults():
    analyzer = DocumentAnalyzer(db=DummyDB(raise_error=True))

    summary = run(analyzer.get_all_documents_summary())

    assert summary == {
        "total_documents": 0,
        "by_type": {},
        "by_issuer": {},
        "total_value": 0.0,
        "documents": [],
    }


def test_get_documents_summary_passes_filters():
    docs = [{"id": "1", "document_type": "NFE", "issuer_cnpj": "1", "extracted_data": {"total": 10}}]
    db = DummyDB(docs)
    analyzer = DocumentAnalyzer(db=db)

    summary = run(analyzer.get_documents_summary(filters={"issuer_cnpj": "1"}))

    assert summary["total_documents"] == 1
    kwargs = db.calls[0]["kwargs"]
    assert kwargs["issuer_cnpj"] == "1"


def test_search_documents_filters_results():
    docs = [
        {"file_name": "Nota Fiscal 001", "document_type": "NFE", "document_number": "123", "issuer_cnpj": "11"},
        {"file_name": "Manifesto MDFE", "document_type": "MDFE", "document_number": "456", "issuer_cnpj": "22"},
    ]

    db = DummyDB(docs)
    analyzer = DocumentAnalyzer(db=db)

    results = run(analyzer.search_documents("manifesto", limit=5))

    assert len(results) == 1
    assert results[0]["document_number"] == "456"
