# CallDoc-SQLHK Patienten-Synchronisation

Diese Dokumentation beschreibt die Funktionalität zur Synchronisation von Patientendaten zwischen dem CallDoc-System und der SQLHK-Datenbank.

## Übersicht

Die Patienten-Synchronisation ermöglicht es, Patientendaten aus CallDoc-Terminen automatisch in die SQLHK-Datenbank zu übertragen. Dabei werden folgende Schritte durchgeführt:

1. Abruf von Terminen aus CallDoc für ein bestimmtes Datum
2. Extraktion der Patientendaten aus den Terminen
3. Mapping der CallDoc-Patientenfelder auf das SQLHK-Datenbankschema
4. Suche nach vorhandenen Patienten in SQLHK
5. Aktualisierung vorhandener oder Einfügen neuer Patientendaten in SQLHK

## Verwendung über die Kommandozeile

Die Patienten-Synchronisation kann über die Kommandozeile mit folgendem Befehl gestartet werden:

```
python main.py patienten-sync [--datum DATUM] [--termintyp TERMINTYP] [--arzt ARZT] [--raum RAUM] [--status STATUS]
```

### Parameter

- `--datum`: Datum im Format YYYY-MM-DD (Standard: aktuelles Datum)
- `--termintyp`: ID oder Name des Termintyps (Standard: HERZKATHETERUNTERSUCHUNG)
- `--arzt`: ID oder Name des Arztes (optional)
- `--raum`: ID oder Name des Raums (optional)
- `--status`: Status-Filter (optional)

### Beispiele

```
# Synchronisation für das aktuelle Datum
python main.py patienten-sync

# Synchronisation für ein bestimmtes Datum
python main.py patienten-sync --datum 2025-07-31

# Synchronisation für einen bestimmten Termintyp
python main.py patienten-sync --termintyp HERZKATHETERUNTERSUCHUNG

# Synchronisation für einen bestimmten Arzt
python main.py patienten-sync --arzt "DR. MÜLLER"

# Synchronisation für einen bestimmten Raum
python main.py patienten-sync --raum "HKL 1"

# Kombination mehrerer Filter
python main.py patienten-sync --datum 2025-07-31 --termintyp HERZKATHETERUNTERSUCHUNG --arzt "DR. MÜLLER"
```

## Feldmapping

Die Patientendaten werden wie folgt zwischen CallDoc und SQLHK gemappt:

| CallDoc-Feld | SQLHK-Feld | Bemerkung |
|--------------|------------|-----------|
| last_name | Nachname | - |
| first_name | Vorname | - |
| date_of_birth | Geburtsdatum | Format-Konvertierung von YYYY-MM-DD zu DD.MM.YYYY |
| gender | Geschlecht | Konvertierung: male -> 1, female -> 2 |
| zip | PLZ | - |
| email | Email | - |
| mobile_phone | Handy | - |
| phone | Telefon | - |
| insurance_company | Krankenkasse | - |
| insurance_number | Versichertennr | - |
| street | Strasse | - |
| city | Stadt | - |
| insurance_status | Krankenkassestatus | - |
| allergies | Allergie | - |

## Ergebnisse

Nach der Synchronisation werden folgende Informationen ausgegeben:

- Gesamtanzahl der verarbeiteten Patienten
- Anzahl der erfolgreich synchronisierten Patienten
- Anzahl der fehlgeschlagenen Synchronisationen
- Anzahl der aktualisierten Patienten
- Anzahl der neu eingefügten Patienten

Die detaillierten Ergebnisse werden in einer JSON-Datei im Format `patient_sync_results_YYYYMMDD_HHMMSS.json` gespeichert.

## Technische Details

Die Patienten-Synchronisation verwendet folgende Komponenten:

- `PatientSynchronizer`: Klasse zur Synchronisation von Patientendaten
- `CallDocSQLHKSynchronizer`: Übergeordnete Klasse für die Synchronisation zwischen CallDoc und SQLHK
- `CallDocInterface`: Schnittstelle zur CallDoc-API
- `SQLHK-API`: REST-API für die SQLHK-Datenbank (Port 7007)

## Fehlerbehandlung

Bei Fehlern während der Synchronisation werden diese protokolliert und in den Ergebnissen ausgegeben. Häufige Fehlerquellen sind:

- Verbindungsprobleme mit der CallDoc-API oder SQLHK-API
- Fehlende oder ungültige Patientendaten
- Fehler beim Mapping der Daten
- Fehler beim Einfügen oder Aktualisieren der Daten in der SQLHK-Datenbank

## Logs

Alle Aktionen und Fehler werden im Log-File protokolliert, das in der `config.json` konfiguriert ist.
