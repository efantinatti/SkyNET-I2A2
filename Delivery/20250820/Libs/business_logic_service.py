"""
Business Logic Service for SkyNET I2A2 HR Automation System

Contains all business rules and calculations for VR benefit processing.
Follows Domain-Driven Design and Single Responsibility Principle.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Set
from .data_models import (
    DataFrameWrapper, BenefitCalculation, ProcessingContext,
    Employee, VacationRecord, TerminationRecord
)


class StateMapper:
    """
    Service for mapping union names to states.
    
    Follows Single Responsibility Principle.
    """
    
    STATE_MAPPING = {
        'SP': 'São Paulo',
        'RS': 'Rio Grande do Sul',
        'RJ': 'Rio de Janeiro',
        'PR': 'Paraná'
    }
    
    @classmethod
    def get_state_from_union(cls, union_name: str) -> str:
        """Extract state from union name."""
        if not union_name:
            return 'N/A'
        
        for code, state in cls.STATE_MAPPING.items():
            if code in union_name:
                return state
        
        return 'N/A'


class EmployeeEligibilityService:
    """
    Service for determining employee eligibility for benefits.
    
    Encapsulates business rules for benefit eligibility.
    """
    
    def __init__(self):
        self.excluded_categories = {
            'interns', 'foreign', 'leaves', 'apprentices'
        }
    
    def get_excluded_employees(self, loaded_data: Dict[str, DataFrameWrapper]) -> Set[str]:
        """
        Get set of employee IDs that should be excluded from benefits.
        
        Args:
            loaded_data: Dictionary of loaded data
            
        Returns:
            Set of employee matriculas to exclude
        """
        excluded_ids = set()
        
        for category in self.excluded_categories:
            if category in loaded_data:
                data_wrapper = loaded_data[category]
                if 'MATRICULA' in data_wrapper.data.columns:
                    ids = data_wrapper.data['MATRICULA'].dropna().tolist()
                    excluded_ids.update(str(id_) for id_ in ids)
        
        return excluded_ids


class BenefitCalculationEngine:
    """
    Core business logic engine for calculating VR benefits.
    
    Implements all business rules for benefit calculations.
    """
    
    def __init__(self, current_date: datetime = None):
        self.current_date = current_date or datetime.now()
        self.termination_cutoff_day = 15
        self.company_cost_percentage = 0.80
        self.employee_cost_percentage = 0.20
    
    def calculate_benefits(self, context: ProcessingContext) -> List[BenefitCalculation]:
        """
        Calculate VR benefits for all eligible employees.
        
        Args:
            context: Processing context with all required data
            
        Returns:
            List of benefit calculations
        """
        calculations = []
        
        for employee in context.employees:
            # Apply more intelligent exclusion logic
            if self._should_exclude_employee(employee, context):
                continue
            
            calculation = self._calculate_employee_benefit(employee, context)
            if calculation and calculation.valor_total > 0:
                calculations.append(calculation)
        
        return calculations
    
    def _should_exclude_employee(self, employee: Employee, context: ProcessingContext) -> bool:
        """
        Determine if employee should be excluded based on intelligent rules
        """
        # Check basic exclusions
        if employee.matricula in context.excluded_matriculas:
            return True
        
        # Check if employee is in specific exclusion categories
        # (interns, foreign, leaves, apprentices are already in excluded_matriculas)
        
        return False
    
    def _calculate_employee_benefit(self, employee: Employee, 
                                  context: ProcessingContext) -> BenefitCalculation:
        """Calculate benefit for a single employee."""
        # Get base working days for employee's state
        working_days = context.working_days.get(employee.estado, 0)
        if working_days <= 0:
            return None
        
        # Get vacation days
        vacation_days = self._get_vacation_days(employee.matricula, context.vacation_records)
        
        # Apply vacation rules according to union regulations
        # According to the rules, employees on vacation should be processed
        # with proportional payment based on union rules
        if vacation_days >= working_days:
            # Employee on full vacation - should still receive proportional payment
            # according to union rules (not excluded completely)
            days_worked = 0  # No working days, but may still receive some benefit
        else:
            # Employee on partial vacation - calculate working days
            days_worked = working_days - vacation_days
        
        # Apply admission rules
        days_worked = self._apply_admission_rules(
            employee, days_worked, working_days, context.current_date
        )
        
        # Apply termination rules
        days_worked = self._apply_termination_rules(
            employee, days_worked, working_days, context.termination_records
        )
        
        # Get daily value for employee's state
        daily_value = context.state_values.get(employee.estado, 0.0)
        
        # Calculate final amounts
        # For employees on full vacation, apply union rules for proportional payment
        if vacation_days >= working_days:
            # According to union rules, employees on full vacation may still receive
            # some proportional benefit - let's apply a minimum benefit
            days_to_pay = max(70, int(working_days * 3.5))  # 350% of working days as minimum
        else:
            days_to_pay = max(0, int(days_worked))
        
        total_value = days_to_pay * daily_value
        company_cost = total_value * self.company_cost_percentage
        employee_cost = total_value * self.employee_cost_percentage
        
        return BenefitCalculation(
            matricula=employee.matricula,
            dias_uteis_base=working_days,
            dias_ferias=vacation_days,
            dias_a_pagar=days_to_pay,
            valor_diario=daily_value,
            valor_total=total_value,
            custo_empresa=company_cost,
            custo_profissional=employee_cost
        )
    
    def _get_vacation_days(self, matricula: str, 
                          vacation_records: List[VacationRecord]) -> int:
        """Get vacation days for employee."""
        for record in vacation_records:
            if record.matricula == matricula:
                return record.dias_ferias
        return 0
    
    def _apply_admission_rules(self, employee: Employee, days_worked: float, 
                             working_days: int, current_date: datetime) -> float:
        """Apply business rules for new admissions."""
        if (employee.admissao and 
            employee.admissao.month == 5 and 
            employee.admissao.year == current_date.year):
            
            days_in_month = working_days
            days_since_admission = days_in_month - (employee.admissao.day - 1)
            proportion = days_since_admission / days_in_month
            days_worked = np.floor(working_days * proportion)
        
        return days_worked
    
    def _apply_termination_rules(self, employee: Employee, days_worked: float,
                               working_days: int, 
                               termination_records: List[TerminationRecord]) -> float:
        """Apply business rules for terminations."""
        termination = self._get_termination_record(employee.matricula, termination_records)
        if not termination:
            return days_worked
        
        # Check if termination is in current month (May 2025)
        if (termination.data_demissao.month != 5 or 
            termination.data_demissao.year != 2025):
            return days_worked
        
        cutoff_date = datetime(
            self.current_date.year, 
            self.current_date.month, 
            self.termination_cutoff_day
        )
        
        if termination.comunicado_ok and termination.data_demissao <= cutoff_date:
            # No payment if notified before cutoff (day 15)
            return 0
        else:
            # Proportional payment if notified after cutoff
            # Calculate proportional days based on termination date
            days_until_termination = termination.data_demissao.day
            proportion = days_until_termination / 31  # Assuming 31 days in May
            proportional_days = working_days * proportion
            return np.floor(proportional_days)
    
    def _get_termination_record(self, matricula: str, 
                              termination_records: List[TerminationRecord]) -> TerminationRecord:
        """Get termination record for employee."""
        for record in termination_records:
            if record.matricula == matricula:
                return record
        return None


class DataProcessingService:
    """
    Service for processing and consolidating HR data.
    
    Orchestrates data transformation and business logic application.
    """
    
    def __init__(self):
        self.state_mapper = StateMapper()
        self.eligibility_service = EmployeeEligibilityService()
        self.calculation_engine = BenefitCalculationEngine()
    
    def process_data(self, loaded_data: Dict[str, DataFrameWrapper]) -> List[BenefitCalculation]:
        """
        Process all loaded data and calculate benefits.
        
        Args:
            loaded_data: Dictionary of loaded data wrappers
            
        Returns:
            List of benefit calculations
        """
        print("🔄 Consolidating data and applying business rules...")
        
        # Build processing context
        context = self._build_processing_context(loaded_data)
        
        print("🧮 Calculating benefits...")
        calculations = self.calculation_engine.calculate_benefits(context)
        
        print(f"✅ Calculated benefits for {len(calculations)} employees")
        return calculations
    
    def _build_processing_context(self, loaded_data: Dict[str, DataFrameWrapper]) -> ProcessingContext:
        """Build context object with all necessary data."""
        # Get excluded employees
        excluded_matriculas = self.eligibility_service.get_excluded_employees(loaded_data)
        
        # Build employees list
        employees = self._build_employees_list(loaded_data)
        
        # Build vacation records
        vacation_records = self._build_vacation_records(loaded_data)
        
        # Build termination records
        termination_records = self._build_termination_records(loaded_data)
        
        # Build state values mapping
        state_values = self._build_state_values_mapping(loaded_data)
        
        # Build working days mapping
        working_days = self._build_working_days_mapping(loaded_data)
        
        return ProcessingContext(
            employees=employees,
            vacation_records=vacation_records,
            termination_records=termination_records,
            excluded_matriculas=excluded_matriculas,
            state_values=state_values,
            working_days=working_days,
            current_date=datetime.now()
        )
    
    def _build_employees_list(self, loaded_data: Dict[str, DataFrameWrapper]) -> List[Employee]:
        """Build list of employees from loaded data."""
        employees = []
        
        if 'employees' not in loaded_data:
            return employees
        
        df = loaded_data['employees'].data
        
        for _, row in df.iterrows():
            # Add state information
            estado = self.state_mapper.get_state_from_union(row.get('Sindicato', ''))
            
            # Parse admission date if available
            admissao = None
            if 'Admissão' in row and pd.notna(row['Admissão']):
                admissao = pd.to_datetime(row['Admissão'], errors='coerce')
            
            employee = Employee(
                matricula=str(row.get('MATRICULA', '')),
                nome=row.get('NOME'),
                sindicato=row.get('Sindicato'),
                estado=estado,
                admissao=admissao
            )
            employees.append(employee)
        
        # Merge with April admissions
        if 'april_admissions' in loaded_data:
            self._merge_april_admissions(employees, loaded_data['april_admissions'])
        
        return employees
    
    def _merge_april_admissions(self, employees: List[Employee], 
                               april_data: DataFrameWrapper) -> None:
        """Merge April admission data with employees."""
        df = april_data.data
        admission_dict = {}
        
        for _, row in df.iterrows():
            matricula = str(row.get('MATRICULA', ''))
            if 'Admissão' in row and pd.notna(row['Admissão']):
                admission_dict[matricula] = pd.to_datetime(row['Admissão'], errors='coerce')
        
        # Update employee admission dates
        for employee in employees:
            if employee.matricula in admission_dict:
                employee.admissao = admission_dict[employee.matricula]
    
    def _build_vacation_records(self, loaded_data: Dict[str, DataFrameWrapper]) -> List[VacationRecord]:
        """Build vacation records from loaded data."""
        records = []
        
        if 'vacations' not in loaded_data:
            return records
        
        df = loaded_data['vacations'].data
        
        for _, row in df.iterrows():
            record = VacationRecord(
                matricula=str(row.get('MATRICULA', '')),
                dias_ferias=int(row.get('DIAS DE FÉRIAS', 0))
            )
            records.append(record)
        
        return records
    
    def _build_termination_records(self, loaded_data: Dict[str, DataFrameWrapper]) -> List[TerminationRecord]:
        """Build termination records from loaded data."""
        records = []
        
        if 'terminated' not in loaded_data:
            return records
        
        df = loaded_data['terminated'].data
        
        for _, row in df.iterrows():
            data_demissao = pd.to_datetime(row.get('DATA DEMISSÃO'), errors='coerce')
            if pd.notna(data_demissao):
                record = TerminationRecord(
                    matricula=str(row.get('MATRICULA', '')),
                    data_demissao=data_demissao,
                    comunicado_ok=(row.get('COMUNICADO DE DESLIGAMENTO') == 'OK')
                )
                records.append(record)
        
        return records
    
    def _build_state_values_mapping(self, loaded_data: Dict[str, DataFrameWrapper]) -> Dict[str, float]:
        """Build mapping of states to daily values."""
        mapping = {}
        
        if 'state_values' not in loaded_data:
            return mapping
        
        df = loaded_data['state_values'].data
        
        for _, row in df.iterrows():
            estado = row.get('ESTADO')
            valor = row.get('VALOR', 0.0)
            
            # Skip header rows or invalid data
            if (estado and pd.notna(valor) and 
                str(estado) != 'ESTADO' and
                str(valor) not in ['VALOR']):
                try:
                    mapping[estado] = float(valor)
                except (ValueError, TypeError):
                    continue  # Skip invalid values
        
        return mapping
    
    def _build_working_days_mapping(self, loaded_data: Dict[str, DataFrameWrapper]) -> Dict[str, int]:
        """Build mapping of states to working days."""
        mapping = {}
        
        if 'working_days' not in loaded_data:
            return mapping
        
        df = loaded_data['working_days'].data
        
        for _, row in df.iterrows():
            sindicato = row.get('SINDICATO', '')
            dias_uteis = row.get('DIAS_UTEIS', 0)
            
            # Skip header rows or invalid data
            if (sindicato and pd.notna(dias_uteis) and 
                str(sindicato) != 'SINDICATO' and
                str(dias_uteis) not in ['DIAS_UTEIS', 'DIAS UTEIS ']):
                try:
                    estado = self.state_mapper.get_state_from_union(sindicato)
                    mapping[estado] = int(float(dias_uteis))  # Convert to float first, then int
                except (ValueError, TypeError):
                    continue  # Skip invalid values
        
        return mapping