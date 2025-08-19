# SkyNET I2A2 HR Automation System

![SkyNET Logo](../../docs/Logo/SkyNET_Logo.png)

**Version 2.1** - August 2025 Delivery  
**File Integrity Monitoring Integration**

## 🚀 Overview

The SkyNET I2A2 HR Automation System is a sophisticated, enterprise-grade solution for processing HR data and benefit calculations. This system has been completely refactored following Clean Code principles and SOLID design patterns, providing a robust, maintainable, and extensible architecture.

### 🆕 **Latest Features (v2.1)**
- **🔒 File Integrity Monitoring**: MD5-based change detection for efficient processing
- **⚡ Smart Processing**: Only runs when input files have actually changed
- **🛠️ Enhanced CLI**: Comprehensive command-line interface for file management
- **📊 Detailed Status Reporting**: Real-time monitoring of file changes and system health

## 📋 Key Features

### 🏗️ **Clean Architecture**
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Design Patterns**: Strategy, Factory, Facade, Template Method, Adapter, Service patterns
- **Modular Design**: 8 specialized services with clear separation of concerns
- **Enterprise Standards**: Production-ready code with comprehensive error handling

### 📁 **File Processing**
- **11 Excel Input Files**: Comprehensive employee data processing
- **Automatic Validation**: LLM-powered data validation with configurable rules
- **Error Handling**: Robust file loading with detailed error reporting
- **Output Generation**: Professional CSV output with email notifications

### 🔒 **File Integrity System**
- **MD5 Checksums**: Automatic file change detection
- **Smart Processing**: Skip automation when no files have changed
- **Checksum Management**: Automatic updates and maintenance
- **Force Options**: Override integrity checks when needed

### 📧 **Email Integration**
- **Automatic Notifications**: Email alerts upon process completion
- **File Attachments**: Attach generated reports to emails
- **Multiple Recipients**: Configure multiple email addresses
- **SMTP Support**: Robust SMTP with fallback mechanisms

## 🏁 Quick Start

### 1. **Initialize File Monitoring** (First Time)
```bash
python hr_automation_main.py --init
```

### 2. **Run Automation** (Normal Operation)
```bash
# Smart run - only processes if files changed
python hr_automation_main.py

# Force run - bypass file integrity check
python hr_automation_main.py --force
```

### 3. **Check Status**
```bash
# Check file integrity
python hr_automation_main.py --check

# System status
python hr_automation_main.py --status
```

## 📂 Project Structure

```
SkyNET-I2A2/Delivery/20250820/
├── 📄 hr_automation_main.py           # Modern CLI entry point
├── 📄 Desafio-4-RH.py               # Legacy entry point (backward compatible)
├── 📁 Libs/                         # Core system libraries
│   ├── config_manager.py            # Configuration management
│   ├── data_models.py               # Domain models and DTOs
│   ├── validation_service.py        # LLM-powered validation
│   ├── data_loading_service.py      # File loading with Factory pattern
│   ├── business_logic_service.py    # HR business rules and calculations
│   ├── output_service.py           # Output generation
│   ├── email_library.py            # Email notification service
│   ├── file_integrity_service.py   # 🆕 MD5-based file monitoring
│   └── hr_automation_orchestrator.py # Main orchestrator (Facade pattern)
├── 📁 Config/                       # Configuration files
│   └── config.ini                  # System configuration
├── 📁 Import/                       # Input Excel files
│   └── 📄 All required Excel files  # 11 HR data files
├── 📁 md5/                         # 🆕 MD5 checksum storage
│   └── 📄 *.xlsx.md5               # Individual file checksums
├── 📁 Output/                      # Generated reports
│   └── 📄 VR_MENSAL_05_2025_FINAL.csv
└── 📄 Documentation Files          # Comprehensive docs
```

## 🔧 Command Line Interface

### **Basic Operations**
```bash
# Normal run with integrity check
python hr_automation_main.py

# Force run (skip integrity check)  
python hr_automation_main.py --force

# Check file integrity only
python hr_automation_main.py --check

# Show system status
python hr_automation_main.py --status
```

### **File Management**
```bash
# Initialize file monitoring (first time)
python hr_automation_main.py --init

# Force update all checksums
python hr_automation_main.py --update-checksums

# Clean orphaned checksum files
python hr_automation_main.py --clean
```

### **Help and Documentation**
```bash
# Show all available options
python hr_automation_main.py --help
```

## 📊 System Workflow

### 🔒 **Integrity Check Phase**
1. **File Scanning**: Check all 11 input files for changes
2. **MD5 Comparison**: Compare current checksums with stored values
3. **Change Detection**: Identify new, changed, and missing files
4. **Smart Decision**: Proceed only if changes detected (unless forced)

### 📂 **Data Processing Phase**
1. **File Loading**: Load and validate all Excel files
2. **Data Consolidation**: Merge employee data from multiple sources
3. **Business Logic**: Apply HR rules and benefit calculations
4. **Output Generation**: Create formatted CSV report

### 🔄 **Finalization Phase**
1. **Checksum Update**: Update MD5 hashes for changed files
2. **Email Notification**: Send completion notification with attachments
3. **Status Reporting**: Provide detailed execution summary

## 📈 Performance & Efficiency

### **🔒 File Integrity Benefits**
- **Reduced Processing**: Skip automation when no files have changed
- **Resource Optimization**: Avoid unnecessary CPU and I/O operations
- **Clear Feedback**: Know immediately if processing is needed
- **Audit Trail**: Track all file changes with timestamps

### **⚡ Processing Metrics**
- **File Loading**: ~11 Excel files processed in seconds
- **Data Processing**: 1,770+ employee records handled efficiently
- **Output Generation**: Professional CSV with 10 data columns
- **Email Delivery**: Multi-recipient notifications with attachments

## 🛠️ Configuration

### **Configuration File** (`Config/config.ini`)
```ini
[gemini]
api_key = your_gemini_api_key
model = gemini-pro

[email]
smtp_host = smtp.yourdomain.com
smtp_port = 465
sender_email = mailer@yourdomain.com
sender_password = your_password
recipient_emails = user1@domain.com,user2@domain.com

[validation_rules]
max_vacation_days = 45
required_fields = Nome,Matrícula,Setor
```

## 📚 Documentation

- **📄 README_File_Integrity.md**: Complete file integrity system documentation
- **📄 README_Email_Integration.md**: Email system configuration and usage
- **📄 Import/README.md**: Input file specifications and requirements
- **📄 Output/README.md**: Output format and structure documentation
- **📄 md5/README.md**: MD5 checksum directory and file integrity details
- **📄 REFACTORING_DOCUMENTATION.md**: Detailed refactoring process and patterns

## 🔄 Migration Guide

### **From v2.0 to v2.1**
1. **Initialize Monitoring**: Run `python hr_automation_main.py --init`
2. **Update Workflow**: Use new CLI commands for better control
3. **Monitor Changes**: Benefit from automatic file change detection

### **From Legacy System**
- **Backward Compatibility**: Original `Desafio-4-RH.py` still works
- **Gradual Migration**: Adopt new features at your own pace
- **Side-by-Side**: Both systems can coexist during transition

## 🎯 Use Cases

### **Daily Operations**
```bash
# Check if processing is needed
python hr_automation_main.py --check

# Run automation (only if files changed)
python hr_automation_main.py
```

### **Data Updates**
```bash
# After updating Excel files
python hr_automation_main.py  # Auto-detects changes and processes

# Force processing regardless of changes
python hr_automation_main.py --force
```

### **System Maintenance**
```bash
# System health check
python hr_automation_main.py --status

# Clean up orphaned checksums
python hr_automation_main.py --clean

# Reset all checksums
python hr_automation_main.py --update-checksums
```

## 🏆 Technical Excellence

### **Clean Code Implementation**
- **SOLID Principles**: Every class follows single responsibility
- **Design Patterns**: 6+ enterprise patterns implemented correctly
- **Error Handling**: Comprehensive exception management
- **Logging**: Detailed operational logging throughout

### **Testing & Validation**
- **Backward Compatibility**: 100% compatibility with legacy system
- **Data Integrity**: LLM-powered validation ensures data quality
- **File Monitoring**: Robust MD5-based change detection
- **Email Delivery**: Multi-fallback SMTP with detailed error reporting

### **Performance Optimization**
- **Smart Processing**: Avoid unnecessary work when files unchanged
- **Efficient I/O**: Chunk-based file reading for large files
- **Memory Management**: Proper DataFrame handling and cleanup
- **Resource Usage**: Minimal overhead for integrity monitoring

## 👥 Team

**SkyNET I2A2 Development Team**
- **Ernani Fantinatti** (Group Leader) - System Architecture & Implementation
- **AI Agent Integration** - Code Refactoring & Pattern Implementation

---

## 📞 Support

For technical support or questions about the system:
1. **Check Documentation**: Review relevant README files
2. **System Status**: Run `python hr_automation_main.py --status`
3. **Error Logs**: Check console output for detailed error information
4. **Force Run**: Use `--force` flag if needed to bypass integrity checks

---

*SkyNET I2A2 HR Automation System v2.1 - Engineered for Enterprise Excellence with Intelligent File Monitoring*