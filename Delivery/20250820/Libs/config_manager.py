"""
Configuration Manager for SkyNET I2A2 HR Automation System

Handles all configuration loading and validation following Single Responsibility Principle.
"""

import configparser
import os
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class ValidationRules:
    """Data class for validation rules configuration."""
    max_vacation_days: int
    required_fields: List[str]
    date_format: str


@dataclass
class EmailConfig:
    """Data class for email configuration."""
    smtp_host: str
    smtp_port: int
    smtp_encryption: str
    sender_name: str
    sender_email: str
    sender_password: str
    recipient_emails: List[str]


@dataclass
class GeminiConfig:
    """Data class for Gemini API configuration."""
    api_key: str


@dataclass
class AppConfig:
    """Main configuration container."""
    gemini: GeminiConfig
    email: EmailConfig
    validation_rules: ValidationRules


class ConfigManager:
    """
    Configuration manager responsible for loading and validating configuration.
    
    Follows Single Responsibility Principle - only handles configuration management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional config path."""
        if config_path is None:
            config_path = self._get_default_config_path()
        self.config_path = Path(config_path)
        self._validate_config_exists()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent.parent
        return current_dir / 'Config' / 'config.ini'
    
    def _validate_config_exists(self) -> None:
        """Validate that configuration file exists."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
    
    def load_config(self) -> AppConfig:
        """
        Load and parse configuration from INI file.
        
        Returns:
            AppConfig: Parsed configuration object
            
        Raises:
            ValueError: If configuration is invalid
        """
        config = configparser.ConfigParser()
        config.read(self.config_path)
        
        try:
            return AppConfig(
                gemini=self._load_gemini_config(config),
                email=self._load_email_config(config),
                validation_rules=self._load_validation_rules(config)
            )
        except KeyError as e:
            raise ValueError(f"Missing configuration section or key: {e}")
    
    def _load_gemini_config(self, config: configparser.ConfigParser) -> GeminiConfig:
        """Load Gemini API configuration."""
        return GeminiConfig(
            api_key=config['gemini']['api_key']
        )
    
    def _load_email_config(self, config: configparser.ConfigParser) -> EmailConfig:
        """Load email configuration."""
        recipient_emails = [
            email.strip() 
            for email in config['email']['recipient_emails'].split(',')
        ]
        
        return EmailConfig(
            smtp_host=config['email']['smtp_host'],
            smtp_port=int(config['email']['smtp_port']),
            smtp_encryption=config['email']['smtp_encryption'],
            sender_name=config['email']['sender_name'],
            sender_email=config['email']['sender_email'],
            sender_password=config['email']['sender_password'],
            recipient_emails=recipient_emails
        )
    
    def _load_validation_rules(self, config: configparser.ConfigParser) -> ValidationRules:
        """Load validation rules configuration."""
        required_fields = [
            field.strip() 
            for field in config['validation_rules']['required_fields'].split(',')
        ]
        
        return ValidationRules(
            max_vacation_days=int(config['validation_rules']['max_vacation_days']),
            required_fields=required_fields,
            date_format=config['validation_rules']['date_format']
        )