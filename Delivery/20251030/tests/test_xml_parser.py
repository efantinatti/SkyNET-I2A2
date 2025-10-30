"""Testes para o módulo de parser de XML."""
import sys
import os
import pathlib
from unittest.mock import patch, mock_open
import pytest

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from backend.tools import xml_parser

# Caminho para o diretório de fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'xml')

def load_xml_fixture(filename):
    """Carrega um arquivo XML de fixture."""
    with open(os.path.join(FIXTURES_DIR, filename), 'r', encoding='utf-8') as f:
        return f.read()

def test_parse_nfe_completa():
    """Testa o parser com uma NFe completa."""
    xml_content = load_xml_fixture('nfe_exemplo.xml')
    result = xml_parser.parse_xml_string(xml_content)
    
    # Verifica dados básicos
    assert result['numero'] == '6'
    assert result['serie'] == '1'
    assert result['data_emissao'] == '2020-10-01T10:10:10-03:00'
    
    # Verifica emitente
    assert result['emitente']['cnpj'] == '06117473000150'
    assert result['emitente']['razao_social'] == 'LOJA DE TESTE LTDA'
    
    # Verifica destinatário
    assert result['destinatario']['cnpj'] == '07504505000132'
    assert result['destinatario']['razao_social'] == 'DESTINATARIO LTDA'
    
    # Verifica itens
    assert len(result['itens']) == 1
    item = result['itens'][0]
    assert item['codigo'] == '123456'
    assert item['descricao'] == 'PRODUTO DE TESTE'
    assert item['quantidade'] == 1.0
    assert item['valor_unitario'] == 100.0
    assert item['valor_total'] == 100.0
    assert item['cfop'] == '5102'
    assert item['ncm'] == '84713020'
    
    # Totais disponíveis no dicionário principal
    assert result['total'] == 100.0
    assert result['total_detalhado']['valor_total'] == 100.0

def test_parse_xml_invalido():
    """Testa o parser com um XML inválido."""
    # XML inválido (faltando fechamento de tag)
    invalid_xml = "<?xml version='1.0'?><root><test>"
    result = xml_parser.parse_xml_string(invalid_xml)
    
    assert 'error' in result
    assert result['error'] == 'xml_parse_error'
    # Verifica se a mensagem de erro começa com 'XML syntax error:'
    assert result['message'].startswith('XML syntax error:')

def test_parse_xml_arquivo_inexistente():
    """Testa o parser com um arquivo que não existe."""
    # Garante que o arquivo realmente não existe
    import os
    file_path = 'arquivo_que_nao_existe.xml'
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Verifica se a exceção é lançada
    with pytest.raises(FileNotFoundError) as excinfo:
        xml_parser.parse_xml_file(file_path)
    
    # Verifica a mensagem de erro
    assert 'Arquivo não encontrado' in str(excinfo.value)

@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data='<?xml version="1.0"?><root><test>123</test></root>')
def test_parse_xml_arquivo_valido(mock_file, mock_exists):
    """Testa o parser com um arquivo XML válido."""
    result = xml_parser.parse_xml_string("<?xml version='1.0'?><root><test>123</test></root>")
    assert result['error'] == 'unknown_document_type'
    assert result['message'] == 'Tipo de documento não identificado'
    assert result['raw_text'] == "<?xml version='1.0'?><root><test>123</test></root>"

def test_parse_xml_sem_namespace():
    """Testa o parser com XML sem namespace."""
    xml_simples = """
    <?xml version="1.0"?>
    <root>
        <teste>valor</teste>
        <numero>123</numero>
    </root>
    """
    result = xml_parser.parse_xml_string(xml_simples)
    assert result['error'] == 'unknown_document_type'
    assert result['message'] == 'Tipo de documento não identificado'
    assert result['raw_text'].strip().startswith('<?xml version="1.0"?>')
