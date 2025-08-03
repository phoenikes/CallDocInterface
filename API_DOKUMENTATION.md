# CallDoc-SQLHK Synchronisierung API

## Übersicht

Diese Dokumentation beschreibt die REST-API für die CallDoc-SQLHK Synchronisierung. Die API ermöglicht die Integration mit anderen Systemen und bietet Funktionen zur Steuerung der Synchronisierung, Abfrage des Status und Konfiguration des Schedulers.

## API-Server starten

Der API-Server kann auf zwei Arten gestartet werden:

1. **Über die GUI**: Verwenden Sie das Menü "API" > "API-Server starten" in der CallDoc-SQLHK Synchronisierungs-GUI.
2. **Über die Kommandozeile**: Führen Sie das folgende Skript aus:

```bash
python api_server.py
```

## Authentifizierung

Alle API-Endpunkte (außer `/api/health`) erfordern eine Authentifizierung mittels API-Schlüssel. Der API-Schlüssel muss im HTTP-Header `X-API-Key` übergeben werden.

Den API-Schlüssel können Sie in der GUI unter "API" > "API-Schlüssel anzeigen" einsehen oder generieren.

## API-Endpunkte

### Health

#### GET /api/health

Prüft, ob der API-Server läuft.

**Antwort:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### GET /api/health/connection

Prüft den Verbindungsstatus zu CallDoc und SQLHK.

**Antwort:**
```json
{
  "calldoc": {
    "status": "connected",
    "message": "Verbindung zu CallDoc hergestellt"
  },
  "sqlhk": {
    "status": "connected",
    "message": "Verbindung zu SQLHK hergestellt"
  }
}
```

### Synchronisierung

#### POST /api/sync

Startet eine manuelle Synchronisierung.

**Request:**
```json
{
  "date": "2025-08-03",
  "appointment_type_id": 24,
  "delete_obsolete": true
}
```

**Antwort:**
```json
{
  "task_id": "sync-2025-08-03-123456",
  "status": "started",
  "message": "Synchronisierung gestartet"
}
```

#### GET /api/sync/status/{task_id}

Ruft den Status einer laufenden Synchronisierung ab.

**Antwort:**
```json
{
  "task_id": "sync-2025-08-03-123456",
  "status": "completed",
  "result": {
    "appointments": {
      "total": 10,
      "processed": 10,
      "errors": 0
    },
    "patients": {
      "inserted": 2,
      "updated": 5,
      "errors": 0
    },
    "examinations": {
      "inserted": 3,
      "updated": 7,
      "deleted": 0,
      "errors": 0
    }
  }
}
```

#### GET /api/sync/history

Ruft den Verlauf der Synchronisierungen ab.

**Antwort:**
```json
{
  "history": [
    {
      "task_id": "sync-2025-08-03-123456",
      "date": "2025-08-03",
      "start_time": "2025-08-03T10:15:30",
      "end_time": "2025-08-03T10:16:45",
      "status": "completed",
      "summary": {
        "appointments": 10,
        "patients_inserted": 2,
        "patients_updated": 5,
        "examinations_inserted": 3,
        "examinations_updated": 7,
        "examinations_deleted": 0
      }
    }
  ]
}
```

### Scheduler

#### GET /api/scheduler/status

Ruft den Status des Synchronisierungs-Schedulers ab.

**Antwort:**
```json
{
  "enabled": true,
  "next_run": "2025-08-03T12:00:00",
  "last_run": "2025-08-03T11:00:00",
  "config": {
    "interval_minutes": 60,
    "start_time": "08:00",
    "end_time": "18:00",
    "days": [1, 2, 3, 4, 5]
  }
}
```

#### PUT /api/scheduler/config

Aktualisiert die Konfiguration des Schedulers.

**Request:**
```json
{
  "enabled": true,
  "interval_minutes": 60,
  "start_time": "08:00",
  "end_time": "18:00",
  "days": [1, 2, 3, 4, 5]
}
```

**Antwort:**
```json
{
  "status": "updated",
  "message": "Scheduler-Konfiguration aktualisiert",
  "config": {
    "enabled": true,
    "interval_minutes": 60,
    "start_time": "08:00",
    "end_time": "18:00",
    "days": [1, 2, 3, 4, 5]
  }
}
```

#### POST /api/scheduler/start

Startet den Scheduler.

**Antwort:**
```json
{
  "status": "started",
  "message": "Scheduler gestartet",
  "next_run": "2025-08-03T12:00:00"
}
```

#### POST /api/scheduler/stop

Stoppt den Scheduler.

**Antwort:**
```json
{
  "status": "stopped",
  "message": "Scheduler gestoppt"
}
```

### Daten

#### GET /api/data/appointments

Ruft CallDoc-Termine ab.

**Parameter:**
- `date` (optional): Datum im Format YYYY-MM-DD
- `appointment_type_id` (optional): ID des Termintyps
- `limit` (optional): Maximale Anzahl der Ergebnisse
- `offset` (optional): Offset für Paginierung

**Antwort:**
```json
{
  "appointments": [
    {
      "id": 12345,
      "patient": {
        "id": 67890,
        "first_name": "Max",
        "last_name": "Mustermann",
        "date_of_birth": "1970-01-01"
      },
      "scheduled_for": "2025-08-03T10:00:00",
      "type": {
        "id": 24,
        "name": "Herzkatheteruntersuchung"
      },
      "status": "confirmed"
    }
  ],
  "total": 10,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/data/appointments/{id}

Ruft einen bestimmten CallDoc-Termin ab.

**Antwort:**
```json
{
  "id": 12345,
  "patient": {
    "id": 67890,
    "first_name": "Max",
    "last_name": "Mustermann",
    "date_of_birth": "1970-01-01"
  },
  "scheduled_for": "2025-08-03T10:00:00",
  "type": {
    "id": 24,
    "name": "Herzkatheteruntersuchung"
  },
  "status": "confirmed",
  "notes": "Patient hat Herzrhythmusstörungen",
  "created_at": "2025-07-30T14:25:00",
  "updated_at": "2025-07-31T09:15:00"
}
```

#### GET /api/data/examinations

Ruft SQLHK-Untersuchungen ab.

**Parameter:**
- `date` (optional): Datum im Format YYYY-MM-DD
- `examination_type_id` (optional): ID des Untersuchungstyps
- `limit` (optional): Maximale Anzahl der Ergebnisse
- `offset` (optional): Offset für Paginierung

**Antwort:**
```json
{
  "examinations": [
    {
      "id": 54321,
      "patient": {
        "id": 98765,
        "first_name": "Erika",
        "last_name": "Musterfrau",
        "date_of_birth": "1975-05-15"
      },
      "scheduled_for": "2025-08-03T14:30:00",
      "type": {
        "id": 2,
        "name": "Herzkatheteruntersuchung"
      },
      "status": "scheduled"
    }
  ],
  "total": 5,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/data/examinations/{id}

Ruft eine bestimmte SQLHK-Untersuchung ab.

**Antwort:**
```json
{
  "id": 54321,
  "patient": {
    "id": 98765,
    "first_name": "Erika",
    "last_name": "Musterfrau",
    "date_of_birth": "1975-05-15"
  },
  "scheduled_for": "2025-08-03T14:30:00",
  "type": {
    "id": 2,
    "name": "Herzkatheteruntersuchung"
  },
  "status": "scheduled",
  "notes": "Patientin hat Bluthochdruck",
  "created_at": "2025-08-01T10:20:00",
  "updated_at": "2025-08-02T11:45:00",
  "calldoc_appointment_id": 12345
}
```

## Fehlerbehandlung

Die API gibt bei Fehlern entsprechende HTTP-Statuscodes zurück:

- `400 Bad Request`: Ungültige Anfrage
- `401 Unauthorized`: Fehlender oder ungültiger API-Schlüssel
- `404 Not Found`: Ressource nicht gefunden
- `500 Internal Server Error`: Interner Serverfehler

Beispiel für eine Fehlerantwort:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Ungültiges Datum. Bitte verwenden Sie das Format YYYY-MM-DD."
  }
}
```

## API-Konfiguration

Die API-Konfiguration kann in der GUI unter "API" > "API-Port konfigurieren" angepasst werden. Standardmäßig läuft der API-Server auf Port 8080 und bindet an alle Netzwerkschnittstellen (0.0.0.0).

Die API-Dokumentation (Swagger UI) ist unter `/api/docs` verfügbar, wenn der API-Server läuft.
