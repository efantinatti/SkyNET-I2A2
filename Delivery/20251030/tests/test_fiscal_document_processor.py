"""Testes para o processador de documentos fiscais."""
import os
import sys
import pytest
from types import ModuleType, SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.tools.fiscal_document_processor as processor_module
from backend.tools.fiscal_document_processor import FiscalDocumentProcessor


def _ensure_module(name: str, module):
    if name not in sys.modules:
        sys.modules[name] = module


_ensure_module(
    'pytesseract',
    SimpleNamespace(
        image_to_string=lambda *args, **kwargs: "",
        get_tesseract_version=lambda: "5.0",
        pytesseract=SimpleNamespace(tesseract_cmd=None),
    ),
)
_ensure_module('pytesseract.pytesseract', SimpleNamespace(tesseract_cmd=None))

_ensure_module(
    'pdf2image',
    SimpleNamespace(convert_from_path=lambda *args, **kwargs: [], convert_from_bytes=lambda *args, **kwargs: []),
)

if 'PIL' not in sys.modules:
    pil_module = ModuleType('PIL')
    image_module = ModuleType('PIL.Image')
    image_module.Resampling = SimpleNamespace(LANCZOS=1)
    image_module.Image = MagicMock
    pil_module.Image = image_module
    pil_module.UnidentifiedImageError = Exception
    image_enhance = ModuleType('PIL.ImageEnhance')
    image_enhance.Contrast = lambda img: SimpleNamespace(enhance=lambda value: img)
    sys.modules['PIL'] = pil_module
    sys.modules['PIL.Image'] = image_module
    sys.modules['PIL.ImageEnhance'] = image_enhance

reportlab_module = sys.modules.get('reportlab')
if reportlab_module is None:
    fake_canvas = SimpleNamespace(
        Canvas=lambda *args, **kwargs: SimpleNamespace(
            showPage=lambda: None,
            save=lambda: None,
            setFont=lambda *a, **k: None,
            drawString=lambda *a, **k: None,
        )
    )
    reportlab_module = ModuleType('reportlab')
    reportlab_module.lib = SimpleNamespace(pagesizes=SimpleNamespace(letter=(612, 792)))
    reportlab_module.pdfgen = SimpleNamespace(canvas=fake_canvas)
    sys.modules['reportlab'] = reportlab_module
    sys.modules['reportlab.lib'] = reportlab_module.lib
    sys.modules['reportlab.lib.pagesizes'] = reportlab_module.lib.pagesizes
    sys.modules['reportlab.pdfgen'] = reportlab_module.pdfgen
    sys.modules['reportlab.pdfgen.canvas'] = reportlab_module.pdfgen.canvas

@pytest.fixture
def processor():
    return FiscalDocumentProcessor()


@pytest.fixture(autouse=True)
def ensure_re(monkeypatch):
    import re

    monkeypatch.setattr(processor_module, 're', re, raising=False)


def test_is_supported_file(processor):
    assert processor.is_supported_file('teste.pdf') is True
    assert processor.is_supported_file('teste.JPG') is True
    assert processor.is_supported_file('teste.txt') is False


def test_extract_text_from_image(tmp_path, processor, monkeypatch):
    image_path = tmp_path / 'nota.png'
    image_path.write_bytes(b'fake')

    fake_image = MagicMock()
    monkeypatch.setattr(processor_module, 'Image', SimpleNamespace(open=MagicMock(return_value=fake_image)), raising=False)
    monkeypatch.setattr(
        FiscalDocumentProcessor,
        '_extract_text_from_image',
        MagicMock(return_value='OCR resultado'),
    )

    result = processor.extract_text(image_path)

    assert result['success'] is True
    assert result['text'] == 'OCR resultado'
    assert result['pages'][1] == 'OCR resultado'


def test_extract_text_from_pdf(tmp_path, processor, monkeypatch):
    pdf_path = tmp_path / 'nota.pdf'
    pdf_path.write_bytes(b'%PDF')

    fake_pages = {1: 'Página 1', 2: 'Página 2'}
    monkeypatch.setattr(
        FiscalDocumentProcessor,
        '_extract_text_from_pdf',
        MagicMock(return_value=fake_pages),
    )

    result = processor.extract_text(pdf_path)

    assert result['success'] is True
    assert result['pages'] == fake_pages
    assert result['text'].startswith('--- PÁGINA 1 ---')


def test_identify_document_type_variants(processor):
    assert processor.identify_document_type('Nota Fiscal Eletrônica Nº 123') == 'nfe'
    assert processor.identify_document_type('NFCE modelo 65 em trânsito') == 'nfce'
    assert processor.identify_document_type('Conhecimento de Transporte Eletrônico') == 'cte'
    assert processor.identify_document_type('Manifesto de Documentos Fiscais Eletrônicos') == 'mdfe'
    assert processor.identify_document_type('Documento sem identificação') == 'unknown'


def test_extract_with_heuristics_returns_core_fields(processor):
    sample_text = """
    NOTA FISCAL ELETRÔNICA
    Nº 12345
    EMITENTE: LOJA TESTE LTDA
    CNPJ: 12.345.678/0001-90
    DESTINATÁRIO: CONSUMIDOR
    CPF: 123.456.789-00
    VALOR TOTAL R$ 175,50
    ICMS: R$ 31,59
    """

    doc = processor._extract_with_heuristics(sample_text, 'nfe')

    assert doc['success'] is True
    assert doc['document_type'] == 'nfe'
    assert doc['emitente']['cnpj'] == '12.345.678/0001-90'
    assert doc['destinatario']['cpf'] == '123.456.789-00'
    assert doc['valor_total'] == pytest.approx(175.50)
    assert doc['impostos']['icms'] == pytest.approx(31.59)


def test_process_document_uses_llm_when_available(tmp_path, processor, monkeypatch):
    llm_response = {
        'success': True,
        'document_type': 'nfe',
        'numero': '12345',
        'valor_total': 200.0,
        'emitente': {'razao_social': 'Empresa X'},
        'destinatario': {'razao_social': 'Cliente Y'},
        'itens': [{'descricao': 'Item', 'valor_total': 200.0}],
        'impostos': {'icms': 36.0},
    }

    class FakeMapper:
        def __init__(self, *_args, **_kwargs):
            self.available = True

        def map_ocr_text(self, text):
            return llm_response

    fake_llm_module = ModuleType('backend.tools.llm_ocr_mapper')
    fake_llm_module.LLMOCRMapper = FakeMapper
    sys.modules['backend.tools.llm_ocr_mapper'] = fake_llm_module

    monkeypatch.setattr(
        FiscalDocumentProcessor,
        'extract_text',
        lambda self, path: {
            'success': True,
            'text': 'conteúdo OCR',
            'pages': {1: 'conteúdo'},
        },
    )

    pdf_path = tmp_path / 'nota.pdf'
    pdf_path.write_bytes(b'%PDF')

    result = processor.process_document(pdf_path)

    assert result['success'] is True
    assert result['numero'] == '12345'
    assert result['valor_total'] == 200.0
    assert result['impostos']['icms'] == 36.0


if __name__ == "__main__":
    pytest.main(["-v", "test_fiscal_document_processor.py"])
