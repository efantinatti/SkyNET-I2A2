#!/usr/bin/env python3
"""
SMTP Credential Diagnostic Tool
Helps diagnose SMTP authentication issues for SkyNET I2A2

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import smtplib
import ssl
import configparser
import os
import base64
from getpass import getpass

def load_current_config():
    """Load current configuration"""
    config = configparser.ConfigParser()
    config_path = 'Config/config.ini'
    
    if os.path.exists(config_path):
        config.read(config_path)
        return config
    else:
        print("❌ Config file not found!")
        return None

def test_credentials_manually():
    """Test SMTP credentials with manual input"""
    print("🔧 Manual SMTP Credential Test")
    print("=" * 40)
    
    # Get server details
    host = input("SMTP Host [smtp.titan.email]: ").strip() or "smtp.titan.email"
    port = int(input("SMTP Port [465]: ").strip() or "465")
    
    # Get credentials
    username = input("SMTP Username (email): ").strip()
    password = getpass("SMTP Password: ").strip()
    
    print(f"\n🧪 Testing connection to {host}:{port}")
    print(f"Username: {username}")
    print(f"Password length: {len(password)} characters")
    
    try:
        # Try SSL connection
        print("\nAttempting SSL connection...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(host, port, context=context)
        
        print("✅ SSL connection established")
        
        # Enable debug to see what's happening
        server.set_debuglevel(1)
        
        print("🔐 Attempting authentication...")
        server.login(username, password)
        
        print("✅ Authentication successful!")
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def show_current_config():
    """Show current configuration (hiding password)"""
    config = load_current_config()
    if not config:
        return
    
    print("📋 Current Configuration:")
    print("=" * 30)
    
    if 'email' in config:
        email_config = config['email']
        print(f"SMTP Host: {email_config.get('smtp_host', 'Not set')}")
        print(f"SMTP Port: {email_config.get('smtp_port', 'Not set')}")
        print(f"Encryption: {email_config.get('smtp_encryption', 'Not set')}")
        print(f"Sender Email: {email_config.get('sender_email', 'Not set')}")
        
        password = email_config.get('sender_password', '')
        if password:
            print(f"Password: {'*' * len(password)} ({len(password)} characters)")
        else:
            print("Password: Not set")
        
        print(f"Recipients: {email_config.get('recipient_emails', 'Not set')}")
    else:
        print("❌ No email configuration found")

def decode_error_message(error_msg):
    """Try to decode error messages"""
    print(f"\n🔍 Error Analysis:")
    print(f"Raw error: {error_msg}")
    
    # Try to find base64 encoded parts
    if 'UGFzc3dvcmQ6' in str(error_msg):
        decoded = base64.b64decode('UGFzc3dvcmQ6').decode('utf-8')
        print(f"Decoded part: '{decoded}'")
        print("This suggests the server is expecting a different password format.")

def main():
    """Main diagnostic function"""
    print("🩺 SkyNET I2A2 SMTP Diagnostic Tool")
    print("=" * 45)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. 📋 Show current configuration")
        print("2. 🧪 Test credentials manually")
        print("3. 🔍 Analyze last error")
        print("4. ❌ Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            show_current_config()
        elif choice == '2':
            if test_credentials_manually():
                print("\n🎉 Manual test successful! The credentials work.")
                print("The issue might be in the email library configuration.")
            else:
                print("\n❌ Manual test failed. Please check your credentials.")
        elif choice == '3':
            error = "UGFzc3dvcmQ6"
            decode_error_message(error)
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()