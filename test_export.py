import os
import json
from main import get_next_monday, CallDocInterface
from weekly_appointment_exporter import WeeklyAppointmentExporter
from appointment_patient_enricher import AppointmentPatientEnricher
from datetime import datetime, timedelta

# Test-Konfiguration laden
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_next_weekdays():
    monday = datetime.strptime(get_next_monday(), "%Y-%m-%d")
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

def test_week_export():
    config = load_config()
    week_start = get_next_monday()
    exporter = WeeklyAppointmentExporter(
        week_start=week_start,
        appointment_type_id=config["appointment_type_id"],
        doctor_id=config.get("doctor_id"),
        room_id=config.get("room_id"),
        skip_holidays=config.get("skip_holidays", True),
        export_directory=config.get("export_directory"),
        country=config.get("country", "DE"),
        subdiv=config.get("subdiv", "BY")
    )
    exporter.export_week()
    # Überprüfe, ob für jeden Wochentag eine Exportdatei existiert
    files = os.listdir(config["export_directory"])
    found = 0
    for day in get_next_weekdays():
        expected = f"{day}_{day}_{config['appointment_type_id']}"
        if any(f.startswith(expected) and f.endswith(".json") for f in files):
            found += 1
        else:
            print(f"Fehlende Exportdatei für {day}")
    assert found >= 3, "Weniger als 3 Tages-Exporte gefunden!"
    print(f"Test erfolgreich: {found} Exportdateien für die Woche vorhanden.")

def test_get_patient_by_piz():
    interface = CallDocInterface(from_date="2025-01-01", to_date="2025-01-02")
    piz = 1679787
    result = interface.get_patient_by_piz(piz)
    print("Ergebnis für PIZ 1679787:")
    print(result)

def test_appointments_for_doctor(doctor_id, day_offset=0):
    # Nächsten Montag berechnen und Offset anwenden
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    target_day = next_monday + timedelta(days=day_offset)
    from_date = target_day.strftime("%Y-%m-%d")
    to_date = from_date
    try:
        enricher = AppointmentPatientEnricher(
            from_date=from_date,
            to_date=to_date,
            appointment_type_id=24,  # Standard-Typ, kann angepasst werden
            doctor_id=doctor_id
        )
        appointments = enricher.fetch_appointments()
        print(f"Teste Termine für Arzt-ID {doctor_id} am {from_date}...")
        print(f"Gefundene Termine: {len(appointments.get('data', []))}")
        return appointments
    except Exception as e:
        print(f"Fehler: {e}")
        return {"data": []}

def check_any_appointments_next_tuesday():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    next_tuesday = next_monday + timedelta(days=1)
    from_date = next_tuesday.strftime("%Y-%m-%d")
    to_date = from_date
    try:
        # Kein Arztfilter, alle Termine holen
        enricher = AppointmentPatientEnricher(
            from_date=from_date,
            to_date=to_date,
            appointment_type_id=24  # Standard-Typ, ggf. anpassen
        )
        appointments = enricher.fetch_appointments()
        appt_list = appointments.get('data', [])
        print(f"Termine am {from_date}: {len(appt_list)}")
        if appt_list:
            arzt_ids = set(a.get('doctor_id') for a in appt_list if a.get('doctor_id') is not None)
            print(f"Arzt-IDs mit Terminen: {arzt_ids}")
        else:
            print("Keine Termine gefunden.")
    except Exception as e:
        print(f"Fehler: {e}")

def check_any_appointments_on_date(date_str):
    from_date = to_date = date_str
    try:
        enricher = AppointmentPatientEnricher(
            from_date=from_date,
            to_date=to_date,
            appointment_type_id=24
        )
        appointments = enricher.fetch_appointments()
        appt_list = appointments.get('data', [])
        print(f"Termine am {from_date}: {len(appt_list)}")
        if appt_list:
            # Arzt-IDs und Namen aus employee_id und employee_name Feldern extrahieren
            arzt_map = {}
            for a in appt_list:
                eid = a.get('employee_id')
                if eid is not None:
                    arzt_map[eid] = f"{a.get('employee_title','')} {a.get('employee_first_name','')} {a.get('employee_last_name','')}".strip()
            print(f"Arzt-IDs mit Terminen: {list(arzt_map.keys())}")
            print(f"Arzt-Namen: {list(arzt_map.values())}")
        else:
            print("Keine Termine gefunden.")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    check_any_appointments_on_date("2025-05-05")
