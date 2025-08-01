"""
Einfaches Skript zum Testen der CallDoc-API-Abfrage für einen bestimmten Tag.

Dieses Skript ruft Termine für den 05.08.2025 ab und gibt die Ergebnisse aus,
um die Struktur der zurückgegebenen Daten zu verstehen.
"""

import json
from datetime import datetime
from calldoc_interface import CallDocInterface

def main():
    # Datum für die Abfrage
    date_str = "2025-08-05"
    
    print(f"Rufe Termine für {date_str} von CallDoc ab...")
    
    # CallDoc-Interface initialisieren
    calldoc_interface = CallDocInterface(from_date=date_str, to_date=date_str)
    
    # Termine abrufen
    appointments = calldoc_interface.appointment_search()
    
    # Ausgabe der Ergebnisse
    print(f"\nAnzahl der gefundenen Termine: {len(appointments.get('data', []))}")
    
    # Detaillierte Ausgabe der ersten 10 Termine (falls vorhanden)
    print("\nBeispiel-Termine (bis zu 10):")
    for i, appointment in enumerate(appointments.get('data', [])[:10]):
        print(f"\nTermin {i+1}:")
        print(json.dumps(appointment, indent=4, ensure_ascii=False))
    
    # Struktur eines Termins anzeigen (falls vorhanden)
    if appointments.get('data'):
        print("\nStruktur eines Termins (Feldnamen):")
        fields = list(appointments['data'][0].keys())
        for field in fields:
            print(f"- {field}")

if __name__ == "__main__":
    main()
