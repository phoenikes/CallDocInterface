"""
Überprüft die Tabellen Untersuchungart und Herzkatheter sowie deren Beziehungen.
Führt dann einen Abruf der Untersuchungen für den 24.07.2025 durch.
"""

import requests
import json
import logging
from datetime import datetime, date, time

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)

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

def get_columns(table_name):
    """
    Gibt die Spalten einer Tabelle zurück.
    
    Args:
        table_name: Name der Tabelle
        
    Returns:
        Liste der Spalten als Dictionary
    """
    query = f"""
        SELECT 
            COLUMN_NAME, 
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM 
            INFORMATION_SCHEMA.COLUMNS
        WHERE 
            TABLE_NAME = '{table_name}'
        ORDER BY 
            ORDINAL_POSITION
    """
    
    return execute_sql(query)

def get_sample_data(table_name, limit=5):
    """
    Gibt Beispieldaten aus einer Tabelle zurück.
    
    Args:
        table_name: Name der Tabelle
        limit: Maximale Anzahl der Datensätze
        
    Returns:
        Beispieldaten als Dictionary
    """
    query = f"""
        SELECT TOP {limit} *
        FROM {table_name}
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

def get_foreign_keys(table_name):
    """
    Gibt die Fremdschlüsselbeziehungen einer Tabelle zurück.
    
    Args:
        table_name: Name der Tabelle
        
    Returns:
        Liste der Fremdschlüsselbeziehungen als Dictionary
    """
    query = f"""
        SELECT 
            fk.name AS FK_Name,
            OBJECT_NAME(fk.parent_object_id) AS Table_Name,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Column_Name,
            OBJECT_NAME(fk.referenced_object_id) AS Referenced_Table_Name,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS Referenced_Column_Name
        FROM 
            sys.foreign_keys AS fk
        INNER JOIN 
            sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        WHERE 
            OBJECT_NAME(fk.parent_object_id) = '{table_name}'
            OR OBJECT_NAME(fk.referenced_object_id) = '{table_name}'
        ORDER BY 
            Table_Name, Column_Name
    """
    
    return execute_sql(query)

def get_untersuchungen_by_date(date_str):
    """
    Ruft Untersuchungen für ein bestimmtes Datum ab.
    
    Args:
        date_str: Datum im Format 'DD.MM.YYYY'
        
    Returns:
        Untersuchungen als Dictionary
    """
    query = f"""
        SELECT u.*, p.Nachname, p.Vorname, p.Geburtsdatum, 
               ua.UntersuchungartName, ua.Untersuchungjsonname,
               h.HerzkatheterName
        FROM Untersuchung u
        LEFT JOIN Patient p ON u.PatientID = p.PatientID
        LEFT JOIN Untersuchungart ua ON u.UntersuchungartID = ua.UntersuchungartID
        LEFT JOIN Herzkatheter h ON u.HerzkatheterID = h.HerzkatheterID
        WHERE u.Datum = '{date_str}'
        ORDER BY u.UntersuchungID
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

if __name__ == "__main__":
    # Spalten der Tabelle Untersuchungart anzeigen
    print("=== Spalten der Tabelle Untersuchungart ===")
    untersuchungart_columns = get_columns("Untersuchungart")
    if untersuchungart_columns.get("success", False):
        print(json.dumps(untersuchungart_columns["results"], indent=4))
    else:
        print(f"Fehler: {untersuchungart_columns.get('error', 'Unbekannter Fehler')}")
    
    # Beispieldaten aus der Tabelle Untersuchungart anzeigen
    print("\n=== Beispieldaten aus Untersuchungart ===")
    untersuchungart_data = get_sample_data("Untersuchungart")
    if untersuchungart_data.get("success", False):
        print(json.dumps(untersuchungart_data["results"], indent=4, cls=JSONEncoder))
    else:
        print(f"Fehler: {untersuchungart_data.get('error', 'Unbekannter Fehler')}")
    
    # Spalten der Tabelle Herzkatheter anzeigen
    print("\n=== Spalten der Tabelle Herzkatheter ===")
    herzkatheter_columns = get_columns("Herzkatheter")
    if herzkatheter_columns.get("success", False):
        print(json.dumps(herzkatheter_columns["results"], indent=4))
    else:
        print(f"Fehler: {herzkatheter_columns.get('error', 'Unbekannter Fehler')}")
    
    # Beispieldaten aus der Tabelle Herzkatheter anzeigen
    print("\n=== Beispieldaten aus Herzkatheter ===")
    herzkatheter_data = get_sample_data("Herzkatheter")
    if herzkatheter_data.get("success", False):
        print(json.dumps(herzkatheter_data["results"], indent=4, cls=JSONEncoder))
    else:
        print(f"Fehler: {herzkatheter_data.get('error', 'Unbekannter Fehler')}")
    
    # Fremdschlüsselbeziehungen der Tabelle Untersuchung anzeigen
    print("\n=== Fremdschlüsselbeziehungen der Tabelle Untersuchung ===")
    untersuchung_fk = get_foreign_keys("Untersuchung")
    if untersuchung_fk.get("success", False):
        print(json.dumps(untersuchung_fk["results"], indent=4))
    else:
        print(f"Fehler: {untersuchung_fk.get('error', 'Unbekannter Fehler')}")
    
    # Fremdschlüsselbeziehungen der Tabelle Untersuchungart anzeigen
    print("\n=== Fremdschlüsselbeziehungen der Tabelle Untersuchungart ===")
    untersuchungart_fk = get_foreign_keys("Untersuchungart")
    if untersuchungart_fk.get("success", False):
        print(json.dumps(untersuchungart_fk["results"], indent=4))
    else:
        print(f"Fehler: {untersuchungart_fk.get('error', 'Unbekannter Fehler')}")
    
    # Fremdschlüsselbeziehungen der Tabelle Herzkatheter anzeigen
    print("\n=== Fremdschlüsselbeziehungen der Tabelle Herzkatheter ===")
    herzkatheter_fk = get_foreign_keys("Herzkatheter")
    if herzkatheter_fk.get("success", False):
        print(json.dumps(herzkatheter_fk["results"], indent=4))
    else:
        print(f"Fehler: {herzkatheter_fk.get('error', 'Unbekannter Fehler')}")
    
    # Untersuchungen für den 24.07.2025 abrufen
    print("\n=== Untersuchungen am 24.07.2025 ===")
    untersuchungen = get_untersuchungen_by_date("24.07.2025")
    if untersuchungen.get("success", False):
        print(json.dumps(untersuchungen["results"], indent=4, cls=JSONEncoder))
    else:
        print(f"Fehler: {untersuchungen.get('error', 'Unbekannter Fehler')}")
