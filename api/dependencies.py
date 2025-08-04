#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API-Abhängigkeiten für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die Abhängigkeiten und Hilfsfunktionen für die API-Endpunkte
der CallDoc-SQLHK Synchronisierungs-API.

Autor: Markus
Datum: 03.08.2025
"""

import os
import logging
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

from config_manager import ConfigManager
from connection_checker import ConnectionChecker
from auto_sync_scheduler import AutoSyncScheduler

# Logger konfigurieren
logger = logging.getLogger(__name__)

# API-Schlüssel-Konfiguration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Singleton-Instanzen
config_manager = ConfigManager()

# Basis-URLs aus der Konfiguration laden
calldoc_config = config_manager.get_calldoc_config()
sqlhk_config = config_manager.get_sqlhk_config()

calldoc_base_url = calldoc_config.get('BASE_URL', 'https://api.calldoc.de')
sqlhk_base_url = sqlhk_config.get('BASE_URL', 'http://localhost:8000')

# ConnectionChecker mit den Basis-URLs initialisieren
connection_checker = ConnectionChecker(calldoc_base_url, sqlhk_base_url)

# API-Schlüssel aus Konfiguration oder Umgebungsvariable
def get_api_key():
    """Gibt den API-Schlüssel aus der Konfiguration oder Umgebungsvariable zurück."""
    # Prüfe zuerst die Umgebungsvariable
    api_key = os.environ.get("CALLDOC_SQLHK_API_KEY")
    
    # Wenn nicht in der Umgebungsvariable, dann aus der Konfiguration
    if not api_key:
        api_key = config_manager.get_value("API", "API_KEY", "")
    
    # Wenn kein API-Schlüssel konfiguriert ist, generiere einen und speichere ihn
    if not api_key:
        import secrets
        api_key = secrets.token_urlsafe(32)
        config_manager.set_value("API", "API_KEY", api_key)
        config_manager.save_config()
        logger.info("Neuer API-Schlüssel generiert und in der Konfiguration gespeichert")
    
    return api_key

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    """Überprüft den API-Schlüssel."""
    if api_key_header == get_api_key():
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Ungültiger API-Schlüssel"
    )

def get_config_manager():
    """Gibt die ConfigManager-Instanz zurück."""
    return config_manager

def get_connection_checker():
    """Gibt die ConnectionChecker-Instanz zurück."""
    return connection_checker

def get_auto_sync_scheduler(sync_function):
    """Gibt eine AutoSyncScheduler-Instanz zurück."""
    auto_sync_settings = config_manager.get_auto_sync_settings()
    return AutoSyncScheduler(sync_function, auto_sync_settings)

class SyncService:
    """Service für die Synchronisierung zwischen CallDoc und SQLHK."""
    
    def __init__(self, config_manager=None, connection_checker=None):
        """Initialisiert den SyncService."""
        self.config_manager = config_manager or get_config_manager()
        self.connection_checker = connection_checker or get_connection_checker()
        
    def synchronize(self, date, appointment_type_id=None, delete_obsolete=True):
        """
        Führt eine Synchronisierung für das angegebene Datum durch.
        
        Args:
            date: Datum im Format YYYY-MM-DD
            appointment_type_id: Optional, ID des Termintyps
            delete_obsolete: Optional, obsolete Untersuchungen löschen
            
        Returns:
            Ein Dictionary mit den Synchronisierungsergebnissen
        """
        import time
        from datetime import datetime
        
        # Zeitmessung starten
        start_time = time.time()
        
        # Verbindungen prüfen
        sqlhk_success, sqlhk_error = self.connection_checker.check_sqlhk_connection()
        if not sqlhk_success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SQLHK-Server nicht erreichbar: {sqlhk_error}"
            )
        
        calldoc_success, calldoc_error = self.connection_checker.check_calldoc_connection()
        if not calldoc_success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"CallDoc-Server nicht erreichbar: {calldoc_error}"
            )
        
        # Hier würde die eigentliche Synchronisierungslogik aufgerufen werden
        # Dies ist ein Platzhalter für die tatsächliche Implementierung
        
        # In einer realen Implementierung würden wir hier die bestehende Synchronisierungslogik aufrufen
        # und die Ergebnisse zurückgeben
        
        # Zeitmessung beenden
        end_time = time.time()
        duration = end_time - start_time
        
        # Beispielergebnis (in der realen Implementierung würden hier die tatsächlichen Ergebnisse stehen)
        result = {
            "date": date,
            "total_appointments": 10,
            "new_examinations": 5,
            "updated_examinations": 3,
            "deleted_examinations": 2,
            "duration_seconds": duration,
            "timestamp": datetime.now(),
            "details": {
                "appointment_type_id": appointment_type_id,
                "delete_obsolete": delete_obsolete
            }
        }
        
        return result

def get_sync_service():
    """Gibt eine SyncService-Instanz zurück."""
    return SyncService(config_manager, connection_checker)
