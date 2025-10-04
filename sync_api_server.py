"""
CallDoc-SQLHK Synchronization API Server

REST API für die automatische Synchronisierung ohne GUI-Interaktion.
Ermöglicht das Triggern der Synchronisierung via HTTP-Request.

Autor: Markus
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
import os
import sys
import signal
from typing import Dict, Any

# Import der Synchronisierungs-Module
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from untersuchung_synchronizer import UntersuchungSynchronizer
from patient_synchronizer import PatientSynchronizer
from single_patient_sync import SinglePatientSynchronizer

# Konfiguration laden
config_file = 'sync_api_config.json'
default_config = {
    "api": {
        "host": "127.0.0.1",
        "port": 5555,
        "debug": False,
        "log_file": "sync_api_server.log",
        "log_level": "INFO",
        "max_workers": 4
    },
    "sync": {
        "default_appointment_type": 24,
        "max_retries": 3
    }
}

config = default_config.copy()
if os.path.exists(config_file):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            config.update(loaded_config)
    except Exception as e:
        print(f"Warnung: Konnte Config nicht laden, nutze Defaults: {e}")

# Logging konfigurieren
log_level = getattr(logging, config['api'].get('log_level', 'INFO'))
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
logger.handlers = []  # Clear existing handlers

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File Handler mit Rotation
log_file = config['api'].get('log_file', 'sync_api_server.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info(f"API Server Config geladen: Host={config['api']['host']}, Port={config['api']['port']}, Log={log_file}")

# Flask App initialisieren
app = Flask(__name__)
if config['api'].get('cors_enabled', True):
    CORS(app)  # Cross-Origin Resource Sharing aktivieren

# Globale Variablen für aktive Synchronisierungen
active_syncs = {}
sync_lock = threading.Lock()
shutdown_event = threading.Event()

# Graceful Shutdown Handler
def signal_handler(sig, frame):
    """Behandelt CTRL+C für sauberes Herunterfahren"""
    logger.info("Shutdown signal empfangen. Beende laufende Tasks...")
    shutdown_event.set()
    
    # Warte auf laufende Tasks
    with sync_lock:
        for task_id, task in active_syncs.items():
            if task.status == "running" and task.thread:
                logger.info(f"Warte auf Task {task_id}...")
                task.thread.join(timeout=10)
    
    logger.info("API Server beendet.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class SyncTask:
    """Repräsentiert eine Synchronisierungs-Aufgabe"""
    
    def __init__(self, task_id: str, date_str: str, appointment_type_id: int = None):
        self.task_id = task_id
        self.date_str = date_str
        self.appointment_type_id = appointment_type_id or config['sync'].get('default_appointment_type', 24)
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.result = {}
        self.error = None
        self.thread = None
        self.cancelled = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Task zu Dictionary für JSON Response"""
        return {
            "task_id": self.task_id,
            "date": self.date_str,
            "appointment_type_id": self.appointment_type_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            "result": self.result,
            "error": self.error
        }


class SinglePatientSyncTask(SyncTask):
    """Repräsentiert eine Single-Patient Synchronisierungs-Aufgabe"""
    
    def __init__(self, task_id: str, date_str: str, piz: str, appointment_type_id: int = None):
        super().__init__(task_id, date_str, appointment_type_id)
        self.piz = piz
        self.sync_type = "single_patient"
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Task zu Dictionary für JSON Response"""
        result = super().to_dict()
        result.update({
            "piz": self.piz,
            "sync_type": self.sync_type
        })
        return result


def run_synchronization(task: SyncTask):
    """
    Führt die Synchronisierung in einem separaten Thread aus.
    """
    try:
        task.status = "running"
        task.start_time = datetime.now()
        logger.info(f"Starte Synchronisierung für Task {task.task_id}: Datum={task.date_str}, Type={task.appointment_type_id}")
        
        # Konvertiere Datum für SQLHK (DD.MM.YYYY)
        date_parts = task.date_str.split('-')
        sqlhk_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        
        # 1. CallDoc Termine abrufen
        logger.info(f"Rufe CallDoc Termine ab für {task.date_str}")
        calldoc_client = CallDocInterface(
            from_date=task.date_str,
            to_date=task.date_str
        )
        
        response = calldoc_client.appointment_search(
            appointment_type_id=task.appointment_type_id
        )
        
        if 'error' in response:
            raise Exception(f"CallDoc API Fehler: {response}")
        
        appointments = response.get('data', [])
        
        # Filter nach appointment_type (mit dem Fix!)
        filtered_appointments = [
            a for a in appointments 
            if a.get('appointment_type') == task.appointment_type_id
        ]
        
        # Filter nach Status (aktive Termine)
        active_appointments = [
            a for a in filtered_appointments 
            if a.get('status') != 'canceled'
        ]
        
        logger.info(f"CallDoc: {len(appointments)} total, {len(filtered_appointments)} gefiltert, {len(active_appointments)} aktiv")
        
        # Patientendaten anreichern
        logger.info("Reichere Termine mit Patientendaten an...")
        patient_cache = {}
        MAX_CACHE_SIZE = 500
        
        for appointment in active_appointments:
            if len(patient_cache) > MAX_CACHE_SIZE:
                patient_cache.clear()
                
            piz = appointment.get("piz")
            if piz and piz not in patient_cache:
                try:
                    patient_response = calldoc_client.get_patient_by_piz(piz)
                    if patient_response and not patient_response.get("error"):
                        patients_list = patient_response.get("patients", [])
                        if patients_list and len(patients_list) > 0 and patients_list[0] is not None:
                            patient_data = patients_list[0]
                            if isinstance(patient_data, dict):
                                patient_cache[piz] = patient_data
                                appointment["patient"] = patient_data
                                logger.info(f"Patient gefunden: {patient_data.get('surname')}, {patient_data.get('name')}")
                except Exception as e:
                    logger.warning(f"Fehler beim Laden der Patientendaten für PIZ {piz}: {str(e)}")
            elif piz in patient_cache:
                appointment["patient"] = patient_cache[piz]
        
        # 2. SQLHK Untersuchungen abrufen
        logger.info(f"Rufe SQLHK Untersuchungen ab für {sqlhk_date}")
        mssql_client = MsSqlApiClient()
        sqlhk_untersuchungen = mssql_client.get_untersuchungen_by_date(sqlhk_date)
        
        logger.info(f"SQLHK: {len(sqlhk_untersuchungen)} Untersuchungen gefunden")
        
        # 3. Patienten synchronisieren
        logger.info("Starte Patienten-Synchronisierung...")
        patient_sync = PatientSynchronizer()
        patient_result = patient_sync.sync_patients_from_appointments(active_appointments)
        
        # 4. Untersuchungen synchronisieren
        logger.info("Starte Untersuchungs-Synchronisierung...")
        
        # Appointment Type Mapping wird intern in UntersuchungSynchronizer geladen
        
        untersuchung_sync = UntersuchungSynchronizer()
        untersuchung_result = untersuchung_sync.synchronize_appointments(
            active_appointments, 
            sqlhk_untersuchungen
        )
        
        # Ergebnis zusammenstellen
        task.result = {
            "calldoc": {
                "total_appointments": len(appointments),
                "filtered_appointments": len(filtered_appointments),
                "active_appointments": len(active_appointments),
                "canceled_appointments": len(filtered_appointments) - len(active_appointments)
            },
            "sqlhk": {
                "existing_untersuchungen": len(sqlhk_untersuchungen)
            },
            "patient_sync": {
                "successful": patient_result.get("successful", 0),
                "failed": patient_result.get("failed", 0),
                "inserted": patient_result.get("inserted", 0),
                "updated": patient_result.get("updated", 0)
            },
            "untersuchung_sync": {
                "inserted": untersuchung_result.get("inserted", 0),
                "updated": untersuchung_result.get("updated", 0),
                "deleted": untersuchung_result.get("deleted", 0),
                "failed": untersuchung_result.get("failed", 0)
            },
            "summary": {
                "total_processed": len(active_appointments),
                "sync_needed": len(active_appointments) - len(sqlhk_untersuchungen)
            }
        }
        
        task.status = "completed"
        task.end_time = datetime.now()
        logger.info(f"Synchronisierung abgeschlossen für Task {task.task_id}")
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.end_time = datetime.now()
        logger.error(f"Fehler bei Synchronisierung für Task {task.task_id}: {str(e)}")
    
    finally:
        # Task aus aktiven Syncs entfernen nach 5 Minuten
        def cleanup():
            import time
            time.sleep(300)  # 5 Minuten warten
            with sync_lock:
                if task.task_id in active_syncs:
                    del active_syncs[task.task_id]
        
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()


def run_single_patient_synchronization_new(task: SinglePatientSyncTask):
    """
    NEUE Implementierung: Führt Single-Patient Synchronisierung mit separater Logik aus.
    Nutzt die komplett unabhängige SinglePatientSynchronizer Klasse.
    """
    try:
        task.status = "running"
        task.start_time = datetime.now()
        logger.info(f"Starte Single-Patient Sync für Task {task.task_id}: PIZ={task.piz}, Datum={task.date_str}")
        
        # Verwende die NEUE, unabhängige Implementierung
        synchronizer = SinglePatientSynchronizer()
        result = synchronizer.sync_single_patient(
            piz=task.piz,
            date_str=task.date_str,
            appointment_type_id=task.appointment_type_id
        )
        
        task.result = result
        task.status = "completed" if result.get("success") else "failed"
        task.end_time = datetime.now()
        
        if result.get("success"):
            logger.info(f"Single-Patient Sync erfolgreich für Task {task.task_id}")
        else:
            logger.error(f"Single-Patient Sync fehlgeschlagen für Task {task.task_id}: {result.get('message')}")
            task.error = result.get("message")
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.end_time = datetime.now()
        logger.error(f"Fehler bei Single-Patient Sync für Task {task.task_id}: {str(e)}")
    
    finally:
        # Task aus aktiven Syncs entfernen nach 5 Minuten
        def cleanup():
            import time
            time.sleep(300)  # 5 Minuten warten
            with sync_lock:
                if task.task_id in active_syncs:
                    del active_syncs[task.task_id]
        
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()


def run_single_patient_synchronization(task: SinglePatientSyncTask):
    """
    Führt die Single-Patient-Synchronisierung in einem separaten Thread aus.
    """
    try:
        task.status = "running"
        task.start_time = datetime.now()
        logger.info(f"Starte Single-Patient-Synchronisierung für Task {task.task_id}: PIZ={task.piz}, Datum={task.date_str}")
        
        # Konvertiere Datum für SQLHK (DD.MM.YYYY)
        date_parts = task.date_str.split('-')
        sqlhk_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        
        # 1. ALLE CallDoc Termine des Tages abrufen (wichtig für korrekte Funktionalität)
        logger.info(f"Rufe ALLE CallDoc Termine ab für {task.date_str}")
        calldoc_client = CallDocInterface(
            from_date=task.date_str,
            to_date=task.date_str
        )
        
        response = calldoc_client.appointment_search(
            appointment_type_id=task.appointment_type_id
        )
        
        if 'error' in response:
            raise Exception(f"CallDoc API Fehler: {response}")
        
        all_appointments = response.get('data', [])
        
        # Filter nach appointment_type
        filtered_appointments = [
            a for a in all_appointments 
            if a.get('appointment_type') == task.appointment_type_id
        ]
        
        # Filter nach Status (aktive Termine)
        active_appointments = [
            a for a in filtered_appointments 
            if a.get('status') != 'canceled'
        ]
        
        # Filtere nach target_piz (der eigentliche Single-Patient-Filter)
        patient_appointments = []
        for app in active_appointments:
            app_piz = app.get("piz")
            if str(app_piz) == str(task.piz):
                patient_appointments.append(app)
        
        logger.info(f"CallDoc: {len(all_appointments)} total, {len(filtered_appointments)} gefiltert, {len(active_appointments)} aktiv, {len(patient_appointments)} für PIZ {task.piz}")
        
        if not patient_appointments:
            logger.warning(f"Keine Termine für PIZ {task.piz} am {task.date_str} gefunden")
            task.result = {
                "message": f"Keine Termine für PIZ {task.piz} gefunden",
                "calldoc": {
                    "total_appointments": len(all_appointments),
                    "filtered_appointments": len(filtered_appointments),
                    "active_appointments": len(active_appointments),
                    "patient_appointments": len(patient_appointments)
                }
            }
            task.status = "completed"
            task.end_time = datetime.now()
            return
        
        # Patientendaten anreichern
        logger.info("Reichere Patient-Termine mit Patientendaten an...")
        for appointment in patient_appointments:
            piz = appointment.get("piz")
            if piz:
                try:
                    patient_response = calldoc_client.get_patient_by_piz(piz)
                    if patient_response and not patient_response.get("error"):
                        patients_list = patient_response.get("patients", [])
                        if patients_list and len(patients_list) > 0 and patients_list[0] is not None:
                            patient_data = patients_list[0]
                            if isinstance(patient_data, dict):
                                appointment["patient"] = patient_data
                                logger.info(f"Patient gefunden: {patient_data.get('surname')}, {patient_data.get('name')}")
                except Exception as e:
                    logger.warning(f"Fehler beim Laden der Patientendaten für PIZ {piz}: {str(e)}")
        
        # 2. SQLHK Untersuchungen abrufen (nur für Vergleich)
        logger.info(f"Rufe SQLHK Untersuchungen ab für {sqlhk_date}")
        mssql_client = MsSqlApiClient()
        sqlhk_untersuchungen = mssql_client.get_untersuchungen_by_date(sqlhk_date)
        
        logger.info(f"SQLHK: {len(sqlhk_untersuchungen)} Untersuchungen gefunden")
        
        # 3. Patienten synchronisieren (nur der eine Patient)
        logger.info(f"Starte Patienten-Synchronisierung für PIZ {task.piz}...")
        patient_sync = PatientSynchronizer()
        patient_result = patient_sync.sync_patients_from_appointments(patient_appointments)
        
        # 4. Untersuchungen synchronisieren (SINGLE-PATIENT-MODUS aktiviert!)
        logger.info(f"Starte Untersuchungs-Synchronisierung für PIZ {task.piz} (Single-Patient-Modus)...")
        
        untersuchung_sync = UntersuchungSynchronizer()
        untersuchung_result = untersuchung_sync.synchronize_appointments(
            patient_appointments,  # Nur die Termine des einen Patienten
            sqlhk_untersuchungen,  # Alle Untersuchungen des Tages (für Vergleich)
            single_patient_mode=True,  # WICHTIG: Verhindert Löschung anderer Patienten
            target_piz=task.piz        # PIZ für zusätzliche Validierung
        )
        
        # Ergebnis zusammenstellen
        task.result = {
            "piz": task.piz,
            "single_patient_mode": True,
            "calldoc": {
                "total_appointments": len(all_appointments),
                "filtered_appointments": len(filtered_appointments),
                "active_appointments": len(active_appointments),
                "patient_appointments": len(patient_appointments)
            },
            "sqlhk": {
                "existing_untersuchungen": len(sqlhk_untersuchungen)
            },
            "patient_sync": {
                "successful": patient_result.get("successful", 0),
                "failed": patient_result.get("failed", 0),
                "inserted": patient_result.get("inserted", 0),
                "updated": patient_result.get("updated", 0)
            },
            "untersuchung_sync": {
                "inserted": untersuchung_result.get("inserted", 0),
                "updated": untersuchung_result.get("updated", 0),
                "deleted": untersuchung_result.get("deleted", 0),  # Sollte 0 sein im Single-Patient-Modus
                "failed": untersuchung_result.get("failed", 0)
            },
            "summary": {
                "patient_processed": len(patient_appointments),
                "safety_note": "Andere Patienten wurden nicht berührt (Single-Patient-Modus)"
            }
        }
        
        task.status = "completed"
        task.end_time = datetime.now()
        logger.info(f"Single-Patient-Synchronisierung abgeschlossen für Task {task.task_id}")
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.end_time = datetime.now()
        logger.error(f"Fehler bei Single-Patient-Synchronisierung für Task {task.task_id}: {str(e)}")
    
    finally:
        # Task aus aktiven Syncs entfernen nach 5 Minuten
        def cleanup():
            import time
            time.sleep(300)  # 5 Minuten warten
            with sync_lock:
                if task.task_id in active_syncs:
                    del active_syncs[task.task_id]
        
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()


# API Endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health Check Endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_syncs": len(active_syncs)
    })


@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """
    Trigger eine Synchronisierung.
    
    Request Body:
    {
        "date": "2025-08-20",  # Format: YYYY-MM-DD
        "appointment_type_id": 24  # Optional, default: 24 (Herzkatheteruntersuchung)
    }
    """
    try:
        data = request.json
        
        # Validierung
        if not data or 'date' not in data:
            return jsonify({
                "error": "Missing required field: date",
                "example": {
                    "date": "2025-08-20",
                    "appointment_type_id": 24
                }
            }), 400
        
        date_str = data['date']
        appointment_type_id = data.get('appointment_type_id', 24)
        
        # Datum validieren
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                "error": "Invalid date format. Use YYYY-MM-DD"
            }), 400
        
        # Task ID generieren
        task_id = f"sync_{date_str}_{appointment_type_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prüfen ob bereits eine Sync für dieses Datum läuft
        with sync_lock:
            running_tasks = [
                t for t in active_syncs.values() 
                if t.date_str == date_str and t.status == "running"
            ]
            if running_tasks:
                return jsonify({
                    "error": "Synchronization already running for this date",
                    "task_id": running_tasks[0].task_id
                }), 409
            
            # Neue Task erstellen
            task = SyncTask(task_id, date_str, appointment_type_id)
            active_syncs[task_id] = task
        
        # Synchronisierung in separatem Thread starten
        thread = threading.Thread(
            target=run_synchronization,
            args=(task,)
        )
        thread.daemon = True
        thread.start()
        task.thread = thread
        
        return jsonify({
            "message": "Synchronization started",
            "task_id": task_id,
            "status_url": f"/api/sync/status/{task_id}"
        }), 202
        
    except Exception as e:
        logger.error(f"Fehler beim Starten der Synchronisierung: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/api/sync/status/<task_id>', methods=['GET'])
def get_sync_status(task_id):
    """
    Abrufen des Status einer Synchronisierungs-Task.
    """
    with sync_lock:
        if task_id not in active_syncs:
            return jsonify({
                "error": "Task not found",
                "task_id": task_id
            }), 404
        
        task = active_syncs[task_id]
        return jsonify(task.to_dict())


@app.route('/api/sync/active', methods=['GET'])
def get_active_syncs():
    """
    Liste aller aktiven Synchronisierungen.
    """
    with sync_lock:
        tasks = [task.to_dict() for task in active_syncs.values()]
    
    return jsonify({
        "count": len(tasks),
        "tasks": tasks
    })


@app.route('/api/sync/cancel/<task_id>', methods=['POST'])
def cancel_sync(task_id):
    """
    Versucht eine laufende Synchronisierung abzubrechen.
    """
    with sync_lock:
        if task_id not in active_syncs:
            return jsonify({
                "error": "Task not found",
                "task_id": task_id
            }), 404
        
        task = active_syncs[task_id]
        if task.status != "running":
            return jsonify({
                "error": f"Task is not running (status: {task.status})",
                "task_id": task_id
            }), 400
        
        # Thread kann nicht sauber abgebrochen werden in Python
        # Markiere als cancelled
        task.status = "cancelled"
        task.end_time = datetime.now()
        
    return jsonify({
        "message": "Cancellation requested",
        "task_id": task_id
    })


@app.route('/api/sync/patient', methods=['POST'])
def sync_single_patient():
    """
    Synchronisiert einen einzelnen Patienten anhand der M1Ziffer (PIZ).
    
    Request Body:
    {
        "date": "2025-08-20",           # Format: YYYY-MM-DD
        "piz": "12345",                 # M1Ziffer des Patienten
        "appointment_type_id": 24       # Optional, default: 24 (Herzkatheteruntersuchung)
    }
    """
    try:
        data = request.json
        
        # Validierung
        if not data or 'date' not in data or 'piz' not in data:
            return jsonify({
                "error": "Missing required fields: date, piz",
                "example": {
                    "date": "2025-08-20",
                    "piz": "12345",
                    "appointment_type_id": 24
                }
            }), 400
        
        date_str = data['date']
        piz = str(data['piz'])
        appointment_type_id = data.get('appointment_type_id', 24)
        
        # Datum validieren
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                "error": "Invalid date format. Use YYYY-MM-DD"
            }), 400
        
        # PIZ validieren
        if not piz or piz.strip() == "":
            return jsonify({
                "error": "PIZ cannot be empty"
            }), 400
        
        # Task ID generieren
        task_id = f"patient_sync_{piz}_{date_str}_{appointment_type_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prüfen ob bereits eine Sync für diesen Patienten an diesem Tag läuft
        with sync_lock:
            running_tasks = [
                t for t in active_syncs.values() 
                if hasattr(t, 'piz') and t.piz == piz and t.date_str == date_str and t.status == "running"
            ]
            if running_tasks:
                return jsonify({
                    "error": "Patient synchronization already running for this date",
                    "task_id": running_tasks[0].task_id
                }), 409
            
            # Neue Task erstellen
            task = SinglePatientSyncTask(task_id, date_str, piz, appointment_type_id)
            active_syncs[task_id] = task
        
        # Synchronisierung in separatem Thread starten
        # WICHTIG: Verwende die NEUE Implementierung!
        thread = threading.Thread(
            target=run_single_patient_synchronization_new,
            args=(task,)
        )
        thread.daemon = True
        thread.start()
        task.thread = thread
        
        return jsonify({
            "message": "Single patient synchronization started",
            "task_id": task_id,
            "piz": piz,
            "date": date_str,
            "status_url": f"/api/sync/status/{task_id}"
        }), 202
        
    except Exception as e:
        logger.error(f"Fehler beim Starten der Patient-Synchronisierung: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500


# Server starten
def start_api_server(port=None, host=None, debug=None):
    """
    Startet den API Server mit Konfiguration aus sync_api_config.json.
    
    Args:
        port: Port auf dem der Server läuft (überschreibt Config)
        host: Host/IP für den Server (überschreibt Config)
        debug: Debug-Modus aktivieren (überschreibt Config)
    """
    # Nutze Config-Werte oder Übergebene Parameter
    final_port = port or config['api'].get('port', 5555)
    final_host = host or config['api'].get('host', '127.0.0.1')
    final_debug = debug if debug is not None else config['api'].get('debug', False)
    
    logger.info(f"=== CallDoc-SQLHK Sync API Server ===")
    logger.info(f"Host: {final_host}")
    logger.info(f"Port: {final_port}")
    logger.info(f"Debug: {final_debug}")
    logger.info(f"Log File: {config['api'].get('log_file', 'sync_api_server.log')}")
    logger.info(f"Config: {config_file if os.path.exists(config_file) else 'Using defaults'}")
    logger.info(f"=====================================")
    
    try:
        app.run(host=final_host, port=final_port, debug=final_debug, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Server durch Benutzer beendet.")
    except Exception as e:
        logger.error(f"Fehler beim Start des Servers: {e}")
        raise


if __name__ == '__main__':
    # Server starten wenn direkt ausgeführt (nutzt Config)
    start_api_server()