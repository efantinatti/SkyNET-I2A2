"""
Local JSON file storage implementation for development and fallback.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from .base_storage import (
    StorageInterface,
    PaginatedResponse,
    StorageError,
    generate_id,
    get_current_timestamp
)

logger = logging.getLogger(__name__)


class LocalStorageError(StorageError):
    """Local storage-specific errors."""
    pass


class LocalJSONStorage(StorageInterface):
    """Local JSON file storage implementation."""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.docs_path = self.data_dir / 'documents.json'
        self.history_path = self.data_dir / 'document_history.json'
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.docs_path.exists():
            self.docs_path.write_text('{"documents": [], "next_id": 1}')

    def _read_data(self) -> Dict[str, Any]:
        """Read data from the JSON file."""
        try:
            return json.loads(self.docs_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or doesn't exist, reset it
            self._ensure_data_dir()
            return {"documents": [], "next_id": 1}

    def _write_data(self, data: Dict[str, Any]):
        """Write data to the JSON file."""
        self.docs_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def save_fiscal_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Save a fiscal document to local JSON storage."""
        data = self._read_data()
        documents = data.get("documents", [])

        # Generate ID if not provided
        if "id" not in document or not document["id"]:
            document["id"] = str(data["next_id"])
            data["next_id"] += 1
            document["created_at"] = get_current_timestamp()
            documents.append(document)
        else:
            # Update existing document
            doc_id = document["id"]
            for i, doc in enumerate(documents):
                if doc.get("id") == doc_id:
                    document["updated_at"] = get_current_timestamp()
                    documents[i] = document
                    break
            else:
                document["created_at"] = get_current_timestamp()
                documents.append(document)

        # Save back to file
        data["documents"] = documents
        self._write_data(data)
        return document

    def get_fiscal_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single fiscal document by ID."""
        data = self._read_data()
        for doc in data.get("documents", []):
            if doc.get("id") == doc_id:
                return doc
        return None

    def get_fiscal_documents(
        self,
        page: int = 1,
        page_size: int = 10,
        **filters
    ) -> PaginatedResponse:
        """Get a paginated list of fiscal documents with optional filtering."""
        data = self._read_data()
        documents = data.get("documents", [])

        # Apply filters
        if filters:
            filtered_docs = []
            for doc in documents:
                match = True
                for key, value in filters.items():
                    if key in doc and doc[key] != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
            documents = filtered_docs

        # Handle page_size=0 as "use default"
        if page_size <= 0:
            page_size = 10  # Default page size

        # Pagination
        total = len(documents)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = documents[start:end]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def delete_fiscal_document(self, doc_id: str) -> bool:
        """Delete a fiscal document by ID."""
        data = self._read_data()
        documents = data.get("documents", [])

        for i, doc in enumerate(documents):
            if doc.get("id") == doc_id:
                del documents[i]
                data["documents"] = documents
                self._write_data(data)
                return True

        return False

    def add_document_analysis(self, doc_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add an analysis to a document."""
        document = self.get_fiscal_document(doc_id)
        if not document:
            raise LocalStorageError(f"Document {doc_id} not found")

        # Add analysis to document
        if "analyses" not in document:
            document["analyses"] = []

        # Generate analysis ID
        analysis_id = len(document["analyses"]) + 1
        analysis["id"] = analysis_id
        analysis["created_at"] = get_current_timestamp()

        document["analyses"].append(analysis)
        document["updated_at"] = get_current_timestamp()

        # Update the document
        self.save_fiscal_document(document)
        return analysis

    def save_history(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Save a history event to local storage."""
        events = self._load_history()

        if not isinstance(events, list):
            events = []

        if 'id' not in event:
            event['id'] = generate_id()
        if 'created_at' not in event:
            event['created_at'] = get_current_timestamp()

        events.append(event)

        # Ensure directory exists before saving
        self._ensure_data_dir()
        self.history_path.write_text(
            json.dumps(events, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        logger.debug(f"History saved to {self.history_path}")
        return event

    def get_document_history(self, fiscal_document_id: str) -> List[Dict[str, Any]]:
        """Get history events for a document."""
        events = self._load_history()
        return [
            e for e in events
            if e.get('fiscal_document_id') == fiscal_document_id
        ]

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from the JSON file."""
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            logger.error(f"Error loading history file: {self.history_path}. Returning empty list.")
            return []
