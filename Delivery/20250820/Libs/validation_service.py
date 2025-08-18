"""
Data Validation Service for SkyNET I2A2 HR Automation System

Handles all data validation using LLM integration.
Follows Single Responsibility Principle and Strategy pattern.
"""

import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from .data_models import ValidationResult, ValidationLevel
from .config_manager import GeminiConfig


class ValidationStrategy(ABC):
    """Abstract base class for validation strategies."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any], rules: List[str]) -> List[ValidationResult]:
        """Validate data according to rules."""
        pass


class LLMValidationStrategy(ValidationStrategy):
    """
    LLM-based validation strategy using Gemini API.
    
    Implements Strategy pattern for pluggable validation methods.
    """
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def validate(self, data: Dict[str, Any], rules: List[str]) -> List[ValidationResult]:
        """
        Validate data using Gemini LLM.
        
        Args:
            data: Data to validate
            rules: Validation rules to apply
            
        Returns:
            List of validation results
        """
        try:
            prompt = self._build_validation_prompt(data, rules)
            response = self._call_gemini_api(prompt)
            return self._parse_validation_response(response)
        except Exception as e:
            return [ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Validation failed: {str(e)}"
            )]
    
    def _build_validation_prompt(self, data: Dict[str, Any], rules: List[str]) -> str:
        """Build prompt for LLM validation."""
        return f"""
        Sistema: Você é um validador especializado em dados de RH e folha de pagamento.
        
        Contexto: Analisando dados de benefícios (VR) com as seguintes regras:
        {rules}
        
        Dados recebidos:
        {data}
        
        Por favor, analise e retorne:
        1. Inconsistências encontradas
        2. Correções sugeridas
        3. Validação de regras de negócio
        4. Alertas sobre possíveis problemas
        
        Formato da resposta:
        {{
            "inconsistencias": [],
            "correcoes": [],
            "validacoes": [],
            "alertas": []
        }}
        
        Por favor, responda APENAS com o JSON solicitado, sem texto adicional.
        """
    
    def _call_gemini_api(self, prompt: str) -> Optional[Dict]:
        """Make API call to Gemini."""
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.config.api_key
        }
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.1,
                "topK": 1
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API call failed: {e}")
    
    def _parse_validation_response(self, response: Optional[Dict]) -> List[ValidationResult]:
        """Parse LLM response into validation results."""
        if not response or 'candidates' not in response:
            return [ValidationResult(
                level=ValidationLevel.ERROR,
                message="Invalid API response"
            )]
        
        try:
            text_response = response['candidates'][0]['content']['parts'][0]['text']
            text_response = self._clean_json_response(text_response)
            
            result_data = json.loads(text_response)
            return self._convert_to_validation_results(result_data)
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return [ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Failed to parse validation response: {e}"
            )]
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from LLM."""
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        return response.strip()
    
    def _convert_to_validation_results(self, data: Dict) -> List[ValidationResult]:
        """Convert parsed JSON to ValidationResult objects."""
        results = []
        
        # Add inconsistencies as errors
        for inconsistency in data.get('inconsistencias', []):
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Inconsistency: {inconsistency}"
            ))
        
        # Add alerts as warnings
        for alert in data.get('alertas', []):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Alert: {alert}"
            ))
        
        # Add corrections as info
        for correction in data.get('correcoes', []):
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message=f"Correction: {correction}"
            ))
        
        return results


class DataValidationService:
    """
    Service for validating HR data using pluggable validation strategies.
    
    Follows Service pattern and Dependency Injection.
    """
    
    def __init__(self, validation_strategy: ValidationStrategy):
        self.validation_strategy = validation_strategy
    
    def validate_employee_data(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate employee data."""
        rules = [
            "Datas devem estar em formato válido (YYYY-MM-DD)",
            "Campos obrigatórios não podem estar vazios",
            "Datas de admissão e demissão devem ser coerentes",
            "Matrícula deve ser única"
        ]
        return self.validation_strategy.validate(data, rules)
    
    def validate_vacation_data(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate vacation data."""
        rules = [
            "Dias de férias devem estar entre 0 e 30",
            "Períodos de férias não podem se sobrepor",
            "Matrícula deve existir na base de ativos"
        ]
        return self.validation_strategy.validate(data, rules)
    
    def validate_termination_data(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate termination data."""
        rules = [
            "Datas de demissão devem ser válidas",
            "Status de comunicado deve estar preenchido",
            "Data de demissão não pode ser anterior à admissão"
        ]
        return self.validation_strategy.validate(data, rules)
    
    def validate_working_days_data(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate working days data."""
        rules = [
            "Feriados devem ter data válida",
            "Cada estado deve ter seus feriados específicos",
            "Dias úteis devem ser coerentes com feriados"
        ]
        return self.validation_strategy.validate(data, rules)