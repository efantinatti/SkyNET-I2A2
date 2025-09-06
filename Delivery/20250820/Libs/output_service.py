"""
Output Generation Service for SkyNET I2A2 HR Automation System

Handles generation and formatting of output files.
Follows Single Responsibility Principle and Template Method pattern.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict
from abc import ABC, abstractmethod
from .data_models import BenefitCalculation, DataFrameWrapper


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""
    
    @abstractmethod
    def format_data(self, calculations: List[BenefitCalculation], 
                   template: DataFrameWrapper) -> pd.DataFrame:
        """Format calculation data for output."""
        pass


class CSVOutputFormatter(OutputFormatter):
    """
    CSV output formatter for VR benefit calculations.
    
    Implements Template Method pattern for output formatting.
    """
    
    def format_data(self, calculations: List[BenefitCalculation], 
                   template: DataFrameWrapper) -> pd.DataFrame:
        """
        Format benefit calculations as CSV-ready DataFrame.
        
        Args:
            calculations: List of benefit calculations
            template: Template data wrapper for column ordering
            
        Returns:
            Formatted DataFrame ready for CSV export
        """
        if not calculations:
            return pd.DataFrame()
        
        # Build output DataFrame
        output_data = self._build_output_data(calculations)
        output_df = pd.DataFrame(output_data)
        
        
        # Ensure column order matches template if template has columns
        if template and hasattr(template, 'data') and not template.data.empty:
            try:
                template_columns = template.data.columns.tolist()
                # Only reindex if template columns exist and are valid
                if template_columns and all(isinstance(col, str) for col in template_columns):
                    output_df = output_df.reindex(columns=template_columns, fill_value='')
            except Exception as e:
                print(f"⚠️ Warning: Could not match template columns: {e}")
                # Continue with default column order
        
        return output_df
    
    def _build_output_data(self, calculations: List[BenefitCalculation]) -> Dict:
        """Build output data dictionary from calculations."""
        output_data = {
            'Matricula': [],
            'Admissão': [],
            'Sindicato do Colaborador': [],
            'Competência': [],
            'Dias': [],
            'VALOR DIÁRIO VR': [],
            'TOTAL': [],
            'Custo empresa': [],
            'Desconto profissional': [],
            'OBS GERAL': []
        }
        
        for calc in calculations:
            output_data['Matricula'].append(calc.matricula)
            output_data['Admissão'].append('')  # Will be filled from employee data
            output_data['Sindicato do Colaborador'].append('')  # Will be filled from employee data
            output_data['Competência'].append('05/2025')
            output_data['Dias'].append(calc.dias_a_pagar)
            output_data['VALOR DIÁRIO VR'].append(calc.valor_diario)
            output_data['TOTAL'].append(calc.valor_total)
            output_data['Custo empresa'].append(calc.custo_empresa)
            output_data['Desconto profissional'].append(calc.custo_profissional)
            output_data['OBS GERAL'].append('')
        
        return output_data


class OutputWriter(ABC):
    """Abstract base class for output writers."""
    
    @abstractmethod
    def write(self, data: pd.DataFrame, file_path: str) -> bool:
        """Write data to file."""
        pass


class CSVOutputWriter(OutputWriter):
    """
    CSV file writer with proper formatting for Brazilian locale.
    
    Handles CSV-specific formatting requirements.
    """
    
    def write(self, data: pd.DataFrame, file_path: str) -> bool:
        """
        Write DataFrame to CSV file with Brazilian formatting.
        
        Args:
            data: DataFrame to write
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with Brazilian CSV format
            data.to_csv(
                file_path,
                index=False,
                decimal=',',
                sep=';',
                encoding='utf-8'
            )
            return True
            
        except Exception as e:
            print(f"❌ Failed to write output file: {e}")
            return False


class OutputGenerationService:
    """
    Service for generating output files from benefit calculations.
    
    Coordinates formatting and writing operations.
    """
    
    def __init__(self, output_dir: str = 'Output'):
        self.output_dir = Path(output_dir)
        self.formatter = CSVOutputFormatter()
        self.writer = CSVOutputWriter()
    
    def generate_output(self, calculations: List[BenefitCalculation],
                       template: DataFrameWrapper,
                       employee_data: DataFrameWrapper = None,
                       april_admissions_data: DataFrameWrapper = None) -> str:
        """
        Generate output file from benefit calculations.
        
        Args:
            calculations: List of benefit calculations
            template: Template for column ordering
            employee_data: Optional employee data for enrichment
            april_admissions_data: Optional April admissions data for dates
            
        Returns:
            Generated file path
        """
        print("📊 Formatting output data...")
        
        # Format the data
        output_df = self.formatter.format_data(calculations, template)
        
        # Enrich with employee data if available
        if employee_data is not None:
            output_df = self._enrich_with_employee_data(output_df, employee_data, april_admissions_data)
        
        # Generate output file
        output_filename = self._generate_filename()
        output_path = self.output_dir / output_filename
        
        print(f"💾 Writing output to {output_path}...")
        
        success = self.writer.write(output_df, str(output_path))
        
        if success:
            print(f"✅ Output file generated: {output_filename}")
            print(f"📊 Records written: {len(output_df)}")
            return str(output_path)
        else:
            raise RuntimeError("Failed to generate output file")
    
    def _enrich_with_employee_data(self, output_df: pd.DataFrame, 
                                  employee_data: DataFrameWrapper,
                                  april_admissions_data: DataFrameWrapper = None) -> pd.DataFrame:
        """Enrich output data with employee information."""
        emp_df = employee_data.data
        
        # Create lookup dictionaries
        admission_lookup = {}
        union_lookup = {}
        
        # Get data from main employees file
        for _, row in emp_df.iterrows():
            matricula = str(row.get('MATRICULA', ''))
            
            # Format admission date if available in main file
            if 'Admissão' in row and pd.notna(row['Admissão']):
                admission_date = pd.to_datetime(row['Admissão'], errors='coerce')
                if pd.notna(admission_date):
                    admission_lookup[matricula] = admission_date.strftime('%d/%m/%Y')
            
            # Get union info
            if 'Sindicato' in row and pd.notna(row['Sindicato']):
                union_lookup[matricula] = row['Sindicato']
        
        # Get admission dates from April admissions file if provided
        if april_admissions_data is not None:
            april_df = april_admissions_data.data
            for _, row in april_df.iterrows():
                matricula = str(row.get('MATRICULA', ''))
                if 'Admissão' in row and pd.notna(row['Admissão']):
                    admission_date = pd.to_datetime(row['Admissão'], errors='coerce')
                    if pd.notna(admission_date):
                        admission_lookup[matricula] = admission_date.strftime('%d/%m/%Y')
        
        # Enrich output DataFrame
        output_df['Admissão'] = output_df['Matricula'].map(
            lambda x: admission_lookup.get(str(x), '')
        )
        output_df['Sindicato do Colaborador'] = output_df['Matricula'].map(
            lambda x: union_lookup.get(str(x), '')
        )
        
        return output_df
    
    def _generate_filename(self) -> str:
        """Generate output filename with timestamp."""
        return 'VR_MENSAL_05_2025_FINAL.csv'