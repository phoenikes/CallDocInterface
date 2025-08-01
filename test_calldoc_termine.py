"""
Testet die Funktion zum Abrufen von CallDoc-Terminen für ein bestimmtes Datum.
"""

import json
import logging
import requests
from datetime import datetime
from constants import APPOINTMENT_SEARCH_URL, APPOINTMENT_TYPES

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_calldoc_appointments(date_str, filter_by_type_id=None, filter_by_status=None, smart_status_filter=True):
    """
    Ruft Termine aus der CallDoc-API ab und filtert sie nach Typ und Status.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        filter_by_type_id: Optional, ID des Termintyps zum Filtern
        filter_by_status: Optional, Status zum Filtern
        smart_status_filter: Optional, wenn True, wird die Statusfilterung basierend auf dem Datum intelligent angepasst
        
    Returns:
        Liste der gefilterten Termine
    """
    try:
        # API-URL für Terminsuche
        url = APPOINTMENT_SEARCH_URL
        
        # Parameter für die Suche
        params = {
            "from_date": date_str,
            "to_date": date_str
        }
        
        # Optionale Filter hinzufügen
        if filter_by_type_id:
            params["appointment_type_id"] = filter_by_type_id
        
        # Intelligente Statusfilterung basierend auf dem Datum
        if smart_status_filter:
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            search_date = datetime.strptime(date_str, "%Y-%m-%d")
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            
            # Wenn das Suchdatum in der Zukunft liegt
            if search_date > current_date_obj and not filter_by_status:
                logger.info(f"Intelligente Statusfilterung: Datum {date_str} liegt in der Zukunft, filtere nach 'created' Status")
                params["status"] = "created"
            # Wenn explizit ein Status angegeben wurde, diesen verwenden
            elif filter_by_status:
                params["status"] = filter_by_status
        
        logger.info(f"Sende Anfrage an {url} mit Parametern {params}")
        
        # API-Aufruf durchführen
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Ergebnis verarbeiten
        result = response.json()
        appointments = result.get("data", [])
        
        logger.info(f"Insgesamt {len(appointments)} CallDoc-Termine gefunden")
        
        # Zählen, wie viele Termine Patientendaten haben
        with_patient_data = 0
        for appointment in appointments:
            if isinstance(appointment, dict) and appointment.get("patient") is not None:
                with_patient_data += 1
        
        logger.info(f"Davon {with_patient_data} Termine mit Patientendaten")
        
        return appointments
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der CallDoc-Termine: {str(e)}")
        return []

def main():
    """
    Hauptfunktion zum Testen der CallDoc-Terminabfrage.
    """
    # Datum für die Abfrage - aktuelles Datum und Zukunftsdatum testen
    current_date = "2025-07-31"  # Heute
    future_date = "2025-08-01"   # Morgen
    
    # Test 1: Aktuelles Datum (heute) - keine automatische Statusfilterung
    logger.info(f"\n=== Test 1: Aktuelles Datum {current_date} ===\n")
    logger.info(f"Rufe CallDoc-Termine für {current_date} ab...")
    logger.info("Filtere nach appointment_type_id=24 (Herzkatheteruntersuchung)...")
    
    # Abfrage für aktuelles Datum mit intelligenter Statusfilterung
    current_appointments = get_calldoc_appointments(
        current_date, 
        filter_by_type_id=24, 
        smart_status_filter=True
    )
    
    # Test 2: Zukünftiges Datum (morgen) - automatische Statusfilterung nach 'created'
    logger.info(f"\n=== Test 2: Zukünftiges Datum {future_date} ===\n")
    logger.info(f"Rufe CallDoc-Termine für {future_date} ab...")
    logger.info("Filtere nach appointment_type_id=24 (Herzkatheteruntersuchung)...")
    
    # Abfrage für zukünftiges Datum mit intelligenter Statusfilterung
    future_appointments = get_calldoc_appointments(
        future_date, 
        filter_by_type_id=24, 
        smart_status_filter=True
    )
    
    # Funktion zum Analysieren und Ausgeben der Termine
    def analyze_appointments(appointments, date_label):
        # Status-Werte zählen
        status_counts = {}
        for appointment in appointments:
            status = appointment.get("status")
            if status:
                status_counts[status] = status_counts.get(status, 0) + 1
        
        # Ergebnisse zusammenfassen
        logger.info(f"Insgesamt {len(appointments)} Herzkatheteruntersuchungs-Termine für {date_label} gefunden.")
        logger.info(f"Status-Verteilung für {date_label}:")
        for status, count in sorted(status_counts.items()):
            logger.info(f"  {status}: {count} Termine")
        
        # Zählen, wie viele Termine Patientendaten haben
        with_patient_data = sum(1 for app in appointments if app.get("patient") is not None)
        logger.info(f"Termine mit Patientendaten: {with_patient_data}")
        
        # Detaillierte Informationen zu allen Terminen ausgeben
        logger.info(f"\nDetails zu allen Terminen für {date_label}:")
        for i, appointment in enumerate(appointments):
            try:
                logger.info(f"Termin {i+1}:")
                
                # Patientendaten sicher abrufen
                patient = appointment.get("patient")
                if patient and isinstance(patient, dict):
                    logger.info(f"  Patient: {patient.get('firstName', '')} {patient.get('lastName', '')}")
                    logger.info(f"  PIZ: {patient.get('piz', 'Keine PIZ')}")
                else:
                    logger.info(f"  Patient: {appointment.get('name', '')} {appointment.get('surname', '')}")
                    logger.info(f"  PIZ: {appointment.get('piz', 'Keine PIZ')}")
                    
                # Termindaten sicher abrufen
                logger.info(f"  Termin-ID: {appointment.get('id', 'Keine ID')}")
                logger.info(f"  Status: {appointment.get('status', 'Kein Status')}")
                logger.info(f"  Terminzeit: {appointment.get('scheduled_for_datetime', 'Keine Zeit')}")
                logger.info(f"  Friendly Name: {appointment.get('friendly_name', 'Kein Name')}")
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von Termin {i+1}: {str(e)}")
                continue
        
        # Ergebnisse in JSON-Datei speichern
        date_str = date_label.split()[-1]  # Extrahiere das Datum aus dem Label
        with open(f"calldoc_termine_{date_str}_type24.json", "w", encoding="utf-8") as f:
            json.dump(appointments, f, indent=2, ensure_ascii=False)
    
    # Analysiere die Ergebnisse für beide Datumswerte
    analyze_appointments(current_appointments, f"Heute ({current_date})")
    analyze_appointments(future_appointments, f"Morgen ({future_date})")

if __name__ == "__main__":
    main()
