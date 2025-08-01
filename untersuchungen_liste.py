"""
Ruft Untersuchungen für den 31.07.2025 aus der SQLHK-Datenbank ab und gibt sie aus.
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

def get_untersuchungen(datum, server_url="http://localhost:7007"):
    """
    Ruft Untersuchungen aus der SQLHK-Datenbank über die API ab.
    
    Args:
        datum: Datum im Format TT.MM.JJJJ
        server_url: URL des API-Servers
        
    Returns:
        Liste der Untersuchungen
    """
    try:
        url = f"{server_url}/api/untersuchung"
        params = {"datum": datum}
        
        logger.info(f"Abfrage der Untersuchungen mit Parametern: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            untersuchungen = result.get("data", [])
            logger.info(f"{len(untersuchungen)} Untersuchungen gefunden")
            return untersuchungen
        else:
            logger.error(f"API-Fehler: {result.get('error', 'Unbekannter Fehler')}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"API-Kommunikationsfehler: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return []

def main():
    """
    Hauptfunktion zum Abrufen und Anzeigen der Untersuchungen.
    """
    # Datum für die Abfrage
    datum = "31.07.2025"
    
    print(f"Rufe Untersuchungen für {datum} ab...")
    
    # Untersuchungen abrufen
    untersuchungen = get_untersuchungen(datum)
    
    if not untersuchungen:
        print("Keine Untersuchungen gefunden.")
        return
    
    # Untersuchungen anzeigen
    print(f"\n{len(untersuchungen)} Untersuchungen gefunden:")
    
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        print(f"   PatientID: {untersuchung.get('PatientID')}")
        print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
        print(f"   UntersucherAbrechnungID: {untersuchung.get('UntersucherAbrechnungID')}")
        print(f"   ZuweiserID: {untersuchung.get('ZuweiserID')}")
        print(f"   Materialpreis: {untersuchung.get('Materialpreis')}")
    
    # Statistiken nach UntersuchungartID
    untersuchungsarten = {}
    for untersuchung in untersuchungen:
        art_id = untersuchung.get("UntersuchungartID")
        if art_id not in untersuchungsarten:
            untersuchungsarten[art_id] = 0
        untersuchungsarten[art_id] += 1
    
    print("\nStatistiken nach UntersuchungartID:")
    for art_id, anzahl in untersuchungsarten.items():
        print(f"   UntersuchungartID {art_id}: {anzahl} Untersuchungen")
    
    # Optional: Untersuchungen als JSON-Datei speichern
    with open(f"untersuchungen_{datum.replace('.', '_')}.json", "w", encoding="utf-8") as f:
        json.dump(untersuchungen, f, indent=2, ensure_ascii=False)
    
    print(f"\nUntersuchungen wurden in untersuchungen_{datum.replace('.', '_')}.json gespeichert.")

if __name__ == "__main__":
    main()
