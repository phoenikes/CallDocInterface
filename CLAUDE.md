# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**CallDocInterface** - Bidirectional synchronization system between CallDoc appointment system and SQLHK medical database for managing cardiac catheterization appointments and patient data.

## Architecture & Data Flow

### High-Level Architecture
```
CallDoc API (192.168.1.76:8001)          SQLHK Database (SQL-KI\SQL_KI)
     ↓                                              ↑
   Appointments                                 Untersuchungen
     ↓                                              ↑
CallDocInterface ←→ Synchronizers ←→ MsSqlApiClient (192.168.1.67:7007)
                         ↓
                    GUI (PyQt5)
```

### Core Synchronization Flow
1. **Appointment Fetch**: CallDoc API → filter by date/type/doctor/room/status
2. **Patient Enrichment**: Appointments enriched with patient data from CallDoc
3. **Comparison**: Match CallDoc appointments with SQLHK Untersuchungen via PatientID
4. **Synchronization**: Execute INSERT/UPDATE/DELETE operations to align both systems
5. **Validation**: M1-Ziffer enrichment and data validation

### Smart Status Filtering
- Future dates → filter by "created" status only
- Past/current dates → no status filtering (include all)
- Manual override via explicit status parameter

## Common Commands

### Build Executable
```bash
pyinstaller CallDocSQLHKSync.spec
# Output: dist/CallDocSQLHKSync.exe
```

### Run GUI Application
```bash
python sync_gui_qt.py
# Or use the built exe: CallDocSQLHKSync.exe
```

### Command-Line Synchronization
```bash
# Compare CallDoc vs SQLHK for specific date
python main.py vergleich --datum 2025-08-19 --termintyp HERZKATHETERUNTERSUCHUNG

# Patient synchronization
python main.py patienten-sync --datum 2025-08-19

# Weekly export (uses config*.json files)
python main.py
```

### Debug & Analysis
```bash
# Check database connection
python check_database_connection.py

# Check API server status
python check_api_server.py

# Compare appointments with Untersuchungen
python vergleich_calldoc_sqlhk.py
```

## Key Modules & Their Responsibilities

### Core Synchronizers
- **calldoc_sqlhk_synchronizer.py**: Main orchestrator for bidirectional sync
- **patient_synchronizer.py**: Handles patient data sync (CallDoc→SQLHK)
- **untersuchung_synchronizer.py**: Manages Untersuchung (examination) sync

### API Interfaces
- **calldoc_interface.py**: CallDoc API client (appointments, patients)
- **sqlhk_interface.py**: Direct SQLHK database interface
- **mssql_api_client.py**: HTTP API wrapper for SQLHK operations

### GUI Components
- **sync_gui_qt.py**: Main PyQt5 GUI application
- **dashboard.py**: Sync monitoring dashboard
- **log_viewer.py**: Real-time log viewer

### Configuration
- **constants.py**: API URLs, appointment types, doctors, rooms mappings
- **config.json**: Runtime configuration (scheduler, export settings)
- **appointment_types_mapping.py**: Dynamic appointment type ID resolution

## Database Schema Understanding

### SQLHK Key Tables
- **Untersuchung**: Main examination records (UntersuchungID, PatientID, UntersuchungartID)
- **Patient**: Patient master data (PatientID, M1Ziffer, personal data)
- **Untersuchungart**: Examination types linked to CallDoc appointment types via ExterneID

### CallDoc Data Structure
- Appointments contain: id, patient (id/object), status, appointment_type_id
- Patient objects include: surname, name, date_of_birth, piz (patient ID)

## API Endpoints

### CallDoc API (192.168.1.76:8001)
- `GET /api/v1/frontend/appointment_search/` - Search appointments
- `GET /api/v1/frontend/patient_search/` - Search patients by PIZ

### SQLHK API (192.168.1.67:7007)
- `GET /api/untersuchung` - Fetch Untersuchungen by date
- `GET /api/patient/{id}` - Get patient details including M1Ziffer
- `POST/PUT/DELETE /api/untersuchung` - Manage Untersuchungen

## Important Business Logic

### Appointment Type Mapping
- CallDoc appointment_type_id ↔ SQLHK UntersuchungartID via Untersuchungart.ExterneID
- Default: Type 24 (HERZKATHETERUNTERSUCHUNG) for cardiac catheterization

### Date Format Conversion
- CallDoc: YYYY-MM-DD
- SQLHK: DD.MM.YYYY
- Automatic conversion handled in synchronizers

### Conflict Resolution
- Existing Untersuchung: UPDATE if data differs
- No matching Untersuchung: INSERT new record
- Untersuchung without appointment: Mark for potential DELETE

## Testing & Validation

### Manual Testing Scripts
```bash
# Test specific date synchronization
python synchronize_04_08_2025.py

# Debug Untersuchungen for date
python debug_untersuchungen.py

# Check patient data structure
python check_patient_structure.py
```

### Data Validation Files
- JSON exports: `calldoc_termine_*.json`, `sqlhk_untersuchungen_*.json`
- Sync results: `sync_result_*_*.json` with detailed operation logs
- CSV comparisons: `vergleich_*.csv` for tabular analysis

## Deployment Notes

### PyInstaller Build
- Entry point: `sync_gui_qt.py`
- Icon: `resources\app_icon.ico`
- Console mode: False (GUI application)
- Hidden imports resolved automatically

### Production Configuration
- Scheduler runs every hour (configurable in config.json)
- Logs stored with timestamp: `sync_gui_YYYYMMDD_HHMMSS.log`
- Auto-sync on startup if configured

## Common Troubleshooting

### Connection Issues
1. Check VPN/network to reach 192.168.x.x addresses
2. Verify SQL Server allows remote connections
3. Check SQLHK API service is running on port 7007

### Sync Discrepancies
1. Verify appointment_type_mapping is loaded correctly
2. Check date format conversions
3. Review patient ID matching logic
4. Examine sync_result JSON files for detailed errors

### Performance Optimization
- Patient data is cached during sync session
- Bulk operations used where possible
- Connection pooling in MsSqlApiClient