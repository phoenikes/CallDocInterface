#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zum Einfügen der _delete_all_untersuchungen_by_date-Methode und zum Anpassen der synchronize_appointments-Methode
"""

import re

# Datei lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Methode aus der Datei lesen
with open('correct_method.py', 'r', encoding='utf-8') as f:
    delete_method = f.read()

# Finde die Position, an der die Methode eingefügt werden soll (vor _delete_untersuchung)
delete_untersuchung_pattern = r'def _delete_untersuchung\(self, untersuchung: Dict\[str, Any\]\) -> bool:'
match = re.search(delete_untersuchung_pattern, content)

if match:
    # Füge die Methode vor _delete_untersuchung ein
    insert_pos = match.start()
    new_content = content[:insert_pos] + delete_method + "\n\n    " + content[insert_pos:]
    
    # Finde die Stelle in synchronize_appointments, wo wir den Aufruf einfügen wollen
    # Wir suchen nach der Stelle, wo date_str extrahiert wird
    date_extraction_pattern = r'date_str = None.*?if appointments and len\(appointments\) > 0:.*?scheduled_for = appointments\[0\]\.get\("scheduled_for_datetime"\).*?if scheduled_for:.*?try:.*?date_obj = datetime\.fromisoformat\(scheduled_for\.replace\("Z", "\+00:00"\)\).*?date_str = date_obj\.strftime\("%Y-%m-%d"\).*?except Exception as e:.*?logger\.error\(f"Fehler beim Extrahieren des Datums: {str\(e\)}"\)'
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
        
        # Ersetze die alte deleted_count-Zuweisung
        obsolete_pattern = r'# Lösche obsolete Untersuchungen, wenn ein Datum gefunden wurde\s+deleted_count = 0\s+if date_str:\s+deleted_count = self\._delete_obsolete_untersuchungen\(active_appointments, untersuchungen, date_str\)\s+self\.stats\["deleted"\] = deleted_count'
        obsolete_match = re.search(obsolete_pattern, new_content, re.DOTALL)
        
        if obsolete_match:
            # Ersetze den alten Code durch unseren neuen Code
            new_content = new_content[:obsolete_match.start()] + delete_call + new_content[obsolete_match.end():]
        else:
            # Wenn wir den alten Code nicht finden, fügen wir unseren Code nach der Datumsextraktion ein
            new_content = new_content[:insert_call_pos] + delete_call + new_content[insert_call_pos:]
    
    # Schreibe die geänderte Datei zurück
    with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Die _delete_all_untersuchungen_by_date-Methode wurde hinzugefügt und die synchronize_appointments-Methode wurde angepasst.")
else:
    print("Die _delete_untersuchung-Methode wurde nicht gefunden.")
