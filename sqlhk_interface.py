"""
SQLHK Datenbank-Interface für die Integration mit CallDoc.

Dieses Modul stellt eine Schnittstelle zur SQLHK-Datenbank bereit, insbesondere
für die Tabellen Untersuchungen, Patient und Untersuchungart.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Logger konfigurieren
logger = logging.getLogger(__name__)

class SQLHKInterface:
    """
    Schnittstelle zur SQLHK-Datenbank über den MCP SQL Server.
    
    Diese Klasse ermöglicht den Zugriff auf die SQLHK-Datenbank und bietet
    Methoden zum Abfragen und Verknüpfen von Daten aus den Tabellen
    Untersuchungen, Patient und Untersuchungart.
    """
    
    def __init__(self, server_url: str = "http://192.168.1.67:7007"):
        """
        Initialisiert die SQLHKInterface-Klasse.
        
        Args:
            server_url: URL des MCP SQL Servers
        """
        self.server_url = server_url
        self.database = "SQLHK"
    
    def _execute_sql(self, query: str) -> Dict[str, Any]:
        """
        Führt eine SQL-Abfrage auf dem MCP SQL Server aus.
        
        Args:
            query: SQL-Abfrage
            
        Returns:
            Ergebnis der Abfrage als Dictionary
            
        Raises:
            Exception: Bei Fehlern in der API-Kommunikation oder SQL-Ausführung
        """
        try:
            url = f"{self.server_url}/tools/execute_sql"
            payload = {
                "sql": query,
                "database": self.database
            }
            headers = {"Content-Type": "application/json"}
            
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
    
    def get_patient_by_piz(self, piz: str) -> Dict[str, Any]:
        """
        Sucht einen Patienten anhand der PIZ-Nummer.
        
        Args:
            piz: Patienten-Identifikationsnummer
            
        Returns:
            Patientendaten als Dictionary
        """
        query = f"""
            SELECT *
            FROM Patient
            WHERE PIZ = '{piz}'
        """
        
        result = self._execute_sql(query)
        
        if result.get("success", False) and "results" in result:
            # Formatiere das Ergebnis in ein ähnliches Format wie die CallDoc-API
            patients = []
            for row in result["results"]:
                patient = {
                    "piz": row.get("PIZ"),
                    "surname": row.get("Nachname"),
                    "name": row.get("Vorname"),
                    "date_of_birth": row.get("GebDatum"),
                    # Weitere Felder können hier hinzugefügt werden
                }
                patients.append(patient)
            
            return {"patients": patients}
        
        return {"patients": [], "error": result.get("error", "Unbekannter Fehler")}
    
    def get_untersuchungen_by_date_range(self, from_date: str, to_date: str, 
                                         untersuchungart_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Sucht Untersuchungen in einem bestimmten Zeitraum.
        
        Args:
            from_date: Startdatum im Format 'YYYY-MM-DD'
            to_date: Enddatum im Format 'YYYY-MM-DD'
            untersuchungart_id: Optionale ID der Untersuchungsart
            
        Returns:
            Untersuchungsdaten als Dictionary
        """
        # Basisabfrage
        query = f"""
            SELECT u.*, p.Nachname, p.Vorname, p.GebDatum, ua.Bezeichnung as UntersuchungartName
            FROM Untersuchungen u
            LEFT JOIN Patient p ON u.PIZ = p.PIZ
            LEFT JOIN Untersuchungart ua ON u.UntersuchungartID = ua.UntersuchungartID
            WHERE u.Datum BETWEEN '{from_date}' AND '{to_date}'
        """
        
        # Filter für Untersuchungsart hinzufügen, falls angegeben
        if untersuchungart_id is not None:
            query += f" AND u.UntersuchungartID = {untersuchungart_id}"
        
        query += " ORDER BY u.Datum, u.Uhrzeit"
        
        result = self._execute_sql(query)
        
        if result.get("success", False) and "results" in result:
            # Formatiere das Ergebnis in ein ähnliches Format wie die CallDoc-API
            appointments = []
            for row in result["results"]:
                # Datum und Uhrzeit kombinieren
                datum = row.get("Datum")
                uhrzeit = row.get("Uhrzeit")
                if datum and uhrzeit:
                    try:
                        # Versuche, ein datetime-Objekt zu erstellen
                        if isinstance(datum, str):
                            datum = datetime.strptime(datum, "%Y-%m-%d").date()
                        if isinstance(uhrzeit, str):
                            uhrzeit_parts = uhrzeit.split(":")
                            hours = int(uhrzeit_parts[0])
                            minutes = int(uhrzeit_parts[1]) if len(uhrzeit_parts) > 1 else 0
                            
                            # Kombiniere Datum und Uhrzeit
                            start_time = datetime.combine(datum, datetime.min.time())
                            start_time = start_time.replace(hour=hours, minute=minutes)
                            
                            # Standarddauer: 30 Minuten
                            end_time = start_time + timedelta(minutes=30)
                            
                            start_time_str = start_time.isoformat()
                            end_time_str = end_time.isoformat()
                        else:
                            start_time_str = None
                            end_time_str = None
                    except (ValueError, TypeError):
                        start_time_str = None
                        end_time_str = None
                else:
                    start_time_str = None
                    end_time_str = None
                
                appointment = {
                    "id": row.get("UntersuchungID"),
                    "piz": row.get("PIZ"),
                    "appointment_type_id": row.get("UntersuchungartID"),
                    "appointment_type": row.get("UntersuchungartName"),
                    "start_time": start_time_str,
                    "end_time": end_time_str,
                    "date": row.get("Datum"),
                    "time": row.get("Uhrzeit"),
                    "last_name": row.get("Nachname"),
                    "first_name": row.get("Vorname"),
                    "date_of_birth": row.get("GebDatum"),
                    # Weitere Felder können hier hinzugefügt werden
                }
                appointments.append(appointment)
            
            return {"data": appointments, "count": len(appointments)}
        
        return {"data": [], "count": 0, "error": result.get("error", "Unbekannter Fehler")}
    
    def get_untersuchungarten(self) -> Dict[str, Any]:
        """
        Gibt alle verfügbaren Untersuchungsarten zurück.
        
        Returns:
            Liste der Untersuchungsarten als Dictionary
        """
        query = """
            SELECT *
            FROM Untersuchungart
            ORDER BY Bezeichnung
        """
        
        result = self._execute_sql(query)
        
        if result.get("success", False) and "results" in result:
            return {"data": result["results"], "count": len(result["results"])}
        
        return {"data": [], "count": 0, "error": result.get("error", "Unbekannter Fehler")}
    
    def describe_tables(self) -> Dict[str, Any]:
        """
        Beschreibt die Struktur der wichtigsten Tabellen.
        
        Returns:
            Tabellenbeschreibungen als Dictionary
        """
        tables = ["Untersuchungen", "Patient", "Untersuchungart"]
        result = {}
        
        for table in tables:
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
                    c.object_id = OBJECT_ID('{table}')
                ORDER BY 
                    c.column_id
            """
            
            table_result = self._execute_sql(query)
            
            if table_result.get("success", False) and "results" in table_result:
                result[table] = table_result["results"]
            else:
                result[table] = {"error": table_result.get("error", "Unbekannter Fehler")}
        
        return result


# Beispiel für die Verwendung
if __name__ == "__main__":
    # Logger konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    
    # Interface initialisieren
    sqlhk = SQLHKInterface()
    
    # Tabellenstruktur ausgeben
    print("Tabellenstruktur:")
    table_structure = sqlhk.describe_tables()
    print(json.dumps(table_structure, indent=4))
    
    # Untersuchungsarten ausgeben
    print("\nUntersuchungsarten:")
    untersuchungarten = sqlhk.get_untersuchungarten()
    print(json.dumps(untersuchungarten, indent=4))
    
    # Beispiel für eine Patientensuche
    print("\nPatientensuche:")
    patient = sqlhk.get_patient_by_piz("12345")
    print(json.dumps(patient, indent=4))
    
    # Beispiel für eine Untersuchungssuche
    print("\nUntersuchungssuche:")
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    untersuchungen = sqlhk.get_untersuchungen_by_date_range(today, next_week)
    print(json.dumps(untersuchungen, indent=4))
