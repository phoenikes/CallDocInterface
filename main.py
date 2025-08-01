"""
Hauptmodul für den CallDoc-Export.

- Unterstützt Wochen- und Einzel-Tages-Export auf Basis von Konfigurationsdateien.
- Beim Start ohne Argumente werden automatisch alle config*.json im aktuellen Verzeichnis verarbeitet.
- Fehler werden abgefangen und ausgegeben, das Fenster bleibt am Ende offen.

Benutzung:
- Per Doppelklick oder Kommandozeile starten. Standardmäßig werden alle config*.json verarbeitet.
- Alternativ können gezielt Konfigurationsdateien als Argumente übergeben werden:
    main.exe config.json config2.json

Konfigurationsbeispiele siehe README.md
"""
import schedule
import time
import sys
import requests
import json
from datetime import datetime, timedelta
from constants import (
    PATIENT_SEARCH_URL,
    APPOINTMENT_SEARCH_URL,
    APPOINTMENT_TYPES,
    DOCTORS,
    ROOMS
)
import logging
import glob
from weekly_appointment_exporter import WeeklyAppointmentExporter
from calldoc_interface import CallDocInterface  # Import aus separatem Modul
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer  # Import des neuen Synchronizers
from patient_synchronizer import PatientSynchronizer  # Import des PatientSynchronizer

# Globale Konfiguration laden
with open("config.json", "r", encoding="utf-8") as f:
    global_config = json.load(f)

# Logging-Konfiguration
logging.basicConfig(
    filename=global_config.get("log_file", "calldoc_export.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8"
)

# Scheduler-Konfiguration auslesen
scheduler_config = global_config.get("scheduler", {})
interval_hours = scheduler_config.get("interval_hours", 6)
run_on_startup = scheduler_config.get("run_on_startup", True)


def print_formatted_json(data):
    """Hilfsfunktion zur formatierten Ausgabe von JSON-Daten"""
    print(json.dumps(data, indent=4, ensure_ascii=False))


def enrich_appointments_with_patients(from_date, to_date, appointment_type_id=24, output_path=None):
    """Sucht Termine und ergänzt Patientendaten direkt, optional Speicherung als JSON."""
    interface = CallDocInterface(from_date=from_date, to_date=to_date)
    result = interface.appointment_search(appointment_type_id=appointment_type_id)
    piz_set = set()
    for appt in result.get("data", []):
        piz = appt.get("piz")
        if piz and piz not in piz_set:
            patient_data = interface.get_patient_by_piz(piz)
            last_name = first_name = date_of_birth = None
            if patient_data and isinstance(patient_data, dict):
                patients_list = patient_data.get("patients")
                if patients_list and isinstance(patients_list, list) and len(patients_list) > 0:
                    pat = patients_list[0]
                    last_name = pat.get("surname")
                    first_name = pat.get("name")
                    date_of_birth = pat.get("date_of_birth")
            appt["last_name"] = last_name
            appt["first_name"] = first_name
            appt["date_of_birth"] = date_of_birth
            piz_set.add(piz)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"Ergebnis wurde nach {output_path} geschrieben.")
    return result


def get_next_monday():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return next_monday.strftime("%Y-%m-%d")


def run_calldoc_sqlhk_comparison(date_str=None, appointment_type_id=None, doctor_id=None, room_id=None, status=None):
    """
    Führt einen Vergleich zwischen CallDoc-Terminen und SQLHK-Untersuchungen durch.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD oder DD.MM.YYYY (Standard: aktuelles Datum)
        appointment_type_id: ID des Termintyps (Standard: HERZKATHETERUNTERSUCHUNG)
        doctor_id: Optional, ID des Arztes
        room_id: Optional, ID des Raums
        status: Optional, expliziter Status-Filter (überschreibt smart_status_filter)
        
    Returns:
        Dictionary mit den Ergebnissen des Vergleichs
    """


def run_patient_synchronization(date_str=None, appointment_type_id=None, doctor_id=None, room_id=None, status=None):
    """
    Führt eine Synchronisation der Patientendaten zwischen CallDoc und SQLHK durch.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD (Standard: aktuelles Datum)
        appointment_type_id: ID des Termintyps (Standard: HERZKATHETERUNTERSUCHUNG)
        doctor_id: Optional, ID des Arztes
        room_id: Optional, ID des Raums
        status: Optional, expliziter Status-Filter (überschreibt smart_status_filter)
        
    Returns:
        Dictionary mit den Ergebnissen der Synchronisation
    """
    # Logger initialisieren
    logger = logging.getLogger(__name__)
    
    # Standardwerte setzen
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    if appointment_type_id is None:
        appointment_type_id = APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"]
    
    # PatientSynchronizer initialisieren
    patient_synchronizer = PatientSynchronizer()
    
    # Termine direkt über den Synchronizer abrufen
    # Wir verwenden die Methode get_calldoc_appointments aus dem CallDocSQLHKSynchronizer
    synchronizer = CallDocSQLHKSynchronizer()
    appointments = synchronizer.get_calldoc_appointments(
        date_str=date_str,
        filter_by_type_id=appointment_type_id,
        doctor_id=doctor_id,
        room_id=room_id,
        status=status,
        smart_status_filter=True
    )
    
    # Wenn keine Termine gefunden wurden, leere Ergebnisse zurückgeben
    if not appointments or len(appointments) == 0:
        logger.warning(f"Keine Termine für das Datum {date_str} gefunden.")
        return {
            "total": 0,
            "success": 0,
            "error": 0,
            "updated": 0,
            "inserted": 0,
            "output_file": None
        }
    
    logger.info(f"{len(appointments)} Termine für die Patienten-Synchronisation gefunden.")
    
    # Patienten aus den Terminen synchronisieren
    sync_results = patient_synchronizer.synchronize_patients_from_appointments(appointments)
    
    # Ergebnisse in einem einheitlichen Format zurückgeben
    return {
        "total": sync_results.get("total", 0),
        "success": sync_results.get("success", 0),
        "error": sync_results.get("failed", 0),
        "updated": sync_results.get("updated", 0),
        "inserted": sync_results.get("inserted", 0),
        "output_file": sync_results.get("output_file", None)
    }


def run_export():
    """Führt den Export-Prozess aus (ursprünglicher main-Code)"""
    try:
        if len(sys.argv) > 1:
            config_files = sys.argv[1:]
        else:
            # Alle config*.json im aktuellen Verzeichnis verwenden
            config_files = sorted(glob.glob("config*.json"))
            if not config_files:
                print("Keine Konfigurationsdateien (config*.json) gefunden!")
                return

        for config_file in config_files:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Einzel-Tag-Export, falls from_date und to_date gesetzt sind
            if config.get("from_date") and config.get("to_date"):
                from_date = config["from_date"]
                to_date = config["to_date"]
                print(f"Starte Einzel-Tages-Export für {config_file}: {from_date}")
                enrich_appointments_with_patients(
                    from_date=from_date,
                    to_date=to_date,
                    appointment_type_id=config["appointment_type_id"],
                    output_path=f"{config.get('export_directory', '.')}/{from_date}_{to_date}_{config['appointment_type_id']}_{config.get('doctor_id', 'none')}_{config.get('room_id', 'none')}.json"
                )
                logging.info(f"Einzeltag-Export abgeschlossen für {config_file}.")
                continue

            # Wochen-Export (Standard)
            week_offset = config.get("week_offset", 0)
            week_start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) + week_offset * 7)
            week_start_str = week_start.strftime("%Y-%m-%d")
            exporter = WeeklyAppointmentExporter(
                week_start=week_start_str,
                appointment_type_id=config["appointment_type_id"],
                doctor_id=config.get("doctor_id"),
                room_id=config.get("room_id"),
                skip_holidays=config.get("skip_holidays", True),
                export_directory=config.get("export_directory"),
                country=config.get("country", "DE"),
                subdiv=config.get("subdiv", "BY")
            )
            print(f"Starte Export für Config: {config_file}")
            exporter.export_week()
            logging.info(f"Wochexport abgeschlossen für {config_file}.")

        print(f"Export abgeschlossen um {datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        print("Fehler beim Export:", e)
        logging.error(f"Fehler beim Export: {e}")
        import traceback
        traceback.print_exc()


def parse_command_line_args():
    """
    Parst die Kommandozeilenargumente und führt die entsprechende Aktion aus.
    """
    if len(sys.argv) > 1:
        # Prüfen, ob ein Vergleich oder eine Patienten-Synchronisation durchgeführt werden soll
        if sys.argv[1] in ["vergleich", "patienten-sync"]:
            # Parameter für den Vergleich oder die Synchronisation extrahieren
            date_str = None
            appointment_type_id = None
            doctor_id = None
            room_id = None
            status = None
            
            # Argumente parsen
            i = 2
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg == "--datum" and i + 1 < len(sys.argv):
                    date_str = sys.argv[i + 1]
                    i += 2
                elif arg == "--termintyp" and i + 1 < len(sys.argv):
                    try:
                        appointment_type_id = int(sys.argv[i + 1])
                    except ValueError:
                        # Versuche, den Namen des Termintyps zu verwenden
                        typ_name = sys.argv[i + 1].upper()
                        if typ_name in APPOINTMENT_TYPES:
                            appointment_type_id = APPOINTMENT_TYPES[typ_name]
                        else:
                            print(f"Unbekannter Termintyp: {sys.argv[i + 1]}")
                            print("Verfügbare Termintypen:")
                            for name, id in APPOINTMENT_TYPES.items():
                                print(f"  {name}: {id}")
                            return
                    i += 2
                elif arg == "--arzt" and i + 1 < len(sys.argv):
                    try:
                        doctor_id = int(sys.argv[i + 1])
                    except ValueError:
                        # Versuche, den Namen des Arztes zu verwenden
                        arzt_name = sys.argv[i + 1].upper()
                        if arzt_name in DOCTORS:
                            doctor_id = DOCTORS[arzt_name]
                        else:
                            print(f"Unbekannter Arzt: {sys.argv[i + 1]}")
                            print("Verfügbare Ärzte:")
                            for name, id in DOCTORS.items():
                                print(f"  {name}: {id}")
                            return
                    i += 2
                elif arg == "--raum" and i + 1 < len(sys.argv):
                    try:
                        room_id = int(sys.argv[i + 1])
                    except ValueError:
                        # Versuche, den Namen des Raums zu verwenden
                        raum_name = sys.argv[i + 1].upper()
                        if raum_name in ROOMS:
                            room_id = ROOMS[raum_name]
                        else:
                            print(f"Unbekannter Raum: {sys.argv[i + 1]}")
                            print("Verfügbare Räume:")
                            for name, id in ROOMS.items():
                                print(f"  {name}: {id}")
                            return
                    i += 2
                elif arg == "--status" and i + 1 < len(sys.argv):
                    status = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            # Vergleich oder Patienten-Synchronisation durchführen
            if sys.argv[1] == "vergleich":
                run_calldoc_sqlhk_comparison(
                    date_str=date_str,
                    appointment_type_id=appointment_type_id,
                    doctor_id=doctor_id,
                    room_id=room_id,
                    status=status
                )
            elif sys.argv[1] == "patienten-sync":
                print("Starte Patienten-Synchronisation...")
                results = run_patient_synchronization(
                    date_str=date_str,
                    appointment_type_id=appointment_type_id,
                    doctor_id=doctor_id,
                    room_id=room_id,
                    status=status
                )
                # Ergebnisse ausgeben
                print("\nErgebnisse der Patienten-Synchronisation:")
                print(f"Insgesamt verarbeitete Patienten: {results.get('total', 0)}")
                print(f"Erfolgreich synchronisiert: {results.get('success', 0)}")
                print(f"Fehler: {results.get('error', 0)}")
                print(f"Aktualisiert: {results.get('updated', 0)}")
                print(f"Neu eingefügt: {results.get('inserted', 0)}")
                print(f"Details wurden gespeichert in: {results.get('output_file', 'keine Datei') or 'keine Datei'}")
            return
    
    # Standardverhalten: Export-Scheduler starten
    return False


if __name__ == "__main__":
    # Prüfen, ob spezielle Kommandozeilenargumente vorhanden sind
    if parse_command_line_args() is not False:
        # Kommandozeilenargumente wurden verarbeitet, Programm beenden
        sys.exit(0)
    
    # Standardverhalten: Export-Scheduler starten
    print(f"CallDoc Export Scheduler gestartet - läuft alle {interval_hours} Stunden")
    print(f"Run on startup: {run_on_startup}")
    print(f"Erste Ausführung um {datetime.now().strftime('%H:%M:%S')}")

    # Plane die Ausführung basierend auf Konfiguration
    schedule.every(interval_hours).hours.do(run_export)

    # Optional: Sofortige Ausführung beim Start
    if run_on_startup:
        print("Führe initialen Export aus...")
        run_export()
    else:
        print(f"Warte {interval_hours} Stunden bis zum ersten Export...")

    # Halte das Programm am Laufen
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Prüfe jede Minute
    except KeyboardInterrupt:
        print("\nProgramm durch Benutzer beendet")