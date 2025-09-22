"""
Test für den 24.09.2025 - Alle Termine einlesen und verarbeiten
"""

import json
import logging
from datetime import datetime
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from untersuchung_synchronizer import UntersuchungSynchronizer

# Detailliertes Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_24_september():
    """Test für den 24.09.2025"""
    
    date_str = "2025-09-24"
    print(f"\n{'='*80}")
    print(f"TESTE SYNCHRONISATION FÜR {date_str} (Dienstag)")
    print(f"{'='*80}\n")
    
    # 1. CallDoc-Interface initialisieren
    print("1. Initialisiere CallDoc-Interface...")
    calldoc = CallDocInterface(from_date=date_str, to_date=date_str)
    
    # 2. Alle Termine abrufen (Typ 24 = Herzkatheteruntersuchung)
    print("2. Hole alle Termine vom CallDoc-System...")
    result = calldoc.appointment_search(appointment_type_id=24)
    
    if not result or 'data' not in result:
        print("FEHLER: Keine Daten von CallDoc erhalten!")
        return
    
    appointments = result['data']
    print(f"   -> {len(appointments)} Termine gefunden\n")
    
    # 3. Termine analysieren
    print("3. ANALYSE DER TERMINE:")
    print("-" * 60)
    
    missing_patients = []
    found_patients = []
    
    for i, appt in enumerate(appointments, 1):
        appt_id = appt.get('id')
        piz = appt.get('piz')
        status = appt.get('status')
        employee = appt.get('employee')
        room = appt.get('room')
        scheduled = appt.get('scheduled_for_datetime')
        
        # Zeit extrahieren
        time_str = ""
        if scheduled:
            try:
                dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "??:??"
        
        print(f"{i:2}. Termin ID: {appt_id}")
        print(f"    Zeit: {time_str} | Status: {status}")
        print(f"    PIZ/M1Ziffer: {piz}")
        print(f"    Arzt (employee): {employee} | Raum: {room}")
        
        # Patient-Details abrufen
        if piz:
            patient_result = calldoc.get_patient_by_piz(piz)
            if patient_result and 'patients' in patient_result and patient_result['patients']:
                patient = patient_result['patients'][0]
                surname = patient.get('surname', '?')
                firstname = patient.get('name', '?')
                # Entferne problematische Unicode-Zeichen
                if surname:
                    surname = surname.encode('ascii', 'replace').decode('ascii')
                if firstname:
                    firstname = firstname.encode('ascii', 'replace').decode('ascii')
                name = f"{surname}, {firstname}"
                print(f"    Patient: {name}")
                found_patients.append({
                    'appointment_id': appt_id,
                    'piz': piz,
                    'name': name,
                    'time': time_str
                })
            else:
                print(f"    Patient: NICHT GEFUNDEN!")
                missing_patients.append({
                    'appointment_id': appt_id,
                    'piz': piz,
                    'time': time_str
                })
        else:
            print(f"    Patient: KEINE PIZ!")
            missing_patients.append({
                'appointment_id': appt_id,
                'piz': None,
                'time': time_str
            })
        print()
    
    # 4. Zusammenfassung
    print("="*60)
    print("ZUSAMMENFASSUNG:")
    print(f"  Termine gesamt: {len(appointments)}")
    print(f"  Mit Patient gefunden: {len(found_patients)}")
    print(f"  Ohne Patient/PIZ: {len(missing_patients)}")
    
    if missing_patients:
        print("\n  PROBLEMATISCHE TERMINE:")
        for mp in missing_patients:
            print(f"    - Termin {mp['appointment_id']} um {mp['time']} (PIZ: {mp['piz'] or 'FEHLT'})")
    
    # 5. SQLHK-Prüfung
    print("\n" + "="*60)
    print("5. PRÜFE SQLHK-DATENBANK:")
    print("-" * 60)
    
    mssql = MsSqlApiClient()
    
    # Prüfe vorhandene Untersuchungen für diesen Tag
    german_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    existing = mssql.get_untersuchungen_by_date(date_str)
    
    if existing.get('success') and 'results' in existing:
        existing_count = len(existing['results'])
        print(f"  Bereits in SQLHK: {existing_count} Untersuchungen")
        
        if existing_count > 0:
            print("  Vorhandene Einträge:")
            for entry in existing['results'][:5]:  # Zeige max 5
                print(f"    - UntersuchungID {entry.get('UntersuchungID')}: "
                      f"Patient {entry.get('PatientID')} um {entry.get('Datum')}")
    else:
        print(f"  Fehler beim Abrufen: {existing.get('error')}")
    
    # 6. Mapping-Probleme prüfen
    print("\n" + "="*60)
    print("6. PRÜFE MAPPINGS:")
    print("-" * 60)
    
    # Sammle alle verwendeten IDs
    employees = set()
    rooms = set()
    
    for appt in appointments:
        if appt.get('employee'):
            employees.add(appt.get('employee'))
        if appt.get('room'):
            rooms.add(appt.get('room'))
    
    print(f"  Verwendete Employee IDs: {sorted(employees)}")
    print(f"  Verwendete Room IDs: {sorted(rooms)}")
    
    # Prüfe ob Mappings existieren
    print("\n  Prüfe Untersucher-Mappings:")
    for emp_id in sorted(employees):
        query = f"SELECT UntersucherAbrechnungID FROM Untersucherabrechnung WHERE employee_id = {emp_id}"
        result = mssql.execute_sql(query, "SQLHK")
        if result.get('success') and result.get('rows'):
            print(f"    Employee {emp_id}: OK (UntersucherAbrechnungID gefunden)")
        else:
            print(f"    Employee {emp_id}: FEHLT! (Kein Mapping vorhanden)")
    
    print("\n  Prüfe Herzkatheter-Mappings:")
    for room_id in sorted(rooms):
        query = f"SELECT HerzkatheterID FROM Herzkatheter WHERE room_id = {room_id}"
        result = mssql.execute_sql(query, "SQLHK")
        if result.get('success') and result.get('rows'):
            print(f"    Room {room_id}: OK (HerzkatheterID gefunden)")
        else:
            print(f"    Room {room_id}: FEHLT! (Kein Mapping vorhanden)")
    
    print("\n" + "="*80)
    print("TEST ABGESCHLOSSEN")
    print("="*80)
    
    return {
        'total_appointments': len(appointments),
        'found_patients': len(found_patients),
        'missing_patients': len(missing_patients),
        'appointments': appointments
    }

if __name__ == "__main__":
    result = test_24_september()
    
    # Speichere Rohdaten für weitere Analyse
    with open(f"test_24_september_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)