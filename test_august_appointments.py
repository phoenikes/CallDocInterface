"""
Testskript für die Abfrage der Termine am 01.08.2025.

Dieses Skript demonstriert die Verwendung der erweiterten search_appointments-Funktion
mit dem Status-Filter und vergleicht die Ergebnisse mit manuell abgerufenen Daten.
"""

from appointment_search import search_appointments
from datetime import datetime


def main():
    """
    Hauptfunktion zum Testen der Appointment-Search-Funktionalität für den 01.08.2025.
    """
    print("CallDoc Termin-Suche für den 01.08.2025")
    print("======================================\n")

    # Alle Herzkatheteruntersuchungen am 01.08.2025
    print("\n1. Alle Herzkatheteruntersuchungen am 01.08.2025:")
    result_all = search_appointments(
        appointment_type_id=24,  # 24 = Herzkatheteruntersuchung
        date="2025-08-01",
        output_file="termine_2025-08-01_alle.json"
    )
    
    # Nur stornierte Termine am 01.08.2025
    print("\n2. Nur stornierte Termine am 01.08.2025:")
    result_canceled = search_appointments(
        appointment_type_id=24,
        date="2025-08-01",
        status="canceled",
        output_file="termine_2025-08-01_storniert.json"
    )
    
    # Nur erstellte Termine am 01.08.2025
    print("\n3. Nur erstellte Termine am 01.08.2025:")
    result_created = search_appointments(
        appointment_type_id=24,
        date="2025-08-01",
        status="created",
        output_file="termine_2025-08-01_erstellt.json"
    )
    
    # Termine nach Arzt filtern
    print("\n4. Termine von Dr. Anger am 01.08.2025:")
    search_appointments(
        appointment_type_id=24,
        date="2025-08-01",
        employee_id=30  # 30 = Dr. Anger
    )
    
    # Termine nach Raum filtern
    print("\n5. Termine im Herzkatheter 1 (Raum 18) am 01.08.2025:")
    search_appointments(
        appointment_type_id=24,
        date="2025-08-01",
        room_id=18  # 18 = Herzkatheter 1
    )
    
    # Zusammenfassung
    print("\n\nZusammenfassung der Ergebnisse:")
    print(f"Gesamtanzahl der Termine: {result_all.get('count', 0)}")
    print(f"Anzahl stornierter Termine: {result_canceled.get('count', 0)}")
    print(f"Anzahl erstellter Termine: {result_created.get('count', 0)}")


if __name__ == "__main__":
    main()
