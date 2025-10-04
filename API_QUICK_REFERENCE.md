# 🚀 CallDoc-SQLHK API Quick Reference

## Base URL
```
http://localhost:5555
```

## Endpoints

### 1️⃣ Health Check
```http
GET /health
```

### 2️⃣ Single Patient Sync
```http
POST /api/sync/patient
Content-Type: application/json

{
    "piz": "1698369",           # Required: Patient ID
    "date": "2025-10-06",       # Required: YYYY-MM-DD
    "appointment_type_id": 24   # Optional: Default 24
}
```

### 3️⃣ Check Task Status
```http
GET /api/sync/status/{task_id}
```

### 4️⃣ List Active Tasks
```http
GET /api/sync/active
```

### 5️⃣ Full Day Sync
```http
POST /api/sync
Content-Type: application/json

{
    "date": "2025-10-06",       # Required: YYYY-MM-DD
    "appointment_type_id": 24   # Optional: Default 24
}
```

---

## Quick Examples

### Python - Minimal
```python
import requests

# Sync single patient
response = requests.post('http://localhost:5555/api/sync/patient', 
    json={'piz': '1698369', 'date': '2025-10-06'})
task_id = response.json()['task_id']

# Check status
status = requests.get(f'http://localhost:5555/api/sync/status/{task_id}')
print(status.json())
```

### PowerShell - One-Liner
```powershell
Invoke-RestMethod -Uri http://localhost:5555/api/sync/patient -Method POST -Body (@{piz='1698369';date='2025-10-06'} | ConvertTo-Json) -ContentType 'application/json'
```

### cURL - Quick Test
```bash
curl -X POST http://localhost:5555/api/sync/patient \
  -H "Content-Type: application/json" \
  -d '{"piz":"1698369","date":"2025-10-06"}'
```

### JavaScript - Fetch
```javascript
fetch('http://localhost:5555/api/sync/patient', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({piz: '1698369', date: '2025-10-06'})
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## Response Format

### Success (202 Accepted)
```json
{
    "message": "Single patient synchronization started",
    "task_id": "patient_sync_1698369_2025-10-06_24_20251004120000",
    "status_url": "/api/sync/status/patient_sync_1698369_2025-10-06_24_20251004120000"
}
```

### Task Completed
```json
{
    "status": "completed",
    "result": {
        "success": true,
        "message": "Single-Patient erfolgreich synchronisiert",
        "execution_time_ms": 2913,
        "patient": {"found": true, "name": "Wippel", "vorname": "Hermann"},
        "sqlhk_sync": {"action": "created", "untersuchung_id": 20369}
    }
}
```

### Error (400 Bad Request)
```json
{
    "error": "Missing required fields: date, piz"
}
```

---

## Status Values
- `pending` - Queued
- `running` - Processing
- `completed` - Success ✅
- `failed` - Error ❌

---

## Performance
- **Single Patient:** 2-4 seconds
- **Full Day:** 10-30 seconds
- **Timeout:** 60 seconds max

---

## Troubleshooting

```bash
# Check if API is running
curl http://localhost:5555/health

# View active syncs
curl http://localhost:5555/api/sync/active

# Check Windows service
tasklist | findstr CallDocSync

# Check port
netstat -an | findstr 5555
```

---

**Version:** 1.0.0 | **Port:** 5555 | **Author:** Markus | **Date:** 04.10.2025