#!/usr/bin/env python3
"""
Gmail App Password Setup Helper
Helps users create and configure Gmail App Passwords for the SkyNET I2A2 email system

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import configparser
import os
from getpass import getpass

#!/usr/bin/env python3
"""
SMTP Email Setup Helper
Helps users configure SMTP settings for the SkyNET I2A2 email system

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import configparser
import os
from getpass import getpass

def show_smtp_providers():
    """Show common SMTP provider configurations"""
    print("🌐 Common SMTP Provider Settings")
    print("=" * 50)
    
    providers = {
        "Titan": {
            "host": "smtp.titan.email",
            "port": "465",
            "encryption": "SSL"
        },
        "Hostinger": {
            "host": "smtp.hostinger.com",
            "port": "465",
            "encryption": "SSL"
        },
        "Gmail": {
            "host": "smtp.gmail.com",
            "port": "587",
            "encryption": "TLS"
        },
        "Outlook": {
            "host": "smtp-mail.outlook.com",
            "port": "587",
            "encryption": "TLS"
        },
        "Yahoo": {
            "host": "smtp.mail.yahoo.com",
            "port": "587",
            "encryption": "TLS"
        },
        "Godaddy": {
            "host": "smtpout.secureserver.net",
            "port": "587",
            "encryption": "TLS"
        }
    }
    
    for provider, settings in providers.items():
        print(f"\n📧 {provider}:")
        print(f"  Host: {settings['host']}")
        print(f"  Port: {settings['port']}")
        print(f"  Encryption: {settings['encryption']}")

def configure_smtp_settings():
    """Interactive SMTP configuration"""
    print("\n� SMTP Configuration")
    print("-" * 30)
    
    config = configparser.ConfigParser()
    config_file = 'Config/config.ini'
    
    # Ensure Config directory exists
    if not os.path.exists('Config'):
        os.makedirs('Config')
    
    # Read existing config if it exists
    if os.path.exists(config_file):
        config.read(config_file)
    
    if 'email' not in config:
        config.add_section('email')
    
    # Get current settings
    current_host = config.get('email', 'smtp_host', fallback='smtp.hostinger.com')
    current_port = config.get('email', 'smtp_port', fallback='465')
    current_encryption = config.get('email', 'smtp_encryption', fallback='SSL')
    current_sender = config.get('email', 'sender_email', fallback='')
    current_recipients = config.get('email', 'recipient_emails', fallback='')
    
    print("📊 Current Configuration:")
    print(f"  Host: {current_host}")
    print(f"  Port: {current_port}")
    print(f"  Encryption: {current_encryption}")
    print(f"  Sender: {current_sender}")
    print(f"  Recipients: {current_recipients}")
    
    print("\n🔧 New Configuration:")
    
    # SMTP Server Settings
    new_host = input(f"SMTP Host [{current_host}]: ").strip()
    if new_host:
        config.set('email', 'smtp_host', new_host)
    elif current_host:
        config.set('email', 'smtp_host', current_host)
    
    new_port = input(f"SMTP Port [{current_port}]: ").strip()
    if new_port:
        config.set('email', 'smtp_port', new_port)
    elif current_port:
        config.set('email', 'smtp_port', current_port)
    
    new_encryption = input(f"Encryption (SSL/TLS) [{current_encryption}]: ").strip().upper()
    if new_encryption:
        config.set('email', 'smtp_encryption', new_encryption)
    elif current_encryption:
        config.set('email', 'smtp_encryption', current_encryption)
    
    # Email Settings
    new_sender = input(f"Sender email [{current_sender}]: ").strip()
    if new_sender:
        config.set('email', 'sender_email', new_sender)
    elif current_sender:
        config.set('email', 'sender_email', current_sender)
    else:
        print("❌ Sender email is required!")
        return False
    
    new_password = getpass("Sender email password (hidden input): ").strip()
    if new_password:
        config.set('email', 'sender_password', new_password)
    
    new_recipients = input(f"Recipient emails (comma-separated) [{current_recipients}]: ").strip()
    if new_recipients:
        config.set('email', 'recipient_emails', new_recipients)
    elif current_recipients:
        config.set('email', 'recipient_emails', current_recipients)
    else:
        print("❌ At least one recipient email is required!")
        return False
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        print("✅ SMTP configuration updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def reconfigure_email():
    """Reconfigure email settings with proper validation"""
    print("\n🔧 Email Reconfiguration")
    print("-" * 30)
    
    config = configparser.ConfigParser()
    config_file = 'Config/config.ini'
    
    # Read existing config
    if os.path.exists(config_file):
        config.read(config_file)
    
    if 'email' not in config:
        config.add_section('email')
    
    # Get current settings
    current_email = config.get('email', 'sender_email', fallback='')
    current_recipient = config.get('email', 'recipient_email', fallback='')
    
    print(f"Current sender email: {current_email}")
    
    # Confirm email or enter new one
    new_email = input(f"Enter Gmail address [{current_email}]: ").strip()
    if new_email:
        config.set('email', 'sender_email', new_email)
    elif current_email:
        new_email = current_email
    else:
        print("❌ Email address is required!")
        return False
    
    # Get new App Password
    print("\n🔑 Enter your NEW 16-character App Password:")
    print("(It should look like: abcdefghijklmnop - without spaces)")
    new_password = getpass("App Password: ").strip().replace(' ', '')
    
    if len(new_password) != 16:
        print(f"⚠️ Warning: App Password should be 16 characters, got {len(new_password)}")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    config.set('email', 'sender_password', new_password)
    
    # Confirm recipient
    new_recipient = input(f"Enter recipient email [{current_recipient}]: ").strip()
    if new_recipient:
        config.set('email', 'recipient_email', new_recipient)
    elif current_recipient:
        new_recipient = current_recipient
    else:
        print("❌ Recipient email is required!")
        return False
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        print("✅ Email configuration updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def test_smtp_configuration():
    """Test the SMTP configuration with detailed error reporting"""
    print("\n🧪 Testing SMTP Configuration")
    print("-" * 35)
    
    try:
        from Libs.email_library import EmailNotifier
        
        notifier = EmailNotifier()
        
        # Test connection first
        print("Step 1: Testing SMTP connection...")
        if notifier.test_connection():
            print("✅ SMTP connection successful!")
        else:
            print("❌ SMTP connection failed!")
            return False
        
        # Test sending email
        print("Step 2: Testing email sending...")
        success = notifier.send_completion_notification(
            filename="smtp_setup_test.txt",
            attach_file=False,
            additional_message="This is a test email from the SMTP setup helper. If you receive this, your configuration is working!"
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print("📧 Check your recipient inbox(es) for the test email.")
            return True
        else:
            print("❌ Failed to send test email!")
            return False
            
    except Exception as e:
        print(f"❌ Error during SMTP test: {e}")
        return False

def main():
    """Main function"""
    print("📧 SkyNET I2A2 SMTP Setup Helper")
    print("=" * 40)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. 🌐 View common SMTP provider settings")
        print("2. 🔧 Configure SMTP settings")
        print("3. 🧪 Test current SMTP configuration")
        print("4. ❌ Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            show_smtp_providers()
        elif choice == '2':
            if configure_smtp_settings():
                print("\n✅ Configuration updated! You can now test it (option 3).")
        elif choice == '3':
            test_smtp_configuration()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()