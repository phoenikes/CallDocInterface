import os
import json
from main import get_next_monday
from weekly_appointment_exporter import WeeklyAppointmentExporter
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

if __name__ == "__main__":
    test_week_export()
