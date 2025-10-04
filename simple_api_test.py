#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Einfacher API-Test ohne Unicode-Zeichen
Testet die Single-Patient Sync API mit PIZ 1698369
"""

import requests
import json
import time
import threading
from datetime import datetime

def start_api_server():
    """Startet den API Server"""
    from sync_api_server import app
    print('[START] Starte API Server...')
    app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)

def wait_for_api(max_attempts=10):
    """Wartet bis API bereit ist"""
    for i in range(max_attempts):
        try:
            resp = requests.get('http://127.0.0.1:5555/health', timeout=2)
            if resp.status_code == 200:
                print('[OK] API ist bereit!')
                return True
        except:
            print('[WAIT] Warte auf API... ({}/{})'.format(i+1, max_attempts))
            time.sleep(2)
    return False

def test_health_check():
    """Test 1: Health Check"""
    print('\n[TEST 1] HEALTH CHECK')
    print('-' * 40)
    
    try:
        resp = requests.get('http://127.0.0.1:5555/health', timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            print('[OK] Status: {}'.format(data.get('status')))
            print('[OK] Timestamp: {}'.format(data.get('timestamp')))
            print('[OK] Aktive Syncs: {}'.format(data.get('active_syncs')))
            return True
        else:
            print('[ERROR] Unerwarteter Status Code: {}'.format(resp.status_code))
            return False
    except Exception as e:
        print('[ERROR] Health Check fehlgeschlagen: {}'.format(e))
        return False

def test_successful_sync():
    """Test 2: Erfolgreicher Single-Patient Sync"""
    print('\n[TEST 2] SINGLE-PATIENT SYNC')
    print('-' * 40)
    
    payload = {
        'piz': '1698369',
        'date': '2025-10-06',
        'appointment_type_id': 24
    }
    
    print('[INFO] Test-PIZ: {}'.format(payload['piz']))
    print('[INFO] Test-Datum: {}'.format(payload['date']))
    print('[INFO] Appointment Type: {}'.format(payload['appointment_type_id']))
    
    try:
        start_time = time.time()
        resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=10)
        
        if resp.status_code != 202:
            print('[ERROR] Unerwarteter Status beim Starten: {}'.format(resp.status_code))
            print('Response: {}'.format(resp.text))
            return False
        
        result = resp.json()
        task_id = result.get('task_id')
        print('[OK] Sync gestartet - Task ID: {}'.format(task_id))
        
        # Status polling
        for i in range(20):  # Max 40 Sekunden
            time.sleep(2)
            status_resp = requests.get('http://127.0.0.1:5555/api/sync/status/{}'.format(task_id), timeout=5)
            
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                print('[STATUS] Check {}: {}'.format(i+1, status))
                
                if status == 'completed':
                    execution_time = time.time() - start_time
                    print('[SUCCESS] Abgeschlossen in {:.2f}s'.format(execution_time))
                    
                    # Performance Check
                    if execution_time <= 5:
                        print('[PERF] Performance OK: {:.2f}s <= 5s'.format(execution_time))
                    else:
                        print('[WARN] Performance langsam: {:.2f}s > 5s'.format(execution_time))
                    
                    # Response Struktur validieren
                    result_data = status_data.get('result', {})
                    print('[OK] Sync erfolgreich: {}'.format(result_data.get('success')))
                    print('[OK] PIZ verarbeitet: {}'.format(result_data.get('piz')))
                    
                    # Details ausgeben
                    print('\n[DETAILS] SYNC-ERGEBNIS:')
                    print(json.dumps(result_data, indent=2, ensure_ascii=False))
                    return True
                    
                elif status == 'failed':
                    print('[ERROR] FEHLGESCHLAGEN: {}'.format(status_data.get('error')))
                    return False
            else:
                print('[ERROR] Status-Abfrage fehlgeschlagen: {}'.format(status_resp.status_code))
                return False
        
        print('[WARN] TIMEOUT: Sync dauerte länger als 40 Sekunden')
        return False
        
    except Exception as e:
        print('[ERROR] Exception beim Test: {}'.format(e))
        return False

def test_nonexistent_patient():
    """Test 3: Nicht-existenter Patient"""
    print('\n[TEST 3] NICHT-EXISTENTER PATIENT')
    print('-' * 40)
    
    payload = {
        'piz': '9999999',
        'date': '2025-10-06',
        'appointment_type_id': 24
    }
    
    print('[INFO] Test-PIZ: {} (nicht existent)'.format(payload['piz']))
    
    try:
        resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=10)
        
        if resp.status_code == 202:
            result = resp.json()
            task_id = result.get('task_id')
            print('[OK] Sync gestartet - Task ID: {}'.format(task_id))
            
            # Status polling
            for i in range(10):
                time.sleep(2)
                status_resp = requests.get('http://127.0.0.1:5555/api/sync/status/{}'.format(task_id), timeout=5)
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get('status')
                    print('[STATUS] Check {}: {}'.format(i+1, status))
                    
                    if status == 'completed':
                        result_data = status_data.get('result', {})
                        appointments = result_data.get('appointments_processed', 0)
                        
                        if appointments == 0:
                            print('[OK] Korrekt: Keine Termine für nicht-existenten Patient gefunden')
                            return True
                        else:
                            print('[WARN] Unerwartetes Ergebnis: {} Termine gefunden'.format(appointments))
                            return False
                            
                    elif status == 'failed':
                        error = status_data.get('error', '')
                        print('[OK] Korrekt erkannt: {}'.format(error))
                        return True
            
            print('[WARN] TIMEOUT bei Test mit nicht-existentem Patient')
            return False
        else:
            print('[ERROR] Unerwarteter Status: {}'.format(resp.status_code))
            return False
            
    except Exception as e:
        print('[ERROR] Exception: {}'.format(e))
        return False

def test_invalid_requests():
    """Test 4: Ungültige Requests"""
    print('\n[TEST 4] UNGÜLTIGE REQUESTS')
    print('-' * 40)
    
    tests = [
        ({}, "Leerer Request"),
        ({'date': '2025-10-06'}, "Fehlende PIZ"),
        ({'piz': '123'}, "Fehlendes Datum"),
        ({'piz': '123', 'date': 'invalid'}, "Ungültiges Datumsformat"),
        ({'piz': '', 'date': '2025-10-06'}, "Leere PIZ")
    ]
    
    all_passed = True
    
    for payload, description in tests:
        print('\n[SUBTEST] {}'.format(description))
        try:
            resp = requests.post('http://127.0.0.1:5555/api/sync/patient', json=payload, timeout=5)
            
            if resp.status_code == 400:
                print('[OK] Korrekt abgelehnt (400)')
            else:
                print('[ERROR] Unerwarteter Status: {}'.format(resp.status_code))
                all_passed = False
                
        except Exception as e:
            print('[ERROR] Exception: {}'.format(e))
            all_passed = False
    
    return all_passed

def main():
    """Hauptfunktion für alle Tests"""
    print('UMFASSENDER SINGLE-PATIENT API-TEST')
    print('=' * 60)
    print('Testzeit: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print('Testdatum: 06.10.2025')
    print('Test-PIZ: 1698369')
    print('=' * 60)
    
    # Server starten
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()
    
    # Warten bis API bereit ist
    if not wait_for_api():
        print('[ERROR] API konnte nicht gestartet werden!')
        return False
    
    # Alle Tests durchführen
    test_results = []
    
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("Erfolgreicher Sync", test_successful_sync()))
    test_results.append(("Nicht-existenter Patient", test_nonexistent_patient()))
    test_results.append(("Ungültige Requests", test_invalid_requests()))
    
    # Zusammenfassung
    print('\n' + '='*60)
    print('TESTERGEBNISSE')
    print('='*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS] BESTANDEN" if result else "[FAIL] FEHLGESCHLAGEN"
        print('{:<25} {}'.format(test_name, status))
        if result:
            passed += 1
    
    print('\n' + '='*60)
    print('GESAMT: {}/{} Tests bestanden'.format(passed, total))
    
    if passed == total:
        print('\n[SUCCESS] ALLE TESTS ERFOLGREICH!')
        print('\nNÄCHSTE SCHRITTE:')
        print('1. [OK] API ist voll funktionsfähig')
        print('2. [OK] Single-Patient Sync funktioniert korrekt')
        print('3. [OK] Fehlerbehandlung arbeitet ordnungsgemäß')
        print('4. [CHECK] Prüfen Sie die SQLHK-Datenbank auf korrekte Synchronisation')
        return True
    else:
        print('\n[WARN] EINIGE TESTS SIND FEHLGESCHLAGEN!')
        print('\nFEHLERBEHEBUNG:')
        print('1. Prüfen Sie die API-Server Logs')
        print('2. Verifizieren Sie CallDoc/SQLHK Verbindungen')
        print('3. Überprüfen Sie die Datenbankzugriffe')
        return False

if __name__ == "__main__":
    success = main()
    print('\n[EXIT] Testprogramm beendet mit Status: {}'.format('ERFOLG' if success else 'FEHLER'))