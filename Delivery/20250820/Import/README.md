# Import Folder - Input Data Files

This folder contains all the Excel files required for the HR automation process. The system expects specific files with predefined formats to calculate VR (meal voucher) benefits.

## Required Files

### Employee Data
- **`ATIVOS.xlsx`** - Active employees database
  - **Sheet**: `ATIVOS`
  - **Required columns**: `MATRICULA`, `EMPRESA`, `TITULO DO CARGO`, `DESC. SITUACAO`, `Sindicato`
  - **Purpose**: Main employee registry with current status and union information

### Working Days & Values
- **`Base dias uteis.xlsx`** - Working days per union/state
  - **Sheet**: `Planilha1`
  - **Expected columns**: `SINDICATO`, `DIAS_UTEIS`
  - **Purpose**: Defines working days for each union/state for benefit calculation

- **`Base sindicato x valor.xlsx`** - Daily VR values per state
  - **Sheet**: `Planilha1`
  - **Expected columns**: `ESTADO`, `VALOR`
  - **Purpose**: Maps states to their respective daily VR values

### Employee Status Files
- **`DESLIGADOS.xlsx`** - Terminated employees
  - **Sheet**: `DESLIGADOS `
  - **Key columns**: `MATRICULA`, `DATA DEMISSÃO`, `COMUNICADO DE DESLIGAMENTO`
  - **Purpose**: Tracks terminations and notification status for benefit calculations

- **`FÉRIAS.xlsx`** - Vacation records
  - **Sheet**: `Planilha1`
  - **Key columns**: `MATRICULA`, `DIAS DE FÉRIAS`
  - **Purpose**: Vacation days to subtract from benefit calculations

- **`ADMISSÃO ABRIL.xlsx`** - April admissions
  - **Sheet**: `Planilha1`
  - **Key columns**: `MATRICULA`, `Admissão`, `Cargo`
  - **Purpose**: New employees admitted in April with prorated benefits

### Exclusion Categories
- **`ESTÁGIO.xlsx`** - Interns
  - **Sheet**: `Planilha1`
  - **Key column**: `MATRICULA`
  - **Purpose**: Excludes interns from VR benefits

- **`EXTERIOR.xlsx`** - Foreign employees
  - **Sheet**: `Planilha1`
  - **Expected columns**: `MATRICULA`, `VALOR_EXTERIOR`, `STATUS_EXTERIOR`
  - **Purpose**: Excludes foreign employees from standard VR benefits

- **`AFASTAMENTOS.xlsx`** - Employees on leave
  - **Sheet**: `Planilha1`
  - **Key column**: `MATRICULA`
  - **Purpose**: Excludes employees on leave from VR benefits

- **`APRENDIZ.xlsx`** - Apprentices
  - **Sheet**: `Planilha1`
  - **Key column**: `MATRICULA`
  - **Purpose**: Excludes apprentices from VR benefits

### Template File
- **`VR MENSAL 05.2025.xlsx`** - Output template
  - **Sheet**: `VR MENSAL 05.2025`
  - **Purpose**: Defines the column order and structure for the final output file

## File Format Requirements

### General Requirements
- **Format**: Excel (.xlsx) files
- **Encoding**: UTF-8 compatible
- **Date Format**: YYYY-MM-DD for dates
- **Numeric Format**: Decimal numbers for monetary values

### Critical Data Points
- **MATRICULA**: Employee ID (must be consistent across all files)
- **Dates**: Must be in Excel date format or YYYY-MM-DD text format
- **Values**: Numeric format for calculations (VR daily rates, working days)

## Data Validation

The system performs automatic validation on all input files:
- ✅ Date format validation
- ✅ Required field presence
- ✅ Cross-file consistency checks
- ✅ Business rule validation (e.g., vacation days ≤ 30)
- ✅ LLM-powered data quality assessment

## File Placement

1. Place all required Excel files directly in this `Import/` folder
2. Ensure file names match exactly (case-sensitive)
3. Verify sheet names match the expected values
4. Do not modify the internal structure of the files

## Troubleshooting

### Common Issues
- **File not found**: Ensure exact file name match
- **Sheet not found**: Verify sheet names in Excel files
- **Data validation errors**: Check date formats and required columns
- **Empty files**: Ensure files contain data in expected format

### Getting Help
- Check the main system logs for specific error messages
- Verify file structure using Excel before processing
- Ensure all MATRICULA values are consistent across files
- Contact system administrator for persistent issues

---

**Last Updated**: August 18, 2025  
**System Version**: SkyNET I2A2 v2.0 (Refactored Architecture)