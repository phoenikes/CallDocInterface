"""
Testskript für die Appointment-Search-Funktionalität.

Dieses Skript demonstriert die Verwendung der search_appointments-Funktion
mit verschiedenen Filteroptionen.
"""

from appointment_search import search_appointments
from datetime import datetime, timedelta


def main():
    """
    Hauptfunktion zum Testen der Appointment-Search-Funktionalität.
    """
    print("CallDoc Termin-Suche Testprogramm")
    print("================================\n")

    # Beispiel 1: Alle Herzkatheteruntersuchungen für einen bestimmten Tag
    print("\nBeispiel 1: Alle Herzkatheteruntersuchungen am 23.07.2025")
    search_appointments(
        appointment_type_id=24,  # 24 = Herzkatheteruntersuchung
        date="2025-07-23"
    )

    # Beispiel 2: Termine eines bestimmten Arztes
    print("\nBeispiel 2: Termine von Dr. Sandrock am 23.07.2025")
    search_appointments(
        appointment_type_id=24,
        date="2025-07-23",
        employee_id=18  # 18 = Dr. Sandrock
    )

    # Beispiel 3: Termine in einem bestimmten Raum
    print("\nBeispiel 3: Termine im Herzkatheter 1 (Raum 18) am 23.07.2025")
    search_appointments(
        appointment_type_id=24,
        date="2025-07-23",
        room_id=18  # 18 = Herzkatheter 1
    )

    # Beispiel 4: Termine mit Ausgabe in eine Datei
    print("\nBeispiel 4: Termine speichern in JSON-Datei")
    search_appointments(
        appointment_type_id=24,
        date="2025-07-23",
        output_file="termine_2025-07-23.json"
    )

    # Beispiel 5: Termine für morgen
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"\nBeispiel 5: Termine für morgen ({tomorrow})")
    search_appointments(
        appointment_type_id=24,
        date=tomorrow
    )


if __name__ == "__main__":
    main()
