"""
Zeigt die Untersuchungen aus der SQLHK-Datenbank für ein bestimmtes Datum an.
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
    Konvertiert ein Datum im Format YYYY-MM-DD in das Format TT.MM.JJJJ für die API.
    
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
        return None

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

def get_patient_details(patient_id):
    """
    Ruft Patientendetails aus der SQLHK-Datenbank über die API ab.
    
    Args:
        patient_id: ID des Patienten
        
    Returns:
        Patientendetails oder None, wenn nicht gefunden
    """
    try:
        # SQL-Abfrage über die API ausführen
        url = "http://localhost:7007/api/execute_sql"
        query = f"""
            SELECT PatientID, Nachname, Vorname, Geburtsdatum, PIZ 
            FROM Patient 
            WHERE PatientID = {patient_id}
        """
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and len(result.get("results", [])) > 0:
            return result["results"][0]
        
        logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Suche nach Patient mit ID {patient_id}: {str(e)}")
        return None

def get_untersuchungsart_name(untersuchungsart_id):
    """
    Ruft den Namen einer Untersuchungsart aus der SQLHK-Datenbank über die API ab.
    
    Args:
        untersuchungsart_id: ID der Untersuchungsart
        
    Returns:
        Name der Untersuchungsart oder None, wenn nicht gefunden
    """
    try:
        # SQL-Abfrage über die API ausführen
        url = "http://localhost:7007/api/execute_sql"
        query = f"""
            SELECT UntersuchungartName 
            FROM Untersuchungart 
            WHERE UntersuchungartID = {untersuchungsart_id}
        """
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and len(result.get("results", [])) > 0:
            return result["results"][0]["UntersuchungartName"]
        
        logger.warning(f"Untersuchungsart mit ID {untersuchungsart_id} nicht gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Suche nach Untersuchungsart mit ID {untersuchungsart_id}: {str(e)}")
        return None

def show_untersuchungen(date_str):
    """
    Zeigt die Untersuchungen für ein bestimmtes Datum an.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
    """
    # Datum für API formatieren
    formatted_date = format_date_for_api(date_str)
    if not formatted_date:
        print(f"Fehler: Ungültiges Datumsformat: {date_str}")
        return
    
    print(f"Rufe Untersuchungen für {formatted_date} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum=formatted_date)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    # Zusätzliche Informationen für jede Untersuchung abrufen
    for i, untersuchung in enumerate(untersuchungen, 1):
        patient_id = untersuchung.get("PatientID")
        untersuchungsart_id = untersuchung.get("UntersuchungartID")
        
        # Patientendetails abrufen
        patient = get_patient_details(patient_id) if patient_id else None
        
        # Untersuchungsart abrufen
        untersuchungsart = get_untersuchungsart_name(untersuchungsart_id) if untersuchungsart_id else None
        
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        
        if patient:
            print(f"   Patient: {patient.get('Nachname')}, {patient.get('Vorname')} (PIZ: {patient.get('PIZ', 'N/A')})")
        else:
            print(f"   PatientID: {patient_id}")
        
        print(f"   Untersuchungsart: {untersuchungsart or untersuchungsart_id}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
        print(f"   UntersucherAbrechnungID: {untersuchung.get('UntersucherAbrechnungID')}")
    
    # Optional: Untersuchungen als JSON-Datei speichern
    filename = f"sqlhk_untersuchungen_{date_str.replace('-', '')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=JSONEncoder)
    print(f"\nUntersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Untersuchungen für den 01.08.2025 abrufen
    target_date = "2025-08-01"
    show_untersuchungen(target_date)
