"""Database package for the application."""

import importlib
import logging
import sys

from .base_storage import (
    StorageInterface,
    StorageType,
    StorageError,
    PaginatedResponse,
    generate_id,
    get_current_timestamp
)

from .postgresql_storage import PostgreSQLStorage, PostgreSQLStorageError
from .local_storage import LocalJSONStorage, LocalStorageError

logger = logging.getLogger(__name__)

try:
    from .storage_manager import StorageManager, storage_manager, get_storage, get_storage_type
except KeyError as exc:
    # Streamlit/Hot reload can leave a partially-initialized module in sys.modules
    logger.warning("Reloading backend.database.storage_manager after KeyError: %s", exc)
    sys.modules.pop('backend.database.storage_manager', None)
    storage_manager_module = importlib.import_module('backend.database.storage_manager')
    StorageManager = storage_manager_module.StorageManager
    storage_manager = storage_manager_module.storage_manager
    get_storage = storage_manager_module.get_storage
    get_storage_type = storage_manager_module.get_storage_type

__all__ = [
    # Base types and interfaces
    'StorageInterface',
    'StorageType',
    'StorageError',
    'PaginatedResponse',
    'generate_id',
    'get_current_timestamp',

    # Storage implementations
    'PostgreSQLStorage',
    'PostgreSQLStorageError',
    'LocalJSONStorage',
    'LocalStorageError',

    # Storage management
    'StorageManager',
    'storage_manager',
    'get_storage',
    'get_storage_type',
]
