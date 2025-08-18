#!/usr/bin/env python3
"""
SkyNET I2A2 HR Automation System - Main Entry Point

Refactored version following Clean Code, SOLID principles, and design patterns.
This script provides a clean, maintainable interface to the HR automation system.

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
Version: 2.0 (Refactored)
"""

import sys
from pathlib import Path

# Add the Libs directory to the Python path
sys.path.append(str(Path(__file__).parent / 'Libs'))

from Libs.hr_automation_orchestrator import main

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
    """
    main()