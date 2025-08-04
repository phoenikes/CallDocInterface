# CallDoc-SQLHK API Anleitung

## Übersicht

Die CallDoc-SQLHK Synchronisierungs-API ermöglicht die Fernsteuerung der Synchronisierungsfunktionen und den Zugriff auf Daten über eine REST-Schnittstelle. Diese Anleitung erklärt die Einrichtung, Konfiguration und Verwendung der API.

## Inhaltsverzeichnis

1. [API-Server starten](#api-server-starten)
2. [API-Konfiguration](#api-konfiguration)
3. [API-Schlüssel verwalten](#api-schlüssel-verwalten)
4. [API-Dokumentation](#api-dokumentation)
5. [Beispiele für API-Aufrufe](#beispiele-für-api-aufrufe)
6. [Fehlerbehebung](#fehlerbehebung)

## API-Server starten

### Über die GUI

1. Starte die CallDoc-SQLHK Synchronisierungs-GUI:
   ```
   python sync_gui_qt.py
   ```

2. Wähle im Menü "API" > "API-Server starten"

3. Der Server wird im Hintergrund gestartet und eine Meldung im Log-Bereich bestätigt den erfolgreichen Start

### Über die Kommandozeile

Der API-Server kann auch direkt über die Kommandozeile gestartet werden:

```
python api_server.py
```

## API-Konfiguration

### Host und Port konfigurieren

1. Öffne in der GUI das Menü "API" > "API-Port konfigurieren"
2. Gib den gewünschten Port ein (Standard: 8080)
3. Bestätige mit "OK"

Die Konfiguration wird in der `config.ini` Datei gespeichert und beim nächsten Start automatisch geladen.

### Manuelle Konfiguration

Die API-Konfiguration kann auch direkt in der `config.ini` Datei bearbeitet werden:

```ini
[API_SERVER]
HOST = 0.0.0.0
PORT = 8080
API_KEY = dein_api_schlüssel
```

## API-Schlüssel verwalten

### API-Schlüssel anzeigen

1. Öffne in der GUI das Menü "API" > "API-Schlüssel anzeigen"
2. Der API-Schlüssel wird in einem Dialog angezeigt
3. Klicke auf "Kopieren", um den Schlüssel in die Zwischenablage zu kopieren

### API-Schlüssel neu generieren

1. Öffne in der GUI das Menü "API" > "API-Schlüssel anzeigen"
2. Klicke auf "Neu generieren"
3. Bestätige die Sicherheitsabfrage
4. Der neue API-Schlüssel wird angezeigt und in der Konfiguration gespeichert

**Wichtig:** Nach der Neugenerierung des API-Schlüssels müssen alle Anwendungen, die die API verwenden, mit dem neuen Schlüssel aktualisiert werden.

## API-Dokumentation

### Swagger UI

Die interaktive API-Dokumentation ist verfügbar, wenn der API-Server läuft:

1. Starte den API-Server wie oben beschrieben
2. Öffne in der GUI das Menü "API" > "API-Dokumentation öffnen"
3. Alternativ kannst du die URL direkt in deinem Browser öffnen: `http://localhost:8080/api/docs`

### Markdown-Dokumentation

Eine ausführliche Dokumentation aller API-Endpunkte findest du in der Datei `API_DOKUMENTATION.md`.

## Beispiele für API-Aufrufe

### Gesundheitsstatus abfragen

```python
import requests

# Health-Endpunkt (keine Authentifizierung erforderlich)
response = requests.get("http://localhost:8080/api/health")
print(response.json())

# Verbindungsstatus abfragen (Authentifizierung erforderlich)
api_key = "dein_api_schlüssel"
headers = {"X-API-Key": api_key}
response = requests.get("http://localhost:8080/api/health/connection", headers=headers)
print(response.json())
```

### Synchronisierung starten

```python
import requests
import json

api_key = "dein_api_schlüssel"
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

data = {
    "date": "2025-08-03",
    "appointment_type_id": 24,
    "delete_obsolete": True
}

response = requests.post(
    "http://localhost:8080/api/sync",
    headers=headers,
    data=json.dumps(data)
)

print(response.json())
```

### Scheduler-Status abfragen

```python
import requests

api_key = "dein_api_schlüssel"
headers = {"X-API-Key": api_key}

response = requests.get("http://localhost:8080/api/scheduler/status", headers=headers)
print(response.json())
```

### Termine abrufen

```python
import requests

api_key = "dein_api_schlüssel"
headers = {"X-API-Key": api_key}

# Parameter für die Abfrage
params = {
    "date": "2025-08-03",
    "appointment_type_id": 24,
    "limit": 10,
    "offset": 0
}

response = requests.get(
    "http://localhost:8080/api/data/appointments",
    headers=headers,
    params=params
)

print(response.json())
```

## Fehlerbehebung

### API-Server startet nicht

1. Überprüfe, ob der Port bereits verwendet wird:
   ```
   netstat -ano | findstr :8080
   ```

2. Überprüfe die Logs in der GUI oder in der Konsole auf Fehlermeldungen

3. Stelle sicher, dass alle erforderlichen Abhängigkeiten installiert sind:
   ```
   pip install fastapi uvicorn
   ```

### Authentifizierungsfehler

1. Überprüfe, ob der API-Schlüssel korrekt ist
2. Stelle sicher, dass der API-Schlüssel im Header `X-API-Key` übergeben wird
3. Generiere bei Bedarf einen neuen API-Schlüssel

### Verbindungsprobleme

1. Überprüfe, ob der API-Server läuft
2. Stelle sicher, dass die Firewall den Zugriff auf den konfigurierten Port erlaubt
3. Überprüfe die Verbindung zu CallDoc und SQLHK über den Health-Endpunkt

## Support

Bei Fragen oder Problemen mit der API wende dich an das Entwicklungsteam der Praxis Heydoc.
