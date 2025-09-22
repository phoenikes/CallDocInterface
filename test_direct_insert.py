"""
Test direkter SQL INSERT statt upsert_data
"""

import requests
import json

def test_direct_sql_insert():
    """Teste direkten SQL INSERT"""
    
    print("Teste direkten SQL INSERT in die Untersuchung-Tabelle...")
    
    # Zuerst prüfen, ob PatientID 12938 existiert
    check_patient = """
    SELECT PatientID, Nachname, Vorname FROM Patient WHERE PatientID = 12938
    """
    
    payload = {
        "sql": check_patient,
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
                if content["results"]:
                    print(f"OK: Patient 12938 existiert: {content['results'][0]}")
                else:
                    print("FEHLER: Patient 12938 existiert NICHT! Erstelle Testpatient...")
                    
                    # Testpatient erstellen
                    create_patient = """
                    INSERT INTO Patient (PatientID, Nachname, Vorname, Geburtsdatum, M1Ziffer)
                    VALUES (12938, 'Test', 'Patient', '01.01.1970', 12938)
                    """
                    
                    payload = {"sql": create_patient, "database": "SQLHK"}
                    response = requests.post(
                        "http://192.168.1.67:7007/tools/execute_sql",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    print(f"Patient erstellt: {response.status_code}")
    
    # Jetzt INSERT in Untersuchung
    print("\nVersuche INSERT in Untersuchung-Tabelle...")
    
    insert_query = """
    INSERT INTO [SQLHK].[dbo].[Untersuchung] 
    (Datum, PatientID, UntersuchungartID, HerzkatheterID, UntersucherAbrechnungID, 
     ZuweiserID, Roentgen, Herzteam, Materialpreis, DRGID)
    VALUES 
    ('22.09.2025', 12938, 1, 1, 1, 2, 1, 1, 0, 1)
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
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if "content" in result:
            content = json.loads(result["content"][0]["text"])
            if content.get("success"):
                print("OK: INSERT erfolgreich!")
                
                # Verifiziere den INSERT
                verify_query = """
                SELECT TOP 5 * FROM Untersuchung 
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
                        if content.get("success") and "results" in content:
                            print(f"\nEingefügte Untersuchungen für 22.09.2025:")
                            for row in content["results"]:
                                print(f"  - UntersuchungID: {row.get('UntersuchungID')}, PatientID: {row.get('PatientID')}")
            else:
                print(f"FEHLER: INSERT fehlgeschlagen: {content.get('error', 'Unbekannter Fehler')}")
    else:
        print(f"HTTP-Fehler: {response.text}")

if __name__ == "__main__":
    test_direct_sql_insert()