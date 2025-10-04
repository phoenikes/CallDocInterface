# CallDoc-SQLHK Synchronisation System

## Projektüberblick
Bidirektionales Synchronisationssystem zwischen CallDoc Terminverwaltung und SQLHK Datenbank für Herzkatheter-Untersuchungen und Patientendaten. Das System bietet:

1. **GUI-Anwendung mit Dashboard**: Moderne PyQt5-Oberfläche mit Echtzeit-Protokoll und Statistiken
2. **REST API Server**: Automatisierte Synchronisation via HTTP API (Port 5555)
3. **Export von Termindaten**: Strukturierte JSON/CSV Exporte aus dem CallDoc-System
4. **Bidirektionale Synchronisierung**: Intelligenter Abgleich zwischen CallDoc und SQLHK

---

## Hauptfunktionen

### 1. GUI-Anwendung (sync_gui_qt.py)
- **Hauptfenster** mit Datum-Auswahl und Sync-Button
- **Echtzeit-Protokoll** zeigt alle Sync-Vorgänge
- **Statistik-Dashboard** mit grafischen Auswertungen
- **API-Menü** mit integrierter Dokumentation und Server-Steuerung
- **Auto-Sync** Option beim Start
- **Thread-sichere** Ausführung mit Fortschrittsanzeige

### 2. REST API Server (sync_api_server.py)
- Läuft automatisch auf Port 5555 beim Start der GUI
- Ermöglicht automatisierte Synchronisation via HTTP/REST
- **NEU: Single-Patient Synchronisation** für gezielte Einzelpatient-Updates
- Endpoints:
  - `POST /api/sync/patient` - **NEU:** Synchronisiert einzelnen Patienten via M1Ziffer
  - `POST /api/sync` - Startet Synchronisation für bestimmtes Datum
  - `GET /api/sync/status/{task_id}` - Status-Abfrage mit Echtzeit-Fortschritt
  - `GET /api/sync/active` - Zeigt alle aktiven Synchronisierungen
  - `GET /health` - Health Check für Monitoring
- Vollständige Dokumentation: siehe [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### 3. Datenbank-Synchronisierung
- **Tagesweise Synchronisierung:** Abgleich der CallDoc-Termine mit der SQLHK-Datenbank
- **Automatische Erkennung:** Neue, zu aktualisierende und zu löschende Untersuchungen
- **Konfliktauflösung:** Intelligente Duplikat-Erkennung und Merge-Strategien
- **Transaktional:** Atomare Operations für Datenkonsistenz

### 4. Export-Funktionen
- **Einzelexport:** Termine eines Tages mit Patientendaten als JSON
- **Wochenexport:** Komplette Kalenderwoche (Mo-Fr, ohne Feiertage)
- **Flexible Filter:** Nach Terminart, Arzt und Raum filterbar

---

## Wichtige Dateien & Klassen

### GUI & API Komponenten
- **sync_gui_qt.py**: Moderne PyQt5 GUI-Anwendung mit Dashboard und integrierter API
- **sync_api_server.py**: Flask REST API Server (startet automatisch mit GUI)
- **single_patient_sync.py**: NEU - Unabhängige Single-Patient Synchronisation
- **api_documentation_dialog.py**: Integrierte API-Dokumentation in GUI
- **API_DOCUMENTATION.md**: Vollständige API-Dokumentation für externe Programme
- **API_QUICK_REFERENCE.md**: Kompakte API-Übersicht mit Beispielen
- **API_EXAMPLES.md**: Getestete, funktionierende Beispiele mit echten Daten (04.10.2025)
- **CallDocSync.spec**: PyInstaller Build-Konfiguration
- **sync_app.ico**: Anwendungs-Icon

### Synchronisierungs-Komponenten
- **calldoc_sqlhk_synchronizer.py**: Hauptkoordinator für bidirektionale Sync
- **patient_synchronizer.py**: Patient-Daten Synchronisation
- **untersuchung_synchronizer.py**: Untersuchung-Daten Synchronisation
- **mssql_api_client.py**: HTTP API Client für SQLHK

### Daten-Interfaces
- **calldoc_interface.py**: CallDoc API Client
- **sqlhk_interface.py**: Direkte SQLHK Datenbank-Anbindung
- **constants.py**: API URLs, Appointment Types, Mappings
- **appointment_types_mapping.py**: Dynamische Typ-Zuordnung

---

## Installation & Benutzung

### Schnellstart - Desktop Shortcut
1. **Doppelklick** auf "CallDoc-SQLHK Sync" auf dem Desktop
2. **API startet automatisch** auf Port 5555
3. **Datum wählen** oder Heute/Morgen Button nutzen
4. **Synchronisieren** klicken
5. **Fortschritt** im Protokoll verfolgen

### GUI-Anwendung (mit integrierter API)
```powershell
# Direkt starten (API läuft automatisch mit)
python sync_gui_qt.py

# Oder über die EXE (API integriert)
CallDocSyncWithAPI.exe
```

### REST API Nutzung (läuft automatisch)

#### NEU: Single-Patient Synchronisation
```powershell
# PowerShell - Einzelnen Patienten synchronisieren
Invoke-RestMethod -Uri "http://localhost:5555/api/sync/patient" `
  -Method POST `
  -Body (@{piz="1698369"; date="2025-10-06"} | ConvertTo-Json) `
  -ContentType "application/json"
```

#### Vollständige Synchronisation
```powershell
# PowerShell - Alle Patienten eines Tages
Invoke-RestMethod -Uri "http://localhost:5555/api/sync" `
  -Method POST `
  -Body '{"date":"2025-08-20","appointment_type_id":24}' `
  -ContentType "application/json"

# Oder mit cURL
curl -X POST http://localhost:5555/api/sync \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-08-20", "appointment_type_id": 24}'
```

### Export-Funktion
```powershell
# Wochenexport
python main.py

# Einzelexport für spezifischen Tag
python appointment_patient_enricher.py --datum 2025-08-20
```

---

## Technische Details

### CallDoc-API
- Zugriff über die `CallDocInterface`-Klasse
- Unterstützt Patienten- und Terminsuche
- Erfordert Datum im Format YYYY-MM-DD

### MS SQL Server API
- Zugriff über die `MsSqlApiClient`-Klasse
- Unterstützt SQL-Ausführung und Upsert-Operationen
- Spezielle Methoden für die Untersuchungstabelle

### Patientenabfrage
- Funktionen in `patient_abfrage.py`
- Unterstützt Abfrage nach PatientID oder M1Ziffer
- Wichtig: Erfordert spezielle Datenbankwechsel-Logik (siehe unten)

### Synchronisierungslogik
- Mapping zwischen CallDoc-Terminen und SQLHK-Untersuchungen
- Vergleich basierend auf externen IDs und relevanten Feldern
- Transaktionsmanagement für atomare Operationen

---

## Erstellung einer .exe (Windows)

### Vorbereitung
```powershell
# Dependencies installieren
pip install -r requirements.txt

# Icon erstellen
python create_simple_icon.py
```

### Build-Prozess
```powershell
# EXE mit PyInstaller erstellen
pyinstaller CallDocSync.spec --noconfirm

# Desktop-Shortcut erstellen
python create_shortcut.py
```

### Ergebnis
- **EXE**: `C:\Users\administrator.PRAXIS\dist\CallDocSync.exe`
- **Desktop-Shortcut**: "CallDoc-SQLHK Sync" mit Icon
- **Standalone**: Keine Python-Installation erforderlich

---

## Patientenabfrage aus SQLHK

### Überblick
Die Funktionen in `patient_abfrage.py` ermöglichen den Abruf von Patientendaten aus der SQLHK-Datenbank anhand der PatientID oder M1Ziffer. Diese Funktionen sind wichtig für die Synchronisierung zwischen CallDoc und SQLHK, da die M1Ziffer als Schlüssel für die Zuordnung dient.

### Verwendung

```python
# Patientenabfrage nach ID
from patient_abfrage import get_patient_by_id

patient = get_patient_by_id(12825)
if patient:
    print(f"Patient gefunden: {patient['Nachname']}, {patient['Vorname']}")
    print(f"M1Ziffer: {patient['M1Ziffer']}")

# Patientenabfrage nach M1Ziffer
from patient_abfrage import get_patient_by_m1ziffer

patient = get_patient_by_m1ziffer(1695672)
if patient:
    print(f"Patient gefunden: {patient['Nachname']}, {patient['Vorname']}")
    print(f"PatientID: {patient['PatientID']}")
```

### Wichtige Hinweise zur Datenbankabfrage

1. **Datenbankwechsel erforderlich**: Die Abfrage erfordert einen expliziten Wechsel zur SQLHK-Datenbank und anschließend zurück zur SuPDatabase.

2. **Dreischrittiges Verfahren**:
   - Erster API-Aufruf: `USE SQLHK;`
   - Zweiter API-Aufruf: Die eigentliche Patientenabfrage
   - Dritter API-Aufruf: `USE SuPDatabase;`

3. **Fehlerbehandlung**: Die Funktionen stellen sicher, dass auch im Fehlerfall ein Rückwechsel zur SuPDatabase erfolgt.

4. **Testbeispiele**: Die Datei enthält Testcode für mehrere PatientIDs (12825, 12844, 5538, 12263, 12830).

### Beispielaufruf

```powershell
python patient_abfrage.py
```

Dies testet die Patientenabfrage für mehrere PatientIDs und speichert die Ergebnisse als JSON-Dateien.

## Wichtige Fixes & Known Issues

### Gelöste Probleme
1. **Appointment Type Filtering**: CallDoc API gibt `appointment_type` zurück, nicht `appointment_type_id` 
   - Fix in sync_gui_qt.py Zeile 143

2. **NoneType Fehler bei Patientendaten**: Robuste None-Checks implementiert
   - Fix in untersuchung_synchronizer.py Zeilen 737-752

3. **SQL Injection Vulnerabilities**: Parametrisierte Queries implementiert
   - Fixes in mehreren Synchronizer-Modulen

4. **Memory Leaks**: Cache-Größen limitiert auf 1000 Einträge
   - Fix in sync_gui_qt.py mit MAX_CACHE_SIZE

### Konfiguration

#### API Endpoints
- **CallDoc API**: `http://192.168.1.76:8001/api/v1/frontend/`
- **SQLHK API**: `http://192.168.1.67:7007/api/`
- **Sync API**: `http://localhost:5555/` (wenn aktiv)

#### Appointment Types
- **24**: Herzkatheteruntersuchung (Standard)
- **1**: Sprechstunde Kardiologie
- **4**: Sprechstunde Pulmologie
- **13**: Herzultraschall
- **44**: Schrittmacherkontrolle

## Automatisierung

### Windows Task Scheduler
```xml
<Actions>
  <Exec>
    <Command>powershell.exe</Command>
    <Arguments>-Command "Invoke-RestMethod -Uri 'http://localhost:5555/api/sync' -Method POST -Body '{\"date\":\"$(Get-Date -Format yyyy-MM-dd)\",\"appointment_type_id\":24}' -ContentType 'application/json'"</Arguments>
  </Exec>
</Actions>
```

### Batch Script für tägliche Sync
```batch
@echo off
FOR /F "tokens=1-3 delims=." %%a IN ('date /t') DO (SET mydate=%%c-%%b-%%a)
curl -X POST http://localhost:5555/api/sync ^
  -H "Content-Type: application/json" ^
  -d "{\"date\":\"%mydate%\",\"appointment_type_id\":24}"
```

## Support & Debugging

### Log-Dateien
- **GUI Logs**: `sync_gui_YYYYMMDD_HHMMSS.log`
- **API Logs**: Konsolen-Output
- **Sync Results**: `sync_result_DATUM_TYP.json`

### Test-Scripts
- `check_database_connection.py` - DB-Verbindung testen
- `check_api_server.py` - API-Status prüfen
- `test_api_simple.py` - API Health Check

---

## Version & Historie
- **Version 2.0**: REST API Integration, moderne GUI mit Dashboard
- **Version 1.0**: Basis-Synchronisation
- **Letztes Update**: 19.08.2025
- **Entwickelt mit**: Claude AI Unterstützung

## Lizenz
Interne Nutzung Praxis Heydoc. Weitergabe oder kommerzielle Nutzung nur nach Rücksprache.
