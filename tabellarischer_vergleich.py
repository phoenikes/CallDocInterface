"""
Vergleicht CallDoc-Termine mit SQLHK-Untersuchungen für ein bestimmtes Datum
und stellt die Ergebnisse in einer Tabelle dar.
"""

import requests
import json
import logging
from datetime import datetime
import sys
import os
from prettytable import PrettyTable
import csv

# Eigene Module importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from calldoc_interface import CallDocInterface
from constants import APPOINTMENT_TYPES

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_calldoc_appointments(date_str, status=None):
    """
    Ruft Termine aus der CallDoc-API ab.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        status: Optionaler Statusfilter (z.B. 'created', 'canceled')
        
    Returns:
        Liste der Termine
    """
    try:
        # CallDoc-Interface initialisieren
        calldoc = CallDocInterface()
        
        # Termine abrufen
        appointments = calldoc.appointment_search(
            from_date=date_str,
            to_date=date_str,
            appointment_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
            status="created" if status == "created" else status
        )
        
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
        "Patientennummer", 
        "In CallDoc", 
        "In SQLHK", 
        "CallDoc Termin-ID", 
        "SQLHK Untersuchungs-ID",
        "Untersuchungsart",
        "Status"
    ]
    
    # Patienten-Lookup-Tabellen erstellen
    calldoc_patients = {}
    for appointment in calldoc_appointments:
        patient_piz = appointment.get("patient", {}).get("piz")
        if patient_piz:
            if patient_piz not in calldoc_patients:
                calldoc_patients[patient_piz] = []
            calldoc_patients[patient_piz].append(appointment)
    
    sqlhk_patients = {}
    for untersuchung in sqlhk_untersuchungen:
        patient_id = untersuchung.get("PatientID")
        if patient_id:
            # Patientendetails abrufen
            patient = get_patient_details(patient_id)
            patient_piz = patient.get("PatientenID_KIS")
            if patient_piz:
                if patient_piz not in sqlhk_patients:
                    sqlhk_patients[patient_piz] = []
                sqlhk_patients[patient_piz].append({
                    "untersuchung": untersuchung,
                    "patient": patient
                })
    
    # Alle eindeutigen Patientennummern sammeln
    all_piz = set(list(calldoc_patients.keys()) + list(sqlhk_patients.keys()))
    
    # Tabelle füllen
    for piz in sorted(all_piz):
        in_calldoc = piz in calldoc_patients
        in_sqlhk = piz in sqlhk_patients
        
        if in_calldoc and in_sqlhk:
            # Patient ist in beiden Systemen
            for calldoc_app in calldoc_patients[piz]:
                for sqlhk_data in sqlhk_patients[piz]:
                    untersuchung = sqlhk_data["untersuchung"]
                    untersuchungsart_id = untersuchung.get("UntersuchungartID")
                    untersuchungsart = get_untersuchungsart_details(untersuchungsart_id)
                    
                    table.add_row([
                        piz,
                        "Ja",
                        "Ja",
                        calldoc_app.get("id"),
                        untersuchung.get("UntersuchungID"),
                        untersuchungsart.get("Bezeichnung", f"ID: {untersuchungsart_id}"),
                        "Übereinstimmung"
                    ])
        elif in_calldoc:
            # Patient ist nur in CallDoc
            for calldoc_app in calldoc_patients[piz]:
                table.add_row([
                    piz,
                    "Ja",
                    "Nein",
                    calldoc_app.get("id"),
                    "-",
                    "-",
                    "Nur in CallDoc"
                ])
        elif in_sqlhk:
            # Patient ist nur in SQLHK
            for sqlhk_data in sqlhk_patients[piz]:
                untersuchung = sqlhk_data["untersuchung"]
                untersuchungsart_id = untersuchung.get("UntersuchungartID")
                untersuchungsart = get_untersuchungsart_details(untersuchungsart_id)
                
                table.add_row([
                    piz,
                    "Nein",
                    "Ja",
                    "-",
                    untersuchung.get("UntersuchungID"),
                    untersuchungsart.get("Bezeichnung", f"ID: {untersuchungsart_id}"),
                    "Nur in SQLHK"
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
    
    # CallDoc-Termine abrufen (nur erstellte Termine)
    appointments = get_calldoc_appointments(calldoc_date, status="created")
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    # Vergleichstabelle erstellen
    table = create_comparison_table(appointments, untersuchungen)
    
    # Tabelle anzeigen
    print("\nVergleichstabelle:")
    print(table)
    
    # Statistiken berechnen
    in_both = sum(1 for row in table._rows if row[1] == "Ja" and row[2] == "Ja")
    only_calldoc = sum(1 for row in table._rows if row[1] == "Ja" and row[2] == "Nein")
    only_sqlhk = sum(1 for row in table._rows if row[1] == "Nein" and row[2] == "Ja")
    
    print("\nStatistiken:")
    print(f"Gesamt Datensätze: {len(table._rows)}")
    print(f"In beiden Systemen: {in_both}")
    print(f"Nur in CallDoc: {only_calldoc}")
    print(f"Nur in SQLHK: {only_sqlhk}")
    
    # Tabelle als CSV speichern
    csv_filename = f"vergleich_{calldoc_date.replace('-', '_')}.csv"
    save_table_to_csv(table, csv_filename)

if __name__ == "__main__":
    main()
