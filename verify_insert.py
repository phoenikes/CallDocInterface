"""
Prüfe ob INSERT funktioniert hat
"""

import requests
import json

def verify_inserts():
    """Prüfe Untersuchungen für heute"""
    
    query = """
    SELECT 
        u.UntersuchungID,
        u.Datum,
        u.PatientID,
        p.Nachname,
        p.Vorname,
        u.UntersuchungartID,
        u.HerzkatheterID
    FROM Untersuchung u
    LEFT JOIN Patient p ON u.PatientID = p.PatientID
    WHERE u.Datum = '22.09.2025'
    ORDER BY u.UntersuchungID DESC
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
                entries = content["results"]
                print(f"Untersuchungen für 22.09.2025: {len(entries)}")
                print("-" * 80)
                for entry in entries:
                    print(f"UntersuchungID: {entry.get('UntersuchungID')} | "
                          f"Patient: {entry.get('Nachname')}, {entry.get('Vorname')} (ID: {entry.get('PatientID')}) | "
                          f"HK: {entry.get('HerzkatheterID')}")
            else:
                print(f"Fehler: {content}")
    else:
        print(f"HTTP-Fehler: {response.status_code}")

if __name__ == "__main__":
    verify_inserts()