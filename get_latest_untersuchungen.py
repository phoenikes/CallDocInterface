"""
Ruft die letzten 10 Untersuchungen aus der SQLHK-Datenbank ab.
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
        SELECT TOP {limit} u.UntersuchungID, u.Datum, u.PatientID, 
               p.Nachname, p.Vorname, p.Geburtsdatum, 
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

def get_untersuchungen_by_date(date_str):
    """
    Ruft Untersuchungen für ein bestimmtes Datum ab.
    
    Args:
        date_str: Datum im Format 'DD.MM.YYYY'
        
    Returns:
        Untersuchungen als Dictionary
    """
    query = f"""
        SELECT u.UntersuchungID, u.Datum, u.PatientID, 
               p.Nachname, p.Vorname, p.Geburtsdatum, 
               ua.UntersuchungartName, ua.Untersuchungjsonname,
               h.HerzkatheterName
        FROM Untersuchung u
        LEFT JOIN Patient p ON u.PatientID = p.PatientID
        LEFT JOIN Untersuchungart ua ON u.UntersuchungartID = ua.UntersuchungartID
        LEFT JOIN Herzkatheter h ON u.HerzkatheterID = h.HerzkatheterID
        WHERE u.Datum = '{date_str}'
        ORDER BY u.UntersuchungID
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

if __name__ == "__main__":
    # Die neuesten 10 Untersuchungen abrufen
    print("=== Die neuesten 10 Untersuchungen ===")
    latest_untersuchungen = get_latest_untersuchungen(10)
    if latest_untersuchungen.get("success", False):
        if latest_untersuchungen["results"]:
            print(f"Anzahl der Untersuchungen: {len(latest_untersuchungen['results'])}")
            print(json.dumps(latest_untersuchungen["results"], indent=4, cls=JSONEncoder))
        else:
            print("Keine Untersuchungen gefunden.")
    else:
        print(f"Fehler: {latest_untersuchungen.get('error', 'Unbekannter Fehler')}")
    
    # Untersuchungen für den aktuellen Tag (24.07.2025) abrufen
    today_date = "24.07.2025"
    print(f"\n=== Untersuchungen am {today_date} ===")
    today_untersuchungen = get_untersuchungen_by_date(today_date)
    if today_untersuchungen.get("success", False):
        if today_untersuchungen["results"]:
            print(f"Anzahl der Untersuchungen: {len(today_untersuchungen['results'])}")
            print(json.dumps(today_untersuchungen["results"], indent=4, cls=JSONEncoder))
        else:
            print(f"Keine Untersuchungen für das Datum {today_date} gefunden.")
    else:
        print(f"Fehler: {today_untersuchungen.get('error', 'Unbekannter Fehler')}")
