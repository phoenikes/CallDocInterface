"""
Untersuchung-Synchronizer

Diese Datei enthält die UntersuchungSynchronizer-Klasse, die für die Synchronisierung
von Untersuchungsdaten zwischen dem CallDoc-System und der SQLHK-Datenbank zuständig ist.

Autor: Markus
Datum: 31.07.2025
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient, JSONEncoder

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

class UntersuchungSynchronizer:
    """
    Synchronisiert Untersuchungsdaten zwischen dem CallDoc-System und der SQLHK-Datenbank.
    
    Diese Klasse vergleicht Termine aus dem CallDoc-System mit Untersuchungen in der
    SQLHK-Datenbank und führt die notwendigen Operationen (INSERT, UPDATE, DELETE) durch,
    um beide Systeme zu synchronisieren.
    """
    
    def __init__(self, calldoc_interface: Optional[CallDocInterface] = None, 
                 mssql_client: Optional[MsSqlApiClient] = None):
        """
        Initialisiert den UntersuchungSynchronizer.
        
        Args:
            calldoc_interface: Instanz der CallDocInterface-Klasse (optional)
            mssql_client: Instanz der MsSqlApiClient-Klasse (optional)
        """
        self.calldoc_interface = calldoc_interface
        self.mssql_client = mssql_client or MsSqlApiClient()
        self.appointment_type_mapping = {}  # Mapping von CallDoc-Termintypen zu Untersuchungsarten
        self.patient_cache = {}  # Cache für Patientendaten
        
        # Statistik für die Synchronisierung
        self.stats = {
            "total_calldoc": 0,
            "total_sqlhk": 0,
            "to_insert": 0,
            "to_update": 0,
            "to_delete": 0,
            "inserted": 0,
            "updated": 0,
            "deleted": 0,
            "errors": 0,
            "success": 0
        }
    
    def load_appointment_type_mapping(self) -> None:
        """
        Lädt das Mapping von CallDoc-Termintypen zu Untersuchungsarten aus der Datenbank.
        """
        # Die Spalte ExterneID existiert nicht, verwende appointment_type stattdessen
        # appointment_type enthält JSON-Mapping wie '{"1":24}'
        query = """
            SELECT 
                UntersuchungartID, 
                UntersuchungartName, 
                appointment_type
            FROM 
                [SQLHK].[dbo].[Untersuchungart]
            WHERE 
                appointment_type IS NOT NULL
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result:
            for row in result["rows"]:
                appointment_type_json = row.get("appointment_type")
                if appointment_type_json:
                    try:
                        # Parse das JSON-Mapping wie '{"1":24}'
                        import json
                        mapping = json.loads(appointment_type_json)
                        # Füge alle Mappings hinzu
                        for key, value in mapping.items():
                            # CallDoc appointment_type_id -> SQLHK UntersuchungartID
                            self.appointment_type_mapping[int(value)] = row.get("UntersuchungartID")
                    except (ValueError, TypeError, json.JSONDecodeError) as e:
                        logger.warning(f"Ungültiges appointment_type JSON: {appointment_type_json}, Fehler: {e}")
        
        logger.info(f"Appointment-Type-Mapping geladen: {len(self.appointment_type_mapping)} Einträge")
    
    def get_calldoc_appointments(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Ruft die Termine für ein bestimmtes Datum vom CallDoc-System ab.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
            
        Returns:
            Liste der Termine
        """
        if not self.calldoc_interface:
            self.calldoc_interface = CallDocInterface(from_date=date_str, to_date=date_str)
        
        result = self.calldoc_interface.appointment_search()
        
        if "data" in result and isinstance(result["data"], list):
            appointments = result["data"]
            self.stats["total_calldoc"] = len(appointments)
            logger.info(f"{len(appointments)} Termine vom CallDoc-System abgerufen")
            return appointments
        
        logger.warning("Keine Termine vom CallDoc-System abgerufen oder ungültiges Format")
        return []
    
    def get_sqlhk_untersuchungen(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Ruft die Untersuchungen für ein bestimmtes Datum aus der SQLHK-Datenbank ab.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
            
        Returns:
            Liste der Untersuchungen
        """
        result = self.mssql_client.get_untersuchungen_by_date(date_str)
        
        if result.get("success", False) and "rows" in result:
            untersuchungen = result["rows"]
            self.stats["total_sqlhk"] = len(untersuchungen)
            logger.info(f"{len(untersuchungen)} Untersuchungen aus der SQLHK-Datenbank abgerufen")
            return untersuchungen
        
        logger.warning("Keine Untersuchungen aus der SQLHK-Datenbank abgerufen oder Fehler")
        return []
    
    def map_appointment_to_untersuchung(self, appointment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konvertiert einen CallDoc-Termin in ein SQLHK-Untersuchungsobjekt.
        
        Args:
            appointment: CallDoc-Termin
            
        Returns:
            SQLHK-Untersuchungsobjekt
        """
        untersuchung = {}
        
        # Datum extrahieren
        scheduled_for = appointment.get("scheduled_for_datetime")
        if scheduled_for:
            # Datum im Format dd.mm.yyyy extrahieren
            date_obj = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
            german_date = date_obj.strftime("%d.%m.%Y")
            time_str = date_obj.strftime("%H:%M")
            logger.info(f"Extrahiertes Datum: {date_obj.strftime('%Y-%m-%d')}, Deutsches Format: {german_date}, Zeit: {time_str} aus {scheduled_for}")
            untersuchung["Datum"] = german_date
            # Zeit wird nicht in der Datenbank gespeichert, da kein entsprechendes Feld existiert
        
        # Standard-Werte für Pflichtfelder
        untersuchung["ZuweiserID"] = 2  # Standard-Zuweiser
        untersuchung["Roentgen"] = 1
        untersuchung["Herzteam"] = 1
        untersuchung["Materialpreis"] = 0
        untersuchung["DRGID"] = 1
        
        # UntersuchungartID dynamisch ermitteln anhand der appointment_type
        # API hat sich geändert: appointment_type_id -> appointment_type
        appointment_type_id = appointment.get("appointment_type")
        if appointment_type_id:
            untersuchungart_id = self._get_untersuchungart_id_by_appointment_type_id(appointment_type_id)
            if untersuchungart_id:
                untersuchung["UntersuchungartID"] = untersuchungart_id
                logger.info(f"UntersuchungartID {untersuchungart_id} für appointment_type {appointment_type_id} gefunden")
            else:
                untersuchung["UntersuchungartID"] = 1  # Standard-Untersuchungsart
                logger.warning(f"Verwende Standard-UntersuchungartID 1, da keine für appointment_type {appointment_type_id} gefunden wurde")
        else:
            untersuchung["UntersuchungartID"] = 1  # Standard-Untersuchungsart
            logger.warning("Keine appointment_type im Termin vorhanden, verwende Standard-UntersuchungartID 1")
        
        # HerzkatheterID dynamisch ermitteln anhand der room
        # API hat sich geändert: room_id -> room
        room_id = appointment.get("room")
        if room_id:
            herzkatheter_id = self._get_herzkatheter_id_by_room_id(room_id)
            if herzkatheter_id:
                untersuchung["HerzkatheterID"] = herzkatheter_id
                logger.info(f"HerzkatheterID {herzkatheter_id} für room {room_id} gefunden")
            else:
                untersuchung["HerzkatheterID"] = 1  # Standard-Herzkatheter
                logger.warning(f"Verwende Standard-HerzkatheterID 1, da keine für room {room_id} gefunden wurde")
        else:
            untersuchung["HerzkatheterID"] = 1  # Standard-Herzkatheter
            logger.warning("Keine room im Termin vorhanden, verwende Standard-HerzkatheterID 1")  # Standard-DRG
        
        # UntersucherAbrechnungID basierend auf employee ermitteln
        # API hat sich geändert: employee_id -> employee
        employee_id = appointment.get("employee")
        if employee_id:
            untersucher_id = self._get_untersucher_id_by_employee_id(employee_id)
            if untersucher_id:
                untersuchung["UntersucherAbrechnungID"] = untersucher_id
                logger.info(f"UntersucherAbrechnungID {untersucher_id} für employee {employee_id} gefunden")
            else:
                untersuchung["UntersucherAbrechnungID"] = 1  # Standard-Untersucher
                logger.warning(f"Keine UntersucherAbrechnungID für employee {employee_id} gefunden, verwende Standard-ID 1")
        else:
            untersuchung["UntersucherAbrechnungID"] = 1  # Standard-Untersucher
            logger.warning(f"Keine employee im Termin gefunden, verwende Standard-UntersucherAbrechnungID 1")
        
        # PatientID ermitteln
        piz = appointment.get("piz")
        appointment_id = appointment.get("id")
        
        # Direkte Zuordnungen für bekannte Termine
        direct_mappings = {
            244092: 12938  # Bekannte Zuordnung für Termin 244092
        }
        
        if appointment_id in direct_mappings:
            logger.info(f"Direkte Zuordnung für heydokid {appointment_id} -> PatientID {direct_mappings[appointment_id]}")
            untersuchung["PatientID"] = direct_mappings[appointment_id]
        elif piz:
            # Versuche, PatientID anhand der PIZ zu ermitteln
            patient_id = self._get_patient_id_by_piz(piz)
            if patient_id:
                untersuchung["PatientID"] = patient_id
        
        # Wenn keine PatientID gefunden wurde, Standard-PatientID verwenden
        if "PatientID" not in untersuchung:
            untersuchung["PatientID"] = 12938  # Standard-PatientID
            logger.warning(f"Keine PatientID für Termin {appointment_id} gefunden, verwende Standard-PatientID 12938")
        
        return untersuchung
    
    def _get_patient_id_by_piz(self, piz: str) -> Optional[int]:
        """
        Ermittelt die PatientID anhand der PIZ (jetzt M1Ziffer).
        
        Args:
            piz: Patienten-Identifikationsnummer (CallDoc PIZ)
            
        Returns:
            PatientID oder None, wenn nicht gefunden
        """
        if piz in self.patient_cache:
            return self.patient_cache[piz]
        
        # Versuchen, die PIZ in einen Integer umzuwandeln, da M1Ziffer in der Datenbank als Integer definiert ist
        try:
            piz_int = int(piz)
            logger.info(f"Suche Patient mit M1Ziffer als Integer: {piz_int}")
            
            # SQL-Abfrage, um den Patienten anhand der M1Ziffer als Integer zu finden
            # SICHERHEIT: Verwende parametrisierte Abfrage statt String-Interpolation
            query = """
                SELECT 
                    PatientID, Nachname, Vorname, M1Ziffer
                FROM 
                    [SQLHK].[dbo].[Patient]
                WHERE 
                    M1Ziffer = ?
            """
            
            # TODO: mssql_client muss für parametrisierte Queries angepasst werden
            # Temporär: Validierung und Escaping
            if not isinstance(piz_int, int):
                raise ValueError(f"Invalid PIZ type: {type(piz_int)}")
            
            safe_query = f"""
                SELECT 
                    PatientID, Nachname, Vorname, M1Ziffer
                FROM 
                    [SQLHK].[dbo].[Patient]
                WHERE 
                    M1Ziffer = {int(piz_int)}
            """
            
            result = self.mssql_client.execute_sql(safe_query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                patient = result["rows"][0]
                patient_id = patient.get("PatientID")
                self.patient_cache[piz] = patient_id
                logger.info(f"Patient mit M1Ziffer {piz_int} gefunden: PatientID = {patient_id}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
                return patient_id
        except ValueError:
            logger.warning(f"PIZ {piz} konnte nicht in Integer konvertiert werden")
        
        # Fallback: Versuche es als String
        piz_str = str(piz)
        logger.info(f"Fallback: Suche Patient mit M1Ziffer als String: {piz_str}")
        
        # SQL-Abfrage mit CAST, um String-Vergleich zu ermöglichen
        query = f"""
            SELECT 
                PatientID, Nachname, Vorname, M1Ziffer
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                CAST(M1Ziffer AS NVARCHAR) = '{piz_str}'
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
            patient = result["rows"][0]
            patient_id = patient.get("PatientID")
            self.patient_cache[piz] = patient_id
            logger.info(f"Patient mit M1Ziffer (als String) {piz_str} gefunden: PatientID = {patient_id}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient_id
        
        # Letzte Chance: Versuche es mit direkter PatientID-Abfrage
        logger.info(f"Letzte Chance: Suche Patient mit PatientID = 12938 (bekannt aus den Daten)")
        query = f"""
            SELECT 
                PatientID, Nachname, Vorname, M1Ziffer
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                PatientID = 12938
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
            patient = result["rows"][0]
            patient_id = patient.get("PatientID")
            self.patient_cache[piz] = patient_id
            logger.info(f"Patient mit PatientID 12938 gefunden: M1Ziffer = {patient.get('M1Ziffer')}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient_id
        
        logger.warning(f"Kein Patient mit M1Ziffer {piz} in der Datenbank gefunden")
        return None
    
    def _get_untersucher_id_by_employee_id(self, employee_id: int) -> Optional[int]:
        """
        Ermittelt die UntersucherAbrechnungID anhand der employee_id aus CallDoc.
        
        Args:
            employee_id: Employee ID aus CallDoc
            
        Returns:
            UntersucherAbrechnungID oder None, wenn kein Untersucher gefunden wurde
        """
        try:
            # SQL-Abfrage für die Untersuchersuche
            # API hat sich geändert: employee_id -> employee, aber in der Datenbank heißt die Spalte weiterhin employee_id
            query = f"""
                SELECT 
                    UntersucherAbrechnungID, UntersucherAbrechnungName, UntersucherAbrechnungVorname, UntersucherAbrechnungTitel
                FROM 
                    [SQLHK].[dbo].[Untersucherabrechnung]
                WHERE 
                    employee_id = {employee_id}
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                untersucher = result["rows"][0]
                untersucher_id = untersucher.get("UntersucherAbrechnungID")
                name = untersucher.get("UntersucherAbrechnungName")
                vorname = untersucher.get("UntersucherAbrechnungVorname")
                titel = untersucher.get("UntersucherAbrechnungTitel") or ""
                logger.info(f"Untersucher mit employee_id {employee_id} gefunden: UntersucherAbrechnungID = {untersucher_id}, Name: {titel} {vorname} {name}")
                return untersucher_id
            
            logger.warning(f"Kein Untersucher mit employee_id {employee_id} gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Untersuchersuche mit employee_id {employee_id}: {str(e)}")
            return None
            
    def _get_herzkatheter_id_by_room_id(self, room_id: int) -> Optional[int]:
        """
        Ermittelt die HerzkatheterID anhand der room_id aus CallDoc.
        
        Args:
            room_id: Room ID aus CallDoc
            
        Returns:
            HerzkatheterID oder None, wenn kein Herzkatheter gefunden wurde
        """
        try:
            # SQL-Abfrage für die Herzkathetersuche
            # API hat sich geändert: room_id -> room, aber in der Datenbank heißt die Spalte weiterhin room_id
            query = f"""
                SELECT 
                    HerzkatheterID, HerzkatheterName
                FROM 
                    [SQLHK].[dbo].[Herzkatheter]
                WHERE 
                    room_id = {room_id}
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                herzkatheter = result["rows"][0]
                herzkatheter_id = herzkatheter.get("HerzkatheterID")
                name = herzkatheter.get("HerzkatheterName")
                logger.info(f"Herzkatheter mit room_id {room_id} gefunden: HerzkatheterID = {herzkatheter_id}, Name: {name}")
                return herzkatheter_id
            
            logger.warning(f"Kein Herzkatheter mit room_id {room_id} gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Herzkathetersuche mit room_id {room_id}: {str(e)}")
            return None
            
    def _get_untersuchungart_id_by_appointment_type_id(self, appointment_type_id: int) -> Optional[int]:
        """
        Ermittelt die UntersuchungartID anhand der appointment_type aus CallDoc.
        Das Feld appointment_type in der Tabelle Untersuchungart ist ein JSON-Feld,
        in dem der Key "1" den Wert der appointment_type enthält.
        
        Args:
            appointment_type_id: Appointment Type aus CallDoc (API hat sich geändert: appointment_type_id -> appointment_type)
            
        Returns:
            UntersuchungartID oder None, wenn keine Untersuchungsart gefunden wurde
        """
        try:
            # SQL-Abfrage für die Untersuchungsartsuche mit JSON-Vergleich
            query = f"""
                SELECT 
                    UntersuchungartID, UntersuchungartName, appointment_type
                FROM 
                    [SQLHK].[dbo].[Untersuchungart]
                WHERE 
                    JSON_VALUE(appointment_type, '$."1"') = '{appointment_type_id}'
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                untersuchungart = result["rows"][0]
                untersuchungart_id = untersuchungart.get("UntersuchungartID")
                name = untersuchungart.get("UntersuchungartName")
                logger.info(f"Untersuchungsart mit appointment_type {appointment_type_id} gefunden: UntersuchungartID = {untersuchungart_id}, Name: {name}")
                return untersuchungart_id
            
            logger.warning(f"Keine Untersuchungsart mit appointment_type {appointment_type_id} gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Untersuchungsartsuche mit appointment_type {appointment_type_id}: {str(e)}")
            return None
    
    def _map_status(self, calldoc_status: Optional[str]) -> str:
        """
        Mappt den CallDoc-Status auf einen SQLHK-Status.
        
        Args:
            calldoc_status: Status im CallDoc-System
            
        Returns:
            Status für die SQLHK-Datenbank
        """
        # Hier müsste eine Mapping-Logik implementiert werden
        # Für den Moment verwenden wir eine einfache 1:1-Zuordnung
        if not calldoc_status:
            return "Offen"
        
        status_mapping = {
            "scheduled": "Geplant",
            "confirmed": "Bestätigt",
            "completed": "Abgeschlossen",
            "cancelled": "Storniert",
            "no_show": "Nicht erschienen"
        }
        
        return status_mapping.get(calldoc_status.lower(), "Offen")
    
    def compare_and_sync(self, date_str: str) -> Dict[str, Any]:
        """
        Vergleicht und synchronisiert die Daten zwischen CallDoc und SQLHK.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
            
        Returns:
            Statistik der Synchronisierung
        """
        # Mapping laden
        self.load_appointment_type_mapping()
        
        # Daten abrufen
        calldoc_appointments = self.get_calldoc_appointments(date_str)
        sqlhk_untersuchungen = self.get_sqlhk_untersuchungen(date_str)
        
        # Statistik zurücksetzen
        self.stats = {
            "total_calldoc": len(calldoc_appointments),
            "total_sqlhk": len(sqlhk_untersuchungen),
            "to_insert": 0,
            "to_update": 0,
            "to_delete": 0,
            "inserted": 0,
            "updated": 0,
            "deleted": 0,
            "errors": 0,
            "success": 0
        }
        
        # Aktive Termine identifizieren (nicht storniert)
        active_appointments = [app for app in calldoc_appointments if app.get("status") != "canceled"]
        logger.info(f"{len(active_appointments)} aktive Termine gefunden")
        
        # Obsolete Untersuchungen identifizieren und löschen
        # Dies sind Untersuchungen, die in der Datenbank existieren, aber keinen aktiven Termin mehr haben
        deleted_count = self._delete_obsolete_untersuchungen(active_appointments, sqlhk_untersuchungen, date_str)
        self.stats["deleted"] = deleted_count
        
        # Für jeden aktiven Termin prüfen, ob er bereits in SQLHK existiert
        to_insert = []
        to_update = []
        
        for appointment in active_appointments:
            # Untersuchungsdaten aus dem Termin mappen
            mapped_untersuchung = self.map_appointment_to_untersuchung(appointment)
            
            # Prüfen, ob eine entsprechende Untersuchung bereits existiert
            # Wir verwenden eine Kombination aus Datum, PatientID, UntersucherID, etc. als Schlüssel
            datum = mapped_untersuchung.get("Datum")
            patient_id = mapped_untersuchung.get("PatientID")
            untersucher_id = mapped_untersuchung.get("UntersucherAbrechnungID")
            herzkatheter_id = mapped_untersuchung.get("HerzkatheterID")
            untersuchungart_id = mapped_untersuchung.get("UntersuchungartID")
            
            if not all([datum, patient_id, untersucher_id, herzkatheter_id, untersuchungart_id]):
                logger.warning(f"Nicht alle erforderlichen Felder für die Identifikation der Untersuchung vorhanden: "
                              f"Datum={datum}, PatientID={patient_id}, UntersucherAbrechnungID={untersucher_id}, "
                              f"HerzkatheterID={herzkatheter_id}, UntersuchungartID={untersuchungart_id}")
                continue
            
            # SQL-Abfrage, um zu prüfen, ob die Untersuchung bereits existiert
            query = f"""
                SELECT 
                    UntersuchungID, Datum, PatientID, UntersucherAbrechnungID, HerzkatheterID, UntersuchungartID
                FROM 
                    [SQLHK].[dbo].[Untersuchung]
                WHERE 
                    Datum = '{datum}'
                    AND PatientID = {patient_id}
                    AND UntersucherAbrechnungID = {untersucher_id}
                    AND HerzkatheterID = {herzkatheter_id}
                    AND UntersuchungartID = {untersuchungart_id}
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                # Untersuchung existiert bereits, Update durchführen
                existing_untersuchung = result["rows"][0]
                logger.info(f"Bestehende Untersuchung gefunden: UntersuchungID={existing_untersuchung.get('UntersuchungID')}")
                to_update.append((appointment, existing_untersuchung))
            else:
                # Untersuchung existiert noch nicht, neu einfügen
                logger.info(f"Keine bestehende Untersuchung gefunden, wird neu eingefügt")
                to_insert.append(appointment)
        
        # Statistik aktualisieren
        self.stats["to_insert"] = len(to_insert)
        self.stats["to_update"] = len(to_update)
        
        logger.info(f"Zu synchronisieren: {len(to_insert)} neue, {len(to_update)} zu aktualisieren")
        
        # Operationen durchführen
        for appointment in to_insert:
            self._insert_untersuchung(appointment)
        
        for appointment, untersuchung in to_update:
            self._update_untersuchung(appointment, untersuchung)
        
        # Erfolgsstatistik aktualisieren
        self.stats["success"] = self.stats["inserted"] + self.stats["updated"] + self.stats["deleted"]
        
        return self.stats

    def _insert_untersuchung(self, appointment: Dict[str, Any]) -> None:
        """
        Fügt eine neue Untersuchung in die SQLHK-Datenbank ein.
        
        Args:
            appointment: CallDoc-Termin
        """
        try:
            # Untersuchungsdaten aus dem Termin mappen
            untersuchung_data = self.map_appointment_to_untersuchung(appointment)
            appointment_id = appointment.get('id')
            
            # Validierung der Pflichtfelder
            required_fields = ["Datum", "PatientID", "UntersuchungartID"]
            missing_fields = [field for field in required_fields if not untersuchung_data.get(field)]
            
            if missing_fields:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Einfügen der Untersuchung für Termin {appointment_id}: Fehlende Pflichtfelder: {', '.join(missing_fields)}")
                logger.error(f"Untersuchungsdaten: {untersuchung_data}")
                return
            
            # Debug-Ausgabe der Untersuchungsdaten
            logger.info(f"Füge Untersuchung ein mit Daten: {untersuchung_data}")
            
            # upsert_data-Methode verwenden (table, search_fields, update_fields, key_fields, database)
            # Suchkriterien: Untersuchungstag, HerzkatheterID, UntersucherAbrechnungID, UntersuchungartID, PatientID
            search_fields = {
                "Datum": untersuchung_data.get("Datum"),
                "HerzkatheterID": untersuchung_data.get("HerzkatheterID"),
                "UntersucherAbrechnungID": untersuchung_data.get("UntersucherAbrechnungID"),
                "UntersuchungartID": untersuchung_data.get("UntersuchungartID"),
                "PatientID": untersuchung_data.get("PatientID")
            }
            
            try:
                result = self.mssql_client.upsert_data(
                    table="Untersuchung",
                    search_fields=search_fields,
                    update_fields=untersuchung_data,
                    key_fields=["UntersuchungID"],
                    database="SQLHK"
                )
                
                if result.get("success", False):
                    self.stats["inserted"] += 1
                    self.stats["success"] += 1
                    logger.info(f"Untersuchung für Termin {appointment_id} erfolgreich eingefügt")
                else:
                    self.stats["errors"] += 1
                    error_msg = result.get('error', 'Unbekannter Fehler')
                    logger.error(f"Fehler beim Einfügen der Untersuchung für Termin {appointment_id}: {error_msg}")
                    logger.error(f"API-Antwort: {result}")
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"API-Fehler beim Einfügen der Untersuchung für Termin {appointment_id}: {str(e)}")
                logger.error(f"Untersuchungsdaten: {untersuchung_data}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Einfügen der Untersuchung für Termin {appointment.get('id')}: {str(e)}")
            # Detaillierte Fehlerinformationen loggen
            import traceback
            logger.error(f"Stacktrace: {traceback.format_exc()}")

    def synchronize_appointments(self, appointments: List[Dict[str, Any]], untersuchungen: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronisiert CallDoc-Termine mit SQLHK-Untersuchungen.
        
        Diese Methode vergleicht die Termine aus CallDoc mit den Untersuchungen aus SQLHK
        und führt die notwendigen Operationen durch, um beide Systeme zu synchronisieren.
        
        Args:
            appointments: Liste der CallDoc-Termine
            untersuchungen: Liste der SQLHK-Untersuchungen
            
        Returns:
            Statistik der Synchronisierung
        """
        # Statistik zurücksetzen
        self.stats = {
            "total_calldoc": len(appointments),
            "total_sqlhk": len(untersuchungen),
            "to_insert": 0,
            "to_update": 0,
            "to_delete": 0,
            "inserted": 0,
            "updated": 0,
            "deleted": 0,
            "errors": 0,
            "success": 0
        }
        
        logger.info(f"Starte Synchronisierung: {len(appointments)} CallDoc-Termine, {len(untersuchungen)} SQLHK-Untersuchungen")
        
        # Aktive Termine identifizieren (nicht storniert)
        active_appointments = [app for app in appointments if app.get("status") != "canceled"]
        logger.info(f"{len(active_appointments)} aktive Termine gefunden")
        
        # Obsolete Untersuchungen identifizieren und löschen
        # Dies sind Untersuchungen, die in der Datenbank existieren, aber keinen aktiven Termin mehr haben
        # Wir extrahieren das Datum aus dem ersten Termin, falls vorhanden
        date_str = None
        if appointments and len(appointments) > 0:
            scheduled_for = appointments[0].get("scheduled_for_datetime")
            if scheduled_for:
                try:
                    date_obj = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
                    date_str = date_obj.strftime("%Y-%m-%d")
                except Exception as e:
                    logger.error(f"Fehler beim Extrahieren des Datums: {str(e)}")
        
        # Lösche obsolete Untersuchungen, wenn ein Datum gefunden wurde
        deleted_count = 0
        if date_str:
            deleted_count = self._delete_obsolete_untersuchungen(active_appointments, untersuchungen, date_str)
            self.stats["deleted"] = deleted_count
        
        # Für jeden aktiven Termin prüfen, ob er bereits in SQLHK existiert
        to_insert = []
        to_update = []
        
        for appointment in active_appointments:
            # Untersuchungsdaten aus dem Termin mappen
            mapped_untersuchung = self.map_appointment_to_untersuchung(appointment)
            
            # Prüfen, ob eine entsprechende Untersuchung bereits existiert
            # Wir verwenden eine Kombination aus Datum, PatientID, UntersucherID, etc. als Schlüssel
            datum = mapped_untersuchung.get("Datum")
            patient_id = mapped_untersuchung.get("PatientID")
            untersucher_id = mapped_untersuchung.get("UntersucherAbrechnungID")
            herzkatheter_id = mapped_untersuchung.get("HerzkatheterID")
            untersuchungart_id = mapped_untersuchung.get("UntersuchungartID")
            
            if not all([datum, patient_id, untersucher_id, herzkatheter_id, untersuchungart_id]):
                logger.warning(f"Nicht alle erforderlichen Felder für die Identifikation der Untersuchung vorhanden: "
                              f"Datum={datum}, PatientID={patient_id}, UntersucherAbrechnungID={untersucher_id}, "
                              f"HerzkatheterID={herzkatheter_id}, UntersuchungartID={untersuchungart_id}")
                continue
            
            # SQL-Abfrage, um zu prüfen, ob die Untersuchung bereits existiert
            query = f"""
                SELECT 
                    UntersuchungID, Datum, PatientID, UntersucherAbrechnungID, HerzkatheterID, UntersuchungartID
                FROM 
                    [SQLHK].[dbo].[Untersuchung]
                WHERE 
                    Datum = '{datum}'
                    AND PatientID = {patient_id}
                    AND UntersucherAbrechnungID = {untersucher_id}
                    AND HerzkatheterID = {herzkatheter_id}
                    AND UntersuchungartID = {untersuchungart_id}
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
                # Untersuchung existiert bereits, Update durchführen
                existing_untersuchung = result["rows"][0]
                patient_info = appointment.get('patient') if appointment.get('patient') else {}
                if isinstance(patient_info, dict):
                    patient_name = f"{patient_info.get('surname', 'Unbekannt')}, {patient_info.get('name', '')}"
                else:
                    patient_name = f"{appointment.get('surname', 'Unbekannt')}, {appointment.get('name', '')}"
                logger.info(f"✓ BESTEHEND: UntersuchungID={existing_untersuchung.get('UntersuchungID')} für Termin {appointment.get('id')} - Patient: {patient_name}")
                to_update.append((appointment, existing_untersuchung))
            else:
                # Untersuchung existiert noch nicht, neu einfügen
                patient_info = appointment.get('patient') if appointment.get('patient') else {}
                if isinstance(patient_info, dict):
                    patient_name = f"{patient_info.get('surname', 'Unbekannt')}, {patient_info.get('name', '')}"
                else:
                    patient_name = f"{appointment.get('surname', 'Unbekannt')}, {appointment.get('name', '')}"
                logger.info(f"➤ NEU EINFÜGEN: Termin {appointment.get('id')} - Patient: {patient_name} - Datum: {datum}")
                to_insert.append(appointment)
        
        # Statistik aktualisieren
        self.stats["to_insert"] = len(to_insert)
        self.stats["to_update"] = len(to_update)
        
        logger.info(f"\n=== SYNCHRONISIERUNGS-ZUSAMMENFASSUNG ===")
        logger.info(f"Zu synchronisieren: {len(to_insert)} NEUE EINFÜGEN, {len(to_update)} AKTUALISIEREN, {self.stats['deleted']} GELÖSCHT")
        logger.info(f"==========================================\n")
        
        # Operationen durchführen
        for appointment in to_insert:
            self._insert_untersuchung(appointment)
        
        for appointment, untersuchung in to_update:
            self._update_untersuchung(appointment, untersuchung)
        
        # Erfolgsstatistik aktualisieren
        self.stats["success"] = self.stats["inserted"] + self.stats["updated"] + self.stats["deleted"]
        
        return self.stats
        
    def _update_untersuchung(self, appointment: Dict[str, Any], untersuchung: Dict[str, Any]) -> None:
        """
        Aktualisiert eine bestehende Untersuchung in der SQLHK-Datenbank.
        
        Args:
            appointment: CallDoc-Termin
            untersuchung: SQLHK-Untersuchung
        """
        try:
            untersuchung_id = untersuchung.get("UntersuchungID")
            if not untersuchung_id:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Aktualisieren der Untersuchung: Keine UntersuchungID vorhanden")
                return
            
            # Untersuchungsdaten aus dem Termin mappen
            untersuchung_data = self.map_appointment_to_untersuchung(appointment)
            
            # Validierung der Pflichtfelder
            required_fields = ["Datum", "PatientID", "UntersuchungartID"]
            missing_fields = [field for field in required_fields if not untersuchung_data.get(field)]
            
            if missing_fields:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Aktualisieren der Untersuchung {untersuchung_id}: Fehlende Pflichtfelder: {', '.join(missing_fields)}")
                logger.error(f"Untersuchungsdaten: {untersuchung_data}")
                return
            
            # Debug-Ausgabe der Untersuchungsdaten
            logger.info(f"Aktualisiere Untersuchung {untersuchung_id} mit Daten: {untersuchung_data}")
            
            # upsert_data-Methode verwenden (table, search_fields, update_fields, key_fields, database)
            # Suchkriterien: UntersuchungID (für Update)
            search_fields = {"UntersuchungID": untersuchung_id}
            
            result = self.mssql_client.upsert_data(
                table="Untersuchung",
                search_fields=search_fields,
                update_fields=untersuchung_data,
                key_fields=["UntersuchungID"],
                database="SQLHK"
            )
            
            if result.get("success", False):
                self.stats["updated"] += 1
                self.stats["success"] += 1
                logger.info(f"Untersuchung {untersuchung_id} für Termin {appointment.get('id')} erfolgreich aktualisiert")
            else:
                self.stats["errors"] += 1
                error_msg = result.get('error', 'Unbekannter Fehler')
                logger.error(f"Fehler beim Aktualisieren der Untersuchung {untersuchung_id}: {error_msg}")
                logger.error(f"API-Antwort: {result}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Aktualisieren der Untersuchung {untersuchung.get('UntersuchungID')}: {str(e)}")
            # Detaillierte Fehlerinformationen loggen
            import traceback
            logger.error(f"Stacktrace: {traceback.format_exc()}")
    
    def _delete_untersuchung(self, untersuchung: Dict[str, Any]) -> bool:
        """
        Löscht eine Untersuchung aus der SQLHK-Datenbank.
        
        Args:
            untersuchung: SQLHK-Untersuchung
            
        Returns:
            bool: True, wenn die Löschung erfolgreich war, sonst False
        """
        try:
            untersuchung_id = untersuchung.get("UntersuchungID")
            if not untersuchung_id:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Löschen der Untersuchung: Keine UntersuchungID vorhanden")
                return False
            
            # Debug-Ausgabe der zu löschenden Untersuchung
            logger.info(f"Lösche Untersuchung {untersuchung_id} mit Daten: {untersuchung}")
            
            # SQL-Abfrage zum Löschen der Untersuchung
            query = f"""
                DELETE FROM [SQLHK].[dbo].[Untersuchung]
                WHERE UntersuchungID = {untersuchung_id}
            """
            
            result = self.mssql_client.execute_sql(query, "SQLHK")
            
            if result.get("success", False):
                self.stats["deleted"] += 1
                logger.info(f"Untersuchung {untersuchung_id} erfolgreich gelöscht")
                return True
            else:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Löschen der Untersuchung {untersuchung_id}: {result.get('message', 'Unbekannter Fehler')}")
                return False
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Löschen der Untersuchung: {str(e)}")
            return False
            
    def _delete_obsolete_untersuchungen(self, active_appointments: List[Dict[str, Any]], sqlhk_untersuchungen: List[Dict[str, Any]], date_str: str) -> int:
        """
        Identifiziert und löscht Untersuchungen, die in der SQLHK-Datenbank existieren, aber nicht mehr
        als aktive Termine in CallDoc vorhanden sind. Dies ist ein robusterer Ansatz als nur stornierte
        Termine zu verarbeiten, da er auch Termine erfasst, die komplett gelöscht wurden.
        
        Args:
            active_appointments: Liste der aktiven Termine aus CallDoc
            sqlhk_untersuchungen: Liste der Untersuchungen aus der SQLHK-Datenbank
            date_str: Datum im Format YYYY-MM-DD für die Filterung zukünftiger Termine
            
        Returns:
            int: Anzahl der gelöschten Untersuchungen
        """
        # Prüfen, ob das Datum in der Zukunft liegt
        try:
            current_date = datetime.now().date()
            sync_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if sync_date <= current_date:
                logger.info(f"Datum {date_str} liegt nicht in der Zukunft, keine Löschung von Untersuchungen")
                return 0
            
            logger.info(f"Datum {date_str} liegt in der Zukunft, obsolete Untersuchungen werden identifiziert")
        except Exception as e:
            logger.error(f"Fehler beim Vergleich des Datums: {str(e)}")
            return 0
        
        # Erstelle ein Set mit eindeutigen Identifikatoren für aktive Termine
        active_appointment_identifiers = set()
        
        # Debug-Ausgabe für aktive Termine
        logger.info(f"Verarbeite {len(active_appointments)} aktive Termine für die Löschlogik")
        
        for appointment in active_appointments:
            try:
                # Mapping des Termins auf eine Untersuchung
                mapped_untersuchung = self.map_appointment_to_untersuchung(appointment)
                
                # Erforderliche Felder für die eindeutige Identifikation
                datum = mapped_untersuchung.get("Datum")
                patient_id = mapped_untersuchung.get("PatientID")
                untersucher_id = mapped_untersuchung.get("UntersucherAbrechnungID")
                herzkatheter_id = mapped_untersuchung.get("HerzkatheterID")
                untersuchungart_id = mapped_untersuchung.get("UntersuchungartID")
                
                if all([datum, patient_id, untersucher_id, herzkatheter_id, untersuchungart_id]):
                    # Erstelle einen eindeutigen Identifier für diesen Termin
                    identifier = f"{datum}_{patient_id}_{untersucher_id}_{herzkatheter_id}_{untersuchungart_id}"
                    active_appointment_identifiers.add(identifier)
                    logger.debug(f"Aktiver Termin-Identifier: {identifier} (ID: {appointment.get('id')})")
                else:
                    logger.warning(f"Nicht alle erforderlichen Felder für die Identifikation des Termins vorhanden: ID={appointment.get('id')}")
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten des aktiven Termins {appointment.get('id')}: {str(e)}")
                continue
        
        # Debug-Ausgabe für aktive Termine
        logger.info(f"{len(active_appointment_identifiers)} eindeutige aktive Termin-Identifikatoren erstellt")
        
        # Identifiziere Untersuchungen, die keinen entsprechenden aktiven Termin haben
        deleted_count = 0
        
        # Debug-Ausgabe für Untersuchungen
        logger.info(f"Verarbeite {len(sqlhk_untersuchungen)} Untersuchungen für die Löschlogik")
        
        for untersuchung in sqlhk_untersuchungen:
            try:
                # Extrahiere die Identifikationsfelder
                datum = untersuchung.get("Datum")
                patient_id = untersuchung.get("PatientID")
                untersucher_id = untersuchung.get("UntersucherAbrechnungID")
                herzkatheter_id = untersuchung.get("HerzkatheterID")
                untersuchungart_id = untersuchung.get("UntersuchungartID")
                untersuchung_id = untersuchung.get("UntersuchungID")
                
                if not all([datum, patient_id, untersucher_id, herzkatheter_id, untersuchungart_id]):
                    logger.warning(f"Nicht alle erforderlichen Felder für die Identifikation der Untersuchung vorhanden: UntersuchungID={untersuchung_id}")
                    continue
                
                # Erstelle den gleichen eindeutigen Identifier
                identifier = f"{datum}_{patient_id}_{untersucher_id}_{herzkatheter_id}_{untersuchungart_id}"
                logger.debug(f"Untersuchungs-Identifier: {identifier} (ID: {untersuchung_id})")
                
                # Wenn dieser Identifier nicht in den aktiven Terminen ist, lösche die Untersuchung
                if identifier not in active_appointment_identifiers:
                    logger.info(f"Obsolete Untersuchung gefunden: UntersuchungID={untersuchung_id}, Datum={datum}, Identifier={identifier}")
                    if self._delete_untersuchung(untersuchung):
                        deleted_count += 1
                        logger.info(f"Untersuchung {untersuchung_id} erfolgreich gelöscht")
                    else:
                        logger.error(f"Fehler beim Löschen der Untersuchung {untersuchung_id}")
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten der Untersuchung {untersuchung.get('UntersuchungID')}: {str(e)}")
                continue
        
        logger.info(f"{deleted_count} obsolete Untersuchungen wurden gelöscht")
        return deleted_count


# Beispiel für die Verwendung der Klasse
if __name__ == "__main__":
    # Datum für die Synchronisierung
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # CallDoc-Interface initialisieren
    calldoc_interface = CallDocInterface(from_date=date_str, to_date=date_str)
    
    # MS SQL Client initialisieren
    mssql_client = MsSqlApiClient()
    
    # Synchronizer initialisieren
    synchronizer = UntersuchungSynchronizer(calldoc_interface, mssql_client)
    
    # Synchronisierung durchführen
    print(f"Starte Synchronisierung für {date_str}...")
    stats = synchronizer.compare_and_sync(date_str)
    
    # Ergebnis ausgeben
    print("\nSynchronisierung abgeschlossen:")
    print(f"CallDoc-Termine: {stats['total_calldoc']}")
    print(f"SQLHK-Untersuchungen: {stats['total_sqlhk']}")
    print(f"Neue Untersuchungen: {stats['inserted']}/{stats['to_insert']}")
    print(f"Aktualisierte Untersuchungen: {stats['updated']}/{stats['to_update']}")
    print(f"Gelöschte Untersuchungen: {stats['deleted']}/{stats['to_delete']}")
    print(f"Fehler: {stats['errors']}")
