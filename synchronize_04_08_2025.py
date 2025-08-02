#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Synchronisierungsskript für CallDoc-Termine und SQLHK-Untersuchungen für den 04.08.2025.

Dieses Skript führt folgende Schritte aus:
1. Abrufen der CallDoc-Termine für den 04.08.2025
2. Abrufen der SQLHK-Untersuchungen für den 04.08.2025
3. Synchronisieren der Patienten aus den CallDoc-Terminen
4. Synchronisieren der Untersuchungen (inkl. Löschen obsoleter Untersuchungen)
5. Speichern der Ergebnisse in einer JSON-Datei
"""

import json
import logging
from datetime import datetime

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer
from constants import APPOINTMENT_TYPES

# Konfiguriere das Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Datum für die Synchronisierung (04.08.2025)
date_str = "2025-08-04"
date_str_de = "04.08.2025"

def main():
    logger.info(f"Starte Synchronisierung für Datum: {date_str} ({date_str_de})")
    
    # Initialisiere die Clients
    calldoc_client = CallDocInterface(from_date=date_str, to_date=date_str)
    mssql_client = MsSqlApiClient()
    
    # Initialisiere die Synchronizer
    patient_sync = PatientSynchronizer()
    untersuchung_sync = UntersuchungSynchronizer(
        calldoc_interface=calldoc_client, 
        mssql_client=mssql_client
    )
    synchronizer = CallDocSQLHKSynchronizer()
    
    try:
        # 1. CallDoc-Termine abrufen
        logger.info("1. CallDoc-Termine abrufen")
        calldoc_appointments = synchronizer.get_calldoc_appointments(
            date_str=date_str,
            filter_by_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
            smart_status_filter=True
        )
        
        if not calldoc_appointments:
            logger.warning(f"Keine CallDoc-Termine für {date_str} gefunden.")
            return {"success": False, "error": "Keine Termine gefunden"}
        
        logger.info(f"{len(calldoc_appointments)} CallDoc-Termine gefunden.")
        
        # Termine als JSON speichern
        with open(f"calldoc_termine_{date_str}.json", "w", encoding="utf-8") as f:
            json.dump(calldoc_appointments, f, indent=2)
        
        # 2. SQLHK-Untersuchungen abrufen
        logger.info("2. SQLHK-Untersuchungen abrufen")
        sqlhk_untersuchungen = []
        
        # Versuche beide Datumsformate
        sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(date_str)
        if not sqlhk_untersuchungen:
            sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(date_str_de)
        
        logger.info(f"{len(sqlhk_untersuchungen)} SQLHK-Untersuchungen gefunden.")
        
        # Untersuchungen als JSON speichern
        with open(f"sqlhk_untersuchungen_{date_str}.json", "w", encoding="utf-8") as f:
            json.dump(sqlhk_untersuchungen, f, indent=2)
        
        # 3. Patienten synchronisieren
        logger.info("3. Patienten synchronisieren")
        patient_stats = patient_sync.synchronize_patients_from_appointments(calldoc_appointments)
        
        logger.info("Patienten-Synchronisierung abgeschlossen:")
        logger.info(f"  - Erfolgreiche Operationen: {patient_stats.get('success', 0)}")
        logger.info(f"  - Fehler: {patient_stats.get('errors', 0)}")
        logger.info(f"  - Eingefügt: {patient_stats.get('inserted', 0)}")
        logger.info(f"  - Aktualisiert: {patient_stats.get('updated', 0)}")
        
        # 4. Untersuchungen synchronisieren
        logger.info("4. Untersuchungen synchronisieren")
        
        # Zuerst das Mapping von Termintypen zu Untersuchungsarten laden
        untersuchung_sync.load_appointment_type_mapping()
        
        # Dann die Synchronisierung durchführen
        result = untersuchung_sync.synchronize_appointments(
            calldoc_appointments,
            sqlhk_untersuchungen
        )
        
        # Ausgabe der Ergebnisse
        logger.info("Untersuchungs-Synchronisierung abgeschlossen:")
        logger.info(f"  - Erfolgreiche Operationen: {result.get('success', 0)}")
        logger.info(f"  - Fehler: {result.get('errors', 0)}")
        logger.info(f"  - Eingefügt: {result.get('inserted', 0)}")
        logger.info(f"  - Aktualisiert: {result.get('updated', 0)}")
        logger.info(f"  - Gelöscht: {result.get('deleted', 0)}")
        
        # Speichere die Ergebnisse in einer JSON-Datei
        with open(f"sync_result_{date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Synchronisierung für {date_str} ({date_str_de}) abgeschlossen")
        return result
    except Exception as e:
        logger.error(f"Fehler bei der Synchronisierung: {str(e)}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    main()
