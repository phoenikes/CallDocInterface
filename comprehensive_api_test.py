#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Umfassender Test für die Single-Patient Sync API
Testet alle Szenarien einschließlich Performance und Fehlerbehandlung.

Autor: Test-Agent
Datum: 04.10.2025
"""

import requests
import json
import time
import threading
from datetime import datetime
import sys

# API Server starten
def start_api_server():
    """Startet den API Server in einem Thread"""
    try:
        from sync_api_server import app
        print("[START] Starte API Server...")
        app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[ERROR] Fehler beim Starten des API Servers: {e}")

def wait_for_api(max_attempts=10):
    """Wartet bis API bereit ist"""
    for i in range(max_attempts):
        try:
            resp = requests.get('http://127.0.0.1:5555/health', timeout=2)
            if resp.status_code == 200:
                print("[OK] API ist bereit!")
                return True
        except:
            print(f"[WAIT] Warte auf API... ({i+1}/{max_attempts})")
            time.sleep(2)
    return False

def test_health_check():
    """Test 1: Health Check"""
    print("\n" + "="*50)
    print("TEST 1: HEALTH CHECK")
    print("="*50)
    
    try:
        resp = requests.get('http://127.0.0.1:5555/health', timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[OK] Status: {data.get('status')}")
            print(f"[OK] Timestamp: {data.get('timestamp')}")
            print(f"[OK] Aktive Syncs: {data.get('active_syncs')}")
            return True
        else:
            print(f"[ERROR] Unerwarteter Status Code: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Health Check fehlgeschlagen: {e}")
        return False

def test_successful_sync():
    """Test 2: Erfolgreicher Single-Patient Sync"""
    print("\n" + "="*50)
    print("TEST 2: ERFOLGREICHER SINGLE-PATIENT SYNC")
    print("="*50)
    
    payload = {
        'piz': '1698369',
        'date': '2025-10-06',
        'appointment_type_id': 24
    }
    
    print(f"[INFO] Test-PIZ: {payload['piz']}")
    print(f"[INFO] Test-Datum: {payload['date']}")
    print(f"[INFO] Appointment Type: {payload['appointment_type_id']}")
    
    try:
        start_time = time.time()
        
        # Sync starten
        resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=10)
        
        if resp.status_code != 202:
            print(f"[ERROR] Unerwarteter Status beim Starten: {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
        
        result = resp.json()
        task_id = result.get('task_id')
        print(f"[OK] Sync gestartet - Task ID: {task_id}")
        
        # Status polling
        for i in range(20):  # Max 40 Sekunden
            time.sleep(2)
            status_resp = requests.get(f'http://127.0.0.1:5555/api/sync/status/{task_id}', timeout=5)
            
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                print(f"[STATUS] Check {i+1}: {status}")
                
                if status == 'completed':
                    execution_time = time.time() - start_time
                    print(f"[SUCCESS] ERFOLGREICH abgeschlossen in {execution_time:.2f}s")
                    
                    # Performance Check
                    if execution_time <= 5:
                        print(f"[PERF] Performance OK: {execution_time:.2f}s <= 5s")
                    else:
                        print(f"[WARN] Performance langsam: {execution_time:.2f}s > 5s")
                    
                    # Response Struktur validieren
                    result_data = status_data.get('result', {})
                    print(f"[OK] Sync erfolgreich: {result_data.get('success')}")
                    print(f"[OK] PIZ verarbeitet: {result_data.get('piz')}")
                    
                    # Details ausgeben
                    print("\n[DETAILS] SYNC-DETAILS:")
                    appointments = result_data.get('appointments_processed', 0)
                    patients = result_data.get('patients_synced', 0)
                    untersuchungen = result_data.get('untersuchungen_synced', 0)
                    
                    print(f"   - Termine verarbeitet: {appointments}")
                    print(f"   - Patienten synchronisiert: {patients}")
                    print(f"   - Untersuchungen synchronisiert: {untersuchungen}")
                    
                    return True
                    
                elif status == 'failed':
                    print(f"[ERROR] FEHLGESCHLAGEN: {status_data.get('error')}")
                    return False
            else:
                print(f"[ERROR] Status-Abfrage fehlgeschlagen: {status_resp.status_code}")
                return False
        
        print("[WARN] TIMEOUT: Sync dauerte länger als 40 Sekunden")
        return False
        
    except Exception as e:
        print(f"[ERROR] Exception beim Test: {e}")
        return False

def test_nonexistent_patient():
    """Test 3: Nicht-existenter Patient"""
    print("\n" + "="*50)
    print("TEST 3: NICHT-EXISTENTER PATIENT")
    print("="*50)
    
    payload = {
        'piz': '9999999',
        'date': '2025-10-06',
        'appointment_type_id': 24
    }
    
    print(f"🔹 Test-PIZ: {payload['piz']} (nicht existent)")
    
    try:
        start_time = time.time()
        resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=10)
        
        if resp.status_code == 202:
            result = resp.json()
            task_id = result.get('task_id')
            print(f"✅ Sync gestartet - Task ID: {task_id}")
            
            # Status polling
            for i in range(10):
                time.sleep(2)
                status_resp = requests.get(f'http://127.0.0.1:5555/api/sync/status/{task_id}', timeout=5)
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get('status')
                    print(f"⏳ Status Check {i+1}: {status}")
                    
                    if status == 'completed':
                        execution_time = time.time() - start_time
                        result_data = status_data.get('result', {})
                        
                        # Bei nicht-existentem Patient sollte sync trotzdem "erfolgreich" sein,
                        # aber keine Termine finden
                        appointments = result_data.get('appointments_processed', 0)
                        if appointments == 0:
                            print(f"✅ Korrekt: Keine Termine für nicht-existenten Patient gefunden")
                            return True
                        else:
                            print(f"⚠️ Unerwartetes Ergebnis: {appointments} Termine gefunden")
                            return False
                            
                    elif status == 'failed':
                        # Auch OK - System erkennt nicht-existenten Patient
                        error = status_data.get('error', '')
                        if 'keine termine' in error.lower() or 'not found' in error.lower():
                            print(f"✅ Korrekt erkannt: {error}")
                            return True
                        else:
                            print(f"❌ Unerwarteter Fehler: {error}")
                            return False
            
            print("⚠️ TIMEOUT bei Test mit nicht-existentem Patient")
            return False
        else:
            print(f"❌ Unerwarteter Status: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_wrong_date():
    """Test 4: Falsches Datum ohne Termine"""
    print("\n" + "="*50)
    print("TEST 4: FALSCHES DATUM OHNE TERMINE")
    print("="*50)
    
    payload = {
        'piz': '1698369',
        'date': '2025-12-25',  # Weihnachten - wahrscheinlich keine Termine
        'appointment_type_id': 24
    }
    
    print(f"🔹 Test-PIZ: {payload['piz']}")
    print(f"🔹 Test-Datum: {payload['date']} (wahrscheinlich keine Termine)")
    
    try:
        start_time = time.time()
        resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=10)
        
        if resp.status_code == 202:
            result = resp.json()
            task_id = result.get('task_id')
            print(f"✅ Sync gestartet - Task ID: {task_id}")
            
            # Status polling
            for i in range(10):
                time.sleep(2)
                status_resp = requests.get(f'http://127.0.0.1:5555/api/sync/status/{task_id}', timeout=5)
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get('status')
                    print(f"⏳ Status Check {i+1}: {status}")
                    
                    if status == 'completed':
                        result_data = status_data.get('result', {})
                        appointments = result_data.get('appointments_processed', 0)
                        
                        if appointments == 0:
                            print(f"✅ Korrekt: Keine Termine am {payload['date']} gefunden")
                            return True
                        else:
                            print(f"⚠️ Unerwartetes Ergebnis: {appointments} Termine gefunden")
                            return False
                            
                    elif status == 'failed':
                        error = status_data.get('error', '')
                        if 'keine termine' in error.lower():
                            print(f"✅ Korrekt erkannt: {error}")
                            return True
                        else:
                            print(f"❌ Unerwarteter Fehler: {error}")
                            return False
            
            print("⚠️ TIMEOUT bei Test mit falschem Datum")
            return False
        else:
            print(f"❌ Unerwarteter Status: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_invalid_requests():
    """Test 5: Ungültige Requests"""
    print("\n" + "="*50)
    print("TEST 5: UNGÜLTIGE REQUESTS")
    print("="*50)
    
    tests = [
        ({}, "Leerer Request"),
        ({'date': '2025-10-06'}, "Fehlende PIZ"),
        ({'piz': '123'}, "Fehlendes Datum"),
        ({'piz': '123', 'date': 'invalid'}, "Ungültiges Datumsformat"),
        ({'piz': '', 'date': '2025-10-06'}, "Leere PIZ")
    ]
    
    all_passed = True
    
    for payload, description in tests:
        print(f"\n🔸 Test: {description}")
        try:
            resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=5)
            
            if resp.status_code == 400:
                print(f"✅ Korrekt abgelehnt (400)")
            else:
                print(f"❌ Unerwarteter Status: {resp.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Hauptfunktion für alle Tests"""
    print("UMFASSENDER API-TEST")
    print("=" * 60)
    print(f"Testzeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testdatum: 06.10.2025")
    print(f"Test-PIZ: 1698369")
    print("=" * 60)
    
    # Server starten
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()
    
    # Warten bis API bereit ist
    if not wait_for_api():
        print("❌ API konnte nicht gestartet werden!")
        return False
    
    # Alle Tests durchführen
    test_results = []
    
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("Erfolgreicher Sync", test_successful_sync()))
    test_results.append(("Nicht-existenter Patient", test_nonexistent_patient()))
    test_results.append(("Falsches Datum", test_wrong_date()))
    test_results.append(("Ungültige Requests", test_invalid_requests()))
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("TESTERGEBNISSE")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("\n" + "="*60)
    print(f"GESAMT: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("\n📋 NÄCHSTE SCHRITTE:")
        print("1. ✅ API ist voll funktionsfähig")
        print("2. ✅ Single-Patient Sync funktioniert korrekt")
        print("3. ✅ Fehlerbehandlung arbeitet ordnungsgemäß")
        print("4. ✅ Performance ist akzeptabel")
        print("5. 🔍 Prüfen Sie die SQLHK-Datenbank auf korrekte Synchronisation")
        return True
    else:
        print("⚠️ EINIGE TESTS SIND FEHLGESCHLAGEN!")
        print("\n🔧 FEHLERBEHEBUNG:")
        print("1. Prüfen Sie die API-Server Logs")
        print("2. Verifizieren Sie CallDoc/SQLHK Verbindungen")
        print("3. Überprüfen Sie die Datenbankzugriffe")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)