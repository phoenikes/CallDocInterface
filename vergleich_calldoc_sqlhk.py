"""
Vergleicht CallDoc-Termine mit SQLHK-Untersuchungen für ein bestimmtes Datum.
"""

import requests
import json
import logging
from datetime import datetime
import sys
import os

# Eigene Module importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from calldoc_interface import CallDocInterface
from constants import APPOINTMENT_TYPE_HKU, APPOINTMENT_STATUS_CREATED

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

def format_date_for_calldoc(date_str):
    """
    Formatiert ein Datum im Format TT.MM.JJJJ zu YYYY-MM-DD für die CallDoc-API.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        
    Returns:
        Datum im Format YYYY-MM-DD
    """
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        logger.error(f"Ungültiges Datumsformat: {date_str}")
        return date_str

def format_date_for_sqlhk(date_str):
    """
    Formatiert ein Datum im Format YYYY-MM-DD zu TT.MM.JJJJ für die SQLHK-API.
    
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

def get_calldoc_appointments(date_str, status=None):
    """
    Ruft Termine aus der CallDoc-API ab.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        status: Optionaler Statusfilter (z.B. 'created', 'canceled')
        
    Returns:
        Liste der Termine
    """
    try:
        # CallDoc-Interface initialisieren
        calldoc = CallDocInterface()
        
        # Termine abrufen
        appointments = calldoc.appointment_search(
            from_date=date_str,
            to_date=date_str,
            appointment_type_id=APPOINTMENT_TYPE_HKU,
            status=status
        )
        
        logger.info(f"{len(appointments)} CallDoc-Termine gefunden")
        return appointments
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der CallDoc-Termine: {str(e)}")
        return []

def get_sqlhk_untersuchungen(date_str, server_url="http://localhost:7007"):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {"datum": date_str}
        
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            logger.info(f"{len(result.get('data', []))} SQLHK-Untersuchungen gefunden")
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

def get_patient_by_piz(piz, calldoc):
    """
    Sucht einen Patienten in CallDoc anhand der PIZ.
    
    Args:
        piz: Patientenidentifikationsnummer
        calldoc: CallDocInterface-Instanz
        
    Returns:
        Patientendaten oder None, wenn nicht gefunden
    """
    try:
        patient = calldoc.get_patient_by_piz(piz)
        return patient
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Patienten mit PIZ {piz}: {str(e)}")
        return None

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

def compare_appointments_with_untersuchungen(appointments, untersuchungen):
    """
    Vergleicht CallDoc-Termine mit SQLHK-Untersuchungen.
    
    Args:
        appointments: Liste der CallDoc-Termine
        untersuchungen: Liste der SQLHK-Untersuchungen
        
    Returns:
        Dictionary mit Vergleichsergebnissen
    """
    # Initialisiere Ergebnisstruktur
    results = {
        "calldoc_count": len(appointments),
        "sqlhk_count": len(untersuchungen),
        "matched": [],
        "only_in_calldoc": [],
        "only_in_sqlhk": []
    }
    
    # Erstelle eine Kopie der Untersuchungen, um sie zu markieren
    untersuchungen_copy = untersuchungen.copy()
    
    # Für jeden CallDoc-Termin
    for appointment in appointments:
        patient_id = appointment.get("patient", {}).get("id")
        patient_piz = appointment.get("patient", {}).get("piz")
        
        # Suche nach passender Untersuchung
        match_found = False
        
        for i, untersuchung in enumerate(untersuchungen_copy):
            # Hier müsste eine Logik zur Zuordnung implementiert werden
            # Da wir keine direkte ID-Zuordnung haben, können wir nach Patientendaten suchen
            
            # Beispiel für eine einfache Zuordnung (muss angepasst werden)
            if patient_piz:
                # Patientendetails abrufen
                patient = get_patient_details(untersuchung.get("PatientID"))
                if patient.get("PatientenID_KIS") == patient_piz:
                    match_found = True
                    results["matched"].append({
                        "calldoc": appointment,
                        "sqlhk": untersuchung
                    })
                    untersuchungen_copy.pop(i)
                    break
        
        if not match_found:
            results["only_in_calldoc"].append(appointment)
    
    # Alle übrigen Untersuchungen sind nur in SQLHK vorhanden
    results["only_in_sqlhk"] = untersuchungen_copy
    
    return results

def display_comparison_results(results):
    """
    Zeigt die Vergleichsergebnisse an.
    
    Args:
        results: Vergleichsergebnisse
    """
    print("\n=== Vergleichsergebnisse ===")
    print(f"CallDoc-Termine: {results['calldoc_count']}")
    print(f"SQLHK-Untersuchungen: {results['sqlhk_count']}")
    print(f"Übereinstimmungen: {len(results['matched'])}")
    print(f"Nur in CallDoc: {len(results['only_in_calldoc'])}")
    print(f"Nur in SQLHK: {len(results['only_in_sqlhk'])}")
    
    if results["matched"]:
        print("\n=== Übereinstimmende Termine/Untersuchungen ===")
        for i, match in enumerate(results["matched"], 1):
            calldoc = match["calldoc"]
            sqlhk = match["sqlhk"]
            print(f"\n{i}. CallDoc: {calldoc.get('id')} - {calldoc.get('patient', {}).get('lastName')}, {calldoc.get('patient', {}).get('firstName')}")
            print(f"   SQLHK: {sqlhk.get('UntersuchungID')} - PatientID: {sqlhk.get('PatientID')}")
    
    if results["only_in_calldoc"]:
        print("\n=== Nur in CallDoc vorhandene Termine ===")
        for i, appointment in enumerate(results["only_in_calldoc"], 1):
            print(f"\n{i}. ID: {appointment.get('id')}")
            print(f"   Patient: {appointment.get('patient', {}).get('lastName')}, {appointment.get('patient', {}).get('firstName')}")
            print(f"   PIZ: {appointment.get('patient', {}).get('piz')}")
            print(f"   Status: {appointment.get('status')}")
    
    if results["only_in_sqlhk"]:
        print("\n=== Nur in SQLHK vorhandene Untersuchungen ===")
        for i, untersuchung in enumerate(results["only_in_sqlhk"], 1):
            print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
            print(f"   PatientID: {untersuchung.get('PatientID')}")
            print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")

def save_comparison_results(results, filename):
    """
    Speichert die Vergleichsergebnisse als JSON-Datei.
    
    Args:
        results: Vergleichsergebnisse
        filename: Name der Ausgabedatei
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, cls=JSONEncoder)
    print(f"\nVergleichsergebnisse wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Datum für den Vergleich (31.07.2025)
    calldoc_date = "2025-07-31"
    sqlhk_date = "31.07.2025"
    
    print(f"Vergleiche CallDoc-Termine mit SQLHK-Untersuchungen für {calldoc_date} / {sqlhk_date}...")
    
    # CallDoc-Termine abrufen (nur erstellte Termine)
    appointments = get_calldoc_appointments(calldoc_date, status=APPOINTMENT_STATUS_CREATED)
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    # Termine und Untersuchungen vergleichen
    comparison_results = compare_appointments_with_untersuchungen(appointments, untersuchungen)
    
    # Ergebnisse anzeigen
    display_comparison_results(comparison_results)
    
    # Ergebnisse speichern
    save_comparison_results(comparison_results, f"vergleich_{calldoc_date}.json")
