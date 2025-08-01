"""
Vergleicht CallDoc-Termine mit Untersuchungen in der SQLHK-Datenbank.

Dieses Skript ruft Termine aus der CallDoc-API ab und vergleicht sie mit
den entsprechenden Untersuchungen in der SQLHK-Datenbank. Es zeigt Unterschiede
und fehlende Einträge an.
"""

import requests
import json
import logging
from datetime import datetime, date
from appointment_search import search_appointments

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
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def get_untersuchungen(datum=None, patient_id=None):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ (optional)
        patient_id: PatientID (optional)
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = "http://localhost:7007/api/untersuchung"
        params = {}
        
        if datum:
            params["Datum"] = datum
        if patient_id:
            params["PatientID"] = patient_id
            
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

def get_patient_by_piz(piz):
    """
    Sucht einen Patienten anhand der PIZ in der SQLHK-Datenbank.
    
    Args:
        piz: Patientenidentifikationszahl
        
    Returns:
        PatientID oder None, wenn nicht gefunden
    """
    try:
        # SQL-Abfrage über die API ausführen
        url = "http://localhost:7007/api/execute_sql"
        query = f"SELECT PatientID FROM Patient WHERE PIZ = '{piz}'"
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and len(result.get("results", [])) > 0:
            return result["results"][0]["PatientID"]
        
        logger.warning(f"Patient mit PIZ {piz} nicht gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Suche nach Patient mit PIZ {piz}: {str(e)}")
        return None

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

def compare_appointments_with_untersuchungen(appointments_date):
    """
    Vergleicht CallDoc-Termine mit Untersuchungen in der SQLHK-Datenbank.
    
    Args:
        appointments_date: Datum der Termine im Format YYYY-MM-DD
        
    Returns:
        Dictionary mit Vergleichsergebnissen
    """
    # 1. CallDoc-Termine abrufen
    logger.info(f"Rufe CallDoc-Termine für {appointments_date} ab...")
    appointments = search_appointments(
        appointment_type="Herzkatheter",
        date=appointments_date,
        print_results=False,
        save_json=False
    )
    
    if not appointments:
        logger.error("Keine CallDoc-Termine gefunden")
        return {
            "error": "Keine CallDoc-Termine gefunden",
            "calldoc_count": 0,
            "untersuchung_count": 0,
            "matching": [],
            "only_in_calldoc": [],
            "only_in_sqlhk": []
        }
    
    logger.info(f"{len(appointments)} CallDoc-Termine gefunden")
    
    # 2. Untersuchungen aus SQLHK abrufen
    formatted_date = format_date_for_api(appointments_date)
    if not formatted_date:
        return {
            "error": f"Ungültiges Datumsformat: {appointments_date}",
            "calldoc_count": len(appointments),
            "untersuchung_count": 0,
            "matching": [],
            "only_in_calldoc": appointments,
            "only_in_sqlhk": []
        }
    
    logger.info(f"Rufe Untersuchungen für {formatted_date} ab...")
    untersuchungen = get_untersuchungen(datum=formatted_date)
    
    logger.info(f"{len(untersuchungen)} Untersuchungen gefunden")
    
    # 3. Vergleich durchführen
    matching = []
    only_in_calldoc = []
    only_in_sqlhk = []
    
    # PIZ-zu-PatientID-Mapping erstellen
    piz_to_patient_id = {}
    
    # Prüfen, welche CallDoc-Termine in SQLHK vorhanden sind
    for appointment in appointments:
        piz = appointment.get("patient", {}).get("piz")
        
        if not piz:
            logger.warning(f"Termin ohne PIZ gefunden: {appointment.get('id')}")
            only_in_calldoc.append(appointment)
            continue
        
        # PatientID aus PIZ ermitteln oder aus Cache abrufen
        if piz in piz_to_patient_id:
            patient_id = piz_to_patient_id[piz]
        else:
            patient_id = get_patient_by_piz(piz)
            piz_to_patient_id[piz] = patient_id
        
        if not patient_id:
            logger.warning(f"Patient mit PIZ {piz} nicht in SQLHK gefunden")
            only_in_calldoc.append(appointment)
            continue
        
        # Prüfen, ob eine entsprechende Untersuchung existiert
        found = False
        for untersuchung in untersuchungen:
            if untersuchung.get("PatientID") == patient_id:
                matching.append({
                    "calldoc": appointment,
                    "sqlhk": untersuchung
                })
                found = True
                break
        
        if not found:
            only_in_calldoc.append(appointment)
    
    # Prüfen, welche SQLHK-Untersuchungen nicht in CallDoc vorhanden sind
    for untersuchung in untersuchungen:
        patient_id = untersuchung.get("PatientID")
        if not patient_id:
            continue
        
        found = False
        for match in matching:
            if match["sqlhk"].get("PatientID") == patient_id:
                found = True
                break
        
        if not found:
            only_in_sqlhk.append(untersuchung)
    
    return {
        "calldoc_count": len(appointments),
        "untersuchung_count": len(untersuchungen),
        "matching_count": len(matching),
        "only_in_calldoc_count": len(only_in_calldoc),
        "only_in_sqlhk_count": len(only_in_sqlhk),
        "matching": matching,
        "only_in_calldoc": only_in_calldoc,
        "only_in_sqlhk": only_in_sqlhk
    }

def print_comparison_results(results):
    """
    Gibt die Vergleichsergebnisse formatiert aus.
    
    Args:
        results: Ergebnisse des Vergleichs
    """
    print("\n=== VERGLEICHSERGEBNISSE ===")
    print(f"CallDoc-Termine: {results['calldoc_count']}")
    print(f"SQLHK-Untersuchungen: {results['untersuchung_count']}")
    print(f"Übereinstimmungen: {results['matching_count']}")
    print(f"Nur in CallDoc: {results['only_in_calldoc_count']}")
    print(f"Nur in SQLHK: {results['only_in_sqlhk_count']}")
    
    if results['matching_count'] > 0:
        print("\n--- ÜBEREINSTIMMENDE EINTRÄGE ---")
        for i, match in enumerate(results['matching'], 1):
            calldoc = match['calldoc']
            sqlhk = match['sqlhk']
            print(f"\n{i}. Patient: {calldoc.get('patient', {}).get('lastName', '')}, {calldoc.get('patient', {}).get('firstName', '')}")
            print(f"   CallDoc-ID: {calldoc.get('id')}, Status: {calldoc.get('status')}")
            print(f"   SQLHK-ID: {sqlhk.get('UntersuchungID')}")
    
    if results['only_in_calldoc_count'] > 0:
        print("\n--- NUR IN CALLDOC ---")
        for i, appointment in enumerate(results['only_in_calldoc'], 1):
            print(f"\n{i}. Patient: {appointment.get('patient', {}).get('lastName', '')}, {appointment.get('patient', {}).get('firstName', '')}")
            print(f"   CallDoc-ID: {appointment.get('id')}, Status: {appointment.get('status')}")
            print(f"   PIZ: {appointment.get('patient', {}).get('piz', 'N/A')}")
    
    if results['only_in_sqlhk_count'] > 0:
        print("\n--- NUR IN SQLHK ---")
        for i, untersuchung in enumerate(results['only_in_sqlhk'], 1):
            print(f"\n{i}. PatientID: {untersuchung.get('PatientID')}")
            print(f"   UntersuchungID: {untersuchung.get('UntersuchungID')}")

def save_comparison_results(results, filename):
    """
    Speichert die Vergleichsergebnisse als JSON-Datei.
    
    Args:
        results: Ergebnisse des Vergleichs
        filename: Dateiname
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, cls=JSONEncoder)
        logger.info(f"Ergebnisse wurden in {filename} gespeichert")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Ergebnisse: {str(e)}")

if __name__ == "__main__":
    # Vergleich für den 01.08.2025 durchführen
    target_date = "2025-08-01"
    
    print(f"Vergleiche CallDoc-Termine mit SQLHK-Untersuchungen für {target_date}")
    results = compare_appointments_with_untersuchungen(target_date)
    
    # Ergebnisse ausgeben
    print_comparison_results(results)
    
    # Ergebnisse speichern
    save_comparison_results(
        results, 
        f"vergleich_calldoc_sqlhk_{target_date.replace('-', '')}.json"
    )
