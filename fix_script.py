#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zur Korrektur der Datenbank in der _delete_all_untersuchungen_by_date-Methode
"""

import re

# Datei öffnen und Inhalt lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Suchen und Ersetzen
pattern = r'result = self\.mssql_client\.execute_sql\(query, "SuPDatabase"\)'
replacement = 'result = self.mssql_client.execute_sql(query, "SQLHK")'

# Ersetzen
new_content = re.sub(pattern, replacement, content)

# Zurückschreiben
with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Die Datei wurde erfolgreich aktualisiert.")
