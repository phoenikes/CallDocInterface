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
            "errors": 0
        }
    
    def load_appointment_type_mapping(self) -> None:
        """
        Lädt das Mapping von CallDoc-Termintypen zu Untersuchungsarten aus der Datenbank.
        """
        query = """
            SELECT 
                UntersuchungartID, 
                UntersuchungartName, 
                ExterneID
            FROM 
                Untersuchungart
            WHERE 
                ExterneID IS NOT NULL
        """
        
        result = self.mssql_client.execute_sql(query)
        
        if result.get("success", False) and "results" in result:
            for row in result["results"]:
                externe_id = row.get("ExterneID")
                if externe_id:
                    try:
                        externe_id = int(externe_id)
                        self.appointment_type_mapping[externe_id] = row.get("UntersuchungartID")
                    except (ValueError, TypeError):
                        logger.warning(f"Ungültige ExterneID: {externe_id}")
        
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
        
        if result.get("success", False) and "results" in result:
            untersuchungen = result["results"]
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
        # Grundlegende Felder mappen
        untersuchung = {
            "Datum": appointment.get("date"),
            "Zeit": appointment.get("time"),
            "Bemerkung": appointment.get("notes") or "",
            "ExterneID": str(appointment.get("appointment_id")),
            "Status": self._map_status(appointment.get("status"))
        }
        
        # Termintyp zu UntersuchungartID mappen
        appointment_type_id = appointment.get("appointment_type_id")
        if appointment_type_id in self.appointment_type_mapping:
            untersuchung["UntersuchungartID"] = self.appointment_type_mapping[appointment_type_id]
        else:
            logger.warning(f"Kein Mapping für Termintyp {appointment_type_id} gefunden")
        
        # Patient mappen (PIZ zu PatientID)
        piz = appointment.get("piz")
        if piz:
            patient_id = self._get_patient_id_by_piz(piz)
            if patient_id:
                untersuchung["PatientID"] = patient_id
            else:
                logger.warning(f"Kein Patient mit PIZ {piz} gefunden")
        
        return untersuchung
    
    def _get_patient_id_by_piz(self, piz: str) -> Optional[int]:
        """
        Ermittelt die PatientID anhand der PIZ.
        
        Args:
            piz: Patienten-Identifikationsnummer
            
        Returns:
            PatientID oder None, wenn nicht gefunden
        """
        if piz in self.patient_cache:
            return self.patient_cache[piz]
        
        patient = self.mssql_client.get_patient_by_piz(piz)
        
        if patient:
            patient_id = patient.get("PatientID")
            self.patient_cache[piz] = patient_id
            return patient_id
        
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
        
        # Indizes erstellen für schnellen Zugriff
        calldoc_index = {str(app.get("appointment_id")): app for app in calldoc_appointments}
        sqlhk_index = {}
        for u in sqlhk_untersuchungen:
            externe_id = u.get("ExterneID")
            if externe_id:
                sqlhk_index[externe_id] = u
        
        # Identifizieren der Operationen
        to_insert = []
        to_update = []
        to_delete = []
        
        # 1. Neue und zu aktualisierende Untersuchungen identifizieren
        for app_id, appointment in calldoc_index.items():
            if app_id not in sqlhk_index:
                # Neuer Termin
                to_insert.append(appointment)
            else:
                # Existierender Termin - prüfen, ob Update notwendig
                sqlhk_untersuchung = sqlhk_index[app_id]
                if self._needs_update(appointment, sqlhk_untersuchung):
                    to_update.append((appointment, sqlhk_untersuchung))
        
        # 2. Zu löschende Untersuchungen identifizieren
        for externe_id, untersuchung in sqlhk_index.items():
            if externe_id not in calldoc_index:
                to_delete.append(untersuchung)
        
        # Statistik aktualisieren
        self.stats["to_insert"] = len(to_insert)
        self.stats["to_update"] = len(to_update)
        self.stats["to_delete"] = len(to_delete)
        
        logger.info(f"Zu synchronisieren: {len(to_insert)} neue, {len(to_update)} zu aktualisieren, {len(to_delete)} zu löschen")
        
        # Operationen durchführen
        for appointment in to_insert:
            self._insert_untersuchung(appointment)
        
        for appointment, untersuchung in to_update:
            self._update_untersuchung(appointment, untersuchung)
        
        for untersuchung in to_delete:
            self._delete_untersuchung(untersuchung)
        
        return self.stats
    
    def _needs_update(self, appointment: Dict[str, Any], untersuchung: Dict[str, Any]) -> bool:
        """
        Prüft, ob eine Untersuchung aktualisiert werden muss.
        
        Args:
            appointment: CallDoc-Termin
            untersuchung: SQLHK-Untersuchung
            
        Returns:
            True, wenn Update notwendig, sonst False
        """
        # Hier müsste eine detaillierte Vergleichslogik implementiert werden
        # Für den Moment prüfen wir nur einige grundlegende Felder
        
        # Zeit vergleichen
        if appointment.get("time") != untersuchung.get("Zeit"):
            return True
        
        # Status vergleichen
        calldoc_status = self._map_status(appointment.get("status"))
        if calldoc_status != untersuchung.get("Status"):
            return True
        
        # Bemerkung vergleichen
        if appointment.get("notes") != untersuchung.get("Bemerkung"):
            return True
        
        return False
    
    def _insert_untersuchung(self, appointment: Dict[str, Any]) -> None:
        """
        Fügt eine neue Untersuchung in die SQLHK-Datenbank ein.
        
        Args:
            appointment: CallDoc-Termin
        """
        try:
            untersuchung_data = self.map_appointment_to_untersuchung(appointment)
            result = self.mssql_client.insert_untersuchung(untersuchung_data)
            
            if result.get("success", False):
                self.stats["inserted"] += 1
                logger.info(f"Untersuchung für Termin {appointment.get('appointment_id')} eingefügt")
            else:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Einfügen der Untersuchung für Termin {appointment.get('appointment_id')}: {result.get('error', 'Unbekannter Fehler')}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Einfügen der Untersuchung für Termin {appointment.get('appointment_id')}: {str(e)}")
    
    def _update_untersuchung(self, appointment: Dict[str, Any], untersuchung: Dict[str, Any]) -> None:
        """
        Aktualisiert eine bestehende Untersuchung in der SQLHK-Datenbank.
        
        Args:
            appointment: CallDoc-Termin
            untersuchung: SQLHK-Untersuchung
        """
        try:
            untersuchung_id = untersuchung.get("UntersuchungID")
            untersuchung_data = self.map_appointment_to_untersuchung(appointment)
            result = self.mssql_client.update_untersuchung(untersuchung_id, untersuchung_data)
            
            if result.get("success", False):
                self.stats["updated"] += 1
                logger.info(f"Untersuchung {untersuchung_id} für Termin {appointment.get('appointment_id')} aktualisiert")
            else:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Aktualisieren der Untersuchung {untersuchung_id}: {result.get('error', 'Unbekannter Fehler')}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Aktualisieren der Untersuchung {untersuchung.get('UntersuchungID')}: {str(e)}")
    
    def _delete_untersuchung(self, untersuchung: Dict[str, Any]) -> None:
        """
        Löscht eine Untersuchung aus der SQLHK-Datenbank.
        
        Args:
            untersuchung: SQLHK-Untersuchung
        """
        try:
            untersuchung_id = untersuchung.get("UntersuchungID")
            result = self.mssql_client.delete_untersuchung(untersuchung_id)
            
            if result.get("success", False):
                self.stats["deleted"] += 1
                logger.info(f"Untersuchung {untersuchung_id} gelöscht")
            else:
                self.stats["errors"] += 1
                logger.error(f"Fehler beim Löschen der Untersuchung {untersuchung_id}: {result.get('error', 'Unbekannter Fehler')}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Löschen der Untersuchung {untersuchung.get('UntersuchungID')}: {str(e)}")


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
