"""
Ruft Untersuchungen für den 31.07.2025 über die verbesserte API ab.
"""

import requests
import json
import logging
from datetime import datetime

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """
    Benutzerdefinierter JSON-Encoder für spezielle Datentypen.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_untersuchungen(datum):
    """
    Ruft Untersuchungen für ein bestimmtes Datum ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ
        
    Returns:
        Liste der Untersuchungen
    """
    # Basisadresse der API
    base_url = "http://localhost:7007/api/untersuchung"
    
    # Parameter mit deutschem Datumsformat
    params = {"datum": datum}
    
    logger.info(f"Sende Anfrage an {base_url} mit Parametern {params}")
    
    # API-Aufruf durchführen
    response = requests.get(base_url, params=params)
    
    # Ergebnis verarbeiten
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Anzahl gefundener Untersuchungen: {len(result.get('data', []))}")
        return result.get('data', [])
    else:
        logger.error(f"Fehler: {response.status_code} - {response.text}")
        return []

def display_untersuchungen(untersuchungen):
    """
    Zeigt die Untersuchungen übersichtlich an.
    
    Args:
        untersuchungen: Liste der Untersuchungen
    """
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    # Untersuchungen anzeigen
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        print(f"   PatientID: {untersuchung.get('PatientID')}")
        print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
        print(f"   UntersucherAbrechnungID: {untersuchung.get('UntersucherAbrechnungID')}")
        print(f"   ZuweiserID: {untersuchung.get('ZuweiserID')}")
        print(f"   Materialpreis: {untersuchung.get('Materialpreis')}")
    
    # Gruppieren nach UntersuchungartID
    art_counts = {}
    for u in untersuchungen:
        art_id = u.get("UntersuchungartID", "unbekannt")
        art_counts[art_id] = art_counts.get(art_id, 0) + 1
    
    print("\nAnzahl der Untersuchungen pro UntersuchungartID:")
    for art_id, count in art_counts.items():
        print(f"   UntersuchungartID {art_id}: {count}")

def save_to_json(untersuchungen, filename):
    """
    Speichert die Untersuchungen als JSON-Datei.
    
    Args:
        untersuchungen: Liste der Untersuchungen
        filename: Name der Ausgabedatei
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=JSONEncoder)
    print(f"\nUntersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    # Datum für die Abfrage
    datum = "31.07.2025"
    
    print(f"Rufe Untersuchungen für {datum} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum)
    
    # Untersuchungen anzeigen
    display_untersuchungen(untersuchungen)
    
    # Untersuchungen als JSON-Datei speichern
    save_to_json(untersuchungen, f"untersuchungen_{datum.replace('.', '_')}.json")
