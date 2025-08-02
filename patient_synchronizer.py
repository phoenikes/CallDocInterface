"""
Patient-Synchronizer für CallDoc und SQLHK.

Dieses Modul enthält die Klasse PatientSynchronizer, die für die Synchronisation
von Patientendaten zwischen CallDoc und der SQLHK-Datenbank zuständig ist.

Die Klasse bietet Funktionen zum:
1. Abrufen von Patientendaten aus CallDoc-Terminen
2. Abrufen von Patientendaten aus SQLHK
3. Mapping der Datenstrukturen zwischen beiden Systemen
4. Aktualisieren oder Einfügen (Upsert) von Patientendaten in SQLHK
5. Synchronisieren von Patientendaten aus einer Liste von Terminen

Unterstützte Felder für die Synchronisation:
- Nachname, Vorname
- Geburtsdatum
- Adresse (PLZ, Stadt, Straße)
- Geschlecht
- Versichertennummer (insurance_number)
- Mobiltelefonnummer (erste Mobilnummer aus dem phones-Array)
- E-Mail-Adresse (erste E-Mail aus dem emails-Array)
- M1Ziffer/heydokid als eindeutige Kennung

PatientSynchronizer - Synchronisiert Patientendaten zwischen CallDoc und SQLHK

Diese Klasse ermöglicht die Synchronisation von Patientendaten aus CallDoc-Terminen
in die SQLHK-Datenbank. Sie extrahiert relevante Patientenfelder aus den Terminen,
mappt sie auf das SQLHK-Format und führt dann Insert- oder Update-Operationen durch.

Unterstützte Felder:
- Vorname (name)
- Nachname (surname)
- Geburtsdatum (date_of_birth)
- M1Ziffer/PIZ (piz)
- Versichertennummer (insurance_number)
- Telefonnummer (phone_number, aus phones-Array)
- E-Mail-Adresse (email, aus emails-Array)
- PLZ (city_code)

Zukünftig zu implementierende Felder:
- CallDoc Patienten-ID (patient) - Eindeutige ID des Patienten in CallDoc
  Diese ID könnte als zusätzliches Identifikationsmerkmal neben der M1Ziffer
  verwendet werden, um Patienten zuverlässiger zu identifizieren.

Beispiel:
    synchronizer = PatientSynchronizer()
    appointments = calldoc.appointment_search(appointment_type_id=24)
    stats = synchronizer.synchronize_patients_from_appointments(appointments)
    print(f"Synchronisiert: {stats['success']}, Fehlgeschlagen: {stats['failed']}")

Autor: Markus
Version: 1.0 (2025-08-01)
"""

import json
import requests
from datetime import datetime
import logging
import time
from constants import API_BASE_URL, SQLHK_API_BASE_URL

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatientSynchronizer:
    """
    Klasse zur Synchronisation von Patientendaten zwischen CallDoc und SQLHK.
    
    Diese Klasse bietet Methoden zum Extrahieren von Patientendaten aus CallDoc-Terminen,
    Mapping auf das SQLHK-Format und Synchronisieren mit der SQLHK-Datenbank.
    Die Synchronisation erfolgt durch Suche nach vorhandenen Patienten anhand von
    Name, Vorname, Geburtsdatum oder der heydokid und anschließendes Aktualisieren
    oder Neuanlegen der Patientendaten.
    """
    
    def __init__(self):
        """Initialisiert den PatientSynchronizer."""
        self.calldoc_api_base = API_BASE_URL
        self.sqlhk_api_base = SQLHK_API_BASE_URL
    
    def get_sqlhk_patient(self, patient_id=None, search_params=None):
        """
        Ruft einen Patienten aus SQLHK ab.
        
        Args:
            patient_id: Die ID des Patienten in SQLHK (optional)
            search_params: Suchparameter für den Patienten (optional)
            
        Returns:
            dict: Die Patientendaten oder None bei Fehler
        """
        logger = logging.getLogger("patient_synchronizer")
        try:
            if patient_id:
                # Suche nach PatientID
                sql_query = f"SELECT * FROM Patient WHERE PatientID = {patient_id}"
                url = f"{self.sqlhk_api_base}/execute_sql"
                response = requests.post(url, json={"query": sql_query, "database": "SQLHK"})
            elif search_params:
                # Suche nach verschiedenen Kriterien
                conditions = []
                params = {}
                
                # Suche nach heydokid (CallDoc Patient ID)
                if "heydokid" in search_params and search_params["heydokid"]:
                    conditions.append("heydokid = @heydokid")
                    params["heydokid"] = search_params["heydokid"]
                
                # Suche nach Name und Geburtsdatum
                if "Nachname" in search_params and search_params["Nachname"]:
                    conditions.append("Nachname = @Nachname")
                    params["Nachname"] = search_params["Nachname"]
                
                if "Vorname" in search_params and search_params["Vorname"]:
                    conditions.append("Vorname = @Vorname")
                    params["Vorname"] = search_params["Vorname"]
                
                if "Geburtsdatum" in search_params and search_params["Geburtsdatum"]:
                    conditions.append("Geburtsdatum = @Geburtsdatum")
                    params["Geburtsdatum"] = search_params["Geburtsdatum"]
                
                if not conditions:
                    logger.error("Keine gültigen Suchparameter angegeben")
                    return None
                
                # SQL-Query zusammenbauen
                where_clause = " AND ".join(conditions)
                sql_query = f"SELECT * FROM Patient WHERE {where_clause}"
                
                # API-Aufruf mit SQL-Query und Parametern
                url = f"{self.sqlhk_api_base}/execute_sql"
                response = requests.post(url, json={"query": sql_query, "params": params, "database": "SQLHK"})
            else:
                logger.error("Weder patient_id noch search_params angegeben")
                return None
            
            if response.status_code == 200:
                result = response.json()
                # execute_sql gibt ein Objekt mit rows zurück
                if "rows" in result and result["rows"]:
                    return result["rows"][0]  # Ersten Treffer zurückgeben
                else:
                    logger.info("Kein Patient gefunden")
                    return None
            else:
                logger.error(f"Fehler beim Abrufen des Patienten aus SQLHK: {response.status_code}")
                logger.error(f"API-Antwort: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Fehler beim Zugriff auf die SQLHK-API: {str(e)}")
            return None
    
    def map_appointment_to_sqlhk(self, appointment):
        """
        Mappt die Patientendaten aus einem CallDoc-Termin auf das SQLHK-Format.
        
        Diese Methode extrahiert alle relevanten Patientendaten direkt aus dem appointment-Objekt
        und konvertiert sie in das Format, das von der SQLHK-Datenbank erwartet wird.
        
        Folgende Felder werden extrahiert und gemappt:
        - Nachname: aus surname oder last_name
        - Vorname: aus name oder first_name
        - Geburtsdatum: aus date_of_birth (konvertiert von YYYY-MM-DD zu DD.MM.YYYY)
        - PLZ: aus city_code
        - Stadt: aus city
        - Straße: aus street + house_number
        - Geschlecht: aus gender (0=unbekannt, 1=männlich, 2=weiblich)
        - E-Mail: aus email oder dem ersten Eintrag im emails-Array
        - Handy: erste Mobilnummer aus dem phones-Array mit phone_type="Mobile"
        - M1Ziffer/heydokid: aus piz (Patient-Identifikationsnummer)
        - Versichertennummer: aus insurance_number
        
        Args:
            appointment (dict): Die Termindaten aus CallDoc mit den Patienteninformationen
            
        Returns:
            dict: Die gemappten Patientendaten im SQLHK-Format, bereinigt von None-Werten
        """
        logger = logging.getLogger("patient_synchronizer")
        if not appointment:
            return None
        
        # Extrahiere die relevanten Daten direkt aus dem appointment
        nachname = appointment.get("surname") or appointment.get("last_name")
        vorname = appointment.get("name") or appointment.get("first_name")
        
        # Geburtsdatum konvertieren (YYYY-MM-DD -> DD.MM.YYYY)
        geburtsdatum = None
        birth_date = appointment.get("date_of_birth")
        if birth_date:
            try:
                date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
                geburtsdatum = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                logger.warning(f"Ungültiges Geburtsdatum-Format: {birth_date}")
        
        # Weitere Daten extrahieren
        plz = appointment.get("city_code")
        stadt = appointment.get("city")
        strasse = appointment.get("street")
        if appointment.get("house_number"):
            strasse = f"{strasse} {appointment.get('house_number')}"
        telefon = appointment.get("phone_number")
        handy = None
        email = appointment.get("email")
        versicherung = appointment.get("insurance_provider")
        
        # Versichertennummer aus patient_insurance_number
        versichertennr = appointment.get("patient_insurance_number")
        
        # Handy-Nummer aus phones-Array extrahieren (erste Mobilnummer)
        if "phones" in appointment and isinstance(appointment["phones"], list) and appointment["phones"]:
            for phone_entry in appointment["phones"]:
                if phone_entry.get("phone_type") == "Mobile" and phone_entry.get("phone_number"):
                    handy = phone_entry.get("phone_number")
                    break
        
        # E-Mail aus emails-Array extrahieren (erste E-Mail)
        if "emails" in appointment and isinstance(appointment["emails"], list) and appointment["emails"]:
            if appointment["emails"][0].get("email"):
                email = appointment["emails"][0].get("email")
        
        # Geschlecht (falls vorhanden)
        geschlecht = 0  # Standardwert: unbekannt
        if appointment.get("gender"):
            if appointment.get("gender").lower() in ["m", "männlich", "male"]:
                geschlecht = 1  # männlich
            elif appointment.get("gender").lower() in ["w", "weiblich", "female"]:
                geschlecht = 2  # weiblich
        
        # PIZ als M1Ziffer und ID als heydokid verwenden
        piz = appointment.get("piz")
        patient_id = appointment.get("id")
        
        # Mapping auf SQLHK-Format entsprechend der Datenbankstruktur
        sqlhk_patient = {
            "Nachname": nachname,
            "Vorname": vorname,
            "Geburtsdatum": geburtsdatum,
            "PLZ": plz if plz and plz.isdigit() else None,  # PLZ muss eine Zahl sein
            "Stadt": stadt,
            "Strasse": strasse,
            "Geschlecht": geschlecht,  # Immer gesetzt, mindestens auf 0 (unbekannt)
            "email": email,
            "handy": handy,
            "M1Ziffer": piz,  # PIZ als M1Ziffer (eindeutiges Suchkriterium)
            "heydokid": patient_id,  # Wir verwenden die CallDoc-ID als heydokid
            "versichertennr": versichertennr  # Versichertennummer aus insurance_number
        }
        
        # Entferne None-Werte, aber behalte Geschlecht immer bei
        return {k: v for k, v in sqlhk_patient.items() if v is not None or k == "Geschlecht"}
    
    def map_calldoc_to_sqlhk(self, calldoc_patient):
        """
        Mappt die Patientendaten aus CallDoc auf das SQLHK-Format.
        
        Args:
            calldoc_patient: Die Patientendaten aus CallDoc
            
        Returns:
            dict: Die gemappten Patientendaten im SQLHK-Format
        """
        if not calldoc_patient:
            return None
        
        # Extrahiere die relevanten Daten aus dem CallDoc-Patienten
        nachname = calldoc_patient.get("surname") or calldoc_patient.get("last_name")
        vorname = calldoc_patient.get("name") or calldoc_patient.get("first_name")
        
        # Geburtsdatum konvertieren (YYYY-MM-DD -> DD.MM.YYYY)
        geburtsdatum = None
        birth_date = calldoc_patient.get("date_of_birth")
        if birth_date:
            try:
                date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
                geburtsdatum = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                logger.warning(f"Ungültiges Geburtsdatum-Format: {birth_date}")
        
        # Weitere Daten extrahieren
        plz = calldoc_patient.get("city_code")
        ort = calldoc_patient.get("city")
        strasse = calldoc_patient.get("street")
        hausnummer = calldoc_patient.get("house_number")
        telefon = calldoc_patient.get("phone")
        mobil = calldoc_patient.get("mobile")
        email = calldoc_patient.get("email")
        versicherung = calldoc_patient.get("insurance")
        
        # Mapping auf SQLHK-Format
        sqlhk_patient = {
            "Nachname": nachname,
            "Vorname": vorname,
            "Geburtsdatum": geburtsdatum,
            "PLZ": plz,
            "Ort": ort,
            "Strasse": strasse,
            "Hausnummer": hausnummer,
            "Telefon": telefon,
            "Mobil": mobil,
            "Email": email,
            "Versicherung": versicherung
        }
        
        # Entferne None-Werte
        return {k: v for k, v in sqlhk_patient.items() if v is not None}
    
    def upsert_patient(self, sqlhk_patient, patient_id=None):
        """
        Aktualisiert oder fügt einen Patienten in SQLHK ein.
        
        Args:
            sqlhk_patient: Die zu speichernden Patientendaten
            patient_id: Die ID des Patienten in SQLHK (optional, nur bei Update)
            
        Returns:
            dict: Die Antwort der API oder None bei Fehler
        """
        logger = logging.getLogger("patient_synchronizer")
        start_zeit = time.time()
        try:
            if patient_id:
                # Update eines bestehenden Patienten
                sqlhk_patient["PatientID"] = patient_id
                url = f"{self.sqlhk_api_base}/upsert_data"
                payload = {
                    "table": "Patient",
                    "database": "SQLHK",
                    "search_fields": {"PatientID": patient_id},
                    "update_fields": sqlhk_patient,
                    "key_fields": ["PatientID"],
                    "operation": "update"
                }
                response = requests.post(url, json=payload)
                action = "Aktualisierung"
            else:
                # Prüfen, ob ein Patient mit der gleichen M1Ziffer bereits existiert
                if "M1Ziffer" in sqlhk_patient and sqlhk_patient["M1Ziffer"]:
                    m1ziffer = sqlhk_patient["M1Ziffer"]
                    sql_query = f"SELECT * FROM Patient WHERE M1Ziffer = @M1Ziffer"
                    search_url = f"{self.sqlhk_api_base}/execute_sql"
                    search_result = requests.post(search_url, json={"query": sql_query, "params": {"M1Ziffer": m1ziffer}, "database": "SQLHK"})
                    
                    if search_result.status_code == 200:
                        result = search_result.json()
                        if "rows" in result and result["rows"] and len(result["rows"]) > 0:
                            # Patient existiert bereits, Update durchführen
                            existing_patient = result["rows"][0]
                            patient_id = existing_patient.get("PatientID")
                            sqlhk_patient["PatientID"] = patient_id
                            logger.info(f"Patient mit M1Ziffer {m1ziffer} existiert bereits (ID: {patient_id}), führe Update durch")
                            
                            url = f"{self.sqlhk_api_base}/upsert_data"
                            payload = {
                                "table": "Patient",
                                "database": "SQLHK",
                                "search_fields": {"PatientID": patient_id},
                                "update_fields": sqlhk_patient,
                                "key_fields": ["PatientID"],
                                "operation": "update"
                            }
                            response = requests.post(url, json=payload)
                            action = "Aktualisierung"
                            return response.json() if response.status_code in [200, 201] else None
                
                # Einfügen eines neuen Patienten
                url = f"{self.sqlhk_api_base}/upsert_data"
                payload = {
                    "table": "Patient",
                    "database": "SQLHK",
                    "search_fields": {"M1Ziffer": sqlhk_patient.get("M1Ziffer")} if "M1Ziffer" in sqlhk_patient else {},
                    "update_fields": sqlhk_patient,
                    "key_fields": ["M1Ziffer"] if "M1Ziffer" in sqlhk_patient else [],
                    "operation": "insert"
                }
                response = requests.post(url, json=payload)
                action = "Einfügen"
            
            if response.status_code in [200, 201]:
                result = response.json()
                # Prüfen, ob es sich um ein Update oder Insert handelt
                if "operation_code" in result:
                    if result["operation_code"] == 1:  # Update
                        logger.info(f"Patient mit M1Ziffer {sqlhk_patient.get('M1Ziffer')} wurde aktualisiert")
                        result["is_update"] = True
                    elif result["operation_code"] == 2:  # Insert
                        logger.info(f"Patient mit M1Ziffer {sqlhk_patient.get('M1Ziffer')} wurde neu angelegt")
                        result["is_update"] = False
                    else:
                        logger.info(f"{action} des Patienten erfolgreich")
                else:
                    logger.info(f"{action} des Patienten erfolgreich")
                return result
            else:
                logger.error(f"Fehler beim {action.lower()} des Patienten: {response.status_code}")
                logger.error(f"API-Antwort: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Fehler beim {action.lower() if 'action' in locals() else 'Speichern'} des Patienten: {str(e)}")
            return None
    
    # Die synchronize_patient-Methode wurde entfernt, da die Synchronisation
    # jetzt direkt in der synchronize_patients_from_appointments-Methode erfolgt.
    
    def synchronize_patients_from_appointments(self, appointments):
        """
        Synchronisiert Patienten aus einer Liste von CallDoc-Terminen mit der SQLHK-Datenbank.
        
        Diese Methode durchläuft alle übergebenen Termine und extrahiert die Patientendaten.
        Für jeden Patienten wird geprüft, ob er bereits in der SQLHK-Datenbank existiert:
        1. Zuerst wird nach der M1Ziffer (PIZ) gesucht
        2. Falls nicht gefunden, wird nach Name, Vorname und Geburtsdatum gesucht
        
        Abhängig vom Ergebnis wird der Patient entweder aktualisiert oder neu angelegt.
        Die Methode führt eine detaillierte Statistik über alle Vorgänge.
        
        Args:
            appointments (list): Liste von CallDoc-Terminen mit Patientendaten
            
        Returns:
            dict: Statistik über die Synchronisation mit folgenden Schlüsseln:
                - total: Gesamtzahl der verarbeiteten Patienten
                - success: Anzahl der erfolgreich synchronisierten Patienten
                - failed: Anzahl der fehlgeschlagenen Synchronisationen
                - updated: Anzahl der aktualisierten Patienten
                - inserted: Anzahl der neu angelegten Patienten
                - details: Liste mit Details zu jedem verarbeiteten Patienten
        """
        logger = logging.getLogger("patient_synchronizer")
        gesamt_start_zeit = time.time()
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "updated": 0,
            "inserted": 0,
            "details": []
        }
        
        if not appointments:
            return stats
        
        for appointment in appointments:
            patient_start_zeit = time.time()
            stats["total"] += 1
            appointment_id = appointment.get("id")
            logger.info(f"Starte Verarbeitung von Patient {stats['total']} (Termin-ID: {appointment_id})")
            
            # Prüfen, ob die notwendigen Patientendaten im Termin vorhanden sind
            if not appointment.get("surname") or not appointment.get("name") or not appointment.get("date_of_birth"):
                stats["failed"] += 1
                stats["details"].append({
                    "appointment_id": appointment_id,
                    "success": False,
                    "message": "Unvollständige Patientendaten im Termin"
                })
                continue
            
            # Patientendaten aus dem Termin extrahieren und auf SQLHK-Format mappen
            mapping_start = time.time()
            sqlhk_patient = self.map_appointment_to_sqlhk(appointment)
            mapping_ende = time.time()
            logger.info(f"Mapping der Patientendaten: {mapping_ende - mapping_start:.2f} Sekunden")
            
            if not sqlhk_patient:
                stats["failed"] += 1
                stats["details"].append({
                    "appointment_id": appointment_id,
                    "success": False,
                    "message": "Fehler beim Mapping der Patientendaten"
                })
                continue
            
            # Nach einem passenden Patienten in SQLHK suchen
            search_params = {
                "Nachname": sqlhk_patient.get("Nachname"),
                "Vorname": sqlhk_patient.get("Vorname"),
                "Geburtsdatum": sqlhk_patient.get("Geburtsdatum")
            }
            
            # Optimierte Suche: Wir suchen zuerst nach M1Ziffer und dann nach Name+Geburtsdatum in einer einzigen Anfrage
            suche_start = time.time()
            existing_patient = None
            search_conditions = []
            search_params_dict = {}
            
            # M1Ziffer-Suche vorbereiten
            if "M1Ziffer" in sqlhk_patient and sqlhk_patient["M1Ziffer"]:
                search_conditions.append("M1Ziffer = @M1Ziffer")
                search_params_dict["M1Ziffer"] = sqlhk_patient["M1Ziffer"]
            
            # Name+Geburtsdatum-Suche als Alternative vorbereiten
            name_conditions = []
            if search_params["Nachname"]:
                name_conditions.append("Nachname = @Nachname")
                search_params_dict["Nachname"] = search_params["Nachname"]
            
            if search_params["Vorname"]:
                name_conditions.append("Vorname = @Vorname")
                search_params_dict["Vorname"] = search_params["Vorname"]
            
            if search_params["Geburtsdatum"]:
                name_conditions.append("Geburtsdatum = @Geburtsdatum")
                search_params_dict["Geburtsdatum"] = search_params["Geburtsdatum"]
            
            # Name+Geburtsdatum-Bedingung zusammenfügen
            if name_conditions:
                name_where = " AND ".join(name_conditions)
                search_conditions.append(f"({name_where})")
            
            # Gesamte Suchbedingung erstellen
            if search_conditions:
                where_clause = " OR ".join(search_conditions)
                sql_query = f"SELECT * FROM Patient WHERE {where_clause}"
                url = f"{self.sqlhk_api_base}/execute_sql"
                search_result = requests.post(url, json={"query": sql_query, "params": search_params_dict, "database": "SQLHK"})
                
                if search_result.status_code == 200:
                    result = search_result.json()
                    if "rows" in result and result["rows"] and len(result["rows"]) > 0:
                        existing_patient = result["rows"][0]
            
            suche_ende = time.time()
            logger.info(f"Suche nach existierendem Patienten: {suche_ende - suche_start:.2f} Sekunden")
            
            # Patient aktualisieren oder neu anlegen
            db_operation_start = time.time()
            if existing_patient:
                # Patient aktualisieren
                patient_id = existing_patient.get("PatientID")
                logger.info(f"Aktualisiere bestehenden Patienten mit ID {patient_id} und M1Ziffer {sqlhk_patient.get('M1Ziffer')}")
                update_result = self.upsert_patient(sqlhk_patient, patient_id)
                
                if update_result and "success" in update_result and update_result["success"]:
                    stats["success"] += 1
                    stats["updated"] += 1
                    stats["details"].append({
                        "appointment_id": appointment_id,
                        "patient_id": patient_id,
                        "success": True,
                        "message": "Patient aktualisiert"
                    })
                    logger.info(f"Patient mit ID {patient_id} erfolgreich aktualisiert")
                else:
                    stats["failed"] += 1
                    stats["details"].append({
                        "appointment_id": appointment_id,
                        "patient_id": patient_id,
                        "success": False,
                        "message": "Fehler beim Aktualisieren des Patienten"
                    })
                    logger.error(f"Fehler beim Aktualisieren des Patienten mit ID {patient_id}")
                
                db_operation_ende = time.time()
                logger.info(f"Aktualisierung des Patienten: {db_operation_ende - db_operation_start:.2f} Sekunden")
            else:
                logger.info(f"Lege neuen Patienten mit M1Ziffer {sqlhk_patient.get('M1Ziffer')} an")
                insert_result = self.upsert_patient(sqlhk_patient)
                
                if insert_result and "success" in insert_result and insert_result["success"]:
                    stats["success"] += 1
                    
                    # Prüfen, ob es ein Update oder Insert war
                    if "is_update" in insert_result and insert_result["is_update"]:
                        stats["updated"] += 1
                        patient_id = insert_result.get("id", "Aktualisiert")
                        stats["details"].append({
                            "appointment_id": appointment_id,
                            "patient_id": patient_id,
                            "success": True,
                            "message": "Patient aktualisiert"
                        })
                        logger.info(f"Patient mit M1Ziffer {sqlhk_patient.get('M1Ziffer')} erfolgreich aktualisiert")
                    else:
                        stats["inserted"] += 1
                        stats["details"].append({
                            "appointment_id": appointment_id,
                            "patient_id": "Neu angelegt",
                            "success": True,
                            "message": "Neuer Patient angelegt"
                        })
                        logger.info(f"Neuer Patient mit M1Ziffer {sqlhk_patient.get('M1Ziffer')} erfolgreich angelegt")
                else:
                    stats["failed"] += 1
                    stats["details"].append({
                        "appointment_id": appointment_id,
                        "patient_id": "-",
                        "success": False,
                        "message": "Fehler beim Anlegen eines neuen Patienten"
                    })
                    logger.error(f"Fehler beim Anlegen eines neuen Patienten mit M1Ziffer {sqlhk_patient.get('M1Ziffer')}")
                
                db_operation_ende = time.time()
                logger.info(f"Anlegen des neuen Patienten: {db_operation_ende - db_operation_start:.2f} Sekunden")
            
            patient_ende_zeit = time.time()
            logger.info(f"Gesamtzeit für Patient {stats['total']}: {patient_ende_zeit - patient_start_zeit:.2f} Sekunden\n")
        
        gesamt_ende_zeit = time.time()
        logger.info(f"Gesamtzeit für alle {stats['total']} Patienten: {gesamt_ende_zeit - gesamt_start_zeit:.2f} Sekunden")
        logger.info(f"Durchschnittliche Zeit pro Patient: {(gesamt_ende_zeit - gesamt_start_zeit) / max(stats['total'], 1):.2f} Sekunden")
        
        return stats


if __name__ == "__main__":
    # Beispiel für die Verwendung
    import sys
    
    if len(sys.argv) > 1:
        patient_id = sys.argv[1]
        synchronizer = PatientSynchronizer()
        result = synchronizer.synchronize_patient(patient_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Bitte geben Sie eine Patienten-ID an.")
