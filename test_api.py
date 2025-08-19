"""
Test-Skript zur Überprüfung der CallDoc-API
"""

import json
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer
from constants import APPOINTMENT_TYPES

# Synchronizer initialisieren
sync = CallDocSQLHKSynchronizer()

# Termine für den 13.08.2025 abrufen
date_str = "2025-08-13"

# Teste beide Varianten
print("Test mit appointment_type_id:")
appointments_old = sync.get_calldoc_appointments(date_str, filter_by_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"])
print(f"Anzahl gefundener Termine: {len(appointments_old)}")

# Speichere die Antwort als JSON
with open("test_response_old.json", "w", encoding="utf-8") as f:
    json.dump(appointments_old, f, indent=2)

# Modifiziere die Methode temporär
def get_appointments_with_type(date_str):
    """Ruft Termine mit appointment_type statt appointment_type_id ab"""
    url = sync.api_client.base_url + "/appointment_search/"
    params = {
        "from_date": date_str,
        "to_date": date_str,
        "appointment_type": APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"]
    }
    response = sync.api_client.get(url, params=params)
    if isinstance(response, dict):
        return response.get("data", [])
    return []

print("\nTest mit appointment_type:")
appointments_new = get_appointments_with_type(date_str)
print(f"Anzahl gefundener Termine: {len(appointments_new)}")

# Speichere die Antwort als JSON
with open("test_response_new.json", "w", encoding="utf-8") as f:
    json.dump(appointments_new, f, indent=2)

# Wenn Termine gefunden wurden, zeige Details
if appointments_new:
    print("\nErster Termin Details:")
    print(json.dumps(appointments_new[0], indent=2, ensure_ascii=False))
    print(f"appointment_type: {appointments_new[0].get('appointment_type')}")
    print(f"appointment_type_id: {appointments_new[0].get('appointment_type_id')}")
