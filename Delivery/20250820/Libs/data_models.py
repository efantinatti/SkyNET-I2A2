"""
Data Models for SkyNET I2A2 HR Automation System

Contains all data models and enums used throughout the system.
Follows Data Transfer Object pattern for clean data handling.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd


class EmployeeStatus(Enum):
    """Enumeration for employee status types."""
    ACTIVE = "ATIVO"
    TERMINATED = "DESLIGADO"
    ON_LEAVE = "AFASTADO"
    INTERN = "ESTAGIO"
    APPRENTICE = "APRENDIZ"
    FOREIGN = "EXTERIOR"


class ValidationLevel(Enum):
    """Enumeration for validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Data model for validation results."""
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class Employee:
    """Data model for employee information."""
    matricula: str
    nome: Optional[str] = None
    sindicato: Optional[str] = None
    estado: Optional[str] = None
    admissao: Optional[datetime] = None
    status: Optional[EmployeeStatus] = None


@dataclass
class VacationRecord:
    """Data model for vacation records."""
    matricula: str
    dias_ferias: int
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None


@dataclass
class TerminationRecord:
    """Data model for termination records."""
    matricula: str
    data_demissao: datetime
    comunicado_ok: bool


@dataclass
class BenefitCalculation:
    """Data model for benefit calculation results."""
    matricula: str
    dias_uteis_base: int
    dias_ferias: int
    dias_a_pagar: int
    valor_diario: float
    valor_total: float
    custo_empresa: float
    custo_profissional: float


@dataclass
class ProcessingContext:
    """Context object containing all data needed for processing."""
    employees: List[Employee]
    vacation_records: List[VacationRecord]
    termination_records: List[TerminationRecord]
    excluded_matriculas: set
    state_values: Dict[str, float]
    working_days: Dict[str, int]
    current_date: datetime


class DataFrameWrapper:
    """
    Wrapper for pandas DataFrame to provide clean interface.
    
    Follows Adapter pattern to isolate pandas dependency.
    """
    
    def __init__(self, df: pd.DataFrame):
        self._df = df
    
    @property
    def data(self) -> pd.DataFrame:
        """Get underlying DataFrame."""
        return self._df
    
    def clean_column_names(self) -> None:
        """Clean column names by removing whitespace."""
        try:
            # Only apply string operations if columns are actually strings
            if hasattr(self._df.columns, 'str'):
                self._df.columns = self._df.columns.str.strip()
        except (AttributeError, TypeError):
            # Skip cleaning if columns are not string-based (e.g., numeric indices)
            pass
    
    def drop_empty_rows(self) -> None:
        """Remove completely empty rows."""
        self._df.dropna(how='all', inplace=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for validation."""
        return self._df.head().to_dict()
    
    def __len__(self) -> int:
        """Get number of rows."""
        return len(self._df)
    
    def __getitem__(self, key):
        """Get column or slice."""
        return self._df[key]