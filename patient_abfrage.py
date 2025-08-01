"""
Funktionen zum Abrufen von Patientendaten aus der SQLHK-Datenbank.
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

def get_patient_by_id(patient_id, server_url="http://localhost:7007"):
    """
    Ruft einen Patienten anhand seiner PatientID aus der SQLHK-Datenbank ab.
    Verwendet eine zweistufige Abfrage: Erst Wechsel zur SQLHK-Datenbank, dann Abfrage der Patientendaten.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Dictionary mit Patientendaten oder None bei Fehler
    """
    try:
        url = f"{server_url}/api/execute_sql"
        headers = {"Content-Type": "application/json"}
        
        # Schritt 1: Zur SQLHK-Datenbank wechseln
        switch_query = "USE SQLHK;"
        switch_payload = {"query": switch_query, "database": "SQLHK"}
        
        logger.info("Wechsle zur SQLHK-Datenbank...")
        switch_response = requests.post(url, json=switch_payload, headers=headers)
        switch_response.raise_for_status()
        
        # Schritt 2: Patientendaten abfragen
        patient_query = f"SELECT * FROM dbo.Patient WHERE PatientID = {patient_id}"
        patient_payload = {"query": patient_query, "database": "SQLHK"}
        
        logger.info(f"Rufe Patient mit ID {patient_id} ab...")
        patient_response = requests.post(url, json=patient_payload, headers=headers)
        patient_response.raise_for_status()
        
        patient_result = patient_response.json()
        logger.info(f"Patienten-Abfrage-Ergebnis: {json.dumps(patient_result, indent=2)}")
        
        # Schritt 3: Zurück zur SuPDatabase wechseln
        back_query = "USE SuPDatabase;"
        back_payload = {"query": back_query, "database": "SQLHK"}
        
        logger.info("Wechsle zurück zur SuPDatabase...")
        back_response = requests.post(url, json=back_payload, headers=headers)
        back_response.raise_for_status()
        
        # Prüfen, ob Patientendaten gefunden wurden
        if (patient_result.get("success", False) and 
            patient_result.get("rows") and 
            len(patient_result.get("rows", [])) > 0):
            
            patient = patient_result["rows"][0]
            logger.info(f"Patient gefunden: {patient.get('Nachname', 'N/A')}, {patient.get('Vorname', 'N/A')}")
            return patient
        else:
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            
            # Debug-Informationen ausgeben
            if not patient_result.get("success", False):
                logger.error(f"API-Fehler: {patient_result.get('error', 'Unbekannter Fehler')}")
            elif not patient_result.get("rows"):
                logger.warning("Keine Zeilen in der Antwort")
            elif len(patient_result.get("rows", [])) == 0:
                logger.warning("Leere Ergebnisliste")
            
            return None
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Patienten: {str(e)}")
        
        # Versuchen wir, zur SuPDatabase zurückzuwechseln
        try:
            back_query = "USE SuPDatabase;"
            back_payload = {"query": back_query, "database": "SQLHK"}
            requests.post(url, json=back_payload, headers=headers)
            logger.info("Notfall-Rückwechsel zur SuPDatabase durchgeführt")
        except:
            pass
            
        return None
        
        # Versuchen wir, zur SuPDatabase zurückzuwechseln, falls der Fehler beim Datenbankwechsel auftrat
        try:
            fallback_query = "USE SuPDatabase;"
            fallback_payload = {"query": fallback_query, "database": "SQLHK"}
            requests.post(url, json=fallback_payload, headers=headers)
            logger.info("Notfall-Rückwechsel zur SuPDatabase durchgeführt")
        except:
            pass
            
        return None

def get_patient_by_m1ziffer(m1ziffer, server_url="http://localhost:7007"):
    """
    Ruft einen Patienten anhand seiner M1Ziffer aus der SQLHK-Datenbank ab.
    Wechselt zur SQLHK-Datenbank und dann zurück zur SuPDatabase.
    
    Args:
        m1ziffer: M1Ziffer des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Dictionary mit Patientendaten oder None bei Fehler
    """
    try:
        url = f"{server_url}/api/execute_sql"
        
        # Wechsel zur SQLHK-Datenbank und Abfrage der Patientendaten
        query = f"""
        USE SQLHK;
        SELECT * FROM Patient WHERE M1Ziffer = '{m1ziffer}';
        USE SuPDatabase;
        """
        
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Rufe Patient mit M1Ziffer {m1ziffer} ab...")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results") and len(result["results"]) > 0:
            patient = result["results"][0]
            logger.info(f"Patient gefunden: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient
        else:
            logger.warning(f"Patient mit M1Ziffer {m1ziffer} nicht gefunden")
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
    print(f"Adresse: {patient.get('Strasse')}, {patient.get('PLZ')} {patient.get('Stadt')}")
    
    # Alle weiteren Felder ausgeben
    print("\nAlle Felder:")
    for key, value in patient.items():
        if key not in ['PatientID', 'Nachname', 'Vorname', 'Geburtsdatum', 'M1Ziffer', 'krankenkasse', 'versichertennr', 'Strasse', 'PLZ', 'Stadt']:
            print(f"{key}: {value}")

if __name__ == "__main__":
    # Liste von PatientIDs zum Testen
    patient_ids = [12825, 12844, 5538, 12263, 12830]
    
    print("\nTeste Patientenabfrage für mehrere PatientIDs...\n")
    print("-" * 60)
    
    for patient_id in patient_ids:
        print(f"\nTest für PatientID {patient_id}:")
        patient = get_patient_by_id(patient_id)
        
        if patient:
            print(f"[+] Patient gefunden: {patient.get('Nachname', 'N/A')}, {patient.get('Vorname', 'N/A')}")
            print(f"    M1Ziffer: {patient.get('M1Ziffer', 'N/A')}")
            
            # Speichern der Patientendaten als JSON
            with open(f"patient_{patient_id}.json", "w", encoding="utf-8") as f:
                json.dump(patient, f, indent=2, ensure_ascii=False)
            print(f"  Daten gespeichert in patient_{patient_id}.json")
        else:
            print(f"[-] Patient mit ID {patient_id} nicht gefunden")
        
        print("-" * 60)
