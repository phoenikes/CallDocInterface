# Dokumentation: Synchronisationsproblem und Lösung

## Datum: 22.09.2025

## Problem
Die Synchronisation zwischen CallDoc und SQLHK funktionierte nicht. Termine wurden aus CallDoc gelesen, aber:
- Patienten wurden nicht in SQLHK eingefügt
- Untersuchungen wurden nicht in SQLHK eingefügt  
- Es gab keine klaren Fehlermeldungen

## Ursachen des Problems

### 1. **Datenbankzugriff - Falscher Datenbankname** ❌
- In `untersuchung_synchronizer.py` wurden Patient-Lookups mit der falschen Datenbank gemacht
- **Fehler**: `self.mssql_client.execute_sql(query, "SuPDatabase")` (3 Stellen)
- **Korrektur**: `self.mssql_client.execute_sql(query, "SQLHK")`

### 2. **API-Endpoints nicht funktionsfähig** ❌
- Die `upsert_data` Endpoints gaben 500-Fehler zurück
- apimsdata.exe war möglicherweise nicht korrekt gestartet oder konfiguriert
- **Workaround**: Direktes SQL mit INSERT statt upsert_data verwenden

### 3. **Fehlende Mappings in der Datenbank** ❌
- Beim ersten Durchlauf existierten keine Mappings zwischen:
  - CallDoc room_id → SQLHK HerzkatheterID
  - CallDoc employee_id → SQLHK UntersucherAbrechnungID  
  - CallDoc appointment_type → SQLHK UntersuchungartID
- **Lösung**: Mappings wurden automatisch oder manuell in der Datenbank erstellt

### 4. **SQL INSERT ohne Fehlerbehandlung** ❌
- INSERT-Statements geben normalerweise "This result object does not return rows" zurück
- Dies wurde als Fehler interpretiert, obwohl es normal ist
- **Lösung**: Diese Meldung als Erfolg behandeln

## Was wurde geändert

### 1. Datenbankzugriff korrigiert
```python
# Alt (FALSCH):
result = self.mssql_client.execute_sql(query, "SuPDatabase")

# Neu (RICHTIG):
result = self.mssql_client.execute_sql(query, "SQLHK")
```

### 2. Workaround für upsert_data implementiert
```python
# Prüfe ob Datensatz existiert
check_result = self.mssql_client.execute_sql(check_query, "SQLHK")

if check_result.get("success") and check_result.get("rows"):
    # Datensatz existiert - UPDATE oder Skip
    logger.info(f"Untersuchung existiert bereits")
else:
    # Datensatz existiert nicht - INSERT
    result = self.mssql_client.insert_untersuchung(untersuchung_data)
```

### 3. Mappings wurden erstellt
Die Datenbank hat jetzt Mappings für:
- room_id 54 → HerzkatheterID 3 (Offenbach1)
- room_id 19 → HerzkatheterID 2 (Rummelsberg 2)
- room_id 18 → HerzkatheterID 1 (Rummelsberg 1)
- room_id 61 → HerzkatheterID 6 (Braunschweig)
- employee_id 18 → UntersucherAbrechnungID 1 (Dr. Markus Sandrock)
- employee_id 27 → UntersucherAbrechnungID 2 (Papageorgiou Polykarpos)
- employee_id 49 → UntersucherAbrechnungID 13 (Andeep Pannu)
- employee_id 50 → UntersucherAbrechnungID 12 (Dr. Alexander Koch)
- employee_id 56 → UntersucherAbrechnungID 22 (PD Dr. Jochen Tillmanns)
- appointment_type 24 → UntersuchungartID 1 (KV Diagnostik ambulant)

### 4. INSERT-Fehlerbehandlung verbessert
```python
if result.get("error") and "does not return rows" in str(result.get("error")):
    # Das ist normal bei INSERT - es werden keine Zeilen zurückgegeben
    return {"success": True, "message": "Erfolgreich eingefügt"}
```

## Verifizierung der Lösung

### 24.09.2025 - Erfolgreich ✅
- 29 Untersuchungen eingefügt
- 27 aktive Termine synchronisiert
- Alle Patienten angelegt

### 30.09.2025 - Erfolgreich ✅
- 8 Untersuchungen eingefügt
- 8 aktive Termine synchronisiert
- Alle Patienten angelegt

## Wichtige Hinweise für die Zukunft

1. **apimsdata.exe MUSS laufen** für SQL-Operationen
2. **Mappings müssen existieren** zwischen CallDoc und SQLHK IDs
3. **Datenbankname muss korrekt sein**: Immer "SQLHK" verwenden, nicht "SuPDatabase"
4. **INSERT-Meldungen richtig interpretieren**: "does not return rows" ist normal

## Status
✅ **PROBLEM GELÖST** - Synchronisation funktioniert vollständig