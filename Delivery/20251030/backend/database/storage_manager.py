"""
Storage manager for the application.
Handles initialization and switching between storage backends.
"""
import logging
from typing import Optional
import uuid
from datetime import datetime
import asyncio

from config import SUPABASE_URL, SUPABASE_KEY, DATABASE_CONFIG
from .base_storage import StorageInterface, StorageType
from .local_storage import LocalJSONStorage, LocalStorageError

# Import PostgreSQL storage with error handling
try:
    from .postgresql_storage import PostgreSQLStorage, PostgreSQLStorageError
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    PostgreSQLStorage = None
    PostgreSQLStorageError = Exception

try:
    from .async_postgresql_storage import AsyncPostgreSQLStorage
except ImportError:
    AsyncPostgreSQLStorage = None

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Centralized storage manager for the application.
    Ensures consistent storage status across all components.
    """
    _instance = None
    _initialized = False
    _lock = None  # Will be initialized on first use

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StorageManager, cls).__new__(cls)
            # Initialize instance variables
            cls._instance._storage = None
            cls._instance._status = "🔃 Inicializando armazenamento..."
            cls._instance._status_type = "info"  # Can be "info", "success", "warning", or "error"
            cls._instance._initialized = False
            cls._instance._async_storage = None
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        # Initialize the lock if not already done
        if StorageManager._lock is None:
            import threading
            StorageManager._lock = threading.Lock()
            
        with StorageManager._lock:
            if not self._initialized:  # Double-checked locking pattern
                self._initialize_storage()
                self._initialized = True

    def _initialize_storage(self):
        """Initialize the appropriate storage backend."""
        try:
            # First, try to use PostgreSQL if credentials are available
            if self._has_postgresql_config() and POSTGRESQL_AVAILABLE:
                try:
                    logger.info("Attempting to initialize PostgreSQL storage...")
                    self._storage = PostgreSQLStorage()
                    self._async_storage = None
                    # Test connection synchronously
                    self._test_postgresql_connection()
                    self._status = "✅ Conectado ao PostgreSQL (via psycopg2)"
                    logger.info("Successfully connected to PostgreSQL")
                except Exception as e:
                    logger.warning(f"PostgreSQL connection failed: {str(e)}")
                    logger.warning("Falling back to local storage")
                    self._storage = LocalJSONStorage()
                    self._status = "⚠️ Falha na conexão PostgreSQL, usando armazenamento local"
                    self._status_type = "warning"
                    self._status_type = "success"
                except PostgreSQLStorageError as e:
                    logger.warning(f"PostgreSQL connection failed ({e}), falling back to local storage")
                    self._storage = LocalJSONStorage()
                    self._status = "⚠️ Falha na conexão PostgreSQL, usando armazenamento local"
                    self._status_type = "warning"
                except Exception as e:
                    logger.warning(f"PostgreSQL error ({e}), falling back to local storage")
                    self._storage = LocalJSONStorage()
                    self._status = "⚠️ Erro no PostgreSQL, usando armazenamento local"
                    self._status_type = "warning"
            else:
                if not POSTGRESQL_AVAILABLE:
                    self._storage = LocalJSONStorage()
                    self._status = "⚠️ PostgreSQL não disponível (módulo psycopg2), usando armazenamento local"
                    self._status_type = "warning"
                else:
                    raise ValueError("PostgreSQL configuration not available")

        except (Exception) as e:
            # Fall back to local storage
            logger.warning(f"Storage initialization failed ({e}), falling back to local storage")
            self._storage = LocalJSONStorage()
            self._async_storage = None
            self._status = "⚠️ Usando armazenamento local (arquivos JSON)"
            self._status_type = "warning"
            logger.error(f"Error initializing storage: {str(e)}")

    def _has_postgresql_config(self) -> bool:
        """Check if PostgreSQL configuration is available."""
        required_fields = ['dbname', 'user', 'password', 'host', 'port']
        return all(DATABASE_CONFIG.get(field) for field in required_fields)

    def _test_postgresql_connection(self):
        """Test PostgreSQL connection."""
        try:
            # Get a connection and execute a test query
            conn = self._storage._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                conn.close()  # Close the connection after the test
        except Exception as e:
            if hasattr(self._storage, '_connection') and self._storage._connection:
                try:
                    self._storage._connection.close()
                except:
                    pass
            self._status = f" Falha na conexão com o PostgreSQL: {str(e)}"
            self._status_type = "error"
            logger.error(f"PostgreSQL connection test failed: {str(e)}")
            raise

    @property
    def storage(self) -> StorageInterface:
        """Get the storage instance."""
        if self._storage is None:
            self._initialize_storage()
        return self._storage

    def get_async_storage(self):
        """Get (and lazily create) an async wrapper around the storage."""
        if not POSTGRESQL_AVAILABLE or not isinstance(self.storage, PostgreSQLStorage):
            raise RuntimeError("Async storage is only available when PostgreSQL storage is active")

        if AsyncPostgreSQLStorage is None:
            raise RuntimeError("AsyncPostgreSQLStorage adapter is not available")

        if self._async_storage is None:
            self._async_storage = AsyncPostgreSQLStorage(self.storage)

        return self._async_storage

    @property
    def storage_type(self) -> StorageType:
        """Get the current storage type."""
        if POSTGRESQL_AVAILABLE and isinstance(self._storage, PostgreSQLStorage):
            return StorageType.POSTGRESQL
        else:
            return StorageType.LOCAL_JSON

    @property
    def status(self) -> str:
        """Get the current storage status message."""
        return self._status

    @property
    def status_type(self) -> str:
        """Get the status type for display (info, success, warning, error)."""
        return self._status_type

    def display_status(self, container=None):
        """Display the storage status in the provided container or the sidebar.

        Args:
            container: Streamlit container to display the status in. If None, uses the sidebar.
        """
        try:
            import streamlit as st
            display = container if container is not None else st.sidebar

            if self._status_type == "success":
                display.success(self._status)
            elif self._status_type == "warning":
                display.warning(self._status)
            elif self._status_type == "error":
                display.error(self._status)
            else:
                display.info(self._status)
        except ImportError:
            # Streamlit not available
            print(f"Storage Status: {self._status}")

    @property
    def supabase_client(self):
        """Get a PostgreSQL-based client that mimics Supabase API for chat system compatibility."""
        # Since chat system now uses PostgreSQL directly, this method just returns the storage
        # This maintains backward compatibility for any code that still references supabase_client
        if not isinstance(self._storage, PostgreSQLStorage):
            # If not using PostgreSQL, return a mock client that raises errors
            class MockClient:
                def table(self, table_name):
                    raise AttributeError("PostgreSQL storage not available - chat system requires PostgreSQL")
            return MockClient()

        # Return the storage directly since chat system now uses it directly
        return self._storage

    def close(self):
        """Close any open connections."""
        if hasattr(self._storage, 'close'):
            self._storage.close()

    def __del__(self):
        """Cleanup when the manager is destroyed."""
        self.close()


class _StorageManagerSingleton:
    _instance = None
    _initialized = False
    _lock = None

    def __init__(self):
        if not self._initialized:
            if _StorageManagerSingleton._lock is None:
                import threading
                _StorageManagerSingleton._lock = threading.Lock()
                
            with _StorageManagerSingleton._lock:
                if not self._initialized:
                    self._manager = StorageManager()
                    self._initialized = True
            
    def get_manager(self) -> 'StorageManager':
        if not hasattr(self._manager, '_storage') or self._manager._storage is None:
            self._manager._initialize_storage()
        return self._manager

# Global instance with lazy initialization
_storage_manager_singleton = _StorageManagerSingleton()

# Backward compatibility
def get_storage() -> StorageInterface:
    """Get the current storage instance (synchronous)."""
    manager = _storage_manager_singleton.get_manager()
    return manager.storage

# For backward compatibility with direct attribute access
class _StorageManagerProxy:
    @property
    def storage(self):
        manager = _storage_manager_singleton.get_manager()
        return manager.storage
    
    @property
    def storage_type(self):
        manager = _storage_manager_singleton.get_manager()
        return manager.storage_type
    
    def get_async_storage(self):
        manager = _storage_manager_singleton.get_manager()
        return manager.get_async_storage()
    
    def __getattr__(self, name):
        # Forward any other attribute access to the actual manager
        manager = _storage_manager_singleton.get_manager()
        return getattr(manager, name)

# Create a proxy instance for backward compatibility
storage_manager = _StorageManagerProxy()

def get_storage_type() -> StorageType:
    """Get the current storage type."""
    return storage_manager.storage_type

def get_async_storage():
    """Convenience helper to obtain the async storage wrapper."""
    return storage_manager.get_async_storage()
