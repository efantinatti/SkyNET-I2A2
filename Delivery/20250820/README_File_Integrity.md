# File Integrity Monitoring System

The SkyNET I2A2 HR Automation System now includes a comprehensive file integrity monitoring system using MD5 checksums. This feature ensures that the automation only runs when input files have actually changed, improving efficiency and avoiding unnecessary processing.

## Features

### 🔒 **Automatic Change Detection**
- Monitors all 11 input Excel files in the `Import/` directory
- Uses MD5 checksums to detect any file modifications
- Stores checksums in dedicated `.md5` files within `md5/` directory (at project root level)

### 📊 **Smart Processing Logic**
- **Default Behavior**: Only runs automation when files have changed or are new
- **Force Mode**: Bypass integrity check and run regardless of file status
- **Checksum Updates**: Automatically updates checksums after successful processing
- **Documentation**: Complete documentation available in `md5/README.md`

### 🛠️ **Command Line Interface**

#### Basic Operations
```bash
# Normal run (with integrity check)
python hr_automation_main.py

# Force run (skip integrity check)
python hr_automation_main.py --force

# Check file integrity only
python hr_automation_main.py --check

# Show system status
python hr_automation_main.py --status
```

#### Management Operations
```bash
# Initialize file monitoring (first time setup)
python hr_automation_main.py --init

# Force update all checksums
python hr_automation_main.py --update-checksums

# Clean orphaned checksum files
python hr_automation_main.py --clean
```

## File Structure

```
Import/
├── ATIVOS.xlsx
├── ADMISSÃO ABRIL.xlsx
├── AFASTAMENTOS.xlsx
├── APRENDIZ.xlsx
├── Base dias uteis.xlsx
├── Base sindicato x valor.xlsx
├── DESLIGADOS.xlsx
├── ESTÁGIO.xlsx
├── EXTERIOR.xlsx
├── FÉRIAS.xlsx
└── VR MENSAL 05.2025.xlsx

md5/
├── ATIVOS.xlsx.md5
├── ADMISSÃO ABRIL.xlsx.md5
├── AFASTAMENTOS.xlsx.md5
├── APRENDIZ.xlsx.md5
├── Base dias uteis.xlsx.md5
├── Base sindicato x valor.xlsx.md5
├── DESLIGADOS.xlsx.md5
├── ESTÁGIO.xlsx.md5
├── EXTERIOR.xlsx.md5
├── FÉRIAS.xlsx.md5
└── VR MENSAL 05.2025.xlsx.md5
```

## Workflow Examples

### 🚀 **First Time Setup**
```bash
# 1. Initialize monitoring
python hr_automation_main.py --init

# 2. Check status
python hr_automation_main.py --status

# 3. Run automation normally
python hr_automation_main.py
```

### 🔄 **Regular Operations**
```bash
# Normal run - will only process if files changed
python hr_automation_main.py
```

**Output when no changes:**
```
🔒 INTEGRITY CHECK: Checking for file changes...
✅ No file changes detected. Automation not needed.
📊 File Status Summary:
   • Unchanged files: 11
   • Missing files: 0
💡 To force execution, use force_run=True parameter
```

**Output when changes detected:**
```
🔒 INTEGRITY CHECK: Checking for file changes...
📈 File changes detected:
   • Changed files: 1
     - ATIVOS.xlsx
   • Unchanged files: 10
🔄 Proceeding with automation due to file changes...
```

### 🛠️ **Maintenance Operations**
```bash
# Check what files have changed
python hr_automation_main.py --check

# Force run regardless of file status
python hr_automation_main.py --force

# Clean up orphaned checksum files
python hr_automation_main.py --clean
```

## Technical Implementation

### 🔧 **FileIntegrityService Class**
Located in `Libs/file_integrity_service.py`, this service provides:

- **MD5 Calculation**: Efficient chunk-based MD5 calculation for large files
- **Change Detection**: Compares current file hashes with stored checksums
- **Storage Management**: Manages `.md5` files in dedicated directory
- **Error Handling**: Robust error handling for file I/O operations

### 🏗️ **Integration Points**
- **HRAutomationOrchestrator**: Main integration point for file integrity checks
- **Command Line Interface**: Extended `hr_automation_main.py` with integrity commands
- **Configuration**: No additional configuration required - works out of the box

### 📋 **Monitored Files**
The system monitors these 11 critical input files:
1. `ATIVOS.xlsx` - Active employees
2. `Base dias uteis.xlsx` - Working days
3. `Base sindicato x valor.xlsx` - Union values
4. `DESLIGADOS.xlsx` - Terminated employees
5. `ESTÁGIO.xlsx` - Interns
6. `EXTERIOR.xlsx` - Foreign employees
7. `FÉRIAS.xlsx` - Vacations
8. `ADMISSÃO ABRIL.xlsx` - April admissions
9. `AFASTAMENTOS.xlsx` - Leave of absence
10. `APRENDIZ.xlsx` - Apprentices
11. `VR MENSAL 05.2025.xlsx` - Monthly VR template

## Benefits

### ⚡ **Performance**
- **Reduced Processing Time**: Skip automation when no files have changed
- **Efficient Checksums**: Fast MD5 calculation with chunk-based reading
- **Smart Updates**: Only update checksums for files that actually changed

### 🔒 **Reliability**
- **Data Integrity**: Ensure processing only occurs when data has actually changed
- **Error Prevention**: Avoid processing stale or corrupted data
- **Audit Trail**: Clear logging of all file changes and checksum updates

### 🎯 **User Experience**
- **Clear Feedback**: Detailed status information about file changes
- **Flexible Control**: Multiple command-line options for different scenarios
- **Maintenance Tools**: Built-in tools for managing checksums and cleanup

## Troubleshooting

### 🔍 **Common Issues**

**Missing MD5 Files:**
```bash
# Initialize monitoring to create missing checksums
python hr_automation_main.py --init
```

**Corrupted Checksums:**
```bash
# Force update all checksums
python hr_automation_main.py --update-checksums
```

**Orphaned MD5 Files:**
```bash
# Clean up orphaned files
python hr_automation_main.py --clean
```

**Force Run When Needed:**
```bash
# Bypass integrity check
python hr_automation_main.py --force
```

### 📝 **Logging**
The system provides detailed logging at multiple levels:
- **INFO**: File changes detected, checksums stored
- **WARNING**: Missing files, I/O errors
- **ERROR**: Critical failures in checksum operations

## Integration with Existing Workflow

The file integrity system is designed to integrate seamlessly with existing workflows:

1. **Backward Compatibility**: Legacy `Desafio-4-RH.py` continues to work unchanged
2. **Optional Feature**: Can be disabled by always using `--force` flag
3. **Zero Configuration**: Works immediately after installation
4. **Minimal Overhead**: Fast checksums don't significantly impact runtime

---

*This file integrity monitoring system ensures efficient, reliable, and intelligent processing of HR automation data while maintaining the highest standards of data integrity and user experience.*