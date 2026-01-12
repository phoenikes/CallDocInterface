# TASKS.md - CallDocInterface Verbesserungen

## Datum: 12.01.2026
## Kontext: Analyse vom 13.01.2026 Sync

---

## Problem-Analyse

### Gefundene Probleme:

1. **Termine ohne PIZ werden ignoriert** (8 von 16 Terminen)
   - 4 haben KVNR aber keine PIZ -> M1Ziffer kann via .con gefunden werden
   - 4 haben weder KVNR noch PIZ -> Neue Patienten

2. **Falsche Statistik-Anzeige** ("16 Faelle geloescht")
   - Seit KVDT-Implementierung (v2.0.3) fehlerhaft
   - Statistik zeigt falsche Werte fuer inserted/updated/deleted

3. **Geschlecht wird nicht aktualisiert**
   - KVDT-Anreicherung mappt Geschlecht korrekt (M->1, W->2)
   - Aber UPDATE in SQLHK wird nicht ausgefuehrt oder ueberschrieben

---

## Tasks

### Task 1: Patient-Resolver implementieren (KVNR-Fallback)
- [ ] 1.1 Neue Klasse `PatientResolver` erstellen
- [ ] 1.2 Methode: `resolve_by_piz()` - Direkte PIZ-Suche
- [ ] 1.3 Methode: `resolve_by_kvnr()` - KVNR in .con Dateien suchen
- [ ] 1.4 Methode: `resolve_by_name_dob()` - Name+Geburtsdatum Fallback
- [ ] 1.5 Integration in `sync_gui_qt.py` SyncWorker
- [ ] 1.6 Logging fuer jeden Schritt

### Task 2: Statistik-Bug fixen
- [ ] 2.1 Analyse: Wo wird die Statistik berechnet?
- [ ] 2.2 Vergleich mit funktionierender Version (vor v2.0.3)
- [ ] 2.3 Bug identifizieren und fixen
- [ ] 2.4 Test mit bekannten Daten

### Task 3: KVDT-Anreicherung Geschlecht fixen
- [x] 3.1 Analyse: Wann wird Geschlecht ueberschrieben?
- [x] 3.2 Pruefen ob patient_synchronizer Geschlecht ueberschreibt
- [x] 3.3 Reihenfolge der Updates pruefen
- [x] 3.4 Fix implementieren

### Task 4: Erweitertes Logging - SKIPPED
- [~] Bereits 136 Logger-Aufrufe in den relevanten Modulen vorhanden
- [~] PatientResolver: 24 Aufrufe (jeden Schritt geloggt)
- [~] UntersuchungSynchronizer: 99 Aufrufe (INSERT/UPDATE/DELETE)
- [~] KVDTEnricher: 13 Aufrufe (Feld-Updates)
- **Entscheidung**: Zusaetzliches Logging nicht noetig

---

## Aktueller Status

| Task | Status | Bearbeiter |
|------|--------|------------|
| Task 1 | DONE | Claude |
| Task 2 | DONE (war durch Task 1 verursacht) | Claude |
| Task 3 | DONE | Claude |
| Task 4 | SKIPPED (Logging bereits ausreichend) | - |

---

## Erledigte Tasks

### Task 1: PatientResolver (DONE - 12.01.2026)
- `patient_resolver.py` erstellt
- Suche nach PIZ, KVNR, Name+Geb.datum implementiert
- Neuanlage von Patienten wenn nicht gefunden
- In `untersuchung_synchronizer.py` integriert
- **Ergebnis**: 15 von 15 Terminen aufgeloest (vorher: 7)

### Task 2: Statistik-Bug (DONE - 12.01.2026)
- Bug war verursacht durch PatientID=1 Fallback
- Alle Termine ohne PIZ hatten denselben Identifier
- Durch PatientResolver behoben - jeder Patient hat nun eindeutige ID
- **Ergebnis**: Statistik zeigt korrekt 8 INSERT, 7 UPDATE, 0 DELETE

### Task 3: KVDT-Anreicherung Geschlecht (DONE - 12.01.2026)
- Problem: KVDT-Anreicherung verwendete nur `apt.get("piz")`, ignorierte `resolved_piz`
- Patienten via PatientResolver aufgeloest hatten keine KVDT-Anreicherung
- Fix in `sync_gui_qt.py`: M1Ziffern-Liste beruecksichtigt jetzt beide Quellen
- **Ergebnis**: Geschlecht wird korrekt von 0 auf 1/2 aktualisiert
- **Test**: Petrich (1713657), Maerbert (1711929), Uphoff (1653518) - alle Geschlecht=1

### Task 5: Duplikat-Bug bei Patienten ohne KVNR (DONE - 12.01.2026)
- Problem: PatientResolver legte bei jedem Sync neue Patienten an statt existierende zu finden
- Ursache: Keine SQLHK-Suche nach Name+Geburtsdatum vor Neuanlage
- Fix in `patient_resolver.py`: Neue Methode `_find_patient_in_sqlhk_by_name_dob()`
- **Ergebnis**: Keine Duplikate mehr bei wiederholten Syncs
- **Test**: Rusiti, Born, Repp, Gerlach-Mazza - alle nur 1x vorhanden

---

## Notizen

### Performance-Messungen (124 .con Dateien):
- PIZ-Suche: ~0.1 Sek
- KVNR-Suche: ~1-2 Sek
- Name+Geb.datum: ~2 Sek

### Test-Daten 13.01.2026:
- 16 Termine gesamt
- 8 mit PIZ (funktioniert)
- 4 mit KVNR ohne PIZ (M1Ziffer gefunden via .con)
- 4 ohne KVNR (neue Patienten)
