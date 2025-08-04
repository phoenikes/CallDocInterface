# Dokumentation: CallDoc-SQLHK Synchronisierung v3.0

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Projektübersicht](#projektübersicht)
3. [Systemarchitektur](#systemarchitektur)
4. [Komponenten](#komponenten)
   - [CallDocInterface](#calldocinterface)
   - [MsSqlApiClient](#mssqlapiclient)
   - [PatientSynchronizer](#patientsynchronizer)
   - [UntersuchungSynchronizer](#untersuchungsynchronizer)
   - [CallDocSQLHKSynchronizer](#calldocsqlhksynchronizer)
5. [Synchronisierungsprozess](#synchronisierungsprozess)
   - [Schritt 1: Abrufen der CallDoc-Termine](#schritt-1-abrufen-der-calldoc-termine)
   - [Schritt 2: Abrufen der SQLHK-Untersuchungen](#schritt-2-abrufen-der-sqlhk-untersuchungen)
   - [Schritt 3: Synchronisieren der Patienten](#schritt-3-synchronisieren-der-patienten)
   - [Schritt 4: Synchronisieren der Untersuchungen](#schritt-4-synchronisieren-der-untersuchungen)
   - [Schritt 5: Löschen obsoleter Untersuchungen](#schritt-5-löschen-obsoleter-untersuchungen)
6. [Implementierungsdetails](#implementierungsdetails)
   - [Datenmodell-Mapping](#datenmodell-mapping)
   - [Fehlerbehandlung](#fehlerbehandlung)
   - [Logging](#logging)
7. [Testergebnisse](#testergebnisse)
8. [Bekannte Einschränkungen](#bekannte-einschränkungen)
9. [Zukünftige Erweiterungen](#zukünftige-erweiterungen)
10. [Anhang](#anhang)

## Einführung

Die CallDoc-SQLHK Synchronisierung ist ein System zur automatisierten Synchronisierung von Termindaten aus dem CallDoc-System mit Untersuchungsdaten in der SQLHK-Datenbank. Das System wurde entwickelt, um den manuellen Aufwand bei der Datenpflege zu reduzieren und die Konsistenz zwischen beiden Systemen sicherzustellen.

Diese Dokumentation beschreibt die Version 3.0 der Synchronisierungslösung, die erfolgreich für mehrere Tage getestet wurde und die Funktionen zum Einfügen, Aktualisieren und Löschen von Untersuchungen bietet.

## Projektübersicht

Das Projekt CallDocInterface hat folgende Hauptziele:

1. Automatisierte Synchronisierung von Untersuchungsdaten zwischen dem CallDoc-System und der SQLHK-Datenbank
2. Implementierung eines zuverlässigen Workflows: Abfrage CallDoc für einen Tag → Vergleich mit Datenbank → Synchronisierung (Hinzufügen/Aktualisieren/Löschen)
3. Sicherstellung der Datenintegrität und -konsistenz zwischen beiden Systemen
4. Minimierung des manuellen Aufwands bei der Datenpflege

## Systemarchitektur

Die Systemarchitektur basiert auf einem modularen Ansatz mit mehreren Komponenten, die jeweils spezifische Aufgaben übernehmen:

```
+----------------+      +----------------+      +-------------------+
| CallDoc-System | <--> | CallDocInterface| <--> | PatientSynchronizer|
+----------------+      +----------------+      +-------------------+
                              ^                          ^
                              |                          |
                              v                          v
                        +------------------+     +---------------------+
                        |CallDocSQLHKSynchronizer| <--> |UntersuchungSynchronizer|
                        +------------------+     +---------------------+
                                                          ^
                                                          |
                                                          v
                        +----------------+      +------------------+
                        | SQLHK-Datenbank| <--> | MsSqlApiClient   |
                        +----------------+      +------------------+
```

## Komponenten

### CallDocInterface

Die `CallDocInterface`-Klasse ist für die Kommunikation mit dem CallDoc-System verantwortlich. Sie bietet Methoden zum Abrufen von Termindaten für einen bestimmten Zeitraum.

Hauptfunktionen:
- Initialisierung mit Datumsbereich
- Abrufen von Terminen nach verschiedenen Kriterien
- Filterung von Terminen nach Typ, Status, Arzt, etc.
- Fehlerbehandlung bei API-Anfragen

### MsSqlApiClient

Der `MsSqlApiClient` ist für die Kommunikation mit der SQLHK-Datenbank über eine REST-API verantwortlich. Er bietet Methoden zum Abfragen, Einfügen, Aktualisieren und Löschen von Datensätzen.

Hauptfunktionen:
- Ausführen von SQL-Abfragen
- Upsert-Operationen (Einfügen oder Aktualisieren)
- Löschen von Datensätzen
- Fehlerbehandlung bei API-Anfragen

### PatientSynchronizer

Der `PatientSynchronizer` ist für die Synchronisierung von Patientendaten zwischen CallDoc und SQLHK verantwortlich. Er extrahiert Patientendaten aus CallDoc-Terminen und synchronisiert sie mit der SQLHK-Datenbank.

Hauptfunktionen:
- Extraktion von Patientendaten aus Terminen
- Überprüfung, ob ein Patient bereits existiert
- Einfügen oder Aktualisieren von Patientendaten
- Sammeln von Statistiken über die Synchronisierung

### UntersuchungSynchronizer

Der `UntersuchungSynchronizer` ist für die Synchronisierung von Untersuchungsdaten zwischen CallDoc und SQLHK verantwortlich. Er extrahiert Untersuchungsdaten aus CallDoc-Terminen und synchronisiert sie mit der SQLHK-Datenbank.

Hauptfunktionen:
- Extraktion von Untersuchungsdaten aus Terminen
- Überprüfung, ob eine Untersuchung bereits existiert
- Einfügen oder Aktualisieren von Untersuchungsdaten
- Löschen obsoleter Untersuchungen
- Sammeln von Statistiken über die Synchronisierung

### CallDocSQLHKSynchronizer

Der `CallDocSQLHKSynchronizer` ist die Hauptklasse, die den gesamten Synchronisierungsprozess koordiniert. Er verwendet die anderen Komponenten, um Termine abzurufen, zu vergleichen und zu synchronisieren.

Hauptfunktionen:
- Abrufen von CallDoc-Terminen für ein bestimmtes Datum
- Intelligente Statusfilterung basierend auf dem Datum
- Flexible Filterung nach Termintyp, Arzt, Raum und Status
- Detaillierte Analyse der Terminverteilung
- Vergleich zwischen CallDoc-Terminen und SQLHK-Untersuchungen
- Export der Ergebnisse als JSON und CSV

## Synchronisierungsprozess

Der Synchronisierungsprozess besteht aus mehreren Schritten, die in einer bestimmten Reihenfolge ausgeführt werden:

### Schritt 1: Abrufen der CallDoc-Termine

Im ersten Schritt werden die CallDoc-Termine für das gewünschte Datum abgerufen. Dabei werden nur Termine vom Typ "HERZKATHETERUNTERSUCHUNG" berücksichtigt. Die Termine werden nach Status gefiltert, wobei die Filterung je nach Datum unterschiedlich ist:

- Für vergangene Termine: Nur abgeschlossene Termine werden berücksichtigt
- Für zukünftige Termine: Alle aktiven Termine werden berücksichtigt

Die abgerufenen Termine werden als JSON-Datei gespeichert, um sie später analysieren zu können.

### Schritt 2: Abrufen der SQLHK-Untersuchungen

Im zweiten Schritt werden die SQLHK-Untersuchungen für das gewünschte Datum abgerufen. Dabei werden beide Datumsformate (ISO und deutsch) ausprobiert, um sicherzustellen, dass alle Untersuchungen gefunden werden.

Die abgerufenen Untersuchungen werden als JSON-Datei gespeichert, um sie später analysieren zu können.

### Schritt 3: Synchronisieren der Patienten

Im dritten Schritt werden die Patienten aus den CallDoc-Terminen mit der SQLHK-Datenbank synchronisiert. Für jeden Termin wird geprüft, ob der Patient bereits in der Datenbank existiert. Falls nicht, wird er eingefügt. Falls ja, werden die Daten aktualisiert.

Die Synchronisierung der Patienten ist ein wichtiger Vorbereitungsschritt für die Synchronisierung der Untersuchungen, da die Untersuchungen auf die Patienten verweisen.

### Schritt 4: Synchronisieren der Untersuchungen

Im vierten Schritt werden die Untersuchungen aus den CallDoc-Terminen mit der SQLHK-Datenbank synchronisiert. Für jeden Termin wird geprüft, ob bereits eine Untersuchung in der Datenbank existiert. Falls nicht, wird sie eingefügt. Falls ja, werden die Daten aktualisiert.

Bei der Synchronisierung werden verschiedene Daten aus dem Termin extrahiert und in die Untersuchung übernommen, wie z.B. Datum, Untersucher, Herzkatheter, Untersuchungsart, etc.

### Schritt 5: Löschen obsoleter Untersuchungen

Im fünften Schritt werden obsolete Untersuchungen in der SQLHK-Datenbank identifiziert und gelöscht. Eine Untersuchung gilt als obsolet, wenn sie in der Datenbank existiert, aber kein entsprechender aktiver Termin in CallDoc vorhanden ist.

Das Löschen erfolgt nur für zukünftige Termine, um zu verhindern, dass historische Daten versehentlich gelöscht werden.

## Implementierungsdetails

### Datenmodell-Mapping

Ein wichtiger Aspekt der Synchronisierung ist das Mapping zwischen den Datenmodellen von CallDoc und SQLHK. Die folgende Tabelle zeigt die wichtigsten Mappings:

| CallDoc-Feld | SQLHK-Feld | Beschreibung |
|--------------|------------|--------------|
| scheduled_for_datetime | Datum | Datum und Uhrzeit des Termins |
| employee_id | UntersucherAbrechnungID | ID des Untersuchers |
| room_id | HerzkatheterID | ID des Herzkatheters |
| appointment_type_id | UntersuchungartID | ID der Untersuchungsart |
| patient_id | PatientID | ID des Patienten |

Für einige Felder ist eine Umwandlung erforderlich, z.B. muss die employee_id in eine UntersucherAbrechnungID umgewandelt werden. Dafür werden entsprechende Lookup-Tabellen in der Datenbank verwendet.

### Fehlerbehandlung

Die Synchronisierung enthält umfangreiche Fehlerbehandlung, um mit verschiedenen Fehlersituationen umzugehen:

- Fehlende Pflichtfelder in Terminen werden erkannt und geloggt
- Fehler bei API-Anfragen werden abgefangen und geloggt
- Bei fehlenden Referenzdaten (z.B. UntersucherAbrechnungID) werden Standardwerte verwendet
- Alle Fehler werden in den Logs dokumentiert und in den Statistiken gezählt

### Logging

Die Synchronisierung verwendet das Python-Logging-System, um detaillierte Informationen über den Ablauf zu protokollieren:

- INFO-Level: Allgemeine Informationen über den Ablauf
- DEBUG-Level: Detaillierte Informationen für die Fehlersuche
- WARNING-Level: Warnungen über potenzielle Probleme
- ERROR-Level: Fehler, die den Ablauf beeinträchtigen

Die Logs werden sowohl in der Konsole ausgegeben als auch in Dateien gespeichert, um sie später analysieren zu können.

## Testergebnisse

Die Synchronisierung wurde für mehrere Tage getestet und hat in allen Fällen korrekt funktioniert:

| Datum      | Termine | Neue Patienten | Neue Untersuchungen | Aktualisierte Untersuchungen | Gelöschte Untersuchungen |
|------------|---------|----------------|---------------------|-----------------------------|-----------------------|
| 04.08.2025 | 17      | 0              | 7                   | 10                          | 0                     |
| 05.08.2025 | 8       | 8              | 8                   | 0                           | 0                     |
| 06.08.2025 | 30      | 0              | 0                   | 30                          | 0                     |
| 07.08.2025 | 27      | 27             | 27                  | 0                           | 0                     |
| 08.08.2025 | 20      | 20             | 20                  | 0                           | 0                     |

Die Tests haben verschiedene Szenarien abgedeckt:

- Tage mit bereits vorhandenen Untersuchungen, die aktualisiert werden müssen (04.08. und 06.08.)
- Tage mit komplett neuen Terminen, für die neue Untersuchungen angelegt werden müssen (05.08., 07.08. und 08.08.)

Die Löschlogik hat in allen Fällen korrekt gearbeitet - es wurden keine Untersuchungen gelöscht, da keine obsoleten Untersuchungen in der SQLHK-Datenbank vorhanden waren.

## Bekannte Einschränkungen

Die aktuelle Implementierung hat einige bekannte Einschränkungen:

1. Die Synchronisierung ist auf einen bestimmten Tag beschränkt und muss für jeden Tag separat ausgeführt werden
2. Die Löschlogik funktioniert nur für zukünftige Termine, nicht für vergangene
3. Bei fehlenden Referenzdaten werden Standardwerte verwendet, was zu unvollständigen Daten führen kann
4. Die Synchronisierung ist auf Termine vom Typ "HERZKATHETERUNTERSUCHUNG" beschränkt

## Zukünftige Erweiterungen

Für zukünftige Versionen sind folgende Erweiterungen geplant:

1. Implementierung einer Benutzeroberfläche für die Datumsauswahl
2. Unterstützung für die Synchronisierung mehrerer Tage in einem Durchlauf
3. Verbesserung der Fehlerbehandlung und Berichterstattung
4. Erweiterung der Synchronisierung auf andere Termintypen
5. Implementierung einer Kommandozeilenschnittstelle für die flexible Ausführung

## Anhang

### Beispiel-Synchronisierungsskript

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Synchronisierungsskript für CallDoc-Termine und SQLHK-Untersuchungen für den 06.08.2025.

Dieses Skript führt folgende Schritte aus:
1. Abrufen der CallDoc-Termine für den 06.08.2025
2. Abrufen der SQLHK-Untersuchungen für den 06.08.2025
3. Synchronisieren der Patienten aus den CallDoc-Terminen
4. Synchronisieren der Untersuchungen (inkl. Löschen obsoleter Untersuchungen)
5. Speichern der Ergebnisse in einer JSON-Datei
"""

import json
import logging
from datetime import datetime

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer
from calldoc_sqlhk_synchronizer import CallDocSQLHKSynchronizer
from constants import APPOINTMENT_TYPES

# Konfiguriere das Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Datum für die Synchronisierung (06.08.2025)
date_str = "2025-08-06"
date_str_de = "06.08.2025"

def main():
    logger.info(f"Starte Synchronisierung für Datum: {date_str} ({date_str_de})")
    
    # Initialisiere die Clients
    calldoc_client = CallDocInterface(from_date=date_str, to_date=date_str)
    mssql_client = MsSqlApiClient()
    
    # Initialisiere die Synchronizer
    patient_sync = PatientSynchronizer()
    untersuchung_sync = UntersuchungSynchronizer(
        calldoc_interface=calldoc_client, 
        mssql_client=mssql_client
    )
    synchronizer = CallDocSQLHKSynchronizer()
    
    try:
        # 1. CallDoc-Termine abrufen
        logger.info("1. CallDoc-Termine abrufen")
        calldoc_appointments = synchronizer.get_calldoc_appointments(
            date_str=date_str,
            filter_by_type_id=APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"],
            smart_status_filter=True
        )
        
        if not calldoc_appointments:
            logger.warning(f"Keine CallDoc-Termine für {date_str} gefunden.")
            return {"success": False, "error": "Keine Termine gefunden"}
        
        logger.info(f"{len(calldoc_appointments)} CallDoc-Termine gefunden.")
        
        # Termine als JSON speichern
        with open(f"calldoc_termine_{date_str}.json", "w", encoding="utf-8") as f:
            json.dump(calldoc_appointments, f, indent=2)
        
        # 2. SQLHK-Untersuchungen abrufen
        logger.info("2. SQLHK-Untersuchungen abrufen")
        sqlhk_untersuchungen = []
        
        # Versuche beide Datumsformate
        sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(date_str)
        if not sqlhk_untersuchungen:
            sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(date_str_de)
        
        logger.info(f"{len(sqlhk_untersuchungen)} SQLHK-Untersuchungen gefunden.")
        
        # Untersuchungen als JSON speichern
        with open(f"sqlhk_untersuchungen_{date_str}.json", "w", encoding="utf-8") as f:
            json.dump(sqlhk_untersuchungen, f, indent=2)
        
        # 3. Patienten synchronisieren
        logger.info("3. Patienten synchronisieren")
        patient_stats = patient_sync.synchronize_patients_from_appointments(calldoc_appointments)
        
        logger.info("Patienten-Synchronisierung abgeschlossen:")
        logger.info(f"  - Erfolgreiche Operationen: {patient_stats.get('success', 0)}")
        logger.info(f"  - Fehler: {patient_stats.get('errors', 0)}")
        logger.info(f"  - Eingefügt: {patient_stats.get('inserted', 0)}")
        logger.info(f"  - Aktualisiert: {patient_stats.get('updated', 0)}")
        
        # 4. Untersuchungen synchronisieren
        logger.info("4. Untersuchungen synchronisieren")
        
        # Zuerst das Mapping von Termintypen zu Untersuchungsarten laden
        untersuchung_sync.load_appointment_type_mapping()
        
        # Dann die Synchronisierung durchführen
        result = untersuchung_sync.synchronize_appointments(
            calldoc_appointments,
            sqlhk_untersuchungen
        )
        
        # Ausgabe der Ergebnisse
        logger.info("Untersuchungs-Synchronisierung abgeschlossen:")
        logger.info(f"  - Erfolgreiche Operationen: {result.get('success', 0)}")
        logger.info(f"  - Fehler: {result.get('errors', 0)}")
        logger.info(f"  - Eingefügt: {result.get('inserted', 0)}")
        logger.info(f"  - Aktualisiert: {result.get('updated', 0)}")
        logger.info(f"  - Gelöscht: {result.get('deleted', 0)}")
        
        # Speichere die Ergebnisse in einer JSON-Datei
        with open(f"sync_result_{date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Synchronisierung für {date_str} ({date_str_de}) abgeschlossen")
        return result
    except Exception as e:
        logger.error(f"Fehler bei der Synchronisierung: {str(e)}")
        import traceback
        logger.error(f"Stacktrace: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    main()
```

### Entwicklungsschritte

Die Entwicklung der CallDoc-SQLHK Synchronisierung erfolgte in mehreren Schritten:

1. **Analyse der Anforderungen**
   - Identifikation der zu synchronisierenden Daten
   - Definition der Synchronisierungslogik
   - Festlegung der Fehlerbehandlung

2. **Implementierung der Basiskomponenten**
   - Entwicklung des CallDocInterface
   - Entwicklung des MsSqlApiClient
   - Implementierung der Logging-Funktionalität

3. **Implementierung der Synchronisierungslogik**
   - Entwicklung des PatientSynchronizer
   - Entwicklung des UntersuchungSynchronizer
   - Implementierung der Löschlogik

4. **Integration und Tests**
   - Integration der Komponenten
   - Tests mit verschiedenen Szenarien
   - Fehlerbehebung und Optimierung

5. **Dokumentation und Bereitstellung**
   - Erstellung der Dokumentation
   - Bereitstellung des Codes in Git
   - Schulung der Anwender

### Verwendete Technologien

- Python 3.12
- Requests (HTTP-Client)
- JSON (Datenaustauschformat)
- Logging (Protokollierung)
- Git (Versionskontrolle)

### Kontakt

Bei Fragen oder Problemen wenden Sie sich bitte an:

- Markus (Projektleiter)
- E-Mail: markus@example.com
