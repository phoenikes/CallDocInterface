"""
Vergleicht CallDoc-Termine mit SQLHK-Untersuchungen für den 31.07.2025.
Stellt die Ergebnisse in einer Tabelle dar und speichert sie als CSV.
"""

import requests
import json
import logging
import sys
import os
from datetime import datetime
from prettytable import PrettyTable
import csv

# Eigene Module importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from constants import APPOINTMENT_TYPES, API_BASE_URL, APPOINTMENT_SEARCH_URL

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_calldoc_appointments(date_str):
    """
    Ruft Termine aus der CallDoc-API ab.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        
    Returns:
        Liste der Termine
    """
    try:
        # API-URL für Terminsuche
        url = APPOINTMENT_SEARCH_URL
        
        # Parameter für die Suche
        params = {
            "from_date": date_str,
            "to_date": date_str,
            "appointment_type_id": APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
            "status": "created"
        }
        
        logger.info(f"Sende Anfrage an {url} mit Parametern {params}")
        
        # API-Aufruf durchführen
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Ergebnis verarbeiten
        result = response.json()
        appointments = result.get("data", [])
        
        logger.info(f"{len(appointments)} CallDoc-Termine gefunden")
        return appointments
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der CallDoc-Termine: {str(e)}")
        return []

def get_sqlhk_untersuchungen(date_str, server_url="http://localhost:7007"):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {"datum": date_str}
        
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            logger.info(f"{len(result.get('data', []))} SQLHK-Untersuchungen gefunden")
            return result.get("data", [])
        else:
            logger.error(f"API-Fehler: {result.get('error', 'Unbekannter Fehler')}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return []

def get_patient_details(patient_id, server_url="http://localhost:7007"):
    """
    Ruft Patientendetails aus der SQLHK-Datenbank über die API ab.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Patientendetails als Dictionary
    """
    try:
        url = f"{server_url}/api/execute_sql"
        query = f"SELECT * FROM Patient WHERE PatientID = {patient_id}"
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results"):
            return result["results"][0]
        else:
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            return {}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Patientendetails: {str(e)}")
        return {}

def get_untersuchungsart_details(untersuchungsart_id, server_url="http://localhost:7007"):
    """
    Ruft Details zur Untersuchungsart aus der SQLHK-Datenbank über die API ab.
    
    Args:
        untersuchungsart_id: ID der Untersuchungsart
        server_url: URL des API-Servers
        
    Returns:
        Untersuchungsart-Details als Dictionary
    """
    try:
        url = f"{server_url}/api/execute_sql"
        query = f"SELECT * FROM Untersuchungart WHERE UntersuchungartID = {untersuchungsart_id}"
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results"):
            return result["results"][0]
        else:
            logger.warning(f"Untersuchungsart mit ID {untersuchungsart_id} nicht gefunden")
            return {}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Untersuchungsart-Details: {str(e)}")
        return {}

def create_comparison_table(calldoc_appointments, sqlhk_untersuchungen):
    """
    Erstellt eine Tabelle zum Vergleich von CallDoc-Terminen und SQLHK-Untersuchungen.
    
    Args:
        calldoc_appointments: Liste der CallDoc-Termine
        sqlhk_untersuchungen: Liste der SQLHK-Untersuchungen
        
    Returns:
        PrettyTable-Objekt mit den Vergleichsergebnissen
    """
    # Tabelle erstellen
    table = PrettyTable()
    table.field_names = [
        "Quelle", 
        "ID", 
        "PatientenID/PIZ", 
        "Patient", 
        "Untersuchungsart",
        "Status"
    ]
    
    # CallDoc-Termine hinzufügen
    for appointment in calldoc_appointments:
        # Robuste Verarbeitung der Patientendaten
        if isinstance(appointment, dict):
            patient = appointment.get("patient", {})
            if patient:
                patient_name = f"{patient.get('lastName', '')}, {patient.get('firstName', '')}"
                patient_piz = patient.get("piz", "")
            else:
                patient_name = "Unbekannt"
                patient_piz = ""
            
            appointment_id = appointment.get("id", "")
            appointment_status = appointment.get("status", "")
        else:
            logger.warning(f"Ungültiges Appointment-Format: {type(appointment)}")
            patient_name = "Unbekannt"
            patient_piz = ""
            appointment_id = ""
            appointment_status = ""
        
        table.add_row([
            "CallDoc",
            appointment_id,
            patient_piz,
            patient_name,
            "Herzkatheteruntersuchung",
            appointment_status
        ])
    
    # SQLHK-Untersuchungen hinzufügen
    for untersuchung in sqlhk_untersuchungen:
        patient_id = untersuchung.get("PatientID", "")
        patient = get_patient_details(patient_id)
        patient_name = f"{patient.get('Nachname', '')}, {patient.get('Vorname', '')}"
        patient_piz = patient.get("PatientenID_KIS", "")
        
        untersuchungsart_id = untersuchung.get("UntersuchungartID")
        untersuchungsart = get_untersuchungsart_details(untersuchungsart_id)
        untersuchungsart_name = untersuchungsart.get("Bezeichnung", f"ID: {untersuchungsart_id}")
        
        table.add_row([
            "SQLHK",
            untersuchung.get("UntersuchungID", ""),
            patient_piz or patient_id,
            patient_name,
            untersuchungsart_name,
            ""
        ])
    
    return table

def save_table_to_csv(table, filename):
    """
    Speichert die Tabelle als CSV-Datei.
    
    Args:
        table: PrettyTable-Objekt
        filename: Name der CSV-Datei
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(table.field_names)
        for row in table._rows:
            writer.writerow(row)
    
    print(f"Tabelle wurde als {filename} gespeichert.")

def main():
    """
    Hauptfunktion zum Vergleich von CallDoc-Terminen und SQLHK-Untersuchungen.
    """
    # Datum für den Vergleich (31.07.2025)
    calldoc_date = "2025-07-31"
    sqlhk_date = "31.07.2025"
    
    print(f"Vergleiche CallDoc-Termine mit SQLHK-Untersuchungen für {calldoc_date} / {sqlhk_date}...")
    
    # CallDoc-Termine abrufen
    appointments = get_calldoc_appointments(calldoc_date)
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    # Vergleichstabelle erstellen
    table = create_comparison_table(appointments, untersuchungen)
    
    # Tabelle anzeigen
    print("\nVergleichstabelle:")
    print(table)
    
    # Statistiken berechnen
    calldoc_count = sum(1 for row in table._rows if row[0] == "CallDoc")
    sqlhk_count = sum(1 for row in table._rows if row[0] == "SQLHK")
    
    print("\nStatistiken:")
    print(f"CallDoc-Termine: {calldoc_count}")
    print(f"SQLHK-Untersuchungen: {sqlhk_count}")
    
    # Tabelle als CSV speichern
    csv_filename = f"vergleich_calldoc_sqlhk_{calldoc_date.replace('-', '_')}.csv"
    save_table_to_csv(table, csv_filename)

if __name__ == "__main__":
    main()
