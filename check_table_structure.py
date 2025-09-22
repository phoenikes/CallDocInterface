"""
Überprüfe die tatsächliche Struktur der Untersuchung-Tabelle
"""

import requests
import json

def check_table_structure():
    """Prüfe welche Spalten wirklich in der Untersuchung-Tabelle existieren"""
    
    print("Prüfe Tabellenstruktur der Untersuchung-Tabelle...")
    
    # Abfrage der Spalteninformationen
    query = """
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        CHARACTER_MAXIMUM_LENGTH
    FROM 
        INFORMATION_SCHEMA.COLUMNS
    WHERE 
        TABLE_NAME = 'Untersuchung' 
        AND TABLE_SCHEMA = 'dbo'
    ORDER BY 
        ORDINAL_POSITION
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
            if content.get("success") and "rows" in content:
                print("\nSpalten in der Untersuchung-Tabelle:")
                print("-" * 50)
                for row in content["rows"]:
                    col_name = row.get("COLUMN_NAME")
                    data_type = row.get("DATA_TYPE")
                    nullable = row.get("IS_NULLABLE")
                    max_length = row.get("CHARACTER_MAXIMUM_LENGTH", "")
                    print(f"{col_name:<30} {data_type:<15} {nullable:<10} {max_length}")
                    
                # Prüfe spezifisch nach den problematischen Spalten
                column_names = [row.get("COLUMN_NAME") for row in content["rows"]]
                print("\n" + "=" * 50)
                print("Existenz-Check der problematischen Spalten:")
                for col in ["Untersuchungtype", "heydokid", "termin_id"]:
                    if col in column_names:
                        print(f"  ✓ {col} existiert")
                    else:
                        print(f"  ✗ {col} existiert NICHT")
            else:
                print(f"Fehler in der Abfrage: {content}")
    else:
        print(f"HTTP-Fehler: {response.status_code}")
        print(response.text)
    
    # Teste auch einen direkten SELECT mit den fraglichen Spalten
    print("\n" + "=" * 50)
    print("Teste direkten SELECT mit allen Spalten:")
    
    test_query = """
    SELECT TOP 1 * FROM Untersuchung
    """
    
    payload = {
        "sql": test_query,
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
            if content.get("success") and "rows" in content and len(content["rows"]) > 0:
                row = content["rows"][0]
                print("\nVorhandene Spalten im Ergebnis:")
                for key in row.keys():
                    print(f"  - {key}")
            else:
                print(f"Keine Daten oder Fehler: {content}")
    else:
        print(f"HTTP-Fehler: {response.status_code}")

if __name__ == "__main__":
    check_table_structure()