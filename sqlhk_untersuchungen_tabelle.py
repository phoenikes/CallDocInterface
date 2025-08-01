"""
Stellt die SQLHK-Untersuchungen für den 31.07.2025 in einer Tabelle dar.
"""

import requests
import json
import logging
from datetime import datetime
from prettytable import PrettyTable
import csv

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

def create_untersuchungen_table(untersuchungen):
    """
    Erstellt eine Tabelle mit den SQLHK-Untersuchungen.
    
    Args:
        untersuchungen: Liste der Untersuchungen
        
    Returns:
        PrettyTable-Objekt mit den Untersuchungen
    """
    # Tabelle erstellen
    table = PrettyTable()
    table.field_names = [
        "UntersuchungID", 
        "PatientID", 
        "UntersuchungartID", 
        "Untersuchungsart",
        "HerzkatheterID",
        "UntersucherAbrechnungID",
        "ZuweiserID",
        "Materialpreis"
    ]
    
    # Tabelle füllen
    for untersuchung in untersuchungen:
        untersuchungsart_id = untersuchung.get("UntersuchungartID")
        untersuchungsart = get_untersuchungsart_details(untersuchungsart_id)
        
        table.add_row([
            untersuchung.get("UntersuchungID"),
            untersuchung.get("PatientID"),
            untersuchungsart_id,
            untersuchungsart.get("Bezeichnung", "Unbekannt"),
            untersuchung.get("HerzkatheterID"),
            untersuchung.get("UntersucherAbrechnungID"),
            untersuchung.get("ZuweiserID"),
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
    Hauptfunktion zur Darstellung der SQLHK-Untersuchungen in einer Tabelle.
    """
    # Datum für die Abfrage
    sqlhk_date = "31.07.2025"
    
    print(f"Rufe SQLHK-Untersuchungen für {sqlhk_date} ab...")
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    # Untersuchungstabelle erstellen
    table = create_untersuchungen_table(untersuchungen)
    
    # Tabelle anzeigen
    print("\nSQLHK-Untersuchungen:")
    print(table)
    
    # Statistiken nach Untersuchungsart
    untersuchungsarten = {}
    for untersuchung in untersuchungen:
        art_id = untersuchung.get("UntersuchungartID")
        untersuchungsarten[art_id] = untersuchungsarten.get(art_id, 0) + 1
    
    print("\nStatistiken nach Untersuchungsart:")
    for art_id, anzahl in untersuchungsarten.items():
        untersuchungsart = get_untersuchungsart_details(art_id)
        bezeichnung = untersuchungsart.get("Bezeichnung", f"Unbekannt (ID: {art_id})")
        print(f"- {bezeichnung}: {anzahl} Untersuchungen")
    
    # Tabelle als CSV speichern
    csv_filename = f"sqlhk_untersuchungen_{sqlhk_date.replace('.', '_')}.csv"
    save_table_to_csv(table, csv_filename)

if __name__ == "__main__":
    main()
