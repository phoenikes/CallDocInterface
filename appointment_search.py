"""
Modul zur flexiblen Abfrage von CallDoc-Terminen.

Dieses Modul bietet Funktionen zur gezielten Abfrage von Terminen aus der CallDoc-API
mit verschiedenen Filteroptionen wie Termintyp, Datum, Arzt, Raum und Patient.
"""

import json
from datetime import datetime, timedelta
from calldoc_interface import CallDocInterface
from constants import APPOINTMENT_TYPES, DOCTORS, ROOMS


def search_appointments(appointment_type_id, date, employee_id=None, room_id=None, 
                       location_id=None, patient_id=None, status=None, output_file=None, print_results=True):
    """
    Sucht Termine in CallDoc basierend auf verschiedenen Filterkriterien.
    
    Args:
        appointment_type_id (int): ID des Termintyps (z.B. 24 für Herzkatheteruntersuchung)
        date (str): Datum im Format 'YYYY-MM-DD'
        employee_id (int, optional): ID des Arztes
        room_id (int, optional): ID des Raums
        location_id (int, optional): ID des Standorts
        patient_id (int, optional): ID des Patienten
        status (str, optional): Status des Termins (z.B. 'created', 'canceled', 'finished_final')
        output_file (str, optional): Pfad zur Ausgabedatei für die JSON-Ergebnisse
        print_results (bool, optional): Wenn True, werden die Ergebnisse auf der Konsole ausgegeben
        
    Returns:
        dict: Die API-Antwort als Dictionary
    """
    # Datumsformat validieren und ggf. konvertieren
    try:
        if isinstance(date, str):
            # Versuche das Datum zu parsen
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        elif isinstance(date, datetime):
            parsed_date = date
        else:
            raise ValueError("Datum muss ein String im Format 'YYYY-MM-DD' oder ein datetime-Objekt sein")
        
        # Formatiere das Datum für die API
        date_str = parsed_date.strftime('%Y-%m-%d')
    except ValueError as e:
        print(f"Fehler beim Parsen des Datums: {e}")
        return {"error": True, "message": f"Ungültiges Datumsformat: {e}"}
    
    # Erstelle ein CallDocInterface-Objekt mit dem angegebenen Datum
    # Wir verwenden das gleiche Datum für from_date und to_date, um nur einen Tag abzufragen
    interface = CallDocInterface(date_str, date_str)
    
    # Parameter für die API-Abfrage vorbereiten
    params = {"appointment_type_id": appointment_type_id}
    
    # Optionale Parameter hinzufügen, wenn sie angegeben wurden
    if employee_id is not None:
        params["employee_id"] = employee_id
    if room_id is not None:
        params["room_id"] = room_id
    if location_id is not None:
        params["doctors_office_location"] = location_id
    if patient_id is not None:
        params["patient"] = patient_id
    if status is not None:
        params["status"] = status
    
    # API-Abfrage durchführen
    result = interface.appointment_search(**params)
    
    # Prüfen, ob ein Fehler aufgetreten ist
    if "error" in result:
        print(f"Fehler bei der API-Abfrage: {result.get('message', 'Unbekannter Fehler')}")
        return result
    
    # Ergebnisse ausgeben, wenn gewünscht
    if print_results:
        print(f"\nGefundene Termine für {date_str} (Typ: {appointment_type_id}):")
        print(f"Anzahl: {result.get('count', 0)}")
        
        # Termine nach Uhrzeit sortieren
        appointments = sorted(
            result.get("data", []),
            key=lambda x: x.get("scheduled_for_datetime", "")
        )
        
        # Termine ausgeben
        for i, appointment in enumerate(appointments, 1):
            time_str = appointment.get("scheduled_for_datetime", "").split("T")[1][:5]
            doctor = f"{appointment.get('employee_title', '')} {appointment.get('employee_first_name', '')} {appointment.get('employee_last_name', '')}"
            patient = f"{appointment.get('first_name', '')} {appointment.get('last_name', '')}"
            piz = appointment.get("piz", "")
            status = appointment.get("status", "")
            
            print(f"{i}. {time_str} | {doctor} | {patient} (PIZ: {piz}) | Status: {status}")
    
    # Ergebnisse in Datei speichern, wenn gewünscht
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nErgebnisse wurden in {output_file} gespeichert.")
        except Exception as e:
            print(f"Fehler beim Speichern der Ergebnisse: {e}")
    
    return result


def get_appointment_type_name(appointment_type_id):
    """
    Gibt den Namen eines Termintyps anhand seiner ID zurück.
    
    Args:
        appointment_type_id (int): Die ID des Termintyps
        
    Returns:
        str: Der Name des Termintyps oder "Unbekannter Typ"
    """
    for name, type_id in APPOINTMENT_TYPES.items():
        if type_id == appointment_type_id:
            return name
    return "Unbekannter Typ"


def get_doctor_name(employee_id):
    """
    Gibt den Namen eines Arztes anhand seiner ID zurück.
    
    Args:
        employee_id (int): Die ID des Arztes
        
    Returns:
        str: Der Name des Arztes oder "Unbekannter Arzt"
    """
    for name, doctor_id in DOCTORS.items():
        if doctor_id == employee_id:
            return name
    return "Unbekannter Arzt"


def get_room_name(room_id):
    """
    Gibt den Namen eines Raums anhand seiner ID zurück.
    
    Args:
        room_id (int): Die ID des Raums
        
    Returns:
        str: Der Name des Raums oder "Unbekannter Raum"
    """
    for name, rid in ROOMS.items():
        if rid == room_id:
            return name
    return "Unbekannter Raum"


if __name__ == "__main__":
    # Beispielaufruf für Herzkatheteruntersuchungen am 23.07.2025
    print("Beispielabfrage für Herzkatheteruntersuchungen am 23.07.2025:")
    result = search_appointments(
        appointment_type_id=24,  # 24 = Herzkatheteruntersuchung
        date="2025-07-23"
    )
    
    # Beispiel mit zusätzlichen Filtern
    print("\nBeispielabfrage für Termine von Dr. Sandrock:")
    result = search_appointments(
        appointment_type_id=24,
        date="2025-07-23",
        employee_id=18  # 18 = Dr. Sandrock
    )
