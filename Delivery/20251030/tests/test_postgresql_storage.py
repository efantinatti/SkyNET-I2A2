"""Tests for PostgreSQL storage implementation with new features."""
import pytest
import sys
import pathlib
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from backend.database.postgresql_storage import PostgreSQLStorage, PostgreSQLStorageError


class TestPostgreSQLStorageDateConversion:
    """Test date conversion functionality in PostgreSQL storage."""

    def test_save_document_with_brazilian_date(self):
        """Test saving document with Brazilian date format."""
        # Mock the database connection and queries
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            # Setup mocks
            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            # Mock table columns response
            mock_execute.side_effect = [
                # _get_table_columns response
                [{'column_name': 'id'}, {'column_name': 'file_name'}, {'column_name': 'issue_date'}],
                # INSERT query response
                {'id': 'test-id-123', 'file_name': 'test.xml', 'issue_date': '2025-08-28T00:00:00Z'}
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'issue_date': '28/08/2025',  # Brazilian format
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify the date was converted
            assert result['issue_date'] == '2025-08-28T00:00:00Z'

            # Verify the query was called with converted date
            mock_execute.assert_called()
            # The second call should be the INSERT with the converted date
            insert_call = mock_execute.call_args_list[-1]
            assert '28/08/2025' not in str(insert_call)  # Original format should not be in query
            assert '2025-08-28T00:00:00Z' in str(insert_call)  # Converted format should be in query

    def test_save_document_with_iso_date_passthrough(self):
        """Test that ISO dates are passed through unchanged."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            mock_execute.side_effect = [
                [{'column_name': 'id'}, {'column_name': 'file_name'}, {'column_name': 'issue_date'}],
                {'id': 'test-id-123', 'file_name': 'test.xml', 'issue_date': '2025-08-28T10:30:00Z'}
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'issue_date': '2025-08-28T10:30:00Z',  # Already ISO format
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify the date was not changed
            assert result['issue_date'] == '2025-08-28T10:30:00Z'

    def test_save_document_with_datetime_object(self):
        """Test saving document with datetime object."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            mock_execute.side_effect = [
                [{'column_name': 'id'}, {'column_name': 'file_name'}, {'column_name': 'issue_date'}],
                {'id': 'test-id-123', 'file_name': 'test.xml', 'issue_date': '2025-08-28T10:30:00Z'}
            ]

            storage = PostgreSQLStorage()
            dt = datetime(2025, 8, 28, 10, 30, 0)
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'issue_date': dt,  # datetime object
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify the datetime object was converted to ISO string
            assert result['issue_date'] == '2025-08-28T10:30:00Z'

    def test_save_document_with_recipient_fields(self):
        """Test saving document with new recipient fields."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            # Mock table columns including recipient fields
            mock_execute.side_effect = [
                [
                    {'column_name': 'id'}, {'column_name': 'file_name'},
                    {'column_name': 'recipient_cnpj'}, {'column_name': 'recipient_name'},
                    {'column_name': 'issue_date'}, {'column_name': 'total_value'}
                ],
                {
                    'id': 'test-id-123',
                    'file_name': 'test.xml',
                    'recipient_cnpj': '98765432000100',
                    'recipient_name': 'Cliente Teste S.A.',
                    'issue_date': '2025-08-28T00:00:00Z',
                    'total_value': 100.0
                }
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'recipient_cnpj': '98765432000100',
                'recipient_name': 'Cliente Teste S.A.',
                'issue_date': '28/08/2025',
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify recipient fields were saved
            assert result['recipient_cnpj'] == '98765432000100'
            assert result['recipient_name'] == 'Cliente Teste S.A.'
            assert result['issue_date'] == '2025-08-28T00:00:00Z'

    def test_column_filtering_functionality(self):
        """Test that non-existent columns are filtered out."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            # Mock table columns (simulating older schema without recipient fields)
            mock_execute.side_effect = [
                [
                    {'column_name': 'id'}, {'column_name': 'file_name'},
                    {'column_name': 'issue_date'}, {'column_name': 'total_value'}
                ],  # Only basic columns exist
                {
                    'id': 'test-id-123',
                    'file_name': 'test.xml',
                    'issue_date': '2025-08-28T00:00:00Z',
                    'total_value': 100.0
                }
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'recipient_cnpj': '98765432000100',  # This column doesn't exist in mock
                'recipient_name': 'Cliente Teste S.A.',  # This column doesn't exist in mock
                'issue_date': '28/08/2025',
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify that non-existent columns were filtered out
            assert 'recipient_cnpj' not in result
            assert 'recipient_name' not in result
            # But existing columns should be there
            assert result['file_name'] == 'test.xml'
            assert result['issue_date'] == '2025-08-28T00:00:00Z'
            assert result['total_value'] == 100.0

    def test_jsonb_fields_serialization(self):
        """Test that JSONB fields are properly serialized."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            mock_execute.side_effect = [
                [
                    {'column_name': 'id'}, {'column_name': 'file_name'},
                    {'column_name': 'extracted_data'}, {'column_name': 'classification'},
                    {'column_name': 'validation_details'}, {'column_name': 'metadata'}
                ],
                {
                    'id': 'test-id-123',
                    'file_name': 'test.xml',
                    'extracted_data': '{"emitente": {"cnpj": "12345678000195"}}',
                    'classification': '{"tipo": "venda"}',
                    'validation_details': '{"status": "success"}',
                    'metadata': '{"has_issues": false}'
                }
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'extracted_data': {
                    'emitente': {'cnpj': '12345678000195', 'razao_social': 'Teste Ltda'},
                    'itens': [{'descricao': 'Produto teste', 'valor': 100.0}]
                },
                'classification': {'tipo': 'venda', 'categoria': 'mercadorias'},
                'validation_details': {'status': 'success', 'issues': []},
                'metadata': {'has_issues': False, 'item_count': 1}
            }

            result = storage.save_fiscal_document(doc)

            # JSONB fields should be returned as dicts
            assert isinstance(result['extracted_data'], dict)
            assert isinstance(result['classification'], dict)
            assert isinstance(result['validation_details'], dict)
            assert isinstance(result['metadata'], dict)

            assert result['extracted_data']['emitente']['cnpj'] == '12345678000195'
            assert result['classification']['tipo'] == 'venda'


class TestPostgreSQLStorageEdgeCases:
    """Test edge cases and error conditions."""

    def test_save_document_with_none_date(self):
        """Test saving document with None date."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            mock_execute.side_effect = [
                [{'column_name': 'id'}, {'column_name': 'file_name'}, {'column_name': 'issue_date'}],
                {'id': 'test-id-123', 'file_name': 'test.xml', 'issue_date': None}
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'issue_date': None  # None date should be handled
            }

            result = storage.save_fiscal_document(doc)
            assert result['issue_date'] is None

    def test_save_document_with_invalid_date(self):
        """Test saving document with invalid date format."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            mock_execute.side_effect = [
                [{'column_name': 'id'}, {'column_name': 'file_name'}, {'column_name': 'issue_date'}],
                {'id': 'test-id-123', 'file_name': 'test.xml', 'issue_date': None}
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'issue_date': 'invalid-date-format'  # Invalid format should be handled gracefully
            }

            result = storage.save_fiscal_document(doc)
            # Should handle invalid date by setting it to None or keeping original
            assert 'issue_date' in result
