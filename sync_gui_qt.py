#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CallDoc-SQLHK Synchronisierung - Grafische Benutzeroberfläche

Diese Datei enthält eine moderne GUI für die Synchronisierung von Untersuchungsdaten
zwischen dem CallDoc-System und der SQLHK-Datenbank.

Version 5.0 - Neue Funktionen:
- Verbindungsprüfung beim Start
- Konfigurationsdialog für API-URLs und Auto-Sync-Einstellungen
- Automatische Synchronisierung mit konfigurierbarem Zeitplan
- Verbesserte Fehlerbehandlung und Benutzerführung

Autor: Markus
Datum: 03.08.2025
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QCalendarWidget, QGroupBox, 
                            QPushButton, QTabWidget, QTextEdit, QLabel,
                            QComboBox, QCheckBox, QProgressBar, QMessageBox,
                            QFileDialog, QTableWidget, QTableWidgetItem,
                            QSplitter, QFrame, QDateEdit, QStatusBar,
                            QLineEdit, QFormLayout, QTimeEdit, QDialog,
                            QAction, QMenu)
from PyQt5.QtGui import QFont, QIcon, QIntValidator
from PyQt5.QtCore import QDate, pyqtSlot, Qt, QThread, pyqtSignal, QTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import der Synchronisierungskomponenten
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from appointment_types_mapping import map_appointment_to_untersuchung
from constants import APPOINTMENT_TYPES
from connection_checker import ConnectionChecker
from config_manager import ConfigManager
from auto_sync_scheduler import AutoSyncScheduler
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer
from constants import APPOINTMENT_TYPES

# Import der neuen Komponenten
from config_manager import config_manager
from connection_checker import ConnectionChecker
from auto_sync_scheduler import AutoSyncScheduler

# Konfiguriere das Logging
log_filename = f"sync_gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Log-Datei erstellt: {log_filename}")


class SyncWorker(QThread):
    """
    Worker-Thread für die Synchronisierung, um die GUI nicht zu blockieren.
    """
    update_signal = pyqtSignal(str, dict)
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)
    
    def __init__(self, date_str, appointment_type_id=None, smart_status_filter=True):
        super().__init__()
        self.date_str = date_str
        self.appointment_type_id = appointment_type_id
        self.smart_status_filter = smart_status_filter
        self.running = True
        
    def run(self):
        """
        Führt die Synchronisierung durch.
        """
        try:
            self.log_signal.emit(f"Starte Synchronisierung für Datum: {self.date_str}")
            
            # Datum im deutschen Format für die Datenbank
            try:
                date_parts = self.date_str.split("-")
                date_str_de = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
                self.log_signal.emit(f"Datum für SQLHK-Abfrage: {date_str_de}")
            except Exception as e:
                self.log_signal.emit(f"Fehler bei der Datumskonvertierung: {str(e)}")
                date_str_de = self.date_str
            
            # Initialisiere die Clients
            self.log_signal.emit("Initialisiere API-Clients...")
            self.log_signal.emit(f"Verwende Datum: {self.date_str} für API-Abfrage")
            calldoc_client = CallDocInterface(from_date=self.date_str, to_date=self.date_str)
            mssql_client = MsSqlApiClient()
            
            # Initialisiere die Synchronizer
            patient_sync = PatientSynchronizer()
            untersuchung_sync = UntersuchungSynchronizer(
                calldoc_interface=calldoc_client, 
                mssql_client=mssql_client
            )
            
            # 1. CallDoc-Termine abrufen
            self.log_signal.emit("1. CallDoc-Termine abrufen")
            self.update_signal.emit("Rufe CallDoc-Termine ab...", {"progress": 10})
            
            # Parameter für die Terminsuche
            search_params = {
                "from_date": self.date_str,
                "to_date": self.date_str
            }
            if self.appointment_type_id:
                search_params["appointment_type_id"] = self.appointment_type_id
            
            # Termine abrufen
            self.log_signal.emit(f"Rufe Termine für Datum {self.date_str} ab mit Parametern: {search_params}")
            response = calldoc_client.appointment_search(**search_params)
            self.log_signal.emit(f"API-Antwort erhalten: {type(response)}")
            
            # Überprüfe die Struktur der Antwort
            if isinstance(response, dict):
                self.log_signal.emit(f"API-Antwort Schlüssel: {response.keys()}")
                appointments = response.get("data", [])
                if not appointments and "appointments" in response:
                    appointments = response.get("appointments", [])
            else:
                self.log_signal.emit(f"Unerwartetes Antwortformat: {type(response)}")
                appointments = []
            
            if not appointments:
                self.log_signal.emit(f"Keine CallDoc-Termine für {self.date_str} gefunden.")
                self.finished_signal.emit({"success": False, "error": "Keine Termine gefunden"})
                return
            
            # Filtere nach Datum
            self.log_signal.emit(f"Filtere Termine nach Datum: {self.date_str}")
            filtered_appointments = []
            for appointment in appointments:
                scheduled_date = appointment.get("scheduled_for_datetime", "")
                if scheduled_date and self.date_str in scheduled_date:
                    filtered_appointments.append(appointment)
                    
            self.log_signal.emit(f"Nach Datumsfilterung: {len(filtered_appointments)} von {len(appointments)} Terminen übrig")
            appointments = filtered_appointments
            
            # Filtere nach Termintyp, falls angegeben
            if self.appointment_type_id:
                before_count = len(appointments)
                appointments = [a for a in appointments if a.get("appointment_type_id") == self.appointment_type_id]
                self.log_signal.emit(f"Nach Typfilterung: {len(appointments)} von {before_count} Terminen übrig")
            
            # Filtere nach Status, falls aktiviert
            if self.smart_status_filter:
                # Für vergangene Termine nur abgeschlossene, für zukünftige alle aktiven
                today = datetime.now().strftime("%Y-%m-%d")
                if self.date_str < today:
                    # Vergangene Termine: Nur abgeschlossene
                    appointments = [a for a in appointments if a.get("status") == "completed"]
                else:
                    # Zukünftige Termine: Alle aktiven (nicht storniert)
                    appointments = [a for a in appointments if a.get("status") != "cancelled"]
            
            self.log_signal.emit(f"{len(appointments)} CallDoc-Termine gefunden.")
            
            # Termine als JSON speichern
            with open(f"calldoc_termine_{self.date_str}.json", "w", encoding="utf-8") as f:
                json.dump(appointments, f, indent=2)
            
            # 2. SQLHK-Untersuchungen abrufen
            self.log_signal.emit("2. SQLHK-Untersuchungen abrufen")
            self.update_signal.emit("Rufe SQLHK-Untersuchungen ab...", {"progress": 30})
            
            # Versuche beide Datumsformate
            sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(self.date_str)
            if not sqlhk_untersuchungen:
                sqlhk_untersuchungen = untersuchung_sync.get_sqlhk_untersuchungen(date_str_de)
            
            self.log_signal.emit(f"{len(sqlhk_untersuchungen)} SQLHK-Untersuchungen gefunden.")
            
            # Untersuchungen als JSON speichern
            with open(f"sqlhk_untersuchungen_{self.date_str}.json", "w", encoding="utf-8") as f:
                json.dump(sqlhk_untersuchungen, f, indent=2)
            
            # 3. Patienten synchronisieren
            self.log_signal.emit("3. Patienten synchronisieren")
            self.update_signal.emit("Synchronisiere Patienten...", {"progress": 50})
            patient_stats = patient_sync.synchronize_patients_from_appointments(appointments)
            
            self.log_signal.emit("Patienten-Synchronisierung abgeschlossen:")
            self.log_signal.emit(f"  - Erfolgreiche Operationen: {patient_stats.get('success', 0)}")
            self.log_signal.emit(f"  - Fehler: {patient_stats.get('errors', 0)}")
            self.log_signal.emit(f"  - Eingefügt: {patient_stats.get('inserted', 0)}")
            self.log_signal.emit(f"  - Aktualisiert: {patient_stats.get('updated', 0)}")
            
            # 4. Untersuchungen synchronisieren
            self.log_signal.emit("4. Untersuchungen synchronisieren")
            self.update_signal.emit("Synchronisiere Untersuchungen...", {"progress": 70})
            
            # Zuerst das Mapping von Termintypen zu Untersuchungsarten laden
            untersuchung_sync.load_appointment_type_mapping()
            
            # Dann die Synchronisierung durchführen
            result = untersuchung_sync.synchronize_appointments(
                appointments,
                sqlhk_untersuchungen
            )
            
            # Ausgabe der Ergebnisse
            self.log_signal.emit("Untersuchungs-Synchronisierung abgeschlossen:")
            self.log_signal.emit(f"  - Erfolgreiche Operationen: {result.get('success', 0)}")
            self.log_signal.emit(f"  - Fehler: {result.get('errors', 0)}")
            self.log_signal.emit(f"  - Eingefügt: {result.get('inserted', 0)}")
            self.log_signal.emit(f"  - Aktualisiert: {result.get('updated', 0)}")
            self.log_signal.emit(f"  - Gelöscht: {result.get('deleted', 0)}")
            
            # Speichere die Ergebnisse in einer JSON-Datei
            result_filename = f"sync_result_{self.date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            
            self.log_signal.emit(f"Synchronisierung für {self.date_str} abgeschlossen")
            self.update_signal.emit("Synchronisierung abgeschlossen", {"progress": 100})
            
            # Füge die Patientenstatistik zum Ergebnis hinzu
            result.update({"patient_stats": patient_stats})
            
            # Signal mit dem Ergebnis senden
            self.finished_signal.emit(result)
            
        except Exception as e:
            import traceback
            error_msg = f"Fehler bei der Synchronisierung: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit({"success": False, "error": str(e)})
    
    def stop(self):
        """
        Stoppt den Thread.
        """
        self.running = False
        self.terminate()


class SyncApp(QMainWindow):
    """
    Hauptfenster der Synchronisierungsanwendung.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CallDoc-SQLHK Synchronisierung v5.0")
        self.setGeometry(100, 100, 1200, 800)
        self.sync_worker = None
        self.results = {}
        
        # Initialisiere den ConfigManager
        self.config_manager = ConfigManager()
        
        # Lade die API-URLs aus der Konfiguration
        self.api_urls = self.config_manager.get_api_urls()
        
        # Initialisiere den ConnectionChecker
        self.connection_checker = ConnectionChecker(
            self.api_urls["CALLDOC_API_BASE_URL"],
            self.api_urls["SQLHK_API_BASE_URL"]
        )
        
        # Erstelle Auto-Sync-Scheduler (wird später konfiguriert)
        self.auto_sync_scheduler = None
        
        # Initialisiere UI
        self.initUI()
        
        # Prüfe die Verbindungen beim Start
        self.check_connections_on_startup()
        
    def initUI(self):
        """
        Initialisiert die Benutzeroberfläche.
        """
        # Titel wurde bereits im Konstruktor gesetzt
        self.setGeometry(100, 100, 1000, 700)
        
        # Hauptwidget und Layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Oberer Bereich: Kalender und Parameter
        top_layout = QHBoxLayout()
        
        # Kalender
        calendar_group = QGroupBox("Datum auswählen")
        calendar_layout = QVBoxLayout()
        
        # Datum-Auswahl
        date_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        yesterday_btn = QPushButton("Gestern")
        yesterday_btn.clicked.connect(self.set_yesterday)
        today_btn = QPushButton("Heute")
        today_btn.clicked.connect(self.set_today)
        tomorrow_btn = QPushButton("Morgen")
        tomorrow_btn.clicked.connect(self.set_tomorrow)
        
        date_layout.addWidget(self.date_edit)
        date_layout.addWidget(yesterday_btn)
        date_layout.addWidget(today_btn)
        date_layout.addWidget(tomorrow_btn)
        
        calendar_layout.addLayout(date_layout)
        
        # Kalender-Widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        calendar_group.setLayout(calendar_layout)
        
        # Parameter
        params_group = QGroupBox("Synchronisierungsparameter")
        params_layout = QVBoxLayout()
        
        # Konfigurationsbutton
        config_btn = QPushButton("Konfiguration")
        config_btn.setIcon(QIcon.fromTheme("preferences-system"))
        config_btn.clicked.connect(self.show_config_dialog)
        params_layout.addWidget(config_btn)
        
        # Verbindungsstatus
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Verbindungsstatus:"))
        self.connection_status_label = QLabel("Wird geprüft...")
        self.connection_status_label.setStyleSheet("color: orange;")
        status_layout.addWidget(self.connection_status_label)
        params_layout.addLayout(status_layout)
        
        # Termintyp
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Termintyp:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Alle Typen", None)
        self.type_combo.addItem("Herzkatheteruntersuchung", APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"])
        self.type_combo.addItem("Herzultraschall", APPOINTMENT_TYPES["HERZULTRASCHALL"])
        self.type_combo.addItem("Kardiologische Untersuchung", APPOINTMENT_TYPES["KARDIOLOGISCHE_UNTERSUCHUNG"])
        # Standardmäßig Herzkatheteruntersuchung auswählen (Index 1)
        self.type_combo.setCurrentIndex(1)
        type_layout.addWidget(self.type_combo)
        params_layout.addLayout(type_layout)
        
        # Status-Filter
        self.status_filter_cb = QCheckBox("Intelligenter Status-Filter")
        self.status_filter_cb.setChecked(True)
        self.status_filter_cb.setToolTip("Für vergangene Termine nur abgeschlossene, für zukünftige alle aktiven")
        params_layout.addWidget(self.status_filter_cb)
        
        # Löschlogik
        self.delete_logic_cb = QCheckBox("Obsolete Untersuchungen löschen")
        self.delete_logic_cb.setChecked(True)
        self.delete_logic_cb.setToolTip("Löscht Untersuchungen, die keinem aktiven Termin mehr zugeordnet sind")
        params_layout.addWidget(self.delete_logic_cb)
        
        params_group.setLayout(params_layout)
        
        top_layout.addWidget(calendar_group)
        top_layout.addWidget(params_group)
        
        # Steuerungsbereich
        control_group = QGroupBox("Steuerung")
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Synchronisierung starten")
        self.start_button.clicked.connect(self.start_sync)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.stop_button = QPushButton("Stoppen")
        self.stop_button.clicked.connect(self.stop_sync)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        
        # Button zum Anzeigen der Logs
        self.show_log_button = QPushButton("Log-Datei öffnen")
        self.show_log_button.clicked.connect(self.open_log_file)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.show_log_button)
        
        # Fortschrittsanzeige
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        
        # Tabs für Ergebnisse und Protokoll
        self.tabs = QTabWidget()
        
        # Ergebnisse-Tab
        results_tab = QWidget()
        results_layout = QVBoxLayout()
        
        # Ergebnistabelle
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels([
            "Kategorie", "Erfolge", "Fehler", "Eingefügt", "Aktualisiert"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        
        # Matplotlib-Figur für Diagramme
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)
        
        results_tab.setLayout(results_layout)
        
        # Protokoll-Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_tab.setLayout(log_layout)
        
        self.tabs.addTab(results_tab, "Ergebnisse")
        self.tabs.addTab(log_tab, "Protokoll")
        
        # Alles zum Hauptlayout hinzufügen
        main_layout.addLayout(top_layout)
        main_layout.addWidget(control_group)
        main_layout.addWidget(self.tabs)
        
        # Menüleiste erstellen
        menubar = self.menuBar()
        config_menu = menubar.addMenu('Einstellungen')
        
        # Konfigurationsmenüpunkt
        config_action = QAction('Konfiguration', self)
        config_action.setShortcut('Ctrl+K')
        config_action.setStatusTip('Konfiguration öffnen')
        config_action.triggered.connect(self.show_config_dialog)
        config_menu.addAction(config_action)
        
        # Auto-Sync-Menüpunkte
        auto_sync_menu = config_menu.addMenu('Auto-Sync')
        
        start_auto_sync_action = QAction('Auto-Sync starten', self)
        start_auto_sync_action.setStatusTip('Automatische Synchronisierung starten')
        start_auto_sync_action.triggered.connect(self.start_auto_sync)
        auto_sync_menu.addAction(start_auto_sync_action)
        
        stop_auto_sync_action = QAction('Auto-Sync stoppen', self)
        stop_auto_sync_action.setStatusTip('Automatische Synchronisierung stoppen')
        stop_auto_sync_action.triggered.connect(self.stop_auto_sync)
        auto_sync_menu.addAction(stop_auto_sync_action)
        
        # Statuszeile
        self.statusBar().showMessage('Bereit')
        
        self.show()
    
    @pyqtSlot()
    def set_yesterday(self):
        """
        Setzt das Datum auf gestern.
        """
        yesterday = QDate.currentDate().addDays(-1)
        self.date_edit.setDate(yesterday)
        self.calendar.setSelectedDate(yesterday)
    
    @pyqtSlot()
    def set_today(self):
        """
        Setzt das Datum auf heute.
        """
        today = QDate.currentDate()
        self.date_edit.setDate(today)
        self.calendar.setSelectedDate(today)
    
    @pyqtSlot()
    def set_tomorrow(self):
        """
        Setzt das Datum auf morgen.
        """
        tomorrow = QDate.currentDate().addDays(1)
        self.date_edit.setDate(tomorrow)
        self.calendar.setSelectedDate(tomorrow)
    
    @pyqtSlot(QDate)
    def on_date_selected(self, date):
        """
        Wird aufgerufen, wenn ein Datum im Kalender ausgewählt wird.
        """
        self.date_edit.setDate(date)
        selected_date = date.toString("yyyy-MM-dd")
        self.statusBar().showMessage(f'Datum ausgewählt: {selected_date}')
    
    @pyqtSlot()
    def start_sync(self):
        """
        Startet die Synchronisierung.
        """
        # Prüfe zuerst die Verbindung zum SQLHK-Server
        self.statusBar().showMessage('Prüfe Verbindung zum SQLHK-Server...')
        self.append_log('Prüfe Verbindung zum SQLHK-Server vor der Synchronisierung...')
        
        sqlhk_success, sqlhk_error = self.connection_checker.check_sqlhk_connection()
        
        if not sqlhk_success:
            self.statusBar().showMessage('Synchronisierung abgebrochen: SQLHK-Server nicht erreichbar')
            self.append_log(f'FEHLER: SQLHK-Server nicht erreichbar: {sqlhk_error}')
            
            QMessageBox.critical(
                self,
                "Verbindungsfehler",
                f"Die Synchronisierung kann nicht gestartet werden, da der SQLHK-Server nicht erreichbar ist.\n\n"
                f"Fehlermeldung: {sqlhk_error}\n\n"
                f"Bitte überprüfen Sie die Verbindung und die Server-Einstellungen im Konfigurationsmenü."
            )
            return
        
        # Prüfe die Verbindung zum CallDoc-Server
        self.statusBar().showMessage('Prüfe Verbindung zum CallDoc-Server...')
        self.append_log('Prüfe Verbindung zum CallDoc-Server vor der Synchronisierung...')
        
        calldoc_success, calldoc_error = self.connection_checker.check_calldoc_connection()
        
        if not calldoc_success:
            self.statusBar().showMessage('Synchronisierung abgebrochen: CallDoc-Server nicht erreichbar')
            self.append_log(f'FEHLER: CallDoc-Server nicht erreichbar: {calldoc_error}')
            
            QMessageBox.critical(
                self,
                "Verbindungsfehler",
                f"Die Synchronisierung kann nicht gestartet werden, da der CallDoc-Server nicht erreichbar ist.\n\n"
                f"Fehlermeldung: {calldoc_error}\n\n"
                f"Bitte überprüfen Sie die Verbindung und die Server-Einstellungen im Konfigurationsmenü."
            )
            return
        
        # Wenn beide Verbindungen erfolgreich sind, starte die Synchronisierung
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        appointment_type_id = self.type_combo.currentData()
        smart_status_filter = self.status_filter_cb.isChecked()
        
        self.statusBar().showMessage(f'Synchronisierung für {selected_date} gestartet...')
        self.append_log(f'Synchronisierung für {selected_date} gestartet...')
        
        # UI-Elemente aktualisieren
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Worker-Thread starten
        self.sync_worker = SyncWorker(
            selected_date, 
            appointment_type_id, 
            smart_status_filter
        )
        self.sync_worker.update_signal.connect(self.update_status)
        self.sync_worker.finished_signal.connect(self.sync_finished)
        self.sync_worker.log_signal.connect(self.append_log)
        self.sync_worker.start()
    
    @pyqtSlot()
    def stop_sync(self):
        """
        Stoppt die Synchronisierung.
        """
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()
            self.statusBar().showMessage('Synchronisierung gestoppt')
            self.log_text.append('Synchronisierung gestoppt')
            
            # UI-Elemente aktualisieren
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    @pyqtSlot(str, dict)
    def update_status(self, status, data):
        """
        Aktualisiert den Status und die Fortschrittsanzeige.
        """
        self.statusBar().showMessage(status)
        
        if "progress" in data:
            self.progress_bar.setValue(data["progress"])
    
    @pyqtSlot(dict)
    def sync_finished(self, result):
        """
        Wird aufgerufen, wenn die Synchronisierung abgeschlossen ist.
        """
        # UI-Elemente aktualisieren
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100)
        
        # Ergebnisse speichern
        self.sync_results = result
        
        # Ergebnistabelle aktualisieren
        self.update_results_table(result)
        
        # Diagramm aktualisieren
        self.update_chart(result)
        
        # Status aktualisieren
        if result.get("success", 0) > 0:
            self.statusBar().showMessage('Synchronisierung erfolgreich abgeschlossen')
        else:
            self.statusBar().showMessage(f'Synchronisierung mit Fehlern: {result.get("error", "Unbekannter Fehler")}')
    
    def update_results_table(self, result):
        """
        Aktualisiert die Ergebnistabelle.
        """
        self.results_table.setRowCount(0)
        
        # Untersuchungen
        self.add_result_row("Untersuchungen", result)
        
        # Patienten
        if "patient_stats" in result:
            self.add_result_row("Patienten", result["patient_stats"])
    
    def add_result_row(self, category, data):
        """
        Fügt eine Zeile zur Ergebnistabelle hinzu.
        """
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(category))
        self.results_table.setItem(row, 1, QTableWidgetItem(str(data.get("success", 0))))
        self.results_table.setItem(row, 2, QTableWidgetItem(str(data.get("errors", 0))))
        self.results_table.setItem(row, 3, QTableWidgetItem(str(data.get("inserted", 0))))
        self.results_table.setItem(row, 4, QTableWidgetItem(str(data.get("updated", 0))))
    
    def update_chart(self, result):
        """
        Aktualisiert das Diagramm mit den Synchronisierungsergebnissen.
        """
        self.figure.clear()
        
        # Daten vorbereiten
        categories = ['Eingefügt', 'Aktualisiert', 'Gelöscht', 'Fehler']
        values = [
            result.get('inserted', 0),
            result.get('updated', 0),
            result.get('deleted', 0),
            result.get('errors', 0)
        ]
        
        # Diagramm erstellen
        ax = self.figure.add_subplot(111)
        bars = ax.bar(categories, values)
        
        # Farben für die Balken
        colors = ['green', 'blue', 'red', 'orange']
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_title('Synchronisierungsergebnisse')
        ax.set_ylabel('Anzahl')
        
        # Werte über den Balken anzeigen
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        self.canvas.draw()
    
    @pyqtSlot(str)
    def append_log(self, text):
        """
        Fügt Text zum Protokoll hinzu.
        """
        self.log_text.append(text)
        # Scrolle zum Ende des Textes
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
        # Auch in die Log-Datei schreiben
        logger.info(text)
        
    def open_log_file(self):
        """
        Öffnet die aktuelle Log-Datei im Standard-Texteditor.
        """
        try:
            import os
            os.startfile(log_filename)
        except Exception as e:
            self.statusBar().showMessage(f"Fehler beim Öffnen der Log-Datei: {str(e)}")
            QMessageBox.warning(self, "Fehler", f"Die Log-Datei konnte nicht geöffnet werden: {str(e)}")
    
    def check_connections_on_startup(self):
        """
        Prüft die Verbindungen zu den API-Servern beim Start der Anwendung.
        """
        self.append_log("Prüfe Verbindungen zu den API-Servern...")
        
        # Prüfe SQLHK-Verbindung (wichtiger für die Synchronisierung)
        sqlhk_success, sqlhk_error = self.connection_checker.check_sqlhk_connection()
        
        if not sqlhk_success:
            self.append_log(f"WARNUNG: SQLHK-Server nicht erreichbar: {sqlhk_error}")
            self.connection_status_label.setText("SQLHK: Nicht verbunden")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("SQLHK-Server nicht erreichbar")
            msg.setInformativeText(f"Der SQLHK-Server unter {self.api_urls['SQLHK_API_BASE_URL']} ist nicht erreichbar.\n\n"
                                  f"Fehlermeldung: {sqlhk_error}\n\n"
                                  f"Die Synchronisierung kann ohne Verbindung zum SQLHK-Server nicht durchgeführt werden.\n\n"
                                  f"Bitte überprüfen Sie die Server-Einstellungen im Konfigurationsmenü.")
            msg.setWindowTitle("Verbindungsproblem")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            self.append_log("SQLHK-Server erfolgreich verbunden.")
        
        # Prüfe CallDoc-Verbindung
        calldoc_success, calldoc_error = self.connection_checker.check_calldoc_connection()
        
        if not calldoc_success:
            self.append_log(f"WARNUNG: CallDoc-Server nicht erreichbar: {calldoc_error}")
            self.connection_status_label.setText("CallDoc: Nicht verbunden")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("CallDoc-Server nicht erreichbar")
            msg.setInformativeText(f"Der CallDoc-Server unter {self.api_urls['CALLDOC_API_BASE_URL']} ist nicht erreichbar.\n\n"
                                  f"Fehlermeldung: {calldoc_error}\n\n"
                                  f"Die Synchronisierung kann ohne Verbindung zum CallDoc-Server nicht durchgeführt werden.\n\n"
                                  f"Bitte überprüfen Sie die Server-Einstellungen im Konfigurationsmenü.")
            msg.setWindowTitle("Verbindungsproblem")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            self.append_log("CallDoc-Server erfolgreich verbunden.")
        
        # Aktualisiere den Verbindungsstatus in der GUI
        if sqlhk_success and calldoc_success:
            self.connection_status_label.setText("Alle Server verbunden")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Richte die automatische Synchronisierung ein
            self.setup_auto_sync()
        elif sqlhk_success:
            self.connection_status_label.setText("SQLHK: OK, CallDoc: Fehler")
            self.connection_status_label.setStyleSheet("color: orange; font-weight: bold;")
        elif calldoc_success:
            self.connection_status_label.setText("CallDoc: OK, SQLHK: Fehler")
            self.connection_status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.connection_status_label.setText("Keine Verbindung")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def show_config_dialog(self):
        """
        Zeigt den Konfigurationsdialog an.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Konfiguration")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Tabs für verschiedene Konfigurationsbereiche
        tabs = QTabWidget()
        
        # API-URLs Tab
        api_tab = QWidget()
        api_layout = QFormLayout()
        
        calldoc_url_input = QLineEdit(self.api_urls["CALLDOC_API_BASE_URL"])
        sqlhk_url_input = QLineEdit(self.api_urls["SQLHK_API_BASE_URL"])
        
        api_layout.addRow("CallDoc API URL:", calldoc_url_input)
        api_layout.addRow("SQLHK API URL:", sqlhk_url_input)
        
        # Test-Buttons
        test_calldoc_btn = QPushButton("Verbindung testen")
        test_sqlhk_btn = QPushButton("Verbindung testen")
        
        api_layout.addRow("", test_calldoc_btn)
        api_layout.addRow("", test_sqlhk_btn)
        
        api_tab.setLayout(api_layout)
        
        # Auto-Sync Tab
        auto_sync_tab = QWidget()
        auto_sync_layout = QFormLayout()
        
        # Hole die aktuellen Auto-Sync-Einstellungen
        auto_sync_settings = self.config_manager.get_auto_sync_settings()
        
        enabled_checkbox = QCheckBox("Automatische Synchronisierung aktivieren")
        enabled_checkbox.setChecked(auto_sync_settings["auto_sync_enabled"])
        
        interval_input = QLineEdit(str(auto_sync_settings["auto_sync_interval"]))
        interval_input.setValidator(QIntValidator(5, 1440))  # 5 Minuten bis 24 Stunden
        
        start_time = QTime.fromString(auto_sync_settings["start_time"], "HH:mm")
        end_time = QTime.fromString(auto_sync_settings["end_time"], "HH:mm")
        
        start_time_input = QTimeEdit(start_time)
        start_time_input.setDisplayFormat("HH:mm")
        
        end_time_input = QTimeEdit(end_time)
        end_time_input.setDisplayFormat("HH:mm")
        
        auto_sync_layout.addRow(enabled_checkbox)
        auto_sync_layout.addRow("Intervall (Minuten):", interval_input)
        auto_sync_layout.addRow("Startzeit:", start_time_input)
        auto_sync_layout.addRow("Endzeit:", end_time_input)
        
        # Wochentage
        days_layout = QHBoxLayout()
        day_checkboxes = []
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        day_codes = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        days_container = QWidget()
        days_container.setLayout(days_layout)
        
        for i, (day, day_code) in enumerate(zip(days, day_codes)):
            cb = QCheckBox(day)
            cb.setChecked(day_code in auto_sync_settings["active_days"])
            days_layout.addWidget(cb)
            day_checkboxes.append((cb, day_code))
        
        auto_sync_layout.addRow("Tage:", days_container)
        auto_sync_tab.setLayout(auto_sync_layout)
        
        # Füge die Tabs hinzu
        tabs.addTab(api_tab, "API-URLs")
        tabs.addTab(auto_sync_tab, "Auto-Sync")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Speichern")
        cancel_btn = QPushButton("Abbrechen")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Verbinde Signale
        cancel_btn.clicked.connect(dialog.reject)
        
        # Test-Button-Funktionen
        def test_calldoc_connection():
            checker = ConnectionChecker(calldoc_url_input.text(), "")
            success, error = checker.check_calldoc_connection()
            if success:
                QMessageBox.information(dialog, "Verbindungstest", "Verbindung zum CallDoc-Server erfolgreich!")
            else:
                QMessageBox.warning(dialog, "Verbindungstest", f"Verbindung zum CallDoc-Server fehlgeschlagen: {error}")
        
        def test_sqlhk_connection():
            checker = ConnectionChecker("", sqlhk_url_input.text())
            success, error = checker.check_sqlhk_connection()
            if success:
                QMessageBox.information(dialog, "Verbindungstest", "Verbindung zum SQLHK-Server erfolgreich!")
            else:
                QMessageBox.warning(dialog, "Verbindungstest", f"Verbindung zum SQLHK-Server fehlgeschlagen: {error}")
        
        test_calldoc_btn.clicked.connect(test_calldoc_connection)
        test_sqlhk_btn.clicked.connect(test_sqlhk_connection)
        
        # Speichern-Funktion
        def save_config():
            # API-URLs speichern
            new_api_urls = {
                "CALLDOC_API_BASE_URL": calldoc_url_input.text(),
                "SQLHK_API_BASE_URL": sqlhk_url_input.text()
            }
            self.config_manager.update_api_urls(new_api_urls)
            
            # Auto-Sync-Einstellungen speichern
            active_days = [day_code for cb, day_code in day_checkboxes if cb.isChecked()]
            new_auto_sync_settings = {
                "auto_sync_enabled": enabled_checkbox.isChecked(),
                "auto_sync_interval": int(interval_input.text()),
                "start_time": start_time_input.time().toString("HH:mm"),
                "end_time": end_time_input.time().toString("HH:mm"),
                "active_days": active_days
            }
            self.config_manager.update_auto_sync_settings(new_auto_sync_settings)
            
            # Aktualisiere die lokalen Einstellungen
            self.api_urls = self.config_manager.get_api_urls()
            
            # Aktualisiere den Verbindungsprüfer mit den neuen URLs
            self.connection_checker = ConnectionChecker(
                self.api_urls["CALLDOC_API_BASE_URL"],
                self.api_urls["SQLHK_API_BASE_URL"]
            )
            
            # Prüfe die Verbindungen mit den neuen URLs
            self.check_connections_on_startup()
            
            # Aktualisiere den Auto-Sync-Scheduler mit den neuen Einstellungen
            self.setup_auto_sync()
            
            self.append_log("Konfiguration gespeichert und angewendet.")
            self.statusBar().showMessage("Konfiguration gespeichert und angewendet.")
            dialog.accept()
        
        save_btn.clicked.connect(save_config)
        
        # Zeige den Dialog
        dialog.exec_()
    
    def setup_auto_sync(self):
        """
        Richtet die automatische Synchronisierung basierend auf den Konfigurationseinstellungen ein.
        """
        # Hole die aktuellen Auto-Sync-Einstellungen aus dem ConfigManager
        auto_sync_settings = self.config_manager.get_auto_sync_settings()
        
        # Erstelle eine Funktion für die automatische Synchronisierung, falls noch nicht vorhanden
        if not hasattr(self, '_auto_sync_function'):
            def auto_sync_function():
                # Setze das Datum auf heute
                self.set_today()
                # Starte die Synchronisierung
                self.start_sync()
            self._auto_sync_function = auto_sync_function
        
        # Erstelle den Scheduler, falls noch nicht vorhanden
        if not self.auto_sync_scheduler:
            # Die Einstellungen aus dem ConfigManager verwenden
            self.auto_sync_scheduler = AutoSyncScheduler(self._auto_sync_function, auto_sync_settings)
        
        # Konfiguriere und starte den Scheduler basierend auf den Einstellungen
        if auto_sync_settings['ENABLED']:
            self.append_log("Automatische Synchronisierung wird eingerichtet...")
            self.append_log(f"Intervall: {auto_sync_settings['INTERVAL_MINUTES']} Minuten")
            self.append_log(f"Aktive Tage: {', '.join(map(str, auto_sync_settings['DAYS']))}")
            self.append_log(f"Zeitfenster: {auto_sync_settings['START_TIME']} - {auto_sync_settings['END_TIME']}")
            
            # Starte den Auto-Sync-Scheduler mit den aktuellen Einstellungen
            self.auto_sync_scheduler.start_scheduler(
                interval_minutes=auto_sync_settings['INTERVAL_MINUTES'],
                active_days=auto_sync_settings['DAYS'],
                start_time=auto_sync_settings['START_TIME'],
                end_time=auto_sync_settings['END_TIME']
            )
            self.statusBar().showMessage('Automatische Synchronisierung aktiviert')
        else:
            self.append_log("Automatische Synchronisierung ist deaktiviert.")
            self.auto_sync_scheduler.stop()
            self.statusBar().showMessage('Automatische Synchronisierung deaktiviert')
    
    def start_auto_sync(self):
        """
        Startet die automatische Synchronisierung manuell.
        """
        # Prüfe zuerst die Verbindungen
        sqlhk_success, _ = self.connection_checker.check_sqlhk_connection()
        calldoc_success, _ = self.connection_checker.check_calldoc_connection()
        
        if not sqlhk_success or not calldoc_success:
            QMessageBox.warning(
                self,
                "Verbindungsproblem",
                "Die automatische Synchronisierung kann nicht gestartet werden, da nicht alle Server erreichbar sind.\n\n"
                "Bitte überprüfen Sie die Verbindungen und versuchen Sie es erneut."
            )
            return
        
        # Hole die aktuellen Auto-Sync-Einstellungen
        auto_sync_settings = self.config_manager.get_auto_sync_settings()
        
        # Aktiviere die automatische Synchronisierung
        self.config_manager.set_value("AUTO_SYNC", "ENABLED", "True")
        # Konfiguration speichern
        self.config_manager.save_config()
        
        # Starte den Scheduler
        self.setup_auto_sync()
        
        self.append_log("Automatische Synchronisierung wurde manuell gestartet.")
        self.statusBar().showMessage('Automatische Synchronisierung aktiviert')
    
    def stop_auto_sync(self):
        """
        Stoppt die automatische Synchronisierung manuell.
        """
        if not self.auto_sync_scheduler:
            self.append_log("Automatische Synchronisierung ist nicht konfiguriert.")
            return
        
        # Hole die aktuellen Auto-Sync-Einstellungen
        auto_sync_settings = self.config_manager.get_auto_sync_settings()
        
        # Deaktiviere die automatische Synchronisierung
        self.config_manager.set_value("AUTO_SYNC", "ENABLED", "False")
        # Konfiguration speichern
        self.config_manager.save_config()
        
        # Stoppe den Scheduler
        self.auto_sync_scheduler.stop()
        
        self.append_log("Automatische Synchronisierung wurde manuell gestoppt.")
        self.statusBar().showMessage('Automatische Synchronisierung deaktiviert')


def main():
    """
    Hauptfunktion für den Start der Anwendung.
    """
    app = QApplication(sys.argv)
    ex = SyncApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
