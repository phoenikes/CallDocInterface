"""
Ruft Untersuchungen für den 04.08.2025 über die UntersuchungSynchronizer-Klasse ab.

Dieses Skript verwendet die bestehende UntersuchungSynchronizer-Klasse, um
Untersuchungen aus der SQLHK-Datenbank für den 04.08.2025 abzurufen.
"""

import json
import logging
from datetime import datetime
from untersuchung_synchronizer import UntersuchungSynchronizer

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

def main():
    # Versuche beide Datumsformate: YYYY-MM-DD und DD.MM.YYYY
    target_date_iso = "2025-08-04"
    target_date_de = "04.08.2025"
    
    # Alternativ auch das Datum 31.07.2025 prüfen
    alt_date_iso = "2025-07-31"
    alt_date_de = "31.07.2025"
    
    # UntersuchungSynchronizer initialisieren
    synchronizer = UntersuchungSynchronizer()
    
    # Versuche zuerst das ISO-Format für das Zieldatum
    logger.info(f"Rufe Untersuchungen für {target_date_iso} (ISO-Format) ab...")
    untersuchungen = synchronizer.get_sqlhk_untersuchungen(target_date_iso)
    
    # Wenn keine Ergebnisse, versuche das deutsche Format
    if not untersuchungen:
        logger.info(f"Keine Untersuchungen im ISO-Format gefunden. Versuche deutsches Format {target_date_de}...")
        untersuchungen = synchronizer.get_sqlhk_untersuchungen(target_date_de)
    
    # Wenn immer noch keine Ergebnisse, versuche alternatives Datum
    if not untersuchungen:
        logger.info(f"Keine Untersuchungen für 04.08.2025 gefunden. Versuche alternatives Datum {alt_date_iso}...")
        untersuchungen = synchronizer.get_sqlhk_untersuchungen(alt_date_iso)
        
    # Letzter Versuch mit deutschem Format des alternativen Datums
    if not untersuchungen:
        logger.info(f"Versuche alternatives Datum im deutschen Format {alt_date_de}...")
        untersuchungen = synchronizer.get_sqlhk_untersuchungen(alt_date_de)
    
    if not untersuchungen:
        logger.warning(f"Keine Untersuchungen für beide Datumsformate gefunden.")
        return
        
    # Ermittle, welches Datum erfolgreich war
    current_date = target_date_iso
    if "31.07" in str(untersuchungen) or "2025-07-31" in str(untersuchungen):
        current_date = alt_date_iso
    
    # Untersuchungen anzeigen
    logger.info(f"{len(untersuchungen)} Untersuchungen gefunden:")
    
    for i, untersuchung in enumerate(untersuchungen, 1):
        print(f"\n{i}. UntersuchungID: {untersuchung.get('UntersuchungID')}")
        print(f"   Datum: {untersuchung.get('Datum')}")
        print(f"   PatientID: {untersuchung.get('PatientID')}")
        print(f"   UntersuchungartID: {untersuchung.get('UntersuchungartID')}")
        print(f"   HerzkatheterID: {untersuchung.get('HerzkatheterID')}")
    
    # Gruppieren nach UntersuchungartID
    art_counts = {}
    for u in untersuchungen:
        art_id = u.get("UntersuchungartID", "unbekannt")
        art_counts[art_id] = art_counts.get(art_id, 0) + 1
    
    print("\nAnzahl der Untersuchungen pro UntersuchungartID:")
    for art_id, count in art_counts.items():
        print(f"   UntersuchungartID {art_id}: {count}")
    
    # Untersuchungen als JSON-Datei speichern
    filename = f"sqlhk_untersuchungen_{current_date.replace('-', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(untersuchungen, f, indent=2, cls=json.JSONEncoder)
    logger.info(f"Untersuchungen wurden in {filename} gespeichert.")

if __name__ == "__main__":
    main()
