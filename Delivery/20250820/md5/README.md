# MD5 Checksum Storage Directory

This directory contains MD5 checksum files for file integrity monitoring in the SkyNET I2A2 HR Automation System.

## Purpose

The MD5 checksum files in this directory are used to:
- **Detect File Changes**: Monitor when input Excel files have been modified
- **Optimize Processing**: Skip automation when no files have changed
- **Ensure Data Integrity**: Verify that input data hasn't been corrupted
- **Provide Audit Trail**: Track when files were last processed

## File Structure

Each `.md5` file corresponds to an Excel file in the `Import/` directory:

```
md5/
├── ADMISSÃO ABRIL.xlsx.md5      # April admissions data
├── AFASTAMENTOS.xlsx.md5        # Leave of absence records
├── APRENDIZ.xlsx.md5            # Apprentice data
├── ATIVOS.xlsx.md5              # Active employees (main file)
├── Base dias uteis.xlsx.md5     # Working days configuration
├── Base sindicato x valor.xlsx.md5  # Union value mappings
├── DESLIGADOS.xlsx.md5          # Terminated employees
├── ESTÁGIO.xlsx.md5             # Intern records
├── EXTERIOR.xlsx.md5            # Foreign employees
├── FÉRIAS.xlsx.md5              # Vacation records
└── VR MENSAL 05.2025.xlsx.md5   # Monthly VR template
```

## File Format

Each `.md5` file contains a single line with the 32-character hexadecimal MD5 hash:

```
82583652d75615953f432d812a254388
```

## How It Works

### 1. **Initialization**
```bash
python hr_automation_main.py --init
```
- Creates initial MD5 checksums for all Excel files
- Stores them in this directory

### 2. **Change Detection**
```bash
python hr_automation_main.py --check
```
- Calculates current MD5 for each Excel file
- Compares with stored checksums
- Reports which files have changed

### 3. **Automatic Processing**
```bash
python hr_automation_main.py
```
- Only processes if files have changed
- Updates checksums after successful processing

## File Lifecycle

### **New Files**
- When a new Excel file is added to `Import/`, its `.md5` file is created automatically
- Status: "New file detected"

### **Changed Files**
- When an Excel file is modified, its MD5 changes
- Status: "File changed" with old/new checksums shown
- Checksum updated after successful processing

### **Unchanged Files**
- Files with matching checksums are skipped
- Status: "File unchanged"
- No processing needed

### **Missing Files**
- If an Excel file is deleted, its `.md5` file becomes orphaned
- Can be cleaned up with: `python hr_automation_main.py --clean`

## Management Commands

### **Status Check**
```bash
python hr_automation_main.py --status
```
Shows overall file integrity status.

### **Detailed Check**
```bash
python hr_automation_main.py --check
```
Lists all files and their change status.

### **Force Update**
```bash
python hr_automation_main.py --update-checksums
```
Recalculates and updates all checksums.

### **Cleanup**
```bash
python hr_automation_main.py --clean
```
Removes orphaned `.md5` files.

## Benefits

### **Performance**
- **Skip Unnecessary Work**: Don't process when no files changed
- **Fast Checksums**: MD5 calculation is quick even for large files
- **Minimal Overhead**: Checking is faster than full processing

### **Reliability**
- **Data Integrity**: Ensure processing uses current data
- **Change Tracking**: Know exactly which files triggered processing
- **Error Prevention**: Avoid processing with stale data

### **Transparency**
- **Clear Status**: Always know if processing is needed
- **Detailed Logging**: Track all file changes with timestamps
- **Audit Trail**: Historical record of when files were processed

## Troubleshooting

### **Missing MD5 Files**
If some `.md5` files are missing, initialize monitoring:
```bash
python hr_automation_main.py --init
```

### **Corrupted Checksums**
If checksums seem incorrect, force update:
```bash
python hr_automation_main.py --update-checksums
```

### **Orphaned Files**
If Excel files were deleted but `.md5` files remain:
```bash
python hr_automation_main.py --clean
```

### **Force Processing**
To bypass integrity check and process anyway:
```bash
python hr_automation_main.py --force
```

## Technical Details

### **MD5 Algorithm**
- Industry-standard hash function
- 32 hexadecimal characters (128 bits)
- Deterministic: same file always produces same hash
- Sensitive: any change produces completely different hash

### **File Monitoring**
- Monitors 11 specific Excel files
- Chunk-based reading for memory efficiency
- Robust error handling for I/O operations
- Automatic directory creation and maintenance

### **Integration**
- Seamlessly integrated with main automation workflow
- No configuration required
- Works with both modern and legacy interfaces
- Optional feature: can be bypassed with `--force`

---

**Note**: This directory and its contents are automatically managed by the file integrity system. Manual modification of `.md5` files is not recommended as it may cause inconsistent behavior.

For more information, see:
- `README_File_Integrity.md` - Complete file integrity documentation
- `Libs/file_integrity_service.py` - Implementation details
- Main project documentation for usage examples