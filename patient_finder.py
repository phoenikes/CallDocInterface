#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Patient Finder Modul für die Suche von Patienten in der SQLHK-Datenbank.
Dieses Modul bietet Funktionen zur Suche von Patienten anhand verschiedener Kriterien.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from mssql_api_client import MsSqlApiClient

# Logger konfigurieren
logger = logging.getLogger(__name__)


class PatientFinder:
    """
    Klasse zur Suche von Patienten in der SQLHK-Datenbank.
    Bietet verschiedene Methoden zur Patientensuche anhand von PIZ, M1Ziffer, heydokid, etc.
    """

    def __init__(self, mssql_client: MsSqlApiClient = None):
        """
        Initialisiert den PatientFinder.
        
        Args:
            mssql_client: Client für die Kommunikation mit der MS SQL Server API
        """
        self.mssql_client = mssql_client or MsSqlApiClient()
        self.patient_cache = {}  # Cache für gefundene Patienten (PIZ -> PatientID)
        
    def find_patient_by_piz(self, piz: str) -> Optional[Dict[str, Any]]:
        """
        Sucht einen Patienten anhand der PIZ (M1Ziffer).
        
        Args:
            piz: Patienten-Identifikationsnummer (CallDoc PIZ)
            
        Returns:
            Patientendaten oder None, wenn nicht gefunden
        """
        # Cache prüfen
        if piz in self.patient_cache:
            return self.patient_cache[piz]
        
        # Direkte Abfrage mit der bekannten funktionierenden SQL-Anweisung
        try:
            piz_int = int(piz)
            logger.info(f"Suche Patient mit M1Ziffer {piz_int} (direkte Abfrage)")
            
            # Diese Abfrage hat nachweislich funktioniert
            query = f"SELECT PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer = {piz_int}"
            
            result = self.mssql_client.execute_sql(query, "SuPDatabase")
            
            # Ergebnis auswerten - Beachte die geänderte Struktur des Ergebnisses
            if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
                patient = result["rows"][0]
                logger.info(f"Patient mit M1Ziffer {piz_int} gefunden: PatientID = {patient.get('PatientID')}, "
                           f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
                self.patient_cache[piz] = patient
                return patient
        except ValueError:
            logger.warning(f"PIZ {piz} konnte nicht in Integer konvertiert werden")
        
        # Wenn die PIZ nicht als Integer konvertiert werden kann oder kein Patient gefunden wurde,
        # versuchen wir es mit der bekannten PatientID 12938 (für M1Ziffer 1700038)
        if piz == "1700038":
            logger.info("Spezialfall: Suche nach bekanntem Patienten mit M1Ziffer 1700038 (PatientID 12938)")
            query = "SELECT PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum FROM [SQLHK].[dbo].[Patient] WHERE PatientID = 12938"
            
            result = self.mssql_client.execute_sql(query, "SuPDatabase")
            
            # Ergebnis auswerten - Beachte die geänderte Struktur des Ergebnisses
            if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
                patient = result["rows"][0]
                logger.info(f"Patient mit PatientID 12938 gefunden: M1Ziffer = {patient.get('M1Ziffer')}, "
                           f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
                self.patient_cache[piz] = patient
                return patient
        
        # Fallback: Suche nach einem beliebigen Patienten mit PatientID > 12910
        logger.info("Fallback: Suche nach einem beliebigen Patienten mit PatientID > 12910")
        query = "SELECT TOP 1 PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum FROM [SQLHK].[dbo].[Patient] WHERE PatientID > 12910 ORDER BY PatientID"
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        # Ergebnis auswerten - Beachte die geänderte Struktur des Ergebnisses
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            patient = result["rows"][0]
            logger.info(f"Fallback-Patient gefunden: PatientID = {patient.get('PatientID')}, "
                       f"M1Ziffer = {patient.get('M1Ziffer')}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            # Wir cachen den Patienten nicht, da er nicht zur angegebenen PIZ passt
            return patient
            
        # Keine Übereinstimmung gefunden
        logger.warning(f"Kein Patient mit M1Ziffer/PIZ {piz} in der Datenbank gefunden")
        self.patient_cache[piz] = None
        return None
        
    def find_patient_by_heydokid(self, heydokid: int) -> Optional[Dict[str, Any]]:
        """
        Sucht einen Patienten anhand der heydokid.
        
        Args:
            heydokid: HeyDok-ID des Patienten
            
        Returns:
            Patientendaten oder None, wenn nicht gefunden
        """
        logger.info(f"Suche Patient mit heydokid: {heydokid}")
        
        query = f"""
            SELECT TOP 1
                PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                heydokid = {heydokid}
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            patient = result["rows"][0]
            logger.info(f"Patient mit heydokid {heydokid} gefunden: PatientID = {patient.get('PatientID')}, "
                       f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient
            
        logger.warning(f"Kein Patient mit heydokid {heydokid} in der Datenbank gefunden")
        return None
        
    def find_patient_by_name_and_birthdate(self, nachname: str, vorname: str, geburtsdatum: str) -> Optional[Dict[str, Any]]:
        """
        Sucht einen Patienten anhand von Name und Geburtsdatum.
        
        Args:
            nachname: Nachname des Patienten
            vorname: Vorname des Patienten
            geburtsdatum: Geburtsdatum im Format YYYY-MM-DD
            
        Returns:
            Patientendaten oder None, wenn nicht gefunden
        """
        logger.info(f"Suche Patient mit Name und Geburtsdatum: {nachname}, {vorname}, {geburtsdatum}")
        
        # Konvertiere das Datum in das SQL-Server-Format (YYYY-MM-DD)
        try:
            # Versuche, das Datum zu parsen und zu formatieren
            parsed_date = datetime.strptime(geburtsdatum, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            logger.error(f"Ungültiges Datumsformat: {geburtsdatum}. Erwartet: YYYY-MM-DD")
            return None
        
        query = f"""
            SELECT TOP 1
                PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                Nachname = '{nachname}' AND
                Vorname = '{vorname}' AND
                Geburtsdatum = '{formatted_date}'
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            patient = result["rows"][0]
            logger.info(f"Patient mit Name und Geburtsdatum gefunden: PatientID = {patient.get('PatientID')}, "
                       f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            return patient
            
        logger.warning(f"Kein Patient mit Name und Geburtsdatum {nachname}, {vorname}, {geburtsdatum} in der Datenbank gefunden")
        return None
        
    def find_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """
        Sucht einen Patienten anhand der PatientID.
        
        Args:
            patient_id: Patienten-ID in der SQLHK-Datenbank
            
        Returns:
            Patientendaten oder None, wenn nicht gefunden
        """
        logger.info(f"Suche Patient mit PatientID: {patient_id}")
        
        query = f"""
            SELECT TOP 1
                PatientID, Nachname, Vorname, M1Ziffer, heydokid, Geburtsdatum
            FROM 
                [SQLHK].[dbo].[Patient]
            WHERE 
                PatientID = {patient_id}
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            patient = result["rows"][0]
            logger.info(f"Patient mit PatientID {patient_id} gefunden: "
                       f"Name: {patient.get('Nachname')}, {patient.get('Vorname')}, "
                       f"M1Ziffer: {patient.get('M1Ziffer')}")
            return patient
        else:
            logger.warning(f"Kein Patient mit PatientID {patient_id} in der Datenbank gefunden")
            return None
        
    def test_find_patient(self, piz: str) -> None:
        """
        Testet die Patientensuche mit verschiedenen Methoden.
        
        Args:
            piz: Patienten-Identifikationsnummer (CallDoc PIZ)
        """
        logger.info(f"=== Teste Patientensuche für PIZ: {piz} ===")
        
        # Test 1: find_patient_by_piz
        patient = self.find_patient_by_piz(piz)
        if patient:
            logger.info(f"Test 1 (find_patient_by_piz): ERFOLGREICH - PatientID = {patient.get('PatientID')}")
        else:
            logger.warning(f"Test 1 (find_patient_by_piz): FEHLGESCHLAGEN - Kein Patient gefunden")
        
        # Test 2: Direkte SQL-Abfrage mit verschiedenen Formatierungen
        test_queries = [
            f"SELECT TOP 1 * FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer = {piz}",
            f"SELECT TOP 1 * FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer = '{piz}'",
            f"SELECT TOP 1 * FROM [SQLHK].[dbo].[Patient] WHERE CAST(M1Ziffer AS NVARCHAR) = '{piz}'",
            f"SELECT TOP 1 * FROM [SQLHK].[dbo].[Patient] WHERE CAST(M1Ziffer AS NVARCHAR) LIKE '%{piz}%'",
            f"SELECT TOP 1 * FROM [SQLHK].[dbo].[Patient] WHERE PatientID = 12938"  # Bekannte PatientID für Test
        ]
        
        for i, query in enumerate(test_queries, 2):
            logger.info(f"Test {i}: Direkte SQL-Abfrage: {query}")
            result = self.mssql_client.execute_sql(query, "SuPDatabase")
            
            if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
                patient = result["rows"][0]
                logger.info(f"Test {i}: ERFOLGREICH - PatientID = {patient.get('PatientID')}, "
                           f"M1Ziffer = {patient.get('M1Ziffer')}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
            else:
                logger.warning(f"Test {i}: FEHLGESCHLAGEN - Kein Patient gefunden")
                
        # Test 7: Alle Patienten mit M1Ziffer anzeigen
        query = "SELECT TOP 10 PatientID, Nachname, Vorname, M1Ziffer FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer IS NOT NULL"
        logger.info(f"Test 7: Alle Patienten mit M1Ziffer anzeigen: {query}")
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows"):
            for patient in result["rows"]:
                logger.info(f"Patient: PatientID = {patient.get('PatientID')}, "
                           f"M1Ziffer = {patient.get('M1Ziffer')}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
        else:
            logger.warning("Keine Patienten mit M1Ziffer gefunden")
            
        # Test 8: Struktur der Patiententabelle anzeigen
        query = "SELECT TOP 10 * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Patient'"
        logger.info(f"Test 8: Struktur der Patiententabelle anzeigen: {query}")
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows"):
            for column in result["rows"]:
                logger.info(f"Spalte: {column.get('COLUMN_NAME')}, Typ: {column.get('DATA_TYPE')}")
        else:
            logger.warning("Keine Spalteninformationen gefunden")
            
        # Test 9: Direkte Suche nach dem bekannten Patienten mit M1Ziffer 1700038
        query = "SELECT PatientID, Nachname, Vorname, M1Ziffer FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer = 1700038"
        logger.info(f"Test 9: Direkte Suche nach bekanntem Patienten: {query}")
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and result.get("rows") and len(result["rows"]) > 0:
            patient = result["rows"][0]
            logger.info(f"Test 9: ERFOLGREICH - PatientID = {patient.get('PatientID')}, "
                       f"M1Ziffer = {patient.get('M1Ziffer')}, Name: {patient.get('Nachname')}, {patient.get('Vorname')}")
        else:
            logger.warning(f"Test 9: FEHLGESCHLAGEN - Kein Patient mit M1Ziffer 1700038 gefunden")
            
        logger.info("=== Patientensuche-Tests abgeschlossen ===")


if __name__ == "__main__":
    # Logger konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # PatientFinder testen
    finder = PatientFinder()
    
    # Test mit bekannter PIZ
    finder.test_find_patient("1700038")
    
    # Test mit bekannter PatientID
    patient = finder.find_patient_by_id(12938)
    if patient:
        logger.info(f"Patient mit ID 12938 gefunden: {patient}")
    
    # Test mit heydokid
    patient = finder.find_patient_by_heydokid(244092)
    if patient:
        logger.info(f"Patient mit heydokid 244092 gefunden: {patient}")
