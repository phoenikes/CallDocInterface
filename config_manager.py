#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Konfigurationsmanager für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die Klasse ConfigManager, die für das Laden und Speichern
der Konfigurationseinstellungen aus der config.ini Datei verantwortlich ist.

Autor: Markus
Datum: 03.08.2025
"""

import os
import configparser
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Verwaltet die Konfigurationseinstellungen der Anwendung.
    Lädt Einstellungen aus der config.ini Datei und ermöglicht das Speichern von Änderungen.
    """
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Initialisiert den ConfigManager.
        
        Args:
            config_file: Pfad zur Konfigurationsdatei (Standard: config.ini)
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        
        # Standardwerte setzen
        self._set_defaults()
        
        # Konfigurationsdatei laden
        self.load_config()
    
    def _set_defaults(self) -> None:
        """Setzt die Standardwerte für die Konfiguration."""
        self.config["API"] = {
            "CALLDOC_API_BASE_URL": "http://192.168.1.76:8001/api/v1/frontend",
            "PATIENT_SEARCH_URL": "${CALLDOC_API_BASE_URL}/patient_search/",
            "APPOINTMENT_SEARCH_URL": "${CALLDOC_API_BASE_URL}/appointment_search/",
            "SQLHK_API_BASE_URL": "http://192.168.1.67:7007/api"
        }
        
        self.config["SYNC"] = {
            "DEFAULT_APPOINTMENT_TYPE": "HERZKATHETERUNTERSUCHUNG",
            "SMART_STATUS_FILTER": "True",
            "DELETE_OBSOLETE": "True"
        }
        
        self.config["AUTO_SYNC"] = {
            "ENABLED": "False",
            "INTERVAL_MINUTES": "60",
            "START_TIME": "08:00",
            "END_TIME": "18:00",
            "DAYS": "1,2,3,4,5"  # Montag bis Freitag
        }
    
    def load_config(self) -> None:
        """Lädt die Konfiguration aus der Datei."""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                logger.info(f"Konfiguration aus {self.config_file} geladen")
            else:
                logger.warning(f"Konfigurationsdatei {self.config_file} nicht gefunden, verwende Standardwerte")
                self.save_config()  # Erstelle die Datei mit Standardwerten
        except Exception as e:
            logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
    
    def save_config(self) -> None:
        """Speichert die aktuelle Konfiguration in der Datei."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info(f"Konfiguration in {self.config_file} gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {str(e)}")
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Gibt den Wert für einen bestimmten Schlüssel in einer Sektion zurück.
        
        Args:
            section: Name der Sektion
            key: Name des Schlüssels
            default: Standardwert, falls der Schlüssel nicht existiert
            
        Returns:
            Der Wert des Schlüssels oder der Standardwert
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set_value(self, section: str, key: str, value: Any) -> None:
        """
        Setzt den Wert für einen bestimmten Schlüssel in einer Sektion.
        
        Args:
            section: Name der Sektion
            key: Name des Schlüssels
            value: Zu setzender Wert
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def get_api_urls(self) -> Dict[str, str]:
        """
        Gibt alle API-URLs zurück.
        
        Returns:
            Dictionary mit den API-URLs
        """
        return {
            "CALLDOC_API_BASE_URL": self.get_value("API", "CALLDOC_API_BASE_URL"),
            "PATIENT_SEARCH_URL": self.get_value("API", "PATIENT_SEARCH_URL"),
            "APPOINTMENT_SEARCH_URL": self.get_value("API", "APPOINTMENT_SEARCH_URL"),
            "SQLHK_API_BASE_URL": self.get_value("API", "SQLHK_API_BASE_URL")
        }
    
    def get_sync_settings(self) -> Dict[str, Any]:
        """
        Gibt die Synchronisierungseinstellungen zurück.
        
        Returns:
            Dictionary mit den Synchronisierungseinstellungen
        """
        return {
            "DEFAULT_APPOINTMENT_TYPE": self.get_value("SYNC", "DEFAULT_APPOINTMENT_TYPE"),
            "SMART_STATUS_FILTER": self.get_value("SYNC", "SMART_STATUS_FILTER") == "True",
            "DELETE_OBSOLETE": self.get_value("SYNC", "DELETE_OBSOLETE") == "True"
        }
    
    def get_auto_sync_settings(self) -> Dict[str, Any]:
        """
        Gibt die Einstellungen für die automatische Synchronisierung zurück.
        
        Returns:
            Dictionary mit den Einstellungen für die automatische Synchronisierung
        """
        days_str = self.get_value("AUTO_SYNC", "DAYS", "1,2,3,4,5")
        days = [int(d.strip()) for d in days_str.split(",") if d.strip().isdigit()]
        
        return {
            "ENABLED": self.get_value("AUTO_SYNC", "ENABLED") == "True",
            "INTERVAL_MINUTES": int(self.get_value("AUTO_SYNC", "INTERVAL_MINUTES", "60")),
            "START_TIME": self.get_value("AUTO_SYNC", "START_TIME", "08:00"),
            "END_TIME": self.get_value("AUTO_SYNC", "END_TIME", "18:00"),
            "DAYS": days
        }
    
    def update_api_urls(self, urls: Dict[str, str]) -> None:
        """
        Aktualisiert die API-URLs.
        
        Args:
            urls: Dictionary mit den zu aktualisierenden URLs
        """
        for key, value in urls.items():
            if value:  # Nur setzen, wenn ein Wert vorhanden ist
                self.set_value("API", key, value)
        
        self.save_config()
    
    def update_sync_settings(self, settings: Dict[str, Any]) -> None:
        """
        Aktualisiert die Synchronisierungseinstellungen.
        
        Args:
            settings: Dictionary mit den zu aktualisierenden Einstellungen
        """
        for key, value in settings.items():
            if isinstance(value, bool):
                value = str(value)
            self.set_value("SYNC", key, value)
        
        self.save_config()
    
    def update_auto_sync_settings(self, settings: Dict[str, Any]) -> None:
        """
        Aktualisiert die Einstellungen für die automatische Synchronisierung.
        
        Args:
            settings: Dictionary mit den zu aktualisierenden Einstellungen
        """
        for key, value in settings.items():
            if key == "DAYS" and isinstance(value, list):
                value = ",".join(map(str, value))
            elif isinstance(value, bool):
                value = str(value)
            
            self.set_value("AUTO_SYNC", key, value)
        
        self.save_config()

# Globale Instanz des ConfigManager
config_manager = ConfigManager()

if __name__ == "__main__":
    # Test
    print("API URLs:", config_manager.get_api_urls())
    print("Sync Settings:", config_manager.get_sync_settings())
    print("Auto Sync Settings:", config_manager.get_auto_sync_settings())
