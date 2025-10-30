"""Tests for the importador (formerly upload document) functionality."""
import pytest
import sys
import pathlib
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from zoneinfo import ZoneInfo

# Add parent directory to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from frontend.pages.importador import _prepare_document_record, _validate_document_data


class TestDocumentPreparation:
    """Test document preparation for importador."""

    def test_prepare_document_record_with_brazilian_date(self):
        """Test document preparation with Brazilian date format."""
        # Mock uploaded file
        mock_uploaded = MagicMock()
        mock_uploaded.name = 'test_document.xml'

        # Mock parsed data with Brazilian date
        parsed = {
            'document_type': 'NFe',
            'numero': '12345',
            'data_emissao': '28/08/2025',  # Brazilian format
            'emitente': {
                'cnpj': '12345678000195',
                'razao_social': 'Empresa Teste Ltda'
            },
            'destinatario': {
                'cnpj': '98765432000100',
                'razao_social': 'Cliente Teste S.A.'
            },
            'itens': [
                {'descricao': 'Produto Teste', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0}
            ],
            'total': 100.0,
            'impostos': {'icms': 18.0, 'pis': 1.65, 'cofins': 7.6}
        }

        # Mock classification
        classification = {
            'tipo': 'venda',
            'categoria': 'mercadorias',
            'confianca': 0.95,
            'validacao': {
                'status': 'success',
                'issues': [],
                'warnings': [],
                'validations': {
                    'emitente': {'cnpj': True, 'razao_social': True},
                    'destinatario': {'cnpj': True, 'razao_social': True},
                    'itens': {'has_items': True, 'all_valid': True},
                    'totais': {'valid': True}
                }
            }
        }

        # Prepare document record
        record = _prepare_document_record(mock_uploaded, parsed, classification)

        # Verify structure
        assert record['file_name'] == 'test_document.xml'
        assert record['document_type'] == 'NFe'
        assert record['document_number'] == '12345'
        assert record['issuer_cnpj'] == '12345678000195'
        assert record['issuer_name'] == 'Empresa Teste Ltda'
        assert record['recipient_cnpj'] == '98765432000100'
        assert record['recipient_name'] == 'Cliente Teste S.A.'

        # Verify date conversion
        assert record['issue_date'] == '2025-08-28T00:00:00Z'  # Brazilian date converted to ISO

        # Verify timestamps
        assert 'uploaded_at' in record
        assert 'processed_at' in record
        assert 'T' in record['uploaded_at']  # ISO format
        assert 'T' in record['processed_at']  # ISO format

        # Verify extracted data is preserved
        assert 'extracted_data' in record
        assert record['extracted_data']['numero'] == '12345'

        # Verify validation details
        assert record['validation_status'] == 'success'
        assert 'validation_details' in record
        assert 'classification' in record

        # Verify metadata
        assert 'metadata' in record
        assert record['metadata']['has_issues'] is False
        assert record['metadata']['item_count'] == 1

    def test_prepare_document_record_with_iso_date(self):
        """Test document preparation with already ISO formatted date."""
        mock_uploaded = MagicMock()
        mock_uploaded.name = 'test_document.xml'

        parsed = {
            'document_type': 'NFe',
            'numero': '12345',
            'data_emissao': '2025-08-28T10:30:00Z',  # Already ISO format
            'emitente': {'cnpj': '12345678000195', 'razao_social': 'Empresa Teste Ltda'},
            'destinatario': {'cnpj': '98765432000100', 'razao_social': 'Cliente Teste S.A.'},
            'itens': [],
            'total': 0.0
        }

        record = _prepare_document_record(mock_uploaded, parsed)

        # Date should be preserved as-is
        assert record['issue_date'] == '2025-08-28T10:30:00Z'

    def test_prepare_document_record_missing_fields(self):
        """Test document preparation with missing optional fields."""
        mock_uploaded = MagicMock()
        mock_uploaded.name = 'test_document.xml'

        parsed = {
            'document_type': 'NFe',
            'numero': '12345',
            # Missing many optional fields
        }

        record = _prepare_document_record(mock_uploaded, parsed)

        # Should have default values for missing fields
        assert record['file_name'] == 'test_document.xml'
        assert record['document_type'] == 'NFe'
        assert record['document_number'] == '12345'
        assert record['issuer_cnpj'] == '00000000000000'  # Default CNPJ
        assert record['issuer_name'] == 'Emitente não identificado'
        assert record['total_value'] == 0.0
        assert record['issue_date'] is None  # No date provided

    def test_validate_document_data_valid(self):
        """Test validation of valid document data."""
        valid_doc = {
            'emitente': {'cnpj': '12345678000195', 'razao_social': 'Teste'},
            'destinatario': {'cnpj': '98765432000100', 'razao_social': 'Cliente'},
            'itens': [
                {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0}
            ],
            'total': 100.0,
            'impostos': {'icms': 18.0}
        }

        assert _validate_document_data(valid_doc) is True

    def test_validate_document_data_missing_emitente(self):
        """Test validation with missing emitente."""
        invalid_doc = {
            # Missing emitente
            'destinatario': {'cnpj': '98765432000100'},
            'itens': [],
            'total': 0.0
        }

        assert _validate_document_data(invalid_doc) is False

    def test_validate_document_data_missing_itens_list(self):
        """Test validation with items not being a list."""
        invalid_doc = {
            'emitente': {'cnpj': '12345678000195'},
            'itens': 'not a list',  # Should be a list
            'total': 0.0
        }

        assert _validate_document_data(invalid_doc) is False

    def test_prepare_document_record_date_edge_cases(self):
        """Test document preparation with various date formats."""
        mock_uploaded = MagicMock()
        mock_uploaded.name = 'test_document.xml'

        test_cases = [
            # (input_date, expected_output)
            ('28/08/2025', '2025-08-28T00:00:00Z'),
            ('15/03/2024', '2024-03-15T00:00:00Z'),
            ('01/01/2023', '2023-01-01T00:00:00Z'),
            ('31/12/2024', '2024-12-31T00:00:00Z'),
            ('28/08/25', '2025-08-28T00:00:00Z'),  # YY format
            ('', None),  # Empty string
            ('invalid-date', None),  # Invalid format
        ]

        for input_date, expected in test_cases:
            parsed = {
                'document_type': 'NFe',
                'numero': '12345',
                'data_emissao': input_date,
                'emitente': {'cnpj': '12345678000195'},
                'itens': [],
                'total': 0.0
            }

            record = _prepare_document_record(mock_uploaded, parsed)
            assert record['issue_date'] == expected, f"Failed for input: {input_date}"


class TestDocumentUploadIntegration:
    """Test the complete importador integration."""

    @patch('frontend.pages.importador.coordinator')
    @patch('frontend.pages.importador.storage')
    def test_full_upload_workflow(self, mock_storage, mock_coordinator):
        """Test the complete importador workflow."""
        # Setup mocks
        mock_coordinator.run_task.side_effect = [
            # Extract result
            {
                'document_type': 'NFe',
                'numero': '16.687',
                'data_emissao': '28/08/2025',
                'emitente': {
                    'cnpj': '05584042000564',
                    'razao_social': 'EDITORA FUNDAMENTO EDUCACIONAL LTDA'
                },
                'destinatario': {
                    'cnpj_cpf': '05798781712',
                    'razao_social': 'Fabio Dias Rhein'
                },
                'itens': [
                    {
                        'descricao': 'GATINHA HARMONIA: NAO SE PREOCUPE, AMIGO!',
                        'quantidade': 1,
                        'valor_unitario': 38.57,
                        'valor_total': 38.57
                    }
                ],
                'impostos': {'icms': 0.00, 'pis': 0.00, 'cofins': None, 'ipi': 0.00},
                'total': 38.57
            },
            # Classify result
            {
                'tipo': 'venda',
                'categoria': 'livros',
                'validacao': {
                    'status': 'success',
                    'issues': [],
                    'warnings': ['CFOP não informado'],
                    'validations': {
                        'emitente': {'cnpj': True, 'razao_social': True},
                        'destinatario': {'cnpj': False, 'razao_social': True},
                        'itens': {'has_items': True, 'all_valid': False},
                        'totais': {'valid': True}
                    }
                }
            }
        ]

        # Mock saved document
        mock_storage.save_fiscal_document.return_value = {
            'id': 'test-doc-id-123',
            'file_name': '41250805584042000564550010000166871854281592 nfe_page-0001.jpg',
            'document_number': '16.687',
            'issue_date': '2025-08-28T00:00:00Z',
            'recipient_name': 'Fabio Dias Rhein'
        }

        # Test the workflow would work (this is more of an integration test)
        # In a real scenario, this would be tested through the Streamlit interface
        # Here we verify that the functions can handle the real data

        mock_uploaded = MagicMock()
        mock_uploaded.name = '41250805584042000564550010000166871854281592 nfe_page-0001.jpg'

        parsed = {
            'document_type': 'NFe',
            'numero': '16.687',
            'data_emissao': '28/08/2025',
            'emitente': {
                'cnpj': '05584042000564',
                'razao_social': 'EDITORA FUNDAMENTO EDUCACIONAL LTDA'
            },
            'destinatario': {
                'cnpj_cpf': '05798781712',
                'razao_social': 'Fabio Dias Rhein'
            },
            'itens': [
                {
                    'descricao': 'GATINHA HARMONIA: NAO SE PREOCUPE, AMIGO!',
                    'quantidade': 1,
                    'valor_unitario': 38.57,
                    'valor_total': 38.57
                }
            ],
            'impostos': {'icms': 0.00, 'pis': 0.00, 'cofins': None, 'ipi': 0.00},
            'total': 38.57
        }

        # Test document preparation with real data
        record = _prepare_document_record(mock_uploaded, parsed)

        # Verify the real data is handled correctly
        assert record['file_name'] == '41250805584042000564550010000166871854281592 nfe_page-0001.jpg'
        assert record['document_number'] == '16.687'
        assert record['issue_date'] == '2025-08-28T00:00:00Z'  # Date converted
        assert record['recipient_cnpj'] == '05798781712'
        assert record['recipient_name'] == 'Fabio Dias Rhein'
        assert record['total_value'] == 38.57

        # Test that document validation passes
        assert _validate_document_data(parsed) is True
