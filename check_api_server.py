"""
Überprüft, welcher SQL Server tatsächlich hinter der MCP API steht.
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
    Ruft umfassende Informationen über den SQL Server ab.
    
    Returns:
        Server-Informationen als Dictionary
    """
    # Abfrage 1: Servername und Version
    query1 = """
        SELECT 
            @@SERVERNAME AS ServerName,
            @@SERVICENAME AS ServiceName,
            SERVERPROPERTY('MachineName') AS MachineName,
            SERVERPROPERTY('ServerName') AS ServerPropertyName,
            SERVERPROPERTY('InstanceName') AS InstanceName,
            SERVERPROPERTY('IsClustered') AS IsClustered,
            SERVERPROPERTY('ComputerNamePhysicalNetBIOS') AS ComputerNamePhysicalNetBIOS,
            DB_NAME() AS CurrentDatabase,
            @@VERSION AS ServerVersion
    """
    
    # Abfrage 2: Verbindungsinformationen
    query2 = """
        SELECT 
            net_transport, 
            auth_scheme, 
            local_net_address,
            local_tcp_port,
            client_net_address
        FROM sys.dm_exec_connections
        WHERE session_id = @@SPID
    """
    
    # Abfrage 3: Konfigurationsinformationen
    query3 = """
        SELECT 
            name, 
            value, 
            value_in_use, 
            description
        FROM sys.configurations
        WHERE name IN ('remote access', 'remote query timeout', 'remote proc trans')
    """
    
    # Abfrage 4: Aktuelle Verbindungsinformationen
    query4 = """
        SELECT 
            HOST_NAME() AS HostName,
            APP_NAME() AS AppName,
            SUSER_NAME() AS UserName,
            CONNECTIONPROPERTY('protocol_type') AS ProtocolType,
            CONNECTIONPROPERTY('client_net_address') AS ClientNetAddress
    """
    
    result1 = execute_sql(query1)
    result2 = execute_sql(query2)
    result3 = execute_sql(query3)
    result4 = execute_sql(query4)
    
    return {
        "server_info": result1.get("results", []),
        "connection_info": result2.get("results", []),
        "configuration": result3.get("results", []),
        "current_connection": result4.get("results", [])
    }

if __name__ == "__main__":
    print("=== Detaillierte Server-Informationen ===")
    server_info = get_server_info()
    
    print("\n=== 1. Grundlegende Server-Informationen ===")
    print(json.dumps(server_info["server_info"], indent=4))
    
    print("\n=== 2. Verbindungsinformationen ===")
    print(json.dumps(server_info["connection_info"], indent=4))
    
    print("\n=== 3. Server-Konfiguration ===")
    print(json.dumps(server_info["configuration"], indent=4))
    
    print("\n=== 4. Aktuelle Verbindung ===")
    print(json.dumps(server_info["current_connection"], indent=4))
    
    print("\n=== API-Endpunkt ===")
    print("URL: http://192.168.1.67:7007/tools/execute_sql")
    print("Methode: POST")
    print("Content-Type: application/json")
    print("Body-Format: {\"sql\": \"SQL-ABFRAGE\", \"database\": \"DATENBANKNAME\"}")
    
    # Zusammenfassung
    if server_info["server_info"]:
        server_name = server_info["server_info"][0].get("ServerName", "Unbekannt")
        machine_name = server_info["server_info"][0].get("MachineName", "Unbekannt")
        instance_name = server_info["server_info"][0].get("InstanceName", "Unbekannt")
        current_db = server_info["server_info"][0].get("CurrentDatabase", "Unbekannt")
        
        print("\n=== ZUSAMMENFASSUNG ===")
        print(f"Die MCP API (http://192.168.1.67:7007) ist mit folgendem SQL Server verbunden:")
        print(f"Server-Name: {server_name}")
        print(f"Maschinen-Name: {machine_name}")
        print(f"Instanz-Name: {instance_name}")
        print(f"Aktuelle Datenbank: {current_db}")
        
        if "SQL-KI" in server_name or "SQL-KI" in machine_name:
            print("\nDies ist der KI-Server.")
        elif "SQLSERVER" in server_name or "SQLEXPRESS" in instance_name:
            print("\nDies ist der Test-Server (SQLSERVER\\SQLEXPRESS).")
        else:
            print("\nDies ist ein anderer Server als der KI-Server oder der Test-Server.")
