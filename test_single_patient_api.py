"""
Test-Script für die Single-Patient Sync API

Testet die neue API mit echten Daten vom 06.10.2025.
Autor: Markus
Datum: 04.10.2025
"""
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys
from datetime import datetime
from calldoc_interface import CallDocInterface


def find_test_patient(date_str="2025-10-06", appointment_type_id=24):
    """
    Findet einen echten Patienten mit Termin am 06.10.2025
    """
    print(f"\n[SUCHE] Testpatient für {date_str}...")
    
    try:
        # CallDoc Interface verwenden
        calldoc = CallDocInterface(date_str, date_str)
        response = calldoc.appointment_search(appointment_type_id=appointment_type_id)
        
        if 'error' in response:
            print(f"[FEHLER] CallDoc-Abfrage: {response}")
            return None
            
        appointments = response.get('data', [])
        
        if not appointments:
            print(f"[WARNUNG] Keine Termine am {date_str} gefunden")
            return None
        
        print(f"[OK] {len(appointments)} Termine gefunden")
        
        # Nehme ersten Termin mit PIZ
        for appointment in appointments:
            piz = appointment.get('piz')
            if piz:
                patient_name = "Unbekannt"
                # Versuche Patientendaten zu holen
                try:
                    patient_response = calldoc.get_patient_by_piz(piz)
                    if patient_response and not patient_response.get("error"):
                        patients = patient_response.get("patients", [])
                        if patients:
                            patient = patients[0]
                            patient_name = f"{patient.get('surname', '')}, {patient.get('name', '')}"
                except:
                    pass
                    
                print(f"[GEFUNDEN] Testpatient: PIZ={piz}, Name={patient_name}")
                return {
                    "piz": str(piz),
                    "name": patient_name,
                    "appointment": appointment
                }
        
        print("[WARNUNG] Kein Termin mit PIZ gefunden")
        return None
        
    except Exception as e:
        print(f"[FEHLER] Beim Suchen: {str(e)}")
        return None


def test_single_patient_sync(piz, date_str="2025-10-06"):
    """
    Testet die Single-Patient Sync API
    """
    base_url = "http://localhost:5555"
    
    print(f"\n[START] Teste Single-Patient Sync API")
    print(f"   PIZ: {piz}")
    print(f"   Datum: {date_str}")
    print("-" * 50)
    
    # 1. Health Check
    print("\n[1] Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"[OK] API ist erreichbar: {response.json()}")
        else:
            print(f"[FEHLER] API nicht erreichbar: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FEHLER] API Server läuft nicht auf Port 5555!")
        print("   Bitte starten Sie zuerst die sync_gui_qt.exe")
        return False
    except Exception as e:
        print(f"[FEHLER] Verbindungsfehler: {str(e)}")
        return False
    
    # 2. Single-Patient Sync starten
    print("\n[2] Starte Single-Patient Synchronisation...")
    
    payload = {
        "piz": piz,
        "date": date_str,
        "appointment_type_id": 24
    }
    
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/sync/patient",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 202:
            print(f"[FEHLER] Unerwarteter Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        task_id = result.get('task_id')
        
        print(f"[OK] Sync gestartet!")
        print(f"   Task ID: {task_id}")
        print(f"   Status URL: {result.get('status_url')}")
        
    except Exception as e:
        print(f"[FEHLER] Beim Starten: {str(e)}")
        return False
    
    # 3. Status abfragen (Polling)
    print("\n[3] Warte auf Ergebnis...")
    
    max_attempts = 30  # Max 60 Sekunden warten (30 x 2 Sekunden)
    for i in range(max_attempts):
        try:
            status_response = requests.get(
                f"{base_url}/api/sync/status/{task_id}",
                timeout=5
            )
            
            if status_response.status_code != 200:
                print(f"[FEHLER] Status-Abfrage fehlgeschlagen: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            current_status = status_data.get('status')
            
            # Progress-Anzeige
            print(f"\r   Status: {current_status} {'.' * (i % 4)}    ", end="")
            
            if current_status == 'completed':
                execution_time = time.time() - start_time
                print(f"\n[ERFOLG] Synchronisation erfolgreich abgeschlossen!")
                print(f"   Ausführungszeit: {execution_time:.2f} Sekunden")
                
                # Ergebnis-Details anzeigen
                result = status_data.get('result', {})
                print("\n[ERGEBNIS] Details:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Validierung
                if execution_time > 5:
                    print(f"\n[WARNUNG] Performance: Sync dauerte {execution_time:.2f}s (Ziel: < 5s)")
                
                return True
                
            elif current_status == 'failed':
                print(f"\n[FEHLER] Synchronisation fehlgeschlagen!")
                print(f"   Fehler: {status_data.get('error')}")
                return False
            
            # Warte 2 Sekunden vor nächstem Versuch
            time.sleep(2)
            
        except Exception as e:
            print(f"\n[FEHLER] Bei Status-Abfrage: {str(e)}")
            return False
    
    print(f"\n[TIMEOUT] Synchronisation dauert länger als {max_attempts * 2} Sekunden")
    return False


def run_full_test():
    """
    Führt den kompletten Test durch
    """
    print("=" * 60)
    print("TEST: SINGLE-PATIENT SYNC API")
    print("=" * 60)
    print(f"Testdatum: 06.10.2025")
    print(f"Startzeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Testpatient finden
    test_patient = find_test_patient("2025-10-06")
    
    if not test_patient:
        print("\n[FEHLER] Kein Testpatient gefunden. Test abgebrochen.")
        return False
    
    # 2. API testen
    success = test_single_patient_sync(
        piz=test_patient['piz'],
        date_str="2025-10-06"
    )
    
    # 3. Zusammenfassung
    print("\n" + "=" * 60)
    if success:
        print("[ERFOLG] TEST ERFOLGREICH BESTANDEN!")
        print("\nNächste Schritte:")
        print("1. Prüfen Sie die SQLHK-Datenbank ob die Untersuchung angelegt wurde")
        print("2. Verifizieren Sie dass andere Patienten nicht verändert wurden")
        print("3. Testen Sie mit verschiedenen PIZ-Werten")
    else:
        print("[FEHLER] TEST FEHLGESCHLAGEN!")
        print("\nBitte prüfen Sie:")
        print("1. Läuft die sync_gui_qt.exe?")
        print("2. Ist der API-Server auf Port 5555 aktiv?")
        print("3. Sind die CallDoc/SQLHK Verbindungen aktiv?")
    
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    # Teste die API
    success = run_full_test()
    
    # Exit-Code für CI/CD
    sys.exit(0 if success else 1)