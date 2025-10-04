"""
Single-Patient Synchronization Module

Komplett separate Implementierung für die Synchronisierung einzelner Patienten
von CallDoc nach SQLHK basierend auf M1Ziffer und Datum.

WICHTIG: Diese Implementierung ist vollständig unabhängig von den bestehenden
Synchronisierungs-Funktionen und ändert diese NICHT.

Autor: Markus
Datum: 04.10.2025
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient

# Logger konfigurieren
logger = logging.getLogger(__name__)


class SinglePatientSynchronizer:
    """
    Synchronisiert einen einzelnen Patienten von CallDoc nach SQLHK.
    
    Diese Klasse ist KOMPLETT UNABHÄNGIG von UntersuchungSynchronizer
    und anderen bestehenden Sync-Klassen.
    """
    
    def __init__(self):
        """Initialisiert den Single-Patient Synchronizer."""
        self.mssql_client = MsSqlApiClient()
        self.stats = {
            "patient_found": False,
            "appointments_found": 0,
            "sqlhk_action": None,  # created, updated, already_exists
            "execution_time_ms": 0,
            "errors": []
        }
        
    def sync_single_patient(self, piz: str, date_str: str, 
                           appointment_type_id: int = 24) -> Dict[str, Any]:
        """
        Hauptmethode für Single-Patient Synchronisation.
        
        Args:
            piz: M1Ziffer des Patienten
            date_str: Datum im Format YYYY-MM-DD
            appointment_type_id: Termintyp (default: 24 für Herzkatheter)
            
        Returns:
            Dictionary mit Sync-Ergebnis
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starte Single-Patient Sync: PIZ={piz}, Datum={date_str}")
            
            # 1. Hole ALLE Termine des Tages aus CallDoc
            logger.info(f"Lade CallDoc-Termine für {date_str}")
            calldoc_client = CallDocInterface(date_str, date_str)
            response = calldoc_client.appointment_search(
                appointment_type_id=appointment_type_id
            )
            
            if 'error' in response:
                raise Exception(f"CallDoc API Fehler: {response}")
            
            all_appointments = response.get('data', [])
            logger.info(f"Gesamt {len(all_appointments)} Termine gefunden")
            
            # 2. Filtere auf Target-Patient
            patient_appointments = [
                a for a in all_appointments
                if str(a.get('piz')) == str(piz)
            ]
            
            self.stats["appointments_found"] = len(patient_appointments)
            logger.info(f"Gefiltert: {len(patient_appointments)} Termine für PIZ {piz}")
            
            if not patient_appointments:
                logger.warning(f"Keine Termine für PIZ {piz} am {date_str}")
                return self._create_response(
                    success=False,
                    message=f"Keine Termine für Patient {piz} am {date_str} gefunden",
                    start_time=start_time
                )
            
            # 3. Patientendaten anreichern
            logger.info(f"Lade Patientendaten für PIZ {piz}")
            patient_response = calldoc_client.get_patient_by_piz(piz)
            
            patient_data = None
            if patient_response and not patient_response.get("error"):
                patients_list = patient_response.get("patients", [])
                if patients_list and len(patients_list) > 0:
                    patient_data = patients_list[0]
                    self.stats["patient_found"] = True
                    
                    # Füge Patientendaten zu jedem Termin hinzu
                    for appointment in patient_appointments:
                        appointment["patient"] = patient_data
                        
            if not patient_data:
                logger.warning(f"Patientendaten für PIZ {piz} nicht in CallDoc gefunden")
                
            # 4. Patient in SQLHK suchen/anlegen
            sqlhk_patient_id = self._ensure_patient_in_sqlhk(piz, patient_data)
            
            if not sqlhk_patient_id:
                raise Exception(f"Konnte Patient {piz} nicht in SQLHK anlegen/finden")
            
            # 5. Untersuchung in SQLHK synchronisieren
            # Konvertiere Datum für SQLHK (DD.MM.YYYY)
            date_parts = date_str.split('-')
            sqlhk_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
            
            sync_result = self._sync_untersuchung_to_sqlhk(
                patient_appointments[0],  # Nehme ersten Termin
                sqlhk_patient_id,
                sqlhk_date,
                appointment_type_id
            )
            
            self.stats["sqlhk_action"] = sync_result["action"]
            
            # 6. Erfolgs-Response erstellen
            return self._create_response(
                success=True,
                message="Single-Patient erfolgreich synchronisiert",
                start_time=start_time,
                patient_data=patient_data,
                sync_result=sync_result
            )
            
        except Exception as e:
            logger.error(f"Fehler bei Single-Patient Sync: {str(e)}")
            self.stats["errors"].append(str(e))
            return self._create_response(
                success=False,
                message=str(e),
                start_time=start_time
            )
    
    def _ensure_patient_in_sqlhk(self, piz: str, 
                                 patient_data: Optional[Dict]) -> Optional[int]:
        """
        Stellt sicher, dass Patient in SQLHK existiert.
        
        Returns:
            PatientID aus SQLHK oder None
        """
        try:
            # Suche Patient via M1Ziffer
            existing = self.mssql_client.get_patient_by_piz(piz)
            
            if existing:
                logger.info(f"Patient {piz} bereits in SQLHK vorhanden")
                return existing.get("PatientID")
            
            # Patient existiert nicht - anlegen wenn Daten vorhanden
            if not patient_data:
                logger.error(f"Kann Patient {piz} nicht anlegen - keine Daten")
                return None
            
            # Patient anlegen
            logger.info(f"Lege neuen Patient {piz} in SQLHK an")
            result = self._create_patient_in_sqlhk(piz, patient_data)
            
            if result and result.get("success"):
                # Neu angelegten Patient suchen für ID
                new_patient = self.mssql_client.get_patient_by_piz(piz)
                if new_patient:
                    return new_patient.get("PatientID")
                    
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei Patient-Verwaltung: {str(e)}")
            return None
    
    def _create_patient_in_sqlhk(self, piz: str, patient_data: Dict) -> Dict[str, Any]:
        """
        Erstellt einen neuen Patienten in SQLHK.
        """
        # Bereite Patient-Daten vor
        name = patient_data.get("surname", "").replace("'", "''")
        vorname = patient_data.get("name", "").replace("'", "''")
        geburtsdatum = patient_data.get("birthdate", "")
        
        # Konvertiere Geburtsdatum wenn nötig
        if geburtsdatum and "T" in geburtsdatum:
            geburtsdatum = geburtsdatum.split("T")[0]
        
        sql_query = f"""
            INSERT INTO [SQLHK].[dbo].[Patient] 
            (M1Ziffer, Name, Vorname, Geburtsdatum, AnlagedatumZeit)
            VALUES 
            ('{piz}', '{name}', '{vorname}', '{geburtsdatum}', GETDATE())
        """
        
        result = self.mssql_client.execute_sql(sql_query, "SQLHK")
        
        if result.get("success"):
            logger.info(f"Patient {piz} erfolgreich angelegt")
        else:
            logger.error(f"Fehler beim Anlegen von Patient {piz}: {result}")
            
        return result
    
    def _sync_untersuchung_to_sqlhk(self, appointment: Dict, 
                                    patient_id: int,
                                    sqlhk_date: str,
                                    appointment_type_id: int) -> Dict[str, Any]:
        """
        Synchronisiert eine Untersuchung nach SQLHK.
        WICHTIG: Führt NUR INSERT oder UPDATE aus, NIEMALS DELETE!
        """
        try:
            # Prüfe ob Untersuchung bereits existiert
            check_query = f"""
                SELECT UntersuchungID 
                FROM [SQLHK].[dbo].[Untersuchung]
                WHERE PatientID = {patient_id}
                AND Datum = '{sqlhk_date}'
                AND UntersuchungartID = (
                    SELECT TOP 1 UntersuchungartID 
                    FROM [SQLHK].[dbo].[Untersuchungart]
                    WHERE appointment_type LIKE '%{appointment_type_id}%'
                )
            """
            
            existing = self.mssql_client.execute_sql(check_query, "SQLHK")
            
            if existing.get("success") and existing.get("rows"):
                # Untersuchung existiert bereits
                untersuchung_id = existing["rows"][0].get("UntersuchungID")
                logger.info(f"Untersuchung existiert bereits: ID={untersuchung_id}")
                
                # Optional: UPDATE durchführen
                # Hier könnte man Felder aktualisieren wenn gewünscht
                
                return {
                    "action": "already_exists",
                    "untersuchung_id": untersuchung_id
                }
            
            # Untersuchung existiert nicht - INSERT
            logger.info(f"Erstelle neue Untersuchung für Patient {patient_id}")
            
            # Hole UntersuchungartID
            untersuchungart_id = self._get_untersuchungart_id(appointment_type_id)
            
            # Hole HerzkatheterID (Room)
            herzkatheter_id = self._get_herzkatheter_id(appointment)
            
            # Hole UntersucherID (Doctor)
            untersucher_id = self._get_untersucher_id(appointment)
            
            # Zeit extrahieren
            uhrzeit = self._extract_time(appointment)
            
            # INSERT Query - verwende die korrekten Spalten aus der SQLHK DB
            insert_query = f"""
                INSERT INTO [SQLHK].[dbo].[Untersuchung]
                (Datum, PatientID, UntersuchungartID, HerzkatheterID, 
                 UntersucherAbrechnungID, ZuweiserID, Roentgen, Herzteam, 
                 Materialpreis, DRGID)
                VALUES
                ('{sqlhk_date}', {patient_id}, {untersuchungart_id}, {herzkatheter_id},
                 1, 2, 1, 1, 0, 1)
            """
            
            result = self.mssql_client.execute_sql(insert_query, "SQLHK")
            
            if result.get("success"):
                logger.info("Untersuchung erfolgreich erstellt")
                return {
                    "action": "created",
                    "untersuchung_id": None  # Könnte man mit SCOPE_IDENTITY() holen
                }
            else:
                raise Exception(f"INSERT fehlgeschlagen: {result}")
                
        except Exception as e:
            logger.error(f"Fehler bei Untersuchungs-Sync: {str(e)}")
            raise
    
    def _get_untersuchungart_id(self, appointment_type_id: int) -> int:
        """Ermittelt die UntersuchungartID für einen appointment_type."""
        query = f"""
            SELECT TOP 1 UntersuchungartID 
            FROM [SQLHK].[dbo].[Untersuchungart]
            WHERE appointment_type LIKE '%{appointment_type_id}%'
        """
        
        result = self.mssql_client.execute_sql(query, "SQLHK")
        
        if result.get("success") and result.get("rows"):
            return result["rows"][0].get("UntersuchungartID")
        
        # Fallback auf Standard
        logger.warning(f"Keine Untersuchungsart für Type {appointment_type_id}, nutze Standard")
        return 1
    
    def _get_herzkatheter_id(self, appointment: Dict) -> int:
        """Ermittelt die HerzkatheterID aus dem Room."""
        room_id = appointment.get("room_id")
        
        if not room_id:
            return 1  # Fallback
        
        query = f"""
            SELECT TOP 1 HerzkatheterID
            FROM [SQLHK].[dbo].[Herzkatheter]
            WHERE room_id = {room_id}
        """
        
        result = self.mssql_client.execute_sql(query, "SQLHK")
        
        if result.get("success") and result.get("rows"):
            return result["rows"][0].get("HerzkatheterID")
            
        return 1  # Fallback
    
    def _get_untersucher_id(self, appointment: Dict) -> int:
        """Ermittelt die UntersucherID aus dem Doctor."""
        employee_id = appointment.get("employee_id")
        
        if not employee_id:
            return 1  # Fallback
            
        query = f"""
            SELECT TOP 1 UntersucherID
            FROM [SQLHK].[dbo].[Untersucher]
            WHERE employee_id = {employee_id}
        """
        
        result = self.mssql_client.execute_sql(query, "SQLHK")
        
        if result.get("success") and result.get("rows"):
            return result["rows"][0].get("UntersucherID")
            
        return 1  # Fallback
    
    def _extract_time(self, appointment: Dict) -> str:
        """Extrahiert die Uhrzeit aus dem Appointment."""
        # Versuche verschiedene Zeitfelder
        start_time = appointment.get("start_time") or appointment.get("date_time")
        
        if not start_time:
            return "08:00"  # Fallback
        
        # Extrahiere Zeit aus ISO-String
        if "T" in str(start_time):
            time_part = str(start_time).split("T")[1]
            if ":" in time_part:
                return time_part.split(":")[0] + ":" + time_part.split(":")[1]
        
        return "08:00"  # Fallback
    
    def _create_response(self, success: bool, message: str, 
                        start_time: datetime,
                        patient_data: Optional[Dict] = None,
                        sync_result: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Erstellt eine standardisierte Response.
        """
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        self.stats["execution_time_ms"] = execution_time
        
        response = {
            "success": success,
            "message": message,
            "execution_time_ms": execution_time,
            "stats": self.stats
        }
        
        if patient_data:
            response["patient"] = {
                "found": True,
                "name": patient_data.get("surname"),
                "vorname": patient_data.get("name"),
                "geburtsdatum": patient_data.get("birthdate")
            }
        
        if sync_result:
            response["sqlhk_sync"] = sync_result
        
        if self.stats.get("errors"):
            response["errors"] = self.stats["errors"]
        
        return response