#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logging-Konfigurationsdialog für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält einen Dialog zur Konfiguration des Logging-Systems.
Der Dialog ermöglicht die Einstellung von Logging-Level, Ausgabezielen und Rotation.

Autor: Markus
Datum: 04.08.2025
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLabel, QComboBox, QCheckBox, QSpinBox, 
                           QPushButton, QFileDialog, QLineEdit, QGroupBox,
                           QMessageBox)
from PyQt5.QtCore import Qt
from config_manager import config_manager
from logging_config import configure_logging, get_logger

# Logger konfigurieren
logger = get_logger(__name__)

class LoggingConfigDialog(QDialog):
    """
    Dialog zur Konfiguration des Logging-Systems.
    Ermöglicht die Einstellung von Logging-Level, Ausgabezielen und Rotation.
    """
    
    def __init__(self, parent=None):
        """
        Initialisiert den Logging-Konfigurationsdialog.
        
        Args:
            parent: Elternobjekt für Qt
        """
        super().__init__(parent)
        self.setWindowTitle("Logging-Konfiguration")
        self.setMinimumWidth(500)
        
        # Aktuelle Konfiguration laden
        self.config = config_manager.get_logging_config()
        
        # UI initialisieren
        self.init_ui()
        
        # Werte aus Konfiguration setzen
        self.load_config()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche des Dialogs."""
        layout = QVBoxLayout()
        
        # Allgemeine Einstellungen
        general_group = QGroupBox("Allgemeine Einstellungen")
        general_layout = QFormLayout()
        
        # Logging-Level
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        general_layout.addRow("Logging-Level:", self.level_combo)
        
        # Log-Verzeichnis
        log_dir_layout = QHBoxLayout()
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setReadOnly(True)
        log_dir_layout.addWidget(self.log_dir_edit)
        
        self.browse_button = QPushButton("...")
        self.browse_button.setMaximumWidth(30)
        self.browse_button.clicked.connect(self.browse_log_dir)
        log_dir_layout.addWidget(self.browse_button)
        
        general_layout.addRow("Log-Verzeichnis:", log_dir_layout)
        
        # Ausgabeziele
        self.console_output_check = QCheckBox("Konsolenausgabe")
        general_layout.addRow("", self.console_output_check)
        
        self.file_output_check = QCheckBox("Dateiausgabe")
        general_layout.addRow("", self.file_output_check)
        
        # Komponenten-Logging
        self.component_logging_check = QCheckBox("Komponenten-spezifisches Logging")
        general_layout.addRow("", self.component_logging_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Rotation-Einstellungen
        rotation_group = QGroupBox("Datei-Rotation")
        rotation_layout = QFormLayout()
        
        # Maximale Dateigröße
        self.max_bytes_spin = QSpinBox()
        self.max_bytes_spin.setRange(1, 1000)
        self.max_bytes_spin.setSuffix(" MB")
        self.max_bytes_spin.setValue(10)
        rotation_layout.addRow("Maximale Dateigröße:", self.max_bytes_spin)
        
        # Anzahl der Backup-Dateien
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        self.backup_count_spin.setValue(5)
        rotation_layout.addRow("Anzahl der Backup-Dateien:", self.backup_count_spin)
        
        rotation_group.setLayout(rotation_layout)
        layout.addWidget(rotation_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Anwenden")
        self.apply_button.clicked.connect(self.apply_config)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_config)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_config(self):
        """Lädt die Konfiguration in die UI-Elemente."""
        # Logging-Level
        level_index = self.level_combo.findText(self.config.get('level', 'INFO'))
        if level_index >= 0:
            self.level_combo.setCurrentIndex(level_index)
        
        # Log-Verzeichnis
        self.log_dir_edit.setText(self.config.get('log_dir', 'logs'))
        
        # Ausgabeziele
        self.console_output_check.setChecked(self.config.get('console_output', True))
        self.file_output_check.setChecked(self.config.get('file_output', True))
        
        # Komponenten-Logging
        self.component_logging_check.setChecked(self.config.get('component_logging', True))
        
        # Rotation-Einstellungen
        self.max_bytes_spin.setValue(self.config.get('max_bytes', 10485760) // 1048576)  # Umrechnung in MB
        self.backup_count_spin.setValue(self.config.get('backup_count', 5))
    
    def browse_log_dir(self):
        """Öffnet einen Dialog zur Auswahl des Log-Verzeichnisses."""
        current_dir = self.log_dir_edit.text()
        if not os.path.isdir(current_dir):
            current_dir = os.getcwd()
        
        directory = QFileDialog.getExistingDirectory(
            self, "Log-Verzeichnis auswählen", current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.log_dir_edit.setText(directory)
    
    def get_config_from_ui(self):
        """
        Liest die Konfiguration aus den UI-Elementen.
        
        Returns:
            Dictionary mit der Logging-Konfiguration
        """
        return {
            'level': self.level_combo.currentText(),
            'log_dir': self.log_dir_edit.text(),
            'console_output': self.console_output_check.isChecked(),
            'file_output': self.file_output_check.isChecked(),
            'max_bytes': self.max_bytes_spin.value() * 1048576,  # Umrechnung von MB in Bytes
            'backup_count': self.backup_count_spin.value(),
            'component_logging': self.component_logging_check.isChecked()
        }
    
    def apply_config(self):
        """Wendet die Konfiguration an, ohne den Dialog zu schließen."""
        config = self.get_config_from_ui()
        
        # Konfiguration speichern
        config_manager.set_logging_config(
            level=config['level'],
            log_dir=config['log_dir'],
            file_output=config['file_output'],
            console_output=config['console_output'],
            max_bytes=config['max_bytes'],
            backup_count=config['backup_count'],
            component_logging=config['component_logging']
        )
        
        # Logging neu konfigurieren
        level_map = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        
        configure_logging(
            log_level=level_map.get(config['level'], 20),
            log_dir=config['log_dir'],
            app_name="sync_gui",
            console_output=config['console_output'],
            file_output=config['file_output'],
            max_bytes=config['max_bytes'],
            backup_count=config['backup_count'],
            use_config=False  # Wir verwenden die expliziten Parameter
        )
        
        logger.info("Logging-Konfiguration wurde angewendet")
        QMessageBox.information(self, "Konfiguration angewendet", 
                              "Die Logging-Konfiguration wurde erfolgreich angewendet.")
    
    def accept_config(self):
        """Wendet die Konfiguration an und schließt den Dialog."""
        self.apply_config()
        self.accept()


if __name__ == "__main__":
    # Test des Dialogs
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dialog = LoggingConfigDialog()
    dialog.exec_()
