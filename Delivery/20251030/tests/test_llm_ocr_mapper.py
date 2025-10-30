from backend.tools.llm_ocr_mapper import LLMOCRMapper


def test_llm_mapper_heuristic_fallback():
    sample = """
    NF-e
    CNPJ 12.345.678/0001-95
    Data 10/10/2020
    Item Agua 10 1,50 15,00
    TOTAL 15,00
    """
    mapper = LLMOCRMapper()
    result = mapper.map_ocr_text(sample)
    
    # Verifica se o resultado é um dicionário
    assert isinstance(result, dict), "O resultado deve ser um dicionário"
    
    # Verifica se os campos obrigatórios estão presentes
    assert 'emitente' in result, "O resultado deve conter o campo 'emitente'"
    assert isinstance(result['emitente'], dict), "O campo 'emitente' deve ser um dicionário"
    
    # Verifica se o CNPJ foi extraído corretamente
    assert any(key in result['emitente'] for key in ('cnpj', 'documento')), "O emitente deve conter o CNPJ"
    cnpj_value = result['emitente'].get('documento') or result['emitente'].get('cnpj')
    assert cnpj_value == '12345678000195', "O CNPJ extraído está incorreto"
    
    # Verifica se a data foi extraída corretamente
    assert 'data_emissao' in result, "O resultado deve conter a data de emissão"
    assert result['data_emissao'] == '10/10/2020', "A data de emissão extraída está incorreta"
    
    # Verifica se os itens foram extraídos corretamente
    assert 'itens' in result, "O resultado deve conter a lista de itens"
    assert isinstance(result['itens'], list), "O campo 'itens' deve ser uma lista"
    
    # Verifica se o total foi extraído corretamente
    assert 'total' in result, "O resultado deve conter o total"
    assert result['total'] == 15.0, "O total extraído está incorreto"
