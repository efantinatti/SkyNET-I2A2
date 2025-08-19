#!/usr/bin/env python3
"""
SkyNET I2A2 HR Automation System - Legacy Interface

This file maintains backward compatibility with the original interface
while using the new refactored architecture under the hood.

For new development, please use hr_automation_main.py instead.

Author: SkyNET I2A2 AI Agent
Date: 2025-08-19
Version: 2.1 (Enhanced Legacy Compatibility)
"""

import sys
import argparse
from pathlib import Path

# Add the Libs directory to the Python path
sys.path.append(str(Path(__file__).parent / 'Libs'))

from Libs.hr_automation_orchestrator import HRAutomationOrchestrator


def executar_automacao_vr(force_run: bool = False):
    """
    Legacy function that maintains the original interface.
    
    This function provides backward compatibility while using
    the new refactored architecture internally.
    
    Args:
        force_run (bool): If True, bypass file integrity check and force execution
    
    Returns:
        str: Path to generated output file, or None if failed
    """
    try:
        print("🔄 Initializing HR Automation System...")
        print("ℹ️  Using refactored architecture with improved maintainability")
        
        # Initialize the new orchestrator
        orchestrator = HRAutomationOrchestrator()
        
        # Validate environment
        if not orchestrator.validate_environment():
            print("❌ Environment validation failed")
            return None
        
        # Execute the automation with force parameter
        output_file_path = orchestrator.execute_full_automation(force_run=force_run)
        
        if output_file_path == "No processing needed - files unchanged":
            return output_file_path
        
        # Extract just the filename for backward compatibility
        filename = Path(output_file_path).name
        return f"Output/{filename}"
        
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        return None


def parse_arguments():
    """Parse command line arguments for the legacy interface."""
    parser = argparse.ArgumentParser(
        description="SkyNET I2A2 HR Automation System - Legacy Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Desafio-4-RH.py              # Normal run (check for file changes first)
  python Desafio-4-RH.py --force      # Force run (bypass file integrity check)
  
For more advanced options, use the modern interface:
  python hr_automation_main.py --help
        
About File Integrity Monitoring:
  This system now includes smart file monitoring that only processes 
  when Excel files have actually changed, saving time and resources.
  
  Use --force only when you need to override this behavior.
        """
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force execution bypassing file integrity check'
    )
    
    return parser.parse_args()


# Maintain original entry point for backward compatibility
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Show clear guidance about force parameter
    if not args.force:
        print("💡 TIP: If you see 'No file changes detected', you can use:")
        print("        python Desafio-4-RH.py --force")
        print("        to bypass file integrity check and force execution\n")
    else:
        print("⚡ FORCE MODE: Bypassing file integrity check\n")
    
    # Execute with force parameter
    result = executar_automacao_vr(force_run=args.force)
    
    if result:
        print(f"\n✅ Legacy interface completed successfully")
        print(f"📄 Generated file: {result}")
        sys.exit(0)
    else:
        print(f"\n❌ Legacy interface failed")
        sys.exit(1)