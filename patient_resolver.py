"""
PatientResolver - Findet oder erstellt Patienten fuer CallDoc-Termine.

Dieser Resolver versucht Patienten in folgender Reihenfolge zu finden:
1. PIZ (M1Ziffer) - Direkte Suche in SQLHK (~0.1 Sek)
2. KVNR - Suche in .con Dateien, dann M1Ziffer extrahieren (~1-2 Sek)
3. Name + Geburtsdatum - Fallback-Suche in .con Dateien (~2 Sek)
4. Neu anlegen - Falls nicht gefunden, neuen Patienten in SQLHK erstellen

Autor: Claude Code
Version: 1.0
Datum: 12.01.2026
"""

import os
import re
import sys
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# SKILLS_CENTRAL fuer KVDT-Parser
SKILLS_CENTRAL_PATH = r"C:\Users\administrator.PRAXIS\PycharmProjects\SKILLS_CENTRAL"
if os.path.exists(SKILLS_CENTRAL_PATH) and SKILLS_CENTRAL_PATH not in sys.path:
    sys.path.append(SKILLS_CENTRAL_PATH)

from mssql_api_client import MsSqlApiClient

logger = logging.getLogger(__name__)

# Standard-Pfad fuer .con Dateien
KVDT_BASE_PATH = r"M:\M1\PROJECT\KBV"


class PatientResolver:
    """
    Resolver fuer Patienten-Zuordnung zwischen CallDoc und SQLHK.

    Loest das Problem, dass Termine ohne PIZ bisher ignoriert wurden.
    """

    def __init__(self, kvdt_path: str = KVDT_BASE_PATH):
        """
        Initialisiert den PatientResolver.

        Args:
            kvdt_path: Basispfad fuer die .con Dateien
        """
        self.kvdt_path = kvdt_path
        self.mssql_client = MsSqlApiClient()
        self.con_files: List[str] = []
        self._con_files_loaded = False

        # Statistik
        self.stats = {
            "resolved_by_piz": 0,
            "resolved_by_kvnr": 0,
            "resolved_by_name_dob": 0,
            "created_new": 0,
            "failed": 0
        }

    def _ensure_con_files_loaded(self):
        """Laedt .con Dateien nur bei Bedarf (lazy loading)."""
        if self._con_files_loaded:
            return

        try:
            if not os.path.exists(self.kvdt_path):
                logger.warning(f"KVDT-Pfad nicht gefunden: {self.kvdt_path}")
                self._con_files_loaded = True
                return

            for root, dirs, files in os.walk(self.kvdt_path):
                for f in files:
                    if f.endswith('.con'):
                        self.con_files.append(os.path.join(root, f))

            logger.info(f"PatientResolver: {len(self.con_files)} .con Dateien geladen")
            self._con_files_loaded = True

        except Exception as e:
            logger.error(f"Fehler beim Laden der .con Dateien: {e}")
            self._con_files_loaded = True

    def resolve_patient(self, appointment: Dict) -> Optional[Dict]:
        """
        Loest einen Patienten aus einem CallDoc-Termin auf.

        Versucht in dieser Reihenfolge:
        1. PIZ vorhanden -> Direkte SQLHK-Suche
        2. KVNR vorhanden -> Suche M1Ziffer in .con Dateien
        3. Name+Geburtsdatum -> Fallback-Suche in .con Dateien
        4. Nicht gefunden -> Neuen Patienten anlegen

        Args:
            appointment: CallDoc-Termin Dictionary

        Returns:
            Dictionary mit:
            - patient_id: SQLHK PatientID
            - m1ziffer: M1Ziffer
            - method: Wie gefunden (piz, kvnr, name_dob, new)
            - new_patient: True wenn neu angelegt
        """
        piz = appointment.get("piz")
        kvnr = appointment.get("patient_insurance_number")
        surname = appointment.get("surname")
        name = appointment.get("name")
        dob = appointment.get("date_of_birth")

        result = {
            "patient_id": None,
            "m1ziffer": None,
            "method": None,
            "new_patient": False,
            "appointment_id": appointment.get("id")
        }

        # 1. Versuche PIZ
        if piz:
            patient = self._resolve_by_piz(piz)
            if patient:
                result["patient_id"] = patient.get("PatientID")
                result["m1ziffer"] = piz
                result["method"] = "piz"
                self.stats["resolved_by_piz"] += 1
                logger.info(f"Patient via PIZ gefunden: {piz} -> PatientID {result['patient_id']}")
                return result

        # 2. Versuche KVNR
        if kvnr and kvnr.strip():
            m1ziffer = self._resolve_by_kvnr(kvnr)
            if m1ziffer:
                patient = self._resolve_by_piz(m1ziffer)
                if patient:
                    result["patient_id"] = patient.get("PatientID")
                    result["m1ziffer"] = m1ziffer
                    result["method"] = "kvnr"
                    self.stats["resolved_by_kvnr"] += 1
                    logger.info(f"Patient via KVNR gefunden: {kvnr} -> M1Ziffer {m1ziffer} -> PatientID {result['patient_id']}")
                    return result
                else:
                    # M1Ziffer gefunden aber Patient nicht in SQLHK
                    # -> Neuen Patienten mit dieser M1Ziffer anlegen
                    logger.info(f"M1Ziffer {m1ziffer} via KVNR gefunden, aber Patient nicht in SQLHK -> Anlegen")
                    result["m1ziffer"] = m1ziffer

        # 3. Versuche Name + Geburtsdatum
        if surname and name and dob:
            dob_kvdt = self._convert_date_to_kvdt(dob)  # YYYY-MM-DD -> TTMMJJJJ
            if dob_kvdt:
                m1ziffer = self._resolve_by_name_dob(surname, dob_kvdt)
                if m1ziffer:
                    patient = self._resolve_by_piz(m1ziffer)
                    if patient:
                        result["patient_id"] = patient.get("PatientID")
                        result["m1ziffer"] = m1ziffer
                        result["method"] = "name_dob"
                        self.stats["resolved_by_name_dob"] += 1
                        logger.info(f"Patient via Name+Geb.datum gefunden: {surname}, {name} -> M1Ziffer {m1ziffer}")
                        return result
                    else:
                        # M1Ziffer gefunden aber Patient nicht in SQLHK
                        logger.info(f"M1Ziffer {m1ziffer} via Name+Geb.datum gefunden, aber Patient nicht in SQLHK -> Anlegen")
                        result["m1ziffer"] = m1ziffer

        # 4. Patient nicht gefunden -> Neu anlegen
        if surname and name and dob:
            new_patient = self._create_new_patient(appointment, result.get("m1ziffer"))
            if new_patient:
                result["patient_id"] = new_patient.get("PatientID")
                result["m1ziffer"] = new_patient.get("M1Ziffer")
                result["method"] = "new"
                result["new_patient"] = True
                self.stats["created_new"] += 1
                logger.info(f"Neuer Patient angelegt: {surname}, {name} -> PatientID {result['patient_id']}")
                return result

        # Fehlgeschlagen
        self.stats["failed"] += 1
        logger.warning(f"Patient konnte nicht aufgeloest werden: {surname}, {name} (Termin {appointment.get('id')})")
        return None

    def _resolve_by_piz(self, piz: str) -> Optional[Dict]:
        """Sucht Patient in SQLHK nach M1Ziffer."""
        try:
            return self.mssql_client.get_patient_by_piz(piz)
        except Exception as e:
            logger.error(f"Fehler bei PIZ-Suche {piz}: {e}")
            return None

    def _resolve_by_kvnr(self, kvnr: str) -> Optional[str]:
        """
        Sucht M1Ziffer in .con Dateien anhand der KVNR.

        KVNR ist in Feld 3119 gespeichert.

        Args:
            kvnr: Krankenversichertennummer (10-stellig)

        Returns:
            M1Ziffer oder None
        """
        self._ensure_con_files_loaded()

        if not self.con_files:
            return None

        try:
            # KVNR ist in Feld 3119
            pattern = f"3119{kvnr}".encode("cp1252")

            for con_file in self.con_files:
                try:
                    with open(con_file, "rb") as f:
                        content = f.read()

                    if pattern in content:
                        # Gefunden - jetzt M1Ziffer extrahieren
                        kvnr_pos = content.find(pattern)

                        # Suche M1Ziffer (Feld 3000) im Kontext
                        search_start = max(0, kvnr_pos - 2000)
                        search_end = min(len(content), kvnr_pos + 500)
                        case_data = content[search_start:search_end]

                        # Feld 3000 enthaelt die M1Ziffer (7-stellig)
                        m1_matches = re.findall(rb"\d{3}3000(\d{7})", case_data)
                        if m1_matches:
                            m1ziffer = m1_matches[-1].decode("cp1252")
                            logger.debug(f"KVNR {kvnr} gefunden in {con_file}, M1Ziffer: {m1ziffer}")
                            return m1ziffer

                except Exception as e:
                    logger.debug(f"Fehler beim Lesen von {con_file}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Fehler bei KVNR-Suche {kvnr}: {e}")
            return None

    def _resolve_by_name_dob(self, surname: str, dob_kvdt: str) -> Optional[str]:
        """
        Sucht M1Ziffer in .con Dateien anhand von Nachname und Geburtsdatum.

        Args:
            surname: Nachname des Patienten
            dob_kvdt: Geburtsdatum im KVDT-Format (TTMMJJJJ)

        Returns:
            M1Ziffer oder None
        """
        self._ensure_con_files_loaded()

        if not self.con_files:
            return None

        try:
            # Nachname ist in Feld 3101
            surname_pattern = f"3101{surname}".encode("cp1252")
            # Geburtsdatum ist in Feld 3103
            dob_pattern = f"3103{dob_kvdt}".encode("cp1252")

            for con_file in self.con_files:
                try:
                    with open(con_file, "rb") as f:
                        content = f.read()

                    # Erst nach Nachname suchen
                    if surname_pattern not in content:
                        continue

                    # Dann nach Geburtsdatum
                    if dob_pattern not in content:
                        continue

                    # Beide gefunden - pruefen ob im gleichen Fall
                    surname_pos = content.find(surname_pattern)
                    dob_pos = content.find(dob_pattern)

                    # Muessen nahe beieinander sein (gleicher Fall)
                    if abs(surname_pos - dob_pos) < 2000:
                        # M1Ziffer im Kontext suchen
                        search_start = max(0, min(surname_pos, dob_pos) - 500)
                        search_end = max(surname_pos, dob_pos) + 500
                        case_data = content[search_start:search_end]

                        m1_matches = re.findall(rb"\d{3}3000(\d{7})", case_data)
                        if m1_matches:
                            m1ziffer = m1_matches[0].decode("cp1252")
                            logger.debug(f"{surname} ({dob_kvdt}) gefunden in {con_file}, M1Ziffer: {m1ziffer}")
                            return m1ziffer

                except Exception as e:
                    logger.debug(f"Fehler beim Lesen von {con_file}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Fehler bei Name+Geb.datum-Suche {surname}: {e}")
            return None

    def _convert_date_to_kvdt(self, date_str: str) -> Optional[str]:
        """
        Konvertiert Datum von YYYY-MM-DD zu TTMMJJJJ (KVDT-Format).

        Args:
            date_str: Datum im Format YYYY-MM-DD

        Returns:
            Datum im Format TTMMJJJJ oder None
        """
        if not date_str:
            return None

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d%m%Y")
        except ValueError:
            logger.warning(f"Ungueltiges Datumsformat: {date_str}")
            return None

    def _find_patient_in_sqlhk_by_name_dob(self, surname: str, vorname: str, geburtsdatum: str) -> Optional[Dict]:
        """
        Sucht Patient in SQLHK nach Nachname, Vorname und Geburtsdatum.

        WICHTIG: Diese Methode verhindert Duplikate bei Patienten ohne KVNR!

        Args:
            surname: Nachname
            vorname: Vorname
            geburtsdatum: Geburtsdatum im Format DD.MM.YYYY

        Returns:
            Patient-Dictionary oder None
        """
        try:
            # Escape single quotes
            surname_safe = surname.replace("'", "''")
            vorname_safe = vorname.replace("'", "''")

            query = f"""
                SELECT TOP 1 PatientID, M1Ziffer, Nachname, Vorname, Geburtsdatum
                FROM [SQLHK].[dbo].[Patient]
                WHERE Nachname = '{surname_safe}'
                  AND Vorname = '{vorname_safe}'
                  AND Geburtsdatum = '{geburtsdatum}'
            """

            result = self.mssql_client.execute_sql(query, "SQLHK")

            if result.get("rows"):
                patient = result["rows"][0]
                logger.info(f"Patient in SQLHK gefunden: {surname}, {vorname} ({geburtsdatum}) -> PatientID {patient.get('PatientID')}")
                return patient

            return None

        except Exception as e:
            logger.error(f"Fehler bei SQLHK Name+DOB Suche: {e}")
            return None

    def _create_new_patient(self, appointment: Dict, m1ziffer: Optional[str] = None) -> Optional[Dict]:
        """
        Erstellt einen neuen Patienten in SQLHK.

        Args:
            appointment: CallDoc-Termin mit Patientendaten
            m1ziffer: Optional bereits bekannte M1Ziffer

        Returns:
            Dictionary mit PatientID und M1Ziffer oder None
        """
        try:
            surname = appointment.get("surname")
            name = appointment.get("name")
            dob = appointment.get("date_of_birth")

            if not all([surname, name, dob]):
                logger.warning("Unvollstaendige Patientendaten fuer Neuanlage")
                return None

            # Geburtsdatum konvertieren (YYYY-MM-DD -> DD.MM.YYYY)
            try:
                date_obj = datetime.strptime(dob, "%Y-%m-%d")
                geburtsdatum = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                geburtsdatum = None

            # WICHTIG: Erst in SQLHK nach Name+Geburtsdatum suchen!
            # Dies verhindert Duplikate bei Patienten ohne KVNR
            if geburtsdatum:
                existing_by_name = self._find_patient_in_sqlhk_by_name_dob(surname, name, geburtsdatum)
                if existing_by_name:
                    logger.info(f"Patient existiert bereits in SQLHK: {surname}, {name} -> PatientID {existing_by_name.get('PatientID')}")
                    return {
                        "PatientID": existing_by_name.get("PatientID"),
                        "M1Ziffer": existing_by_name.get("M1Ziffer")
                    }

            # Wenn M1Ziffer bekannt, pruefe ob Patient schon existiert
            if m1ziffer:
                existing = self._resolve_by_piz(m1ziffer)
                if existing:
                    logger.info(f"Patient mit M1Ziffer {m1ziffer} existiert bereits: PatientID {existing.get('PatientID')}")
                    return {
                        "PatientID": existing.get("PatientID"),
                        "M1Ziffer": m1ziffer
                    }

            # Wenn keine M1Ziffer bekannt, generiere eine neue
            if not m1ziffer:
                m1ziffer = self._generate_new_m1ziffer()

            # Patient-Daten zusammenstellen
            patient_data = {
                "M1Ziffer": m1ziffer,
                "Nachname": surname,
                "Vorname": name,
                "Geburtsdatum": geburtsdatum
            }

            # Optional: Weitere Daten aus dem Termin
            if appointment.get("patient_insurance_number"):
                patient_data["Versichertennr"] = appointment.get("patient_insurance_number")

            # INSERT in SQLHK
            query = f"""
                INSERT INTO [SQLHK].[dbo].[Patient]
                (M1Ziffer, Nachname, Vorname, Geburtsdatum, Geschlecht)
                VALUES
                ('{m1ziffer}', '{surname.replace("'", "''")}', '{name.replace("'", "''")}', '{geburtsdatum}', 0)
            """

            result = self.mssql_client.execute_sql(query, "SQLHK")

            # INSERT gibt normalerweise keine Rows zurueck - das ist OK
            if result.get("success") or "does not return rows" in str(result.get("error", "")):
                # Patient nochmal suchen um PatientID zu bekommen
                import time
                time.sleep(0.1)  # Kurz warten
                patient = self._resolve_by_piz(m1ziffer)
                if patient:
                    logger.info(f"Neuer Patient angelegt: {surname}, {name} -> PatientID {patient.get('PatientID')}, M1Ziffer {m1ziffer}")
                    return {
                        "PatientID": patient.get("PatientID"),
                        "M1Ziffer": m1ziffer
                    }

            logger.error(f"Fehler beim Anlegen des Patienten: {result.get('error')}")
            return None

        except Exception as e:
            logger.error(f"Fehler beim Anlegen des Patienten: {e}")
            return None

    def _generate_new_m1ziffer(self) -> str:
        """
        Generiert eine neue M1Ziffer.

        Sucht die hoechste M1Ziffer in SQLHK und inkrementiert um 1.

        Returns:
            Neue 7-stellige M1Ziffer
        """
        try:
            query = "SELECT MAX(CAST(M1Ziffer AS INT)) as MaxM1 FROM [SQLHK].[dbo].[Patient] WHERE ISNUMERIC(M1Ziffer) = 1"
            result = self.mssql_client.execute_sql(query, "SQLHK")

            if result.get("success") and result.get("rows"):
                max_m1 = result["rows"][0].get("MaxM1") or 1000000
                new_m1 = int(max_m1) + 1
                return str(new_m1)

            # Fallback
            return str(int(datetime.now().strftime("%Y%m%d")[-7:]))

        except Exception as e:
            logger.error(f"Fehler beim Generieren der M1Ziffer: {e}")
            return str(int(datetime.now().strftime("%Y%m%d")[-7:]))

    def resolve_appointments(self, appointments: List[Dict], progress_callback=None) -> Dict:
        """
        Loest alle Patienten fuer eine Liste von Terminen auf.

        Args:
            appointments: Liste von CallDoc-Terminen
            progress_callback: Optional callback(current, total, appointment, status)

        Returns:
            Dictionary mit:
            - resolved: Liste erfolgreich aufgeloester Termine (mit patient_id)
            - failed: Liste fehlgeschlagener Termine
            - stats: Statistik
        """
        self.stats = {
            "resolved_by_piz": 0,
            "resolved_by_kvnr": 0,
            "resolved_by_name_dob": 0,
            "created_new": 0,
            "failed": 0
        }

        resolved = []
        failed = []

        for i, appointment in enumerate(appointments):
            if progress_callback:
                surname = appointment.get("surname", "?")
                progress_callback(i + 1, len(appointments), f"{surname}", "Aufloesen...")

            result = self.resolve_patient(appointment)

            if result and result.get("patient_id"):
                # Fuege PatientID zum Termin hinzu
                appointment["resolved_patient_id"] = result["patient_id"]
                appointment["resolved_m1ziffer"] = result["m1ziffer"]
                appointment["resolution_method"] = result["method"]
                resolved.append(appointment)

                if progress_callback:
                    progress_callback(i + 1, len(appointments), f"{surname}", f"OK ({result['method']})")
            else:
                failed.append(appointment)

                if progress_callback:
                    progress_callback(i + 1, len(appointments), f"{surname}", "Fehlgeschlagen")

        return {
            "resolved": resolved,
            "failed": failed,
            "stats": self.stats.copy()
        }

    def get_stats(self) -> Dict:
        """Gibt die aktuelle Statistik zurueck."""
        return self.stats.copy()


# Convenience-Funktion
def resolve_patient_for_appointment(appointment: Dict) -> Optional[Dict]:
    """
    Convenience-Funktion zum Aufloesen eines einzelnen Termins.

    Args:
        appointment: CallDoc-Termin Dictionary

    Returns:
        Aufgeloester Termin mit patient_id oder None
    """
    resolver = PatientResolver()
    result = resolver.resolve_patient(appointment)

    if result and result.get("patient_id"):
        appointment["resolved_patient_id"] = result["patient_id"]
        appointment["resolved_m1ziffer"] = result["m1ziffer"]
        appointment["resolution_method"] = result["method"]
        return appointment

    return None


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Test mit einem Termin ohne PIZ aber mit KVNR
    test_appointment = {
        "id": 324460,
        "surname": "Märbert",
        "name": "Wittloff",
        "date_of_birth": "1948-01-29",
        "piz": None,
        "patient_insurance_number": "Z761613259"
    }

    resolver = PatientResolver()
    result = resolver.resolve_patient(test_appointment)

    print(f"\nErgebnis: {result}")
    print(f"Statistik: {resolver.get_stats()}")
