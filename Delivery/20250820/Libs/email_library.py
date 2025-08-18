"""
Email Library for SkyNET I2A2 Project
Uses standard SMTP for reliable email integration with custom SMTP servers

Author: SkyNET I2A2 AI Agent
Date: 2025-08-18
"""

import smtplib
import ssl
import os
import configparser
from datetime import datetime
from typing import Optional, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Email notification class using standard SMTP.
    Sends automated emails with file attachments when processes are completed.
    """
    
    def __init__(self, config_file: str = '../Config/config.ini'):
        """
        Initialize the EmailNotifier with configuration from config.ini
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config = self._load_config(config_file)
        self.smtp_server = None
        
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """
        Load email configuration from INI file
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            configparser.ConfigParser: Configuration object
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        config.read(config_path)
        
        # Validate required email configuration
        if 'email' not in config:
            raise ValueError("Email configuration section not found in config.ini")
        
        required_keys = ['smtp_host', 'smtp_port', 'sender_email', 'sender_password', 'recipient_emails']
        for key in required_keys:
            if key not in config['email']:
                raise ValueError(f"Required email configuration '{key}' not found in config.ini")
        
        # sender_name is optional - if not provided, will use sender_email
        if 'sender_name' not in config['email']:
            logger.info("sender_name not configured, will use sender_email as display name")
        
        return config
    
    def _connect_smtp(self):
        """
        Establish SMTP connection using standard library with multiple fallback methods
        """
        smtp_host = self.config['email']['smtp_host']
        smtp_port = int(self.config['email']['smtp_port'])
        smtp_encryption = self.config['email'].get('smtp_encryption', 'SSL').upper()
        sender_email = self.config['email']['sender_email']
        sender_password = self.config['email']['sender_password']
        
        # Define connection methods to try
        connection_methods = []
        
        if smtp_encryption == 'SSL':
            connection_methods = [
                {'port': 465, 'method': 'SSL', 'description': 'SSL on port 465'},
                {'port': 587, 'method': 'TLS', 'description': 'TLS on port 587 (fallback)'},
                {'port': 25, 'method': 'TLS', 'description': 'TLS on port 25 (fallback)'}
            ]
        elif smtp_encryption in ['TLS', 'STARTTLS']:
            connection_methods = [
                {'port': 587, 'method': 'TLS', 'description': 'TLS on port 587'},
                {'port': 465, 'method': 'SSL', 'description': 'SSL on port 465 (fallback)'},
                {'port': 25, 'method': 'TLS', 'description': 'TLS on port 25 (fallback)'}
            ]
        else:
            connection_methods = [
                {'port': smtp_port, 'method': 'PLAIN', 'description': f'Plain SMTP on port {smtp_port}'}
            ]
        
        last_error = None
        
        for method in connection_methods:
            try:
                port = method['port']
                conn_method = method['method']
                description = method['description']
                
                logger.info(f"Attempting connection: {smtp_host}:{port} using {description}")
                
                # Create SMTP connection based on method
                if conn_method == 'SSL':
                    context = ssl.create_default_context()
                    self.smtp_server = smtplib.SMTP_SSL(smtp_host, port, context=context)
                elif conn_method == 'TLS':
                    self.smtp_server = smtplib.SMTP(smtp_host, port)
                    self.smtp_server.starttls(context=ssl.create_default_context())
                else:
                    # Plain connection
                    self.smtp_server = smtplib.SMTP(smtp_host, port)
                
                # Enable debug mode for troubleshooting
                # self.smtp_server.set_debuglevel(1)
                
                # Authenticate
                logger.info(f"Authenticating with user: {sender_email}")
                self.smtp_server.login(sender_email, sender_password)
                logger.info(f"SMTP connection successful using {description}")
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt failed with {description}: {e}")
                if self.smtp_server:
                    try:
                        self.smtp_server.quit()
                    except:
                        pass
                    self.smtp_server = None
                continue
        
        # If all methods failed, raise the last error with helpful message
        error_msg = f"All SMTP connection methods failed for {smtp_host}. "
        error_msg += f"Last error: {last_error}. "
        error_msg += "Please check your credentials and server settings."
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    def _disconnect_smtp(self):
        """
        Close SMTP connection
        """
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                logger.info("SMTP connection closed")
            except:
                pass
            self.smtp_server = None
    
    def _parse_recipients(self, recipient_override: Optional[str] = None) -> List[str]:
        """
        Parse recipient emails from config or override
        
        Args:
            recipient_override (str, optional): Override recipient email(s)
            
        Returns:
            List[str]: List of recipient email addresses
        """
        if recipient_override:
            recipients = recipient_override
        else:
            recipients = self.config['email']['recipient_emails']
        
        # Split by comma and clean up
        recipient_list = [email.strip() for email in recipients.split(',')]
        recipient_list = [email for email in recipient_list if email]  # Remove empty strings
        
        return recipient_list
    
    def send_completion_notification(self, 
                                   filename: str, 
                                   attach_file: bool = True,
                                   recipient_emails: Optional[str] = None,
                                   additional_message: str = "") -> bool:
        """
        Send email notification when a process is completed
        
        Args:
            filename (str): Name of the generated file
            attach_file (bool): Whether to attach the file to the email
            recipient_emails (str, optional): Override recipient email(s) (comma-separated)
            additional_message (str): Additional message to include in the body
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate current date in YYYYMMDD format
            current_date = datetime.now().strftime("%Y%m%d")
            
            # Prepare email components
            subject = f"Saída gerada com sucesso {current_date}"
            
            body = f"Arquivo: {filename}"
            if additional_message:
                body += f"\n\n{additional_message}"
            
            # Parse recipients
            recipients = self._parse_recipients(recipient_emails)
            sender_email = self.config['email']['sender_email']
            sender_name = self.config['email'].get('sender_name', sender_email)
            
            # Format sender with friendly name
            if sender_name and sender_name != sender_email:
                formatted_sender = f"{sender_name} <{sender_email}>"
            else:
                formatted_sender = sender_email
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formatted_sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Add file attachment if requested and file exists
            if attach_file and os.path.exists(filename):
                try:
                    with open(filename, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(filename)}'
                    )
                    msg.attach(part)
                    logger.info(f"File '{filename}' attached to email")
                except Exception as e:
                    logger.warning(f"Failed to attach file '{filename}': {e}")
            elif attach_file:
                logger.warning(f"File '{filename}' not found, sending email without attachment")
            
            # Establish connection and send email
            self._connect_smtp()
            
            text = msg.as_string()
            self.smtp_server.sendmail(sender_email, recipients, text)
            
            logger.info(f"Email sent successfully to {recipients}")
            logger.info(f"Subject: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
            
        finally:
            self._disconnect_smtp()
    
    def send_custom_email(self, 
                         subject: str, 
                         body: str, 
                         recipient_emails: Optional[str] = None,
                         attachments: Optional[List[str]] = None) -> bool:
        """
        Send a custom email with specified content
        
        Args:
            subject (str): Email subject
            body (str): Email body content
            recipient_emails (str, optional): Override recipient email(s) (comma-separated)
            attachments (List[str], optional): List of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Parse recipients
            recipients = self._parse_recipients(recipient_emails)
            sender_email = self.config['email']['sender_email']
            sender_name = self.config['email'].get('sender_name', sender_email)
            
            # Format sender with friendly name
            if sender_name and sender_name != sender_email:
                formatted_sender = f"{sender_name} <{sender_email}>"
            else:
                formatted_sender = sender_email
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formatted_sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "rb") as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                            
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
                            logger.info(f"File '{file_path}' attached to email")
                        except Exception as e:
                            logger.warning(f"Failed to attach file '{file_path}': {e}")
                    else:
                        logger.warning(f"Attachment '{file_path}' not found, skipping")
            
            # Establish connection and send email
            self._connect_smtp()
            
            text = msg.as_string()
            self.smtp_server.sendmail(sender_email, recipients, text)
            
            logger.info(f"Custom email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return False
            
        finally:
            self._disconnect_smtp()
    
    def test_connection(self) -> bool:
        """
        Test the email connection and configuration
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            self._connect_smtp()
            logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
            
        finally:
            self._disconnect_smtp()


def send_process_completion_email(filename: str, attach_file: bool = True, recipient_emails: Optional[str] = None) -> bool:
    """
    Convenience function to send process completion email
    
    Args:
        filename (str): Name of the generated file
        attach_file (bool): Whether to attach the file
        recipient_emails (str, optional): Override recipient email(s) (comma-separated)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        notifier = EmailNotifier()
        return notifier.send_completion_notification(filename, attach_file, recipient_emails)
    except Exception as e:
        logger.error(f"Failed to send process completion email: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test the email functionality
    notifier = EmailNotifier()
    
    # Test connection
    if notifier.test_connection():
        print("✅ Email connection test successful")
        
        # Send a test email
        test_filename = "test_file.txt"
        success = notifier.send_completion_notification(
            filename=test_filename,
            attach_file=False,  # Don't attach since it's just a test
            additional_message="This is a test email from the SkyNET I2A2 email library using SMTP."
        )
        
        if success:
            print("✅ Test email sent successfully")
        else:
            print("❌ Failed to send test email")
    else:
        print("❌ Email connection test failed")