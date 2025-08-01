"""
Vergleicht CallDoc-Termine mit SQLHK-Untersuchungen für ein bestimmtes Datum.
Nutzt die M1Ziffer aus der Patient-Tabelle als Zuordnungskriterium zwischen den Systemen.
"""

import requests
import json
import logging
import sys
import os
from datetime import datetime
from prettytable import PrettyTable
import csv

# Patientenabfrage-Funktionen importieren
from patient_abfrage import get_patient_by_id

# Eigene Module importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from constants import APPOINTMENT_TYPES, API_BASE_URL, APPOINTMENT_SEARCH_URL

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_calldoc_appointments(date_str, filter_by_type_id=None, smart_status_filter=True):
    """
    Ruft Termine aus der CallDoc-API ab und filtert sie nach Typ und Status.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        filter_by_type_id: Optional, ID des Termintyps zum Filtern (default: HERZKATHETERUNTERSUCHUNG)
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
        
        # Termintyp-Filter setzen (Standard: Herzkatheteruntersuchung)
        if filter_by_type_id is None:
            params["appointment_type_id"] = APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"]
        else:
            params["appointment_type_id"] = filter_by_type_id
            
        # Intelligente Statusfilterung basierend auf dem Datum
        if smart_status_filter:
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            search_date = datetime.strptime(date_str, "%Y-%m-%d")
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            
            # Wenn das Suchdatum in der Zukunft liegt, nur nach "created" Terminen filtern
            if search_date > current_date_obj:
                logger.info(f"Intelligente Statusfilterung: Datum {date_str} liegt in der Zukunft, filtere nach 'created' Status")
                params["status"] = "created"
            else:
                logger.info(f"Intelligente Statusfilterung: Datum {date_str} ist heute oder in der Vergangenheit, keine Statusfilterung")
        else:
            # Wenn keine intelligente Filterung gewünscht ist, Standard-Status verwenden
            params["status"] = "created"
        
        logger.info(f"Sende Anfrage an {url} mit Parametern {params}")
        
        # API-Aufruf durchführen
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Ergebnis verarbeiten
        result = response.json()
        appointments = result.get("data", [])
        
        logger.info(f"{len(appointments)} CallDoc-Termine gefunden")
        return appointments
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der CallDoc-Termine: {str(e)}")
        return []

def get_sqlhk_untersuchungen(date_str, server_url="http://localhost:7007"):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        date_str: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {"datum": date_str}
        
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            logger.info(f"{len(result.get('data', []))} SQLHK-Untersuchungen gefunden")
            return result.get("data", [])
        else:
            logger.error(f"API-Fehler: {result.get('error', 'Unbekannter Fehler')}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return []

def get_patient_m1ziffer(patient_id, server_url="http://localhost:7007"):
    """
    Ruft die M1Ziffer eines Patienten aus der SQLHK-Datenbank ab.
    Nutzt die verbesserte get_patient_by_id-Funktion aus patient_abfrage.py.
    
    Args:
        patient_id: ID des Patienten
        server_url: URL des API-Servers
        
    Returns:
        Dictionary mit Patientendaten inklusive M1Ziffer
    """
    try:
        # Verbesserte Patientenabfrage-Funktion verwenden
        patient_data = get_patient_by_id(patient_id, server_url)
        
        if patient_data:
            return patient_data
        else:
            logger.warning(f"Patient mit ID {patient_id} nicht gefunden")
            return {"PatientID": patient_id, "M1Ziffer": "", "Nachname": "Unbekannt", "Vorname": "Unbekannt"}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der M1Ziffer: {str(e)}")
        return {"PatientID": patient_id, "M1Ziffer": "", "Nachname": "Unbekannt", "Vorname": "Unbekannt"}

def enrich_untersuchungen_with_m1ziffer(untersuchungen, server_url="http://localhost:7007"):
    """
    Ergänzt die Untersuchungen um die M1Ziffer aus der Patient-Tabelle.
    Verwendet die verbesserte Patientenabfrage-Funktion.
    
    Args:
        untersuchungen: Liste der Untersuchungen
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen mit M1Ziffer
    """
    enriched_untersuchungen = []
    logger.info(f"Ergänze {len(untersuchungen)} Untersuchungen mit Patientendaten...")
    
    for i, untersuchung in enumerate(untersuchungen):
        patient_id = untersuchung.get("PatientID")
        logger.info(f"Verarbeite Untersuchung {i+1}/{len(untersuchungen)} - PatientID: {patient_id}")
        
        patient_data = get_patient_m1ziffer(patient_id, server_url)
        
        # Untersuchung um Patientendaten ergänzen
        untersuchung["M1Ziffer"] = patient_data.get("M1Ziffer", "")
        untersuchung["PatientNachname"] = patient_data.get("Nachname", "Unbekannt")
        untersuchung["PatientVorname"] = patient_data.get("Vorname", "Unbekannt")
        untersuchung["PatientGeburtsdatum"] = patient_data.get("Geburtsdatum", "")
        
        enriched_untersuchungen.append(untersuchung)
    
    logger.info(f"Patientendaten-Ergänzung abgeschlossen.")
    return enriched_untersuchungen

def create_comparison_table(calldoc_appointments, sqlhk_untersuchungen):
    """
    Erstellt eine Vergleichstabelle zwischen CallDoc-Terminen und SQLHK-Untersuchungen.
    Nutzt die M1Ziffer als Zuordnungskriterium.
    
    Args:
        calldoc_appointments: Liste der CallDoc-Termine
        sqlhk_untersuchungen: Liste der SQLHK-Untersuchungen mit M1Ziffer
        
    Returns:
        PrettyTable-Objekt mit dem Vergleich
    """
    # Tabelle erstellen
    table = PrettyTable()
    table.field_names = [
        "M1Ziffer",
        "Patient",
        "CallDoc ID",
        "CallDoc Status",
        "SQLHK UntersuchungID",
        "SQLHK UntersuchungartID",
        "Übereinstimmung"
    ]
    
    # Dictionary mit M1Ziffer als Schlüssel für SQLHK-Untersuchungen erstellen
    sqlhk_by_m1ziffer = {}
    for untersuchung in sqlhk_untersuchungen:
        m1ziffer = untersuchung.get("M1Ziffer", "")
        if m1ziffer:
            if m1ziffer not in sqlhk_by_m1ziffer:
                sqlhk_by_m1ziffer[m1ziffer] = []
            sqlhk_by_m1ziffer[m1ziffer].append(untersuchung)
    
    # CallDoc-Termine durchgehen und mit SQLHK-Untersuchungen vergleichen
    logger.info(f"Verarbeite {len(calldoc_appointments)} CallDoc-Termine...")
    
    for appointment in calldoc_appointments:
        # Robuste Prüfung der Appointment-Struktur
        if not appointment or not isinstance(appointment, dict):
            logger.warning(f"Ungültiges Appointment-Format: {appointment}")
            continue
            
        patient = appointment.get("patient")
        if not patient or not isinstance(patient, dict):
            logger.warning(f"Appointment ohne gültige Patientendaten: {appointment.get('id', 'Unbekannt')}")
            patient_id = ""
            patient_name = "Unbekannt"
            appointment_id = appointment.get("id", "")
            appointment_status = appointment.get("status", "")
        else:
            # Gültige Patientendaten vorhanden
            patient_id = patient.get("piz", "")  # PIZ entspricht der M1Ziffer
            patient_name = f"{patient.get('lastName', '')}, {patient.get('firstName', '')}"
            appointment_id = appointment.get("id", "")
            appointment_status = appointment.get("status", "")
            
        # Prüfen, ob es eine passende SQLHK-Untersuchung gibt
        matching_untersuchungen = sqlhk_by_m1ziffer.get(patient_id, [])
        
        if matching_untersuchungen:
            # Es gibt mindestens eine passende Untersuchung
            for untersuchung in matching_untersuchungen:
                table.add_row([
                    patient_id,
                    patient_name,
                    appointment_id,
                    appointment_status,
                    untersuchung.get("UntersuchungID", ""),
                    untersuchung.get("UntersuchungartID", ""),
                    "NEIN" if untersuchung.get("UntersuchungID", "") != appointment_id else "JA"
                ])
        else:
            # Keine passende Untersuchung gefunden
            table.add_row([
                patient_id,
                patient_name,
                appointment_id,
                appointment_status,
                "",
                "",
                "X"
            ])
    
    # SQLHK-Untersuchungen ohne passenden CallDoc-Termin hinzufügen
    for m1ziffer, untersuchungen in sqlhk_by_m1ziffer.items():
        # Prüfen, ob es einen passenden CallDoc-Termin gibt
        has_matching_appointment = False
        
        # Sicherere Prüfung der Appointments
        for appointment in calldoc_appointments:
            if not appointment or not isinstance(appointment, dict):
                continue
                
            patient = appointment.get("patient")
            if not patient or not isinstance(patient, dict):
                continue
                
            piz = patient.get("piz", "")
            if piz and piz == m1ziffer:
                has_matching_appointment = True
                break
        
        if not has_matching_appointment:
            for untersuchung in untersuchungen:
                patient_name = f"{untersuchung.get('PatientNachname', '')}, {untersuchung.get('PatientVorname', '')}"
                table.add_row([
                    m1ziffer,
                    patient_name,
                    "",
                    "",
                    untersuchung.get("UntersuchungID", ""),
                    untersuchung.get("UntersuchungartID", ""),
                    "X"
                ])
    
    return table

def save_table_to_csv(table, filename):
    """
    Speichert die Tabelle als CSV-Datei.
    
    Args:
        table: PrettyTable-Objekt
        filename: Name der CSV-Datei
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(table.field_names)
        for row in table._rows:
            writer.writerow(row)
    
    print(f"Tabelle wurde als {filename} gespeichert.")

def analyze_appointment_status(appointments):
    """
    Analysiert die Statusverteilung der Termine.
    
    Args:
        appointments: Liste der Termine
        
    Returns:
        Dictionary mit Statusverteilung
    """
    status_counts = {}
    patient_counts = {"mit_patient": 0, "ohne_patient": 0}
    
    for appointment in appointments:
        # Status zählen
        status = appointment.get("status", "unbekannt")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Prüfen, ob Patientendaten vorhanden sind
        has_patient = False
        patient_data = appointment.get("patient")
        
        if patient_data:
            # Fall 1: patient ist ein Objekt mit id-Attribut
            if isinstance(patient_data, dict) and patient_data.get("id"):
                has_patient = True
            # Fall 2: patient ist direkt eine ID (int oder string)
            elif isinstance(patient_data, (int, str)) and patient_data:
                has_patient = True
        
        if has_patient:
            patient_counts["mit_patient"] += 1
        else:
            patient_counts["ohne_patient"] += 1
    
    return {
        "status": status_counts,
        "patient": patient_counts,
        "gesamt": len(appointments)
    }

def main():
    """
    Hauptfunktion zum Vergleich von CallDoc-Terminen und SQLHK-Untersuchungen.
    """
    # Datum für den Vergleich aus Kommandozeilenargumenten oder Standardwert
    if len(sys.argv) > 1:
        sqlhk_date = sys.argv[1]
        # Konvertieren des deutschen Datums in ISO-Format für CallDoc
        day, month, year = sqlhk_date.split('.')
        calldoc_date = f"{year}-{month}-{day}"
    else:
        sqlhk_date = "31.07.2025"  # Standarddatum für SQLHK
        calldoc_date = "2025-07-31"  # Standarddatum für CallDoc
    
    print(f"Vergleiche CallDoc-Termine mit SQLHK-Untersuchungen für {sqlhk_date}...")
    
    # CallDoc-Termine abrufen mit intelligenter Statusfilterung
    logger.info(f"Rufe CallDoc-Termine für {calldoc_date} mit intelligenter Statusfilterung ab...")
    appointments = get_calldoc_appointments(
        calldoc_date,
        filter_by_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
        smart_status_filter=True
    )
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    # Untersuchungen um M1Ziffer ergänzen
    enriched_untersuchungen = enrich_untersuchungen_with_m1ziffer(untersuchungen)
    
    # Vergleichstabelle erstellen
    table = create_comparison_table(appointments, enriched_untersuchungen)
    
    # Tabelle anzeigen
    print("\nVergleichstabelle:")
    print(table)
    
    # Statistiken berechnen
    match_count = sum(1 for row in table._rows if row[6] == "JA")
    mismatch_count = sum(1 for row in table._rows if row[6] == "X")
    
    print("\nStatistiken:")
    print(f"- Übereinstimmungen: {match_count}")
    print(f"- Unterschiede: {mismatch_count}")
    
    # Statusanalyse der CallDoc-Termine durchführen
    status_analyse = analyze_appointment_status(appointments)
    
    print("\nCallDoc-Terminanalyse:")
    print(f"- Gesamtanzahl Termine: {status_analyse['gesamt']}")
    print("- Statusverteilung:")
    for status, count in status_analyse['status'].items():
        print(f"  * {status}: {count}")
    print("- Patientendaten:")
    print(f"  * Mit Patientendaten: {status_analyse['patient']['mit_patient']}")
    print(f"  * Ohne Patientendaten: {status_analyse['patient']['ohne_patient']}")
    
    # Tabelle als CSV speichern
    csv_filename = f"vergleich_calldoc_sqlhk_{sqlhk_date.replace('.', '_')}.csv"
    save_table_to_csv(table, csv_filename)
    
    # Rohdaten als JSON speichern
    calldoc_json_file = f"calldoc_termine_{calldoc_date}.json"
    with open(calldoc_json_file, 'w', encoding='utf-8') as f:
        json.dump(appointments, f, indent=2, ensure_ascii=False)
    
    sqlhk_json_file = f"sqlhk_untersuchungen_mit_m1ziffer_{sqlhk_date.replace('.', '_')}.json"
    with open(sqlhk_json_file, "w", encoding="utf-8") as f:
        json.dump(enriched_untersuchungen, f, indent=2, ensure_ascii=False)
    
    print("\nRohdaten wurden in JSON-Dateien gespeichert:")
    print(f"- CallDoc-Termine: {calldoc_json_file}")
    print(f"- SQLHK-Untersuchungen: {sqlhk_json_file}")

if __name__ == "__main__":
    main()
