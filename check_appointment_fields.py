"""
Analysiert die verfügbaren Felder in einem CallDoc-Termin.

Dieses Skript ruft einen einzelnen CallDoc-Termin ab und zeigt alle verfügbaren Felder
mit ihren Werten an, um zu prüfen, welche zusätzlichen Felder für die Synchronisation
verwendet werden können.
"""

import json
import sys
import traceback
from datetime import datetime
from calldoc_interface import CallDocInterface
from constants import APPOINTMENT_TYPES
from appointment_search import search_appointments

def analyze_appointment_fields(date_str, appointment_type_id=24):
    """
    Ruft einen CallDoc-Termin ab und analysiert alle verfügbaren Felder.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        appointment_type_id: ID des Termintyps (Standard: 24 für Herzkatheter)
    """
    print(f"Rufe CallDoc-Termine für {date_str} ab...")
    
    try:
        # Termine mit der search_appointments-Funktion abrufen
        appointments = search_appointments(
            date=date_str,
            appointment_type_id=appointment_type_id,
            print_results=False
        )
        
        print(f"API-Antwort erhalten: {type(appointments)}")
        
        if not appointments:
            print("Keine Termine gefunden.")
            return
            
        # Ersten Termin auswählen
        appointment = appointments[0]
        print(f"Erster Termin gefunden: {appointment.get('id', 'Keine ID')}")
    
    except Exception as e:
        print(f"Fehler beim Abrufen der Termine: {str(e)}")
        traceback.print_exc()
        return
    
    print(f"\nTermin-ID: {appointment.get('id')}")
    print(f"Termintyp: {appointment.get('appointment_type_name')}")
    print(f"Startzeit: {appointment.get('startTime')}")
    print(f"Endzeit: {appointment.get('endTime')}")
    print(f"Status: {appointment.get('status')}")
    
    # Alle Felder und ihre Werte anzeigen
    print("\nAlle verfügbaren Felder:")
    print("=" * 50)
    
    # Flache Liste aller Felder erstellen
    all_fields = {}
    
    def extract_fields(obj, prefix=""):
        """Extrahiert alle Felder rekursiv aus einem verschachtelten Objekt."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_name = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    extract_fields(value, field_name)
                else:
                    all_fields[field_name] = value
        elif isinstance(obj, list) and obj:
            for i, item in enumerate(obj):
                extract_fields(item, f"{prefix}[{i}]")
    
    extract_fields(appointment)
    
    # Felder sortiert ausgeben
    for field, value in sorted(all_fields.items()):
        print(f"{field}: {value}")
    
    # Vollständigen JSON-Termin in Datei speichern
    output_file = f"appointment_fields_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(appointment, f, indent=2, ensure_ascii=False)
    
    print(f"\nVollständiger Termin wurde in {output_file} gespeichert.")

if __name__ == "__main__":
    # Standarddatum: heute
    target_date = "2025-08-01"
    
    # Datum aus Kommandozeile übernehmen, falls angegeben
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    analyze_appointment_fields(target_date)
