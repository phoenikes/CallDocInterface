"""
Ruft die letzten 10 Untersuchungen aus der SQLHK-Datenbank ab, sortiert nach UntersuchungID.
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

def get_latest_untersuchungen_by_id(limit=10):
    """
    Ruft die neuesten Untersuchungen ab, sortiert nach UntersuchungID.
    
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

def get_total_untersuchungen_count():
    """
    Ruft die Gesamtanzahl der Untersuchungen ab.
    
    Returns:
        Anzahl der Untersuchungen
    """
    query = """
        SELECT COUNT(*) AS AnzahlUntersuchungen
        FROM Untersuchung
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return result["results"][0]["AnzahlUntersuchungen"]
    
    return 0

if __name__ == "__main__":
    # Gesamtanzahl der Untersuchungen abrufen
    total_count = get_total_untersuchungen_count()
    print(f"=== Gesamtanzahl der Untersuchungen: {total_count} ===")
    
    # Die neuesten 10 Untersuchungen abrufen, sortiert nach UntersuchungID
    print("\n=== Die neuesten 10 Untersuchungen (sortiert nach UntersuchungID) ===")
    latest_untersuchungen = get_latest_untersuchungen_by_id(10)
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
        
    # Versuche, Untersuchungen für heute mit einem anderen Datumsformat zu finden
    print(f"\n=== Suche nach Untersuchungen am {today_date} mit verschiedenen Datumsformaten ===")
    query = f"""
        SELECT TOP 10 u.UntersuchungID, u.Datum, u.PatientID, 
               p.Nachname, p.Vorname, p.Geburtsdatum
        FROM Untersuchung u
        LEFT JOIN Patient p ON u.PatientID = p.PatientID
        WHERE u.Datum LIKE '%24%07%2025%' OR u.Datum LIKE '%24%7%2025%' OR u.Datum LIKE '%24%07%25%'
        ORDER BY u.UntersuchungID DESC
    """
    result = execute_sql(query)
    if result.get("success", False):
        if result["results"]:
            print(f"Anzahl der Untersuchungen: {len(result['results'])}")
            print(json.dumps(result["results"], indent=4, cls=JSONEncoder))
        else:
            print(f"Keine Untersuchungen mit ähnlichem Datum gefunden.")
    else:
        print(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
