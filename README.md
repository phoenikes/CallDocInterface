# CallDocInterface

## Projektüberblick
Dieses Tool bietet drei Hauptfunktionen:
1. **Export von Termindaten**: Automatisierter Abruf und Export von medizinischen Termindaten (inkl. Patientendaten) aus dem CallDoc-System als strukturierte JSON-Dateien.
2. **Synchronisierung mit SQLHK-Datenbank**: Abgleich der CallDoc-Untersuchungsdaten mit der SQLHK-Datenbank, um Daten konsistent zu halten.
3. **REST API**: RESTful API zur Integration mit anderen Systemen und zur Fernsteuerung der Synchronisierung.

---

## Hauptfunktionen

### 1. Einzel- und Wochenexport
- **Einzelexport:** Termine eines Tages werden mit Patientendaten angereichert und als JSON gespeichert.
- **Wochenexport:** Für eine ganze Kalenderwoche (Mo–Fr, optional ohne Feiertage) werden für jeden Tag eigene JSON-Dateien erzeugt.
- **Flexible Filter:** Nach Terminart, Arzt und Raum filterbar (nur Werte aus `constants.py` erlaubt)

### 2. Datenbank-Synchronisierung
- **Tagesweise Synchronisierung:** Abgleich der CallDoc-Termine mit der SQLHK-Datenbank für einen ausgewählten Tag
- **Automatische Erkennung:** Identifizierung von neuen, zu aktualisierenden und zu löschenden Untersuchungen
- **Benutzerfreundliche GUI:** Einfache Oberfläche zur Auswahl des Datums und Überwachung des Synchronisierungsprozesses

### 3. REST API
- **API-Server:** Integrierter REST API-Server zur Fernsteuerung der Synchronisierung
- **Authentifizierung:** Sicherung der API-Endpunkte durch API-Schlüssel
- **Swagger UI:** Interaktive API-Dokumentation zur einfachen Nutzung
- **Steuerung über GUI:** Start/Stopp des API-Servers und Konfiguration direkt aus der GUI

---

## Wichtige Dateien & Klassen

### Export-Komponenten
- **main.py**: Einstiegspunkt für Wochenexporte
- **appointment_patient_enricher.py**: Anreicherung der Termine mit Patientendaten, Export als JSON/CSV
- **weekly_appointment_exporter.py**: Export für ganze Wochen (inkl. Feiertagsprüfung)
- **constants.py**: Enthält alle erlaubten IDs und API-URLs

### Synchronisierungs-Komponenten
- **plan.py**: Übersicht des Gesamtprojekts mit Teilprojekten und Implementierungsplan
- **mssql_api_client.py**: Client für die Kommunikation mit der MS SQL Server API
- **untersuchung_synchronizer.py**: Logik für den Vergleich und die Synchronisierung der Daten
- **sync_gui_qt.py**: Moderne PyQt5-basierte Benutzeroberfläche für die Synchronisierung
- **connection_checker.py**: Prüft die Verbindung zu den API-Servern
- **config_manager.py**: Verwaltet die Konfigurationseinstellungen
- **auto_sync_scheduler.py**: Steuert die automatische Synchronisierung

### API-Komponenten
- **api_server.py**: Implementierung des REST API-Servers mit FastAPI
- **api_integration.py**: Integration des API-Servers in die GUI-Anwendung
- **API_DOKUMENTATION.md**: Ausführliche Dokumentation aller API-Endpunkte
- **test_api_integration.py**: Testskript für die API-Integration

---

## Benutzung

### Export-Funktion
1. Passe bei Bedarf Filter (appointment_type_id, doctor_id, room_id) in `main.py` an
2. Starte das Script:
   ```powershell
   venv\Scripts\python.exe main.py
   ```
3. Die JSON-Dateien werden automatisch erzeugt

### Synchronisierungs-Funktion
1. Starte die GUI:
   ```powershell
   venv\Scripts\python.exe sync_gui_qt.py
   ```
2. Wähle ein Datum im Kalender aus
3. Klicke auf "Synchronisieren", um den Abgleich zu starten

### API-Funktion
1. Starte die GUI wie oben beschrieben
2. Wähle im Menü "API" > "API-Server starten"
3. Der API-Server wird im Hintergrund gestartet und ist unter http://localhost:8080/api/ erreichbar
4. Unter "API" > "API-Schlüssel anzeigen" kannst du den API-Schlüssel einsehen
5. Die API-Dokumentation kannst du über "API" > "API-Dokumentation öffnen" aufrufen

Alternativ kann der API-Server auch direkt gestartet werden:
```powershell
venv\Scripts\python.exe api_server.py
```

### Neue Funktionen in Version 5.0

#### Verbindungsprüfung
- Automatische Prüfung der Verbindung zu CallDoc und SQLHK beim Start
- Farbliche Anzeige des Verbindungsstatus (grün: verbunden, rot: nicht verbunden)
- Verbindungsprüfung vor jeder Synchronisierung

#### Konfigurationsdialog
- Zugriff über Menü "Einstellungen" oder Tastenkombination Strg+K
- Bearbeitung der API-URLs für CallDoc und SQLHK
- Verbindungstest direkt aus dem Dialog möglich

#### Automatische Synchronisierung
- Konfigurierbare automatische Synchronisierung
- Einstellbare Parameter:
  - Aktivierung/Deaktivierung
  - Synchronisierungsintervall in Minuten
  - Aktive Wochentage
  - Zeitfenster (Start- und Endzeit)
- Steuerung über Menü "Einstellungen" -> "Auto-Sync starten/stoppen"

### Neue Funktionen in Version 6.0

#### API-Server Integration
- Vollständige Integration eines REST API-Servers in die GUI-Anwendung
- Start und Stopp des API-Servers direkt aus der GUI
- Konfiguration des API-Ports über die GUI
- Anzeige und Verwaltung des API-Schlüssels

#### API-Endpunkte
- Health-Endpunkte zur Überprüfung des Server- und Verbindungsstatus
- Synchronisierungs-Endpunkte zum Starten und Überwachen von Synchronisierungen
- Scheduler-Endpunkte zur Steuerung der automatischen Synchronisierung
- Daten-Endpunkte zum Abruf von CallDoc-Terminen und SQLHK-Untersuchungen

#### API-Sicherheit
- Authentifizierung mittels API-Schlüssel für alle geschützten Endpunkte
- Automatische Generierung eines sicheren API-Schlüssels
- Möglichkeit zur Neugenerierung des API-Schlüssels über die GUI

#### API-Dokumentation
- Interaktive Swagger UI-Dokumentation unter `/api/docs`
- Ausführliche Markdown-Dokumentation in `API_DOKUMENTATION.md`
- Beispielanfragen und -antworten für alle Endpunkte

---

## Technische Details

### CallDoc-API
- Zugriff über die `CallDocInterface`-Klasse
- Unterstützt Patienten- und Terminsuche
- Erfordert Datum im Format YYYY-MM-DD

### MS SQL Server API
- Zugriff über die `MsSqlApiClient`-Klasse
- Unterstützt SQL-Ausführung und Upsert-Operationen
- Spezielle Methoden für die Untersuchungstabelle

### Patientenabfrage
- Funktionen in `patient_abfrage.py`
- Unterstützt Abfrage nach PatientID oder M1Ziffer
- Wichtig: Erfordert spezielle Datenbankwechsel-Logik (siehe unten)

### REST API
- Implementiert mit FastAPI
- Authentifizierung über API-Schlüssel
- Swagger UI-Dokumentation unter `/api/docs`
- Unterstützt Synchronisierung, Scheduler-Steuerung und Datenabruf

### Synchronisierungslogik
- Mapping zwischen CallDoc-Terminen und SQLHK-Untersuchungen
- Vergleich basierend auf externen IDs und relevanten Feldern
- Transaktionsmanagement für atomare Operationen

---

## Erstellung einer .exe (Windows)
1. **Voraussetzung:** Alle Abhängigkeiten im venv installiert (inkl. pyinstaller)
2. **Build für Export:**
   ```powershell
   venv\Scripts\pyinstaller.exe --onefile --name calldoc_exporter main.py
   ```
3. **Build für Synchronisierung mit GUI und API:**
   ```powershell
   venv\Scripts\pyinstaller.exe --onefile --name heydok-cathlab-communicator sync_gui_qt.py
   ```
4. Die ausführbaren Dateien findest du im `dist`-Ordner

Eine detaillierte Anleitung zur Erstellung der .exe-Datei findest du in der Datei `ANLEITUNG_EXE_ERSTELLUNG.md`.

---

## Patientenabfrage aus SQLHK

### Überblick
Die Funktionen in `patient_abfrage.py` ermöglichen den Abruf von Patientendaten aus der SQLHK-Datenbank anhand der PatientID oder M1Ziffer. Diese Funktionen sind wichtig für die Synchronisierung zwischen CallDoc und SQLHK, da die M1Ziffer als Schlüssel für die Zuordnung dient.

### Verwendung

```python
# Patientenabfrage nach ID
from patient_abfrage import get_patient_by_id

patient = get_patient_by_id(12825)
if patient:
    print(f"Patient gefunden: {patient['Nachname']}, {patient['Vorname']}")
    print(f"M1Ziffer: {patient['M1Ziffer']}")

# Patientenabfrage nach M1Ziffer
from patient_abfrage import get_patient_by_m1ziffer

patient = get_patient_by_m1ziffer(1695672)
if patient:
    print(f"Patient gefunden: {patient['Nachname']}, {patient['Vorname']}")
    print(f"PatientID: {patient['PatientID']}")
```

### Wichtige Hinweise zur Datenbankabfrage

1. **Datenbankwechsel erforderlich**: Die Abfrage erfordert einen expliziten Wechsel zur SQLHK-Datenbank und anschließend zurück zur SuPDatabase.

2. **Dreischrittiges Verfahren**:
   - Erster API-Aufruf: `USE SQLHK;`
   - Zweiter API-Aufruf: Die eigentliche Patientenabfrage
   - Dritter API-Aufruf: `USE SuPDatabase;`

3. **Fehlerbehandlung**: Die Funktionen stellen sicher, dass auch im Fehlerfall ein Rückwechsel zur SuPDatabase erfolgt.

4. **Testbeispiele**: Die Datei enthält Testcode für mehrere PatientIDs (12825, 12844, 5538, 12263, 12830).

### Beispielaufruf

```powershell
python patient_abfrage.py
```

Dies testet die Patientenabfrage für mehrere PatientIDs und speichert die Ergebnisse als JSON-Dateien.

## Support
Bei Fragen oder Erweiterungswünschen: Ansprechpartner ist das Entwicklungsteam Praxis Heydoc.

---

## Lizenz
Interne Nutzung Praxis Heydoc. Weitergabe oder kommerzielle Nutzung nur nach Rücksprache.
