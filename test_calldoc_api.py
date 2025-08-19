#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Skript für die CallDoc-API
Prüft die Verbindung und ruft Termine ohne Filter ab
"""

import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from constants import API_BASE_URL, APPOINTMENT_SEARCH_URL, APPOINTMENT_TYPES

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_calldoc_api():
    """Testet die CallDoc-API und gibt alle verfügbaren Termine zurück."""
    
    # Heutiges Datum und Datum in einer Woche
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    logger.info(f"Teste CallDoc-API für Zeitraum {today} bis {next_week}")
    
    # API-Anfrage ohne Termintyp-Filter
    params = {
        "from_date": today,
        "to_date": next_week
    }
    
    try:
        logger.info(f"Sende Anfrage an {APPOINTMENT_SEARCH_URL}")
        response = requests.get(APPOINTMENT_SEARCH_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"API-Antwort erhalten: {type(data)}")
        
        if "data" in data:
            appointments = data["data"]
            logger.info(f"Anzahl gefundener Termine: {len(appointments)}")
            
            # Analysiere die Struktur eines Beispieltermins
            if appointments:
                sample = appointments[0]
                logger.info("Struktur eines Beispieltermins:")
                logger.info(f"Verfügbare Felder: {', '.join(sample.keys())}")
                
                # Prüfe, ob appointment_type_id vorhanden ist
                if "appointment_type_id" in sample:
                    logger.info(f"appointment_type_id ist vorhanden: {sample['appointment_type_id']}")
                else:
                    logger.info("ACHTUNG: appointment_type_id ist NICHT vorhanden!")
                    
                    # Prüfe, ob es ein alternatives Feld für den Termintyp gibt
                    for key in sample.keys():
                        if "type" in key.lower():
                            logger.info(f"Mögliches alternatives Feld für Termintyp gefunden: {key} = {sample[key]}")
                
                # Zähle Termine nach Typ (falls vorhanden)
                type_counts = {}
                type_field = "appointment_type_id"
                
                # Wenn appointment_type_id nicht vorhanden ist, versuche ein alternatives Feld zu finden
                if "appointment_type_id" not in sample and any("type" in key.lower() for key in sample.keys()):
                    for key in sample.keys():
                        if "type" in key.lower():
                            type_field = key
                            break
                    logger.info(f"Verwende alternatives Feld für Termintyp: {type_field}")
                
                # Zähle Termine nach dem identifizierten Typ-Feld
                for appointment in appointments:
                    type_id = appointment.get(type_field)
                    if type_id is not None:
                        if type_id not in type_counts:
                            type_counts[type_id] = 0
                        type_counts[type_id] += 1
                
                logger.info("Verteilung der Termintypen:")
                for type_id, count in type_counts.items():
                    # Finde den Namen des Termintyps (falls es sich um appointment_type_id handelt)
                    type_name = "Unbekannt"
                    if type_field == "appointment_type_id":
                        for name, id_value in APPOINTMENT_TYPES.items():
                            if id_value == type_id:
                                type_name = name
                                break
                    logger.info(f"  - {type_field}={type_id} ({type_name}): {count} Termine")
            
            # Speichere einen Beispieltermin für jeden Typ
            logger.info("Speichere Beispieltermine in calldoc_termine_beispiele.json")
            examples = {}
            for type_id in type_counts.keys():
                for appointment in appointments:
                    if appointment.get("appointment_type_id") == type_id:
                        examples[str(type_id)] = appointment
                        break
            
            with open("calldoc_termine_beispiele.json", "w", encoding="utf-8") as f:
                json.dump(examples, f, indent=2, ensure_ascii=False)
            
            return True
            
        else:
            logger.error("Keine Daten in der API-Antwort gefunden")
            return False
            
    except Exception as e:
        logger.error(f"Fehler bei der API-Anfrage: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_calldoc_api()
    if success:
        logger.info("Test erfolgreich abgeschlossen")
    else:
        logger.error("Test fehlgeschlagen")
        sys.exit(1)
