#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Korrigierte _delete_all_untersuchungen_by_date Methode
"""

def _delete_all_untersuchungen_by_date(self, date_str: str) -> int:
    """
    Löscht alle Untersuchungen eines bestimmten Datums aus der SQLHK-Datenbank.
    
    Diese Methode wird vor der eigentlichen Synchronisierung aufgerufen, um sicherzustellen,
    dass keine veralteten oder inkonsistenten Daten in der Datenbank verbleiben.
    
    Args:
        date_str: Datum im Format YYYY-MM-DD oder DD.MM.YYYY
        
    Returns:
        Anzahl der gelöschten Untersuchungen
    """
    try:
        # Prüfen, ob das Datum im Format DD.MM.YYYY vorliegt und ggf. konvertieren
        if '.' in date_str:
            # Konvertiere DD.MM.YYYY zu YYYY-MM-DD für SQL-Abfrage
            date_parts = date_str.split('.')
            if len(date_parts) == 3:
                date_str = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        
        logger.info(f"Lösche alle Untersuchungen für Datum: {date_str}")
        
        # SQL-Abfrage, um alle Untersuchungen für das angegebene Datum zu löschen
        query = f"""
            DELETE FROM [SQLHK].[dbo].[Untersuchung]
            WHERE Datum = '{date_str}'
        """
        
        # Wichtig: Hier wird die SQLHK-Datenbank verwendet, nicht SuPDatabase
        result = self.mssql_client.execute_sql(query, "SQLHK")
        
        if result.get("success", False):
            # Die Anzahl der gelöschten Zeilen ist in result.get("rowcount") enthalten
            deleted_count = result.get("rowcount", 0)
            logger.info(f"{deleted_count} Untersuchungen für Datum {date_str} erfolgreich gelöscht")
            return deleted_count
        else:
            error_msg = result.get('error', 'Unbekannter Fehler')
            logger.error(f"Fehler beim Löschen der Untersuchungen für Datum {date_str}: {error_msg}")
            return 0
            
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Untersuchungen für Datum {date_str}: {str(e)}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return 0
