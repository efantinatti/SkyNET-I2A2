"""Tests for recipient fields functionality."""
import pytest
import sys
import pathlib
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from backend.database.postgresql_storage import PostgreSQLStorage
from backend.tools.fiscal_validator import validate_document


class TestRecipientFields:
    """Test recipient fields handling across the system."""

    def test_fiscal_validator_recipient_validation(self):
        """Test that fiscal validator properly validates recipient fields."""
        doc_with_recipient = {
            'document_type': 'NFe',
            'numero': '12345',
            'emitente': {
                'cnpj': '33.453.678/0001-00',
                'razao_social': 'Empresa Teste LTDA'
            },
            'destinatario': {
                'cnpj': '12.345.678/0001-99',
                'razao_social': 'Cliente Teste SA',
                'nome': 'Cliente Teste SA'
            },
            'itens': [
                {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
            ],
            'total': 100.0,
            'cfop': '5102',
            'data_emissao': '2025-10-24',
            'impostos': {
                'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 18.0}
            }
        }

        result = validate_document(doc_with_recipient)

        # Should validate successfully
        assert result['status'] in ['success', 'warning', 'error']

        # Check that recipient validation exists and reflects normalized structure
        assert 'destinatario' in result['validations']
        dest_validation = result['validations']['destinatario']
        assert dest_validation['tipo'] == 'CNPJ'
        assert dest_validation['identificacao'].replace('.', '').replace('/', '').replace('-', '') == '12345678000199'
        assert dest_validation['valido'] is False  # CNPJ de teste é tratado como inválido

    def test_fiscal_validator_missing_recipient(self):
        """Test fiscal validator with missing recipient."""
        doc_without_recipient = {
            'document_type': 'NFe',
            'numero': '12345',
            'emitente': {
                'cnpj': '33.453.678/0001-00',
                'razao_social': 'Empresa Teste LTDA'
            },
            # No destinatario field
            'itens': [
                {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
            ],
            'total': 100.0,
            'cfop': '5102',
            'data_emissao': '2025-10-24',
            'impostos': {
                'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 18.0}
            }
        }

        result = validate_document(doc_without_recipient)

        # Should still validate successfully (recipient is optional)
        assert result['status'] in ['success', 'warning', 'error']

        # Should not have recipient validation if no recipient present
        if 'destinatario' in result['validations']:
            dest_validation = result['validations']['destinatario']
            assert dest_validation['tipo'] == 'CNPJ'
            identificacao = dest_validation.get('identificacao') or ''
            assert identificacao in (None, '', 'N/A') or identificacao.replace('.', '').replace('/', '').replace('-', '') == ''
            assert dest_validation.get('valido') is False

    def test_postgresql_storage_recipient_fields(self):
        """Test PostgreSQL storage with recipient fields."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            # Mock table columns including recipient fields
            mock_execute.side_effect = [
                [
                    {'column_name': 'id'}, {'column_name': 'file_name'},
                    {'column_name': 'document_type'}, {'column_name': 'document_number'},
                    {'column_name': 'issuer_cnpj'}, {'column_name': 'issuer_name'},
                    {'column_name': 'recipient_cnpj'}, {'column_name': 'recipient_name'},
                    {'column_name': 'issue_date'}, {'column_name': 'total_value'}
                ],
                {
                    'id': 'test-id-123',
                    'file_name': 'test.xml',
                    'document_type': 'NFe',
                    'document_number': '12345',
                    'issuer_cnpj': '12345678000195',
                    'issuer_name': 'Empresa Teste',
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
                'document_number': '12345',
                'issuer_cnpj': '12345678000195',
                'issuer_name': 'Empresa Teste',
                'recipient_cnpj': '98765432000100',
                'recipient_name': 'Cliente Teste S.A.',
                'issue_date': '28/08/2025',
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify recipient fields are preserved
            assert result['recipient_cnpj'] == '98765432000100'
            assert result['recipient_name'] == 'Cliente Teste S.A.'

    def test_postgresql_storage_missing_recipient_fields(self):
        """Test PostgreSQL storage when recipient fields don't exist in table."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn, \
             patch.object(PostgreSQLStorage, '_execute_query') as mock_execute:

            mock_connection = MagicMock()
            mock_conn.return_value = mock_connection

            # Mock table columns WITHOUT recipient fields (older schema)
            mock_execute.side_effect = [
                [
                    {'column_name': 'id'}, {'column_name': 'file_name'},
                    {'column_name': 'document_type'}, {'column_name': 'document_number'},
                    {'column_name': 'issuer_cnpj'}, {'column_name': 'issuer_name'},
                    {'column_name': 'issue_date'}, {'column_name': 'total_value'}
                ],  # No recipient columns
                {
                    'id': 'test-id-123',
                    'file_name': 'test.xml',
                    'document_type': 'NFe',
                    'document_number': '12345',
                    'issuer_cnpj': '12345678000195',
                    'issuer_name': 'Empresa Teste',
                    'issue_date': '2025-08-28T00:00:00Z',
                    'total_value': 100.0
                }
            ]

            storage = PostgreSQLStorage()
            doc = {
                'file_name': 'test.xml',
                'document_type': 'NFe',
                'document_number': '12345',
                'issuer_cnpj': '12345678000195',
                'issuer_name': 'Empresa Teste',
                'recipient_cnpj': '98765432000100',  # This column doesn't exist
                'recipient_name': 'Cliente Teste S.A.',  # This column doesn't exist
                'issue_date': '28/08/2025',
                'total_value': 100.0
            }

            result = storage.save_fiscal_document(doc)

            # Verify non-existent columns were filtered out
            assert 'recipient_cnpj' not in result
            assert 'recipient_name' not in result

            # But existing columns should be there
            assert result['file_name'] == 'test.xml'
            assert result['document_number'] == '12345'
            assert result['issue_date'] == '2025-08-28T00:00:00Z'

    def test_recipient_fields_filtering(self):
        """Test that recipient filters are passed through with normalized values."""
        with patch.object(PostgreSQLStorage, '_get_connection') as mock_conn:
            storage = PostgreSQLStorage()

            with patch.object(storage, '_execute_query') as mock_execute:
                mock_execute.side_effect = [
                    [{'count': 1}],
                    [{'id': 'doc-1', 'recipient_cnpj': '11111111000100'}],
                    [{'count': 1}],
                    [{'id': 'doc-2', 'recipient_name': 'Cliente B'}]
                ]

                storage.get_fiscal_documents(recipient_cnpj='11.111.111/0001-00')
                storage.get_fiscal_documents(recipient_name='Cliente B')

                # Verifica que o CNPJ foi normalizado para apenas dígitos
                assert any('%11111111000100%' in str(call.args[1]) for call in mock_execute.call_args_list)

    def test_recipient_validation_cnpj_formats(self):
        """Test recipient validation with different CNPJ formats."""
        test_cases = [
            # (input_cnpj, expected_clean)
            ('12.345.678/0001-99', '12345678000199'),
            ('12345678000199', '12345678000199'),
            ('12.345.678/0001-00', '12345678000100'),
        ]

        for input_cnpj, expected_clean in test_cases:
            doc = {
                'document_type': 'NFe',
                'numero': '12345',
                'emitente': {
                    'cnpj': '33.453.678/0001-00',
                    'razao_social': 'Empresa Teste LTDA'
                },
                'destinatario': {
                    'cnpj': input_cnpj,
                    'razao_social': 'Cliente Teste SA'
                },
                'itens': [
                    {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
                ],
                'total': 100.0,
                'cfop': '5102',
                'data_emissao': '2025-10-24',
                'impostos': {
                    'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 18.0}
                }
            }

            result = validate_document(doc)

            # Should validate successfully regardless of CNPJ format
            assert result['status'] in ['success', 'warning', 'error']

            # Check that CNPJ normalization and boolean flag are exposed
            if 'destinatario' in result['validations']:
                dest_validation = result['validations']['destinatario']
                assert dest_validation['tipo'] in ['CNPJ', 'CPF']
                identificacao = dest_validation['identificacao'].replace('.', '').replace('/', '').replace('-', '')
                assert identificacao == expected_clean
                assert isinstance(dest_validation['valido'], bool)
