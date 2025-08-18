"""
SkyNET I2A2 Libraries Package
Contains utility libraries for the SkyNET I2A2 project

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

from .email_library import EmailNotifier, send_process_completion_email

__all__ = ['EmailNotifier', 'send_process_completion_email']