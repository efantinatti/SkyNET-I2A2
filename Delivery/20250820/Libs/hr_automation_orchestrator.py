"""
HR Automation Orchestrator for SkyNET I2A2

Main orchestrator that coordinates all services following Clean Architecture principles.
Implements Facade pattern for simplified client interface.
"""

import logging
from pathlib import Path
from typing import Optional
from .config_manager import ConfigManager
from .validation_service import DataValidationService, LLMValidationStrategy
from .data_loading_service import FileLoadingService
from .business_logic_service import DataProcessingService
from .output_service import OutputGenerationService
from .email_library import EmailNotifier
from .file_integrity_service import FileIntegrityService

# Suppress numexpr info messages
logging.getLogger('numexpr.utils').setLevel(logging.WARNING)


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
        
        # Initialize file integrity service
        self.file_integrity_service = FileIntegrityService(data_dir)
        
        print("🚀 SkyNET I2A2 HR Automation System Initialized")
        print(f"📁 Data Directory: {data_dir}")
        print(f"📁 Output Directory: {output_dir}")
        print(f"🔒 File Integrity Monitoring: Enabled")
    
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
    
    def execute_full_automation(self, force_run: bool = False) -> str:
        """
        Execute the complete HR automation workflow.
        
        Args:
            force_run: If True, skip file integrity check and run anyway
        
        Returns:
            Path to generated output file
            
        Raises:
            Exception: If any step in the automation fails
        """
        try:
            print("=" * 60)
            print("🤖 STARTING HR AUTOMATION PROCESS")
            print("=" * 60)
            
            # File Integrity Check (unless forced)
            if not force_run:
                print("\n🔒 INTEGRITY CHECK: Checking for file changes...")
                changes = self.file_integrity_service.check_file_changes()
                
                # Check if any files have changed or are new
                if not changes['changed'] and not changes['new']:
                    print("✅ No file changes detected. Automation not needed.")
                    print("📊 File Status Summary:")
                    print(f"   • Unchanged files: {len(changes['unchanged'])}")
                    print(f"   • Missing files: {len(changes['missing'])}")
                    
                    if changes['missing']:
                        print(f"⚠️ Warning: {len(changes['missing'])} expected files are missing:")
                        for missing_file in changes['missing']:
                            print(f"   - {missing_file}")
                    
                    print("\n💡 To force execution:")
                    print("   Legacy interface:  python Desafio-4-RH.py --force")
                    print("   Modern interface:  python hr_automation_main.py --force")
                    return "No processing needed - files unchanged"
                
                # Files have changed, display summary
                print("📈 File changes detected:")
                if changes['new']:
                    print(f"   • New files: {len(changes['new'])}")
                    for filename in changes['new']:
                        print(f"     - {filename}")
                
                if changes['changed']:
                    print(f"   • Changed files: {len(changes['changed'])}")
                    for filename in changes['changed']:
                        print(f"     - {filename}")
                
                if changes['unchanged']:
                    print(f"   • Unchanged files: {len(changes['unchanged'])}")
                
                if changes['missing']:
                    print(f"   • Missing files: {len(changes['missing'])}")
                    for filename in changes['missing']:
                        print(f"     - {filename}")
                
                print("🔄 Proceeding with automation due to file changes...")
            else:
                print("⚡ FORCED RUN: Skipping file integrity check")
            
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
            
            # Step 4: Update file checksums (if not forced run)
            if not force_run:
                print("\n🔒 STEP 4a: Updating file integrity checksums...")
                changes = self.file_integrity_service.check_file_changes()
                if self.file_integrity_service.update_checksums(changes):
                    updated_count = len(changes['changed']) + len(changes['new'])
                    print(f"✅ Updated checksums for {updated_count} files")
                else:
                    print("⚠️ Some checksum updates failed")
            
            # Step 5: Send email notification
            print(f"\n📧 STEP {'5' if not force_run else '4b'}: Sending email notification...")
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
            },
            'file_integrity': {
                'monitoring_enabled': True,
                'change_summary': self.file_integrity_service.get_change_summary()
            }
        }
    
    def check_file_integrity(self) -> dict:
        """
        Check file integrity without running automation.
        
        Returns:
            Dictionary with file change information
        """
        return self.file_integrity_service.check_file_changes()
    
    def initialize_file_monitoring(self) -> bool:
        """
        Initialize file monitoring for all import files.
        
        Returns:
            True if initialization successful, False otherwise
        """
        print("🔒 Initializing file integrity monitoring...")
        success = self.file_integrity_service.initialize_monitoring()
        
        if success:
            print("✅ File monitoring initialized successfully")
        else:
            print("❌ File monitoring initialization failed")
        
        return success
    
    def force_checksum_update(self) -> bool:
        """
        Force update of all file checksums.
        
        Returns:
            True if update successful, False otherwise
        """
        print("🔄 Forcing checksum update for all files...")
        
        # Get current file states
        changes = self.file_integrity_service.check_file_changes()
        
        # Force update by treating all existing files as "changed"
        all_files = {}
        all_files.update(changes['changed'])
        all_files.update(changes['new'])
        all_files.update({f: 'updated' for f in changes['unchanged']})
        
        # Calculate fresh checksums for unchanged files
        for filename in changes['unchanged']:
            file_path = Path('Import') / filename
            if file_path.exists():
                try:
                    md5_checksum = self.file_integrity_service.calculate_file_md5(file_path)
                    all_files[filename] = md5_checksum
                except Exception as e:
                    print(f"⚠️ Error calculating checksum for {filename}: {e}")
        
        # Update all checksums
        forced_changes = {
            'changed': all_files,
            'new': {},
            'missing': changes['missing'],
            'unchanged': []
        }
        
        success = self.file_integrity_service.update_checksums(forced_changes)
        
        if success:
            updated_count = len(all_files)
            print(f"✅ Force updated checksums for {updated_count} files")
        else:
            print("❌ Some checksum updates failed")
        
        return success
    
    def clean_orphaned_checksums(self) -> int:
        """
        Clean orphaned checksum files.
        
        Returns:
            Number of orphaned files removed
        """
        print("🧹 Cleaning orphaned checksum files...")
        removed_count = self.file_integrity_service.clean_orphaned_md5_files()
        
        if removed_count > 0:
            print(f"✅ Removed {removed_count} orphaned checksum files")
        else:
            print("✅ No orphaned checksum files found")
        
        return removed_count
    
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