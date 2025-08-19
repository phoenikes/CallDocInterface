#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zum Ändern der Datenbankangabe von "SuPDatabase" zu "SQLHK" in der untersuchung_synchronizer.py
"""

# Datei zeilenweise lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeilen durchgehen und die Datenbankangabe ändern
new_lines = []
changes_made = 0
for line in lines:
    if 'execute_sql(query, "SuPDatabase")' in line:
        # Ersetze SuPDatabase durch SQLHK
        new_line = line.replace('execute_sql(query, "SuPDatabase")', 'execute_sql(query, "SQLHK")')
        new_lines.append(new_line)
        changes_made += 1
    else:
        new_lines.append(line)

# Datei zurückschreiben
with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Die Datenbankangabe wurde in {changes_made} Zeilen von SuPDatabase auf SQLHK geändert.")
