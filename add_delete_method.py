#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zum Hinzufügen der _delete_all_untersuchungen_by_date-Methode und zum Anpassen der synchronize_appointments-Methode
"""

import re

# Methode aus der Datei lesen
with open('delete_method_only.py', 'r', encoding='utf-8') as f:
    delete_method = f.read()

# Hauptdatei lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Finde die Position, an der die Methode eingefügt werden soll (vor synchronize_appointments)
sync_method_pattern = r'def synchronize_appointments\(self, appointments: List\[Dict\[str, Any\]\], untersuchungen: List\[Dict\[str, Any\]\]\) -> Dict\[str, Any\]:'
match = re.search(sync_method_pattern, content)

if match:
    # Füge die Methode vor synchronize_appointments ein
    insert_pos = match.start()
    new_content = content[:insert_pos] + delete_method + "\n\n    " + content[insert_pos:]
    
    # Finde die Stelle, an der die Löschfunktion aufgerufen werden soll
    # Wir suchen nach der Stelle, wo date_str extrahiert wird und fügen den Aufruf danach ein
    date_extraction_pattern = r'date_str = None.*?except Exception as e:.*?logger\.error\(f"Fehler beim Extrahieren des Datums: {str\(e\)}"\)'
    date_match = re.search(date_extraction_pattern, new_content, re.DOTALL)
    
    if date_match:
        # Finde die Position nach dem date_extraction_pattern
        insert_call_pos = date_match.end()
        
        # Füge den Aufruf der Löschfunktion ein
        delete_call = """
        
        # Lösche ALLE Untersuchungen des Tages, bevor wir mit der Synchronisierung beginnen
        deleted_count = 0
        if date_str:
            deleted_count = self._delete_all_untersuchungen_by_date(date_str)
            self.stats["deleted"] = deleted_count
            logger.info(f"Alle Untersuchungen für {date_str} wurden gelöscht. Fahre mit der Synchronisierung fort.")
        """
        
        # Finde die Stelle, wo "deleted_count = self._delete_obsolete_untersuchungen" steht
        obsolete_pattern = r'deleted_count = 0.*?if date_str:.*?deleted_count = self\._delete_obsolete_untersuchungen'
        obsolete_match = re.search(obsolete_pattern, new_content, re.DOTALL)
        
        if obsolete_match:
            # Ersetze den alten Code durch unseren neuen Code
            new_content = new_content[:obsolete_match.start()] + delete_call + "\n        # Lösche obsolete Untersuchungen, wenn ein Datum gefunden wurde\n        if date_str:" + new_content[obsolete_match.end():]
        else:
            # Wenn wir den alten Code nicht finden, fügen wir unseren Code nach der Datumsextraktion ein
            new_content = new_content[:insert_call_pos] + delete_call + new_content[insert_call_pos:]
    
    # Schreibe die geänderte Datei zurück
    with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Die _delete_all_untersuchungen_by_date-Methode wurde hinzugefügt und die synchronize_appointments-Methode wurde angepasst.")
else:
    print("Die synchronize_appointments-Methode wurde nicht gefunden.")
