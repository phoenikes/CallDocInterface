#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logging-Konfiguration für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die zentrale Konfiguration für das Logging-System.
Sie ermöglicht strukturiertes Logging mit verschiedenen Detailstufen,
Rotation der Logdateien und Filterung nach Komponenten.

Autor: Markus
Datum: 04.08.2025
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path


class LogFilter(logging.Filter):
    """
    Filter für Logging-Nachrichten basierend auf Komponenten.
    """
    
    def __init__(self, component=None):
        """
        Initialisiert den Filter.
        
        Args:
            component: Name der Komponente, nach der gefiltert werden soll
        """
        super().__init__()
        self.component = component
    
    def filter(self, record):
        """
        Filtert Logging-Nachrichten nach Komponente.
        
        Args:
            record: Logging-Record
            
        Returns:
            True, wenn die Nachricht angezeigt werden soll, sonst False
        """
        if not self.component:
            return True
        
        return record.name.startswith(self.component)


def configure_logging(log_level=logging.INFO, log_dir="logs", app_name="sync_gui",
                     console_output=True, file_output=True, max_bytes=10485760, backup_count=5,
                     use_config=True):
    """
    Konfiguriert das Logging-System mit verschiedenen Ausgabezielen und Formaten.
    
    Args:
        log_level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Verzeichnis für Logdateien
        app_name: Name der Anwendung (für Logdateinamen)
        console_output: Ob Logs in der Konsole ausgegeben werden sollen
        file_output: Ob Logs in Dateien geschrieben werden sollen
        max_bytes: Maximale Größe einer Logdatei in Bytes (10 MB Standard)
        backup_count: Anzahl der zu behaltenden Backup-Dateien
        use_config: Ob die Konfiguration aus dem ConfigManager verwendet werden soll
    """
    # Wenn use_config=True, Einstellungen aus ConfigManager laden
    if use_config:
        try:
            # Lazy-Import, um zirkuläre Abhängigkeiten zu vermeiden
            from config_manager import config_manager
            
            # Logging-Konfiguration aus ConfigManager laden
            config = config_manager.get_logging_config()
            
            # String zu Logging-Level konvertieren
            level_name = config.get('level', 'INFO')
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            log_level = level_map.get(level_name, logging.INFO)
            
            # Weitere Konfigurationsparameter übernehmen
            log_dir = config.get('log_dir', log_dir)
            console_output = config.get('console_output', console_output)
            file_output = config.get('file_output', file_output)
            max_bytes = config.get('max_bytes', max_bytes)
            backup_count = config.get('backup_count', backup_count)
        except (ImportError, AttributeError):
            # Wenn ConfigManager nicht verfügbar ist, Standardwerte verwenden
            pass
    # Hauptlogger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Alle bestehenden Handler entfernen
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatierung für detaillierte Logs
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Formatierung für einfache Logs
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Konsolenausgabe konfigurieren
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
    
    # Dateiausgabe konfigurieren
    if file_output:
        # Logverzeichnis erstellen, falls es nicht existiert
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True, parents=True)
        
        # Dateiname mit Datum
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{app_name}_{current_date}.log"
        
        # Rotating File Handler für automatische Rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Separate Datei für Fehler
        error_log_file = log_path / f"{app_name}_errors_{current_date}.log"
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_file_handler.setFormatter(detailed_formatter)
        error_file_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_file_handler)
    
    # Komponenten-spezifische Logger konfigurieren
    configure_component_logger("calldoc", log_level, log_dir, max_bytes, backup_count)
    configure_component_logger("sqlhk", log_level, log_dir, max_bytes, backup_count)
    configure_component_logger("api", log_level, log_dir, max_bytes, backup_count)
    configure_component_logger("sync", log_level, log_dir, max_bytes, backup_count)
    
    logging.info(f"Logging konfiguriert mit Level {logging.getLevelName(log_level)}")
    return root_logger


def configure_component_logger(component, log_level, log_dir, max_bytes, backup_count):
    """
    Konfiguriert einen Logger für eine bestimmte Komponente.
    
    Args:
        component: Name der Komponente
        log_level: Logging-Level
        log_dir: Verzeichnis für Logdateien
        max_bytes: Maximale Größe einer Logdatei
        backup_count: Anzahl der zu behaltenden Backup-Dateien
    """
    # Logverzeichnis für Komponente
    component_log_dir = Path(log_dir) / component
    component_log_dir.mkdir(exist_ok=True, parents=True)
    
    # Dateiname mit Datum
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    component_log_file = component_log_dir / f"{component}_{current_date}.log"
    
    # Logger für Komponente
    component_logger = logging.getLogger(component)
    component_logger.propagate = True  # Nachrichten an Root-Logger weiterleiten
    
    # Komponenten-Filter erstellen
    component_filter = LogFilter(component)
    
    # Handler für Komponente
    component_handler = logging.handlers.RotatingFileHandler(
        component_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    component_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    ))
    component_handler.setLevel(log_level)
    component_handler.addFilter(component_filter)
    
    component_logger.addHandler(component_handler)


def get_logger(name):
    """
    Gibt einen Logger mit dem angegebenen Namen zurück.
    
    Args:
        name: Name des Loggers
        
    Returns:
        Logger-Instanz
    """
    return logging.getLogger(name)


# Standardkonfiguration, wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    configure_logging(log_level=logging.DEBUG)
    
    # Beispiel-Logs
    logger = logging.getLogger(__name__)
    logger.debug("Debug-Nachricht")
    logger.info("Info-Nachricht")
    logger.warning("Warnung")
    logger.error("Fehler")
    logger.critical("Kritischer Fehler")
    
    # Komponenten-Logger
    calldoc_logger = logging.getLogger("calldoc")
    calldoc_logger.info("CallDoc-Info")
    calldoc_logger.error("CallDoc-Fehler")
    
    sqlhk_logger = logging.getLogger("sqlhk")
    sqlhk_logger.info("SQLHK-Info")
    sqlhk_logger.error("SQLHK-Fehler")
    
    print("Logging-Test abgeschlossen. Überprüfe die Logdateien im 'logs'-Verzeichnis.")
