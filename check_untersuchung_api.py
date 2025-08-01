"""
Ruft Untersuchungen über die API-Endpunkte ab.
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

def get_untersuchungen(datum=None, server_url="http://192.168.1.67:7007"):
    """
    Ruft Untersuchungen über den API-Endpunkt ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ (optional)
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {}
        
        if datum:
            params["Datum"] = datum
            
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        logger.info(f"API-URL: {url}")
        
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

def show_untersuchungen(date_str, server_url="http://192.168.1.67:7007"):
    """
    Zeigt die Untersuchungen für ein bestimmtes Datum an.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
    """
    print(f"Rufe Untersuchungen für {date_str} vom Server {server_url} über die API ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum=date_str, server_url=server_url)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    # Untersuchungen anzeigen
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        print(f"   PatientID: {untersuchung.get('PatientID')}")
        print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
        print(f"   UntersucherAbrechnungID: {untersuchung.get('UntersucherAbrechnungID')}")
        print(f"   ZuweiserID: {untersuchung.get('ZuweiserID')}")
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
    filename = f"api_untersuchungen_{date_str.replace('.', '')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=JSONEncoder)
    print(f"\nUntersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Untersuchungen für den 31.07.2025 abrufen
    target_date = "31.07.2025"
    server_url = "http://192.168.1.67:7007"  # KI-Server-URL
    
    # Zuerst zur SQLHK-Datenbank wechseln
    try:
        change_db_url = f"{server_url}/api/change_database"
        payload = {"database": "SQLHK"}
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Wechsle zur SQLHK-Datenbank...")
        response = requests.post(change_db_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if result.get("success", False):
            logger.info("Erfolgreich zur SQLHK-Datenbank gewechselt")
        else:
            logger.error(f"Fehler beim Wechseln der Datenbank: {result.get('error', 'Unbekannter Fehler')}")
    except Exception as e:
        logger.error(f"Fehler beim Wechseln der Datenbank: {str(e)}")
    
    # Untersuchungen abrufen und anzeigen
    show_untersuchungen(target_date, server_url)
