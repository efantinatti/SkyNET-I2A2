"""Tests for StorageInterface implementation validation."""
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from typing import Dict, Any, List, Optional
from backend.database import StorageInterface, PaginatedResponse
import pytest


class DummyStorage(StorageInterface):
    """Minimal implementation of StorageInterface for testing."""

    def save_fiscal_document(self, record):
        return record

    def get_fiscal_document(self, doc_id):
        return None

    def get_fiscal_documents(self, filters=None, page=1, page_size=50):
        return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

    def delete_fiscal_document(self, doc_id):
        return False

    def add_document_analysis(self, doc_id, analysis):
        return analysis

    def save_history(self, event):
        return event

    def get_document_history(self, fiscal_document_id):
        return []


def test_interface_implementation():
    """Test that a class implementing all methods can be instantiated."""
    storage = DummyStorage()
    assert isinstance(storage, StorageInterface)


class BrokenStorage(StorageInterface):
    """Incomplete implementation missing required methods."""
    pass


def test_incomplete_implementation():
    """Test that an incomplete implementation raises TypeError."""
    class IncompleteStorage(StorageInterface):
        def save_fiscal_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
            pass

        def get_fiscal_documents(
            self,
            filters: Optional[Dict[str, str]] = None,
            page: int = 1,
            page_size: int = 50
        ) -> PaginatedResponse:
            pass

        def get_fiscal_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
            pass

        # Missing: delete_fiscal_document, add_document_analysis, save_history, get_document_history

    # Verifica se a classe abstrata está sendo implementada corretamente
    with pytest.raises(TypeError):
        # Deve lançar TypeError porque faltam métodos abstratos
        storage = IncompleteStorage()


def test_paginated_response_typing():
    """Test PaginatedResponse type validation."""
    # Valid response
    response: PaginatedResponse = {
        'items': [],
        'total': 0,
        'page': 1,
        'page_size': 50
    }
    assert isinstance(response, dict)
    
    # Would raise type error in a typed environment:
    # response: PaginatedResponse = {'items': []}  # Missing required fields