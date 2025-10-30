# Guia de Testes

Este documento descreve como executar, organizar e expandir a suíte de testes da aplicação **SkyNET I2A2**.

## ✅ Pré-requisitos

- Python 3.12
- Ambiente virtual configurado (`.venv`) com as dependências de `requirements.txt`
- Variáveis de ambiente opcionais (ex.: `GOOGLE_API_KEY`) não são necessárias para a maioria dos testes, pois o `conftest.py` fornece dummies.

## ▶️ Executando os testes

```bash
python3 -m pytest                 # roda toda a suíte
python3 -m pytest -m unit          # apenas testes marcados como unitários
python3 -m pytest -m "not slow"   # exclui testes lentos
python3 -m pytest tests/test_chat_agent.py  # arquivo específico
```

### Cobertura

```bash
python3 -m pytest --cov=backend --cov=frontend --cov-report=term-missing
```

- Meta: **≥ 80%** de cobertura global.
- Para HTML detalhado: `--cov-report=html` e abrir `htmlcov/index.html`.

## 🧭 Arquitetura da suíte

| Área | Arquivo(s) chave | O que valida |
|------|------------------|--------------|
| Importador & Upload | `tests/test_importador.py` | Preparação de registros, validações e integração com RAG. |
| Validador Fiscal | `tests/test_recipient_fields.py`, `tests/test_fiscal_validator_agent.py` | Normalização/validação de CNPJ/CPF, fluxos do agente fiscal. |
| Armazenamento | `tests/test_postgresql_storage.py`, `tests/storage_compliance.py` | Serialização JSONB, filtros, contratos do `StorageInterface`. |
| RAG & Embeddings | `tests/test_rag_service.py`, `tests/test_free_embedding_service.py`, `tests/test_analysis_cache.py` | Fallback de embeddings, pipeline RAG e cache de análises. |
| Chat IA | `tests/test_chat_agent.py` | Roteamento, reaproveitamento de cache e fluxos de resposta. |
| Parsing/OCR | `tests/test_xml_parser.py`, `tests/test_llm_ocr_mapper.py` | Extração de dados fiscais via XML e OCR assistido. |

## 🧰 Fixtures e dummies

- `tests/conftest.py` fornece mocks para `pandas`, `streamlit`, `pytesseract`, `langchain`, etc.
- `streamlit.session_state` é um dicionário especializado (`_DummySessionState`) com `get` seguro.
- Utilize `monkeypatch` para ajustar comportamentos durante os testes (ex.: `datetime.now`).

## ➕ Adicionando novos testes

1. **Escolha o escopo**: coloque testes unitários na pasta `tests/` com prefixo `test_`. Use subpasta se o módulo tiver muitos cenários.
2. **Nomeie claramente**: métodos devem seguir o padrão `test_<comportamento>_<cenario>()`.
3. **Marque quando necessário**:
   - `@pytest.mark.unit`, `@pytest.mark.integration`, etc. conforme `pytest.ini`.
   - Para `async`, execute via `asyncio.run` ou marque com `pytest.mark.asyncio`.
4. **Mocks controlados**: substitua dependências externas com `MagicMock/AsyncMock`. Use fixtures do `conftest.py`.
5. **Asserts descritivos**: mensagens claras e validações do estado final e colaterais (chamadas, metadados, logs). Evite asserts genéricos.
6. **Cobertura regressiva**: sempre que corrigir um bug, adicione teste reproduzindo o cenário original.

## 🔁 Fluxo recomendado

1. `python3 -m pytest` – valida regressão completa.
2. Ajuste dos testes quebrados (fase 2).
3. Adição de novos testes (fase 3).
4. `python3 -m pytest --maxfail=1` – garante estabilidade antes do commit.
5. Atualize este README se novas pastas/marcadores forem criados.

## 📋 Observações finais

- A suíte utiliza dummies para bibliotecas pesadas; se algum teste demandar comportamento real, adicione fixtures específicas.
- Documente novos marcadores em `pytest.ini`.
- Para testes de integração que exigem banco de dados, utilize o marcador `integration` e mantenha dependências isoladas.

Bom trabalho e bons testes! 🚀
