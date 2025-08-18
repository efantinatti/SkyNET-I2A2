"""
HR Automation Orchestrator for SkyNET I2A2

Main orchestrator that coordinates all services following Clean Architecture principles.
Implements Facade pattern for simplified client interface.
"""

from pathlib import Path
from typing import Optional
from .config_manager import ConfigManager
from .validation_service import DataValidationService, LLMValidationStrategy
from .data_loading_service import FileLoadingService
from .business_logic_service import DataProcessingService
from .output_service import OutputGenerationService
from .email_library import EmailNotifier


class HRAutomationOrchestrator:
    """
    Main orchestrator for HR automation process.
    
    Implements Facade pattern to provide simple interface for complex operations.
    Follows Clean Architecture with clear separation of concerns.
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 data_dir: str = 'Import', 
                 output_dir: str = 'Output'):
        """
        Initialize the HR automation orchestrator.
        
        Args:
            config_path: Path to configuration file
            data_dir: Directory containing input Excel files
            output_dir: Directory for output files
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        # Initialize services
        self._initialize_services(data_dir, output_dir)
        
        print("🚀 SkyNET I2A2 HR Automation System Initialized")
        print(f"📁 Data Directory: {data_dir}")
        print(f"📁 Output Directory: {output_dir}")
    
    def _initialize_services(self, data_dir: str, output_dir: str) -> None:
        """Initialize all required services."""
        # Validation service with LLM strategy
        llm_strategy = LLMValidationStrategy(self.config.gemini)
        self.validation_service = DataValidationService(llm_strategy)
        
        # File loading service
        self.file_loading_service = FileLoadingService(data_dir, self.validation_service)
        
        # Business logic service
        self.processing_service = DataProcessingService()
        
        # Output generation service
        self.output_service = OutputGenerationService(output_dir)
        
        # Email notification service
        self.email_service = EmailNotifier()
    
    def execute_full_automation(self) -> str:
        """
        Execute the complete HR automation workflow.
        
        Returns:
            Path to generated output file
            
        Raises:
            Exception: If any step in the automation fails
        """
        try:
            print("=" * 60)
            print("🤖 STARTING HR AUTOMATION PROCESS")
            print("=" * 60)
            
            # Step 1: Load and validate all data files
            print("\n📂 STEP 1: Loading and validating data files...")
            loaded_data = self.file_loading_service.load_all_files()
            
            # Step 2: Process data and calculate benefits
            print("\n🔄 STEP 2: Processing data and calculating benefits...")
            calculations = self.processing_service.process_data(loaded_data)
            
            # Step 3: Generate output file
            print("\n📊 STEP 3: Generating output file...")
            template = self.file_loading_service.get_loaded_data('template')
            employee_data = self.file_loading_service.get_loaded_data('employees')
            april_admissions_data = self.file_loading_service.get_loaded_data('april_admissions')
            
            output_file_path = self.output_service.generate_output(
                calculations, template, employee_data, april_admissions_data
            )
            
            # Step 4: Send email notification
            print("\n📧 STEP 4: Sending email notification...")
            self._send_completion_notification(output_file_path)
            
            print("\n" + "=" * 60)
            print("✅ HR AUTOMATION COMPLETED SUCCESSFULLY!")
            print(f"📄 Output file: {output_file_path}")
            print(f"👥 Employees processed: {len(calculations)}")
            print("=" * 60)
            
            return output_file_path
            
        except Exception as e:
            print(f"\n❌ AUTOMATION FAILED: {e}")
            raise
    
    def _send_completion_notification(self, output_file_path: str) -> None:
        """Send email notification about process completion."""
        try:
            filename = Path(output_file_path).name
            
            success = self.email_service.send_completion_notification(
                filename=output_file_path,
                attach_file=True
            )
            
            if success:
                print("✅ Email notification sent successfully")
                recipient_count = len(self.config.email.recipient_emails)
                print(f"📧 Notified {recipient_count} recipients")
            else:
                print("⚠️ Failed to send email notification")
                
        except Exception as e:
            print(f"⚠️ Email notification error: {e}")
    
    def get_system_status(self) -> dict:
        """
        Get system status and configuration summary.
        
        Returns:
            Dictionary with system status information
        """
        return {
            'config_loaded': bool(self.config),
            'gemini_configured': bool(self.config.gemini.api_key),
            'email_configured': bool(self.config.email.smtp_host),
            'recipient_count': len(self.config.email.recipient_emails),
            'validation_rules': {
                'max_vacation_days': self.config.validation_rules.max_vacation_days,
                'required_fields_count': len(self.config.validation_rules.required_fields)
            }
        }
    
    def validate_environment(self) -> bool:
        """
        Validate that the environment is properly configured.
        
        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Check configuration
            status = self.get_system_status()
            
            if not status['config_loaded']:
                print("❌ Configuration not loaded")
                return False
            
            if not status['gemini_configured']:
                print("❌ Gemini API not configured")
                return False
            
            if not status['email_configured']:
                print("❌ Email settings not configured")
                return False
            
            # Check directories
            data_dir = Path('Import')
            output_dir = Path('Output')
            
            if not data_dir.exists():
                print(f"❌ Data directory not found: {data_dir}")
                return False
            
            if not output_dir.exists():
                print(f"⚠️ Output directory not found, will be created: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
            
            print("✅ Environment validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Environment validation failed: {e}")
            return False


def main():
    """
    Main entry point for the HR automation system.
    
    Provides command-line interface for running the automation.
    """
    try:
        # Initialize orchestrator
        orchestrator = HRAutomationOrchestrator()
        
        # Validate environment
        if not orchestrator.validate_environment():
            print("❌ Environment validation failed. Please check configuration.")
            return
        
        # Execute automation
        output_file = orchestrator.execute_full_automation()
        
        print(f"\n🎉 Automation completed successfully!")
        print(f"📄 Output file: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()