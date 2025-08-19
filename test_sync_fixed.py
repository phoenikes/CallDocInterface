#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Skript für die korrigierte CallDoc-SQLHK Synchronisierung
Testet die Synchronisierung mit dem korrigierten API-Parameter
"""

import sys
import logging
import json
from datetime import datetime, timedelta
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer
from constants import APPOINTMENT_TYPES

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"test_sync_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def test_sync():
    """
    Testet die Synchronisierung mit verschiedenen Parametern.
    """
    # Initialisiere den Synchronizer
    synchronizer = CallDocSQLHKSynchronizer()
    
    # Datum für den Test (heute)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Test 1: Ohne Termintyp-Filter
    logger.info("=== Test 1: Ohne Termintyp-Filter ===")
    logger.info(f"Datum: {today}")
    
    results = synchronizer.run_comparison(
        date_str=today,
        appointment_type_id=None,  # Kein Filter
        smart_status_filter=True,
        save_results=True
    )
    
    if results:
        logger.info(f"Ergebnis ohne Filter: {len(results.get('calldoc_appointments', []))} Termine gefunden")
        
        # Speichere die Ergebnisse
        with open(f"test_ohne_filter_{today}.json", "w", encoding="utf-8") as f:
            json.dump(results.get('calldoc_appointments', []), f, indent=2, ensure_ascii=False)
    else:
        logger.error("Keine Ergebnisse für Test ohne Filter")
    
    # Test 2: Mit Herzkatheteruntersuchung-Filter
    logger.info("\n=== Test 2: Mit Herzkatheteruntersuchung-Filter ===")
    logger.info(f"Datum: {today}")
    
    results = synchronizer.run_comparison(
        date_str=today,
        appointment_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
        smart_status_filter=True,
        save_results=True
    )
    
    if results:
        logger.info(f"Ergebnis mit HKU-Filter: {len(results.get('calldoc_appointments', []))} Termine gefunden")
        
        # Speichere die Ergebnisse
        with open(f"test_mit_hku_filter_{today}.json", "w", encoding="utf-8") as f:
            json.dump(results.get('calldoc_appointments', []), f, indent=2, ensure_ascii=False)
    else:
        logger.error("Keine Ergebnisse für Test mit HKU-Filter")
    
    # Test 3: Mit Herzultraschall-Filter
    logger.info("\n=== Test 3: Mit Herzultraschall-Filter ===")
    logger.info(f"Datum: {today}")
    
    results = synchronizer.run_comparison(
        date_str=today,
        appointment_type_id=APPOINTMENT_TYPES["HERZULTRASCHALL"],
        smart_status_filter=True,
        save_results=True
    )
    
    if results:
        logger.info(f"Ergebnis mit HUS-Filter: {len(results.get('calldoc_appointments', []))} Termine gefunden")
        
        # Speichere die Ergebnisse
        with open(f"test_mit_hus_filter_{today}.json", "w", encoding="utf-8") as f:
            json.dump(results.get('calldoc_appointments', []), f, indent=2, ensure_ascii=False)
    else:
        logger.error("Keine Ergebnisse für Test mit HUS-Filter")
    
    logger.info("\nTests abgeschlossen.")

if __name__ == "__main__":
    logger.info("Starte Test der korrigierten CallDoc-SQLHK Synchronisierung")
    test_sync()
