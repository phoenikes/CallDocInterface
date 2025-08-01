"""
Direkte Abfrage eines Patienten aus der SQLHK-Datenbank ohne USE-Befehle.
"""

import requests
import json
import logging

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_patient_by_id(patient_id, server_url="http://localhost:7007"):
    """
    Ruft einen Patienten anhand seiner PatientID direkt aus der SQLHK-Datenbank ab.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Dictionary mit Patientendaten oder None bei Fehler
    """
    try:
        url = f"{server_url}/api/execute_sql"
        
        # Direkte Abfrage der Patientendaten aus SQLHK
        query = f"SELECT * FROM SQLHK.dbo.Patient WHERE PatientID = {patient_id}"
        
        payload = {
            "query": query,
            "database": "SQLHK"  # Direkt SQLHK als Datenbank angeben
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Rufe Patient mit ID {patient_id} direkt aus SQLHK ab...")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results") and len(result["results"]) > 0:
            patient = result["results"][0]
            logger.info(f"Patient gefunden: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient
        else:
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            return None
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Patienten: {str(e)}")
        return None

def print_patient_info(patient):
    """
    Gibt die Informationen eines Patienten aus.
    
    Args:
        patient: Dictionary mit Patientendaten
    """
    if not patient:
        print("Kein Patient gefunden.")
        return
    
    print("\nPatienteninformationen:")
    print(f"PatientID: {patient.get('PatientID')}")
    print(f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
    print(f"Geburtsdatum: {patient.get('Geburtsdatum')}")
    print(f"M1Ziffer: {patient.get('M1Ziffer')}")
    print(f"Krankenkasse: {patient.get('krankenkasse')}")
    print(f"Versichertennummer: {patient.get('versichertennr')}")
    
    # Alle weiteren Felder ausgeben
    print("\nAlle Felder:")
    for key, value in patient.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    # Test mit PatientID 12825
    patient_id = 12825
    patient = get_patient_by_id(patient_id)
    
    if patient:
        print_patient_info(patient)
        
        # Speichern der Patientendaten als JSON
        with open(f"patient_{patient_id}.json", "w", encoding="utf-8") as f:
            json.dump(patient, f, indent=2, ensure_ascii=False)
        print(f"\nPatientendaten wurden in patient_{patient_id}.json gespeichert.")
    else:
        print(f"Patient mit ID {patient_id} konnte nicht abgerufen werden.")
