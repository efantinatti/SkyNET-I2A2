# SkyNET I2A2 - Project Structure

## Overview
This document describes the organized project structure for the SkyNET I2A2 HR automation system.

## Folder Structure

```
SkyNET-I2A2/Delivery/20250820/
├── Import/                          # Input Excel files
│   ├── ADMISSÃO ABRIL.xlsx          # April admissions data
│   ├── AFASTAMENTOS.xlsx            # Leave/absence data
│   ├── APRENDIZ.xlsx                # Apprentice data
│   ├── ATIVOS.xlsx                  # Active employees data
│   ├── Base dias uteis.xlsx         # Working days base
│   ├── Base sindicato x valor.xlsx  # Union vs value mapping
│   ├── DESLIGADOS.xlsx              # Terminated employees
│   ├── ESTÁGIO.xlsx                 # Internship data
│   ├── EXTERIOR.xlsx                # Foreign employees
│   ├── FÉRIAS.xlsx                  # Vacation data
│   └── VR MENSAL 05.2025.xlsx       # VR monthly template
├── Output/                          # Generated CSV files
│   └── VR_MENSAL_05_2025_FINAL.csv  # Final output file
├── Config/                          # Configuration files
│   └── config.ini                   # SMTP and app settings
├── Libs/                           # Python libraries
│   ├── __init__.py                 # Package initializer
│   └── email_library.py            # Email notification system
├── Challenge/                       # Project documentation
│   └── Desafio 4 - Descrição.pdf   # Challenge description
├── Desafio-4-RH.py                 # Main HR automation script
├── requirements.txt                 # Python dependencies
├── setup.py                        # Package setup
├── smtp_diagnostic.py              # SMTP troubleshooting tool
├── smtp_setup_helper.py            # SMTP configuration helper
├── validate_structure.py           # Structure validation tool
├── CONFIGURATION_SUMMARY.md        # Configuration summary
├── README_Email_Integration.md     # Email integration guide
└── PROJECT_STRUCTURE.md           # This file
```

## Key Components

### Input Files (Import/ folder)
- **Excel files**: All HR data sources are now organized in the `Import/` folder
- **Data validation**: Each file is validated using LLM-powered checks
- **Format**: Standard Excel (.xlsx) format

### Output Files (Output/ folder)
- **CSV generation**: Final processed data is saved to `Output/` folder
- **Format**: CSV with semicolon separator and comma decimal
- **Naming**: `VR_MENSAL_05_2025_FINAL.csv`

### Configuration (Config/ folder)
- **SMTP settings**: Email server configuration for Hostinger
- **Application settings**: General application parameters
- **Security**: Sensitive data stored in configuration files

### Libraries (Libs/ folder)
- **Email system**: Custom SMTP-based email notification library
- **Modularity**: Reusable components for the automation system

## Usage

1. **Place input files**: Copy all Excel files to the `Import/` folder
2. **Run automation**: Execute `python Desafio-4-RH.py`
3. **Check output**: Processed CSV will be generated in `Output/` folder
4. **Email notification**: Automatic email sent with the file attached

## Features

- ✅ **Organized structure**: Clear separation of input, output, and configuration
- ✅ **Email integration**: Professional email notifications with friendly sender name "Skynet-I2A2"
- ✅ **Data validation**: LLM-powered validation of input data
- ✅ **Error handling**: Comprehensive error handling and logging
- ✅ **SMTP reliability**: Robust SMTP configuration with fallback methods

## Email Notifications

The system automatically sends email notifications when processing completes:
- **Recipients**: contatosexport021@gmail.com, ernanif@fantinatti.com, fabiorhein@gmail.com
- **Subject**: "Saída gerada com sucesso YYYYMMDD"
- **Body**: Includes filename and completion message
- **Attachment**: Generated CSV file
- **Sender**: "Skynet-I2A2 <mailer@skynet.fantinatti.net>"

## Last Updated
August 18, 2025 - Project structure reorganization completed