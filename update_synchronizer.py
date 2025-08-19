#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zum Aktualisieren der untersuchung_synchronizer.py Datei
"""

import re

# Datei öffnen und Inhalt lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Import-Anweisung hinzufügen
import_statement = 'from delete_untersuchungen import delete_all_untersuchungen_by_date'

# Prüfen, ob der Import bereits vorhanden ist
if import_statement not in content:
    # Finde die letzte Import-Anweisung
    import_pattern = r'import.*$'
    matches = list(re.finditer(import_pattern, content, re.MULTILINE))
    if matches:
        last_import = matches[-1]
        # Füge den neuen Import nach dem letzten Import hinzu
        content = content[:last_import.end()] + '\n' + import_statement + content[last_import.end():]
    else:
        # Wenn keine Imports gefunden wurden, füge am Anfang der Datei hinzu
        content = import_statement + '\n' + content

# Finde die synchronize_appointments-Methode
sync_method_pattern = r'def synchronize_appointments.*?deleted_count = 0.*?if date_str:.*?deleted_count = self\._delete_all_untersuchungen_by_date\(date_str\)'
sync_method_replacement = '''def synchronize_appointments(self, appointments: List[Dict[str, Any]], untersuchungen: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronisiert CallDoc-Termine mit SQLHK-Untersuchungen.
        
        Diese Methode vergleicht die Termine aus CallDoc mit den Untersuchungen aus SQLHK
        und führt die notwendigen Operationen durch, um beide Systeme zu synchronisieren.
        
        Args:
            appointments: Liste der CallDoc-Termine
            untersuchungen: Liste der SQLHK-Untersuchungen
            
        Returns:
            Statistik der Synchronisierung
        """
        # Statistik zurücksetzen
        self.stats = {
            "total_calldoc": len(appointments),
            "total_sqlhk": len(untersuchungen),
            "to_insert": 0,
            "to_update": 0,
            "to_delete": 0,
            "inserted": 0,
            "updated": 0,
            "deleted": 0,
            "errors": 0,
            "success": 0
        }
        
        logger.info(f"Starte Synchronisierung: {len(appointments)} CallDoc-Termine, {len(untersuchungen)} SQLHK-Untersuchungen")
        
        # Aktive Termine identifizieren (nicht storniert)
        active_appointments = [app for app in appointments if app.get("status") != "canceled"]
        logger.info(f"{len(active_appointments)} aktive Termine gefunden")
        
        # Wir extrahieren das Datum aus dem ersten Termin, falls vorhanden
        date_str = None
        if appointments and len(appointments) > 0:
            scheduled_for = appointments[0].get("scheduled_for_datetime")
            if scheduled_for:
                try:
                    date_obj = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
                    date_str = date_obj.strftime("%d.%m.%Y")  # Format DD.MM.YYYY für die Datenbank
                except Exception as e:
                    logger.error(f"Fehler beim Extrahieren des Datums: {str(e)}")
        
        # Lösche ALLE Untersuchungen des Tages, bevor wir mit der Synchronisierung beginnen
        deleted_count = 0
        if date_str:
            deleted_count = delete_all_untersuchungen_by_date(self.mssql_client, date_str)'''

# Ersetzen mit regulärem Ausdruck im DOTALL-Modus (re.DOTALL oder re.S)
new_content = re.sub(sync_method_pattern, sync_method_replacement, content, flags=re.DOTALL)

# Entferne die alte _delete_all_untersuchungen_by_date-Methode
old_method_pattern = r'def _delete_all_untersuchungen_by_date.*?return 0\s+'
new_content = re.sub(old_method_pattern, '', new_content, flags=re.DOTALL)

# Zurückschreiben
with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Die untersuchung_synchronizer.py Datei wurde erfolgreich aktualisiert.")
