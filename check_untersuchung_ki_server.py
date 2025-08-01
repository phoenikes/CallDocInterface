"""
Zeigt die Untersuchungen aus der SQLHK-Datenbank auf dem KI-Server für ein bestimmtes Datum an.
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

def get_untersuchungen_by_date(date_str, server_url="http://192.168.1.67:7007"):
    """
    Ruft Untersuchungen für ein bestimmtes Datum aus der SQLHK-Datenbank ab.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    query = f"""
        SELECT 
            u.UntersuchungID, 
            u.Datum, 
            u.HerzkatheterID, 
            u.PatientID, 
            u.UntersucherAbrechnungID, 
            u.ZuweiserID, 
            u.UntersuchungartID, 
            u.Roentgen, 
            u.Herzteam, 
            u.Materialpreis, 
            u.DRGID,
            p.Nachname,
            p.Vorname,
            p.PIZ
        FROM 
            Untersuchung u
            LEFT JOIN Patient p ON u.PatientID = p.PatientID
        WHERE 
            u.Datum = '{date_str}'
        ORDER BY 
            u.UntersuchungID
    """
    
    result = execute_sql(query, database="SQLHK", server_url=server_url)
    
    if result.get("success", False) and "results" in result:
        return result["results"]
    
    logger.error(f"Fehler bei der Abfrage: {result.get('error', 'Unbekannter Fehler')}")
    return []

def show_untersuchungen(date_str, server_url="http://192.168.1.67:7007"):
    """
    Zeigt die Untersuchungen für ein bestimmtes Datum an.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
    """
    print(f"Rufe Untersuchungen für {date_str} vom Server {server_url} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen_by_date(date_str, server_url)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    # Untersuchungen anzeigen
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        print(f"   Patient: {untersuchung.get('Nachname', '')}, {untersuchung.get('Vorname', '')} (PIZ: {untersuchung.get('PIZ', 'N/A')})")
        print(f"   PatientID: {untersuchung.get('PatientID')}")
        print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
        print(f"   UntersucherAbrechnungID: {untersuchung.get('UntersucherAbrechnungID')}")
        print(f"   Materialpreis: {untersuchung.get('Materialpreis')}")
    
    # Gruppieren nach UntersuchungartID
    art_counts = {}
    for u in untersuchungen:
        art_id = u.get("UntersuchungartID", "unbekannt")
        art_counts[art_id] = art_counts.get(art_id, 0) + 1
    
    print("\nAnzahl der Untersuchungen pro UntersuchungartID:")
    for art_id, count in art_counts.items():
        print(f"   UntersuchungartID {art_id}: {count}")
    
    # Optional: Untersuchungen als JSON-Datei speichern
    filename = f"sqlhk_untersuchungen_{date_str.replace('.', '')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=JSONEncoder)
    print(f"\nUntersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Untersuchungen für den 31.07.2025 abrufen
    target_date = "31.07.2025"
    server_url = "http://192.168.1.67:7007"  # KI-Server-URL
    
    show_untersuchungen(target_date, server_url)
