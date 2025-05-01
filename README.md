# CallDocInterface Exporter

## Projektüberblick
Dieses Tool dient dem automatisierten Abruf und Export von medizinischen Termindaten (inkl. Patientendaten) aus dem CallDoc-System. Die Daten werden für beliebige Zeiträume (z.B. einzelne Tage oder ganze Wochen) als strukturierte JSON-Dateien gespeichert.

---

## Hauptfunktionen

### 1. Einzel- und Wochenexport
- **Einzelexport:** Termine eines Tages werden mit Patientendaten angereichert und als JSON gespeichert.
- **Wochenexport:** Für eine ganze Kalenderwoche (Mo–Fr, optional ohne Feiertage) werden für jeden Tag eigene JSON-Dateien erzeugt.

### 2. Flexible Filter
- Nach Terminart, Arzt und Raum filterbar (nur Werte aus `constants.py` erlaubt)
- Ausgabe-Dateinamen enthalten alle Filterkriterien zur Nachvollziehbarkeit

### 3. Automatisierte Exporte
- Im Hauptskript werden automatisch die nächste und übernächste Woche exportiert
- Die Exportdateien landen im Ordner `P:/imports/cathlab/json_heydoc`

---

## Wichtige Dateien & Klassen

- **main.py**: Einstiegspunkt, steuert den Ablauf für Wochenexporte
- **appointment_patient_enricher.py**: Kapselt die Anreicherung der Termine mit Patientendaten, Export als JSON/CSV
- **weekly_appointment_exporter.py**: Kapselt den Export für ganze Wochen (inkl. Feiertagsprüfung möglich)
- **constants.py**: Enthält alle erlaubten IDs und API-URLs

---

## Benutzung (Python)
1. Passe bei Bedarf Filter (appointment_type_id, doctor_id, room_id) in `main.py` an
2. Starte das Script:
   ```powershell
   venv\Scripts\python.exe main.py
   ```
3. Die JSON-Dateien werden automatisch erzeugt

---

## Erstellung einer .exe (Windows)
1. **Voraussetzung:** Alle Abhängigkeiten im venv installiert (inkl. pyinstaller)
2. **Build:**
   ```powershell
   venv\Scripts\pyinstaller.exe --onefile --name calldoc_exporter main.py
   ```
3. Die ausführbare Datei findest du im `dist`-Ordner

---

## Beispiel: Dateinamen
Die Exportdateien haben folgendes Format:
```
YYYY-MM-DD_YYYY-MM-DD_APPOINTMENTTYPE_DOCTOR_ROOM.json
```
Wird ein Filter nicht gesetzt, steht an dessen Stelle eine 0.

---

## Erweiterungsmöglichkeiten
- Feiertagsprüfung für beliebige Bundesländer (mit Paket `holidays`)
- Weitere Exportformate (CSV, Excel)
- Automatisierung als Task/Scheduled Job

---

## Support
Bei Fragen oder Erweiterungswünschen: Ansprechpartner ist das Entwicklungsteam Praxis Heydoc.

---

## Lizenz
Interne Nutzung Praxis Heydoc. Weitergabe oder kommerzielle Nutzung nur nach Rücksprache.
