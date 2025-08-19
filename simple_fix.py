#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Einfaches Skript zum Ändern der Datenbank in der execute_sql-Anweisung
"""

# Datei zeilenweise lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeilen durchgehen und die Datenbankangabe ändern
new_lines = []
for line in lines:
    if 'execute_sql(query, "SuPDatabase")' in line:
        # Ersetze SuPDatabase durch SQLHK
        line = line.replace('execute_sql(query, "SuPDatabase")', 'execute_sql(query, "SQLHK")')
    new_lines.append(line)

# Datei zurückschreiben
with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Die Datenbankangabe wurde erfolgreich von SuPDatabase auf SQLHK geändert.")
