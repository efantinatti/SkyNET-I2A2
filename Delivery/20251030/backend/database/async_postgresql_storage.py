"""Asynchronous wrapper for PostgreSQLStorage.

This module provides an asyncio-friendly interface on top of the existing
synchronous PostgreSQLStorage implementation. It delegates work to the
underlying storage using ``asyncio.to_thread`` so callers can ``await`` the
methods without blocking the event loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .base_storage import PaginatedResponse
from .postgresql_storage import PostgreSQLStorage


class AsyncPostgreSQLStorage:
    """Async adapter around :class:`PostgreSQLStorage`."""

    def __init__(self, storage: Optional[PostgreSQLStorage] = None) -> None:
        self._storage = storage or PostgreSQLStorage()

    async def get_fiscal_documents(self, *args: Any, **kwargs: Any) -> PaginatedResponse:
        return await asyncio.to_thread(self._storage.get_fiscal_documents, *args, **kwargs)

    async def get_fiscal_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._storage.get_fiscal_document, doc_id)

    async def save_fiscal_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self._storage.save_fiscal_document, document)

    async def search_fiscal_documents(self, *args: Any, **kwargs: Any) -> PaginatedResponse:
        return await asyncio.to_thread(self._storage.get_fiscal_documents, *args, **kwargs)

    async def delete_fiscal_document(self, doc_id: str) -> bool:
        return await asyncio.to_thread(self._storage.delete_fiscal_document, doc_id)

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying storage.

        This allows synchronous helper methods (e.g., configuration helpers)
        to be accessed directly when needed.
        """
        return getattr(self._storage, name)
