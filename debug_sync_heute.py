"""
Debug-Script für die Synchronisation des heutigen Tages
"""

import sys
import json
import logging
from datetime import datetime
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from untersuchung_synchronizer import UntersuchungSynchronizer
from patient_synchronizer import PatientSynchronizer

# Detailliertes Logging einrichten
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'debug_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_sync_today():
    """Testet die Synchronisation für den heutigen Tag mit erweiterten Debug-Ausgaben"""
    
    # Datum für heute
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"=== Starte Debug-Synchronisation für heute: {today} ===")
    
    try:
        # 1. Initialisiere Clients
        logger.info("1. Initialisiere API-Clients...")
        calldoc_client = CallDocInterface(from_date=today, to_date=today)
        mssql_client = MsSqlApiClient()
        
        # 2. Test: CallDoc-API erreichbar?
        logger.info("2. Teste CallDoc-API Verbindung...")
        try:
            test_appointments = calldoc_client.appointment_search(appointment_type_id=24)
            logger.info(f"   ✓ CallDoc-API erreichbar. {len(test_appointments.get('data', []))} Termine gefunden.")
            
            # Debug: Ersten Termin anzeigen
            if test_appointments.get('data'):
                first_appt = test_appointments['data'][0]
                logger.debug(f"   Beispiel-Termin: ID={first_appt.get('id')}, Status={first_appt.get('status')}")
        except Exception as e:
            logger.error(f"   ✗ CallDoc-API Fehler: {str(e)}")
            return
        
        # 3. Test: MSSQL-API erreichbar?
        logger.info("3. Teste MSSQL-API Verbindung...")
        try:
            test_result = mssql_client.execute_sql("SELECT COUNT(*) as count FROM Untersuchung", database="SQLHK")
            logger.info(f"   ✓ MSSQL-API erreichbar. Response: {test_result.get('success', False)}")
        except Exception as e:
            logger.error(f"   ✗ MSSQL-API Fehler: {str(e)}")
            return
        
        # 4. Initialisiere Synchronizer
        logger.info("4. Initialisiere Untersuchung-Synchronizer...")
        untersuchung_sync = UntersuchungSynchronizer(
            calldoc_interface=calldoc_client,
            mssql_client=mssql_client
        )
        
        # 5. Hole CallDoc-Termine
        logger.info("5. Hole CallDoc-Termine...")
        appointments = test_appointments.get('data', [])
        logger.info(f"   {len(appointments)} Termine gefunden")
        
        # 6. Hole SQLHK-Untersuchungen
        logger.info("6. Hole SQLHK-Untersuchungen...")
        german_date = datetime.strptime(today, "%Y-%m-%d").strftime("%d.%m.%Y")
        sqlhk_result = mssql_client.get_untersuchungen_by_date(today)
        
        if sqlhk_result.get('success'):
            untersuchungen = sqlhk_result.get('results', [])
            logger.info(f"   {len(untersuchungen)} Untersuchungen in SQLHK gefunden")
        else:
            logger.error(f"   Fehler beim Abrufen der SQLHK-Untersuchungen: {sqlhk_result.get('error')}")
            untersuchungen = []
        
        # 7. Teste einzelnen INSERT
        if appointments and len(appointments) > 0:
            logger.info("7. Teste INSERT einer einzelnen Untersuchung...")
            test_appointment = appointments[0]
            
            # Mappe den Termin
            logger.info("   Mappe Termin auf Untersuchung...")
            mapped_data = untersuchung_sync.map_appointment_to_untersuchung(test_appointment)
            logger.debug(f"   Gemappte Daten: {json.dumps(mapped_data, indent=2, default=str)}")
            
            # Versuche INSERT
            logger.info("   Führe INSERT aus...")
            insert_result = mssql_client.insert_untersuchung(mapped_data)
            
            if insert_result.get('success'):
                logger.info(f"   ✓ INSERT erfolgreich: {insert_result}")
            else:
                logger.error(f"   ✗ INSERT fehlgeschlagen: {insert_result}")
                
                # Detaillierte Fehleranalyse
                error_msg = insert_result.get('error', 'Unbekannter Fehler')
                logger.error(f"   Fehlerdetails: {error_msg}")
                
                # Prüfe spezifische Felder
                logger.info("   Prüfe kritische Felder:")
                logger.info(f"     - PatientID: {mapped_data.get('PatientID')}")
                logger.info(f"     - UntersuchungartID: {mapped_data.get('UntersuchungartID')}")
                logger.info(f"     - UntersucherAbrechnungID: {mapped_data.get('UntersucherAbrechnungID')}")
                logger.info(f"     - HerzkatheterID: {mapped_data.get('HerzkatheterID')}")
                logger.info(f"     - Datum: {mapped_data.get('Datum')}")
                
        else:
            logger.warning("Keine Termine zum Testen gefunden")
        
    except Exception as e:
        logger.exception(f"Unerwarteter Fehler: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_today()
    print("\n=== Debug-Test abgeschlossen. Details in der Log-Datei. ===")