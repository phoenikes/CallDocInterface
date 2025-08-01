"""
Stellt die Untersuchungen für den 31.07.2025 aus der SQLHK-Datenbank in einer übersichtlichen Tabelle dar.
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
        query = f"SELECT Bezeichnung FROM Untersuchungart WHERE UntersuchungartID = {untersuchungsart_id}"
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

def get_herzkatheterlabor_name(herzkatheterlabor_id, server_url="http://localhost:7007"):
    """
    Ruft den Namen eines Herzkatheterlabors anhand der ID ab.
    
    Args:
        herzkatheterlabor_id: ID des Herzkatheterlabors
        server_url: URL des API-Servers
        
    Returns:
        Name des Herzkatheterlabors oder "Unbekannt"
    """
    try:
        url = f"{server_url}/api/execute_sql"
        query = f"SELECT Bezeichnung FROM Herzkatheterlabor WHERE HerzkatheterID = {herzkatheterlabor_id}"
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
            logger.warning(f"Herzkatheterlabor mit ID {herzkatheterlabor_id} nicht gefunden")
            return f"Labor {herzkatheterlabor_id}"
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Herzkatheterlabors: {str(e)}")
        return f"Labor {herzkatheterlabor_id}"

def create_untersuchungen_table(untersuchungen):
    """
    Erstellt eine Tabelle mit den Untersuchungen.
    
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
        "Untersuchungsart",
        "Herzkatheterlabor",
        "ZuweiserID",
        "Materialpreis"
    ]
    
    # Untersuchungen zur Tabelle hinzufügen
    for untersuchung in untersuchungen:
        # Untersuchungsart-Name abrufen
        untersuchungsart_id = untersuchung.get("UntersuchungartID")
        untersuchungsart = get_untersuchungsart_name(untersuchungsart_id)
        
        # Herzkatheterlabor-Name abrufen
        herzkatheterlabor_id = untersuchung.get("HerzkatheterID")
        herzkatheterlabor = get_herzkatheterlabor_name(herzkatheterlabor_id)
        
        table.add_row([
            untersuchung.get("UntersuchungID"),
            untersuchung.get("PatientID"),
            f"{untersuchungsart} (ID: {untersuchungsart_id})",
            herzkatheterlabor,
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
    Hauptfunktion zum Abrufen und Anzeigen der Untersuchungen.
    """
    # Datum für die Abfrage
    datum = "31.07.2025"
    
    print(f"Rufe Untersuchungen für {datum} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    # Tabelle erstellen
    table = create_untersuchungen_table(untersuchungen)
    
    # Tabelle anzeigen
    print(f"\nUntersuchungen für {datum}:")
    print(table)
    
    # Statistiken nach UntersuchungartID
    untersuchungsarten = {}
    for untersuchung in untersuchungen:
        art_id = untersuchung.get("UntersuchungartID")
        if art_id not in untersuchungsarten:
            untersuchungsarten[art_id] = 0
        untersuchungsarten[art_id] += 1
    
    print("\nStatistiken nach Untersuchungsart:")
    for art_id, anzahl in untersuchungsarten.items():
        art_name = get_untersuchungsart_name(art_id)
        print(f"- {art_name} (ID: {art_id}): {anzahl} Untersuchungen")
    
    # Tabelle als CSV speichern
    csv_filename = f"untersuchungen_tabelle_{datum.replace('.', '_')}.csv"
    save_table_to_csv(table, csv_filename)

if __name__ == "__main__":
    main()
