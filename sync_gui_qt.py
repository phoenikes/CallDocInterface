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
                            QSplitter, QFrame, QDateEdit, QStatusBar)
from PyQt5.QtCore import QDate, pyqtSlot, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import der Synchronisierungskomponenten
from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from patient_synchronizer import PatientSynchronizer
from untersuchung_synchronizer import UntersuchungSynchronizer
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
    Hauptfenster der Synchronisierungs-GUI.
    """
    def __init__(self):
        super().__init__()
        self.title = 'CallDoc-SQLHK Synchronisierung'
        self.sync_worker = None
        self.sync_results = {}
        self.initUI()
        
    def initUI(self):
        """
        Initialisiert die Benutzeroberfläche.
        """
        self.setWindowTitle(self.title)
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


def main():
    """
    Hauptfunktion für den Start der Anwendung.
    """
    app = QApplication(sys.argv)
    ex = SyncApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
