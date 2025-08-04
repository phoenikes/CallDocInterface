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
import secrets
import string
from typing import Dict, Any, Optional
from logging_config import get_logger

# Strukturiertes Logging verwenden
logger = get_logger(__name__)

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
        
        # API-Server Konfiguration
        self.config["API_SERVER"] = {
            "HOST": "0.0.0.0",
            "PORT": "8080",
            "API_KEY": self.generate_api_key()
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
    
    def get_calldoc_config(self) -> Dict[str, str]:
        """
        Gibt die CallDoc-API-Konfiguration zurück.
        
        Returns:
            Dictionary mit der CallDoc-API-Konfiguration
        """
        if not self.config.has_section("CALLDOC"):
            self.config.add_section("CALLDOC")
            self.config.set("CALLDOC", "BASE_URL", self.get_value("API", "CALLDOC_API_BASE_URL"))
            self.config.set("CALLDOC", "API_KEY", "")
            self.save_config()
        
        return {
            "BASE_URL": self.get_value("CALLDOC", "BASE_URL", self.get_value("API", "CALLDOC_API_BASE_URL")),
            "API_KEY": self.get_value("CALLDOC", "API_KEY", "")
        }
    
    def get_sqlhk_config(self) -> Dict[str, str]:
        """
        Gibt die SQLHK-API-Konfiguration zurück.
        
        Returns:
            Dictionary mit der SQLHK-API-Konfiguration
        """
        if not self.config.has_section("SQLHK"):
            self.config.add_section("SQLHK")
            self.config.set("SQLHK", "BASE_URL", self.get_value("API", "SQLHK_API_BASE_URL", "http://localhost:8000"))
            self.config.set("SQLHK", "API_KEY", "")
            self.save_config()
        
        return {
            "BASE_URL": self.get_value("SQLHK", "BASE_URL", self.get_value("API", "SQLHK_API_BASE_URL", "http://localhost:8000")),
            "API_KEY": self.get_value("SQLHK", "API_KEY", "")
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
    
    def generate_api_key(self) -> str:
        """
        Generiert einen zufälligen API-Schlüssel.
        
        Returns:
            Ein zufälliger API-Schlüssel mit 32 Zeichen
        """
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        return api_key
    
    def get_api_key(self) -> str:
        """
        Gibt den API-Schlüssel zurück.
        
        Returns:
            Der API-Schlüssel oder ein neu generierter Schlüssel, falls keiner existiert
        """
        api_key = self.get_value("API_SERVER", "API_KEY")
        if not api_key:
            api_key = self.generate_api_key()
            self.set_value("API_SERVER", "API_KEY", api_key)
            self.save_config()
        return api_key
    
    def set_api_key(self, api_key: str) -> None:
        """
        Setzt den API-Schlüssel.
        
        Args:
            api_key: Der zu setzende API-Schlüssel
        """
        self.set_value("API_SERVER", "API_KEY", api_key)
        self.save_config()
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Gibt die API-Server-Konfiguration zurück.
        
        Returns:
            Dictionary mit der API-Server-Konfiguration
        """
        return {
            "HOST": self.get_value("API_SERVER", "HOST", "0.0.0.0"),
            "PORT": int(self.get_value("API_SERVER", "PORT", "8080")),
            "API_KEY": self.get_api_key()
        }
    
    def set_api_config(self, config: Dict[str, Any]) -> None:
        """
        Aktualisiert die API-Server-Konfiguration.
        
        Args:
            config: Dictionary mit der zu aktualisierenden Konfiguration
        """
        for key, value in config.items():
            self.set_value("API_SERVER", key, str(value))
        
        self.save_config()
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Gibt die Logging-Konfiguration zurück.
        
        Returns:
            Dictionary mit Logging-Konfigurationseinstellungen
        """
        if not self.config.has_section('LOGGING'):
            self.config.add_section('LOGGING')
            self.config.set('LOGGING', 'LEVEL', 'INFO')
            self.config.set('LOGGING', 'LOG_DIR', 'logs')
            self.config.set('LOGGING', 'FILE_OUTPUT', 'True')
            self.config.set('LOGGING', 'CONSOLE_OUTPUT', 'True')
            self.config.set('LOGGING', 'MAX_BYTES', '10485760')  # 10 MB
            self.config.set('LOGGING', 'BACKUP_COUNT', '5')
            self.config.set('LOGGING', 'COMPONENT_LOGGING', 'True')
            self.save_config()
        
        return {
            'level': self.config.get('LOGGING', 'LEVEL', fallback='INFO'),
            'log_dir': self.config.get('LOGGING', 'LOG_DIR', fallback='logs'),
            'file_output': self.config.getboolean('LOGGING', 'FILE_OUTPUT', fallback=True),
            'console_output': self.config.getboolean('LOGGING', 'CONSOLE_OUTPUT', fallback=True),
            'max_bytes': self.config.getint('LOGGING', 'MAX_BYTES', fallback=10485760),
            'backup_count': self.config.getint('LOGGING', 'BACKUP_COUNT', fallback=5),
            'component_logging': self.config.getboolean('LOGGING', 'COMPONENT_LOGGING', fallback=True)
        }
    
    def set_logging_config(self, level: str = None, log_dir: str = None, 
                         file_output: bool = None, console_output: bool = None,
                         max_bytes: int = None, backup_count: int = None,
                         component_logging: bool = None) -> None:
        """
        Setzt die Logging-Konfiguration.
        
        Args:
            level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Verzeichnis für Logdateien
            file_output: Ob Logs in Dateien geschrieben werden sollen
            console_output: Ob Logs in der Konsole ausgegeben werden sollen
            max_bytes: Maximale Größe einer Logdatei in Bytes
            backup_count: Anzahl der zu behaltenden Backup-Dateien
            component_logging: Ob komponentenspezifisches Logging aktiviert sein soll
        """
        if not self.config.has_section('LOGGING'):
            self.config.add_section('LOGGING')
        
        if level is not None:
            self.config.set('LOGGING', 'LEVEL', level)
        if log_dir is not None:
            self.config.set('LOGGING', 'LOG_DIR', log_dir)
        if file_output is not None:
            self.config.set('LOGGING', 'FILE_OUTPUT', str(file_output))
        if console_output is not None:
            self.config.set('LOGGING', 'CONSOLE_OUTPUT', str(console_output))
        if max_bytes is not None:
            self.config.set('LOGGING', 'MAX_BYTES', str(max_bytes))
        if backup_count is not None:
            self.config.set('LOGGING', 'BACKUP_COUNT', str(backup_count))
        if component_logging is not None:
            self.config.set('LOGGING', 'COMPONENT_LOGGING', str(component_logging))
        
        self.save_config()
        logger.info("Logging-Konfiguration aktualisiert")

# Globale Instanz des ConfigManager
config_manager = ConfigManager()

if __name__ == "__main__":
    # Test
    print("API URLs:", config_manager.get_api_urls())
    print("Sync Settings:", config_manager.get_sync_settings())
    print("Auto Sync Settings:", config_manager.get_auto_sync_settings())
