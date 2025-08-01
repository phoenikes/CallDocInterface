# CallDocInterface

## Projektüberblick
Dieses Tool bietet zwei Hauptfunktionen:
1. **Export von Termindaten**: Automatisierter Abruf und Export von medizinischen Termindaten (inkl. Patientendaten) aus dem CallDoc-System als strukturierte JSON-Dateien.
2. **Synchronisierung mit SQLHK-Datenbank**: Abgleich der CallDoc-Untersuchungsdaten mit der SQLHK-Datenbank, um Daten konsistent zu halten.

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
- **sync_gui.py**: Benutzeroberfläche für die Synchronisierung

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
   venv\Scripts\python.exe sync_gui.py
   ```
2. Wähle das gewünschte Datum aus (oder nutze die Buttons für Gestern/Heute/Morgen)
3. Klicke auf "Synchronisieren"
4. Verfolge den Fortschritt in der Log-Ausgabe
5. Nach Abschluss wird eine Zusammenfassung angezeigt

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
3. **Build für Synchronisierung:**
   ```powershell
   venv\Scripts\pyinstaller.exe --onefile --name calldoc_sync sync_gui.py
   ```
4. Die ausführbaren Dateien findest du im `dist`-Ordner

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
