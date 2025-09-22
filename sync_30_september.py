"""
Vollständige Synchronisation für 30.09.2025 mit Patientenerstellung
"""

import json
import logging
from datetime import datetime
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_30_september():
    """Vollständige Synchronisation für 30.09.2025"""
    
    date_str = "2025-09-30"
    print(f"\n{'='*80}")
    print(f"VOLLSTÄNDIGE SYNCHRONISATION FÜR {date_str}")
    print(f"{'='*80}\n")
    
    # Initialisiere Clients
    calldoc = CallDocInterface(from_date=date_str, to_date=date_str)
    mssql = MsSqlApiClient()
    patient_sync = PatientSynchronizer()
    untersuchung_sync = UntersuchungSynchronizer(calldoc, mssql)
    
    # 1. Hole alle Termine
    print("PHASE 1: Hole CallDoc-Termine...")
    result = calldoc.appointment_search(appointment_type_id=24)
    appointments = result.get('data', [])
    
    # Filtere stornierte Termine raus
    active_appointments = [a for a in appointments if a.get('status') != 'canceled']
    canceled_count = len(appointments) - len(active_appointments)
    
    print(f"  Total: {len(appointments)} Termine")
    print(f"  Aktiv: {len(active_appointments)} Termine")
    print(f"  Storniert: {canceled_count} Termine\n")
    
    # 2. Synchronisiere Patienten
    print("PHASE 2: Synchronisiere Patienten...")
    patient_results = {
        'synced': 0,
        'failed': 0,
        'missing_piz': 0
    }
    
    for appt in active_appointments:
        piz = appt.get('piz')
        if not piz or piz == '0' or piz == 0:
            patient_results['missing_piz'] += 1
            print(f"  WARNUNG: Termin {appt.get('id')} hat keine gültige PIZ")
            continue
        
        # Hole Patient von CallDoc
        patient_data = calldoc.get_patient_by_piz(piz)
        if not patient_data or 'patients' not in patient_data or not patient_data['patients']:
            patient_results['failed'] += 1
            print(f"  FEHLER: Patient mit PIZ {piz} nicht in CallDoc gefunden")
            continue
        
        patient = patient_data['patients'][0]
        
        # Synchronisiere zu SQLHK
        try:
            # Erstelle Patient-Mapping für SQLHK
            sqlhk_patient = {
                'M1Ziffer': piz,
                'Nachname': patient.get('surname', 'Unbekannt'),
                'Vorname': patient.get('name', 'Unbekannt'),
                'Geburtsdatum': patient.get('date_of_birth', '01.01.1900'),
                'Geschlecht': patient.get('gender', 'U'),
                'PLZ': patient.get('city_code', '00000'),
                'Ort': patient.get('city', 'Unbekannt'),
                'Strasse': patient.get('address', 'Unbekannt')
            }
            
            # Escape Apostrophe in Namen
            nachname = sqlhk_patient['Nachname'].replace("'", "''")
            vorname = sqlhk_patient['Vorname'].replace("'", "''")
            
            # Füge Patient ein oder aktualisiere
            insert_query = f"""
            IF NOT EXISTS (SELECT 1 FROM Patient WHERE M1Ziffer = {piz})
            BEGIN
                INSERT INTO Patient (M1Ziffer, Nachname, Vorname, Geburtsdatum)
                VALUES ({piz}, '{nachname}', '{vorname}', '{sqlhk_patient['Geburtsdatum']}')
            END
            """
            
            result = mssql.execute_sql(insert_query, "SQLHK")
            if result.get('success') or (result.get('error') and 'does not return rows' in str(result.get('error'))):
                patient_results['synced'] += 1
            else:
                patient_results['failed'] += 1
                print(f"  FEHLER beim Einfügen von Patient {piz}: {result.get('error')}")
                
        except Exception as e:
            patient_results['failed'] += 1
            print(f"  FEHLER bei Patient {piz}: {str(e)}")
    
    print(f"\nPatienten-Sync Ergebnis:")
    print(f"  Synchronisiert: {patient_results['synced']}")
    print(f"  Fehlgeschlagen: {patient_results['failed']}")  
    print(f"  Ohne PIZ: {patient_results['missing_piz']}\n")
    
    # 3. Hole existierende SQLHK-Untersuchungen
    print("PHASE 3: Prüfe existierende SQLHK-Untersuchungen...")
    existing = mssql.get_untersuchungen_by_date(date_str)
    existing_count = 0
    if existing.get('success') and 'results' in existing:
        existing_count = len(existing['results'])
    elif existing.get('success') and 'rows' in existing:
        existing_count = len(existing['rows'])
    print(f"  Bereits vorhanden: {existing_count} Untersuchungen\n")
    
    # 4. Synchronisiere Untersuchungen
    print("PHASE 4: Synchronisiere Untersuchungen...")
    sync_stats = untersuchung_sync.synchronize_appointments(
        active_appointments, 
        existing.get('results', existing.get('rows', []))
    )
    
    print(f"\nSynchronisations-Ergebnis:")
    print(f"  Neue eingefügt: {sync_stats.get('inserted', 0)}")
    print(f"  Aktualisiert: {sync_stats.get('updated', 0)}")
    print(f"  Fehler: {sync_stats.get('errors', 0)}")
    
    # 5. Finale Prüfung
    print(f"\nPHASE 5: Finale Prüfung...")
    final_check = mssql.get_untersuchungen_by_date(date_str)
    final_count = 0
    if final_check.get('success') and 'results' in final_check:
        final_count = len(final_check['results'])
    elif final_check.get('success') and 'rows' in final_check:
        final_count = len(final_check['rows'])
    
    print(f"  Untersuchungen in SQLHK nach Sync: {final_count}")
    print(f"  Erwartete aktive Termine: {len(active_appointments)}")
    
    if final_count >= len(active_appointments):
        print(f"\nERFOLG: Alle aktiven Termine wurden synchronisiert!")
    else:
        diff = len(active_appointments) - final_count
        print(f"\nWARNUNG: {diff} Termine konnten nicht synchronisiert werden!")
    
    print(f"\n{'='*80}")
    print("SYNCHRONISATION ABGESCHLOSSEN")
    print(f"{'='*80}")
    
    return {
        'date': date_str,
        'total_appointments': len(appointments),
        'active_appointments': len(active_appointments),
        'canceled_appointments': canceled_count,
        'patients_synced': patient_results['synced'],
        'patients_failed': patient_results['failed'],
        'untersuchungen_inserted': sync_stats.get('inserted', 0),
        'untersuchungen_updated': sync_stats.get('updated', 0),
        'untersuchungen_errors': sync_stats.get('errors', 0),
        'final_count': final_count
    }

if __name__ == "__main__":
    result = sync_30_september()
    
    # Speichere Ergebnis
    filename = f"sync_30_september_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis gespeichert in: {filename}")