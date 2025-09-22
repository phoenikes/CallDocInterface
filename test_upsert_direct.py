"""
Test direkter upsert_data Aufruf
"""

import requests
import json
from datetime import datetime

def test_direct_upsert():
    """Teste den upsert_data Endpunkt direkt"""
    
    # Teste erst eine SELECT-Abfrage um sicherzustellen, dass die API läuft
    print("1. Teste API-Verbindung mit SELECT...")
    test_sql = {
        "sql": "SELECT TOP 1 * FROM Untersuchung",
        "database": "SQLHK"
    }
    
    response = requests.post(
        "http://192.168.1.67:7007/tools/execute_sql",
        json=test_sql,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("   OK: API ist erreichbar")
    else:
        print(f"   FEHLER: API-Fehler: {response.status_code}")
        return
    
    # Jetzt teste den upsert_data Endpunkt mit minimalen Daten
    print("\n2. Teste upsert_data mit minimalen Daten...")
    
    # Minimale Daten für einen INSERT
    minimal_data = {
        "table": "Untersuchung",
        "database": "SQLHK",
        "search_fields": {},  # Leer für INSERT
        "update_fields": {
            "Datum": "22.09.2025",
            "PatientID": 1,  # Verwende eine bekannte Test-ID
            "UntersuchungartID": 1,
            "HerzkatheterID": 1,
            "UntersucherAbrechnungID": 1,
            "ZuweiserID": 1,
            "Roentgen": 0,
            "Herzteam": 0,
            "Materialpreis": 0,
            "DRGID": 1
        },
        "key_fields": ["UntersuchungID"]
    }
    
    print(f"   Sende Daten: {json.dumps(minimal_data, indent=2)}")
    
    response = requests.post(
        "http://192.168.1.67:7007/api/upsert_data",
        json=minimal_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Response Text: {response.text}")
        
        # Versuche alternative Ansätze
        print("\n3. Versuche direkten SQL INSERT...")
        
        insert_sql = """
        INSERT INTO [SQLHK].[dbo].[Untersuchung] 
        (Datum, PatientID, UntersuchungartID, HerzkatheterID, UntersucherAbrechnungID, 
         ZuweiserID, Roentgen, Herzteam, Materialpreis, DRGID)
        VALUES 
        ('22.09.2025', 1, 1, 1, 1, 1, 0, 0, 0, 1)
        """
        
        sql_request = {
            "sql": insert_sql,
            "database": "SQLHK"
        }
        
        response = requests.post(
            "http://192.168.1.67:7007/tools/execute_sql",
            json=sql_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   SQL INSERT Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "content" in result:
                content = json.loads(result["content"][0]["text"])
                print(f"   Ergebnis: {content}")
        else:
            print(f"   SQL INSERT Fehler: {response.text}")
    else:
        print(f"   OK: Upsert erfolgreich: {response.json()}")

if __name__ == "__main__":
    test_direct_upsert()