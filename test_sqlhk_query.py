"""
Test-Skript zum Abrufen der letzten 10 Untersuchungen aus der SQLHK-Datenbank.
"""

import requests
import json
import logging
from datetime import datetime

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def execute_sql(query, database="SQLHK"):
    """
    Führt eine SQL-Abfrage auf dem MCP SQL Server aus.
    
    Args:
        query: SQL-Abfrage
        database: Name der Datenbank
            
    Returns:
        Ergebnis der Abfrage als Dictionary
    """
    try:
        url = "http://192.168.1.67:7007/tools/execute_sql"
        payload = {
            "sql": query,
            "database": database
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sende Anfrage an {url}")
        logger.info(f"SQL-Abfrage: {query}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        # Extrahiere das eigentliche Ergebnis aus dem MCP-Format
        if "content" in result and len(result["content"]) > 0:
            content_text = result["content"][0].get("text", "{}")
            return json.loads(content_text)
        
        return {"error": "Unerwartetes Antwortformat", "success": False}
        
    except requests.RequestException as e:
        error_msg = f"API-Kommunikationsfehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}
    except json.JSONDecodeError as e:
        error_msg = f"JSON-Dekodierungsfehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}
    except Exception as e:
        error_msg = f"Unerwarteter Fehler: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}

def get_table_structure(table_name):
    """
    Gibt die Struktur einer Tabelle zurück.
    
    Args:
        table_name: Name der Tabelle
        
    Returns:
        Tabellenstruktur als Dictionary
    """
    query = f"""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END AS is_primary_key
        FROM 
            sys.columns c
        INNER JOIN 
            sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN 
            (SELECT ic.column_id, ic.object_id
             FROM sys.index_columns ic
             INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
             WHERE i.is_primary_key = 1) pk 
            ON c.object_id = pk.object_id AND c.column_id = pk.column_id
        WHERE 
            c.object_id = OBJECT_ID('{table_name}')
        ORDER BY 
            c.column_id
    """
    
    return execute_sql(query)

def get_last_10_untersuchungen():
    """
    Ruft die letzten 10 Untersuchungen ab.
    
    Returns:
        Die letzten 10 Untersuchungen als Dictionary
    """
    query = """
        SELECT TOP 10 u.*, p.Nachname, p.Vorname, p.GebDatum, ua.Bezeichnung as UntersuchungartName
        FROM Untersuchung u
        LEFT JOIN Patient p ON u.PIZ = p.PIZ
        LEFT JOIN Untersuchungart ua ON u.UntersuchungartID = ua.UntersuchungartID
        ORDER BY u.UntersuchungID DESC
    """
    
    return execute_sql(query)

def get_last_10_termine():
    """
    Ruft die letzten 10 Termine ab.
    
    Returns:
        Die letzten 10 Termine als Dictionary
    """
    query = """
        SELECT TOP 10 t.*, p.Nachname, p.Vorname, p.GebDatum, ta.Bezeichnung as TerminartName
        FROM Terminvergabe t
        LEFT JOIN Patient p ON t.PIZ = p.PIZ
        LEFT JOIN Terminart ta ON t.TerminartID = ta.TerminartID
        ORDER BY t.TerminID DESC
    """
    
    return execute_sql(query)

if __name__ == "__main__":
    # Tabellenstruktur anzeigen
    print("=== Tabellenstruktur: Untersuchung ===")
    untersuchungen_struktur = get_table_structure("Untersuchung")
    if untersuchungen_struktur.get("success", False):
        print(json.dumps(untersuchungen_struktur["results"], indent=4))
    else:
        print(f"Fehler: {untersuchungen_struktur.get('error', 'Unbekannter Fehler')}")
    
    print("\n=== Tabellenstruktur: Patient ===")
    patient_struktur = get_table_structure("Patient")
    if patient_struktur.get("success", False):
        print(json.dumps(patient_struktur["results"], indent=4))
    else:
        print(f"Fehler: {patient_struktur.get('error', 'Unbekannter Fehler')}")
    
    print("\n=== Tabellenstruktur: Untersuchungart ===")
    untersuchungart_struktur = get_table_structure("Untersuchungart")
    if untersuchungart_struktur.get("success", False):
        print(json.dumps(untersuchungart_struktur["results"], indent=4))
    else:
        print(f"Fehler: {untersuchungart_struktur.get('error', 'Unbekannter Fehler')}")
    
    print("\n=== Tabellenstruktur: Terminvergabe ===")
    terminvergabe_struktur = get_table_structure("Terminvergabe")
    if terminvergabe_struktur.get("success", False):
        print(json.dumps(terminvergabe_struktur["results"], indent=4))
    else:
        print(f"Fehler: {terminvergabe_struktur.get('error', 'Unbekannter Fehler')}")
    
    # Letzte 10 Untersuchungen abrufen
    print("\n=== Letzte 10 Untersuchungen ===")
    untersuchungen = get_last_10_untersuchungen()
    if untersuchungen.get("success", False):
        print(json.dumps(untersuchungen["results"], indent=4))
    else:
        print(f"Fehler: {untersuchungen.get('error', 'Unbekannter Fehler')}")
    
    # Letzte 10 Termine abrufen
    print("\n=== Letzte 10 Termine ===")
    termine = get_last_10_termine()
    if termine.get("success", False):
        print(json.dumps(termine["results"], indent=4))
    else:
        print(f"Fehler: {termine.get('error', 'Unbekannter Fehler')}")
