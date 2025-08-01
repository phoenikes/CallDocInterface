"""
Synchronisierungsplan für CallDoc-Untersuchungen mit der SQLHK-Datenbank

Dieses Modul beschreibt den Gesamtplan für die Synchronisierung von Untersuchungsdaten
zwischen dem CallDoc-System und der SQLHK-Datenbank. Es dient als Übersicht und Roadmap
für die Implementierung.

Hauptziel:
- Abfrage von CallDoc für einen auswählbaren Tag
- Vergleich dieser Informationen mit den Daten in der SQLHK-Datenbank (Tabelle Untersuchung)
- Synchronisierung: Neue Einträge hinzufügen, bestehende aktualisieren, nicht mehr vorhandene löschen

Autor: Markus
Datum: 31.07.2025
"""

# Gesamtplan für die Synchronisierung

"""
# 1. Überblick und Architektur

## 1.1 Systemkomponenten
- CallDoc API: Quelle für Untersuchungs- und Patientendaten
- MS SQL Server API: Schnittstelle zur SQLHK-Datenbank
- Synchronisierungsmodul: Vergleicht und synchronisiert Daten zwischen beiden Systemen

## 1.2 Datenfluss
1. Abfrage der Untersuchungstermine von CallDoc für einen bestimmten Tag
2. Abfrage der vorhandenen Untersuchungen aus der SQLHK-Datenbank für denselben Tag
3. Vergleich der Datensätze und Identifizierung von:
   - Neuen Untersuchungen (in CallDoc, nicht in SQLHK)
   - Zu aktualisierenden Untersuchungen (in beiden Systemen, aber mit Unterschieden)
   - Zu löschenden Untersuchungen (in SQLHK, nicht mehr in CallDoc)
4. Durchführung der entsprechenden Datenbankoperationen (INSERT, UPDATE, DELETE)

# 2. Teilprojekte und Meilensteine

## 2.1 CallDoc-Schnittstelle (bereits implementiert)
- CallDocInterface-Klasse für die Kommunikation mit der CallDoc API
- Methoden für Terminsuche und Patientendatenabfrage

## 2.2 MS SQL Server API-Schnittstelle (zu implementieren)
- MsSqlApiClient-Klasse für die Kommunikation mit der MS SQL Server API
- Methoden für SQL-Ausführung und Upsert-Operationen
- Spezifische Methoden für die Untersuchungstabelle

## 2.3 Datenmodell-Mapping (zu implementieren)
- Mapping zwischen CallDoc-Termindaten und SQLHK-Untersuchungsdaten
- Konvertierungsfunktionen für Datenformate und -strukturen

## 2.4 Synchronisierungslogik (zu implementieren)
- UntersuchungSynchronizer-Klasse für den Vergleich und die Synchronisierung
- Algorithmen für die Identifizierung von Unterschieden
- Transaktionsmanagement für atomare Operationen

## 2.5 Benutzeroberfläche (zu implementieren)
- Einfache GUI oder Kommandozeilen-Interface für die Auswahl des Datums
- Anzeige des Synchronisierungsstatus und der Ergebnisse
- Protokollierung der durchgeführten Aktionen

# 3. Implementierungsplan

## 3.1 Phase 1: Grundlagen und Infrastruktur
- Implementierung der MS SQL Server API-Schnittstelle
- Erstellung des Datenmodell-Mappings
- Einrichtung der Logging-Infrastruktur

## 3.2 Phase 2: Kernfunktionalität
- Implementierung der Synchronisierungslogik
- Entwicklung der Vergleichsalgorithmen
- Implementierung der Datenbankoperationen

## 3.3 Phase 3: Benutzeroberfläche und Tests
- Entwicklung der Benutzeroberfläche
- Umfassende Tests mit verschiedenen Szenarien
- Fehlerbehandlung und Robustheit

## 3.4 Phase 4: Dokumentation und Deployment
- Erstellung der Benutzerdokumentation
- Erstellung der technischen Dokumentation
- Vorbereitung des Deployments

# 4. Technische Details

## 4.1 Datenbankschema (SQLHK.Untersuchung)
Die Tabelle 'Untersuchung' in der SQLHK-Datenbank enthält folgende relevante Felder:
- UntersuchungID (Primärschlüssel)
- PatientID (Fremdschlüssel zur Tabelle Patient)
- UntersuchungartID (Fremdschlüssel zur Tabelle Untersuchungart)
- Datum (Datum der Untersuchung)
- Zeit (Uhrzeit der Untersuchung)
- Bemerkung
- Status
- ... (weitere Felder)

## 4.2 CallDoc-Terminstruktur
Die CallDoc-API liefert Termine mit folgenden relevanten Feldern:
- appointment_id (eindeutige ID des Termins)
- piz (Patienten-ID)
- appointment_type_id (Art des Termins)
- date (Datum des Termins)
- time (Uhrzeit des Termins)
- notes (Bemerkungen)
- status (Status des Termins)
- ... (weitere Felder)

## 4.3 Mapping zwischen CallDoc und SQLHK
- appointment_id → externe_id (für Referenz)
- piz → PatientID (nach Mapping)
- appointment_type_id → UntersuchungartID (nach Mapping)
- date → Datum
- time → Zeit
- notes → Bemerkung
- status → Status (nach Mapping)

# 5. Nächste Schritte

## 5.1 Unmittelbare Aufgaben
1. Implementierung der MsSqlApiClient-Klasse
2. Erstellung des Datenmodell-Mappings
3. Implementierung der grundlegenden Synchronisierungslogik

## 5.2 Offene Fragen
- Wie sollen Konflikte bei der Synchronisierung behandelt werden?
- Welche Felder sind für den Vergleich maßgeblich?
- Wie soll mit fehlenden Patienten oder Untersuchungsarten umgegangen werden?

## 5.3 Risiken und Herausforderungen
- Unterschiedliche Datenstrukturen und -formate
- Netzwerklatenz und API-Verfügbarkeit
- Datenkonsistenz und Transaktionssicherheit

# 6. Technische Erkenntnisse und Best Practices

## 6.1 Datenbankabfragen und Kontextwechsel

### 6.1.1 Patientenabfrage mit Datenbankwechsel
Bei der Abfrage von Patientendaten aus der SQLHK-Datenbank haben wir wichtige Erkenntnisse gewonnen:

1. **Mehrschrittige Abfragen erforderlich**: Die Abfrage von Patientendaten erfordert einen expliziten Wechsel zur SQLHK-Datenbank, gefolgt von der eigentlichen Abfrage und einem Rückwechsel zur SuPDatabase.

2. **Trennung der SQL-Befehle**: Die SQL-Befehle müssen in separaten API-Aufrufen ausgeführt werden:
   - Erster Aufruf: `USE SQLHK;`
   - Zweiter Aufruf: `SELECT * FROM dbo.Patient WHERE PatientID = X;`
   - Dritter Aufruf: `USE SuPDatabase;`

3. **Fehlerbehandlung**: Bei jedem Schritt muss eine angemessene Fehlerbehandlung implementiert werden, insbesondere um sicherzustellen, dass der Rückwechsel zur SuPDatabase auch im Fehlerfall erfolgt.

4. **M1Ziffer als Schlüssel**: Die M1Ziffer im Patientendatensatz ist der Schlüssel für die Zuordnung zwischen SQLHK und CallDoc (entspricht der PIZ in CallDoc).

### 6.1.2 Implementierte Lösung
Die Funktion `get_patient_by_id` in der Datei `patient_abfrage.py` demonstriert die korrekte Vorgehensweise:

```python
def get_patient_by_id(patient_id, server_url="http://localhost:7007"):
    """Ruft einen Patienten anhand seiner PatientID aus der SQLHK-Datenbank ab."""
    try:
        url = f"{server_url}/api/execute_sql"
        headers = {"Content-Type": "application/json"}
        
        # Schritt 1: Zur SQLHK-Datenbank wechseln
        switch_query = "USE SQLHK;"
        switch_payload = {"query": switch_query, "database": "SQLHK"}
        switch_response = requests.post(url, json=switch_payload, headers=headers)
        
        # Schritt 2: Patientendaten abfragen
        patient_query = f"SELECT * FROM dbo.Patient WHERE PatientID = {patient_id}"
        patient_payload = {"query": patient_query, "database": "SQLHK"}
        patient_response = requests.post(url, json=patient_payload, headers=headers)
        patient_result = patient_response.json()
        
        # Schritt 3: Zurück zur SuPDatabase wechseln
        back_query = "USE SuPDatabase;"
        back_payload = {"query": back_query, "database": "SQLHK"}
        back_response = requests.post(url, json=back_payload, headers=headers)
        
        # Ergebnis verarbeiten...
    except Exception:
        # Fehlerbehandlung mit Rückwechsel zur SuPDatabase...
```

Diese Erkenntnisse sind entscheidend für die korrekte Implementierung der Synchronisierungslogik zwischen CallDoc und der SQLHK-Datenbank.
"""
