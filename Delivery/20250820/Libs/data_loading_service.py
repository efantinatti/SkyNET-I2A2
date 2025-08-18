"""
Data Loading Service for SkyNET I2A2 HR Automation System

Handles loading and initial processing of Excel files.
Follows Single Responsibility Principle and Factory pattern.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from .data_models import DataFrameWrapper, ValidationResult
from .validation_service import DataValidationService


class DataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self, file_path: str) -> DataFrameWrapper:
        """Load data from file."""
        pass


class ExcelDataLoader(DataLoader):
    """
    Excel file data loader.
    
    Implements Factory pattern for different data source types.
    """
    
    def __init__(self, sheet_name: Optional[str] = None, header: Optional[int] = 0):
        self.sheet_name = sheet_name
        self.header = header
    
    def load(self, file_path: str) -> DataFrameWrapper:
        """Load data from Excel file."""
        try:
            if self.header is None:
                df = pd.read_excel(file_path, sheet_name=self.sheet_name, header=None)
            else:
                df = pd.read_excel(file_path, sheet_name=self.sheet_name, header=self.header)
            
            wrapper = DataFrameWrapper(df)
            wrapper.clean_column_names()
            return wrapper
            
        except Exception as e:
            raise FileNotFoundError(f"Failed to load {file_path}: {e}")


class DataLoaderFactory:
    """
    Factory for creating appropriate data loaders.
    
    Follows Factory pattern for object creation.
    """
    
    @staticmethod
    def create_excel_loader(sheet_name: Optional[str] = None, 
                          header: Optional[int] = 0) -> ExcelDataLoader:
        """Create Excel data loader with specified parameters."""
        return ExcelDataLoader(sheet_name=sheet_name, header=header)


class FileLoadingService:
    """
    Service for loading and validating all HR data files.
    
    Follows Service pattern and coordinates file loading operations.
    """
    
    def __init__(self, data_dir: str, validation_service: DataValidationService):
        self.data_dir = Path(data_dir)
        self.validation_service = validation_service
        self.loaded_data: Dict[str, DataFrameWrapper] = {}
        self.validation_results: Dict[str, List[ValidationResult]] = {}
    
    def load_all_files(self) -> Dict[str, DataFrameWrapper]:
        """
        Load all required HR data files.
        
        Returns:
            Dictionary of loaded data with file identifiers as keys
        """
        file_configs = self._get_file_configurations()
        
        for file_key, config in file_configs.items():
            try:
                file_path = self.data_dir / config['filename']
                loader = DataLoaderFactory.create_excel_loader(
                    sheet_name=config.get('sheet_name'),
                    header=config.get('header', 0)
                )
                
                data_wrapper = loader.load(str(file_path))
                
                # Apply any post-loading transformations
                if 'columns' in config:
                    data_wrapper.data.columns = config['columns']
                
                data_wrapper.drop_empty_rows()
                
                # Validate the loaded data
                validation_results = self._validate_file_data(file_key, data_wrapper)
                
                self.loaded_data[file_key] = data_wrapper
                self.validation_results[file_key] = validation_results
                
                print(f"✅ Loaded {file_key}: {len(data_wrapper)} records")
                self._print_validation_results(file_key, validation_results)
                
            except Exception as e:
                print(f"❌ Failed to load {file_key}: {e}")
                raise
        
        return self.loaded_data
    
    def _get_file_configurations(self) -> Dict[str, Dict]:
        """Get configuration for all files to be loaded."""
        return {
            'employees': {
                'filename': 'ATIVOS.xlsx',
                'sheet_name': 'ATIVOS'
            },
            'working_days': {
                'filename': 'Base dias uteis.xlsx',
                'sheet_name': 'Planilha1',
                'columns': ['SINDICATO', 'DIAS_UTEIS']
            },
            'state_values': {
                'filename': 'Base sindicato x valor.xlsx',
                'sheet_name': 'Planilha1',
                'columns': ['ESTADO', 'VALOR']
            },
            'terminated': {
                'filename': 'DESLIGADOS.xlsx',
                'sheet_name': 'DESLIGADOS '
            },
            'interns': {
                'filename': 'ESTÁGIO.xlsx',
                'sheet_name': 'Planilha1'
            },
            'foreign': {
                'filename': 'EXTERIOR.xlsx',
                'sheet_name': 'Planilha1',
                'header': None,
                'columns': ['MATRICULA', 'VALOR_EXTERIOR', 'STATUS_EXTERIOR']
            },
            'vacations': {
                'filename': 'FÉRIAS.xlsx',
                'sheet_name': 'Planilha1'
            },
            'april_admissions': {
                'filename': 'ADMISSÃO ABRIL.xlsx',
                'sheet_name': 'Planilha1'
            },
            'leaves': {
                'filename': 'AFASTAMENTOS.xlsx',
                'sheet_name': 'Planilha1'
            },
            'apprentices': {
                'filename': 'APRENDIZ.xlsx',
                'sheet_name': 'Planilha1'
            },
            'template': {
                'filename': 'VR MENSAL 05.2025.xlsx',
                'sheet_name': 'VR MENSAL 05.2025'
            }
        }
    
    def _validate_file_data(self, file_key: str, data_wrapper: DataFrameWrapper) -> List[ValidationResult]:
        """Validate loaded file data based on file type."""
        data_dict = data_wrapper.to_dict()
        
        validation_methods = {
            'employees': self.validation_service.validate_employee_data,
            'vacations': self.validation_service.validate_vacation_data,
            'terminated': self.validation_service.validate_termination_data,
            'working_days': self.validation_service.validate_working_days_data
        }
        
        validation_method = validation_methods.get(file_key)
        if validation_method:
            return validation_method(data_dict)
        
        return []  # No specific validation for this file type
    
    def _print_validation_results(self, file_key: str, results: List[ValidationResult]) -> None:
        """Print validation results in a user-friendly format."""
        if not results:
            return
        
        warnings = [r for r in results if r.level.value == 'warning']
        if warnings:
            print(f"   ⚠️  Warnings for {file_key}:")
            for warning in warnings[:3]:  # Show max 3 warnings
                print(f"      - {warning.message}")
            
            if len(warnings) > 3:
                print(f"      ... and {len(warnings) - 3} more warnings")
    
    def get_loaded_data(self, file_key: str) -> Optional[DataFrameWrapper]:
        """Get specific loaded data by key."""
        return self.loaded_data.get(file_key)
    
    def get_validation_results(self, file_key: str) -> List[ValidationResult]:
        """Get validation results for specific file."""
        return self.validation_results.get(file_key, [])