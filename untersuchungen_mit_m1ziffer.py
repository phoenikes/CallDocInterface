"""
Ruft Untersuchungen für ein bestimmtes Datum aus der SQLHK-Datenbank ab und ergänzt die M1Ziffer aus der Patient-Tabelle.
Die M1Ziffer entspricht der Patientenkennung im CallDoc-System.
"""

import requests
import json
import logging
from datetime import datetime
from prettytable import PrettyTable
import csv
import sys

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_untersuchungen(datum, server_url="http://localhost:7007"):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {"datum": datum}
        
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            untersuchungen = result.get("data", [])
            logger.info(f"{len(untersuchungen)} Untersuchungen gefunden")
            return untersuchungen
        else:
            logger.error(f"API-Fehler: {result.get('error', 'Unbekannter Fehler')}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return []

def get_patient_details_with_m1ziffer(patient_id, server_url="http://localhost:7007"):
    """
    Ruft Patientendetails inklusive M1Ziffer aus der SQLHK-Datenbank über die API ab.
    Wechselt zur SQLHK-Datenbank, führt die Abfrage durch und wechselt zurück zur SuPDatabase.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Patientendetails als Dictionary mit M1Ziffer
    """
    try:
        url = f"{server_url}/api/execute_sql"
        
        # Wechsel zur SQLHK-Datenbank und Abfrage der Patientendaten
        query = f"""
        USE SQLHK;
        SELECT PatientID, Nachname, Vorname, Geburtsdatum, M1Ziffer, krankenkasse, versichertennr
        FROM Patient 
        WHERE PatientID = {patient_id};
        USE SuPDatabase;
        """
        
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results") and len(result["results"]) > 0:
            return result["results"][0]
        else:
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            return {"PatientID": patient_id, "Nachname": "Unbekannt", "Vorname": "Unbekannt", "M1Ziffer": ""}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Patientendetails: {str(e)}")
        return {"PatientID": patient_id, "Nachname": "Unbekannt", "Vorname": "Unbekannt", "M1Ziffer": ""}

def get_untersuchungsart_name(untersuchungsart_id, server_url="http://localhost:7007"):
    """
    Ruft den Namen einer Untersuchungsart anhand der ID ab.
    
    Args:
        untersuchungsart_id: ID der Untersuchungsart
        server_url: URL des API-Servers
        
    Returns:
        Name der Untersuchungsart oder "Unbekannt"
    """
    try:
        url = f"{server_url}/api/execute_sql"
        query = """
        USE SQLHK;
        SELECT Bezeichnung FROM Untersuchungart WHERE UntersuchungartID = {0};
        USE SuPDatabase;
        """.format(untersuchungsart_id)
        
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results") and len(result["results"]) > 0:
            return result["results"][0].get("Bezeichnung", "Unbekannt")
        else:
            logger.warning(f"Untersuchungsart mit ID {untersuchungsart_id} nicht gefunden")
            return "Unbekannt"
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Untersuchungsart: {str(e)}")
        return "Unbekannt"

def create_untersuchungen_table(untersuchungen):
    """
    Erstellt eine Tabelle mit den Untersuchungen und ergänzt die M1Ziffer.
    
    Args:
        untersuchungen: Liste der Untersuchungen
        
    Returns:
        PrettyTable-Objekt mit den Untersuchungen und M1Ziffer
    """
    # Tabelle erstellen
    table = PrettyTable()
    table.field_names = [
        "UntersuchungID",
        "PatientID",
        "M1Ziffer",
        "Patient",
        "Untersuchungsart",
        "Materialpreis"
    ]
    
    # Untersuchungen zur Tabelle hinzufügen
    for untersuchung in untersuchungen:
        # Patientendetails mit M1Ziffer abrufen
        patient_id = untersuchung.get("PatientID")
        patient = get_patient_details_with_m1ziffer(patient_id)
        patient_name = f"{patient.get('Nachname', 'Unbekannt')}, {patient.get('Vorname', 'Unbekannt')}"
        m1ziffer = patient.get("M1Ziffer", "")
        
        # Untersuchungsart-Name abrufen
        untersuchungsart_id = untersuchung.get("UntersuchungartID")
        untersuchungsart = get_untersuchungsart_name(untersuchungsart_id)
        
        table.add_row([
            untersuchung.get("UntersuchungID"),
            patient_id,
            m1ziffer,
            patient_name,
            f"{untersuchungsart} (ID: {untersuchungsart_id})",
            untersuchung.get("Materialpreis")
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
    Hauptfunktion zum Abrufen und Anzeigen der Untersuchungen mit M1Ziffer.
    """
    # Datum für die Abfrage aus Kommandozeilenargumenten oder Standardwert
    if len(sys.argv) > 1:
        datum = sys.argv[1]
    else:
        datum = "31.07.2025"  # Standarddatum
    
    print(f"Rufe Untersuchungen für {datum} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    # Tabelle erstellen
    table = create_untersuchungen_table(untersuchungen)
    
    # Tabelle anzeigen
    print(f"\nUntersuchungen für {datum} mit M1Ziffer:")
    print(table)
    
    # Statistiken nach M1Ziffer
    m1ziffer_vorhanden = 0
    m1ziffer_fehlt = 0
    
    for row in table._rows:
        if row[2]:  # M1Ziffer ist vorhanden
            m1ziffer_vorhanden += 1
        else:
            m1ziffer_fehlt += 1
    
    print("\nStatistiken zur M1Ziffer:")
    print(f"- Patienten mit M1Ziffer: {m1ziffer_vorhanden}")
    print(f"- Patienten ohne M1Ziffer: {m1ziffer_fehlt}")
    
    # Tabelle als CSV speichern
    csv_filename = f"untersuchungen_m1ziffer_{datum.replace('.', '_')}.csv"
    save_table_to_csv(table, csv_filename)

if __name__ == "__main__":
    main()
