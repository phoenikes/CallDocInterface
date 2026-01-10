"""
KVDT Patient Enricher - Reichert Patientendaten aus .con Dateien an.

Nach einem erfolgreichen Sync werden die M1Ziffern der synchronisierten Patienten
verwendet, um zusaetzliche Daten aus den KVDT .con Dateien zu laden und in SQLHK
zu aktualisieren.

Angereicherte Felder:
- PLZ, Ort, Strasse (Adressdaten)
- Krankenkasse (Versicherungsname)
- Geschlecht (M/W -> 1/2)
- ggf. korrigierte Namen (Vor-/Nachname)

Autor: Claude Code
Version: 1.1
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# SKILLS_CENTRAL fuer KVDT-Parser (nur wenn nicht als EXE gepackt)
SKILLS_CENTRAL_PATH = r"C:\Users\administrator.PRAXIS\PycharmProjects\SKILLS_CENTRAL"
if os.path.exists(SKILLS_CENTRAL_PATH) and SKILLS_CENTRAL_PATH not in sys.path:
    sys.path.append(SKILLS_CENTRAL_PATH)

from mssql_api_client import MsSqlApiClient

# Flag ob KVDT-Modul verfuegbar ist
KVDT_AVAILABLE = False
KVDTADTParser = None

def _init_kvdt_module():
    """Versucht das KVDT-Modul zu laden."""
    global KVDT_AVAILABLE, KVDTADTParser
    try:
        from kvdt import KVDTADTParser as Parser
        KVDTADTParser = Parser
        KVDT_AVAILABLE = True
        return True
    except ImportError:
        KVDT_AVAILABLE = False
        return False

# Versuche KVDT beim Import zu laden
_init_kvdt_module()

logger = logging.getLogger(__name__)

# Standard-Pfad fuer .con Dateien
KVDT_BASE_PATH = r"M:\M1\PROJECT\KBV"


class KVDTEnricher:
    """
    Reichert Patientendaten in SQLHK mit Informationen aus KVDT .con Dateien an.
    """

    def __init__(self, kvdt_path: str = KVDT_BASE_PATH):
        """
        Initialisiert den KVDT-Enricher.

        Args:
            kvdt_path: Basispfad fuer die .con Dateien
        """
        self.kvdt_path = kvdt_path
        self.mssql_client = MsSqlApiClient()
        self.con_files = []
        self._load_con_files()

    def _load_con_files(self):
        """Laedt alle .con Dateien aus dem KVDT-Verzeichnis."""
        try:
            if not os.path.exists(self.kvdt_path):
                logger.warning(f"KVDT-Pfad nicht gefunden: {self.kvdt_path}")
                return

            for root, dirs, files in os.walk(self.kvdt_path):
                for f in files:
                    if f.endswith('.con'):
                        self.con_files.append(os.path.join(root, f))

            logger.info(f"{len(self.con_files)} .con Dateien gefunden")
        except Exception as e:
            logger.error(f"Fehler beim Laden der .con Dateien: {e}")

    def _convert_date_kvdt_to_sqlhk(self, kvdt_date: str) -> Optional[str]:
        """
        Konvertiert KVDT-Datum (JJJJMMTT) zu SQLHK-Format (TT.MM.JJJJ).

        Args:
            kvdt_date: Datum im Format JJJJMMTT (z.B. "19600725")

        Returns:
            Datum im Format TT.MM.JJJJ (z.B. "25.07.1960") oder None bei Fehler
        """
        if not kvdt_date or len(kvdt_date) != 8:
            return None

        try:
            # JJJJMMTT -> datetime -> TT.MM.JJJJ
            date_obj = datetime.strptime(kvdt_date, "%Y%m%d")
            return date_obj.strftime("%d.%m.%Y")
        except ValueError as e:
            logger.warning(f"Ungültiges KVDT-Datum: {kvdt_date} - {e}")
            return None

    def _convert_gender_kvdt_to_sqlhk(self, kvdt_gender: str) -> int:
        """
        Konvertiert KVDT-Geschlecht zu SQLHK-Format.

        Args:
            kvdt_gender: "M" oder "W"

        Returns:
            1 (maennlich), 2 (weiblich) oder 0 (unbekannt)
        """
        if not kvdt_gender:
            return 0

        gender_upper = kvdt_gender.upper().strip()
        if gender_upper in ["M", "MÄNNLICH", "MAENNLICH", "MALE"]:
            return 1
        elif gender_upper in ["W", "F", "WEIBLICH", "FEMALE"]:
            return 2
        return 0

    def find_patient_in_kvdt(self, m1ziffer: str) -> Optional[Dict]:
        """
        Sucht einen Patienten in den KVDT .con Dateien.

        Args:
            m1ziffer: Die M1Ziffer des Patienten

        Returns:
            Dictionary mit Patientendaten oder None wenn nicht gefunden
        """
        if not KVDT_AVAILABLE:
            logger.warning("KVDT-Modul nicht verfuegbar")
            return None

        if not self.con_files:
            logger.warning("Keine .con Dateien verfuegbar")
            return None

        try:
            parser = KVDTADTParser()

            result = parser.search_in_multiple_files(self.con_files, m1ziffer)
            if result:
                datei, patient = result
                logger.info(f"Patient {m1ziffer} gefunden in: {datei}")
                return {
                    "file": datei,
                    "patient_data": patient.patient_data,
                    "insurance_data": patient.insurance_data
                }

            return None

        except Exception as e:
            logger.error(f"Fehler bei KVDT-Suche fuer {m1ziffer}: {e}")
            return None

    def map_kvdt_to_sqlhk(self, kvdt_data: Dict) -> Dict:
        """
        Mappt KVDT-Daten auf SQLHK-Format.

        Args:
            kvdt_data: Dictionary mit patient_data und insurance_data

        Returns:
            Dictionary mit SQLHK-kompatiblen Feldern
        """
        patient_data = kvdt_data.get("patient_data", {})
        insurance_data = kvdt_data.get("insurance_data", {})

        sqlhk_data = {}

        # Adressdaten
        if patient_data.get("plz"):
            plz = patient_data["plz"]
            # PLZ muss numerisch sein
            if plz.isdigit():
                sqlhk_data["PLZ"] = int(plz)

        if patient_data.get("ort"):
            sqlhk_data["Stadt"] = patient_data["ort"]

        # Strasse mit Hausnummer kombinieren
        strasse = patient_data.get("strasse", "")
        hausnummer = patient_data.get("hausnummer", "")
        if strasse:
            if hausnummer:
                sqlhk_data["Strasse"] = f"{strasse} {hausnummer}"
            else:
                sqlhk_data["Strasse"] = strasse

        # Geschlecht
        if patient_data.get("geschlecht"):
            geschlecht = self._convert_gender_kvdt_to_sqlhk(patient_data["geschlecht"])
            if geschlecht > 0:  # Nur wenn bekannt
                sqlhk_data["Geschlecht"] = geschlecht

        # Krankenkasse - direkt die 9-stellige Kostentraegerkennung (Feld 4111)
        kassen_ik = insurance_data.get("kassen_ik")
        if kassen_ik and kassen_ik.isdigit():
            sqlhk_data["Krankenkasse"] = int(kassen_ik)  # 9-stellige IK-Nummer als Integer

        # Krankenkassestatus - Gebührenordnung (Feld 4121: 1=GKV, 2=PKV, etc.)
        gebuehrenordnung = insurance_data.get("gebuehrenordnung")
        if gebuehrenordnung and gebuehrenordnung.isdigit():
            sqlhk_data["Krankenkassestatus"] = int(gebuehrenordnung)

        return sqlhk_data

    def update_patient_in_sqlhk(self, m1ziffer: str, update_data: Dict) -> bool:
        """
        Aktualisiert einen Patienten in SQLHK mit den angereicherten Daten.

        Args:
            m1ziffer: Die M1Ziffer des Patienten
            update_data: Die zu aktualisierenden Felder

        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not update_data:
            logger.warning(f"Keine Daten zum Aktualisieren fuer {m1ziffer}")
            return False

        try:
            # Baue UPDATE Statement
            # Nur bekannte SQLHK-Felder verwenden
            valid_fields = ["PLZ", "Stadt", "Strasse", "Geschlecht", "Krankenkasse", "Krankenkassestatus"]
            set_clauses = []

            for field in valid_fields:
                if field in update_data:
                    value = update_data[field]
                    if isinstance(value, str):
                        # Escape single quotes
                        value = value.replace("'", "''")
                        set_clauses.append(f"{field} = '{value}'")
                    elif isinstance(value, int):
                        set_clauses.append(f"{field} = {value}")

            if not set_clauses:
                logger.info(f"Keine gueltigen Felder zum Aktualisieren fuer {m1ziffer}")
                return True

            set_clause = ", ".join(set_clauses)
            query = f"UPDATE Patient SET {set_clause} WHERE M1Ziffer = '{m1ziffer}'"

            result = self.mssql_client.execute_sql(query, "SQLHK")

            # "does not return rows" ist normal bei UPDATE
            if result.get("success") or "does not return rows" in str(result.get("error", "")):
                logger.info(f"Patient {m1ziffer} erfolgreich angereichert: {list(update_data.keys())}")
                return True
            else:
                logger.error(f"Fehler beim Update von {m1ziffer}: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Update von Patient {m1ziffer}: {e}")
            return False

    def enrich_patient(self, m1ziffer: str) -> Dict:
        """
        Reichert einen einzelnen Patienten an.

        Args:
            m1ziffer: Die M1Ziffer des Patienten

        Returns:
            Dictionary mit Status und Details
        """
        result = {
            "m1ziffer": m1ziffer,
            "found": False,
            "enriched": False,
            "fields": [],
            "error": None
        }

        # In KVDT suchen
        kvdt_data = self.find_patient_in_kvdt(m1ziffer)
        if not kvdt_data:
            result["error"] = "Nicht in KVDT gefunden"
            return result

        result["found"] = True
        result["kvdt_file"] = kvdt_data.get("file")

        # Auf SQLHK-Format mappen
        sqlhk_data = self.map_kvdt_to_sqlhk(kvdt_data)
        if not sqlhk_data:
            result["error"] = "Keine anreicherbaren Felder"
            return result

        result["fields"] = list(sqlhk_data.keys())

        # In SQLHK aktualisieren
        if self.update_patient_in_sqlhk(m1ziffer, sqlhk_data):
            result["enriched"] = True
        else:
            result["error"] = "Update fehlgeschlagen"

        return result

    def enrich_patients(self, m1ziffern: List[str], progress_callback=None) -> Dict:
        """
        Reichert mehrere Patienten an.

        Args:
            m1ziffern: Liste der M1Ziffern
            progress_callback: Optional callback(current, total, m1ziffer, status)

        Returns:
            Dictionary mit Gesamtstatistik
        """
        stats = {
            "total": len(m1ziffern),
            "found": 0,
            "enriched": 0,
            "failed": 0,
            "not_found": 0,
            "details": []
        }

        for i, m1ziffer in enumerate(m1ziffern):
            if progress_callback:
                progress_callback(i + 1, len(m1ziffern), m1ziffer, "Suche...")

            result = self.enrich_patient(m1ziffer)
            stats["details"].append(result)

            if result["found"]:
                stats["found"] += 1
                if result["enriched"]:
                    stats["enriched"] += 1
                    if progress_callback:
                        progress_callback(i + 1, len(m1ziffern), m1ziffer, "Angereichert")
                else:
                    stats["failed"] += 1
                    if progress_callback:
                        progress_callback(i + 1, len(m1ziffern), m1ziffer, "Fehler")
            else:
                stats["not_found"] += 1
                if progress_callback:
                    progress_callback(i + 1, len(m1ziffern), m1ziffer, "Nicht gefunden")

        return stats


def enrich_synced_patients(m1ziffern: List[str], progress_callback=None) -> Dict:
    """
    Convenience-Funktion zum Anreichern von synchronisierten Patienten.

    Args:
        m1ziffern: Liste der M1Ziffern der synchronisierten Patienten
        progress_callback: Optional callback fuer Fortschrittsanzeige

    Returns:
        Statistik-Dictionary
    """
    enricher = KVDTEnricher()
    return enricher.enrich_patients(m1ziffern, progress_callback)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    # Test mit einem bekannten Patienten
    enricher = KVDTEnricher()
    result = enricher.enrich_patient("1685384")
    print(f"Ergebnis: {result}")
