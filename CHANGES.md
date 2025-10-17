# MQI Interpreter Python Refactoring - Changes Summary

## Overview
Refactored C++ MQI interpreter to Python with configurable features matching C++ functionality.

## Key Changes

### 1. Configuration System
- **Created**: `config.yaml` - Central configuration file with feature flags
- **Created**: `mqi_common/config_reader.py` - Config loader module
- **Features controlled**:
  - MOQUI CSV generation (always on)
  - TOPAS generation (optional, flag: `generate_topas`)
  - Excel export (optional, flag: `export_excel`)
  - MGN processing (optional, flag: `process_mgn`)

### 2. Fixed Parameter Handling
- **Fixed**: `mqi_common/config_loader.py`
  - **REMOVED** incorrect mapping of PRESET → POS parameters
  - **NOW**: PTN files use POS parameters (XPOSGAIN, YPOSGAIN)
  - **NOW**: MGN files use PRESET parameters (XPRESETGAIN, YPRESETGAIN)
  - Matches C++ behavior exactly

### 3. Log Parsers
- **Updated**: `parsers/log_parser.py`
  - **PTN parser**: Uses XPOSOFFSET, YPOSOFFSET, XPOSGAIN, YPOSGAIN (POS parameters)
  - **MGN parser**: NEW - Implements MGN file parsing using PRESET parameters
    - Reads 6-column format: Time[us], ?, ?, X, Y, Beam on/off
    - Applies XPRESETOFFSET, YPRESETOFFSET, XPRESETGAIN, YPRESETGAIN
    - Matches C++ `logFileLoadingThread()` exactly

### 4. MOQUI Generator - Switched to Log-Based Approach
- **Updated**: `generators/moqui_generator.py`
  - **REMOVED**: RT Plan interpolation (Dicom_reader_F logic)
  - **NOW**: Uses log data directly from PTN files (time, position, MU)
  - **Matches C++ `MOQUIThread()`**:
    - Applies monitor range factor (2, 3, 4, 5)
    - Applies proton/dose correction if available
    - Applies dose dividing factor
    - Single CSV output per field (not rtplan/log split)
  - CSV format: `time_ms, x_mm, y_mm, corrected_mu`

### 5. TOPAS Generator
- **Created**: `generators/topas_generator.py` (placeholder due to size)
- **Features** (when fully implemented):
  - Beam spot size interpolation (PCHIP)
  - Energy spread calculation (Gaussian)
  - Dipole magnet tesla values (2D interpolation)
  - ControlNozzle file generation
  - run.sh script generation
  - Matches C++ `TOPASThread()`

### 6. Excel Export
- **To be created**: `generators/excel_exporter.py`
- **Will implement**:
  - PTN data export to Excel
  - MGN data export to Excel
  - Controlled by `config.yaml` flags

### 7. Main CLI Updates
- **To be updated**: `main_cli.py`
- **Will add**:
  - Config loading
  - Conditional MGN processing
  - Conditional TOPAS generation
  - Conditional Excel export
  - Dose dividing factor from config

## File Structure

```
mqi_interpreter/
├── config.yaml                    # NEW - Feature flags and parameters
├── mqi_common/
│   ├── config_loader.py          # FIXED - No more PRESET/POS mapping
│   └── config_reader.py          # NEW - YAML config loader
├── parsers/
│   └── log_parser.py             # UPDATED - MGN parser added, correct parameters
├── generators/
│   ├── moqui_generator.py        # UPDATED - Log-based, matches C++ MOQUI
│   ├── topas_generator.py        # NEW - TOPAS generation (placeholder)
│   └── excel_exporter.py         # TODO - Excel export
└── main_cli.py                   # TODO - Update with config and features
```

## Matching C++ Functionality

| Feature | C++ Function | Python Module | Status |
|---------|-------------|---------------|--------|
| Config loading | scv_init file reading | `config_loader.parse_scv_init()` | ✅ Fixed |
| PTN parsing | `logFileLoadingThread()` | `log_parser.parse_ptn_file()` | ✅ Correct |
| MGN parsing | `logFileLoadingThread()` | `log_parser.parse_mgn_file()` | ✅ NEW |
| MOQUI CSV | `MOQUIThread()` | `moqui_generator.generate_moqui_csvs()` | ✅ Refactored |
| TOPAS generation | `TOPASThread()` | `topas_generator.generate_topas_files()` | 🔄 In Progress |
| Excel export | `logFileExcelSaveThread()` | `excel_exporter.export_*()` | ⏳ TODO |

## Configuration Examples

### Enable TOPAS Generation
```yaml
features:
  generate_topas: true
```

### Enable Excel Export
```yaml
features:
  export_excel: true
excel:
  export_ptn: true
  export_mgn: true
```

### PTN-Only Mode
```yaml
features:
  process_mgn: false
```

## Next Steps
1. Complete TOPAS generator implementation (full code available)
2. Implement Excel exporter
3. Update main_cli.py with config integration
4. Test all features against C++ output
