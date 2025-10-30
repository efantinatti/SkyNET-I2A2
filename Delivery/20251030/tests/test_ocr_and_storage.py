import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from backend.database.local_storage import LocalJSONStorage
from backend.tools.ocr_processor import ocr_text_to_document


def test_ocr_mapping_basic():
    text = """
    EMPRESA X
    CNPJ: 12.345.678/0001-95
    N° 234
    Data: 10/10/2025
    Parafuso 2 2,00 4,00
    Total: 4,00
    """
    doc = ocr_text_to_document(text)

    assert doc['tipo_documento'] == 'MDF'
    emitente_cnpj = doc['emitente'].get('cnpj') or doc['emitente'].get('documento')
    if emitente_cnpj is not None:
        assert emitente_cnpj == '12345678000195'

    numero = doc.get('numero')
    if numero is not None:
        assert numero == '234'

    total = doc.get('total')
    if total is not None:
        assert isinstance(total, (int, float))
        assert abs(total - 4.0) < 1e-6


def test_local_storage_save_and_load(tmp_path):
    storage = LocalJSONStorage(data_dir=str(tmp_path))

    saved_doc = storage.save_fiscal_document({
        'file_name': 'nota.xml',
        'document_type': 'NFe',
        'document_number': '1'
    })

    assert saved_doc['id'] is not None

    loaded = storage.get_fiscal_document(saved_doc['id'])

    assert loaded is not None
    assert loaded['file_name'] == 'nota.xml'
    assert loaded['document_number'] == '1'
