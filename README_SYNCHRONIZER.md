# CallDoc-SQLHK Synchronizer

Diese Komponente ermöglicht den Vergleich und die Synchronisierung von Terminen zwischen dem CallDoc-System und der SQLHK-Datenbank.

## Features

- **Intelligente Statusfilterung**: Automatische Anpassung der Statusfilterung basierend auf dem Datum
- **Flexible Filterung**: Nach Termintyp, Arzt, Raum und Status
- **Detaillierte Analyse**: Statusverteilung und Patientendaten-Statistik
- **Vergleichstabelle**: Übersichtliche Darstellung der Übereinstimmungen und Unterschiede
- **Export**: Speicherung der Ergebnisse als JSON und CSV

## Verwendung über die Kommandozeile

Der Synchronizer kann direkt über die Kommandozeile aufgerufen werden:

```
python main.py vergleich [--datum DATUM] [--termintyp TERMINTYP] [--arzt ARZT] [--raum RAUM] [--status STATUS]
```

### Parameter

- `--datum`: Datum im Format YYYY-MM-DD oder DD.MM.YYYY (Standard: aktuelles Datum)
- `--termintyp`: ID oder Name des Termintyps (Standard: HERZKATHETERUNTERSUCHUNG)
- `--arzt`: ID oder Name des Arztes (optional)
- `--raum`: ID oder Name des Raums (optional)
- `--status`: Status-Filter (optional, überschreibt die intelligente Statusfilterung)

### Beispiele

```
# Vergleich für das aktuelle Datum mit Standardwerten
python main.py vergleich

# Vergleich für ein bestimmtes Datum
python main.py vergleich --datum 2025-08-04

# Vergleich für einen bestimmten Termintyp
python main.py vergleich --termintyp HERZKATHETERUNTERSUCHUNG

# Vergleich mit mehreren Filtern
python main.py vergleich --datum 2025-08-04 --termintyp 24 --arzt 5 --raum 3
```

## Verwendung im Code

Der Synchronizer kann auch direkt im Code verwendet werden:

```python
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer

# Synchronizer initialisieren
synchronizer = CallDocSQLHKSynchronizer()

# Vergleich durchführen
results = synchronizer.run_comparison(
    date_str="2025-08-04",
    appointment_type_id=24,
    doctor_id=5,
    room_id=3,
    status=None,
    smart_status_filter=True,
    save_results=True
)

# Ergebnisse ausgeben
synchronizer.print_results(results)

# Auf die Ergebnisse zugreifen
calldoc_appointments = results["calldoc_appointments"]
sqlhk_untersuchungen = results["sqlhk_untersuchungen"]
comparison_table = results["comparison_table"]
status_analysis = results["status_analysis"]
statistics = results["statistics"]
```

## Ausgabeformate

### Vergleichstabelle

Die Vergleichstabelle enthält folgende Spalten:

- **M1Ziffer**: M1-Ziffer des Patienten
- **Patient**: Name des Patienten
- **CallDoc ID**: ID des CallDoc-Termins
- **CallDoc Status**: Status des CallDoc-Termins
- **SQLHK UntersuchungID**: ID der SQLHK-Untersuchung
- **SQLHK UntersuchungartID**: Art der SQLHK-Untersuchung
- **Übereinstimmung**: "JA" bei Übereinstimmung, "X" bei Unterschied

### Statusanalyse

Die Statusanalyse enthält:

- **Gesamtanzahl Termine**: Anzahl der gefundenen CallDoc-Termine
- **Statusverteilung**: Anzahl der Termine pro Status (created, finished_final, pending, canceled, etc.)
- **Patientendaten**: Anzahl der Termine mit und ohne Patientendaten

### Dateien

Bei aktivierter Speicherung werden folgende Dateien erstellt:

- **vergleich_calldoc_sqlhk_DD_MM_YYYY.csv**: Vergleichstabelle als CSV
- **calldoc_termine_YYYY-MM-DD.json**: CallDoc-Termine als JSON
- **sqlhk_untersuchungen_mit_m1ziffer_DD_MM_YYYY.json**: SQLHK-Untersuchungen als JSON

## Erweiterungsmöglichkeiten

Der Synchronizer kann in Zukunft um folgende Funktionen erweitert werden:

- **Automatische Synchronisierung**: Automatisches Übertragen von Terminen zwischen den Systemen
- **Patientendaten-Upsert**: Aktualisieren oder Erstellen von Patientendaten in der Datenbank
- **Konfliktlösung**: Automatische oder manuelle Lösung von Konflikten zwischen den Systemen
- **Benachrichtigungen**: E-Mail- oder andere Benachrichtigungen bei Unterschieden
- **Weboberfläche**: Grafische Benutzeroberfläche für den Vergleich und die Synchronisierung
