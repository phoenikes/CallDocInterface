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

---

## Changelog

### Version 2.3.0 (03.06.2026)

#### Kontext:
Beim Abgleich der Aerzte-IDs fiel auf, dass CallDoc keine dedizierte Mitarbeiter-Liste
hat - die Stammdaten lagen verstreut. Loesung: die (vorher unbekannten) CallDoc-Endpunkte
`/doctors/`, `/rooms/`, `/appointment-types/` gefunden und als GUI-Dialoge nutzbar gemacht.

#### Aenderungen:
1. **Neues GUI-Menue "CallDoc"** mit 3 modalen Dialogen
   - Aerzte anzeigen (Ctrl+D), Raeume anzeigen (Ctrl+R), Untersuchungsarten anzeigen (Ctrl+T)
   - Live-Abruf aus CallDoc + Spalten "in constants.py" / "in SQLHK" + Suche/Filter/Hervorhebung
   - Neue Dateien: aerzte_dialog.py, raeume_dialog.py, untersuchungsarten_dialog.py
   - CLI-Tool: list_doctors_from_calldoc.py

2. **constants.py - Mapping vervollstaendigt**
   - DOCTORS (30): + Chen (10103), Degenhardt (10104), Tegtmayer (10105), Gerhards (10116)
   - ROOMS (7 HK-Labore): + Regensburg (188), Augsburg (189)

3. **CallDocSync.spec**: 3 Dialog-Module zu datas + hiddenimports

4. **Nachgezogenes v2.2.1** (war nie committet): Saarbruecken room_id 147, total_raw-Fix, single_patient_sync im Build

5. **Build + Deploy**: CallDocSync.exe (93 MB) -> lokal + P:\MCP\Calldocinterface\
   - Commit f809d70 nach github phoenikes/CallDocInterface gepusht

#### Getestet:
- CallDoc /doctors/ liefert 95 Eintraege (94 Doctor), /rooms/ 211, /appointment-types/ 99
- Smoke-Test EXE: startet sauber, Scheduler laeuft, neue Menues vorhanden
- Deployment P: bestaetigt (alle Runtime-Dateien vorhanden: exe, Start.bat, slack_config.json, ico)

#### Offen (bewusst nicht gemacht):
- SQLHK Untersucherabrechnung.employee_id fuer Gerhards (10116) + Tegtmayer (10105) ist NULL
  -> ihre Termine laufen im Sandrock-Fallback, bis ein DB-UPDATE gesetzt wird
- Merke fuer Arzt-Anlage: Untersucher (Login) / Untersucherabrechnung (Abrechnung) / Zuweiser
  sind 3 unabhaengige Tabellen; factorial_id Pflicht (Kostenstelle), Default 6507

### Version 2.2.1 (21.04.2026)

#### Problem:
Dr. Poesch (employee_id 10081) Untersuchungen am Donnerstag 23.04.2026 landeten auf
**Rummelsberg 1** statt auf **Saarbruecken**. Ursache: Falsche room_id in der
Herzkatheter-Tabelle (187 statt 147).

#### Aenderungen:
1. **DB-Fix: Herzkatheter-Tabelle**
   - Saarbruecken (HerzkatheterID 7): room_id von 187 auf 147 korrigiert
   - CallDoc Room 147 = Saarbruecken HK-Labor

2. **sync_api_server.py - Bug-Fix**
   - Zeile 265: `len(appointments)` -> `total_raw` (NameError bei API-Sync behoben)

3. **constants.py - Neuer Raum**
   - `HERZKATHETER_SAARBRUECKEN: 147` hinzugefuegt

4. **CallDocSync.spec - Fehlende Module**
   - `single_patient_sync.py` zu datas und hiddenimports hinzugefuegt

5. **Neuer Build**
   - CallDocSync.exe (89 MB)
   - Deployed auf P:\MCP\Calldocinterface\

#### Getestet:
- Donnerstag 23.04.2026: 42 aktive Termine synchronisiert (0 Fehler)
- Dr. Poesch: 3 Patienten (Becker, Augustin, Mueller) korrekt auf Saarbruecken (HerzkatheterID 7)
- Alle anderen Standorte unveraendert (Rummelsberg 1+2, Offenbach, Braunschweig)

### Version 2.2.0 (05.04.2026)

#### Aenderungen:
1. **DB-Fix: Untersuchungart-Tabelle**
   - ID 2 (KV Intervention ambulant): appointment_type auf NULL (kein CallDoc-Mapping)
   - ID 8 (Ablation): appointment_type von {"1":31} auf {"1":25} (= CallDoc Ablation)

2. **constants.py**
   - "HERZKATHETER RUMMELSBERG": 25 -> "ABLATION": 25

3. **untersuchung_synchronizer.py - Ablation-Sonderlogik**
   - appointment_type == 25: ZuweiserID=7 (Duckheim), HerzkatheterID=2 (Rummelsberg 2) fix
   - Diagnostik (alle anderen): bestehendes Verhalten unveraendert

4. **sync_gui_qt.py - Multi-Type Support**
   - Neuer Dropdown: "HK Diagnostik + Ablation" ([24, 25]) als Default
   - SyncWorker: appointment_type_ids als Liste, mehrere API-Calls zusammengefuehrt
   - Startup: Auto-Sync immer 07:00, Live-Ueberwachung immer deaktiviert

5. **sync_api_server.py - Multi-Type Support**
   - SyncTask: appointment_type_ids als Liste
   - POST /api/sync: appointment_type_id akzeptiert int oder list, Default [24, 25]

6. **Neuer Build**
   - CallDocSync.exe (66 MB)

#### Getestet:
- Dry-Run Test: 15/15 Mappings korrekt (12 Diagnostik + 3 Ablation)
- GUI-Sync am 07.04.2026: 15 Untersuchungen korrekt in SQLHK
- Ablation: ZuweiserID=7, HerzkatheterID=2, UntersuchungartID=8 - alles korrekt
- Diagnostik: Unveraendert (ZuweiserID=2, HK dynamisch per room)
- EXE startet sauber, Live-Sync deaktiviert, Auto-Sync 07:00

### Version 2.1.1 (21.01.2026)

#### Aenderungen:
1. **constants.py - Vollstaendiges Aerzte-Mapping**
   - Alle 26 Aerzte aus SQLHK Untersucherabrechnung hinzugefuegt
   - Korrigierte employee_ids (z.B. NEUMANN: 29 -> 81)
   - Korrigierte Schreibweisen (STEFAN -> STEPHAN, TILLMANS -> TILLMANNS)
   - Neue Aerzte 2026: Poesch (10081), Vukaninovic (10082), Platschek (10091), Mohammed (10097)
   - Entfernt (nicht in DB): GASPLMAYR, KLOPF, GAWEHN

2. **CallDocSync.spec - Neue Module**
   - patient_resolver.py hinzugefuegt
   - slack_notifier.py hinzugefuegt
   - slack_config.json hinzugefuegt
   - slack_sdk zu hiddenimports hinzugefuegt

3. **Neuer Build**
   - CallDocSync.exe (86 MB)
   - Deployed auf P:\MCP\Calldocinterface\

#### Getestet:
- 51 Herzkatheter-Termine am 21.01.2026
- employee_id 10097 (Dr. Mohammed): 8 Termine in Offenbach korrekt erkannt
- Mapping funktioniert fuer alle aktiven Aerzte
