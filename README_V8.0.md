# CallDoc-SQLHK Synchronisierung Version 8.0

## Übersicht

Die CallDoc-SQLHK Synchronisierung ist eine Anwendung zur Synchronisierung von Termindaten zwischen dem CallDoc-System und der SQLHK-Datenbank. Version 8.0 enthält wichtige Fehlerbehebungen und Verbesserungen für die dynamische Feldzuordnung sowie eine eigenständige ausführbare Datei mit benutzerdefiniertem Icon.

## Fehlerbehebungen

### Korrektur der dynamischen Feldzuordnung

In Version 8.0 wurde ein kritischer Fehler bei der dynamischen Zuordnung der Felder `HerzkatheterID` und `UntersucherAbrechnungID` behoben:

1. **Problem**: Die SQL-Abfragen in den Methoden `_get_herzkatheter_id_by_room_id` und `_get_untersucher_id_by_employee_id` verwendeten falsche Spaltennamen (`room` statt `room_id` und `employee` statt `employee_id`), was dazu führte, dass keine Ergebnisse gefunden wurden und die Standardwerte (HerzkatheterID=1 und UntersucherAbrechnungID=1) verwendet wurden.

2. **Lösung**: Die WHERE-Klauseln in den SQL-Abfragen wurden korrigiert:
   - Von `WHERE room = {room_id}` zu `WHERE room_id = {room_id}`
   - Von `WHERE employee = {employee_id}` zu `WHERE employee_id = {employee_id}`

Diese Korrekturen stellen sicher, dass die dynamische Zuordnung der Felder HerzkatheterID und UntersucherAbrechnungID korrekt funktioniert und die richtigen Werte aus der Datenbank abgerufen werden.

## Neue Funktionen

### Eigenständige ausführbare Datei (EXE)

Die Anwendung wurde als eigenständige ausführbare Datei (EXE) bereitgestellt, die keine separate Python-Installation benötigt:

- **Name**: CallDocSQLHKSync.exe
- **Speicherort**: `dist/CallDocSQLHKSync.exe`
- **Typ**: Eigenständige Anwendung ohne Konsole (--onefile --windowed)

Die EXE-Datei enthält alle notwendigen Abhängigkeiten und kann auf anderen Windows-Computern ausgeführt werden, ohne dass Python installiert sein muss.

### Benutzerdefiniertes Icon

Ein benutzerdefiniertes Icon wurde für die Anwendung erstellt:

- **Speicherort**: `resources/app_icon.ico`
- **Design**: Medizinisches Symbol (Kreuz) mit Synchronisierungssymbol und den Buchstaben "C" und "S" für CallDoc und SQLHK
- **Farben**: Blau als Hintergrund und Rot als Akzentfarbe
- **Größen**: 16, 32, 48, 64, 128, 256 Pixel

### Desktop-Shortcut

Ein Desktop-Shortcut wurde erstellt, der auf die EXE-Datei verweist und das benutzerdefinierte Icon verwendet:

- **Name**: CallDocSQLHKSync.lnk
- **Speicherort**: Desktop des Benutzers
- **Ziel**: `dist/CallDocSQLHKSync.exe`
- **Icon**: `resources/app_icon.ico`
- **Beschreibung**: CallDoc-SQLHK Synchronisierung

## Verwendung

### Starten der Anwendung

Die Anwendung kann auf zwei Arten gestartet werden:

1. **Über den Desktop-Shortcut**: Doppelklick auf den Desktop-Shortcut "CallDocSQLHKSync"
2. **Direkt über die EXE-Datei**: Doppelklick auf `dist/CallDocSQLHKSync.exe`

### Voraussetzungen

Die Anwendung benötigt Zugriff auf den SQL-Server unter der IP-Adresse 192.168.1.67:7007. Stellen Sie sicher, dass:

1. Der Zielcomputer Netzwerkzugriff auf den SQL-Server hat
2. Die Firewall-Einstellungen den Zugriff auf den SQL-Server erlauben
3. Die notwendigen Berechtigungen für den Datenbankzugriff vorhanden sind

## Entwicklungswerkzeuge

### Icon-Generator

Ein Python-Skript `create_icon.py` wurde erstellt, um das benutzerdefinierte Icon zu generieren. Das Skript verwendet die Pillow-Bibliothek, um ein Icon mit verschiedenen Größen zu erstellen.

### Shortcut-Generator

Ein PowerShell-Skript `create_shortcut.ps1` wurde erstellt, um den Desktop-Shortcut zu generieren. Das Skript verwendet die WScript.Shell-COM-Komponente, um einen Shortcut mit dem benutzerdefinierten Icon zu erstellen.

## Bekannte Probleme

Keine bekannten Probleme in dieser Version.

## Nächste Schritte

- Weitere Verbesserungen der Benutzeroberfläche
- Erweiterung der Synchronisierungsfunktionen
- Optimierung der Datenbankabfragen

## Versionsverlauf

- **Version 8.0** (04.08.2025): Korrektur der dynamischen Feldzuordnung, eigenständige EXE-Datei, benutzerdefiniertes Icon
- **Version 7.0**: Verbessertes Logging-System
- **Version 6.0**: Korrektur der Datumsfilterung
- **Version 5.0**: Korrektur der SQL-Server-Verbindung
- **Version 4.0**: GUI-Verbesserungen und Standardauswahl des Termintyps "Herzkatheteruntersuchung"
- **Version 3.0**: Erfolgreiche Implementierung der Synchronisierung
- **Version 2.0**: Erweiterung der Funktionalitäten
- **Version 1.0**: Erste Version mit grundlegenden Funktionen
