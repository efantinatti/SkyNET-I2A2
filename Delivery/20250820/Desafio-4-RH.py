#!/usr/bin/env python3
"""
SkyNET I2A2 HR Automation System - Legacy Interface

This file maintains backward compatibility with the original interface
while using the new refactored architecture under the hood.

For new development, please use hr_automation_main.py instead.

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
Version: 2.0 (Refactored with Legacy Compatibility)
"""

import sys
from pathlib import Path

# Add the Libs directory to the Python path
sys.path.append(str(Path(__file__).parent / 'Libs'))

from Libs.hr_automation_orchestrator import HRAutomationOrchestrator


def executar_automacao_vr():
    """
    Legacy function that maintains the original interface.
    
    This function provides backward compatibility while using
    the new refactored architecture internally.
    
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
        
        # Execute the automation using new architecture
        output_file_path = orchestrator.execute_full_automation()
        
        # Extract just the filename for backward compatibility
        filename = Path(output_file_path).name
        return f"Output/{filename}"
        
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        return None


# Maintain original entry point for backward compatibility
if __name__ == "__main__":
    result = executar_automacao_vr()
    if result:
        print(f"\n✅ Legacy interface completed successfully")
        print(f"📄 Generated file: {result}")
    else:
        print(f"\n❌ Legacy interface failed")
        sys.exit(1)