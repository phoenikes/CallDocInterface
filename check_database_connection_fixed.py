"""
Überprüft die Verbindungsinformationen zum MCP SQL Server mit korrekter Konfiguration.
"""

import requests
import json
import logging
import os
import sys

# Pfad zum MCPMS-Projekt hinzufügen, um auf die Konfiguration zuzugreifen
mcpms_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MCPMS")
if mcpms_path not in sys.path:
    sys.path.append(mcpms_path)

try:
    from mcp_sql_server.config import SERVER_NAME, DATABASE_NAME, DRIVER_NAME
    config_available = True
except ImportError:
    # Fallback-Werte, falls die Konfiguration nicht importiert werden kann
    SERVER_NAME = "SQL-KI\\SQL_KI"  # Korrekte Konfiguration aus config.py
    DATABASE_NAME = "SQLHK"
    DRIVER_NAME = "ODBC Driver 17 for SQL Server"
    config_available = False

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
            DB_NAME() AS CurrentDatabase,
            @@VERSION AS ServerVersion
    """
    
    result = execute_sql(query)
    
    if result.get("success", False) and "results" in result:
        # Füge den korrekten Server-Namen aus der Konfiguration hinzu
        result["results"][0]["ServerName"] = SERVER_NAME
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
    # Konfigurationsstatus anzeigen
    print("=== Konfigurationsstatus ===")
    print(f"Konfiguration aus mcp-sql-server importiert: {config_available}")
    print(f"Verwendeter Server-Name: {SERVER_NAME}")
    print(f"Verwendete Datenbank: {DATABASE_NAME}")
    print(f"Verwendeter Treiber: {DRIVER_NAME}")
    
    # Server-Informationen abrufen
    print("\n=== Server-Informationen ===")
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
    
    # Vergleich der Server-Namen
    print("\n=== Vergleich der Server-Namen ===")
    query = "SELECT @@SERVERNAME AS DynamicServerName"
    dynamic_result = execute_sql(query)
    if dynamic_result.get("success", False) and dynamic_result["results"]:
        dynamic_server = dynamic_result["results"][0]["DynamicServerName"]
        print(f"Dynamischer Server-Name (@@SERVERNAME): {dynamic_server}")
        print(f"Konfigurierter Server-Name: {SERVER_NAME}")
        if dynamic_server != SERVER_NAME:
            print("WARNUNG: Der dynamische Server-Name stimmt nicht mit dem konfigurierten Server-Namen überein!")
            print("Dies kann zu Verbindungsproblemen führen. Verwende immer den konfigurierten Server-Namen.")
    else:
        print(f"Fehler beim Abrufen des dynamischen Server-Namens: {dynamic_result.get('error', 'Unbekannter Fehler')}")
