# SkyNET I2A2 Email Integration

This project includes an email notification system that automatically sends emails when the HR process (`Desafio-4-RH.py`) completes successfully.

## Project Structure

```
SkyNET-I2A2/Delivery/20250820/
├── Libs/
│   ├── __init__.py
│   └── email_library.py          # Email notification library
├── Config/
│   └── config.ini                # Configuration file
├── Challenge/                    # Challenge documentation
├── Desafio-4-RH.py              # Main HR process script
├── setup.py                     # Setup and configuration script
├── validate_structure.py        # Project validation script
├── requirements.txt             # Python dependencies
└── README_Email_Integration.md  # This documentation
```

## Features

- 📧 Automatic email notifications when processes complete
- 📎 File attachment support
- 🔒 Secure Gmail integration using App Passwords
- ⚙️ Configurable email settings via `config.ini`
- 🧪 Built-in testing functionality

## Quick Setup

1. **Validate project structure:**
   ```bash
   python validate_structure.py
   ```

2. **Install dependencies and configure email settings:**
   ```bash
   python setup.py
   ```

3. **Run the HR process:**
   ```bash
   python Desafio-4-RH.py
   ```

## Manual Setup

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

Edit the `Config/config.ini` file and add your SMTP configuration:

```ini
[email]
smtp_host = smtp.hostinger.com
smtp_port = 465
smtp_encryption = SSL
sender_email = your_email@domain.com
sender_password = your_password
recipient_emails = recipient1@domain.com,recipient2@domain.com
```

**Hostinger Email Settings:**
- SMTP Host: `smtp.hostinger.com`
- Port: `465`
- Encryption: `SSL`
- Authentication: Required
- Username: Your full email address

**Important:** For Gmail, you must use an App Password instead of your regular password:
1. Go to your Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use this 16-character password in the configuration

### 3. Test Email Configuration

```python
from Libs.email_library import EmailNotifier

notifier = EmailNotifier()
if notifier.test_connection():
    print("Email configuration is working!")
```

## Usage

### Automatic Integration

The email notification is automatically integrated into `Desafio-4-RH.py`. When the process completes successfully, it will:

1. Generate the output file (`VR_MENSAL_05_2025_FINAL.csv`)
2. Send an email with subject: "Saída gerada com sucesso YYYYMMDD"
3. Include the filename in the email body
4. Attach the generated file to the email

### Manual Email Sending

You can also use the email library independently:

```python
from Libs.email_library import send_process_completion_email, EmailNotifier

# Simple notification
send_process_completion_email("my_file.csv", attach_file=True)

# Custom email
notifier = EmailNotifier()
notifier.send_custom_email(
    subject="Custom Subject",
    body="Custom message",
    attachments=["file1.csv", "file2.xlsx"]
)
```

## Email Library API

### `EmailNotifier` Class

#### Methods:

- `__init__(config_file='config.ini')` - Initialize with configuration file
- `send_completion_notification(filename, attach_file=True, recipient_email=None, additional_message="")` - Send process completion email
- `send_custom_email(subject, body, recipient_email=None, attachments=None)` - Send custom email
- `test_connection()` - Test email configuration

#### Convenience Functions:

- `send_process_completion_email(filename, attach_file=True)` - Quick process completion notification

## Configuration File Structure

```ini
[gemini]
api_key = <your_gemini_api_key>

[email]
sender_email = your_email@gmail.com
sender_password = your_app_password
recipient_email = recipient@gmail.com

[validation_rules]
max_vacation_days = 30
required_fields = MATRICULA,NOME,SINDICATO
date_format = %Y-%m-%d
```

## Security Notes

- Never commit your `config.ini` file with real credentials to version control
- Use Gmail App Passwords instead of regular passwords
- Consider using environment variables for sensitive information in production
- The email library includes proper error handling and logging

## Troubleshooting

### Common Issues:

1. **"Authentication failed" with Hostinger Email**
   - Ensure you're using the correct email address and password
   - Verify that the email account exists and is active
   - Run the diagnostic tool: `python smtp_diagnostic.py`

2. **"Connection failed" errors**
   - Check firewall settings (port 465 for SSL)
   - Verify internet connection
   - Try running: `python smtp_setup_helper.py` for alternative configurations

3. **"Import errors"**
   - Run: `pip install -r requirements.txt`

4. **"Configuration file not found"**
   - Ensure `Config/config.ini` exists in the same directory as the script

5. **Multiple recipients not working**
   - Ensure recipient emails are comma-separated without spaces
   - Example: `email1@domain.com,email2@domain.com`

### Testing:

Run the validation script to test your project structure:
```bash
python validate_structure.py
```

Run the setup script to test your configuration:
```bash
python setup.py
```

If you have SMTP authentication issues, use the diagnostic tool:
```bash
python smtp_diagnostic.py
```

If you need to configure different SMTP providers:
```bash
python smtp_setup_helper.py
```

## Files Included

- `Libs/email_library.py` - Main email notification library (SMTP-based)
- `Libs/__init__.py` - Package initialization file
- `Config/config.ini` - Configuration file (update with your SMTP settings)
- `Desafio-4-RH.py` - Updated HR process with email integration
- `setup.py` - Setup and configuration script
- `smtp_setup_helper.py` - SMTP provider setup helper
- `smtp_diagnostic.py` - SMTP troubleshooting diagnostic tool
- `validate_structure.py` - Project structure validation script
- `requirements.txt` - Required Python packages
- `README_Email_Integration.md` - This documentation

## Dependencies

- `yagmail` - Gmail SMTP interface
- `pandas` - Data processing
- `numpy` - Numerical operations
- `requests` - HTTP requests
- `configparser` - Configuration file parsing
- `openpyxl` - Excel file handling

## Example Output

When the HR process completes, you'll receive an email like:

```
Subject: Saída gerada com sucesso 20250818

Body: 
Arquivo: VR_MENSAL_05_2025_FINAL.csv

Attached: VR_MENSAL_05_2025_FINAL.csv
```

## Support

For issues or questions about the email integration, check the logs in the console output or enable debug logging in the email library.