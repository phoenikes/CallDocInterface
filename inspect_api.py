"""
Skript zur Inspektion der API-Antwort
"""

import json
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer
from constants import APPOINTMENT_TYPES

# Synchronizer initialisieren
sync = CallDocSQLHKSynchronizer()

# Termine für den 13.08.2025 abrufen
date_str = "2025-08-13"
appointments = sync.get_calldoc_appointments(date_str, filter_by_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"])

print(f"Anzahl gefundener Termine: {len(appointments)}")

# Speichere die Antwort als JSON
with open("api_response.json", "w", encoding="utf-8") as f:
    json.dump(appointments, f, indent=2)

# Wenn Termine gefunden wurden, zeige Details
if appointments:
    print("\nErster Termin Details:")
    first_appointment = appointments[0]
    print(json.dumps(first_appointment, indent=2, ensure_ascii=False))
    
    # Überprüfe, welche Felder vorhanden sind
    print("\nVerfügbare Felder:")
    for key in first_appointment.keys():
        print(f"- {key}: {first_appointment[key]}")
        
    # Überprüfe speziell die Termintyp-Felder
    print("\nTermintyp-Felder:")
    print(f"appointment_type_id: {first_appointment.get('appointment_type_id')}")
    print(f"appointment_type: {first_appointment.get('appointment_type')}")
