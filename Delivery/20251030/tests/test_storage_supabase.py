"""Tests for SupabaseStorage implementation."""
import sys
import pathlib
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from backend.database.postgresql_storage import PostgreSQLStorage
from backend.database.base_storage import StorageError
from storage_compliance import StorageComplianceTests

# Skip all tests in this module if integration tests are not enabled
pytestmark = pytest.mark.integration

# Skip if Supabase environment variables are not set
pytestmark = pytest.mark.skipif(
    not (os.getenv('TEST_SUPABASE_URL') and os.getenv('TEST_SUPABASE_KEY')),
    reason="TEST_SUPABASE_URL and TEST_SUPABASE_KEY environment variables required"
)


@pytest.fixture(scope="module")
def supabase_storage():
    """Create a Supabase storage instance for testing.
    
    This fixture is module-scoped to reuse the same storage instance across tests.
    """
    storage = PostgreSQLStorage()
    
    # Clean up any test data before and after tests
    try:
        # Delete all test documents
        test_docs = storage.supabase.table('fiscal_documents') \
            .select('*') \
            .like('file', '%test_%') \
            .execute()
            
        for doc in test_docs.data:
            storage.supabase.table('fiscal_documents') \
                .delete() \
                .eq('id', doc['id']) \
                .execute()
    except Exception as e:
        print(f"Warning: Failed to clean up test data: {e}")
    
    yield storage
    
    # Cleanup after tests (in case any tests didn't clean up after themselves)
    try:
        test_docs = storage.supabase.table('fiscal_documents') \
            .select('*') \
            .like('file', '%test_%') \
            .execute()
            
        for doc in test_docs.data:
            storage.supabase.table('fiscal_documents') \
                .delete() \
                .eq('id', doc['id']) \
                .execute()
    except Exception as e:
        print(f"Warning: Failed to clean up test data: {e}")


class TestSupabaseStorage(StorageComplianceTests):
    """Run compliance tests for SupabaseStorage."""

    @pytest.fixture
    def storage(self, supabase_storage):
        """Use the module-scoped Supabase storage instance for testing."""
        return supabase_storage
    
    @pytest.fixture
    def test_document(self):
        """Create a test document with unique values."""
        test_id = str(uuid.uuid4())[:8]
        return {
            'file_name': f'test_doc_{test_id}.xml',
            'document_type': 'NFe',
            'document_number': f'12345{test_id}',
            'issuer_cnpj': '12345678000195',
            'recipient_cnpj': '98765432000198',
            'issue_date': '2025-10-24',
            'total_value': 100.50,
            'metadata': {
                'test': True,
                'test_id': test_id
            }
        }

    @pytest.mark.integration
    def test_supabase_specific_errors(self, storage):
        """Test Supabase-specific error handling."""
        # Test saving invalid history event (missing required fields)
        with pytest.raises(StorageError):
            storage.save_history({})  # Missing fiscal_document_id
        
        # Test invalid document ID
        history = storage.get_document_history('invalid-id')
        assert len(history) == 0  # Should return empty list
        
        # Test get_fiscal_documents with invalid filters
        with pytest.raises(ValueError):
            storage.get_fiscal_documents(filters={'invalid_field': 'value'})
    
    @pytest.mark.integration
    def test_rest_api_integration(self, storage, test_document):
        """Test that REST API calls work properly."""
        # Test saving a document
        saved = storage.save_fiscal_document(test_document)
        assert 'id' in saved
        assert saved.get('document_number') == test_document['document_number']
        
        # Test retrieving the document by ID
        retrieved = storage.get_fiscal_documents(
            filters={'document_number': test_document['document_number']}
        )
        assert retrieved.total == 1
        assert retrieved.items[0]['document_number'] == test_document['document_number']
        
        # Test updating the document
        update_data = {'total_value': 150.75}
        updated = storage.update_fiscal_document(saved['id'], update_data)
        assert updated['total_value'] == 150.75
        
        # Test pagination
        paginated = storage.get_fiscal_documents(
            page=1, 
            page_size=1,
            filters={'document_type': 'NFe'}
        )
        assert hasattr(paginated, 'total')
        assert hasattr(paginated, 'items')
        assert isinstance(paginated.items, list)
        
        # Test document history
        history_event = {
            'fiscal_document_id': saved['id'],
            'action': 'test',
            'details': 'Test history entry',
            'user_id': 'test_user'
        }
        saved_event = storage.save_history(history_event)
        assert 'id' in saved_event
        
        history = storage.get_document_history(saved['id'])
        assert len(history) >= 1
        assert any(e['action'] == 'test' for e in history)
        
        # Test error handling for non-existent document
        with pytest.raises(StorageError):
            storage.get_fiscal_documents(filters={'document_number': 'non-existent-123'})
    
    @pytest.mark.integration
    def test_pagination_behavior(self, storage, test_document):
        """Test pagination behavior with Supabase storage."""
        # Create multiple test documents
        test_docs = []
        for i in range(5):
            doc = test_document.copy()
            doc['document_number'] = f"{test_document['document_number']}_page_{i}"
            doc['total_value'] = 100 + i
            saved = storage.save_fiscal_document(doc)
            test_docs.append(saved)
        
        # Test page size
        page1 = storage.get_fiscal_documents(
            page=1,
            page_size=2,
            filters={'issuer_cnpj': test_document['issuer_cnpj']}
        )
        
        assert page1.page == 1
        assert page1.page_size == 2
        assert len(page1.items) == 2
        assert page1.total >= 5  # At least our 5 test documents
        
        # Test next page
        page2 = storage.get_fiscal_documents(
            page=2,
            page_size=2,
            filters={'issuer_cnpj': test_document['issuer_cnpj']}
        )
        
        assert page2.page == 2
        assert len(page2.items) == 2
        
        # Verify documents are different between pages
        page1_ids = {doc['id'] for doc in page1.items}
        page2_ids = {doc['id'] for doc in page2.items}
        assert page1_ids.isdisjoint(page2_ids)  # No overlap between pages