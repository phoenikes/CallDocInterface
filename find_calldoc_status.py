#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript zum Extrahieren aller Status-Werte aus den calldoc_termine-Dateien.
"""

import json
import os
import glob
from collections import Counter
from datetime import datetime
from typing import Dict, List, Set

def extract_status_values(file_path: str) -> List[str]:
    """
    Extrahiert alle Status-Werte aus einer JSON-Datei.
    
    Args:
        file_path: Pfad zur JSON-Datei
        
    Returns:
        Liste der gefundenen Status-Werte
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        status_values = []
        for appointment in data:
            status = appointment.get('status')
            if status:
                status_values.append(status)
        
        return status_values
    except Exception as e:
        print(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return []

def main():
    # Alle calldoc_termine-Dateien finden
    files = glob.glob('calldoc_termine*.json')
    
    all_status_values = []
    status_by_file = {}
    
    # Status-Werte aus allen Dateien extrahieren
    for file in files:
        status_values = extract_status_values(file)
        all_status_values.extend(status_values)
        
        # Zählen der Status-Werte pro Datei
        counter = Counter(status_values)
        status_by_file[file] = dict(counter)
    
    # Alle eindeutigen Status-Werte
    unique_status = sorted(set(all_status_values))
    
    # Gesamtzählung aller Status-Werte
    total_counter = Counter(all_status_values)
    
    # Ausgabe der Ergebnisse
    print("\n=== Alle gefundenen Status-Werte ===")
    for status in unique_status:
        print(f"- {status}")
    
    print("\n=== Anzahl der Status-Werte insgesamt ===")
    for status, count in total_counter.most_common():
        print(f"{status}: {count}")
    
    print("\n=== Status-Werte pro Datei ===")
    for file, counter in status_by_file.items():
        print(f"\nDatei: {file}")
        for status, count in counter.items():
            print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
