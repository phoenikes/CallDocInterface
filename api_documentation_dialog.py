"""
API Dokumentation Dialog fuer die CallDoc-SQLHK Synchronisierungs-GUI

Zeigt alle verfuegbaren API Endpoints mit Beispielen.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTextEdit, QPushButton, QLabel, QGroupBox,
                             QDialogButtonBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor


class APIDocumentationDialog(QDialog):
    """
    Modal Dialog der die API Dokumentation anzeigt.
    """

    def __init__(self, parent=None, api_running=False):
        super().__init__(parent)
        self.api_running = api_running
        self.setWindowTitle("API Dokumentation")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.initUI()

    def initUI(self):
        """Erstellt die UI fuer die API Dokumentation"""
        layout = QVBoxLayout()

        # Header
        header_label = QLabel("CallDoc-SQLHK Synchronization REST API")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Status
        if self.api_running:
            status_text = "API Server laeuft auf Port 5555"
            status_style = "color: green; font-weight: bold;"
        else:
            status_text = "API Server ist nicht aktiv"
            status_style = "color: orange; font-weight: bold;"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(status_style)
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)

        # Tab Widget fuer verschiedene Endpoints
        tabs = QTabWidget()

        # Overview Tab
        overview_tab = QTextEdit()
        overview_tab.setReadOnly(True)
        overview_tab.setHtml(self.get_overview_html())
        tabs.addTab(overview_tab, "Uebersicht")

        # Tages-Sync Endpoint Tab
        sync_tab = QTextEdit()
        sync_tab.setReadOnly(True)
        sync_tab.setHtml(self.get_sync_endpoint_html())
        tabs.addTab(sync_tab, "Tages-Sync")

        # Single-Patient Sync Tab (NEU!)
        patient_sync_tab = QTextEdit()
        patient_sync_tab.setReadOnly(True)
        patient_sync_tab.setHtml(self.get_patient_sync_endpoint_html())
        tabs.addTab(patient_sync_tab, "Single-Patient Sync")

        # Status Endpoint Tab
        status_tab = QTextEdit()
        status_tab.setReadOnly(True)
        status_tab.setHtml(self.get_status_endpoint_html())
        tabs.addTab(status_tab, "Status Abfrage")

        # Examples Tab
        examples_tab = QTextEdit()
        examples_tab.setReadOnly(True)
        examples_tab.setHtml(self.get_examples_html())
        tabs.addTab(examples_tab, "Beispiele")

        # cURL Commands Tab
        curl_tab = QTextEdit()
        curl_tab.setReadOnly(True)
        curl_tab.setPlainText(self.get_curl_commands())
        curl_tab.setFont(QFont("Consolas", 10))
        tabs.addTab(curl_tab, "cURL Commands")

        # Python Code Tab
        python_tab = QTextEdit()
        python_tab.setReadOnly(True)
        python_tab.setPlainText(self.get_python_code())
        python_tab.setFont(QFont("Consolas", 10))
        tabs.addTab(python_tab, "Python Code")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        # Copy URL Button
        copy_btn = QPushButton("Base URL kopieren")
        copy_btn.clicked.connect(self.copy_base_url)
        button_layout.addWidget(copy_btn)

        # Start API Button (wenn nicht laeuft)
        if not self.api_running:
            start_btn = QPushButton("API Server starten")
            start_btn.clicked.connect(self.start_api_server)
            button_layout.addWidget(start_btn)

        button_layout.addStretch()

        # Close Button
        close_btn = QPushButton("Schliessen")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_overview_html(self):
        """HTML fuer die Uebersicht"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>API Uebersicht</h2>

        <h3>Base URL</h3>
        <p><code style="background: #f0f0f0; padding: 5px;">http://localhost:5555</code></p>

        <h3>Verfuegbare Endpoints</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr style="background: #e0e0e0;">
            <th>Methode</th>
            <th>Endpoint</th>
            <th>Beschreibung</th>
        </tr>
        <tr>
            <td><b>GET</b></td>
            <td>/health</td>
            <td>Health Check - Prueft ob API laeuft</td>
        </tr>
        <tr style="background: #f9f9f9;">
            <td><b>POST</b></td>
            <td>/api/sync</td>
            <td>Tages-Sync: Synchronisiert ALLE Termine eines Tages</td>
        </tr>
        <tr>
            <td><b>POST</b></td>
            <td><b>/api/sync/patient</b></td>
            <td><b>Single-Patient Sync: Synchronisiert NUR einen Patienten (per M1Ziffer/PIZ)</b></td>
        </tr>
        <tr style="background: #f9f9f9;">
            <td><b>GET</b></td>
            <td>/api/sync/status/{task_id}</td>
            <td>Ruft den Status einer Synchronisierung ab</td>
        </tr>
        <tr>
            <td><b>GET</b></td>
            <td>/api/sync/active</td>
            <td>Listet alle aktiven Synchronisierungen</td>
        </tr>
        <tr style="background: #f9f9f9;">
            <td><b>POST</b></td>
            <td>/api/sync/cancel/{task_id}</td>
            <td>Bricht eine laufende Synchronisierung ab</td>
        </tr>
        </table>

        <h3>Wann welchen Endpoint nutzen?</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr style="background: #e0e0e0;">
            <th>Szenario</th>
            <th>Endpoint</th>
        </tr>
        <tr>
            <td>Morgens alle Herzkatheter-Termine synchronisieren</td>
            <td>POST /api/sync</td>
        </tr>
        <tr style="background: #f9f9f9;">
            <td>Ein Patient wurde gerade in CallDoc angelegt - schnell synchronisieren</td>
            <td>POST /api/sync/patient</td>
        </tr>
        <tr>
            <td>M1 ruft Sync fuer einen spezifischen Patienten auf</td>
            <td>POST /api/sync/patient</td>
        </tr>
        <tr style="background: #f9f9f9;">
            <td>Automatisierung via Windows Task Scheduler</td>
            <td>POST /api/sync</td>
        </tr>
        </table>

        <h3>Authentifizierung</h3>
        <p>Die API benoetigt aktuell keine Authentifizierung (nur lokaler Zugriff empfohlen).</p>

        <h3>Response Format</h3>
        <p>Alle Responses sind im JSON Format.</p>

        <h3>Fehlerbehandlung</h3>
        <ul>
            <li><b>200</b> - OK (erfolgreiche Abfrage)</li>
            <li><b>202</b> - Accepted (Sync gestartet)</li>
            <li><b>400</b> - Bad Request (fehlende oder ungueltige Parameter)</li>
            <li><b>404</b> - Not Found (Task ID nicht gefunden)</li>
            <li><b>409</b> - Conflict (Synchronisierung laeuft bereits)</li>
            <li><b>500</b> - Internal Server Error</li>
        </ul>
        </body>
        </html>
        """

    def get_sync_endpoint_html(self):
        """HTML fuer den Tages-Sync Endpoint"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>POST /api/sync - Tages-Synchronisierung</h2>
        <p>Synchronisiert <b>ALLE</b> Termine eines bestimmten Tages von CallDoc nach SQLHK.</p>

        <h3>Request Body (JSON)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "date": "2026-01-12",           // Pflicht: Datum im Format YYYY-MM-DD
    "appointment_type_id": 24       // Optional: Standard ist 24 (Herzkatheter)
}
        </pre>

        <h3>Verfuegbare Appointment Types</h3>
        <table border="1" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><b>24</b></td><td>Herzkatheteruntersuchung (Standard)</td></tr>
        <tr><td><b>1</b></td><td>Sprechstunde Kardiologie</td></tr>
        <tr><td><b>4</b></td><td>Sprechstunde Pulmologie</td></tr>
        <tr><td><b>13</b></td><td>Herzultraschall</td></tr>
        <tr><td><b>44</b></td><td>Schrittmacherkontrolle</td></tr>
        </table>

        <h3>Success Response (202 Accepted)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "message": "Synchronization started",
    "task_id": "sync_2026-01-12_24_20260110093000",
    "status_url": "/api/sync/status/sync_2026-01-12_24_20260110093000"
}
        </pre>

        <h3>Ergebnis nach Abschluss (GET /api/sync/status/{task_id})</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "status": "completed",
    "duration_seconds": 9.56,
    "result": {
        "calldoc": {
            "total_appointments": 26,
            "active_appointments": 19
        },
        "patient_sync": {
            "updated": 19,
            "inserted": 0
        },
        "untersuchung_sync": {
            "inserted": 17,
            "updated": 2,
            "deleted": 0
        }
    }
}
        </pre>

        <h3>Error Response (409 Conflict)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "error": "Synchronization already running for this date",
    "task_id": "sync_2026-01-12_24_20260110092500"
}
        </pre>
        </body>
        </html>
        """

    def get_patient_sync_endpoint_html(self):
        """HTML fuer den Single-Patient Sync Endpoint"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>POST /api/sync/patient - Single-Patient Sync</h2>
        <p>Synchronisiert <b>NUR EINEN</b> Patienten anhand seiner M1Ziffer (PIZ).</p>

        <div style="background: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50; margin: 10px 0;">
        <b>Vorteile:</b>
        <ul>
            <li>Schnell: Nur ca. 0.3 Sekunden statt 10+ Sekunden</li>
            <li>Sicher: Andere Patienten werden NICHT geloescht oder geaendert</li>
            <li>Gezielt: Ideal fuer M1-Integration oder manuelle Einzelsync</li>
        </ul>
        </div>

        <h3>Request Body (JSON)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "date": "2026-01-12",           // Pflicht: Datum im Format YYYY-MM-DD
    "piz": "1718572",               // Pflicht: M1Ziffer des Patienten
    "appointment_type_id": 24       // Optional: Standard ist 24 (Herzkatheter)
}
        </pre>

        <h3>Success Response (202 Accepted)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "message": "Single patient synchronization started",
    "task_id": "patient_sync_1718572_2026-01-12_24_20260110095114",
    "piz": "1718572",
    "date": "2026-01-12",
    "status_url": "/api/sync/status/patient_sync_1718572_2026-01-12_24_20260110095114"
}
        </pre>

        <h3>Ergebnis nach Abschluss</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "status": "completed",
    "piz": "1718572",
    "sync_type": "single_patient",
    "duration_seconds": 0.29,
    "result": {
        "success": true,
        "message": "Single-Patient erfolgreich synchronisiert",
        "patient": {
            "found": true,
            "name": "Weidemann",
            "vorname": "Anja"
        },
        "stats": {
            "appointments_found": 1,
            "patient_found": true,
            "sqlhk_action": "already_exists"
        },
        "sqlhk_sync": {
            "action": "already_exists",    // oder "created", "updated"
            "untersuchung_id": 22079
        }
    }
}
        </pre>

        <h3>SQLHK Action Werte</h3>
        <table border="1" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><b>created</b></td><td>Neue Untersuchung wurde angelegt</td></tr>
        <tr><td><b>updated</b></td><td>Bestehende Untersuchung wurde aktualisiert</td></tr>
        <tr><td><b>already_exists</b></td><td>Untersuchung existiert bereits (keine Aenderung noetig)</td></tr>
        </table>

        <h3>Error Response (Patient nicht gefunden)</h3>
        <pre style="background: #fff3e0; padding: 10px;">
{
    "status": "completed",
    "result": {
        "success": false,
        "message": "Kein Termin fuer PIZ 9999999 am 2026-01-12 gefunden"
    }
}
        </pre>

        <h3>Typischer Anwendungsfall: M1-Integration</h3>
        <p>Wenn in M1 ein Patient fuer einen HK-Termin markiert wird:</p>
        <pre style="background: #e3f2fd; padding: 10px;">
// M1 ruft auf:
POST http://localhost:5555/api/sync/patient
{
    "date": "2026-01-12",
    "piz": "1718572"
}

// Ergebnis: Patient + Untersuchung in SQLHK angelegt/aktualisiert
        </pre>
        </body>
        </html>
        """

    def get_status_endpoint_html(self):
        """HTML fuer den Status Endpoint"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>GET /api/sync/status/{task_id}</h2>
        <p>Ruft den aktuellen Status einer Synchronisierungs-Task ab.</p>

        <h3>URL Parameter</h3>
        <ul>
            <li><b>task_id</b> - Die Task ID aus der Sync Response</li>
        </ul>

        <h3>Beispiel-Aufruf</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/api/sync/status/sync_2026-01-12_24_20260110093000
        </pre>

        <h3>Success Response (200 OK) - Tages-Sync</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "task_id": "sync_2026-01-12_24_20260110093000",
    "date": "2026-01-12",
    "appointment_type_id": 24,
    "status": "completed",
    "start_time": "2026-01-10T09:30:00",
    "end_time": "2026-01-10T09:30:10",
    "duration_seconds": 9.56,
    "result": {
        "calldoc": {
            "total_appointments": 26,
            "filtered_appointments": 26,
            "active_appointments": 19,
            "canceled_appointments": 7
        },
        "sqlhk": {
            "existing_untersuchungen": 2
        },
        "patient_sync": {
            "successful": 19,
            "failed": 0,
            "inserted": 0,
            "updated": 19
        },
        "untersuchung_sync": {
            "inserted": 17,
            "updated": 2,
            "deleted": 0,
            "failed": 0
        }
    },
    "error": null
}
        </pre>

        <h3>Success Response (200 OK) - Single-Patient Sync</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "task_id": "patient_sync_1718572_2026-01-12_24_20260110095114",
    "piz": "1718572",
    "sync_type": "single_patient",
    "status": "completed",
    "duration_seconds": 0.29,
    "result": {
        "success": true,
        "patient": {"found": true, "name": "Weidemann", "vorname": "Anja"},
        "sqlhk_sync": {"action": "already_exists", "untersuchung_id": 22079}
    }
}
        </pre>

        <h3>Status Werte</h3>
        <table border="1" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><b>pending</b></td><td>Task wartet auf Ausfuehrung</td></tr>
        <tr><td><b>running</b></td><td>Synchronisierung laeuft</td></tr>
        <tr><td><b>completed</b></td><td>Erfolgreich abgeschlossen</td></tr>
        <tr><td><b>failed</b></td><td>Fehler aufgetreten</td></tr>
        <tr><td><b>cancelled</b></td><td>Abgebrochen</td></tr>
        </table>

        <h3>Error Response (404 Not Found)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "error": "Task not found",
    "task_id": "sync_invalid_id"
}
        </pre>

        <h3>Weitere Endpoints</h3>
        <p><b>GET /api/sync/active</b> - Alle aktiven Tasks anzeigen:</p>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "count": 1,
    "tasks": [
        {"task_id": "sync_2026-01-12_24_...", "status": "running", "date": "2026-01-12"}
    ]
}
        </pre>

        <p><b>POST /api/sync/cancel/{task_id}</b> - Task abbrechen</p>
        </body>
        </html>
        """

    def get_examples_html(self):
        """HTML fuer Beispiele"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>Verwendungsbeispiele</h2>

        <h3>1. Health Check</h3>
        <p>Pruefen ob die API laeuft:</p>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/health

Response:
{
    "status": "healthy",
    "timestamp": "2026-01-10T09:30:00",
    "active_syncs": 0
}
        </pre>

        <h3>2. Tages-Sync: Alle Termine synchronisieren</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
POST http://localhost:5555/api/sync
Content-Type: application/json

{
    "date": "2026-01-12",
    "appointment_type_id": 24
}
        </pre>

        <h3>3. Single-Patient Sync: Einen Patienten synchronisieren</h3>
        <pre style="background: #e8f5e9; padding: 10px;">
POST http://localhost:5555/api/sync/patient
Content-Type: application/json

{
    "date": "2026-01-12",
    "piz": "1718572"
}
        </pre>

        <h3>4. Status pruefen</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/api/sync/status/patient_sync_1718572_2026-01-12_24_20260110095114
        </pre>

        <h3>5. Windows Task Scheduler - Taegliche Sync um 6:00 Uhr</h3>
        <p>Batch-Datei erstellen (daily_sync.bat):</p>
        <pre style="background: #fff8e1; padding: 10px;">
@echo off
set TODAY=%date:~6,4%-%date:~3,2%-%date:~0,2%
curl -X POST http://localhost:5555/api/sync ^
  -H "Content-Type: application/json" ^
  -d "{\"date\":\"%TODAY%\",\"appointment_type_id\":24}"
        </pre>

        <h3>6. PowerShell - Sync fuer morgen</h3>
        <pre style="background: #e3f2fd; padding: 10px;">
$tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
$body = @{
    date = $tomorrow
    appointment_type_id = 24
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5555/api/sync" `
    -Method POST -Body $body -ContentType "application/json"
        </pre>

        <h3>7. M1-Integration: Patient nach Terminanlage synchronisieren</h3>
        <pre style="background: #e8f5e9; padding: 10px;">
# Wenn M1 einen neuen HK-Termin anlegt:
$piz = "1718572"  # M1Ziffer aus M1
$datum = "2026-01-12"

$body = @{
    date = $datum
    piz = $piz
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5555/api/sync/patient" `
    -Method POST -Body $body -ContentType "application/json"
        </pre>
        </body>
        </html>
        """

    def get_curl_commands(self):
        """cURL Commands als Text"""
        return """# =============================================================
# cURL Command Beispiele fuer die CallDoc-SQLHK Sync API
# =============================================================

# -------------------------------------------------------------
# 1. HEALTH CHECK
# -------------------------------------------------------------
curl http://localhost:5555/health

# -------------------------------------------------------------
# 2. TAGES-SYNCHRONISIERUNG (alle Termine eines Tages)
# -------------------------------------------------------------

# Sync fuer ein bestimmtes Datum
curl -X POST http://localhost:5555/api/sync \\
  -H "Content-Type: application/json" \\
  -d '{"date": "2026-01-12", "appointment_type_id": 24}'

# Sync fuer heute (Linux/Mac)
curl -X POST http://localhost:5555/api/sync \\
  -H "Content-Type: application/json" \\
  -d '{"date": "'$(date +%Y-%m-%d)'", "appointment_type_id": 24}'

# -------------------------------------------------------------
# 3. SINGLE-PATIENT SYNC (nur ein Patient per M1Ziffer)
# -------------------------------------------------------------

# Einen Patienten synchronisieren
curl -X POST http://localhost:5555/api/sync/patient \\
  -H "Content-Type: application/json" \\
  -d '{"date": "2026-01-12", "piz": "1718572"}'

# Mit appointment_type_id
curl -X POST http://localhost:5555/api/sync/patient \\
  -H "Content-Type: application/json" \\
  -d '{"date": "2026-01-12", "piz": "1718572", "appointment_type_id": 24}'

# -------------------------------------------------------------
# 4. STATUS ABFRAGEN
# -------------------------------------------------------------

# Tages-Sync Status
curl http://localhost:5555/api/sync/status/sync_2026-01-12_24_20260110093000

# Single-Patient Status
curl http://localhost:5555/api/sync/status/patient_sync_1718572_2026-01-12_24_20260110095114

# Alle aktiven Syncs
curl http://localhost:5555/api/sync/active

# -------------------------------------------------------------
# 5. SYNC ABBRECHEN
# -------------------------------------------------------------
curl -X POST http://localhost:5555/api/sync/cancel/sync_2026-01-12_24_20260110093000


# =============================================================
# WINDOWS PowerShell Beispiele
# =============================================================

# Health Check
Invoke-RestMethod -Uri "http://localhost:5555/health" -Method GET

# Tages-Sync
$body = @{date = "2026-01-12"; appointment_type_id = 24} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5555/api/sync" -Method POST -Body $body -ContentType "application/json"

# Single-Patient Sync
$body = @{date = "2026-01-12"; piz = "1718572"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5555/api/sync/patient" -Method POST -Body $body -ContentType "application/json"

# Status abfragen
Invoke-RestMethod -Uri "http://localhost:5555/api/sync/status/patient_sync_1718572_2026-01-12_24_20260110095114" -Method GET


# =============================================================
# WINDOWS CMD Beispiele (ohne PowerShell)
# =============================================================

# Tages-Sync
curl -X POST http://localhost:5555/api/sync -H "Content-Type: application/json" -d "{\"date\":\"2026-01-12\",\"appointment_type_id\":24}"

# Single-Patient Sync
curl -X POST http://localhost:5555/api/sync/patient -H "Content-Type: application/json" -d "{\"date\":\"2026-01-12\",\"piz\":\"1718572\"}"
"""

    def get_python_code(self):
        """Python Code Beispiele"""
        return '''# =============================================================
# Python Beispiele fuer die CallDoc-SQLHK Sync API
# =============================================================

import requests
import json
from datetime import datetime, timedelta
import time

# API Base URL
BASE_URL = "http://localhost:5555"


# -------------------------------------------------------------
# 1. HEALTH CHECK
# -------------------------------------------------------------
def check_health():
    """Prueft ob die API laeuft"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data['status']}")
            print(f"Aktive Syncs: {data['active_syncs']}")
            return True
    except requests.RequestException as e:
        print(f"API nicht erreichbar: {e}")
    return False


# -------------------------------------------------------------
# 2. TAGES-SYNCHRONISIERUNG
# -------------------------------------------------------------
def sync_day(date_str, appointment_type_id=24):
    """
    Synchronisiert ALLE Termine eines Tages.

    Args:
        date_str: Datum im Format YYYY-MM-DD
        appointment_type_id: Termintyp ID (default: 24 = Herzkatheter)

    Returns:
        task_id oder None bei Fehler
    """
    payload = {
        "date": date_str,
        "appointment_type_id": appointment_type_id
    }

    response = requests.post(
        f"{BASE_URL}/api/sync",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 202:
        data = response.json()
        print(f"Tages-Sync gestartet: {data['task_id']}")
        return data['task_id']
    else:
        print(f"Fehler {response.status_code}: {response.json()}")
        return None


# -------------------------------------------------------------
# 3. SINGLE-PATIENT SYNC (NEU!)
# -------------------------------------------------------------
def sync_patient(date_str, piz, appointment_type_id=24):
    """
    Synchronisiert NUR EINEN Patienten anhand der M1Ziffer.

    Args:
        date_str: Datum im Format YYYY-MM-DD
        piz: M1Ziffer des Patienten
        appointment_type_id: Termintyp ID (default: 24)

    Returns:
        task_id oder None bei Fehler
    """
    payload = {
        "date": date_str,
        "piz": str(piz),
        "appointment_type_id": appointment_type_id
    }

    response = requests.post(
        f"{BASE_URL}/api/sync/patient",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 202:
        data = response.json()
        print(f"Single-Patient Sync gestartet fuer PIZ {piz}: {data['task_id']}")
        return data['task_id']
    else:
        print(f"Fehler {response.status_code}: {response.json()}")
        return None


# -------------------------------------------------------------
# 4. STATUS ABFRAGEN
# -------------------------------------------------------------
def get_status(task_id):
    """Ruft den Status einer Synchronisierung ab"""
    response = requests.get(f"{BASE_URL}/api/sync/status/{task_id}")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")

        if data['status'] == 'completed':
            result = data.get('result', {})

            # Unterscheide zwischen Tages-Sync und Single-Patient
            if data.get('sync_type') == 'single_patient':
                print(f"Patient: {result.get('patient', {}).get('name')}")
                print(f"Aktion: {result.get('sqlhk_sync', {}).get('action')}")
            else:
                print(f"CallDoc Termine: {result.get('calldoc', {}).get('active_appointments')}")
                print(f"Eingefuegt: {result.get('untersuchung_sync', {}).get('inserted')}")
                print(f"Aktualisiert: {result.get('untersuchung_sync', {}).get('updated')}")

        elif data['status'] == 'failed':
            print(f"Fehler: {data.get('error')}")

        return data
    else:
        print(f"Task nicht gefunden: {task_id}")
        return None


# -------------------------------------------------------------
# 5. WARTEN BIS FERTIG
# -------------------------------------------------------------
def wait_for_completion(task_id, timeout_seconds=60):
    """Wartet bis ein Task abgeschlossen ist"""
    start = time.time()

    while time.time() - start < timeout_seconds:
        data = get_status(task_id)
        if data and data['status'] in ['completed', 'failed', 'cancelled']:
            return data
        time.sleep(1)

    print("Timeout erreicht!")
    return None


# -------------------------------------------------------------
# BEISPIEL-AUFRUFE
# -------------------------------------------------------------
if __name__ == "__main__":
    # 1. Health Check
    if not check_health():
        print("API nicht erreichbar - beende.")
        exit(1)

    print("\\n" + "="*50)

    # 2. Single-Patient Sync (schnell, ~0.3 Sekunden)
    print("\\nStarte Single-Patient Sync...")
    task_id = sync_patient("2026-01-12", "1718572")
    if task_id:
        time.sleep(1)
        get_status(task_id)

    print("\\n" + "="*50)

    # 3. Tages-Sync (alle Termine, ~10 Sekunden)
    print("\\nStarte Tages-Sync...")
    task_id = sync_day("2026-01-12")
    if task_id:
        result = wait_for_completion(task_id, timeout_seconds=30)
        if result:
            print(f"\\nSync abgeschlossen in {result.get('duration_seconds', 0):.2f} Sekunden")
'''

    def copy_base_url(self):
        """Kopiert die Base URL in die Zwischenablage"""
        clipboard = QApplication.clipboard()
        clipboard.setText("http://localhost:5555")
        QMessageBox.information(self, "Kopiert", "Base URL wurde in die Zwischenablage kopiert!")

    def start_api_server(self):
        """Versucht den API Server zu starten"""
        # Signal an Parent senden
        if self.parent():
            self.parent().start_api_server()
        self.accept()
