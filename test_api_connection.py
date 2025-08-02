"""
Testet die Verbindung zur CallDoc-API.
"""

import requests
from constants import API_BASE_URL

def test_connection():
    """Testet die Verbindung zur CallDoc-API."""
    print(f"Teste Verbindung zu {API_BASE_URL}")
    
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Verbindung erfolgreich!")
        else:
            print(f"Fehler: Unerwarteter Status-Code {response.status_code}")
    except Exception as e:
        print(f"Fehler: {str(e)}")

if __name__ == "__main__":
    test_connection()
