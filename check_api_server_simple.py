"""
Überprüft, welcher SQL Server tatsächlich hinter der MCP API steht.
Verwendet einfachere Abfragen, die zuverlässiger funktionieren sollten.
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
    Ruft grundlegende Informationen über den SQL Server ab.
    
    Returns:
        Server-Informationen als Dictionary
    """
    # Abfrage 1: Servername
    query1 = "SELECT @@SERVERNAME AS ServerName"
    
    # Abfrage 2: Hostname
    query2 = "SELECT HOST_NAME() AS HostName"
    
    # Abfrage 3: Aktuelle Datenbank
    query3 = "SELECT DB_NAME() AS CurrentDatabase"
    
    # Abfrage 4: Server-Version
    query4 = "SELECT @@VERSION AS ServerVersion"
    
    # Abfrage 5: Verbindungsinformationen
    query5 = """
        SELECT 
            APP_NAME() AS AppName,
            SUSER_NAME() AS UserName
    """
    
    result1 = execute_sql(query1)
    result2 = execute_sql(query2)
    result3 = execute_sql(query3)
    result4 = execute_sql(query4)
    result5 = execute_sql(query5)
    
    return {
        "server_name": result1.get("results", []),
        "host_name": result2.get("results", []),
        "current_database": result3.get("results", []),
        "server_version": result4.get("results", []),
        "connection_info": result5.get("results", [])
    }

if __name__ == "__main__":
    print("=== Detaillierte Server-Informationen ===")
    server_info = get_server_info()
    
    print("\n=== 1. Server-Name ===")
    print(json.dumps(server_info["server_name"], indent=4))
    
    print("\n=== 2. Host-Name ===")
    print(json.dumps(server_info["host_name"], indent=4))
    
    print("\n=== 3. Aktuelle Datenbank ===")
    print(json.dumps(server_info["current_database"], indent=4))
    
    print("\n=== 4. Server-Version ===")
    print(json.dumps(server_info["server_version"], indent=4))
    
    print("\n=== 5. Verbindungsinformationen ===")
    print(json.dumps(server_info["connection_info"], indent=4))
    
    print("\n=== API-Endpunkt ===")
    print("URL: http://192.168.1.67:7007/tools/execute_sql")
    print("Methode: POST")
    print("Content-Type: application/json")
    print("Body-Format: {\"sql\": \"SQL-ABFRAGE\", \"database\": \"DATENBANKNAME\"}")
    
    # Zusammenfassung
    server_name = server_info["server_name"][0]["ServerName"] if server_info["server_name"] else "Unbekannt"
    host_name = server_info["host_name"][0]["HostName"] if server_info["host_name"] else "Unbekannt"
    current_db = server_info["current_database"][0]["CurrentDatabase"] if server_info["current_database"] else "Unbekannt"
    
    print("\n=== ZUSAMMENFASSUNG ===")
    print(f"Die MCP API (http://192.168.1.67:7007) ist mit folgendem SQL Server verbunden:")
    print(f"Server-Name: {server_name}")
    print(f"Host-Name: {host_name}")
    print(f"Aktuelle Datenbank: {current_db}")
    
    if "SQL-KI" in server_name or "SQL-KI" in host_name:
        print("\nDies ist der KI-Server.")
    elif "SQLSERVER" in server_name or "SQLEXPRESS" in server_name:
        print("\nDies ist der Test-Server (SQLSERVER\\SQLEXPRESS).")
