"""
MS SQL Server API Client

Diese Datei enthält die MsSqlApiClient-Klasse zur Kommunikation mit der MS SQL Server API.
Sie bietet Methoden für SQL-Ausführung und Upsert-Operationen, insbesondere für die
Untersuchungstabelle in der SQLHK-Datenbank.

Autor: Markus
Datum: 31.07.2025
"""

import requests
import json
import logging
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional, Union

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8"
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

class MsSqlApiClient:
    """
    Client für die Kommunikation mit der MS SQL Server API.
    
    Diese Klasse bietet Methoden für die Ausführung von SQL-Abfragen und
    Upsert-Operationen auf der MS SQL Server-Datenbank über die API.
    """
    
    def __init__(self, base_url: str = "http://192.168.1.67:7007"):
        """
        Initialisiert den MS SQL Server API Client.
        
        Args:
            base_url: Basis-URL der API (Standard: http://192.168.1.67:7007)
        """
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def execute_sql(self, query: str, database: str = "SQLHK", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Führt eine SQL-Abfrage auf dem MS SQL Server aus.
        
        Args:
            query: SQL-Abfrage
            database: Name der Datenbank (Standard: SQLHK)
            params: Parameter für parametrisierte Abfragen
            
        Returns:
            Ergebnis der Abfrage als Dictionary
        """
        try:
            url = f"{self.base_url}/tools/execute_sql"
            payload = {
                "sql": query,
                "database": database
            }
            
            if params:
                payload["params"] = params
            
            logger.info(f"Sende Anfrage an {url}")
            logger.info(f"SQL-Abfrage: {query}")
            logger.info(f"Datenbank: {database}")
            
            response = requests.post(url, json=payload, headers=self.headers)
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
    
    def check_upsert_data(self, table: str, search_fields: Dict[str, Any], 
                         update_fields: Dict[str, Any], key_fields: List[str], 
                         database: str = "SQLHK") -> Dict[str, Any]:
        """
        Prüft, ob ein Datensatz existiert und validiert die Daten für Insert/Update-Operationen.
        
        Args:
            table: Name der Tabelle
            search_fields: Felder für die Suche nach existierenden Datensätzen
            update_fields: Zu aktualisierende Felder
            key_fields: Schlüsselfelder für die Suche
            database: Name der Datenbank (Standard: SQLHK)
            
        Returns:
            Ergebnis der Prüfung als Dictionary
        """
        try:
            url = f"{self.base_url}/api/check_upsert_data"
            payload = {
                "table": table,
                "database": database,
                "search_fields": search_fields,
                "update_fields": update_fields,
                "key_fields": key_fields
            }
            
            logger.info(f"Sende Anfrage an {url}")
            logger.info(f"Payload: {json.dumps(payload, cls=JSONEncoder)}")
            
            response = requests.post(url, data=json.dumps(payload, cls=JSONEncoder), headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
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
    
    def upsert_data(self, table: str, search_fields: Dict[str, Any], 
                   update_fields: Dict[str, Any], key_fields: List[str], 
                   database: str = "SQLHK") -> Dict[str, Any]:
        """
        Führt eine Insert- oder Update-Operation durch, abhängig davon, ob der Datensatz existiert.
        
        Args:
            table: Name der Tabelle
            search_fields: Felder für die Suche nach existierenden Datensätzen
            update_fields: Zu aktualisierende Felder
            key_fields: Schlüsselfelder für die Suche
            database: Name der Datenbank (Standard: SQLHK)
            
        Returns:
            Ergebnis der Operation als Dictionary
        """
        try:
            url = f"{self.base_url}/api/upsert_data"
            payload = {
                "table": table,
                "database": database,
                "search_fields": search_fields,
                "update_fields": update_fields,
                "key_fields": key_fields
            }
            
            logger.info(f"Sende Anfrage an {url}")
            logger.info(f"Payload: {json.dumps(payload, cls=JSONEncoder)}")
            
            response = requests.post(url, data=json.dumps(payload, cls=JSONEncoder), headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
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
    
    def get_untersuchungen_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        Ruft alle Untersuchungen für ein bestimmtes Datum aus der SQLHK-Datenbank ab.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
            
        Returns:
            Liste der Untersuchungen als Dictionary
        """
        # Konvertiere das Datum von YYYY-MM-DD zu DD.MM.YYYY für die SQL-Abfrage
        try:
            # Prüfen, ob das Datum bereits im deutschen Format ist
            if '.' in date_str:
                german_date = date_str
                logging.info(f"Datum ist bereits im deutschen Format: {german_date}")
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                german_date = date_obj.strftime("%d.%m.%Y")
                logging.info(f"Konvertiere Datum von {date_str} zu {german_date} für SQL-Abfrage")
        except Exception as e:
            logging.error(f"Fehler bei der Datumskonvertierung: {str(e)}")
            german_date = date_str
        
        # SQL-Abfrage mit dem deutschen Datumsformat
        query = f"""
            SELECT 
                u.*, 
                p.Nachname, p.Vorname, p.Geburtsdatum, 
                ua.UntersuchungartName
            FROM 
                [SQLHK].[dbo].[Untersuchung] u
            LEFT JOIN 
                [SQLHK].[dbo].[Patient] p ON u.PatientID = p.PatientID
            LEFT JOIN 
                [SQLHK].[dbo].[Untersuchungart] ua ON u.UntersuchungartID = ua.UntersuchungartID
            WHERE 
                u.Datum = '{german_date}'
            ORDER BY 
                u.Zeit
        """
        
        return self.execute_sql(query, "SuPDatabase")
    
    def get_patient_by_piz(self, piz: str) -> Dict[str, Any]:
        """
        Sucht einen Patienten anhand der PIZ-Nummer (M1Ziffer) in der SQLHK-Datenbank.
        
        Args:
            piz: Patienten-Identifikationsnummer (M1Ziffer)
            
        Returns:
            Patientendaten als Dictionary oder None, wenn nicht gefunden
        """
        query = f"""
            SELECT 
                *
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                M1Ziffer = '{piz}'
        """
        
        result = self.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            return result["rows"][0]
        
        return None
    
    def get_untersuchungart_by_appointment_type(self, appointment_type_id: int) -> Dict[str, Any]:
        """
        Sucht eine Untersuchungsart anhand der CallDoc-Appointment-Type-ID.
        
        Args:
            appointment_type_id: CallDoc-Appointment-Type-ID
            
        Returns:
            Untersuchungsart als Dictionary oder None, wenn nicht gefunden
        """
        # Hier müsste eine Mapping-Tabelle oder -Logik implementiert werden
        # Für den Moment verwenden wir eine einfache Abfrage nach der ID
        query = f"""
            SELECT 
                *
            FROM 
                Untersuchungart
            WHERE 
                ExterneID = '{appointment_type_id}'
        """
        
        result = self.execute_sql(query)
        
        if result.get("success", False) and result.get("results") and len(result["results"]) > 0:
            return result["results"][0]
        
        return None
    
    def insert_untersuchung(self, untersuchung_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fügt eine neue Untersuchung in die SQLHK-Datenbank ein.
        
        Args:
            untersuchung_data: Daten der Untersuchung
            
        Returns:
            Ergebnis der Operation als Dictionary
        """
        return self.upsert_data(
            table="Untersuchung",
            search_fields={},  # Leere Suche für Insert
            update_fields=untersuchung_data,
            key_fields=["UntersuchungID"]
        )
    
    def update_untersuchung(self, untersuchung_id: int, untersuchung_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aktualisiert eine bestehende Untersuchung in der SQLHK-Datenbank.
        
        Args:
            untersuchung_id: ID der zu aktualisierenden Untersuchung
            untersuchung_data: Zu aktualisierende Daten
            
        Returns:
            Ergebnis der Operation als Dictionary
        """
        return self.upsert_data(
            table="Untersuchung",
            search_fields={"UntersuchungID": untersuchung_id},
            update_fields=untersuchung_data,
            key_fields=["UntersuchungID"]
        )
    
    def delete_untersuchung(self, untersuchung_id: int) -> Dict[str, Any]:
        """
        Löscht eine Untersuchung aus der SQLHK-Datenbank.
        
        Args:
            untersuchung_id: ID der zu löschenden Untersuchung
            
        Returns:
            Ergebnis der Operation als Dictionary
        """
        query = f"""
            DELETE FROM Untersuchung
            WHERE UntersuchungID = {untersuchung_id}
        """
        
        return self.execute_sql(query)


# Beispiel für die Verwendung der Klasse
if __name__ == "__main__":
    # Client initialisieren
    client = MsSqlApiClient()
    
    # Beispiel: Untersuchungen für heute abrufen
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Untersuchungen für {today}:")
    untersuchungen = client.get_untersuchungen_by_date(today)
    
    if untersuchungen.get("success", False):
        print(json.dumps(untersuchungen["results"], indent=4, cls=JSONEncoder))
    else:
        print(f"Fehler: {untersuchungen.get('error', 'Unbekannter Fehler')}")
