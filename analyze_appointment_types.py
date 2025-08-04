#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dieses Skript ruft alle Termine der nächsten zwei Wochen von CallDoc ab
und erstellt eine Übersicht über die verschiedenen Terminarten mit ihren IDs.
"""

import json
import logging
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd

from calldoc_interface import CallDocInterface

# Konfiguriere das Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Berechne Datum für heute und in zwei Wochen
    today = datetime.now().strftime("%Y-%m-%d")
    two_weeks_later = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    logger.info(f"Rufe Termine von {today} bis {two_weeks_later} ab")
    
    # Initialisiere den CallDoc-Client
    calldoc_client = CallDocInterface(from_date=today, to_date=two_weeks_later)
    
    try:
        # Alle Termine abrufen (ohne Filterung nach Typ)
        response = calldoc_client.appointment_search()
        
        # Logge die API-Antwort für Debugging
        logger.info(f"API-Antwort: {type(response)}")
        if isinstance(response, dict):
            logger.info(f"API-Antwort Schlüssel: {response.keys()}")
        
        # Speichere die vollständige Antwort für die Analyse
        with open(f"calldoc_api_response_{today}.json", "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)
        
        # Extrahiere die Termine aus der API-Antwort
        appointments = response.get("data", []) if isinstance(response, dict) else []
        
        if not appointments:
            logger.warning("Keine Termine gefunden.")
            return
            
        logger.info(f"{len(appointments)} Termine gefunden.")
        
        # Logge ein Beispiel für einen Termin
        if appointments:
            logger.info(f"Beispiel für einen Termin: {json.dumps(appointments[0], indent=2, ensure_ascii=False)[:500]}...")
            logger.info(f"Felder im ersten Termin: {appointments[0].keys()}")
        
        # Speichere alle Termine als JSON für spätere Analyse
        with open(f"calldoc_alle_termine_{today}_bis_{two_weeks_later}.json", "w", encoding="utf-8") as f:
            json.dump(appointments, f, indent=2)
        
        # Extrahiere Termintypen und zähle sie
        appointment_types = {}
        type_counts = Counter()
        
        for appointment in appointments:
            type_id = appointment.get("appointment_type_id")
            type_name = appointment.get("friendly_name")
            
            if type_id and type_name:
                appointment_types[type_id] = type_name
                type_counts[type_id] += 1
        
        # Erstelle eine sortierte Liste der Termintypen mit Anzahl
        sorted_types = []
        for type_id, count in type_counts.most_common():
            type_name = appointment_types[type_id]
            sorted_types.append({
                "ID": type_id,
                "Name": type_name,
                "Anzahl": count
            })
        
        # Erstelle einen DataFrame für eine schöne Ausgabe
        df = pd.DataFrame(sorted_types)
        
        # Speichere die Ergebnisse als CSV
        csv_filename = f"termintypen_analyse_{today}.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8")
        
        # Speichere die Ergebnisse auch als JSON
        with open(f"termintypen_analyse_{today}.json", "w", encoding="utf-8") as f:
            json.dump(sorted_types, f, indent=2, ensure_ascii=False)
        
        # Gib die Ergebnisse in der Konsole aus
        logger.info("\nÜbersicht der Termintypen:")
        logger.info(f"{'ID':<5} {'Anzahl':<10} {'Name'}")
        logger.info("-" * 50)
        
        for item in sorted_types:
            logger.info(f"{item['ID']:<5} {item['Anzahl']:<10} {item['Name']}")
        
        logger.info(f"\nErgebnisse wurden in {csv_filename} gespeichert.")
        
        # Erstelle ein Mapping für constants.py
        constants_mapping = "# Konstanten für die Appointment-Typen mit lesbaren Namen\n"
        constants_mapping += "APPOINTMENT_TYPES = {\n"
        
        for item in sorted_types:
            # Erstelle einen Python-konformen Schlüsselnamen
            key_name = item['Name'].upper().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
            constants_mapping += f"    \"{key_name}\": {item['ID']},\n"
        
        constants_mapping += "}\n"
        
        # Speichere das Mapping in einer separaten Datei
        with open("appointment_types_mapping.py", "w", encoding="utf-8") as f:
            f.write(constants_mapping)
        
        logger.info("Ein aktualisiertes Mapping für constants.py wurde in appointment_types_mapping.py gespeichert.")
        
        return sorted_types
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Termine: {str(e)}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    main()
