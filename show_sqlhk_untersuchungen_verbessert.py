"""
Zeigt Untersuchungen aus der SQLHK-Datenbank für ein bestimmtes Datum an.
Verwendet die verbesserte API-Schnittstelle.
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

def format_date_for_api(date_str):
    """
    Formatiert ein Datum im Format YYYY-MM-DD zu TT.MM.JJJJ für die API.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        
    Returns:
        Datum im Format TT.MM.JJJJ
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        logger.error(f"Ungültiges Datumsformat: {date_str}")
        return date_str

def get_untersuchungen(datum=None, server_url="http://localhost:7007"):
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
        params = {}
        
        if datum:
            params["datum"] = datum  # Beachte: Parameter heißt "datum" (kleingeschrieben)
            
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

def get_patient_details(patient_id, server_url="http://localhost:7007"):
    """
    Ruft Patientendetails aus der SQLHK-Datenbank über die API ab.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Patientendetails als Dictionary
    """
    try:
        url = f"{server_url}/api/execute_sql"
        query = f"SELECT * FROM Patient WHERE PatientID = {patient_id}"
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
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            return {}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Patientendetails: {str(e)}")
        return {}

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

def show_untersuchungen(date_str, server_url="http://localhost:7007"):
    """
    Zeigt die Untersuchungen für ein bestimmtes Datum an.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        server_url: URL des API-Servers
    """
    # Datum für die API formatieren
    api_date = format_date_for_api(date_str)
    
    print(f"Rufe Untersuchungen für {api_date} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum=api_date, server_url=server_url)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    # Untersuchungen anzeigen
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        
        # Patientendetails abrufen und anzeigen
        patient_id = untersuchung.get('PatientID')
        if patient_id:
            patient = get_patient_details(patient_id, server_url)
            if patient:
                print(f"   Patient: {patient.get('Nachname', '')}, {patient.get('Vorname', '')}")
                print(f"   PatientID: {patient_id}")
        
        # Untersuchungsart-Details abrufen und anzeigen
        untersuchungsart_id = untersuchung.get('UntersuchungartID')
        if untersuchungsart_id:
            untersuchungsart = get_untersuchungsart_details(untersuchungsart_id, server_url)
            if untersuchungsart:
                print(f"   Untersuchungsart: {untersuchungsart.get('Bezeichnung', '')}")
                print(f"   UntersuchungartID: {untersuchungsart_id}")
        
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
        untersuchungsart = get_untersuchungsart_details(art_id, server_url)
        bezeichnung = untersuchungsart.get('Bezeichnung', 'Unbekannt')
        print(f"   UntersuchungartID {art_id} ({bezeichnung}): {count}")
    
    # Optional: Untersuchungen als JSON-Datei speichern
    filename = f"sqlhk_untersuchungen_{date_str}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=JSONEncoder)
    print(f"\nUntersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Untersuchungen für den 31.07.2025 abrufen
    target_date = "2025-07-31"
    server_url = "http://localhost:7007"
    
    show_untersuchungen(target_date, server_url)
