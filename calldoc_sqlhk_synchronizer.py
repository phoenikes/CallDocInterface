"""
CallDoc-SQLHK Synchronizer

Diese Klasse bietet Funktionen zum Vergleich und zur Synchronisierung von Terminen zwischen
dem CallDoc-System und der SQLHK-Datenbank.

Features:
- Intelligente Statusfilterung basierend auf dem Datum
- Flexible Filterung nach Termintyp, Arzt, Raum und Status
- Detaillierte Analyse der Terminverteilung
- Vergleich zwischen CallDoc-Terminen und SQLHK-Untersuchungen
- Export der Ergebnisse als JSON und CSV

Autor: Markus
"""

import json
import csv
import logging
import requests
from datetime import datetime
from prettytable import PrettyTable
from constants import (
    APPOINTMENT_SEARCH_URL,
    APPOINTMENT_TYPES,
    DOCTORS,
    ROOMS,
    SQLHK_API_BASE_URL
)
from patient_synchronizer import PatientSynchronizer

# Logger konfigurieren
logger = logging.getLogger(__name__)


class CallDocSQLHKSynchronizer:
    """
    Klasse zum Vergleich und zur Synchronisierung von Terminen zwischen CallDoc und SQLHK.
    """
    
    def __init__(self):
        """Initialisiert den Synchronizer."""
        self.calldoc_appointments = []
        self.sqlhk_untersuchungen = []
        self.enriched_untersuchungen = []
        self.comparison_table = None
        self.status_analysis = {}
        self.patient_synchronizer = PatientSynchronizer()
    
    def get_calldoc_appointments(self, date_str, filter_by_type_id=None, doctor_id=None, 
                                room_id=None, status=None, smart_status_filter=True):
        """
        Ruft Termine aus der CallDoc-API ab und filtert sie nach Typ, Arzt, Raum und Status.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
            filter_by_type_id: Optional, ID des Termintyps zum Filtern (default: HERZKATHETERUNTERSUCHUNG)
            doctor_id: Optional, ID des Arztes
            room_id: Optional, ID des Raums
            status: Optional, expliziter Status-Filter (überschreibt smart_status_filter)
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
            
            # Arzt-Filter setzen, falls angegeben
            if doctor_id:
                params["doctor_id"] = doctor_id
                
            # Raum-Filter setzen, falls angegeben
            if room_id:
                params["room_id"] = room_id
                
            # Status-Filter setzen
            if status:
                # Expliziter Status hat Vorrang
                params["status"] = status
            elif smart_status_filter:
                # Intelligente Statusfilterung basierend auf dem Datum
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
            self.calldoc_appointments = appointments
            return appointments
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der CallDoc-Termine: {str(e)}")
            return []
    
    def get_sqlhk_untersuchungen(self, date_str):
        """
        Ruft Untersuchungen aus der SQLHK-API ab.
        
        Args:
            date_str: Datum im Format DD.MM.YYYY
            
        Returns:
            Liste der Untersuchungen
        """
        try:
            # API-URL für Untersuchungssuche
            url = f"{SQLHK_API_BASE_URL}/untersuchung"
            
            # Parameter für die Suche
            params = {
                "datum": date_str
            }
            
            logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
            
            # API-Aufruf durchführen
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Ergebnis verarbeiten
            untersuchungen = response.json()
            
            logger.info(f"{len(untersuchungen)} SQLHK-Untersuchungen gefunden")
            self.sqlhk_untersuchungen = untersuchungen
            return untersuchungen
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der SQLHK-Untersuchungen: {str(e)}")
            return []
    
    def enrich_untersuchungen_with_m1ziffer(self, untersuchungen):
        """
        Ergänzt die Untersuchungen um die M1-Ziffer.
        
        Args:
            untersuchungen: Liste der Untersuchungen
            
        Returns:
            Liste der ergänzten Untersuchungen
        """
        try:
            logger.info(f"Ergänze {len(untersuchungen)} Untersuchungen mit Patientendaten...")
            
            enriched = []
            for untersuchung in untersuchungen:
                patient_id = untersuchung.get("PatientID")
                if patient_id:
                    try:
                        # API-URL für Patientensuche
                        url = f"{SQLHK_API_BASE_URL}/patient/{patient_id}"
                        
                        # API-Aufruf durchführen
                        response = requests.get(url)
                        response.raise_for_status()
                        
                        # Patientendaten verarbeiten
                        patient_data = response.json()
                        untersuchung["PatientVorname"] = patient_data.get("Vorname", "")
                        untersuchung["PatientNachname"] = patient_data.get("Nachname", "")
                        untersuchung["PatientGeburtsdatum"] = patient_data.get("Geburtsdatum", "")
                        untersuchung["M1Ziffer"] = patient_data.get("M1Ziffer", "")
                    except Exception as e:
                        logger.warning(f"Fehler beim Abrufen der Patientendaten für ID {patient_id}: {str(e)}")
                
                enriched.append(untersuchung)
            
            logger.info("Patientendaten-Ergänzung abgeschlossen.")
            self.enriched_untersuchungen = enriched
            return enriched
            
        except Exception as e:
            logger.error(f"Fehler beim Ergänzen der Untersuchungen: {str(e)}")
            return untersuchungen
    
    def analyze_appointment_status(self, appointments=None):
        """
        Analysiert die Statusverteilung der Termine.
        
        Args:
            appointments: Optional, Liste der Termine (falls None, werden die gespeicherten verwendet)
            
        Returns:
            Dictionary mit Statusverteilung
        """
        if appointments is None:
            appointments = self.calldoc_appointments
            
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
        
        analysis = {
            "status": status_counts,
            "patient": patient_counts,
            "gesamt": len(appointments)
        }
        
        self.status_analysis = analysis
        return analysis
    
    def create_comparison_table(self, appointments=None, untersuchungen=None):
        """
        Erstellt eine Vergleichstabelle zwischen CallDoc-Terminen und SQLHK-Untersuchungen.
        
        Args:
            appointments: Optional, Liste der CallDoc-Termine
            untersuchungen: Optional, Liste der SQLHK-Untersuchungen
            
        Returns:
            PrettyTable-Objekt mit der Vergleichstabelle
        """
        if appointments is None:
            appointments = self.calldoc_appointments
            
        if untersuchungen is None:
            untersuchungen = self.enriched_untersuchungen
            
        # Vergleichstabelle erstellen
        table = PrettyTable()
        table.field_names = [
            "M1Ziffer", "Patient", "CallDoc ID", "CallDoc Status",
            "SQLHK UntersuchungID", "SQLHK UntersuchungartID", "Übereinstimmung"
        ]
        
        # Mapping von PIZ zu Untersuchungen erstellen
        piz_to_untersuchung = {}
        for untersuchung in untersuchungen:
            piz = untersuchung.get("PatientID")
            if piz:
                if piz not in piz_to_untersuchung:
                    piz_to_untersuchung[piz] = []
                piz_to_untersuchung[piz].append(untersuchung)
        
        # CallDoc-Termine verarbeiten
        logger.info(f"Verarbeite {len(appointments)} CallDoc-Termine...")
        for appointment in appointments:
            patient_name = "Unbekannt"
            piz = None
            m1ziffer = ""
            
            # Patientendaten extrahieren
            patient_data = appointment.get("patient")
            if patient_data:
                if isinstance(patient_data, dict):
                    patient_id = patient_data.get("id")
                    if patient_id:
                        piz = patient_id
                        patient_name = f"{patient_data.get('surname', '')}, {patient_data.get('name', '')}"
                elif isinstance(patient_data, (int, str)):
                    piz = patient_data
            
            if not piz:
                logger.warning(f"Appointment ohne gültige Patientendaten: {appointment.get('id')}")
            
            # Prüfen, ob eine passende Untersuchung existiert
            matching_untersuchungen = piz_to_untersuchung.get(piz, []) if piz else []
            
            if matching_untersuchungen:
                # Für jede passende Untersuchung eine Zeile hinzufügen
                for untersuchung in matching_untersuchungen:
                    m1ziffer = untersuchung.get("M1Ziffer", "")
                    table.add_row([
                        m1ziffer,
                        patient_name,
                        appointment.get("id", ""),
                        appointment.get("status", ""),
                        untersuchung.get("UntersuchungID", ""),
                        untersuchung.get("UntersuchungartID", ""),
                        "JA"
                    ])
            else:
                # Keine passende Untersuchung gefunden
                table.add_row([
                    m1ziffer,
                    patient_name,
                    appointment.get("id", ""),
                    appointment.get("status", ""),
                    "",
                    "",
                    "X"
                ])
        
        # Untersuchungen ohne passenden Termin hinzufügen
        for untersuchung in untersuchungen:
            piz = untersuchung.get("PatientID")
            patient_name = f"{untersuchung.get('PatientNachname', '')}, {untersuchung.get('PatientVorname', '')}"
            m1ziffer = untersuchung.get("M1Ziffer", "")
            
            # Prüfen, ob ein passender Termin existiert
            matching_appointment = False
            for appointment in appointments:
                patient_data = appointment.get("patient")
                if patient_data:
                    if isinstance(patient_data, dict) and patient_data.get("id") == piz:
                        matching_appointment = True
                        break
                    elif patient_data == piz:
                        matching_appointment = True
                        break
            
            if not matching_appointment:
                # Kein passender Termin gefunden
                table.add_row([
                    m1ziffer,
                    patient_name,
                    "",
                    "",
                    untersuchung.get("UntersuchungID", ""),
                    untersuchung.get("UntersuchungartID", ""),
                    "X"
                ])
        
        self.comparison_table = table
        return table
    
    def save_table_to_csv(self, filename):
        """
        Speichert die Vergleichstabelle als CSV-Datei.
        
        Args:
            filename: Name der CSV-Datei
        """
        if self.comparison_table is None:
            logger.error("Keine Vergleichstabelle vorhanden.")
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.comparison_table.field_names)
            for row in self.comparison_table._rows:
                writer.writerow(row)
        
        logger.info(f"Tabelle wurde als {filename} gespeichert.")
    
    def save_data_to_json(self, calldoc_filename, sqlhk_filename):
        """
        Speichert die Rohdaten als JSON-Dateien.
        
        Args:
            calldoc_filename: Name der CallDoc-JSON-Datei
            sqlhk_filename: Name der SQLHK-JSON-Datei
        """
        with open(calldoc_filename, 'w', encoding='utf-8') as f:
            json.dump(self.calldoc_appointments, f, indent=2, ensure_ascii=False)
        
        with open(sqlhk_filename, 'w', encoding='utf-8') as f:
            json.dump(self.enriched_untersuchungen, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Rohdaten wurden in JSON-Dateien gespeichert: {calldoc_filename}, {sqlhk_filename}")
    
    def run_comparison(self, date_str, appointment_type_id=None, doctor_id=None, room_id=None, 
                      status=None, smart_status_filter=True, save_results=True):
        """
        Führt einen vollständigen Vergleich zwischen CallDoc und SQLHK durch.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD für CallDoc oder DD.MM.YYYY für SQLHK
            appointment_type_id: Optional, ID des Termintyps
            doctor_id: Optional, ID des Arztes
            room_id: Optional, ID des Raums
            status: Optional, expliziter Status-Filter
            smart_status_filter: Optional, wenn True, wird die Statusfilterung basierend auf dem Datum intelligent angepasst
            save_results: Optional, wenn True, werden die Ergebnisse als Dateien gespeichert
            
        Returns:
            Dictionary mit den Ergebnissen:
            - calldoc_appointments: Liste der CallDoc-Termine
            - sqlhk_untersuchungen: Liste der SQLHK-Untersuchungen
            - comparison_table: Vergleichstabelle als PrettyTable-Objekt
            - status_analysis: Statusanalyse der CallDoc-Termine
            - statistics: Statistiken zum Vergleich
        """
        # Datumsformate konvertieren
        if "-" in date_str:  # Format YYYY-MM-DD
            calldoc_date = date_str
            day, month, year = date_str.split("-")[2], date_str.split("-")[1], date_str.split("-")[0]
            sqlhk_date = f"{day}.{month}.{year}"
        else:  # Format DD.MM.YYYY
            sqlhk_date = date_str
            day, month, year = date_str.split(".")
            calldoc_date = f"{year}-{month}-{day}"
        
        # CallDoc-Termine abrufen
        logger.info(f"Rufe CallDoc-Termine für {calldoc_date} ab...")
        appointments = self.get_calldoc_appointments(
            calldoc_date,
            filter_by_type_id=appointment_type_id,
            doctor_id=doctor_id,
            room_id=room_id,
            status=status,
            smart_status_filter=smart_status_filter
        )
        
        # SQLHK-Untersuchungen abrufen
        untersuchungen = self.get_sqlhk_untersuchungen(sqlhk_date)
        
        # Untersuchungen um M1Ziffer ergänzen
        enriched_untersuchungen = self.enrich_untersuchungen_with_m1ziffer(untersuchungen)
        
        # Vergleichstabelle erstellen
        table = self.create_comparison_table(appointments, enriched_untersuchungen)
        
        # Statusanalyse durchführen
        status_analysis = self.analyze_appointment_status(appointments)
        
        # Statistiken berechnen
        match_count = sum(1 for row in table._rows if row[6] == "JA")
        mismatch_count = sum(1 for row in table._rows if row[6] == "X")
        
        statistics = {
            "matches": match_count,
            "mismatches": mismatch_count,
            "total_rows": len(table._rows)
        }
        
        # Ergebnisse speichern, falls gewünscht
        if save_results:
            csv_filename = f"vergleich_calldoc_sqlhk_{sqlhk_date.replace('.', '_')}.csv"
            self.save_table_to_csv(csv_filename)
            
            calldoc_json_file = f"calldoc_termine_{calldoc_date}.json"
            sqlhk_json_file = f"sqlhk_untersuchungen_mit_m1ziffer_{sqlhk_date.replace('.', '_')}.json"
            self.save_data_to_json(calldoc_json_file, sqlhk_json_file)
        
        # Ergebnisse zurückgeben
        return {
            "calldoc_appointments": appointments,
            "sqlhk_untersuchungen": enriched_untersuchungen,
            "comparison_table": table,
            "status_analysis": status_analysis,
            "statistics": statistics
        }
    
    def print_results(self, results=None):
        """
        Gibt die Ergebnisse des Vergleichs aus.
        
        Args:
            results: Optional, Ergebnisse des Vergleichs (falls None, werden die gespeicherten verwendet)
        """
        if results is None:
            if self.comparison_table is None or self.status_analysis is None:
                logger.error("Keine Ergebnisse vorhanden.")
                return
                
            table = self.comparison_table
            status_analysis = self.status_analysis
            statistics = {
                "matches": sum(1 for row in table._rows if row[6] == "JA"),
                "mismatches": sum(1 for row in table._rows if row[6] == "X"),
                "total_rows": len(table._rows)
            }
        else:
            table = results["comparison_table"]
            status_analysis = results["status_analysis"]
            statistics = results["statistics"]
        
        # Vergleichstabelle ausgeben
        print("\nVergleichstabelle:")
        print(table)
        
        # Statistiken ausgeben
        print("\nStatistiken:")
        print(f"- Übereinstimmungen: {statistics['matches']}")
        print(f"- Unterschiede: {statistics['mismatches']}")
        
        # CallDoc-Terminanalyse ausgeben
        print("\nCallDoc-Terminanalyse:")
        print(f"- Gesamtanzahl Termine: {status_analysis['gesamt']}")
        print("- Statusverteilung:")
        for status, count in status_analysis['status'].items():
            print(f"  * {status}: {count}")
        print("- Patientendaten:")
        print(f"  * Mit Patientendaten: {status_analysis['patient']['mit_patient']}")
        print(f"  * Ohne Patientendaten: {status_analysis['patient']['ohne_patient']}")
    
    def synchronize_patients(self, appointments=None, save_results=True):
        """
        Synchronisiert Patienten aus CallDoc-Terminen mit der SQLHK-Datenbank.
        
        Args:
            appointments: Optional, Liste der CallDoc-Termine (falls None, werden die gespeicherten verwendet)
            save_results: Optional, wenn True, werden die Ergebnisse als Dateien gespeichert
            
        Returns:
            Dictionary mit den Ergebnissen der Synchronisation
        """
        if appointments is None:
            appointments = self.calldoc_appointments
            
        if not appointments:
            logger.warning("Keine Termine für die Patienten-Synchronisation gefunden.")
            return {
                "success": False,
                "message": "Keine Termine gefunden",
                "stats": {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "updated": 0,
                    "inserted": 0
                }
            }
        
        # Patienten aus den Terminen synchronisieren
        stats = self.patient_synchronizer.synchronize_patients_from_appointments(appointments)
        
        # Ergebnisse speichern, wenn gewünscht
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"patient_sync_results_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.info(f"Synchronisationsergebnisse gespeichert in {filename}")
        
        return {
            "success": stats["success"] > 0,
            "message": f"{stats['success']} von {stats['total']} Patienten erfolgreich synchronisiert",
            "stats": stats
        }
    
    def print_patient_sync_results(self, results):
        """
        Gibt die Ergebnisse der Patienten-Synchronisation aus.
        
        Args:
            results: Ergebnisse der Synchronisation
        """
        stats = results.get("stats", {})
        
        print("\nErgebnisse der Patienten-Synchronisation:")
        print(f"- Gesamtanzahl Patienten: {stats.get('total', 0)}")
        print(f"- Erfolgreich synchronisiert: {stats.get('success', 0)}")
        print(f"- Fehlgeschlagen: {stats.get('failed', 0)}")
        print(f"- Aktualisiert: {stats.get('updated', 0)}")
        print(f"- Neu eingefügt: {stats.get('inserted', 0)}")
        
        # Detaillierte Ergebnisse in einer Tabelle ausgeben
        if "details" in stats and stats["details"]:
            table = PrettyTable()
            table.field_names = ["Termin-ID", "Patienten-ID", "Status", "Nachricht"]
            
            for detail in stats["details"]:
                table.add_row([
                    detail.get("appointment_id", "-"),
                    detail.get("patient_id", "-"),
                    "Erfolg" if detail.get("success", False) else "Fehler",
                    detail.get("message", "-")
                ])
            
            print("\nDetails:")
            print(table)
    
    def run_patient_synchronization(self, date_str, appointment_type_id=None, doctor_id=None, 
                                  room_id=None, status=None, smart_status_filter=True, save_results=True):
        """
        Führt eine vollständige Patienten-Synchronisation durch.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD für CallDoc
            appointment_type_id: Optional, ID des Termintyps
            doctor_id: Optional, ID des Arztes
            room_id: Optional, ID des Raums
            status: Optional, expliziter Status-Filter
            smart_status_filter: Optional, wenn True, wird die Statusfilterung basierend auf dem Datum intelligent angepasst
            save_results: Optional, wenn True, werden die Ergebnisse als Dateien gespeichert
            
        Returns:
            Dictionary mit den Ergebnissen der Synchronisation
        """
        # Termine aus CallDoc abrufen
        appointments = self.get_calldoc_appointments(
            date_str=date_str,
            filter_by_type_id=appointment_type_id,
            doctor_id=doctor_id,
            room_id=room_id,
            status=status,
            smart_status_filter=smart_status_filter
        )
        
        if not appointments:
            logger.warning(f"Keine Termine für das Datum {date_str} gefunden.")
            return {
                "success": False,
                "message": f"Keine Termine für das Datum {date_str} gefunden",
                "stats": {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "updated": 0,
                    "inserted": 0
                }
            }
        
        # Patienten synchronisieren
        results = self.synchronize_patients(appointments, save_results)
        
        # Ergebnisse ausgeben
        self.print_patient_sync_results(results)
        
        return results
