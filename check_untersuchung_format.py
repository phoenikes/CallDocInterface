"""
Ruft Untersuchungen mit verschiedenen Datumsformatierungen ab.
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

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def execute_sql(query, database="SQLHK", server_url="http://192.168.1.67:7007"):
    """
    Führt eine SQL-Abfrage auf dem MCP SQL Server aus.
    
    Args:
        query: SQL-Abfrage
        database: Name der Datenbank
        server_url: URL des API-Servers
            
    Returns:
        Ergebnis der Abfrage als Dictionary
    """
    try:
        url = f"{server_url}/api/execute_sql"
        payload = {
            "query": query,
            "database": database
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sende Anfrage an {url}")
        logger.info(f"SQL-Abfrage: {query}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return result
        
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return {"error": str(e), "success": False}
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return {"error": str(e), "success": False}

def check_date_format():
    """
    Überprüft das Datumsformat in der Datenbank.
    """
    query = "SELECT TOP 10 Datum FROM Untersuchung ORDER BY UntersuchungID DESC"
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        print("Beispiel-Datumsformate in der Datenbank:")
        for row in result["results"]:
            print(f"   {row.get('Datum')}")
    else:
        print(f"Fehler bei der SQL-Abfrage: {result.get('error', 'Unbekannter Fehler')}")

def try_different_date_formats(date_str):
    """
    Versucht verschiedene Datumsformate für die Abfrage.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
    """
    # Format 1: TT.MM.JJJJ (Original)
    format1 = date_str
    
    # Format 2: JJJJ-MM-TT
    parts = date_str.split('.')
    if len(parts) == 3:
        format2 = f"{parts[2]}-{parts[1]}-{parts[0]}"
    else:
        format2 = date_str
    
    # Format 3: Mit CONVERT-Funktion
    query1 = f"""
        SELECT COUNT(*) AS Anzahl
        FROM Untersuchung
        WHERE Datum = '{format1}'
    """
    
    query2 = f"""
        SELECT COUNT(*) AS Anzahl
        FROM Untersuchung
        WHERE Datum = '{format2}'
    """
    
    query3 = f"""
        SELECT COUNT(*) AS Anzahl
        FROM Untersuchung
        WHERE CONVERT(VARCHAR, Datum, 104) = '{format1}'
    """
    
    query4 = f"""
        SELECT COUNT(*) AS Anzahl
        FROM Untersuchung
        WHERE CONVERT(DATE, Datum) = CONVERT(DATE, '{format1}', 104)
    """
    
    print(f"\nVersuche verschiedene Datumsformate für {date_str}:")
    
    print(f"\nFormat 1 (TT.MM.JJJJ): {format1}")
    result1 = execute_sql(query1)
    if result1.get("success", False) and "results" in result1:
        count = result1["results"][0].get("Anzahl", 0) if result1["results"] else 0
        print(f"   Anzahl: {count}")
    else:
        print(f"   Fehler: {result1.get('error', 'Unbekannter Fehler')}")
    
    print(f"\nFormat 2 (JJJJ-MM-TT): {format2}")
    result2 = execute_sql(query2)
    if result2.get("success", False) and "results" in result2:
        count = result2["results"][0].get("Anzahl", 0) if result2["results"] else 0
        print(f"   Anzahl: {count}")
    else:
        print(f"   Fehler: {result2.get('error', 'Unbekannter Fehler')}")
    
    print(f"\nFormat 3 (mit CONVERT VARCHAR): {format1}")
    result3 = execute_sql(query3)
    if result3.get("success", False) and "results" in result3:
        count = result3["results"][0].get("Anzahl", 0) if result3["results"] else 0
        print(f"   Anzahl: {count}")
    else:
        print(f"   Fehler: {result3.get('error', 'Unbekannter Fehler')}")
    
    print(f"\nFormat 4 (mit CONVERT DATE): {format1}")
    result4 = execute_sql(query4)
    if result4.get("success", False) and "results" in result4:
        count = result4["results"][0].get("Anzahl", 0) if result4["results"] else 0
        print(f"   Anzahl: {count}")
    else:
        print(f"   Fehler: {result4.get('error', 'Unbekannter Fehler')}")

def get_all_dates():
    """
    Zeigt alle vorhandenen Datumseinträge in der Untersuchungstabelle an.
    """
    query = "SELECT DISTINCT Datum FROM Untersuchung ORDER BY Datum DESC"
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        dates = [row.get('Datum') for row in result["results"]]
        print(f"\nAlle vorhandenen Datumseinträge ({len(dates)}):")
        for date in dates[:20]:  # Zeige die ersten 20 Datumseinträge
            print(f"   {date}")
        
        if len(dates) > 20:
            print(f"   ... und {len(dates) - 20} weitere")
    else:
        print(f"Fehler bei der SQL-Abfrage: {result.get('error', 'Unbekannter Fehler')}")

if __name__ == "__main__":
    target_date = "31.07.2025"
    
    print("Prüfe das Datumsformat in der Datenbank...")
    check_date_format()
    
    print("\nZeige alle vorhandenen Datumseinträge...")
    get_all_dates()
    
    print("\nVersuche verschiedene Datumsformate...")
    try_different_date_formats(target_date)
