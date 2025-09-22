"""
Finde einen gültigen Patienten in der Datenbank
"""

import requests
import json

def find_valid_patient():
    """Finde existierende Patienten in der SQLHK-Datenbank"""
    
    print("Suche nach existierenden Patienten in SQLHK...")
    
    # Suche die ersten 10 Patienten
    query = """
    SELECT TOP 10 
        PatientID, 
        Nachname, 
        Vorname, 
        M1Ziffer,
        Geburtsdatum
    FROM Patient
    ORDER BY PatientID
    """
    
    payload = {
        "sql": query,
        "database": "SQLHK"
    }
    
    response = requests.post(
        "http://192.168.1.67:7007/tools/execute_sql",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if "content" in result:
            content = json.loads(result["content"][0]["text"])
            if content.get("success") and "results" in content:
                patients = content["results"]
                print(f"\nGefundene Patienten: {len(patients)}")
                print("-" * 60)
                for patient in patients:
                    print(f"PatientID: {patient.get('PatientID'):6} | "
                          f"Name: {patient.get('Nachname')}, {patient.get('Vorname')} | "
                          f"M1Ziffer: {patient.get('M1Ziffer')}")
                
                if patients:
                    # Verwende den ersten Patienten für einen Test-INSERT
                    test_patient_id = patients[0].get('PatientID')
                    print(f"\n=> Verwende PatientID {test_patient_id} für Tests")
                    
                    # Teste INSERT mit diesem Patienten
                    print(f"\nTeste INSERT mit PatientID {test_patient_id}...")
                    
                    insert_query = f"""
                    INSERT INTO [SQLHK].[dbo].[Untersuchung] 
                    (Datum, PatientID, UntersuchungartID, HerzkatheterID, UntersucherAbrechnungID, 
                     ZuweiserID, Roentgen, Herzteam, Materialpreis, DRGID)
                    VALUES 
                    ('22.09.2025', {test_patient_id}, 1, 1, 1, 2, 1, 1, 0, 1)
                    """
                    
                    payload = {
                        "sql": insert_query,
                        "database": "SQLHK"
                    }
                    
                    response = requests.post(
                        "http://192.168.1.67:7007/tools/execute_sql",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "content" in result:
                            content = json.loads(result["content"][0]["text"])
                            if content.get("success"):
                                print("OK: INSERT erfolgreich!")
                                
                                # Hole die neue UntersuchungID
                                verify_query = """
                                SELECT TOP 1 UntersuchungID, PatientID 
                                FROM Untersuchung 
                                WHERE Datum = '22.09.2025'
                                ORDER BY UntersuchungID DESC
                                """
                                
                                payload = {"sql": verify_query, "database": "SQLHK"}
                                response = requests.post(
                                    "http://192.168.1.67:7007/tools/execute_sql",
                                    json=payload,
                                    headers={"Content-Type": "application/json"}
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    if "content" in result:
                                        content = json.loads(result["content"][0]["text"])
                                        if content.get("success") and "results" in content and content["results"]:
                                            new_entry = content["results"][0]
                                            print(f"Neue Untersuchung erstellt: UntersuchungID={new_entry.get('UntersuchungID')}")
                            else:
                                print(f"FEHLER beim INSERT: {content.get('error')}")
                    else:
                        print(f"HTTP-Fehler: {response.text}")
            else:
                print(f"Keine Patienten gefunden oder Fehler: {content}")
    else:
        print(f"HTTP-Fehler: {response.status_code}")

if __name__ == "__main__":
    find_valid_patient()