"""
Zeigt die CallDoc-Termine für ein bestimmtes Datum an.
"""

import json
from datetime import datetime
from appointment_search import search_appointments

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def show_appointments(date_str, appointment_type=None, status=None):
    """
    Zeigt die CallDoc-Termine für ein bestimmtes Datum an.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        appointment_type: Termintyp (optional)
        status: Terminstatus (optional)
    """
    print(f"Rufe CallDoc-Termine für {date_str} ab...")
    
    # Termine abrufen
    appointments = search_appointments(
        appointment_type=appointment_type,
        date=date_str,
        status=status,
        print_results=False,
        save_json=False
    )
    
    if not appointments:
        print("Keine Termine gefunden.")
        return
    
    print(f"\n{len(appointments)} Termine gefunden:")
    
    # Termine nach Uhrzeit sortieren
    appointments.sort(key=lambda x: x.get("startTime", ""))
    
    # Termine anzeigen
    for i, appointment in enumerate(appointments, 1):
        patient = appointment.get("patient", {})
        doctor = appointment.get("doctor", {})
        
        print(f"\n{i}. Termin-ID: {appointment.get('id')}")
        print(f"   Status: {appointment.get('status')}")
        print(f"   Uhrzeit: {appointment.get('startTime', 'N/A')} - {appointment.get('endTime', 'N/A')}")
        print(f"   Patient: {patient.get('lastName', '')}, {patient.get('firstName', '')} (PIZ: {patient.get('piz', 'N/A')})")
        print(f"   Arzt: {doctor.get('lastName', '')}, {doctor.get('firstName', '')}")
        print(f"   Raum: {appointment.get('room', {}).get('name', 'N/A')}")
        print(f"   Typ: {appointment.get('appointmentType', {}).get('name', 'N/A')}")
    
    # Zusammenfassung nach Status
    status_counts = {}
    for appointment in appointments:
        status = appointment.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nZusammenfassung nach Status:")
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    
    # Optional: Termine als JSON-Datei speichern
    filename = f"calldoc_termine_{date_str.replace('-', '')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(appointments, f, indent=2, cls=JSONEncoder)
    print(f"\nTermine wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Termine für den 01.08.2025 abrufen
    target_date = "2025-08-01"
    show_appointments(target_date, appointment_type="Herzkatheter")
