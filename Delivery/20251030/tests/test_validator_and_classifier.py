import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from backend.tools import fiscal_validator
from backend.agents import classifier


def test_validate_cnpj():
    assert fiscal_validator.validate_cnpj('12345678000195') is False


def test_totals_validation():
    items = [{'valor_total': 10.0}, {'valor_total': 5.0}]
    ok, s = fiscal_validator.validate_totals(items, 15.0)
    assert ok and abs(s - 15.0) < 1e-6


def test_classify_simple():
    parsed = {'cfop': '5102', 'emitente': {'cnpj': '11111111000191'}, 'total': 2000}
    res = classifier.classify_document(parsed)
    assert res['tipo'] == 'venda'
