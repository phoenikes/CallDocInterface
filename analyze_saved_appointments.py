"""
Analysiert die Felder in gespeicherten CallDoc-Terminen.

Dieses Skript lädt eine gespeicherte JSON-Datei mit CallDoc-Terminen
und analysiert die verfügbaren Felder.
"""

import json
import sys
from pprint import pprint

def analyze_appointment_fields(json_file):
    """
    Analysiert die Felder in einer gespeicherten JSON-Datei mit CallDoc-Terminen.
    
    Args:
        json_file: Pfad zur JSON-Datei mit CallDoc-Terminen
    """
    print(f"Analysiere Termine aus {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Prüfen, ob es sich um ein Array oder ein Objekt mit appointments-Array handelt
        if isinstance(data, list):
            appointments = data
        elif isinstance(data, dict) and "appointments" in data:
            appointments = data["appointments"]
        else:
            print("Unbekanntes Datenformat.")
            return
        
        print(f"Anzahl Termine: {len(appointments)}")
        
        if not appointments:
            print("Keine Termine gefunden.")
            return
        
        # Ersten Termin auswählen
        appointment = appointments[0]
        
        print("\nFelder im ersten Termin:")
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
                    if i > 2:  # Nur die ersten 3 Elemente in Listen analysieren
                        break
                    extract_fields(item, f"{prefix}[{i}]")
        
        extract_fields(appointment)
        
        # Felder sortiert ausgeben
        for field, value in sorted(all_fields.items()):
            print(f"{field}: {value}")
        
        # Interessante Felder für die Patientensynchronisation hervorheben
        print("\nInteressante Felder für die Patientensynchronisation:")
        print("=" * 50)
        
        interesting_fields = [
            "insurance_number", "insurance_provider", "piz", "heydokid", 
            "phones", "emails", "gender", "date_of_birth", "surname", "name",
            "city", "city_code", "street", "house_number"
        ]
        
        for field in interesting_fields:
            if field in appointment:
                print(f"{field}: {appointment[field]}")
            else:
                # Suche nach verschachtelten Feldern
                for full_field in all_fields.keys():
                    if full_field.endswith(f".{field}") or full_field == field:
                        print(f"{full_field}: {all_fields[full_field]}")
        
    except Exception as e:
        print(f"Fehler beim Analysieren der Termine: {str(e)}")

if __name__ == "__main__":
    # Standarddatei
    json_file = "calldoc_termine_2025-07-31_type24.json"
    
    # Datei aus Kommandozeile übernehmen, falls angegeben
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    analyze_appointment_fields(json_file)
