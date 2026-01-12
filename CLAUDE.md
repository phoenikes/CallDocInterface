# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Memory Bank - Active Projects

### Project Index
1. **CallDocInterface** - Medical appointment synchronization system (THIS PROJECT)
   - Location: `C:\Users\administrator.PRAXIS\PycharmProjects\calldocinterface`
   - Purpose: Bidirectional sync between CallDoc and SQLHK databases
   - Main Entry: `sync_gui_qt.py` (GUI) or `sync_api_server.py` (API)

## Project Overview
**CallDocInterface** - Bidirectional synchronization system between CallDoc appointment system and SQLHK medical database for managing cardiac catheterization appointments and patient data.

### Current Version: 2.1.0 (12.01.2026)
- **GUI Application**: Modern PyQt5 interface with real-time dashboard
- **REST API Server**: Automated synchronization via HTTP API (Port 5555)
- **Single-Patient Sync**: Targeted synchronization via M1Ziffer
- **Live-Ueberwachung**: Automatische Aenderungserkennung mit Hash-Vergleich
- **KVDT-Datenanreicherung**: Patientendaten aus .con Dateien
- **PatientResolver**: Automatische Patientenaufloesung via PIZ, KVNR oder Name+Geburtsdatum
- **Slack-Integration**: Sync-Ergebnisse mit Patientendetails an Slack-Channel
- **Desktop Integration**: Standalone EXE with integrated API
- **Last Updated**: 12.01.2026
- **Latest Build**: CallDocSync.exe (86 MB)

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
                         ↓
                 REST API (Port 5555)
```

### Core Synchronization Flow
1. **Appointment Fetch**: CallDoc API → filter by date/type/doctor/room/status
2. **Patient Enrichment**: Appointments enriched with patient data from CallDoc
3. **Comparison**: Match CallDoc appointments with SQLHK Untersuchungen via PatientID
4. **Synchronization**: Execute INSERT/UPDATE/DELETE operations to align both systems
5. **KVDT-Datenanreicherung**: Patientendaten aus .con Dateien (PLZ, Stadt, Strasse, Krankenkasse, Geschlecht)

### Smart Status Filtering
- Future dates → filter by "created" status only
- Past/current dates → no status filtering (include all)
- Manual override via explicit status parameter

## Common Commands

### Build Executable
```bash
# Create icon
python create_simple_icon.py

# Build EXE with integrated API
pyinstaller --onefile --windowed \
  --name CallDocSyncWithAPI \
  --collect-all PyQt5 --collect-all matplotlib \
  --collect-all numpy --collect-all requests \
  --exclude-module PyQt6 \
  --add-data "single_patient_sync.py;." \
  --add-data "sync_api_server.py;." \
  sync_gui_qt.py

# Output: dist/CallDocSyncWithAPI.exe

# Create desktop shortcut
python create_shortcut.py
```

### Run GUI Application
```bash
python sync_gui_qt.py
# Or use the built exe: dist/CallDocSync.exe
# Or use desktop shortcut: "CallDoc-SQLHK Sync"
```

### Run REST API Server
```bash
# API starts automatically with GUI:
python sync_gui_qt.py

# Single-Patient Sync (NEW!)
curl -X POST http://localhost:5555/api/sync/patient \
  -H "Content-Type: application/json" \
  -d '{"piz": "1698369", "date": "2025-10-06"}'

# Full-Day Sync
curl -X POST http://localhost:5555/api/sync \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-10-06", "appointment_type_id": 24}'
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
- **sync_gui_qt.py**: Main PyQt5 GUI application with integrated dashboard
- **api_documentation_dialog.py**: Modal dialog with comprehensive API documentation
- **dashboard.py**: Sync monitoring dashboard (integrated into main GUI)
- **log_viewer.py**: Real-time log viewer (integrated into main GUI)

### REST API Components
- **sync_api_server.py**: Flask REST API server for automated synchronization
- **test_api_simple.py**: Simple API health check script

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

### Sync REST API (localhost:5555)
- `POST /api/sync` - Start synchronization for specific date
- `GET /api/sync/status/{task_id}` - Get sync task status
- `GET /api/sync/active` - List all active sync tasks
- `POST /api/sync/cancel/{task_id}` - Cancel running sync
- `GET /health` - API health check

## Critical Fixes Applied

### 1. Appointment Type Filter Bug (FIXED)
- **Issue**: CallDoc API returns `appointment_type` not `appointment_type_id`
- **Fix**: sync_gui_qt.py line 143 - changed filter to use correct field
- **Impact**: Resolved issue where 30 appointments became 0 after filtering

### 2. NoneType Patient Data (FIXED)
- **Issue**: AttributeError when patient info is None
- **Fix**: untersuchung_synchronizer.py lines 737-752 - added robust None checks
- **Impact**: Prevents crashes when patient data is missing

### 3. SQL Injection Vulnerabilities (FIXED)
- **Issue**: Direct string interpolation in SQL queries
- **Fix**: Added validation and prepared for parametrized queries
- **Impact**: Enhanced security against SQL injection attacks

### 4. Memory Leaks (FIXED)
- **Issue**: Unbounded patient_cache growth
- **Fix**: Added MAX_CACHE_SIZE limit of 1000 entries
- **Impact**: Prevents memory exhaustion during long-running syncs

### 5. Thread Management (FIXED)
- **Issue**: Unsafe thread termination using terminate()
- **Fix**: Implemented graceful shutdown with timeout
- **Impact**: Prevents data corruption and ensures clean shutdown

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

# Test 24.09.2025 synchronization (mit Patientenerstellung)
python sync_24_september_complete.py

# Test 30.09.2025 synchronization
python sync_30_september.py

# Verify INSERT operations
python verify_insert.py

# Test direct INSERT bypassing upsert_data
python test_direct_insert.py
```

### Data Validation Files
- JSON exports: `calldoc_termine_*.json`, `sqlhk_untersuchungen_*.json`
- Sync results: `sync_result_*_*.json` with detailed operation logs
- CSV comparisons: `vergleich_*.csv` for tabular analysis

## Deployment Notes

### PyInstaller Build
- Entry point: `sync_gui_qt.py`
- Icon: `sync_app.ico` (custom created with sync arrows)
- Console mode: False (GUI application)
- Spec file: `CallDocSync.spec`
- Hidden imports: Flask, PyQt5, matplotlib, pandas, numpy (WICHTIG: NumPy/Pandas für Matplotlib!)
- Output: `dist/CallDocSync.exe` (standalone, no Python required, ~90MB)

### Build-Befehl
```bash
pyinstaller CallDocSync.spec --noconfirm --clean
```

### Lokales Deployment
- **Lokale EXE**: `C:\Users\administrator.PRAXIS\PycharmProjects\calldocinterface\dist\CallDocSync.exe`
- **Desktop-Shortcut**: Erstellt mit `create_shortcut.py`
- **WICHTIG**: `slack_config.json` muss im gleichen Ordner wie die EXE liegen!

### Netzwerk-Deployment (22.09.2025)
- **Netzlaufwerk**: `P:\MCP\Calldocinterface\`
- **Enthaltene Dateien**:
  - CallDocSync.exe (89.7 MB)
  - CallDocSync_Start.bat (Starter-Script)
  - sync_app.ico
  - README.md (Benutzer-Dokumentation)
  - CLAUDE.md (Technische Dokumentation)
  - SYNC_FIX_DOKUMENTATION.md (Fehlerbehebungen)
- **Desktop-Shortcut**: "CallDocSync (Netzwerk)" erstellt mit `create_network_shortcut.py`
- **Ausführung**:
  1. Desktop-Shortcut "CallDocSync (Netzwerk)"
  2. Batch-Datei `P:\MCP\Calldocinterface\CallDocSync_Start.bat`
  3. Direkt `P:\MCP\Calldocinterface\CallDocSync.exe`

### Production Configuration
- Scheduler runs every hour (configurable in config.json)
- Logs stored with timestamp: `sync_gui_YYYYMMDD_HHMMSS.log`
- Auto-sync on startup if configured
- Läuft direkt vom Netzlaufwerk ohne lokale Installation

## Common Troubleshooting

### Connection Issues
1. **WICHTIG: apimsdata.exe muss laufen!** - Diese Anwendung stellt die SQL-Verbindung zum Server her
   - Ohne apimsdata.exe gibt es 500 Internal Server Errors beim upsert_data
   - Die apimsdata.exe managed den SQL Traffic zum Server (192.168.1.67:7007)
2. Check VPN/network to reach 192.168.x.x addresses
3. Verify SQL Server allows remote connections
4. Check SQLHK API service is running on port 7007

### Sync Discrepancies
1. Verify appointment_type_mapping is loaded correctly
2. Check date format conversions
3. Review patient ID matching logic
4. Examine sync_result JSON files for detailed errors

## CRITICAL SYNCHRONIZATION FIXES (22.09.2025)

### Problem: Synchronisation funktionierte nicht
Die Synchronisation zwischen CallDoc und SQLHK schlug fehl - Patienten und Untersuchungen wurden nicht eingefügt.

### Gefundene Fehler und Lösungen:

#### 1. ❌ FALSCHER DATENBANKNAME bei Patient-Lookups für Untersuchungen
**Problem**: In `untersuchung_synchronizer.py` wurden Patienten in "SuPDatabase" gesucht statt in "SQLHK"
**Kontext**: Beim Synchronisieren von Untersuchungen müssen Patienten aus SQLHK gelesen werden, da dort die Untersuchungen gespeichert werden
**Lösung**: Für Untersuchungs-bezogene Patient-Lookups:
```python
self.mssql_client.execute_sql(query, "SuPDatabase")  # FALSCH für Untersuchungen
```
Ersetzen durch:
```python
self.mssql_client.execute_sql(query, "SQLHK")  # RICHTIG für Untersuchungen
```
**WICHTIG**: SuPDatabase wird für andere Zwecke weiterhin verwendet - nur bei Untersuchungen ist SQLHK korrekt!

#### 2. ❌ upsert_data Endpoints funktionieren nicht
**Problem**: Die `/api/upsert_data` Endpoints geben 500 Fehler zurück
**Workaround**: Manuelles SELECT vor INSERT/UPDATE:
```python
# Prüfe ob Datensatz existiert
check_result = self.mssql_client.execute_sql(check_query, "SQLHK")
if check_result.get("rows"):
    # UPDATE oder skip
else:
    # INSERT
    result = self.mssql_client.insert_untersuchung(data)
```

#### 3. ❌ INSERT-Fehler falsch interpretiert
**Problem**: "This result object does not return rows" wurde als Fehler behandelt
**Lösung**: Diese Meldung ist NORMAL bei INSERT - als Erfolg behandeln:
```python
if result.get("error") and "does not return rows" in str(result.get("error")):
    return {"success": True, "message": "Erfolgreich eingefügt"}
```

#### 4. ❌ Fehlende Mappings zwischen CallDoc und SQLHK
**Problem**: Keine Zuordnungen zwischen IDs existierten
**Lösung**: Mappings wurden in DB erstellt:
- appointment_type 24 → UntersuchungartID 1
- room_id → HerzkatheterID (z.B. 54→3, 19→2, 18→1, 61→6)  
- employee_id → UntersucherAbrechnungID (z.B. 18→1, 27→2, 50→12)

### WICHTIGE REGELN für die Zukunft:
1. **RICHTIGE DATENBANK VERWENDEN**:
   - **SQLHK**: Für Untersuchungen, Patienten, Herzkatheter, Untersucherabrechnung
   - **SuPDatabase**: Für andere Abfragen (je nach Kontext)
   - **KRITISCH**: Patient-Lookups für Untersuchungen MÜSSEN in "SQLHK" erfolgen, NICHT in "SuPDatabase"
2. **apimsdata.exe MUSS laufen** für SQL-Operationen
3. **Mappings müssen existieren** zwischen CallDoc und SQLHK IDs
4. **INSERT-Meldung "does not return rows" ist NORMAL**, nicht als Fehler behandeln
5. **Bei 500-Fehlern von upsert_data**: Workaround mit direktem SQL verwenden

### Performance Optimization
- Patient data is cached during sync session (max 1000 entries)
- Bulk operations used where possible
- Connection pooling in MsSqlApiClient
- Thread-safe operations with proper locking
- Async task execution in API server

## REST API Integration

### API Server Features
- Runs independently of GUI
- Async task management with threading
- Task status tracking and cancellation
- CORS enabled for cross-origin requests
- JSON request/response format

### Automation Examples
```powershell
# PowerShell daily sync
Invoke-RestMethod -Uri "http://localhost:5555/api/sync" `
  -Method POST `
  -Body '{"date":"2025-08-20","appointment_type_id":24}' `
  -ContentType "application/json"
```

```batch
# Batch script for Windows Task Scheduler
@echo off
curl -X POST http://localhost:5555/api/sync ^
  -H "Content-Type: application/json" ^
  -d "{\"date\":\"2025-08-20\",\"appointment_type_id\":24}"
```

## GUI Menu System

### File Menu
- Export current log
- Clear log
- Exit application

### API Menu
- Start/Stop API Server
- Show API Documentation (comprehensive modal)
- Test API Connection

### Help Menu
- About dialog
- Keyboard shortcuts

## Project Files Summary

### Core Application
- `sync_gui_qt.py` - Main GUI application (1000+ lines)
- `sync_api_server.py` - REST API server (500+ lines)
- `api_documentation_dialog.py` - API docs dialog (550+ lines)

### Synchronization Logic
- `calldoc_sqlhk_synchronizer.py` - Main sync orchestrator
- `patient_synchronizer.py` - Patient data sync
- `untersuchung_synchronizer.py` - Examination sync

### API Clients
- `calldoc_interface.py` - CallDoc API client
- `mssql_api_client.py` - SQLHK HTTP API client
- `sqlhk_interface.py` - Direct DB interface

### Configuration
- `constants.py` - API URLs, mappings
- `appointment_types_mapping.py` - Dynamic type mapping
- `CallDocSync.spec` - PyInstaller configuration

### Utilities
- `create_simple_icon.py` - Icon generator
- `create_shortcut.py` - Desktop shortcut creator
- `test_api_simple.py` - API health check

### KVDT Integration
- `kvdt_enricher.py` - Patientendaten aus .con Dateien anreichern
- SKILLS_CENTRAL/kvdt - KVDT Parser Modul

## KVDT-Datenanreicherung (NEU - 10.01.2026)

### Funktionsweise
Nach der Synchronisation werden Patientendaten automatisch aus KVDT .con Dateien angereichert.
Die .con Dateien befinden sich in `M:\M1\PROJECT\KBV\` (118 Dateien).

### Angereicherte Felder (KVDT → SQLHK Patient)

| KVDT-Feld | SQLHK-Feld | Beschreibung |
|-----------|------------|--------------|
| 3112 (PLZ) | PLZ | Postleitzahl (Integer) |
| 3113 (Ort) | Stadt | Wohnort |
| 3107+3109 | Strasse | Strasse mit Hausnummer |
| 3110 (Geschlecht) | Geschlecht | M→1, W→2 |
| **3119** | **Versichertennr** | **KVNR (10-stellig, z.B. Q361326624)** |
| **4111** | **Krankenkasse** | **9-stellige Kostentraegerkennung (IK)** |
| **4121** | **Krankenkassestatus** | **Gebuehrenordnung (1=GKV, 2=PKV)** |

### WICHTIG: Krankenkassen-Felder
- **Krankenkasse**: Ist ein INTEGER-Feld mit der 9-stelligen IK-Nummer (z.B. 108310400 für AOK Bayern)
- **Krankenkassestatus**: Gebührenordnung aus Feld 4121 (1=GKV, 2=PKV)
- Die IK-Nummer kommt aus KVDT-Feld 4111 (Kostentraegerkennung), NICHT aus 4131

### Datumskonvertierung
- KVDT: JJJJMMTT (z.B. "19720804")
- SQLHK: TT.MM.JJJJ (z.B. "04.08.1972")
- Automatische Konvertierung in `kvdt_enricher._convert_date_kvdt_to_sqlhk()`

### Test-Befehl
```python
from kvdt_enricher import KVDTEnricher
enricher = KVDTEnricher()
result = enricher.enrich_patient('1729414')
print(result)
```

## Live-Ueberwachung / Change Detection (NEU - 10.01.2026)

### Funktionsweise
Die Live-Ueberwachung prueft in regelmaessigen Intervallen, ob sich Termine in CallDoc geaendert haben.
Bei erkannten Aenderungen wird automatisch ein Sync gestartet.

### Features
- **Hash-basierte Erkennung**: Vergleicht Termin-IDs + Status + Patient-IDs
- **Nur aktueller Tag**: Ueberwacht nur Termine des heutigen Tages
- **Einstellbares Intervall**: 1-60 Minuten (Default: 2 Minuten)
- **Automatischer Sync**: Bei Aenderung wird sofort synchronisiert

### GUI-Einstellungen
```
☑ Aenderungen automatisch erkennen
Intervall: [2] Min  (1-60)
Status: Live-Sync: Aktiv (naechster Check: 21:10:00)
```

### Einstellungen speichern
Die Einstellungen werden in `auto_sync_settings.json` gespeichert:
```json
{
  "auto_sync_enabled": true,
  "auto_sync_time": "10:25",
  "live_sync_enabled": true,
  "live_sync_interval": 2
}
```

### Hash-Berechnung
Der Hash wird aus folgenden Daten berechnet:
- Termin-ID
- Status (created, confirmed, cancelled, etc.)
- Patient-ID

Bei Aenderung des Hash wird automatisch synchronisiert.

## Standorte-Verwaltung (NEU - 09.01.2026)

### Menu: Einstellungen → Standorte
Zeigt alle Herzkatheter-Standorte aus der SQLHK Datenbank.

### Felder
- **HerzkatheterID**: Interne ID
- **HerzkatheterName**: Name des Standorts
- **room_id**: Zuordnung zu CallDoc Raum
- **Aktiv**: Ob der Standort aktiv ist

### Aktuelle Standorte
| Name | room_id | Aktiv |
|------|---------|-------|
| Rummelsberg 1 | 18 | Ja |
| Rummelsberg 2 | 19 | Ja |
| Offenbach | 54 | Ja |
| Braunschweig | 61 | Ja |

## Slack-Integration (NEU - 12.01.2026)

### Konfiguration
Die Slack-Benachrichtigungen werden ueber `slack_config.json` konfiguriert:
```json
{
  "channel": "#cathlab",
  "enabled": true,
  "bot_token": "xoxb-..."
}
```

**WICHTIG**: Diese Datei muss im gleichen Ordner wie die EXE liegen!

### GUI-Elemente
- **Checkbox "Slack:"**: Aktiviert/deaktiviert Benachrichtigungen
- **Channel-Eingabefeld**: Slack-Channel (Default: #cathlab)

### Nachrichtenformat
Bei jedem Sync werden Details zu eingefuegten, aktualisierten und geloeschten Patienten gesendet:
```
`1698369` *Mueller, Hans* (15.03.1965) - Dr. Sandrock @ Rummelsberg 1
```

### Untersucher-Mapping (slack_notifier.py)
| ID | Name |
|----|------|
| 1 | Dr. Sandrock |
| 2 | Dr. Papageorgiou |
| 12 | Dr. Koch |
| 13 | Dr. Pannu |
| 19 | Dr. Schaeffer |

### Standort-Mapping (slack_notifier.py)
| ID | Name |
|----|------|
| 1 | Rummelsberg 1 |
| 2 | Rummelsberg 2 |
| 3 | Offenbach |
| 6 | Braunschweig |

## PatientResolver (NEU - 12.01.2026)

### Funktionsweise
Der PatientResolver loest Patienten automatisch auf, auch wenn keine PIZ vorhanden ist:

1. **PIZ-Suche**: Direkte Suche via M1Ziffer in SQLHK
2. **KVNR-Fallback**: Suche der KVNR in KVDT .con Dateien → M1Ziffer
3. **Name+Geburtsdatum**: Suche nach Nachname, Vorname und Geburtsdatum
4. **Neuanlage**: Wenn nicht gefunden, wird Patient in SQLHK angelegt

### Duplikat-Vermeidung
Vor der Neuanlage wird SQLHK nach Name+Geburtsdatum durchsucht, um Duplikate zu verhindern.

### Verwendung
```python
from patient_resolver import PatientResolver
resolver = PatientResolver(mssql_client)
result = resolver.resolve_patient(appointment)
# result = {"patient_id": 12345, "m1ziffer": "1698369", "source": "piz"}
```

## Version History

### Version 2.1.0 (12.01.2026)
- **PatientResolver**: Neue Komponente fuer automatische Patientenaufloesung
  - Suche via PIZ (M1Ziffer)
  - Fallback: KVNR-Suche in KVDT .con Dateien
  - Fallback: Name + Geburtsdatum Suche
  - Automatische Neuanlage wenn Patient nicht gefunden
  - Duplikat-Vermeidung: Prueft SQLHK vor Neuanlage
- **Slack-Integration**: Sync-Ergebnisse an konfigurierbaren Channel
  - Detaillierte Benachrichtigungen mit M1Ziffer, Name, Geburtsdatum
  - Untersucher und Standort werden aufgeloest
  - GUI: Checkbox + Eingabefeld fuer Channel
  - Token in slack_config.json (muss neben EXE liegen)
- **Statistik-Fix**: Korrekte Zaehlung durch eindeutige PatientIDs
- **Neue Dateien**:
  - `patient_resolver.py` - PatientResolver Klasse
  - `slack_notifier.py` - Slack-Benachrichtigungen
  - `slack_config.json` - Slack-Konfiguration (Channel, Token)

### Version 2.0.5 (10.01.2026)
- KVDT-Enricher: Versichertennr (KVNR) aus Feld 3119 hinzugefuegt
- Alle GKV-Patienten erhalten jetzt automatisch ihre KVNR
- PKV-Patienten sind nicht in KVDT (wie erwartet)

### Version 2.0.4 (10.01.2026)
- Live-Ueberwachung mit Hash-basierter Aenderungserkennung
- KVDT-Enricher Fix: Krankenkasse = 9-stellige IK-Nummer (Feld 4111)
- KVDT-Enricher Fix: Krankenkassestatus = Gebuehrenordnung (Feld 4121)
- Neues Feld kassen_ik im KVDT-Parser

### Version 2.0.3 (10.01.2026)
- KVDT-Datenanreicherung nach Sync
- Integration SKILLS_CENTRAL KVDT Parser
- Automatische Datumskonvertierung JJJJMMTT → TT.MM.JJJJ

### Version 2.0.2 (09.01.2026)
- Standorte-Verwaltung Dialog
- API-Endpoint Fix (/api/execute_sql)

### Version 2.0.1 (09.01.2026)
- Auto-Sync Scheduler
- API-Dokumentation Dialog