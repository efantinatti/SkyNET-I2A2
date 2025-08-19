#!/usr/bin/env python3
"""
SkyNET I2A2 HR Automation System - Main Entry Point

Refactored version following Clean Code, SOLID principles, and design patterns.
This script provides a clean, maintainable interface to the HR automation system.

Author: SkyNET I2A2 AI Agent
Date: 2025-08-19
Version: 2.1 (File Integrity Integration)
"""

import sys
import argparse
from pathlib import Path

# Add the Libs directory to the Python path
sys.path.append(str(Path(__file__).parent / 'Libs'))

from Libs.hr_automation_orchestrator import HRAutomationOrchestrator


def main():
    """
    Main entry point with command-line interface for file integrity management.
    """
    parser = argparse.ArgumentParser(
        description='SkyNET I2A2 HR Automation System with File Integrity Monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hr_automation_main.py                    # Run with integrity check
  python hr_automation_main.py --force            # Force run without integrity check
  python hr_automation_main.py --check            # Check file integrity only
  python hr_automation_main.py --init             # Initialize file monitoring
  python hr_automation_main.py --update-checksums # Force update all checksums
  python hr_automation_main.py --clean            # Clean orphaned checksum files
  python hr_automation_main.py --status           # Show system status
        """
    )
    
    parser.add_argument('--force', action='store_true',
                       help='Force run automation without file integrity check')
    parser.add_argument('--check', action='store_true',
                       help='Check file integrity without running automation')
    parser.add_argument('--init', action='store_true',
                       help='Initialize file integrity monitoring')
    parser.add_argument('--update-checksums', action='store_true',
                       help='Force update all file checksums')
    parser.add_argument('--clean', action='store_true',
                       help='Clean orphaned checksum files')
    parser.add_argument('--status', action='store_true',
                       help='Show system status including file integrity')
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = HRAutomationOrchestrator()
        
        # Handle different command modes
        if args.status:
            print("📊 SYSTEM STATUS")
            print("=" * 40)
            status = orchestrator.get_system_status()
            
            print(f"Configuration: {'✅ Loaded' if status['config_loaded'] else '❌ Failed'}")
            print(f"Gemini API: {'✅ Configured' if status['gemini_configured'] else '❌ Not configured'}")
            print(f"Email: {'✅ Configured' if status['email_configured'] else '❌ Not configured'}")
            print(f"Recipients: {status['recipient_count']}")
            print(f"File Monitoring: {'✅ Enabled' if status['file_integrity']['monitoring_enabled'] else '❌ Disabled'}")
            print(f"File Status: {status['file_integrity']['change_summary']}")
            
        elif args.check:
            print("🔒 FILE INTEGRITY CHECK")
            print("=" * 40)
            changes = orchestrator.check_file_integrity()
            
            if changes['new']:
                print(f"🆕 New files ({len(changes['new'])}):")
                for filename in changes['new']:
                    print(f"   • {filename}")
            
            if changes['changed']:
                print(f"🔄 Changed files ({len(changes['changed'])}):")
                for filename in changes['changed']:
                    print(f"   • {filename}")
            
            if changes['unchanged']:
                print(f"✅ Unchanged files ({len(changes['unchanged'])}):")
                for filename in changes['unchanged']:
                    print(f"   • {filename}")
            
            if changes['missing']:
                print(f"❌ Missing files ({len(changes['missing'])}):")
                for filename in changes['missing']:
                    print(f"   • {filename}")
            
            if not changes['new'] and not changes['changed']:
                print("✅ No files changed - automation not needed")
            else:
                print("🔄 Files changed - automation recommended")
                
        elif args.init:
            orchestrator.initialize_file_monitoring()
            
        elif args.update_checksums:
            orchestrator.force_checksum_update()
            
        elif args.clean:
            orchestrator.clean_orphaned_checksums()
            
        else:
            # Default: Run automation with or without force
            if not orchestrator.validate_environment():
                print("❌ Environment validation failed. Please check configuration.")
                return
            
            output_file = orchestrator.execute_full_automation(force_run=args.force)
            
            if output_file != "No processing needed - files unchanged":
                print(f"\n🎉 Automation completed successfully!")
                print(f"📄 Output file: {output_file}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        if '--debug' in sys.argv:
            raise


if __name__ == "__main__":
    """
    Main entry point for the refactored HR automation system.
    
    The new architecture provides:
    - Clean separation of concerns
    - SOLID principles compliance  
    - Improved testability and maintainability
    - Better error handling and logging
    - Pluggable validation strategies
    - Configurable services
    - File integrity monitoring with MD5 checksums
    """
    main()