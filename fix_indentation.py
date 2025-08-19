#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zur Korrektur der Einrückung in der untersuchung_synchronizer.py Datei
"""

# Datei zeilenweise lesen
with open('untersuchung_synchronizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeilen durchgehen und die Einrückung korrigieren
new_lines = []
in_delete_method = False
for line in lines:
    # Wenn wir die Methode finden, setzen wir den Flag
    if "def _delete_all_untersuchungen_by_date" in line:
        in_delete_method = True
        # Korrigiere die Einrückung der Methodendefinition
        if line.startswith("                "):
            line = "    " + line.lstrip()
        new_lines.append(line)
    # Wenn wir in der Methode sind, korrigieren wir die Einrückung
    elif in_delete_method:
        # Wenn wir eine neue Methode finden, beenden wir die Korrektur
        if line.strip().startswith("def ") and not "delete_all_untersuchungen_by_date" in line:
            in_delete_method = False
            new_lines.append(line)
        else:
            # Korrigiere die Einrückung der Methodenzeilen
            if line.startswith("                "):
                line = "        " + line[16:]  # 16 Leerzeichen entfernen und 8 hinzufügen
            new_lines.append(line)
    # Wenn wir nicht in der Methode sind, fügen wir die Zeile unverändert hinzu
    else:
        new_lines.append(line)

# Datei zurückschreiben
with open('untersuchung_synchronizer.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Die Einrückung wurde korrigiert.")
