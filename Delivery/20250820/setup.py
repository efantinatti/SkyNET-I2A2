#!/usr/bin/env python3
"""
Setup script for SkyNET I2A2 Email Integration
Installs dependencies and helps configure email settings

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import subprocess
import sys
import os
import configparser
from getpass import getpass

def install_dependencies():
    """Install required Python packages"""
    print("🔧 Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def configure_email_settings():
    """Interactive configuration of email settings"""
    print("\n📧 Configuring SMTP email settings...")
    print("Default configuration: Hostinger SMTP")
    
    config = configparser.ConfigParser()
    config_file = 'Config/config.ini'
    
    # Ensure Config directory exists
    if not os.path.exists('Config'):
        os.makedirs('Config')
    
    # Read existing config if it exists
    if os.path.exists(config_file):
        config.read(config_file)
    
    # Ensure email section exists
    if 'email' not in config:
        config.add_section('email')
    
    # SMTP Configuration
    print("\n🔧 SMTP Server Configuration:")
    smtp_host = input("SMTP Host [smtp.hostinger.com]: ").strip() or "smtp.hostinger.com"
    smtp_port = input("SMTP Port [465]: ").strip() or "465"
    smtp_encryption = input("Encryption (SSL/TLS) [SSL]: ").strip().upper() or "SSL"
    
    config.set('email', 'smtp_host', smtp_host)
    config.set('email', 'smtp_port', smtp_port)
    config.set('email', 'smtp_encryption', smtp_encryption)
    
    # Email credentials
    print("\n📧 Email Configuration:")
    sender_email = input("Sender email address: ").strip()
    if sender_email:
        config.set('email', 'sender_email', sender_email)
    
    sender_password = getpass("Sender email password (hidden input): ").strip()
    if sender_password:
        config.set('email', 'sender_password', sender_password)
    
    recipient_emails = input("Recipient email addresses (comma-separated): ").strip()
    if recipient_emails:
        config.set('email', 'recipient_emails', recipient_emails)
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        print("✅ SMTP email configuration saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to save email configuration: {e}")
        return False

def test_email_setup():
    """Test the email configuration"""
    print("\n🧪 Testing email configuration...")
    try:
        from Libs.email_library import EmailNotifier
        
        notifier = EmailNotifier()
        if notifier.test_connection():
            print("✅ Email configuration test successful!")
            
            # Ask if user wants to send a test email
            send_test = input("Would you like to send a test email? (y/n): ").strip().lower()
            if send_test == 'y':
                success = notifier.send_completion_notification(
                    filename="setup_test.txt",
                    attach_file=False,
                    additional_message="This is a test email from the SkyNET I2A2 setup process."
                )
                if success:
                    print("✅ Test email sent successfully!")
                else:
                    print("❌ Failed to send test email")
            return True
        else:
            print("❌ Email configuration test failed")
            return False
    except Exception as e:
        print(f"❌ Error testing email setup: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 SkyNET I2A2 Email Integration Setup")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("Setup failed at dependency installation step.")
        return
    
    # Step 2: Configure email settings
    if not configure_email_settings():
        print("Setup failed at email configuration step.")
        return
    
    # Step 3: Test email setup
    if test_email_setup():
        print("\n🎉 Setup completed successfully!")
        print("\nYour SkyNET I2A2 system is now configured to send email notifications.")
        print("The Desafio-4-RH.py script will automatically send emails when processing is complete.")
    else:
        print("\n⚠️ Setup completed with email test issues.")
        print("Please check your email configuration in config.ini")
    
    print("\n📝 Next steps:")
    print("1. Ensure all required data files are in the same directory")
    print("2. Run: python Desafio-4-RH.py")
    print("3. Check your email for completion notifications")

if __name__ == "__main__":
    main()