# 📋 TASK: Single-Patient Synchronization API

## 🎯 PROJEKTZIEL
Entwicklung einer REST API zur Synchronisierung einzelner Patienten von CallDoc nach SQLHK basierend auf M1Ziffer und Datum.

## ✅ ANFORDERUNGEN
- **EINE EXE**: Integriert in sync_gui_qt.exe
- **API Port**: 5555 (läuft mit GUI)
- **Methode**: POST mit JSON Body
- **Timeout**: Max 60 Sekunden
- **KEINE Änderungen** an bestehenden Sync-Funktionen
- **KEINE Löschung** anderer Patienten

---

## 📝 IMPLEMENTIERUNGS-TASKS

### PHASE 1: API-Entwicklung
- [ ] **Task 1.1**: Neue Datei `single_patient_sync.py` erstellen
  - Komplett separate Implementierung
  - Keine Abhängigkeiten zu bestehenden Sync-Methoden
  - Eigene Klasse `SinglePatientSynchronizer`

- [ ] **Task 1.2**: API-Endpoint in `sync_api_server.py` hinzufügen
  ```python
  @app.route('/api/sync/patient', methods=['POST'])
  def trigger_single_patient_sync():
      # Input: {"piz": "1234567", "date": "2025-10-06"}
      # Output: {"task_id": "...", "status_url": "..."}
  ```

- [ ] **Task 1.3**: Status-Endpoint erweitern
  ```python
  GET /api/sync/status/{task_id}
  # Detailliertes Feedback mit Progress
  ```

### PHASE 2: Core-Funktionalität
- [ ] **Task 2.1**: Patientensuche implementieren
  ```python
  def fetch_patient_appointments(date: str, piz: str):
      # 1. Alle Termine des Tages aus CallDoc
      # 2. Filter auf target PIZ
      # 3. Patientendaten anreichern
  ```

- [ ] **Task 2.2**: SQLHK-Synchronisation
  ```python
  def sync_to_sqlhk(patient_data, appointments):
      # 1. Patient in SQLHK suchen/anlegen
      # 2. Untersuchung INSERT oder UPDATE
      # 3. KEINE DELETE Operation!
  ```

- [ ] **Task 2.3**: Fehlerbehandlung
  - Patient nicht gefunden
  - Keine Termine vorhanden
  - Datenbank-Fehler
  - Timeout-Handling

### PHASE 3: GUI-Integration
- [ ] **Task 3.1**: API-Server Auto-Start in `sync_gui_qt.py`
  ```python
  def __init__(self):
      super().__init__()
      # ... GUI Code ...
      # API Server starten
      self.start_api_server_background()
  ```

- [ ] **Task 3.2**: Status-Anzeige in GUI
  - Neues Panel für API-Requests
  - Live-Anzeige laufender Single-Patient-Syncs
  - Fehler-Log

### PHASE 4: Testing
- [ ] **Task 4.1**: Testdaten vorbereiten
  - Datum: **06.10.2025**
  - Patient aus vorhandenen Daten wählen
  - M1Ziffer extrahieren

- [ ] **Task 4.2**: Test-Szenarios
  ```python
  # Test 1: Erfolgreicher Sync
  POST /api/sync/patient
  {"piz": "REAL_PIZ", "date": "2025-10-06"}
  
  # Test 2: Patient nicht vorhanden
  {"piz": "9999999", "date": "2025-10-06"}
  
  # Test 3: Keine Termine
  {"piz": "REAL_PIZ", "date": "2025-12-31"}
  
  # Test 4: Parallel-Requests
  # Zwei Requests für verschiedene Patienten
  ```

- [ ] **Task 4.3**: Performance-Test
  - Response-Zeit < 5 Sekunden
  - Timeout-Test bei 60 Sekunden

### PHASE 5: Build & Deployment
- [ ] **Task 5.1**: PyInstaller Build
  ```bash
  pyinstaller --onefile --windowed \
    --name sync_gui_qt \
    --add-data "single_patient_sync.py;." \
    --exclude-module PyQt6 \
    sync_gui_qt.py
  ```

- [ ] **Task 5.2**: EXE Testing
  - GUI startet
  - API läuft auf Port 5555
  - Single-Patient Sync funktioniert
  - GUI schließen = API stoppt

---

## 🔄 API-SPEZIFIKATION

### Request:
```http
POST http://localhost:5555/api/sync/patient
Content-Type: application/json

{
    "piz": "1234567",        # M1Ziffer (required)
    "date": "2025-10-06",    # Format: YYYY-MM-DD (required)
    "appointment_type_id": 24 # Optional, default: 24
}
```

### Response (Success):
```json
{
    "message": "Single patient synchronization started",
    "task_id": "patient_sync_1234567_2025-10-06_20251004150000",
    "status_url": "/api/sync/status/patient_sync_1234567_2025-10-06_20251004150000"
}
```

### Status Response:
```json
{
    "task_id": "patient_sync_1234567_2025-10-06_20251004150000",
    "status": "completed",
    "execution_time_ms": 2350,
    "patient": {
        "piz": "1234567",
        "found": true,
        "name": "Mustermann",
        "vorname": "Max"
    },
    "appointments": {
        "found": 1,
        "processed": 1
    },
    "sqlhk_sync": {
        "action": "created",
        "untersuchung_id": 12345
    },
    "error": null
}
```

---

## 🧪 TEST-PLAN MIT 06.10.2025

### Schritt 1: Testpatient identifizieren
```python
# Vorhandene Termine für 06.10.2025 prüfen
calldoc_client = CallDocInterface("2025-10-06", "2025-10-06")
appointments = calldoc_client.appointment_search(appointment_type_id=24)
# Ersten Patient mit Termin wählen
test_piz = appointments['data'][0]['piz']
```

### Schritt 2: API-Test
```python
import requests
import time

# Single-Patient Sync starten
response = requests.post(
    "http://localhost:5555/api/sync/patient",
    json={"piz": test_piz, "date": "2025-10-06"}
)
task_id = response.json()['task_id']

# Status polling
for i in range(30):
    status = requests.get(f"http://localhost:5555/api/sync/status/{task_id}")
    if status.json()['status'] in ['completed', 'failed']:
        print(status.json())
        break
    time.sleep(2)
```

### Schritt 3: Validierung
- [ ] Patient wurde in SQLHK gefunden/angelegt
- [ ] Untersuchung wurde korrekt erstellt
- [ ] Andere Patienten am 06.10.2025 unverändert
- [ ] Response-Zeit < 5 Sekunden

---

## 🚦 FREIGABE-CHECKLISTE

### Vor Implementierung:
- [ ] Konzept verstanden und akzeptiert?
- [ ] Test mit 06.10.2025 Daten okay?
- [ ] Keine Änderungen an bestehenden Funktionen bestätigt?

### Nach Implementierung:
- [ ] Code Review durchgeführt
- [ ] Alle Tests bestanden
- [ ] API-Dokumentation vollständig
- [ ] EXE erfolgreich gebaut und getestet

### Test-Agent Aufgaben:
1. **Unit-Tests** für SinglePatientSynchronizer
2. **Integration-Tests** für API-Endpoints
3. **End-to-End-Test** mit echten 06.10.2025 Daten
4. **Performance-Tests** (Response < 5s)
5. **Fehlerfall-Tests** (nicht existente PIZ, etc.)

---

## 📊 ERFOLGS-KRITERIEN

✅ **Funktional:**
- Single-Patient wird korrekt synchronisiert
- Keine Beeinflussung anderer Patienten
- Fehlerbehandlung funktioniert

✅ **Technisch:**
- Eine EXE mit integrierter API
- Response-Zeit < 5 Sekunden
- Timeout bei 60 Sekunden

✅ **Qualität:**
- Keine Änderungen an bestehenden Funktionen
- Saubere Fehler-Messages
- Vollständige Logging

---

## 🛠️ BENÖTIGTE DATEIEN

1. **Neue Dateien:**
   - `single_patient_sync.py` (neue Implementierung)

2. **Zu erweitern:**
   - `sync_api_server.py` (neue Endpoints)
   - `sync_gui_qt.py` (API Auto-Start)

3. **Unverändert:**
   - `untersuchung_synchronizer.py` ✅
   - `patient_synchronizer.py` ✅
   - `calldoc_interface.py` ✅
   - `mssql_api_client.py` ✅

---

## 📅 ZEITPLAN

- **Phase 1-2**: 2 Tage (API-Entwicklung)
- **Phase 3**: 1 Tag (GUI-Integration)
- **Phase 4**: 1 Tag (Testing)
- **Phase 5**: 0.5 Tage (Build)

**Gesamt: ~4.5 Tage**

---

## ⚠️ RISIKEN & MITIGATION

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| Bestehende Funktionen brechen | Niedrig | Separate Implementierung |
| Performance > 5s | Mittel | Direkte SQL-Queries |
| Race Conditions | Niedrig | Task-Locking |
| EXE Build-Fehler | Niedrig | Bereits getestet |

---

## 🔐 STATUS: BEREIT ZUR FREIGABE

**Dieser Plan wartet auf Ihre Freigabe zur Implementierung.**