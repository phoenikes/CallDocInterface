# CallDoc-SQLHK Synchronisierungs-GUI

## Übersicht

Diese Anwendung bietet eine moderne grafische Benutzeroberfläche für die Synchronisierung von Untersuchungsdaten zwischen dem CallDoc-System und der SQLHK-Datenbank. Sie ermöglicht eine einfache Konfiguration und Überwachung des Synchronisierungsprozesses sowie eine übersichtliche Darstellung der Ergebnisse.

## Funktionen

- **Datumsauswahl**: Kalender und Schnellzugriff auf gestern, heute und morgen
- **Konfigurationsoptionen**:
  - Auswahl des Termintyps (z.B. Herzkatheteruntersuchung, Herzultraschall)
  - Intelligenter Status-Filter (für vergangene Termine nur abgeschlossene, für zukünftige alle aktiven)
  - Löschlogik für obsolete Untersuchungen
- **Synchronisierungssteuerung**: Start- und Stopp-Buttons mit Fortschrittsanzeige
- **Ergebnisvisualisierung**:
  - Tabellarische Übersicht der Synchronisierungsergebnisse
  - Grafische Darstellung als Balkendiagramm
- **Protokollierung**: Detaillierte Protokollierung aller Schritte und Ergebnisse

## Installation

Die Anwendung benötigt Python 3.8 oder höher sowie die folgenden Pakete:

```
pip install PyQt5 matplotlib
```

## Verwendung

1. Starten Sie die Anwendung mit:
   ```
   python sync_gui_qt.py
   ```

2. Wählen Sie das gewünschte Datum für die Synchronisierung aus.

3. Konfigurieren Sie die Synchronisierungsparameter:
   - Wählen Sie einen bestimmten Termintyp oder "Alle Typen"
   - Aktivieren oder deaktivieren Sie den intelligenten Status-Filter
   - Aktivieren oder deaktivieren Sie die Löschlogik für obsolete Untersuchungen

4. Klicken Sie auf "Synchronisierung starten", um den Prozess zu beginnen.

5. Überwachen Sie den Fortschritt und die Ergebnisse in den Tabs "Ergebnisse" und "Protokoll".

## Technische Details

Die Anwendung verwendet:
- **PyQt5** für die grafische Benutzeroberfläche
- **Matplotlib** für die Visualisierung der Ergebnisse
- **Threading** für nicht-blockierende Ausführung der Synchronisierung

Die Synchronisierungslogik basiert auf den bestehenden Komponenten:
- `CallDocInterface`: API-Client für CallDoc
- `MsSqlApiClient`: Client für die SQLHK-Datenbank
- `PatientSynchronizer`: Synchronisierung von Patientendaten
- `UntersuchungSynchronizer`: Synchronisierung von Untersuchungsdaten

## Ausgabedateien

Die Anwendung erzeugt folgende Dateien:
- `sync_gui_YYYYMMDD_HHMMSS.log`: Protokolldatei mit allen Meldungen
- `calldoc_termine_YYYY-MM-DD.json`: Abgerufene CallDoc-Termine
- `sqlhk_untersuchungen_YYYY-MM-DD.json`: Abgerufene SQLHK-Untersuchungen
- `sync_result_YYYY-MM-DD_YYYYMMDD_HHMMSS.json`: Detaillierte Ergebnisse der Synchronisierung

## Fehlerbehebung

Bei Problemen überprüfen Sie bitte:
1. Die Verbindung zu den API-Endpunkten von CallDoc und SQLHK
2. Die Protokolldateien für detaillierte Fehlermeldungen
3. Die Konfiguration der Synchronisierungsparameter

## Autor

Markus, August 2025
