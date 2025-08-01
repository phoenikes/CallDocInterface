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

# Eigene Module importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from constants import APPOINTMENT_TYPES, API_BASE_URL, APPOINTMENT_SEARCH_URL

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_calldoc_appointments(date_str):
    """
    Ruft Termine aus der CallDoc-API ab.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD
        
    Returns:
        Liste der Termine
    """
    try:
        # API-URL für Terminsuche
        url = APPOINTMENT_SEARCH_URL
        
        # Parameter für die Suche
        params = {
            "from_date": date_str,
            "to_date": date_str,
            "appointment_type_id": APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
            "status": "created"
        }
        
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

def get_all_patients_with_m1ziffer(server_url="http://localhost:7007"):
    """
    Ruft alle Patienten mit M1Ziffer aus der SQLHK-Datenbank ab.
    
    Args:
        server_url: URL des API-Servers
        
    Returns:
        Dictionary mit PatientID als Schlüssel und Patientendaten als Wert
    """
    try:
        url = f"{server_url}/api/execute_sql"
        
        # Wechsel zur SQLHK-Datenbank und Abfrage aller Patienten
        query = """
        USE SQLHK;
        SELECT PatientID, Nachname, Vorname, Geburtsdatum, M1Ziffer, krankenkasse, versichertennr
        FROM Patient 
        WHERE M1Ziffer IS NOT NULL;
        USE SuPDatabase;
        """
        
        payload = {
            "query": query,
            "database": "SQLHK"
        }
        headers = {"Content-Type": "application/json"}
        
        logger.info("Rufe alle Patienten mit M1Ziffer ab...")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False) and result.get("results"):
            patients = {}
            for patient in result.get("results", []):
                patients[patient.get("PatientID")] = patient
            
            logger.info(f"{len(patients)} Patienten mit M1Ziffer gefunden")
            return patients
        else:
            logger.error("Keine Patienten gefunden")
            return {}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Patienten: {str(e)}")
        return {}

def enrich_untersuchungen_with_m1ziffer(untersuchungen, patients_dict):
    """
    Ergänzt die Untersuchungen um die M1Ziffer aus dem Patienten-Dictionary.
    
    Args:
        untersuchungen: Liste der Untersuchungen
        patients_dict: Dictionary mit PatientID als Schlüssel und Patientendaten als Wert
        
    Returns:
        Liste der Untersuchungen mit M1Ziffer
    """
    enriched_untersuchungen = []
    
    for untersuchung in untersuchungen:
        patient_id = untersuchung.get("PatientID")
        patient_data = patients_dict.get(patient_id, {})
        
        # Untersuchung um Patientendaten ergänzen
        untersuchung["M1Ziffer"] = patient_data.get("M1Ziffer", "")
        untersuchung["PatientNachname"] = patient_data.get("Nachname", "Unbekannt")
        untersuchung["PatientVorname"] = patient_data.get("Vorname", "Unbekannt")
        untersuchung["PatientGeburtsdatum"] = patient_data.get("Geburtsdatum", "")
        
        enriched_untersuchungen.append(untersuchung)
    
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
        "Uebereinstimmung"
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
    for appointment in calldoc_appointments:
        if isinstance(appointment, dict):
            patient = appointment.get("patient", {})
            if patient:
                patient_id = str(patient.get("piz", ""))  # PIZ entspricht der M1Ziffer
                patient_name = f"{patient.get('lastName', '')}, {patient.get('firstName', '')}"
                appointment_id = appointment.get("id", "")
                appointment_status = appointment.get("status", "")
            else:
                patient_id = ""
                patient_name = "Unbekannt"
                appointment_id = ""
                appointment_status = ""
            
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
                        "JA"
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
                    "NEIN"
                ])
    
    # SQLHK-Untersuchungen ohne passenden CallDoc-Termin hinzufügen
    for m1ziffer, untersuchungen in sqlhk_by_m1ziffer.items():
        # Prüfen, ob es einen passenden CallDoc-Termin gibt
        has_matching_appointment = any(
            str(appointment.get("patient", {}).get("piz", "")) == m1ziffer
            for appointment in calldoc_appointments if isinstance(appointment, dict)
        )
        
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
                    "NEIN"
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
    
    # CallDoc-Termine abrufen
    appointments = get_calldoc_appointments(calldoc_date)
    
    # SQLHK-Untersuchungen abrufen
    untersuchungen = get_sqlhk_untersuchungen(sqlhk_date)
    
    # Alle Patienten mit M1Ziffer abrufen
    patients_dict = get_all_patients_with_m1ziffer()
    
    # Untersuchungen um M1Ziffer ergänzen
    enriched_untersuchungen = enrich_untersuchungen_with_m1ziffer(untersuchungen, patients_dict)
    
    # Vergleichstabelle erstellen
    table = create_comparison_table(appointments, enriched_untersuchungen)
    
    # Tabelle anzeigen
    print("\nVergleichstabelle:")
    print(table)
    
    # Statistiken berechnen
    match_count = sum(1 for row in table._rows if row[6] == "JA")
    mismatch_count = sum(1 for row in table._rows if row[6] == "NEIN")
    
    print("\nStatistiken:")
    print(f"- Uebereinstimmungen: {match_count}")
    print(f"- Unterschiede: {mismatch_count}")
    
    # Tabelle als CSV speichern
    csv_filename = f"vergleich_calldoc_sqlhk_{sqlhk_date.replace('.', '_')}.csv"
    save_table_to_csv(table, csv_filename)
    
    # JSON-Dateien mit den Rohdaten speichern
    with open(f"calldoc_termine_{calldoc_date}.json", "w", encoding="utf-8") as f:
        json.dump(appointments, f, indent=2, ensure_ascii=False)
    
    with open(f"sqlhk_untersuchungen_mit_m1ziffer_{sqlhk_date.replace('.', '_')}.json", "w", encoding="utf-8") as f:
        json.dump(enriched_untersuchungen, f, indent=2, ensure_ascii=False)
    
    print(f"\nRohdaten wurden in JSON-Dateien gespeichert.")

if __name__ == "__main__":
    main()
