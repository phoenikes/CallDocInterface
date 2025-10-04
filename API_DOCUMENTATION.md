# 📚 CallDoc-SQLHK Synchronization REST API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:5555`  
**Protocol:** HTTP/HTTPS  
**Format:** JSON  

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Single Patient Sync](#single-patient-sync)
   - [Full Day Sync](#full-day-sync)
   - [Task Status](#task-status)
   - [Active Tasks](#active-tasks)
5. [Response Codes](#response-codes)
6. [Error Handling](#error-handling)
7. [Examples](#examples)
8. [Performance](#performance)
9. [Integration Guide](#integration-guide)

> 🔥 **Siehe [API_EXAMPLES.md](API_EXAMPLES.md) für getestete, funktionierende Beispiele mit echten Daten vom 04.10.2025!**

---

## Overview

The CallDoc-SQLHK Synchronization API provides programmatic access to synchronize patient appointments between CallDoc (read-only source) and SQLHK (target database). The API runs integrated with the GUI application and automatically starts on port 5555.

### Key Features
- 🚀 Single-patient synchronization
- 📅 Full-day synchronization
- ⚡ Asynchronous task processing
- 📊 Real-time status monitoring
- 🔄 Automatic retry on failures

---

## Getting Started

### Prerequisites
1. **CallDocSyncWithAPI.exe** must be running
2. Network access to port 5555
3. Valid CallDoc and SQLHK database connections

### Quick Start

```bash
# 1. Start the application
CallDocSyncWithAPI.exe

# 2. Verify API is running
curl http://localhost:5555/health

# 3. Sync a single patient
curl -X POST http://localhost:5555/api/sync/patient \
  -H "Content-Type: application/json" \
  -d '{"piz":"1698369","date":"2025-10-06"}'
```

---

## Authentication

> **Note:** Currently, the API does not require authentication. For production use, consider implementing API keys or OAuth2.

---

## API Endpoints

### Health Check

Verify API status and availability.

**Endpoint:** `GET /health`

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-10-04T12:00:00.000000",
    "active_syncs": 0
}
```

**Status Codes:**
- `200 OK` - API is healthy
- `503 Service Unavailable` - API is not ready

---

### Single Patient Sync

Synchronize a single patient's appointments from CallDoc to SQLHK.

**Endpoint:** `POST /api/sync/patient`

**Request Body:**
```json
{
    "piz": "1698369",              // Required: Patient M1Ziffer
    "date": "2025-10-06",          // Required: Date (YYYY-MM-DD)
    "appointment_type_id": 24      // Optional: Default 24 (Herzkatheter)
}
```

**Response (202 Accepted):**
```json
{
    "message": "Single patient synchronization started",
    "task_id": "patient_sync_1698369_2025-10-06_24_20251004120000",
    "piz": "1698369",
    "date": "2025-10-06",
    "status_url": "/api/sync/status/patient_sync_1698369_2025-10-06_24_20251004120000"
}
```

**Error Response (400 Bad Request):**
```json
{
    "error": "Missing required fields: date, piz",
    "example": {
        "date": "2025-08-20",
        "piz": "12345",
        "appointment_type_id": 24
    }
}
```

**Validation Rules:**
- `piz`: Must be a non-empty string
- `date`: Must be in YYYY-MM-DD format
- `appointment_type_id`: Integer, defaults to 24

---

### Full Day Sync

Synchronize all appointments for a specific date.

**Endpoint:** `POST /api/sync`

**Request Body:**
```json
{
    "date": "2025-10-06",          // Required: Date (YYYY-MM-DD)
    "appointment_type_id": 24      // Optional: Default 24
}
```

**Response (202 Accepted):**
```json
{
    "message": "Synchronization started",
    "task_id": "sync_2025-10-06_24_20251004120000",
    "status_url": "/api/sync/status/sync_2025-10-06_24_20251004120000"
}
```

---

### Task Status

Check the status of a synchronization task.

**Endpoint:** `GET /api/sync/status/{task_id}`

**Response (200 OK):**
```json
{
    "task_id": "patient_sync_1698369_2025-10-06_24_20251004120000",
    "status": "completed",         // pending | running | completed | failed
    "piz": "1698369",
    "date": "2025-10-06",
    "start_time": "2025-10-04T12:00:00",
    "end_time": "2025-10-04T12:00:03",
    "duration_seconds": 3.02,
    "result": {
        "success": true,
        "message": "Single-Patient erfolgreich synchronisiert",
        "execution_time_ms": 2913,
        "patient": {
            "found": true,
            "name": "Wippel",
            "vorname": "Hermann",
            "geburtsdatum": null
        },
        "stats": {
            "appointments_found": 1,
            "patient_found": true,
            "sqlhk_action": "created",  // created | updated | already_exists
            "errors": []
        },
        "sqlhk_sync": {
            "action": "created",
            "untersuchung_id": 20369
        }
    },
    "error": null
}
```

**Status Values:**
- `pending` - Task is queued
- `running` - Task is being processed
- `completed` - Task finished successfully
- `failed` - Task failed with error

---

### Active Tasks

List all currently active synchronization tasks.

**Endpoint:** `GET /api/sync/active`

**Response (200 OK):**
```json
{
    "count": 2,
    "tasks": [
        {
            "task_id": "sync_2025-10-06_24_20251004120000",
            "status": "running",
            "date": "2025-10-06",
            "appointment_type_id": 24,
            "start_time": "2025-10-04T12:00:00"
        },
        {
            "task_id": "patient_sync_1698369_2025-10-06_24_20251004115959",
            "status": "completed",
            "piz": "1698369",
            "date": "2025-10-06",
            "start_time": "2025-10-04T11:59:59",
            "end_time": "2025-10-04T12:00:02"
        }
    ]
}
```

---

## Response Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Request successful |
| 202 | Accepted | Async task started |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Task already running |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service not ready |

---

## Error Handling

All error responses follow this structure:

```json
{
    "error": "Error message",
    "details": {
        "field": "Additional information"
    }
}
```

### Common Errors

#### Invalid Date Format
```json
{
    "error": "Invalid date format. Use YYYY-MM-DD"
}
```

#### Missing Required Fields
```json
{
    "error": "Missing required fields: date, piz",
    "example": {
        "date": "2025-08-20",
        "piz": "12345"
    }
}
```

#### Task Already Running
```json
{
    "error": "Synchronization already running for this date",
    "task_id": "existing_task_id"
}
```

---

## Examples

### Python Example

```python
import requests
import time
import json

# Configuration
API_URL = "http://localhost:5555"
PIZ = "1698369"
DATE = "2025-10-06"

def sync_single_patient(piz, date):
    """Synchronize a single patient"""
    
    # 1. Check API health
    health = requests.get(f"{API_URL}/health")
    if health.status_code != 200:
        raise Exception("API not available")
    
    # 2. Start synchronization
    payload = {
        "piz": piz,
        "date": date,
        "appointment_type_id": 24
    }
    
    response = requests.post(
        f"{API_URL}/api/sync/patient",
        json=payload
    )
    
    if response.status_code != 202:
        raise Exception(f"Failed to start sync: {response.text}")
    
    task_id = response.json()["task_id"]
    print(f"Task started: {task_id}")
    
    # 3. Poll for result
    while True:
        status = requests.get(f"{API_URL}/api/sync/status/{task_id}")
        data = status.json()
        
        if data["status"] == "completed":
            print("Success:", json.dumps(data["result"], indent=2))
            return data["result"]
        elif data["status"] == "failed":
            print("Failed:", data["error"])
            return None
        
        time.sleep(1)  # Wait 1 second before next poll

# Execute
result = sync_single_patient(PIZ, DATE)
```

### C# Example

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class SyncApiClient
{
    private readonly HttpClient client;
    private readonly string baseUrl = "http://localhost:5555";
    
    public SyncApiClient()
    {
        client = new HttpClient();
    }
    
    public async Task<dynamic> SyncPatientAsync(string piz, string date)
    {
        // Start sync
        var payload = new
        {
            piz = piz,
            date = date,
            appointment_type_id = 24
        };
        
        var json = JsonConvert.SerializeObject(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await client.PostAsync($"{baseUrl}/api/sync/patient", content);
        response.EnsureSuccessStatusCode();
        
        var result = await response.Content.ReadAsStringAsync();
        dynamic data = JsonConvert.DeserializeObject(result);
        
        string taskId = data.task_id;
        
        // Poll for result
        while (true)
        {
            var statusResponse = await client.GetAsync($"{baseUrl}/api/sync/status/{taskId}");
            var statusJson = await statusResponse.Content.ReadAsStringAsync();
            dynamic status = JsonConvert.DeserializeObject(statusJson);
            
            if (status.status == "completed")
            {
                return status.result;
            }
            else if (status.status == "failed")
            {
                throw new Exception($"Sync failed: {status.error}");
            }
            
            await Task.Delay(1000);
        }
    }
}
```

### PowerShell Example

```powershell
# Single Patient Sync Function
function Sync-Patient {
    param(
        [string]$PIZ,
        [string]$Date
    )
    
    $ApiUrl = "http://localhost:5555"
    
    # Start synchronization
    $body = @{
        piz = $PIZ
        date = $Date
        appointment_type_id = 24
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod `
        -Uri "$ApiUrl/api/sync/patient" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    
    $taskId = $response.task_id
    Write-Host "Task started: $taskId"
    
    # Poll for result
    do {
        Start-Sleep -Seconds 1
        $status = Invoke-RestMethod `
            -Uri "$ApiUrl/api/sync/status/$taskId" `
            -Method GET
    } while ($status.status -eq "pending" -or $status.status -eq "running")
    
    if ($status.status -eq "completed") {
        return $status.result
    } else {
        throw "Sync failed: $($status.error)"
    }
}

# Usage
$result = Sync-Patient -PIZ "1698369" -Date "2025-10-06"
$result | ConvertTo-Json -Depth 10
```

### cURL Example

```bash
#!/bin/bash

# Configuration
API_URL="http://localhost:5555"
PIZ="1698369"
DATE="2025-10-06"

# Start sync
RESPONSE=$(curl -s -X POST "$API_URL/api/sync/patient" \
  -H "Content-Type: application/json" \
  -d "{\"piz\":\"$PIZ\",\"date\":\"$DATE\"}")

TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Task started: $TASK_ID"

# Poll for result
while true; do
  STATUS=$(curl -s "$API_URL/api/sync/status/$TASK_ID")
  STATE=$(echo $STATUS | jq -r '.status')
  
  if [ "$STATE" = "completed" ]; then
    echo "Success:"
    echo $STATUS | jq '.result'
    break
  elif [ "$STATE" = "failed" ]; then
    echo "Failed:"
    echo $STATUS | jq '.error'
    exit 1
  fi
  
  sleep 1
done
```

---

## Performance

### Expected Response Times

| Operation | Average Time | Maximum Time |
|-----------|-------------|--------------|
| Health Check | < 100ms | 500ms |
| Single Patient Sync | 2-4 seconds | 5 seconds |
| Full Day Sync | 10-30 seconds | 60 seconds |
| Status Check | < 100ms | 500ms |

### Rate Limits

- Maximum concurrent syncs: 4
- Requests per second: No limit (recommended < 10)
- Task retention: 5 minutes after completion

### Performance Tips

1. **Use async patterns** - Don't block waiting for results
2. **Implement exponential backoff** - For status polling
3. **Cache task results** - Tasks are retained for 5 minutes
4. **Batch operations** - Use full-day sync for multiple patients

---

## Integration Guide

### Step 1: Environment Setup

```yaml
# docker-compose.yml example
services:
  calldoc-sync:
    image: calldoc-sync:latest
    ports:
      - "5555:5555"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=5555
      - LOG_LEVEL=INFO
```

### Step 2: Health Monitoring

Implement health checks in your monitoring system:

```javascript
// Node.js health check
const axios = require('axios');

async function checkApiHealth() {
    try {
        const response = await axios.get('http://localhost:5555/health');
        return response.data.status === 'healthy';
    } catch (error) {
        console.error('API health check failed:', error);
        return false;
    }
}

// Run every 30 seconds
setInterval(checkApiHealth, 30000);
```

### Step 3: Error Recovery

Implement retry logic with exponential backoff:

```python
import time
import requests
from typing import Optional

def sync_with_retry(piz: str, date: str, max_retries: int = 3) -> Optional[dict]:
    """Sync with automatic retry on failure"""
    
    for attempt in range(max_retries):
        try:
            # Start sync
            response = requests.post(
                "http://localhost:5555/api/sync/patient",
                json={"piz": piz, "date": date},
                timeout=10
            )
            
            if response.status_code == 409:
                # Already running, get existing task
                error_data = response.json()
                task_id = error_data.get("task_id")
            elif response.status_code == 202:
                task_id = response.json()["task_id"]
            else:
                raise Exception(f"Unexpected status: {response.status_code}")
            
            # Wait for completion
            return wait_for_task(task_id)
            
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None

def wait_for_task(task_id: str, timeout: int = 60) -> Optional[dict]:
    """Wait for task completion with timeout"""
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"http://localhost:5555/api/sync/status/{task_id}")
        data = response.json()
        
        if data["status"] == "completed":
            return data["result"]
        elif data["status"] == "failed":
            raise Exception(f"Task failed: {data['error']}")
        
        time.sleep(1)
    
    raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
```

### Step 4: Webhook Integration (Future)

For production environments, consider implementing webhooks:

```json
{
    "piz": "1698369",
    "date": "2025-10-06",
    "webhook_url": "https://your-system.com/webhook/sync-complete"
}
```

---

## Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check if application is running
tasklist | findstr CallDocSync

# Check if port is open
netstat -an | findstr 5555

# Restart application
taskkill /F /IM CallDocSyncWithAPI.exe
start CallDocSyncWithAPI.exe
```

#### Sync Failures
- Verify CallDoc connectivity
- Check SQLHK database permissions
- Review logs in `sync_api_server.log`

#### Performance Issues
- Check active sync count: `GET /api/sync/active`
- Monitor database performance
- Increase timeout values if needed

---

## Support

For issues or questions:
- **Log Files:** `sync_api_server.log`, `sync_gui_*.log`
- **Documentation:** This file and TASK_SINGLE_PATIENT_API.md
- **Author:** Markus
- **Version:** 1.0.0
- **Last Updated:** 04.10.2025

---

## Changelog

### Version 1.0.0 (04.10.2025)
- Initial release
- Single-patient synchronization
- Full-day synchronization
- Async task processing
- Real-time status monitoring

---

## License

Proprietary - Internal Use Only

---