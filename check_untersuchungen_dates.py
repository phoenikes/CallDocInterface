"""
Überprüft die vorhandenen Untersuchungen in der SQLHK-Datenbank.
"""

import requests
import json
import logging
from datetime import datetime, date, time

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)

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
        url = "http://192.168.1.67:7007/tools/execute_sql"
        payload = {
            "sql": query,
            "database": database
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sende Anfrage an {url}")
        logger.info(f"SQL-Abfrage: {query}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        # Extrahiere das eigentliche Ergebnis aus dem MCP-Format
        if "content" in result and len(result["content"]) > 0:
            content_text = result["content"][0].get("text", "{}")
            return json.loads(content_text)
        
        return {"error": "Unerwartetes Antwortformat", "success": False}
        
    except requests.RequestException as e:
        error_msg = f"API-Kommunikationsfehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}
    except json.JSONDecodeError as e:
        error_msg = f"JSON-Dekodierungsfehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}
    except Exception as e:
        error_msg = f"Unerwarteter Fehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}

def get_latest_untersuchungen(limit=10):
    """
    Ruft die neuesten Untersuchungen ab.
    
    Args:
        limit: Maximale Anzahl der Datensätze
        
    Returns:
        Untersuchungen als Dictionary
    """
    query = f"""
        SELECT TOP {limit} u.*, p.Nachname, p.Vorname, p.Geburtsdatum, 
               ua.UntersuchungartName, ua.Untersuchungjsonname,
               h.HerzkatheterName
        FROM Untersuchung u
        LEFT JOIN Patient p ON u.PatientID = p.PatientID
        LEFT JOIN Untersuchungart ua ON u.UntersuchungartID = ua.UntersuchungartID
        LEFT JOIN Herzkatheter h ON u.HerzkatheterID = h.HerzkatheterID
        ORDER BY u.UntersuchungID DESC
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

def get_distinct_dates():
    """
    Ruft die verschiedenen Untersuchungsdaten ab.
    
    Returns:
        Liste der Untersuchungsdaten als Dictionary
    """
    query = """
        SELECT DISTINCT TOP 20 Datum
        FROM Untersuchung
        ORDER BY Datum DESC
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

def count_untersuchungen():
    """
    Zählt die Anzahl der Untersuchungen.
    
    Returns:
        Anzahl der Untersuchungen als Dictionary
    """
    query = """
        SELECT COUNT(*) AS AnzahlUntersuchungen
        FROM Untersuchung
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

if __name__ == "__main__":
    # Anzahl der Untersuchungen zählen
    print("=== Anzahl der Untersuchungen ===")
    count = count_untersuchungen()
    if count.get("success", False):
        print(json.dumps(count["results"], indent=4))
    else:
        print(f"Fehler: {count.get('error', 'Unbekannter Fehler')}")
    
    # Die neuesten Untersuchungen abrufen
    print("\n=== Die neuesten Untersuchungen ===")
    untersuchungen = get_latest_untersuchungen()
    if untersuchungen.get("success", False):
        print(json.dumps(untersuchungen["results"], indent=4, cls=JSONEncoder))
    else:
        print(f"Fehler: {untersuchungen.get('error', 'Unbekannter Fehler')}")
    
    # Die verschiedenen Untersuchungsdaten abrufen
    print("\n=== Vorhandene Untersuchungsdaten (neueste 20) ===")
    dates = get_distinct_dates()
    if dates.get("success", False):
        print(json.dumps(dates["results"], indent=4))
    else:
        print(f"Fehler: {dates.get('error', 'Unbekannter Fehler')}")
