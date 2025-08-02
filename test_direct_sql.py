#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Direkter Test der SQL-Abfrage für den Patienten mit M1Ziffer 1700038
"""

import logging
from mssql_api_client import MsSqlApiClient

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Hauptfunktion für den direkten SQL-Test"""
    client = MsSqlApiClient()
    
    # Test 1: Direkte Abfrage nach M1Ziffer 1700038
    query1 = "SELECT PatientID, Nachname, Vorname, M1Ziffer FROM [SQLHK].[dbo].[Patient] WHERE M1Ziffer = 1700038"
    logger.info(f"Test 1: {query1}")
    result1 = client.execute_sql(query1, "SuPDatabase")
    logger.info(f"Ergebnis 1: {result1}")
    
    # Test 2: Direkte Abfrage nach PatientID 12938
    query2 = "SELECT PatientID, Nachname, Vorname, M1Ziffer FROM [SQLHK].[dbo].[Patient] WHERE PatientID = 12938"
    logger.info(f"Test 2: {query2}")
    result2 = client.execute_sql(query2, "SuPDatabase")
    logger.info(f"Ergebnis 2: {result2}")
    
    # Test 3: Abfrage nach beliebigen Patienten
    query3 = "SELECT TOP 5 PatientID, Nachname, Vorname, M1Ziffer FROM [SQLHK].[dbo].[Patient] WHERE PatientID > 12910"
    logger.info(f"Test 3: {query3}")
    result3 = client.execute_sql(query3, "SuPDatabase")
    logger.info(f"Ergebnis 3: {result3}")
    
    # Test 4: Prüfen, ob die Tabelle überhaupt existiert
    query4 = "SELECT TOP 1 * FROM [SQLHK].[dbo].[INFORMATION_SCHEMA].[TABLES] WHERE TABLE_NAME = 'Patient'"
    logger.info(f"Test 4: {query4}")
    result4 = client.execute_sql(query4, "SuPDatabase")
    logger.info(f"Ergebnis 4: {result4}")

if __name__ == "__main__":
    main()
