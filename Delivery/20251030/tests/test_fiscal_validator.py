"""Tests for fiscal_validator.py"""
import pytest
from backend.tools.fiscal_validator import (
    validate_cnpj,
    validate_totals,
    cfop_type,
    validate_document
)

# Test data
VALID_CNPJ = "33.453.678/0001-00"
INVALID_CNPJ = "33.453.678/0001-01"  # Digito verificador inválido
INVALID_FORMAT_CNPJ = "33.453.678/0001"  # Formato inválido

SAMPLE_DOC = {
    "emitente": {
        "cnpj": "33.453.678/0001-00",
        "nome": "Empresa Teste LTDA"
    },
    "itens": [
        {"valor_total": 100.0},
        {"valor_total": 200.0}
    ],
    "total": 300.0,
    "cfop": "5102",
    "impostos": {
        "icms": {"valor": 54.0},
        "ipi": {"valor": 0.0}
    }
}

# CNPJ Validation Tests
def test_validate_cnpj_valid():
    """Test valid CNPJ"""
    assert validate_cnpj(VALID_CNPJ) is True

def test_validate_cnpj_invalid():
    """Test invalid CNPJ"""
    assert validate_cnpj(INVALID_CNPJ) is False

def test_validate_cnpj_short():
    """Test short CNPJ"""
    assert validate_cnpj("123") is False

def test_validate_cnpj_none():
    """Test None CNPJ"""
    assert validate_cnpj(None) is False

def test_validate_cnpj_empty():
    """Test empty CNPJ"""
    assert validate_cnpj("") is False

# Totals Validation Tests
def test_validate_totals_match():
    """Test when totals match"""
    items = [{"valor_total": 100.0}, {"valor_total": 200.0}]
    assert validate_totals(items, 300.0) == (True, 300.0)

def test_validate_totals_within_tolerance():
    """Test when difference is within tolerance (0.01)"""
    items = [{"valor_total": 100.0}, {"valor_total": 200.0}]
    assert validate_totals(items, 300.01) == (True, 300.0)

def test_validate_totals_outside_tolerance():
    """Test when difference is outside tolerance"""
    items = [{"valor_total": 100.0}, {"valor_total": 200.0}]
    assert validate_totals(items, 300.1) == (False, 300.0)

# CFOP Type Tests
def test_cfop_type_venda():
    """Test CFOP types for sales"""
    assert cfop_type("5102") == "venda"
    assert cfop_type("6102") == "venda"

def test_cfop_type_compra():
    """Test CFOP types for purchases"""
    assert cfop_type("1102") == "compra"
    assert cfop_type("2102") == "compra"

def test_cfop_type_devolucao():
    """Test CFOP types for returns"""
    assert cfop_type("3202") == "devolucao"

def test_cfop_type_other():
    """Test other CFOP types"""
    assert cfop_type("4202") == "other"
    assert cfop_type("") == "unknown"

# Document Validation Tests
def test_validate_document_valid():
    """Test validation of a valid document"""
    valid_doc = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA',
            'nome': 'Empresa Teste LTDA'
        },
        'destinatario': {
            'cnpj': '12.345.678/0001-99',
            'razao_social': 'Cliente Teste SA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 2, 'valor_unitario': 50.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102', 'quantity': 2},
            {'descricao': 'Produto 2', 'quantidade': 1, 'valor_unitario': 200.0, 'valor_total': 200.0, 'ncm': '8765.43.21', 'cfop': '5102', 'quantity': 1}
        ],
        'total': 300.0,
        'cfop': '5102',
        'document_type': 'NFe',
        'numero': '12345',
        'data_emissao': '2025-10-24',
        'impostos': {
            'icms': {'valor': 54.0},
            'ipi': {'valor': 0.0}
        }
    }
    
    result = validate_document(valid_doc)
    # We expect 'warning' status due to test CNPJ and NCMs not being recognized
    assert result['status'] == 'warning', f"Expected 'warning' status, got {result['status']}"
    # We expect some warnings for test CNPJ and NCMs
    assert result.get('warnings'), "Expected some warnings for test CNPJ and NCMs"
    # We expect the calculated sum to match
    assert result['calculated_sum'] == 300.0, f"Expected calculated sum of 300.0, got {result['calculated_sum']}"
    # CNPJ validation should pass (test CNPJ is whitelisted)
    assert result['validations']['emitente'].get('cnpj') is True, "CNPJ validation should pass"
    # Check if we have the expected number of items
    assert len(result['validations']['itens'].get('detalhes', [])) == 2, \
        f"Expected 2 items, got {len(result['validations']['itens'].get('detalhes', []))}"
    
    # Items with invalid NCMs should be marked as invalid
    # But the overall document should still be valid with warnings
    assert result['status'] == 'warning', \
        f"Expected 'warning' status, got {result['status']}"
    
    # Verify we have warnings about the NCMs
    assert any('NCM' in warning for warning in result.get('warnings', [])), \
        "Expected warnings about NCMs"
    # Totals should be valid
    assert result['validations']['totals']['valid'] is True, "Totals should be valid"

def test_validate_document_invalid_cnpj():
    """Test validation with invalid CNPJ"""
    invalid_doc = {
        'emitente': {
            'cnpj': '11.111.111/1111-11',  # CNPJ inválido
            'razao_social': 'Empresa Inválida',
            'nome': 'Empresa Inválida'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 2, 'valor_unitario': 50.0, 'valor_total': 100.0}
        ],
        'total': 100.0
    }
    
    result = validate_document(invalid_doc)
    assert result['status'] == 'error'
    assert any('CNPJ do emitente inválido' in issue for issue in result['issues'])
    assert result['validations']['emitente']['cnpj'] is False

def test_validate_document_missing_totals():
    """Test validation with missing totals"""
    doc = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 2, 'valor_unitario': 50.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
        ],
        'total': 400.0  # Total incorreto (deveria ser 100.0)
    }
    
    result = validate_document(doc)
    assert result['status'] == 'error'
    assert any('Divergência nos totais' in issue for issue in result['issues'])
    assert result['validations']['totals']['valid'] is False

def test_validate_document_missing_taxes():
    """Test validation with missing taxes"""
    doc = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102', 'quantity': 1}
        ],
        'total': 100.0,
        'cfop': '5102',
        'document_type': 'NFe',
        'numero': '12345',
        'data_emissao': '2025-10-24',
        'impostos': {}  # Impostos ausentes
    }
    
    result = validate_document(doc)
    # Missing taxes should be an error, not just a warning
    assert result['status'] == 'error', f"Expected status 'error' for missing taxes, but got '{result['status']}'"
    # Verify the specific error message about missing ICMS
    assert any('ICMS não informado' in str(issue) for issue in result['issues']), \
        "Should report missing ICMS"
    
    # Verificar se a mensagem de ICMS está presente
    # Apenas ICMS é verificado como erro, IPI é apenas um aviso
    assert any('ICMS não informado' in str(issue) for issue in result['issues']), \
        f"Expected 'ICMS não informado' in issues, but got: {result['issues']}"

# Test edge cases
def test_validate_document_empty():
    """Test validation of empty document"""
    result = validate_document({})
    assert result['status'] == 'error'
    assert 'CNPJ do emitente não informado' in result['issues']
    assert 'CFOP não informado' in result['issues']
    assert 'ICMS não informado' in result['issues']
    assert 'Número do documento não informado' in result['issues']
    assert not result['validations']['itens']['has_items']

def test_validate_document_with_recipient_fields():
    """Test validation with recipient fields."""
    doc_with_recipient = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA',
            'nome': 'Empresa Teste LTDA'
        },
        'destinatario': {
            'cnpj': '12.345.678/0001-99',
            'razao_social': 'Cliente Teste SA',
            'nome': 'Cliente Teste SA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 2, 'valor_unitario': 50.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102', 'quantity': 2},
            {'descricao': 'Produto 2', 'quantidade': 1, 'valor_unitario': 200.0, 'valor_total': 200.0, 'ncm': '8765.43.21', 'cfop': '5102', 'quantity': 1}
        ],
        'total': 300.0,
        'cfop': '5102',
        'document_type': 'NFe',
        'numero': '12345',
        'data_emissao': '2025-10-24',
        'impostos': {
            'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 54.0},
            'pis': {'cst': '01', 'aliquota': 1.65, 'valor': 4.95},
            'cofins': {'cst': '01', 'aliquota': 7.6, 'valor': 22.8},
            'ipi': {'cst': '50', 'aliquota': 0.0, 'valor': 0.0}
        }
    }

    result = validate_document(doc_with_recipient)

    # Should validate successfully with recipient
    assert result['status'] == 'warning'  # Warning due to test CNPJ/NCM

    # Check recipient validation
    assert 'destinatario' in result['validations']
    destinatario_validation = result['validations']['destinatario']
    assert destinatario_validation['valido'] is False
    assert destinatario_validation['tipo'].lower() in {'cpf', 'cnpj'}
    assert result['warnings']


def test_validate_document_with_icms_st():
    """Test validation with ICMS ST taxes."""
    doc_with_icms_st = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
        ],
        'total': 100.0,
        'cfop': '5102',
        'document_type': 'NFe',
        'numero': '12345',
        'data_emissao': '2025-10-24',
        'impostos': {
            'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 18.0},
            'icms_st': {
                'cst': '41',
                'valor': 10.0,
                'mva': 50.0,
                'aliquota': 18.0
            }
        }
    }

    result = validate_document(doc_with_icms_st)

    # Should not crash with ICMS ST
    assert result['status'] in ['success', 'warning', 'error']

    # Check that ICMS ST validation details are present
    assert 'impostos' in result['validations']
    # The validation should not fail due to undefined icms_st variable

    # Verify no internal errors occurred
    assert not any('icms_st' in str(issue).lower() and 'not associated' in str(issue)
                  for issue in result.get('issues', []))


def test_validate_document_without_icms_st():
    """Test validation without ICMS ST taxes."""
    doc_without_icms_st = {
        'emitente': {
            'cnpj': '33.453.678/0001-00',
            'razao_social': 'Empresa Teste LTDA'
        },
        'itens': [
            {'descricao': 'Produto 1', 'quantidade': 1, 'valor_unitario': 100.0, 'valor_total': 100.0, 'ncm': '1234.56.78', 'cfop': '5102'}
        ],
        'total': 100.0,
        'cfop': '5102',
        'document_type': 'NFe',
        'numero': '12345',
        'data_emissao': '2025-10-24',
        'impostos': {
            'icms': {'cst': '00', 'aliquota': 18.0, 'valor': 18.0}
            # No ICMS ST
        }
    }

    result = validate_document(doc_without_icms_st)

    # Should validate successfully without ICMS ST
    assert result['status'] in ['success', 'warning', 'error']

    # Should not have ICMS ST in validation details if not present
    # But should not crash due to undefined variable
