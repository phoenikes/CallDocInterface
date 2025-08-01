"""
Überprüft die Untersuchungen für den 24.07.2025 in der SQLHK-Datenbank.
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

def get_untersuchungen_by_date(date_str):
    """
    Ruft Untersuchungen für ein bestimmtes Datum ab.
    
    Args:
        date_str: Datum im Format 'DD.MM.YYYY'
        
    Returns:
        Untersuchungen als Dictionary
    """
    query = f"""
        SELECT u.*, p.Nachname, p.Vorname, p.Geburtsdatum, 
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
    # Untersuchungen für den 24.07.2025 abrufen
    today_date = "24.07.2025"
    print(f"=== Untersuchungen am {today_date} ===")
    untersuchungen = get_untersuchungen_by_date(today_date)
    if untersuchungen.get("success", False):
        if untersuchungen["results"]:
            print(json.dumps(untersuchungen["results"], indent=4, cls=JSONEncoder))
        else:
            print(f"Keine Untersuchungen für das Datum {today_date} gefunden.")
    else:
        print(f"Fehler: {untersuchungen.get('error', 'Unbekannter Fehler')}")
        
    # Versuche auch mit einem anderen Format
    print(f"\n=== Versuche alternatives Datumsformat ===")
    alternative_date = "2025-07-24"
    query = f"""
        SELECT COUNT(*) AS AnzahlUntersuchungen
        FROM Untersuchung
        WHERE Datum = '{alternative_date}'
    """
    result = execute_sql(query)
    if result.get("success", False):
        print(json.dumps(result["results"], indent=4))
    else:
        print(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
        
    # Prüfe, ob es Untersuchungen für heute gibt (mit CONVERT)
    print(f"\n=== Prüfe mit CONVERT-Funktion ===")
    query = f"""
        SELECT COUNT(*) AS AnzahlUntersuchungen
        FROM Untersuchung
        WHERE CONVERT(DATE, Datum, 104) = CONVERT(DATE, '{today_date}', 104)
    """
    result = execute_sql(query)
    if result.get("success", False):
        print(json.dumps(result["results"], indent=4))
    else:
        print(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
        
    # Prüfe, ob es Untersuchungen für heute gibt (mit TRY_CONVERT)
    print(f"\n=== Prüfe mit TRY_CONVERT-Funktion ===")
    query = f"""
        SELECT COUNT(*) AS AnzahlUntersuchungen
        FROM Untersuchung
        WHERE TRY_CONVERT(DATE, Datum, 104) = TRY_CONVERT(DATE, '{today_date}', 104)
    """
    result = execute_sql(query)
    if result.get("success", False):
        print(json.dumps(result["results"], indent=4))
    else:
        print(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
