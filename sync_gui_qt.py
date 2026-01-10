#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CallDoc-SQLHK Synchronisierung - Grafische Benutzeroberfläche

Diese Datei enthält eine moderne GUI für die Synchronisierung von Untersuchungsdaten
zwischen dem CallDoc-System und der SQLHK-Datenbank.

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
                            QMenuBar, QMenu, QDialog, QDialogButtonBox, QAction)
from PyQt5.QtCore import QDate, pyqtSlot, Qt, QThread, pyqtSignal, QTimer, QTime
from PyQt5.QtGui import QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import der Synchronisierungskomponenten
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer
from appointment_patient_enricher import AppointmentPatientEnricher
from constants import APPOINTMENT_TYPES

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
                # API gibt "appointment_type" zurück, nicht "appointment_type_id"
                appointments = [a for a in appointments if a.get("appointment_type") == self.appointment_type_id]
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
            
            # Patientendaten anreichern
            self.log_signal.emit("Reichere Termine mit Patientendaten an...")
            patient_cache = {}
            MAX_CACHE_SIZE = 1000  # Begrenze Cache-Größe zur Vermeidung von Memory Leaks
            
            for appointment in appointments:
                # Cache-Größe prüfen und ggf. leeren
                if len(patient_cache) > MAX_CACHE_SIZE:
                    self.log_signal.emit(f"Cache-Limit erreicht ({MAX_CACHE_SIZE}), leere Cache...")
                    patient_cache.clear()
                piz = appointment.get("piz")
                if piz and piz not in patient_cache:
                    try:
                        self.log_signal.emit(f"Lade Patientendaten für PIZ {piz}...")
                        patient_response = calldoc_client.get_patient_by_piz(piz)
                        if patient_response and not patient_response.get("error"):
                            patients_list = patient_response.get("patients", [])
                            if patients_list and len(patients_list) > 0 and patients_list[0] is not None:
                                patient_data = patients_list[0]
                                # Zusätzlicher Check ob patient_data valide ist
                                if not isinstance(patient_data, dict):
                                    self.log_signal.emit(f"Warnung: Ungültiges Patientendaten-Format für PIZ {piz}")
                                    continue
                                patient_cache[piz] = patient_data
                                # Füge Patientendaten zum Termin hinzu
                                appointment["patient"] = {
                                    "id": patient_data.get("id"),
                                    "piz": piz,
                                    "surname": patient_data.get("surname"),
                                    "name": patient_data.get("name"),
                                    "date_of_birth": patient_data.get("date_of_birth"),
                                    "insurance_number": patient_data.get("insurance_number"),
                                    "insurance_provider": patient_data.get("insurance_provider")
                                }
                                self.log_signal.emit(f"Patient gefunden: {patient_data.get('surname')}, {patient_data.get('name')}")
                    except Exception as e:
                        self.log_signal.emit(f"Fehler beim Laden der Patientendaten für PIZ {piz}: {str(e)}")
                elif piz in patient_cache:
                    # Verwende gecachte Patientendaten
                    patient_data = patient_cache[piz]
                    appointment["patient"] = {
                        "id": patient_data.get("id"),
                        "piz": piz,
                        "surname": patient_data.get("surname"),
                        "name": patient_data.get("name"),
                        "date_of_birth": patient_data.get("date_of_birth"),
                        "insurance_number": patient_data.get("insurance_number"),
                        "insurance_provider": patient_data.get("insurance_provider")
                    }
            
            self.log_signal.emit(f"Patientendaten-Anreicherung abgeschlossen")
            
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
            
            # 5. KVDT-Datenanreicherung (optional)
            self.log_signal.emit("5. KVDT-Datenanreicherung starten...")
            self.update_signal.emit("Reichere Patientendaten aus KVDT an...", {"progress": 85})

            try:
                # M1Ziffern aus den Terminen extrahieren
                m1ziffern = []
                for apt in appointments:
                    piz = apt.get("piz")
                    if piz and piz not in m1ziffern:
                        m1ziffern.append(piz)

                if m1ziffern:
                    self.log_signal.emit(f"  {len(m1ziffern)} Patienten zur KVDT-Anreicherung")

                    from kvdt_enricher import KVDTEnricher
                    enricher = KVDTEnricher()

                    enrichment_stats = enricher.enrich_patients(m1ziffern)

                    self.log_signal.emit("KVDT-Anreicherung abgeschlossen:")
                    self.log_signal.emit(f"  - In KVDT gefunden: {enrichment_stats.get('found', 0)}")
                    self.log_signal.emit(f"  - Angereichert: {enrichment_stats.get('enriched', 0)}")
                    self.log_signal.emit(f"  - Nicht gefunden: {enrichment_stats.get('not_found', 0)}")

                    result["kvdt_enrichment"] = enrichment_stats
                else:
                    self.log_signal.emit("  Keine Patienten zur KVDT-Anreicherung")

            except ImportError as e:
                self.log_signal.emit(f"  KVDT-Modul nicht verfuegbar: {e}")
            except Exception as e:
                self.log_signal.emit(f"  KVDT-Anreicherung fehlgeschlagen: {e}")

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
        Stoppt den Thread sicher (graceful shutdown).
        """
        self.running = False
        # Warte bis Thread sauber beendet ist (max 5 Sekunden)
        if self.isRunning():
            self.wait(5000)
            # Nur als letztes Mittel hart terminieren
            if self.isRunning():
                self.terminate()
                self.wait(1000)  # Kurz warten nach terminate


class SyncApp(QMainWindow):
    """
    Hauptfenster der Synchronisierungs-GUI.
    """
    def __init__(self):
        super().__init__()
        self.title = 'CallDoc-SQLHK Synchronisierung'
        self.sync_worker = None
        self.sync_results = {}
        self.api_server_thread = None
        self.api_server = None
        self.api_server_running = False

        # Auto-Sync Scheduler
        self.auto_sync_enabled = False
        self.auto_sync_time = QTime(7, 0)  # 07:00 Uhr
        self.last_auto_sync_date = None  # Datum des letzten Auto-Syncs
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self.check_scheduled_sync)

        self.initUI()
        self.load_scheduler_settings()
        self.start_api_server_background()
        self.start_scheduler()
        
    def initUI(self):
        """
        Initialisiert die Benutzeroberfläche.
        """
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1000, 700)
        
        # Menüleiste erstellen
        self.create_menu_bar()
        
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

        # Trennlinie
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        params_layout.addWidget(separator)

        # Auto-Sync Einstellungen
        auto_sync_label = QLabel("Automatische Synchronisierung:")
        auto_sync_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        params_layout.addWidget(auto_sync_label)

        # Auto-Sync Checkbox
        self.auto_sync_cb = QCheckBox("Taeglich automatisch synchronisieren")
        self.auto_sync_cb.setChecked(False)
        self.auto_sync_cb.stateChanged.connect(self.on_auto_sync_changed)
        self.auto_sync_cb.setToolTip("Synchronisiert jeden Tag automatisch zur eingestellten Uhrzeit")
        params_layout.addWidget(self.auto_sync_cb)

        # Zeit-Auswahl
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Uhrzeit:"))
        from PyQt5.QtWidgets import QTimeEdit
        self.auto_sync_time_edit = QTimeEdit(QTime(7, 0))
        self.auto_sync_time_edit.setDisplayFormat("HH:mm")
        self.auto_sync_time_edit.timeChanged.connect(self.on_auto_sync_time_changed)
        time_layout.addWidget(self.auto_sync_time_edit)
        time_layout.addStretch()
        params_layout.addLayout(time_layout)

        # Status-Anzeige
        self.auto_sync_status_label = QLabel("Auto-Sync: Deaktiviert")
        self.auto_sync_status_label.setStyleSheet("color: gray; font-style: italic;")
        params_layout.addWidget(self.auto_sync_status_label)

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
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        appointment_type_id = self.type_combo.currentData()
        smart_status_filter = self.status_filter_cb.isChecked()
        
        self.statusBar().showMessage(f'Synchronisierung für {selected_date} gestartet...')
        self.log_text.append(f'Synchronisierung für {selected_date} gestartet...')
        
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
    
    def create_menu_bar(self):
        """
        Erstellt die Menüleiste mit API-Menü.
        """
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu('Datei')
        
        # Export Action
        export_action = QAction('Logs exportieren', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_logs)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit Action
        exit_action = QAction('Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # API-Menü
        api_menu = menubar.addMenu('API')
        
        # API Dokumentation
        api_doc_action = QAction('API Dokumentation', self)
        api_doc_action.setShortcut('F1')
        api_doc_action.triggered.connect(self.show_api_documentation)
        api_menu.addAction(api_doc_action)
        
        api_menu.addSeparator()
        
        # API Server starten
        self.start_api_action = QAction('API Server starten', self)
        self.start_api_action.triggered.connect(self.start_api_server)
        api_menu.addAction(self.start_api_action)
        
        # API Server stoppen
        self.stop_api_action = QAction('API Server stoppen', self)
        self.stop_api_action.triggered.connect(self.stop_api_server)
        self.stop_api_action.setEnabled(False)
        api_menu.addAction(self.stop_api_action)
        
        api_menu.addSeparator()
        
        # API Test
        api_test_action = QAction('API testen', self)
        api_test_action.triggered.connect(self.test_api)
        api_menu.addAction(api_test_action)

        # Standorte-Menü
        standorte_menu = menubar.addMenu('Standorte')

        # Herzkatheter-Standorte verwalten
        standorte_action = QAction('Herzkatheter-Standorte verwalten', self)
        standorte_action.setShortcut('Ctrl+H')
        standorte_action.triggered.connect(self.show_standorte_dialog)
        standorte_menu.addAction(standorte_action)

        # Hilfe-Menü
        help_menu = menubar.addMenu('Hilfe')
        
        # Über
        about_action = QAction('Über', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # API Server Thread Variable
        self.api_server_thread = None
        self.api_server_running = False
    
    def show_api_documentation(self):
        """
        Zeigt die API Dokumentation in einem Modal Dialog.
        """
        from api_documentation_dialog import APIDocumentationDialog
        dialog = APIDocumentationDialog(self, self.api_server_running)
        dialog.exec_()

    def show_standorte_dialog(self):
        """
        Zeigt den Dialog zur Verwaltung der Herzkatheter-Standorte.
        """
        from standorte_dialog import StandorteDialog
        dialog = StandorteDialog(self)
        dialog.exec_()

    def start_api_server(self):
        """
        Startet den API Server in einem separaten Thread.
        """
        try:
            import threading
            from sync_api_server import app
            
            def run_server():
                app.run(host='0.0.0.0', port=5555, debug=False, use_reloader=False)
            
            self.api_server_thread = threading.Thread(target=run_server, daemon=True)
            self.api_server_thread.start()
            
            self.api_server_running = True
            self.start_api_action.setEnabled(False)
            self.stop_api_action.setEnabled(True)
            
            QMessageBox.information(
                self,
                "API Server",
                "API Server wurde gestartet auf Port 5555.\n\n"
                "Endpoint: http://localhost:5555/api/sync\n"
                "Dokumentation: Menü -> API -> API Dokumentation"
            )
            self.append_log("API Server gestartet auf Port 5555")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte API Server nicht starten: {str(e)}")
    
    def stop_api_server(self):
        """
        Stoppt den API Server.
        """
        # Flask hat keine eingebaute Stop-Methode
        # Server wird beim Beenden der Anwendung gestoppt
        self.api_server_running = False
        self.start_api_action.setEnabled(True)
        self.stop_api_action.setEnabled(False)
        self.append_log("API Server gestoppt")
        QMessageBox.information(self, "API Server", "API Server wurde gestoppt.")
    
    def test_api(self):
        """
        Testet die API Verbindung.
        """
        import requests
        try:
            response = requests.get("http://localhost:5555/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                QMessageBox.information(
                    self,
                    "API Test",
                    f"API ist online!\n\n"
                    f"Status: {data['status']}\n"
                    f"Aktive Syncs: {data['active_syncs']}"
                )
            else:
                QMessageBox.warning(self, "API Test", f"API antwortet mit Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(
                self,
                "API Test",
                "API ist nicht erreichbar.\n\n"
                "Starten Sie den API Server über:\n"
                "Menü -> API -> API Server starten"
            )
        except Exception as e:
            QMessageBox.critical(self, "API Test", f"Fehler: {str(e)}")
    
    def start_api_server_background(self):
        """
        Startet den API-Server im Hintergrund.
        API läuft auf Port 5555 und ermöglicht Single-Patient Synchronisation.
        """
        try:
            import threading
            from werkzeug.serving import make_server
            from sync_api_server import app
            
            # Der Server muss im Thread laufen, aber wir können noch nicht loggen
            # da die GUI noch nicht vollständig initialisiert ist
            def run_api():
                try:
                    self.api_server_running = True
                    print("API Server wird auf Port 5555 gestartet...")
                    
                    # Verwende Werkzeug's make_server für nicht-blockierenden Server
                    server = make_server('0.0.0.0', 5555, app, threaded=True)
                    self.api_server = server
                    
                    print("API Server läuft auf http://localhost:5555")
                    # serve_forever blockiert, aber läuft in eigenem Thread
                    server.serve_forever()
                    
                except Exception as e:
                    self.api_server_running = False
                    print(f"API Server Fehler: {str(e)}")
            
            # Starte API in separatem Thread
            self.api_server_thread = threading.Thread(target=run_api)
            self.api_server_thread.daemon = True  # Thread stirbt mit GUI
            self.api_server_thread.start()
            
            # Kurz warten und Status prüfen
            import time
            time.sleep(2)
            
            # Prüfe ob Server wirklich läuft
            import requests
            try:
                response = requests.get("http://localhost:5555/health", timeout=1)
                if response.status_code == 200:
                    print("✅ API Server läuft auf http://localhost:5555")
                    print("Single-Patient API verfügbar: POST /api/sync/patient")
                    # Später in GUI loggen wenn append_log verfügbar
                    if hasattr(self, 'log_text'):
                        self.append_log("✅ API Server läuft auf http://localhost:5555")
                        self.append_log("Single-Patient API verfügbar: POST /api/sync/patient")
            except:
                print("⚠️ API Server startet noch...")
            
        except Exception as e:
            print(f"Fehler beim Starten des API-Servers: {str(e)}")
    
    def closeEvent(self, event):
        """
        Wird aufgerufen wenn das Fenster geschlossen wird.
        Stoppt den API-Server sauber.
        """
        if self.api_server_thread and self.api_server_thread.is_alive():
            if hasattr(self, 'log_text'):
                self.append_log("Stoppe API Server...")
            else:
                print("Stoppe API Server...")
            # Stoppe den Werkzeug-Server
            if hasattr(self, 'api_server'):
                try:
                    self.api_server.shutdown()
                except:
                    pass
            # Thread ist daemon=True, wird automatisch beendet
        
        # Stoppe laufende Synchronisation wenn vorhanden
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()
            self.sync_worker.wait()
        
        event.accept()
    
    def export_logs(self):
        """
        Exportiert die Logs in eine Datei.
        """
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Logs exportieren",
            f"sync_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Export", f"Logs wurden exportiert nach:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Logs nicht exportieren: {str(e)}")
    
    def show_about(self):
        """
        Zeigt About Dialog.
        """
        QMessageBox.about(
            self,
            "Über CallDoc-SQLHK Sync",
            "CallDoc-SQLHK Synchronisierung v2.0\n\n"
            "Bidirektionale Synchronisation zwischen CallDoc und SQLHK.\n\n"
            "Features:\n"
            "• Automatische Patienten-Synchronisierung\n"
            "• Untersuchungs-Synchronisierung\n"
            "• REST API für Automation\n"
            "• Echtzeit-Logging\n\n"
            "Autor: Markus\n"
            "© 2025"
        )
    
    def start_api_server_requested(self):
        """
        Wird vom API Dialog aufgerufen wenn Server gestartet werden soll.
        """
        self.start_api_server()
    
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

    # =========================================================================
    # AUTO-SYNC SCHEDULER METHODEN
    # =========================================================================

    def start_scheduler(self):
        """
        Startet den Scheduler-Timer der jede Minute prueft.
        """
        # Timer prueft jede Minute ob Sync-Zeit erreicht
        self.scheduler_timer.start(60000)  # 60 Sekunden
        self.last_auto_sync_date = None
        logger.info("Scheduler gestartet - prueft jede Minute")

    def check_scheduled_sync(self):
        """
        Wird jede Minute aufgerufen und prueft ob Auto-Sync ausgefuehrt werden soll.
        """
        if not self.auto_sync_enabled:
            return

        current_time = QTime.currentTime()
        current_date = QDate.currentDate()

        # Pruefe ob aktuelle Zeit im Fenster der Sync-Zeit liegt (+-1 Minute)
        sync_time = self.auto_sync_time
        time_diff = abs(current_time.secsTo(sync_time))

        # Sync ausfuehren wenn:
        # 1. Zeit stimmt (innerhalb 60 Sekunden)
        # 2. Heute noch nicht synchronisiert wurde
        if time_diff < 60 and self.last_auto_sync_date != current_date:
            self.last_auto_sync_date = current_date
            logger.info(f"Auto-Sync gestartet um {current_time.toString('HH:mm')}")
            self.run_auto_sync()

    def run_auto_sync(self):
        """
        Fuehrt die automatische Synchronisierung fuer heute aus.
        """
        # Setze Datum auf heute
        today = QDate.currentDate()
        self.date_edit.setDate(today)

        # Log-Eintrag
        self.append_log(f"\n{'='*50}")
        self.append_log(f"AUTO-SYNC gestartet um {datetime.now().strftime('%H:%M:%S')}")
        self.append_log(f"Synchronisiere Termine fuer {today.toString('yyyy-MM-dd')}")
        self.append_log(f"{'='*50}\n")

        # Starte Synchronisierung
        self.start_sync()

        # Status aktualisieren
        self.update_auto_sync_status()

    def on_auto_sync_changed(self, state):
        """
        Wird aufgerufen wenn Auto-Sync Checkbox geaendert wird.
        """
        self.auto_sync_enabled = (state == Qt.Checked)
        self.save_scheduler_settings()
        self.update_auto_sync_status()

        if self.auto_sync_enabled:
            logger.info(f"Auto-Sync aktiviert - taeglich um {self.auto_sync_time.toString('HH:mm')}")
            self.append_log(f"Auto-Sync aktiviert - taeglich um {self.auto_sync_time.toString('HH:mm')}")
        else:
            logger.info("Auto-Sync deaktiviert")
            self.append_log("Auto-Sync deaktiviert")

    def on_auto_sync_time_changed(self, time):
        """
        Wird aufgerufen wenn die Sync-Zeit geaendert wird.
        """
        self.auto_sync_time = time
        self.save_scheduler_settings()
        self.update_auto_sync_status()

        if self.auto_sync_enabled:
            logger.info(f"Auto-Sync Zeit geaendert auf {time.toString('HH:mm')}")

    def update_auto_sync_status(self):
        """
        Aktualisiert die Status-Anzeige fuer Auto-Sync.
        """
        if self.auto_sync_enabled:
            time_str = self.auto_sync_time.toString('HH:mm')
            if self.last_auto_sync_date is not None and self.last_auto_sync_date == QDate.currentDate():
                status = f"Auto-Sync: Aktiv (naechster Sync morgen um {time_str})"
                self.auto_sync_status_label.setStyleSheet("color: blue; font-style: italic;")
            else:
                status = f"Auto-Sync: Aktiv (naechster Sync heute um {time_str})"
                self.auto_sync_status_label.setStyleSheet("color: green; font-style: italic;")
        else:
            status = "Auto-Sync: Deaktiviert"
            self.auto_sync_status_label.setStyleSheet("color: gray; font-style: italic;")

        self.auto_sync_status_label.setText(status)

    def save_scheduler_settings(self):
        """
        Speichert die Scheduler-Einstellungen in eine JSON-Datei.
        """
        settings = {
            "auto_sync_enabled": self.auto_sync_enabled,
            "auto_sync_time": self.auto_sync_time.toString("HH:mm")
        }

        try:
            with open("auto_sync_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            logger.info("Scheduler-Einstellungen gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Scheduler-Einstellungen: {e}")

    def load_scheduler_settings(self):
        """
        Laedt die Scheduler-Einstellungen aus der JSON-Datei.
        """
        try:
            if os.path.exists("auto_sync_settings.json"):
                with open("auto_sync_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)

                self.auto_sync_enabled = settings.get("auto_sync_enabled", False)
                time_str = settings.get("auto_sync_time", "07:00")
                self.auto_sync_time = QTime.fromString(time_str, "HH:mm")

                # UI aktualisieren
                self.auto_sync_cb.setChecked(self.auto_sync_enabled)
                self.auto_sync_time_edit.setTime(self.auto_sync_time)

                logger.info(f"Scheduler-Einstellungen geladen: enabled={self.auto_sync_enabled}, time={time_str}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Scheduler-Einstellungen: {e}")

    def closeEvent(self, event):
        """
        Wird beim Schliessen des Fensters aufgerufen.
        Speichert Einstellungen und stoppt Timer.
        """
        # Scheduler stoppen
        self.scheduler_timer.stop()

        # Einstellungen speichern
        self.save_scheduler_settings()

        # API Server stoppen falls laufend
        if self.api_server_running:
            self.stop_api_server()

        # Sync Worker stoppen falls laufend
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()

        event.accept()


def main():
    """
    Hauptfunktion für den Start der Anwendung.
    """
    app = QApplication(sys.argv)
    ex = SyncApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
