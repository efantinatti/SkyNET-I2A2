"""Testes para o FiscalValidatorAgent."""
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.fiscal_validator_agent import (
    FiscalValidatorAgent,
    FiscalCodeValidation,
    FiscalDocumentValidation,
)

# Desativa os avisos de depreciação do Pydantic
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Configuração de logging para testes
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dados de teste
TEST_API_KEY = "test-api-key"
TEST_FISCAL_DATA = {
    "cfop": "5102",
    "cst_icms": "00",
    "cst_pis": "01",
    "cst_cofins": "01",
    "ncm": "22030010"
}

# Mock de resposta do LLM
MOCK_LLM_RESPONSE = """
{
    "cfop": {
        "is_valid": true,
        "normalized_code": "5102",
        "description": "Venda de mercadoria adquirida ou recebida de terceiros",
        "confidence": 0.98
    },
    "cst_icms": {
        "is_valid": true,
        "normalized_code": "00",
        "description": "Tributada integralmente",
        "confidence": 0.99
    },
    "cst_pis": {
        "is_valid": true,
        "normalized_code": "01",
        "description": "Operação tributável com alíquota básica",
        "confidence": 0.97
    },
    "cst_cofins": {
        "is_valid": true,
        "normalized_code": "01",
        "description": "Operação tributável com alíquota básica",
        "confidence": 0.97
    },
    "ncm": {
        "is_valid": true,
        "normalized_code": "22030010",
        "description": "Cervejas de malte",
        "confidence": 0.99
    }
}
"""

@pytest.fixture
def fiscal_validator():
    """Fixture para criar uma instância do FiscalValidatorAgent com mock."""
    with patch('google.generativeai.GenerativeModel') as mock_model, \
         patch('google.generativeai.configure') as mock_configure:
        
        # Configura o mock do modelo
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        # Configura a resposta da geração de conteúdo
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        
        # Configura o mock para retornar a resposta de teste
        mock_instance.generate_content.return_value = mock_response
        
        # Cria uma instância do validador com a chave de teste
        validator = FiscalValidatorAgent(api_key=TEST_API_KEY, cache_enabled=False)
        
        # Armazena o mock para uso nos testes
        validator.model = mock_instance
        
        yield validator

def test_validate_document_success(fiscal_validator):
    mock_response = MagicMock()
    mock_response.text = MOCK_LLM_RESPONSE
    fiscal_validator.model.generate_content.return_value = mock_response

    result = asyncio.run(fiscal_validator.validate_document(TEST_FISCAL_DATA))

    for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
        assert field in result
        assert isinstance(result[field], dict)
        assert result[field]['is_valid'] is True
        assert result[field]['normalized_code']
        assert 'description' in result[field]
        assert result[field]['confidence'] > 0


def test_validate_document_partial_data(fiscal_validator):
    partial_data = {
        'cfop': '5102',
        'ncm': '22030010',
        'cst_icms': '00',
        'cst_pis': '01',
        'cst_cofins': '01',
    }
    mock_response = MagicMock()
    mock_response.text = """
    {
        "cfop": {
            "is_valid": true,
            "normalized_code": "5102",
            "description": "Venda de mercadoria adquirida ou recebida de terceiros",
            "confidence": 0.98
        },
        "ncm": {
            "is_valid": true,
            "normalized_code": "22030010",
            "description": "Cervejas de malte",
            "confidence": 0.99
        }
    }
    """
    fiscal_validator.model.generate_content.return_value = mock_response

    result = asyncio.run(fiscal_validator.validate_document(partial_data))

    assert result['cfop']['is_valid'] is True
    assert result['ncm']['is_valid'] is True
    for field in ['cst_icms', 'cst_pis', 'cst_cofins']:
        assert field in result
        assert result[field].get('normalized_code', '') == ''
        assert result[field].get('is_valid', False) is False


def test_validate_document_invalid_json(fiscal_validator):
    mock_response = MagicMock()
    mock_response.text = "{invalid json}"
    fiscal_validator.model.generate_content.return_value = mock_response

    result = asyncio.run(fiscal_validator.validate_document(TEST_FISCAL_DATA))

    for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
        assert field in result
        assert result[field]['is_valid'] is False
        assert result[field]['normalized_code'] == ''
        assert result[field]['confidence'] == 0.0
        assert result[field]['description'].lower().startswith('erro:')


def test_validate_document_llm_error(fiscal_validator):
    fiscal_validator.model.generate_content.side_effect = Exception("Erro no LLM")

    result = asyncio.run(fiscal_validator.validate_document(TEST_FISCAL_DATA))

    for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
        assert field in result
        assert result[field]['is_valid'] is False
        assert result[field]['normalized_code'] == ''
        assert result[field]['confidence'] == 0.0
        assert result[field]['description'].lower().startswith('erro:')

def test_fiscal_code_validation_model():
    """Testa o modelo Pydantic para validação de códigos fiscais."""
    # Cria uma instância válida
    validation = FiscalCodeValidation(
        is_valid=True,
        normalized_code="5102",
        description="Venda de mercadoria adquirida ou recebida de terceiros",
        confidence=0.98
    )
    
    # Verifica se os valores foram atribuídos corretamente
    assert validation.is_valid is True
    assert validation.normalized_code == "5102"
    assert "Venda" in validation.description
    assert 0 <= validation.confidence <= 1
    
    try:
        # Tenta usar model_dump() (Pydantic v2)
        validation_dict = validation.model_dump()
    except AttributeError:
        # Fallback para dict() (Pydantic v1)
        validation_dict = validation.dict()
    
    assert validation_dict["is_valid"] is True
    assert validation_dict["normalized_code"] == "5102"
    assert "Venda" in validation_dict["description"]
    assert 0 <= validation_dict["confidence"] <= 1

def test_fiscal_document_validation_model():
    """Testa o modelo Pydantic para validação de documentos fiscais."""
    # Cria uma instância válida
    validation = FiscalDocumentValidation(
        cfop=FiscalCodeValidation(
            is_valid=True,
            normalized_code="5102",
            description="Venda de mercadoria adquirida ou recebida de terceiros",
            confidence=0.98
        ),
        cst_icms=FiscalCodeValidation(
            is_valid=True,
            normalized_code="00",
            description="Tributada integralmente",
            confidence=0.99
        ),
        ncm=FiscalCodeValidation(
            is_valid=True,
            normalized_code="22030010",
            description="Cervejas de malte",
            confidence=0.99
        )
    )

    assert validation.cfop.is_valid is True
    assert validation.cst_icms.normalized_code == "00"
    assert validation.ncm is not None
    assert validation.cst_pis is None

    exported = validation.model_dump() if hasattr(validation, "model_dump") else validation.dict()

    def _as_obj(value):
        return value if isinstance(value, FiscalCodeValidation) else FiscalCodeValidation(**value)

    assert _as_obj(exported['cfop']).is_valid is True
    assert _as_obj(exported['cst_icms']).normalized_code == "00"
    assert _as_obj(exported['ncm']).is_valid is True
    assert exported.get('cst_pis') in (None, {})
