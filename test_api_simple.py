"""
Einfacher Test der Sync API
"""
import requests
import json

# Test ob API läuft
try:
    response = requests.get("http://localhost:5555/health", timeout=2)
    if response.status_code == 200:
        print("✓ API ist online!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("✗ API antwortet nicht korrekt")
except requests.exceptions.ConnectionError:
    print("✗ API ist nicht erreichbar. Starte sie mit:")
    print("  python sync_api_server.py")
except Exception as e:
    print(f"✗ Fehler: {e}")