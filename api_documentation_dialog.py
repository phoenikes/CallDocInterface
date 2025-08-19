"""
API Dokumentation Dialog für die CallDoc-SQLHK Synchronisierungs-GUI

Zeigt alle verfügbaren API Endpoints mit Beispielen.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTextEdit, QPushButton, QLabel, QGroupBox,
                             QDialogButtonBox, QMessageBox)
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
        """Erstellt die UI für die API Dokumentation"""
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
            status_text = "✅ API Server läuft auf Port 5555"
            status_style = "color: green; font-weight: bold;"
        else:
            status_text = "⚠️ API Server ist nicht aktiv"
            status_style = "color: orange; font-weight: bold;"
            
        status_label = QLabel(status_text)
        status_label.setStyleSheet(status_style)
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # Tab Widget für verschiedene Endpoints
        tabs = QTabWidget()
        
        # Overview Tab
        overview_tab = QTextEdit()
        overview_tab.setReadOnly(True)
        overview_tab.setHtml(self.get_overview_html())
        tabs.addTab(overview_tab, "Übersicht")
        
        # Sync Endpoint Tab
        sync_tab = QTextEdit()
        sync_tab.setReadOnly(True)
        sync_tab.setHtml(self.get_sync_endpoint_html())
        tabs.addTab(sync_tab, "Synchronisierung")
        
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
        
        # Start API Button (wenn nicht läuft)
        if not self.api_running:
            start_btn = QPushButton("API Server starten")
            start_btn.clicked.connect(self.start_api_server)
            button_layout.addWidget(start_btn)
        
        button_layout.addStretch()
        
        # Close Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_overview_html(self):
        """HTML für die Übersicht"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>API Übersicht</h2>
        
        <h3>Base URL</h3>
        <p><code style="background: #f0f0f0; padding: 5px;">http://localhost:5555</code></p>
        
        <h3>Verfügbare Endpoints</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
        <tr style="background: #e0e0e0;">
            <th>Methode</th>
            <th>Endpoint</th>
            <th>Beschreibung</th>
        </tr>
        <tr>
            <td><b>POST</b></td>
            <td>/api/sync</td>
            <td>Startet eine neue Synchronisierung</td>
        </tr>
        <tr>
            <td><b>GET</b></td>
            <td>/api/sync/status/{task_id}</td>
            <td>Ruft den Status einer Synchronisierung ab</td>
        </tr>
        <tr>
            <td><b>GET</b></td>
            <td>/api/sync/active</td>
            <td>Listet alle aktiven Synchronisierungen</td>
        </tr>
        <tr>
            <td><b>POST</b></td>
            <td>/api/sync/cancel/{task_id}</td>
            <td>Bricht eine laufende Synchronisierung ab</td>
        </tr>
        <tr>
            <td><b>GET</b></td>
            <td>/health</td>
            <td>Health Check - Prüft ob API läuft</td>
        </tr>
        </table>
        
        <h3>Authentifizierung</h3>
        <p>Die API benötigt aktuell keine Authentifizierung (nur lokaler Zugriff).</p>
        
        <h3>Response Format</h3>
        <p>Alle Responses sind im JSON Format.</p>
        
        <h3>Fehlerbehandlung</h3>
        <p>Fehler werden mit entsprechenden HTTP Status Codes und einer JSON Error Message zurückgegeben:</p>
        <ul>
            <li><b>400</b> - Bad Request (fehlende oder ungültige Parameter)</li>
            <li><b>404</b> - Not Found (Task ID nicht gefunden)</li>
            <li><b>409</b> - Conflict (Synchronisierung läuft bereits)</li>
            <li><b>500</b> - Internal Server Error</li>
        </ul>
        </body>
        </html>
        """
    
    def get_sync_endpoint_html(self):
        """HTML für den Sync Endpoint"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>POST /api/sync</h2>
        <p>Startet eine neue Synchronisierung für ein bestimmtes Datum.</p>
        
        <h3>Request Body (JSON)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "date": "2025-08-20",           // Pflicht: Datum im Format YYYY-MM-DD
    "appointment_type_id": 24       // Optional: Standard ist 24 (Herzkatheteruntersuchung)
}
        </pre>
        
        <h3>Verfügbare Appointment Types</h3>
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
    "task_id": "sync_2025-08-20_24_20250819165432",
    "status_url": "/api/sync/status/sync_2025-08-20_24_20250819165432"
}
        </pre>
        
        <h3>Error Response (409 Conflict)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "error": "Synchronization already running for this date",
    "task_id": "sync_2025-08-20_24_20250819164521"
}
        </pre>
        
        <h3>Error Response (400 Bad Request)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "error": "Missing required field: date",
    "example": {
        "date": "2025-08-20",
        "appointment_type_id": 24
    }
}
        </pre>
        </body>
        </html>
        """
    
    def get_status_endpoint_html(self):
        """HTML für den Status Endpoint"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>GET /api/sync/status/{task_id}</h2>
        <p>Ruft den aktuellen Status einer Synchronisierungs-Task ab.</p>
        
        <h3>URL Parameter</h3>
        <ul>
            <li><b>task_id</b> - Die Task ID aus der Sync Response</li>
        </ul>
        
        <h3>Success Response (200 OK)</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
{
    "task_id": "sync_2025-08-20_24_20250819165432",
    "date": "2025-08-20",
    "appointment_type_id": 24,
    "status": "completed",  // pending, running, completed, failed, cancelled
    "start_time": "2025-08-19T16:54:32",
    "end_time": "2025-08-19T16:54:45",
    "duration_seconds": 13.5,
    "result": {
        "calldoc": {
            "total_appointments": 30,
            "filtered_appointments": 30,
            "active_appointments": 25,
            "canceled_appointments": 5
        },
        "sqlhk": {
            "existing_untersuchungen": 4
        },
        "patient_sync": {
            "successful": 25,
            "failed": 0,
            "inserted": 1,
            "updated": 24
        },
        "untersuchung_sync": {
            "inserted": 21,
            "updated": 0,
            "deleted": 0,
            "failed": 0
        },
        "summary": {
            "total_processed": 25,
            "sync_needed": 21
        }
    },
    "error": null
}
        </pre>
        
        <h3>Status Werte</h3>
        <table border="1" cellpadding="3" cellspacing="0" style="border-collapse: collapse;">
        <tr><td><b>pending</b></td><td>Task wartet auf Ausführung</td></tr>
        <tr><td><b>running</b></td><td>Synchronisierung läuft</td></tr>
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
        </body>
        </html>
        """
    
    def get_examples_html(self):
        """HTML für Beispiele"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>Verwendungsbeispiele</h2>
        
        <h3>1. Tägliche Synchronisierung für morgen</h3>
        <p>Synchronisiert alle Herzkatheteruntersuchungen für den nächsten Tag:</p>
        <pre style="background: #f0f0f0; padding: 10px;">
POST http://localhost:5555/api/sync
Content-Type: application/json

{
    "date": "2025-08-20",
    "appointment_type_id": 24
}
        </pre>
        
        <h3>2. Status einer laufenden Synchronisierung prüfen</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/api/sync/status/sync_2025-08-20_24_20250819165432
        </pre>
        
        <h3>3. Alle aktiven Synchronisierungen anzeigen</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/api/sync/active
        </pre>
        
        <h3>4. Health Check</h3>
        <pre style="background: #f0f0f0; padding: 10px;">
GET http://localhost:5555/health
        </pre>
        
        <h3>Integration in Scheduler/Cron</h3>
        <p><b>Windows Task Scheduler:</b></p>
        <pre style="background: #f0f0f0; padding: 10px;">
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:5555/api/sync' -Method POST -Body '{\"date\":\"2025-08-20\",\"appointment_type_id\":24}' -ContentType 'application/json'"
        </pre>
        
        <p><b>Linux Cron (täglich um 6:00 Uhr):</b></p>
        <pre style="background: #f0f0f0; padding: 10px;">
0 6 * * * curl -X POST http://localhost:5555/api/sync -H "Content-Type: application/json" -d '{"date":"'$(date +\%Y-\%m-\%d)'","appointment_type_id":24}'
        </pre>
        </body>
        </html>
        """
    
    def get_curl_commands(self):
        """cURL Commands als Text"""
        return """# cURL Command Beispiele für die CallDoc-SQLHK Sync API

# 1. Health Check
curl http://localhost:5555/health

# 2. Synchronisierung starten (für morgen)
curl -X POST http://localhost:5555/api/sync \\
  -H "Content-Type: application/json" \\
  -d '{"date": "2025-08-20", "appointment_type_id": 24}'

# 3. Synchronisierung starten (für heute)
curl -X POST http://localhost:5555/api/sync \\
  -H "Content-Type: application/json" \\
  -d '{"date": "'$(date +%Y-%m-%d)'", "appointment_type_id": 24}'

# 4. Status einer Synchronisierung abfragen
curl http://localhost:5555/api/sync/status/sync_2025-08-20_24_20250819165432

# 5. Alle aktiven Synchronisierungen anzeigen
curl http://localhost:5555/api/sync/active

# 6. Synchronisierung abbrechen
curl -X POST http://localhost:5555/api/sync/cancel/sync_2025-08-20_24_20250819165432

# Windows PowerShell Beispiele:

# Health Check
Invoke-RestMethod -Uri "http://localhost:5555/health" -Method GET

# Synchronisierung starten
$body = @{
    date = "2025-08-20"
    appointment_type_id = 24
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5555/api/sync" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# Status abfragen
Invoke-RestMethod -Uri "http://localhost:5555/api/sync/status/sync_2025-08-20_24_20250819165432" `
    -Method GET
"""
    
    def get_python_code(self):
        """Python Code Beispiele"""
        return '''# Python Beispiele für die CallDoc-SQLHK Sync API

import requests
import json
from datetime import datetime, timedelta

# API Base URL
BASE_URL = "http://localhost:5555"

# 1. Health Check
def check_health():
    """Prüft ob die API läuft"""
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"API Status: {data['status']}")
        print(f"Aktive Syncs: {data['active_syncs']}")
        return True
    return False

# 2. Synchronisierung starten
def start_sync(date_str, appointment_type_id=24):
    """
    Startet eine Synchronisierung
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        appointment_type_id: Termintyp ID (default: 24)
    
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
        print(f"Synchronisierung gestartet: {data['task_id']}")
        return data['task_id']
    else:
        print(f"Fehler: {response.status_code}")
        print(response.json())
        return None

# 3. Status abfragen
def get_status(task_id):
    """Ruft den Status einer Synchronisierung ab"""
    response = requests.get(f"{BASE_URL}/api/sync/status/{task_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        
        if data['status'] == 'completed':
            result = data['result']
            print(f"CallDoc Termine: {result['calldoc']['active_appointments']}")
            print(f"SQLHK Untersuchungen: {result['sqlhk']['existing_untersuchungen']}")
            print(f"Eingefügt: {result['untersuchung_sync']['inserted']}")
            print(f"Aktualisiert: {result['untersuchung_sync']['updated']}")
        elif data['status'] == 'failed':
            print(f"Fehler: {data['error']}")
        
        return data
    else:
        print(f"Fehler beim Abrufen: {response.status_code}")
        return None

# 4. Alle aktiven Synchronisierungen
def get_active_syncs():
    """Listet alle aktiven Synchronisierungen"""
    response = requests.get(f"{BASE_URL}/api/sync/active")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Aktive Synchronisierungen: {data['count']}")
        for task in data['tasks']:
            print(f"  - {task['task_id']}: {task['status']} ({task['date']})")
        return data['tasks']
    return []

# 5. Vollständiger Workflow
def sync_tomorrow():
    """Synchronisiert die Termine für morgen"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Health Check
    if not check_health():
        print("API ist nicht erreichbar!")
        return
    
    # Synchronisierung starten
    task_id = start_sync(tomorrow)
    if not task_id:
        return
    
    # Status überwachen
    import time
    max_attempts = 30
    
    for i in range(max_attempts):
        time.sleep(1)
        status_data = get_status(task_id)
        
        if status_data:
            if status_data['status'] in ['completed', 'failed', 'cancelled']:
                break
    
    print("Synchronisierung abgeschlossen!")

# Beispiel-Aufruf
if __name__ == "__main__":
    # Health Check
    check_health()
    
    # Sync für morgen starten
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    task_id = start_sync(tomorrow, appointment_type_id=24)
    
    # Kurz warten und Status prüfen
    if task_id:
        import time
        time.sleep(2)
        get_status(task_id)
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
            self.parent().start_api_server_requested()
        self.accept()