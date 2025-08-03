#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Verbindungsprüfung für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die Klasse ConnectionChecker, die für die Prüfung der
Verbindung zu den API-Servern verantwortlich ist.

Autor: Markus
Datum: 03.08.2025
"""

import requests
import logging
from typing import Dict, Tuple, Optional
import time

logger = logging.getLogger(__name__)

class ConnectionChecker:
    """
    Prüft die Verbindung zu den API-Servern.
    """
    
    def __init__(self, calldoc_base_url: str, sqlhk_base_url: str):
        """
        Initialisiert den ConnectionChecker.
        
        Args:
            calldoc_base_url: Basis-URL der CallDoc-API
            sqlhk_base_url: Basis-URL der SQLHK-API
        """
        self.calldoc_base_url = calldoc_base_url
        self.sqlhk_base_url = sqlhk_base_url
    
    def check_calldoc_connection(self, timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Prüft die Verbindung zur CallDoc-API.
        
        Args:
            timeout: Timeout in Sekunden
            
        Returns:
            Tuple aus (Erfolg, Fehlermeldung)
        """
        try:
            # Entferne "/api/v1/frontend" vom Ende der URL für den Health-Check
            base_url = self.calldoc_base_url.split("/api")[0]
            health_url = f"{base_url}/health"
            
            logger.info(f"Prüfe CallDoc-Verbindung: {health_url}")
            response = requests.get(health_url, timeout=timeout)
            
            if response.status_code == 200:
                logger.info("CallDoc-Verbindung erfolgreich")
                return True, None
            else:
                error_msg = f"CallDoc-Server antwortet mit Status {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zum CallDoc-Server fehlgeschlagen"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.Timeout:
            error_msg = "Timeout bei der Verbindung zum CallDoc-Server"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Fehler bei der CallDoc-Verbindungsprüfung: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_sqlhk_connection(self, timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Prüft die Verbindung zur SQLHK-API.
        
        Args:
            timeout: Timeout in Sekunden
            
        Returns:
            Tuple aus (Erfolg, Fehlermeldung)
        """
        try:
            # Entferne "/api" vom Ende der URL für den Health-Check
            base_url = self.sqlhk_base_url.split("/api")[0]
            health_url = f"{base_url}/health"
            
            logger.info(f"Prüfe SQLHK-Verbindung: {health_url}")
            response = requests.get(health_url, timeout=timeout)
            
            if response.status_code == 200:
                logger.info("SQLHK-Verbindung erfolgreich")
                return True, None
            else:
                error_msg = f"SQLHK-Server antwortet mit Status {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zum SQLHK-Server fehlgeschlagen"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.Timeout:
            error_msg = "Timeout bei der Verbindung zum SQLHK-Server"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Fehler bei der SQLHK-Verbindungsprüfung: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_all_connections(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Prüft alle Verbindungen.
        
        Returns:
            Dictionary mit den Ergebnissen der Verbindungsprüfungen
        """
        return {
            "calldoc": self.check_calldoc_connection(),
            "sqlhk": self.check_sqlhk_connection()
        }
    
    def wait_for_sqlhk_connection(self, max_attempts: int = 3, wait_seconds: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Wartet auf eine erfolgreiche Verbindung zum SQLHK-Server.
        
        Args:
            max_attempts: Maximale Anzahl von Verbindungsversuchen
            wait_seconds: Wartezeit zwischen den Versuchen in Sekunden
            
        Returns:
            Tuple aus (Erfolg, Fehlermeldung)
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(f"SQLHK-Verbindungsversuch {attempt}/{max_attempts}")
            success, error = self.check_sqlhk_connection()
            
            if success:
                return True, None
            
            if attempt < max_attempts:
                logger.info(f"Warte {wait_seconds} Sekunden vor dem nächsten Versuch...")
                time.sleep(wait_seconds)
        
        return False, f"SQLHK-Server nach {max_attempts} Versuchen nicht erreichbar"


if __name__ == "__main__":
    # Test
    from config_manager import config_manager
    
    api_urls = config_manager.get_api_urls()
    checker = ConnectionChecker(
        api_urls["CALLDOC_API_BASE_URL"],
        api_urls["SQLHK_API_BASE_URL"]
    )
    
    print("CallDoc:", checker.check_calldoc_connection())
    print("SQLHK:", checker.check_sqlhk_connection())
