"""
Überprüft die Verbindungsinformationen zum MCP SQL Server.
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
        logger.info(f"Datenbank: {database}")
        
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

def get_server_info():
    """
    Ruft Informationen über den SQL Server ab.
    
    Returns:
        Server-Informationen als Dictionary
    """
    query = """
        SELECT 
            @@SERVERNAME AS ServerName,
            DB_NAME() AS CurrentDatabase,
            @@VERSION AS ServerVersion
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

def get_available_databases():
    """
    Ruft die verfügbaren Datenbanken auf dem SQL Server ab.
    
    Returns:
        Liste der Datenbanken
    """
    query = """
        SELECT name 
        FROM sys.databases
        WHERE database_id > 4  -- Systemdatenbanken ausschließen
        ORDER BY name
    """
    
    result = execute_sql(query, database="master")
    
    if result.get("success", False) and "results" in result:
        return {"success": True, "results": result["results"]}
    
    return result

if __name__ == "__main__":
    # Server-Informationen abrufen
    print("=== Server-Informationen ===")
    server_info = get_server_info()
    if server_info.get("success", False):
        print(json.dumps(server_info["results"], indent=4))
    else:
        print(f"Fehler: {server_info.get('error', 'Unbekannter Fehler')}")
    
    # Verfügbare Datenbanken abrufen
    print("\n=== Verfügbare Datenbanken ===")
    databases = get_available_databases()
    if databases.get("success", False):
        print(json.dumps(databases["results"], indent=4))
    else:
        print(f"Fehler: {databases.get('error', 'Unbekannter Fehler')}")
        
    # MCP API-Endpunkt anzeigen
    print("\n=== MCP API-Endpunkt ===")
    print("URL: http://192.168.1.67:7007/tools/execute_sql")
    print("Methode: POST")
    print("Content-Type: application/json")
    print("Body-Format: {\"sql\": \"SQL-ABFRAGE\", \"database\": \"DATENBANKNAME\"}")
