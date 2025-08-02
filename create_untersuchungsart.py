"""
Skript zum Erstellen einer Untersuchungsart für Herzkatheteruntersuchungen.

Dieses Skript erstellt eine neue Untersuchungsart in der SQLHK-Datenbank
mit der ExterneID 24, die dem CallDoc-Termintyp für Herzkatheteruntersuchungen entspricht.

Autor: Markus
Datum: 02.08.2025
"""

import logging
from mssql_api_client import MsSqlApiClient

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_untersuchungsart():
    """
    Erstellt eine neue Untersuchungsart für Herzkatheteruntersuchungen.
    """
    logger.info("Erstelle neue Untersuchungsart für Herzkatheteruntersuchungen (ExterneID: 24)")
    
    # MsSqlApiClient initialisieren
    mssql_client = MsSqlApiClient()
    
    # Prüfen, ob die Untersuchungsart bereits existiert
    query = """
        SELECT * FROM Untersuchungart 
        WHERE ExterneID = '24'
    """
    result = mssql_client.execute_sql(query, "SQLHK")
    
    if result.get("success", False) and "results" in result and len(result["results"]) > 0:
        logger.info("Untersuchungsart mit ExterneID 24 existiert bereits")
        return
    
    # Neue Untersuchungsart erstellen
    insert_query = """
        INSERT INTO Untersuchungart (UntersuchungartName, ExterneID)
        VALUES ('Herzkatheteruntersuchung', '24')
    """
    
    result = mssql_client.execute_sql(insert_query, "SQLHK")
    
    if result.get("success", False):
        logger.info("Untersuchungsart erfolgreich erstellt")
    else:
        logger.error(f"Fehler beim Erstellen der Untersuchungsart: {result.get('error', 'Unbekannter Fehler')}")
        
        # Alternative Methode versuchen
        logger.info("Versuche alternative Methode mit upsert_data")
        result = mssql_client.upsert_data(
            table="Untersuchungart",
            update_fields={
                "UntersuchungartName": "Herzkatheteruntersuchung",
                "ExterneID": "24"
            },
            search_fields={},
            key_fields=["UntersuchungartID"],
            database="SQLHK",
            operation="insert"
        )
        
        if result.get("success", False):
            logger.info("Untersuchungsart erfolgreich erstellt (alternative Methode)")
        else:
            logger.error(f"Fehler beim Erstellen der Untersuchungsart (alternative Methode): {result.get('error', 'Unbekannter Fehler')}")

if __name__ == "__main__":
    create_untersuchungsart()
