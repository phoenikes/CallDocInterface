"""
Zeigt alle verfügbaren Untersuchungen in der SQLHK-Datenbank an.
"""

import requests
import json
import logging
from datetime import datetime

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_untersuchungen(datum=None):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ (optional)
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = "http://localhost:7007/api/untersuchung"
        params = {}
        
        if datum:
            params["Datum"] = datum
            
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            logger.info(f"{len(result.get('data', []))} Untersuchungen gefunden")
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

def execute_sql(query, database="SQLHK"):
    """
    Führt eine SQL-Abfrage auf dem MCP SQL Server aus.
    
    Args:
        query: SQL-Abfrage
        database: Name der Datenbank
            
    Returns:
        Ergebnis der Abfrage als Dictionary
    """
    try:
        url = "http://localhost:7007/api/execute_sql"
        payload = {
            "query": query,
            "database": database
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sende SQL-Abfrage: {query}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return {"error": str(e), "success": False}
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    # Alle Untersuchungen abrufen
    print("Rufe alle Untersuchungen ab...")
    untersuchungen = get_untersuchungen()
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
    else:
        print(f"\n{len(untersuchungen)} Untersuchungen gefunden.")
        
        # Die ersten 5 Untersuchungen anzeigen
        print("\nDie ersten 5 Untersuchungen:")
        for i, untersuchung in enumerate(untersuchungen[:5], 1):
            print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
            print(f"   Datum: {untersuchung.get('Datum')}")
            print(f"   PatientID: {untersuchung.get('PatientID')}")
            print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        
        # Gruppieren nach Datum
        dates = {}
        for u in untersuchungen:
            datum = u.get("Datum")
            if datum:
                dates[datum] = dates.get(datum, 0) + 1
        
        # Sortierte Datumsstatistik anzeigen
        print("\nAnzahl der Untersuchungen pro Datum:")
        for datum in sorted(dates.keys()):
            print(f"   {datum}: {dates[datum]}")
    
    # Prüfen, ob die Tabelle überhaupt existiert und Daten enthält
    print("\nPrüfe die Untersuchungstabelle...")
    table_check = execute_sql("SELECT COUNT(*) AS Anzahl FROM Untersuchung")
    
    if table_check.get("success", False) and "results" in table_check:
        count = table_check["results"][0].get("Anzahl", 0) if table_check["results"] else 0
        print(f"Die Tabelle Untersuchung enthält {count} Datensätze laut SQL-Abfrage.")
        
        if count > 0:
            # Einige Beispieldaten abrufen
            sample_data = execute_sql("SELECT TOP 5 * FROM Untersuchung ORDER BY UntersuchungID DESC")
            if sample_data.get("success", False) and "results" in sample_data:
                print("\nDie neuesten 5 Untersuchungen laut SQL-Abfrage:")
                for i, row in enumerate(sample_data["results"], 1):
                    print(f"\n{i}. UntersuchungID: {row.get('UntersuchungID')}")
                    print(f"   Datum: {row.get('Datum')}")
                    print(f"   PatientID: {row.get('PatientID')}")
            
            # Nach Datum gruppieren
            date_stats = execute_sql("SELECT Datum, COUNT(*) AS Anzahl FROM Untersuchung GROUP BY Datum ORDER BY Datum DESC")
            if date_stats.get("success", False) and "results" in date_stats:
                print("\nUntersuchungen pro Datum laut SQL-Abfrage:")
                for row in date_stats["results"][:10]:  # Zeige die neuesten 10 Datumseinträge
                    print(f"   {row.get('Datum')}: {row.get('Anzahl')}")
    else:
        print(f"Fehler bei der SQL-Abfrage: {table_check.get('error', 'Unbekannter Fehler')}")
