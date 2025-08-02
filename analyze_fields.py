"""
Analysiert alle Felder in den CallDoc-Terminen.
"""

import json
import sys

def analyze_fields(json_file):
    """
    Analysiert alle Felder in einer JSON-Datei mit CallDoc-Terminen.
    
    Args:
        json_file: Pfad zur JSON-Datei mit CallDoc-Terminen
    """
    print(f"Analysiere Termine aus {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Anzahl Termine: {len(data)}")
        
        # Alle Felder sammeln
        fields = set()
        for appointment in data:
            fields.update(appointment.keys())
        
        print("\nAlle Felder im Datensatz:")
        print("=" * 50)
        for field in sorted(fields):
            print(field)
        
        # Beispielwerte für jedes Feld anzeigen
        print("\nBeispielwerte für jedes Feld:")
        print("=" * 50)
        
        sample_appointment = data[0]
        for field in sorted(fields):
            value = sample_appointment.get(field, "Nicht vorhanden im ersten Termin")
            print(f"{field}: {value}")
        
    except Exception as e:
        print(f"Fehler beim Analysieren der Termine: {str(e)}")

if __name__ == "__main__":
    # Standarddatei
    json_file = "calldoc_termine_2025-08-04.json"
    
    # Datei aus Kommandozeile übernehmen, falls angegeben
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    analyze_fields(json_file)
