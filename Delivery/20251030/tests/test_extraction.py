import sys
import pathlib
import pytest
from unittest.mock import patch, mock_open
import os

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from backend.tools import xml_parser
from backend.agents.extraction import extract_from_file

# Test data
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35210112345678901234550020000012341000012345" versao="4.00">
      <ide><nNF>12345</nNF><dhEmi>2023-10-24T10:30:00-03:00</dhEmi></ide>
      <emit><CNPJ>12345678000195</CNPJ><xNome>Empresa Teste</xNome><IE>123456789012</IE></emit>
      <dest><CPF>12345678901</CPF><xNome>Cliente Teste</xNome></dest>
      <det nItem="1">
        <prod><xProd>Produto Teste</xProd><qCom>2.0000</qCom><vUnCom>100.0000</vUnCom><vProd>200.00</vProd><CFOP>5102</CFOP><NCM>84713000</NCM></prod>
        <imposto>
          <ICMS><ICMS00><vICMS>36.00</vICMS></ICMS00></ICMS>
          <PIS><PISAliq><vPIS>3.30</vPIS></PISAliq></PIS>
          <COFINS><COFINSAliq><vCOFINS>15.20</vCOFINS></COFINSAliq></COFINS>
        </imposto>
      </det>
      <total><ICMSTot><vNF>200.00</vNF><vICMS>36.00</vICMS><vPIS>3.30</vPIS><vCOFINS>15.20</vCOFINS></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>"""

def test_parse_minimal_xml():
    """Test parsing of a minimal valid XML."""
    xml = """<?xml version="1.0"?>
    <NFe>
      <infNFe>
        <ide><nNF>123</nNF></ide>
        <emit><xNome>Empresa X</xNome><CNPJ>12345678000195</CNPJ><IE>12345</IE></emit>
        <dest><xNome>Cliente Y</xNome><CPF>12345678901</CPF></dest>
        <det><prod><xProd>Item A</xProd><qCom>2</qCom><vUnCom>10.00</vUnCom><vProd>20.00</vProd><CFOP>5102</CFOP></prod></det>
        <total><ICMSTot><vProd>20.00</vProd><vNF>20.00</vNF></ICMSTot></total>
      </infNFe>
    </NFe>"""
    parsed = xml_parser.parse_xml_string(xml)
    assert parsed['emitente']['razao_social'] == 'Empresa X'
    assert parsed['destinatario']['cnpj'] == '12345678901'
    assert parsed['total'] == 20.0

def test_parse_full_xml():
    """Test parsing of a complete NFe XML."""
    parsed = xml_parser.parse_xml_string(SAMPLE_XML)
    
    # Basic structure
    assert isinstance(parsed, dict)
    assert 'emitente' in parsed
    assert 'destinatario' in parsed
    assert 'itens' in parsed
    assert 'total_detalhado' in parsed
    
    # Emitente data
    assert parsed['emitente']['razao_social'] == 'Empresa Teste'
    assert parsed['emitente']['cnpj'] == '12345678000195'
    assert parsed['emitente']['ie'] == '123456789012'
    
    # Destinatário
    assert parsed['destinatario']['razao_social'] == 'Cliente Teste'
    assert parsed['destinatario']['cnpj'] == '12345678901'
    
    # Itens
    assert len(parsed['itens']) == 1
    assert parsed['itens'][0]['descricao'] == 'Produto Teste'
    assert parsed['itens'][0]['quantidade'] == 2.0
    assert parsed['itens'][0]['valor_unitario'] == 100.0
    assert parsed['itens'][0]['valor_total'] == 200.0
    assert parsed['itens'][0]['cfop'] == '5102'
    assert parsed['itens'][0]['ncm'] == '84713000'
    
    # Impostos
    assert parsed['total_detalhado']['valor_total'] == 200.0
    
    # Total
    assert parsed['total'] == 200.0
    
    # Número e data
    assert parsed['numero'] == '12345'
    assert '2023-10-24' in parsed['data_emissao']

def test_parse_invalid_xml():
    """Test parsing of invalid XML."""
    result = xml_parser.parse_xml_string("<not_xml>Invalid</not_xml>")
    assert isinstance(result, dict)
    assert 'error' in result
    # O parser rotula como tipo desconhecido
    assert result['error'] == 'unknown_document_type'
    assert result['message'] == 'Tipo de documento não identificado'
    assert result['raw_text'] == '<not_xml>Invalid</not_xml>'

def test_parse_xml_file(tmp_path):
    """Test parsing XML from a file."""
    # Create a temporary XML file
    xml_file = tmp_path / "test_nfe.xml"
    xml_file.write_text(SAMPLE_XML, encoding='utf-8')
    
    # Parse the file
    result = xml_parser.parse_xml_file(str(xml_file))
    
    # Check the result
    assert isinstance(result, dict)
    assert 'emitente' in result
    assert result['emitente']['razao_social'] == 'Empresa Teste'
    assert result['total'] == 200.0

def test_extract_from_xml_file(tmp_path):
    """Test extracting data from an XML file."""
    # Create a temporary XML file
    xml_file = tmp_path / "test_nfe.xml"
    xml_file.write_text(SAMPLE_XML, encoding='utf-8')
    
    # Extract data
    result = extract_from_file(str(xml_file))
    
    # Check the result
    assert isinstance(result, dict)
    assert 'document_type' in result
    assert result['document_type'] == 'NFe'
    assert 'emitente' in result
    assert result['emitente']['razao_social'] == 'Empresa Teste'

@patch('PIL.Image.open')
@patch('backend.agents.extraction.ocr_processor.image_to_text')
def test_extract_from_image(mock_image_to_text, mock_image_open, tmp_path):
    """Test extracting text from an image."""
    # Configure mocks
    mock_image_to_text.return_value = "Texto extraído da imagem"
    mock_image = mock_image_open.return_value.__enter__.return_value
    
    # Create a temporary image file
    img_file = tmp_path / "test_img.png"
    img_file.write_bytes(b'dummy image data')
    
    # Extract text
    result = extract_from_file(str(img_file))
    
    # Check the result
    assert isinstance(result, dict)
    assert 'raw_text' in result
    assert result['raw_text'] == "Texto extraído da imagem"
    assert result['document_type'] == 'unknown'

@patch('backend.agents.extraction.ocr_processor.pdf_to_text')
def test_extract_from_pdf(mock_pdf_to_text, tmp_path):
    """Test extracting text from a PDF."""
    # Configure mock
    mock_pdf_to_text.return_value = "Texto extraído do PDF"
    
    # Create a temporary PDF file
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b'%PDF-1.4\ndummy PDF content')
    
    # Extract text
    result = extract_from_file(str(pdf_file))
    
    # Check the result
    assert isinstance(result, dict)
    assert 'raw_text' in result
    assert result['raw_text'] == "Texto extraído do PDF"
    assert result['document_type'] == 'unknown'

def test_extract_unsupported_file_type(tmp_path):
    """Test extracting from an unsupported file type."""
    # Create a temporary file with an unsupported extension
    file_path = tmp_path / "test.unsupported"
    file_path.write_text("Some content")
    
    # Try to extract
    result = extract_from_file(str(file_path))
    
    # Should return an error
    assert 'error' in result
    assert result['error'] == 'unsupported_file_type'
