"""Debug-Skript fuer Synchronisierung"""
import traceback
import sys
import io
from datetime import datetime

# Fix fuer Windows Console Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from untersuchung_synchronizer import UntersuchungSynchronizer
from patient_synchronizer import PatientSynchronizer

def test_sync():
    date_str = "2026-01-12"
    appointment_type_id = 24

    print(f"=== Test Sync für {date_str} ===\n")

    # 1. CallDoc Termine abrufen
    print("1. Rufe CallDoc Termine ab...")
    calldoc_client = CallDocInterface(from_date=date_str, to_date=date_str)
    response = calldoc_client.appointment_search(appointment_type_id=appointment_type_id)

    if 'error' in response:
        print(f"FEHLER: {response}")
        return

    appointments = response.get('data', [])
    print(f"   -> {len(appointments)} Termine gefunden")

    # Filter
    filtered = [a for a in appointments if a.get('appointment_type') == appointment_type_id]
    active = [a for a in filtered if a.get('status') != 'canceled']
    print(f"   -> {len(active)} aktive Termine nach Filter")

    # 2. SQLHK Untersuchungen abrufen
    print("\n2. Rufe SQLHK Untersuchungen ab...")
    date_parts = date_str.split('-')
    sqlhk_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"

    mssql_client = MsSqlApiClient()
    sqlhk_untersuchungen = mssql_client.get_untersuchungen_by_date(sqlhk_date)
    print(f"   -> Untersuchungen: {sqlhk_untersuchungen}")
    print(f"   -> Typ: {type(sqlhk_untersuchungen)}")

    # Wenn es ein Dict mit 'rows' ist, extrahiere die Liste
    if isinstance(sqlhk_untersuchungen, dict):
        print(f"   -> Keys: {sqlhk_untersuchungen.keys()}")
        if 'rows' in sqlhk_untersuchungen:
            sqlhk_untersuchungen = sqlhk_untersuchungen.get('rows', [])
            print(f"   -> Extrahierte {len(sqlhk_untersuchungen)} Untersuchungen aus 'rows'")

    if isinstance(sqlhk_untersuchungen, list) and sqlhk_untersuchungen:
        print(f"   -> Erstes Element Typ: {type(sqlhk_untersuchungen[0])}")
        print(f"   -> Erstes Element: {sqlhk_untersuchungen[0]}")

    # 3. Patienten synchronisieren
    print("\n3. Starte Patienten-Synchronisierung...")
    try:
        patient_sync = PatientSynchronizer()
        patient_result = patient_sync.synchronize_patients_from_appointments(active[:2])  # Nur erste 2 zum Test
        print(f"   -> Patient-Sync Ergebnis: {patient_result}")
    except Exception as e:
        print(f"   -> FEHLER bei Patient-Sync: {e}")
        traceback.print_exc()

    # 4. Untersuchungen synchronisieren
    print("\n4. Starte Untersuchungs-Synchronisierung...")
    try:
        untersuchung_sync = UntersuchungSynchronizer()
        untersuchung_result = untersuchung_sync.synchronize_appointments(
            active[:2],  # Nur erste 2 zum Test
            sqlhk_untersuchungen
        )
        print(f"   -> Untersuchungs-Sync Ergebnis: {untersuchung_result}")
    except Exception as e:
        print(f"   -> FEHLER bei Untersuchungs-Sync: {e}")
        traceback.print_exc()

    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_sync()
