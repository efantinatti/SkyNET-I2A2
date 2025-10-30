from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Emitente(BaseModel):
    razao_social: Optional[str]
    cnpj: Optional[str]
    inscricao_estadual: Optional[str]


class Destinatario(BaseModel):
    razao_social: Optional[str]
    cnpj_cpf: Optional[str]


class Item(BaseModel):
    descricao: Optional[str]
    quantidade: Optional[float]
    valor_unitario: Optional[float]
    valor_total: Optional[float]
    ncm: Optional[str]
    cfop: Optional[str]
    cst: Optional[str]


class Impostos(BaseModel):
    icms: Optional[float]
    ipi: Optional[float]
    pis: Optional[float]
    cofins: Optional[float]
    icms_st: Optional[float]


class FiscalDocument(BaseModel):
    document_type: Optional[str] = Field(None, description="NFe/NFCe/CTe")
    numero: Optional[str]
    data_emissao: Optional[str]
    emitente: Optional[Emitente]
    destinatario: Optional[Destinatario]
    itens: List[Item] = []
    impostos: Optional[Impostos]
    cfop: Optional[str]
    total: Optional[float]
    raw: Optional[Dict[str, Any]] = None
