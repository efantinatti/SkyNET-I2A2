"""
Base storage interfaces and types for the application.
"""
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone, UTC
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class StorageType(Enum):
    """Supported storage types."""
    LOCAL_JSON = "local_json"
    POSTGRESQL = "postgresql"


class StorageError(Exception):
    """Base class for storage-related errors."""
    pass


@dataclass
class PaginatedResponse:
    """Standard response format for paginated queries."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }


class StorageInterface(ABC):
    """Abstract base class defining storage backend interface."""

    @abstractmethod
    def save_fiscal_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Save a fiscal document."""
        pass

    @abstractmethod
    def get_fiscal_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single fiscal document by ID."""
        pass

    @abstractmethod
    def get_fiscal_documents(
        self,
        page: int = 1,
        page_size: int = 10,
        **filters
    ) -> PaginatedResponse:
        """Get a paginated list of fiscal documents with optional filtering."""
        pass

    @abstractmethod
    def delete_fiscal_document(self, doc_id: str) -> bool:
        """Delete a fiscal document by ID."""
        pass

    @abstractmethod
    def add_document_analysis(self, doc_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add an analysis to a document."""
        pass

    @abstractmethod
    def save_history(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Save a history event."""
        pass

    @abstractmethod
    def get_document_history(self, fiscal_document_id: str) -> List[Dict[str, Any]]:
        """Get history events for a document."""
        pass


def generate_id() -> str:
    """Generate a UUID for new records."""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(UTC).isoformat()
