"""
Überprüft die Spalten der Tabellen Untersuchung, Patient und Terminvergabe.
"""

import requests
import json
import logging

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
    
    return execute_sql(query)

if __name__ == "__main__":
    tables = ["Untersuchung", "Patient", "Terminvergabe", "Terminart", "Untersuchungart"]
    
    for table in tables:
        print(f"\n=== Spalten der Tabelle {table} ===")
        columns = get_columns(table)
        if columns.get("success", False):
            print(json.dumps(columns["results"], indent=4))
        else:
            print(f"Fehler: {columns.get('error', 'Unbekannter Fehler')}")
        
        print(f"\n=== Beispieldaten aus {table} ===")
        sample_data = get_sample_data(table)
        if sample_data.get("success", False):
            print(json.dumps(sample_data["results"], indent=4))
        else:
            print(f"Fehler: {sample_data.get('error', 'Unbekannter Fehler')}")
