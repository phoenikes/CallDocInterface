#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Skript für die API-Integration

Dieses Skript testet die API-Integration der CallDoc-SQLHK Synchronisierung.
Es überprüft, ob der API-Server korrekt gestartet und gestoppt werden kann
und ob die API-Endpunkte korrekt funktionieren.

Autor: Markus
Datum: 03.08.2025
"""

import os
import sys
import time
import requests
import logging
from config_manager import ConfigManager
from api_integration import ApiServerManager

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_api_server():
    """
    Testet den API-Server.
    """
    logger.info("Starte Test des API-Servers...")
    
    # Konfiguration laden
    config_manager = ConfigManager()
    api_config = config_manager.get_api_config()
    api_key = api_config["API_KEY"]
    
    # API-Server-Manager erstellen
    api_server_manager = ApiServerManager()
    
    # API-Server starten
    logger.info("Starte API-Server...")
    success = api_server_manager.start_server(host="127.0.0.1", port=8080)
    
    if not success:
        logger.error("API-Server konnte nicht gestartet werden.")
        return False
    
    logger.info("API-Server erfolgreich gestartet.")
    
    # Warten, bis der Server vollständig gestartet ist
    time.sleep(2)
    
    # Health-Endpunkt testen
    try:
        logger.info("Teste Health-Endpunkt...")
        response = requests.get("http://127.0.0.1:8080/api/health")
        
        if response.status_code == 200 and response.json().get("status") == "ok":
            logger.info("Health-Endpunkt funktioniert korrekt.")
        else:
            logger.error(f"Health-Endpunkt fehlgeschlagen: {response.status_code} - {response.text}")
            api_server_manager.stop_server()
            return False
    except Exception as e:
        logger.error(f"Fehler beim Testen des Health-Endpunkts: {str(e)}")
        api_server_manager.stop_server()
        return False
    
    # Verbindungsstatus-Endpunkt testen
    try:
        logger.info("Teste Verbindungsstatus-Endpunkt...")
        headers = {"X-API-Key": api_key}
        response = requests.get("http://127.0.0.1:8080/api/health/connection", headers=headers)
        
        if response.status_code == 200:
            logger.info("Verbindungsstatus-Endpunkt funktioniert korrekt.")
            logger.info(f"Antwort: {response.json()}")
        else:
            logger.error(f"Verbindungsstatus-Endpunkt fehlgeschlagen: {response.status_code} - {response.text}")
            api_server_manager.stop_server()
            return False
    except Exception as e:
        logger.error(f"Fehler beim Testen des Verbindungsstatus-Endpunkts: {str(e)}")
        api_server_manager.stop_server()
        return False
    
    # API-Server stoppen
    logger.info("Stoppe API-Server...")
    api_server_manager.stop_server()
    logger.info("API-Server erfolgreich gestoppt.")
    
    return True

if __name__ == "__main__":
    if test_api_server():
        logger.info("API-Integration-Test erfolgreich abgeschlossen.")
        sys.exit(0)
    else:
        logger.error("API-Integration-Test fehlgeschlagen.")
        sys.exit(1)
