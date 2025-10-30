"""Example: insert a fiscal document and a history event into Supabase.

Set SUPABASE_URL and SUPABASE_KEY in environment before running.
"""
import os
import json
from backend import storage_supabase as storage


def main():
    doc = {
        'file_name': 'exemplo.xml',
        'document_type': 'NFe',
        'document_number': '123',
        'issuer_cnpj': '12345678000195',
        'extracted_data': {'emitente': {'razao_social': 'Empresa X'}},
        'validation_status': 'success',
        'classification': {'tipo': 'venda', 'setor': 'comercio'}
    }

    print('Inserting fiscal document...')
    res = storage.insert_fiscal_document(doc)
    print('Result:', res)

    # If the response returns an id, use it; else try to fetch by document_number
    fid = None
    try:
        if isinstance(res, list) and res:
            fid = res[0].get('id')
        elif isinstance(res, dict):
            fid = res.get('id')
    except Exception:
        pass

    event = {
        'fiscal_document_id': fid,
        'event_type': 'created',
        'event_data': {'note': 'Inserção via script exemplo'}
    }
    print('Inserting history event...')
    print(storage.insert_document_history(event))


if __name__ == '__main__':
    main()
