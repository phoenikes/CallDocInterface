#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug-Skript für die SQLHK-Untersuchungen
Analysiert die Struktur der Untersuchungsdaten und zeigt Probleme auf
"""

import sys
import json
import logging
from datetime import datetime
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"debug_untersuchungen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def debug_untersuchungen():
    """
    Debuggt die SQLHK-Untersuchungen und zeigt ihre Struktur an.
    """
    # Initialisiere den Synchronizer
    synchronizer = CallDocSQLHKSynchronizer()
    
    # Datum für den Test (heute)
    today = datetime.now().strftime("%Y-%m-%d")
    date_parts = today.split("-")
    date_str_de = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
    
    logger.info(f"Rufe SQLHK-Untersuchungen für Datum {date_str_de} ab...")
    
    # Rufe Untersuchungen ab
    untersuchungen = synchronizer.get_sqlhk_untersuchungen(date_str_de)
    
    logger.info(f"{len(untersuchungen)} SQLHK-Untersuchungen gefunden.")
    
    # Analysiere die Struktur der Untersuchungen
    logger.info("Analysiere die Struktur der Untersuchungen...")
    
    for i, untersuchung in enumerate(untersuchungen):
        logger.info(f"Untersuchung {i+1}:")
        logger.info(f"  Typ: {type(untersuchung)}")
        
        if isinstance(untersuchung, str):
            logger.info(f"  String-Inhalt: {untersuchung}")
            try:
                # Versuche, den String als JSON zu parsen
                parsed = json.loads(untersuchung)
                logger.info(f"  Als JSON geparst: {type(parsed)}")
                logger.info(f"  JSON-Schlüssel: {parsed.keys() if isinstance(parsed, dict) else 'Keine Schlüssel'}")
            except json.JSONDecodeError as e:
                logger.info(f"  Kein gültiges JSON: {str(e)}")
        elif isinstance(untersuchung, dict):
            logger.info(f"  Dictionary-Schlüssel: {untersuchung.keys()}")
        else:
            logger.info(f"  Anderer Typ: {type(untersuchung)}")
    
    # Speichere die Untersuchungen zur weiteren Analyse
    with open(f"debug_untersuchungen_{today}.json", "w", encoding="utf-8") as f:
        try:
            json.dump(untersuchungen, f, indent=2, ensure_ascii=False)
            logger.info(f"Untersuchungen in debug_untersuchungen_{today}.json gespeichert.")
        except TypeError as e:
            logger.error(f"Fehler beim Speichern der Untersuchungen: {str(e)}")
            # Versuche, die Untersuchungen als Strings zu speichern
            json.dump([str(u) for u in untersuchungen], f, indent=2, ensure_ascii=False)
            logger.info(f"Untersuchungen als Strings in debug_untersuchungen_{today}.json gespeichert.")

if __name__ == "__main__":
    logger.info("Starte Debug der SQLHK-Untersuchungen")
    debug_untersuchungen()
