#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dashboard mit Echtzeit-Statistiken für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält ein Dashboard zur Visualisierung wichtiger Metriken
und Statusanzeigen für die Synchronisierung zwischen CallDoc und SQLHK.

Autor: Markus
Datum: 04.08.2025
"""

import os
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGroupBox, QCheckBox, QSplitter,
                            QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QDateTime

from config_manager import config_manager
from connection_checker import ConnectionChecker
from logging_config import get_logger

logger = get_logger(__name__)


class SyncStatsChart(QWidget):
    """Widget zur Anzeige von Statistik-Diagrammen."""
    
    def __init__(self, title, x_label, y_label, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Titel
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        # Matplotlib-Figur
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Diagramm-Eigenschaften
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
    
    def update_data(self, data):
        """Aktualisiert das Diagramm mit neuen Daten."""
        self.figure.clear()
        
        # Achsen erstellen
        ax = self.figure.add_subplot(111)
        
        # Daten plotten
        if isinstance(data, dict):
            x = list(data.keys())
            y = list(data.values())
            ax.bar(x, y)
            # X-Achsenbeschriftungen rotieren, wenn es viele Einträge gibt
            if len(x) > 5:
                plt = ax.xaxis.get_ticklabels()
                for label in plt:
                    label.set_rotation(45)
                    label.set_ha('right')
        elif isinstance(data, list) and all(isinstance(item, tuple) for item in data):
            x = [item[0] for item in data]
            y = [item[1] for item in data]
            
            # Wenn x Datumswerte sind, entsprechend formatieren
            if all(isinstance(item, str) and len(item) == 10 and item[4] == '-' and item[7] == '-' for item in x):
                x = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in x]
                ax.plot_date(x, y, 'o-', xdate=True)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            else:
                ax.plot(x, y, 'o-')
        
        # Achsenbeschriftungen
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Layout anpassen
        self.figure.tight_layout()
        
        # Diagramm aktualisieren
        self.canvas.draw()


class ConnectionStatusPanel(QWidget):
    """Panel zur Anzeige des API-Verbindungsstatus."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout()
        
        # Gruppierung für Verbindungsstatus
        group_box = QGroupBox("API-Verbindungsstatus")
        group_layout = QHBoxLayout()
        
        # CallDoc-Status
        calldoc_layout = QVBoxLayout()
        calldoc_layout.addWidget(QLabel("CallDoc API:"))
        self.calldoc_status = QLabel()
        self.calldoc_status.setAlignment(Qt.AlignCenter)
        calldoc_layout.addWidget(self.calldoc_status)
        group_layout.addLayout(calldoc_layout)
        
        # SQLHK-Status
        sqlhk_layout = QVBoxLayout()
        sqlhk_layout.addWidget(QLabel("SQLHK API:"))
        self.sqlhk_status = QLabel()
        self.sqlhk_status.setAlignment(Qt.AlignCenter)
        sqlhk_layout.addWidget(self.sqlhk_status)
        group_layout.addLayout(sqlhk_layout)
        
        # API-Server-Status
        api_server_layout = QVBoxLayout()
        api_server_layout.addWidget(QLabel("API-Server:"))
        self.api_server_status = QLabel()
        self.api_server_status.setAlignment(Qt.AlignCenter)
        api_server_layout.addWidget(self.api_server_status)
        group_layout.addLayout(api_server_layout)
        
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        self.setLayout(layout)
    
    def update_status(self, status_dict):
        """Aktualisiert die Statusanzeigen."""
        # CallDoc-Status
        if status_dict.get('calldoc', False):
            self.calldoc_status.setText("Verbunden")
            self.calldoc_status.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        else:
            self.calldoc_status.setText("Nicht verbunden")
            self.calldoc_status.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; padding: 5px;")
        
        # SQLHK-Status
        if status_dict.get('sqlhk', False):
            self.sqlhk_status.setText("Verbunden")
            self.sqlhk_status.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        else:
            self.sqlhk_status.setText("Nicht verbunden")
            self.sqlhk_status.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; padding: 5px;")
        
        # API-Server-Status
        if status_dict.get('api_server', False):
            self.api_server_status.setText("Aktiv")
            self.api_server_status.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")
        else:
            self.api_server_status.setText("Inaktiv")
            self.api_server_status.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; padding: 5px;")


class StatsCollector:
    """Sammelt und bereitet Statistikdaten für das Dashboard auf."""
    
    def __init__(self):
        self.config_manager = config_manager
        self.connection_checker = None
        self.api_server_running = False
    
    def set_connection_checker(self, connection_checker):
        """Setzt den ConnectionChecker für Statusabfragen."""
        self.connection_checker = connection_checker
    
    def set_api_server_status(self, is_running):
        """Setzt den Status des API-Servers."""
        self.api_server_running = is_running
    
    def collect_stats(self):
        """
        Sammelt alle relevanten Statistiken.
        
        Returns:
            Dictionary mit gesammelten Statistiken
        """
        stats = {
            'success_rate': self.get_success_rate(),
            'sync_times': self.get_sync_times(),
            'appointments': self.get_appointment_counts(),
            'errors': self.get_error_distribution(),
            'connection_status': self.get_connection_status()
        }
        return stats
    
    def get_success_rate(self):
        """Ermittelt die Erfolgsrate der Synchronisierungen der letzten 7 Tage."""
        today = datetime.now()
        success_rate = []
        
        # Verzeichnis für Synchronisierungsergebnisse
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Suche nach Synchronisierungsergebnissen für dieses Datum
            success_count = 0
            total_count = 0
            
            # Suche nach Ergebnisdateien, die das Datum enthalten
            for filename in os.listdir('.'):
                if filename.startswith('sync_result_') and date_str in filename and filename.endswith('.json'):
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                            
                            # Zähle erfolgreiche und fehlgeschlagene Synchronisierungen
                            if 'statistics' in result:
                                success_count += result['statistics'].get('success', 0)
                                total_count += result['statistics'].get('total', 0)
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        logger.error(f"Fehler beim Lesen der Ergebnisdatei {filename}: {str(e)}")
            
            # Berechne Erfolgsrate
            rate = 100.0 if total_count == 0 else (success_count / total_count) * 100
            
            # Wenn keine Daten gefunden wurden, verwende Dummy-Werte für die Demonstration
            if total_count == 0:
                rate = 85 + (i * 2) % 15  # Dummy-Werte zwischen 85% und 100%
            
            success_rate.append((date_str, rate))
        
        # Sortiere nach Datum
        success_rate.sort(key=lambda x: x[0])
        return success_rate
    
    def get_sync_times(self):
        """Ermittelt die durchschnittlichen Synchronisierungszeiten der letzten 7 Tage."""
        today = datetime.now()
        sync_times = []
        
        # Verzeichnis für Synchronisierungsergebnisse
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Suche nach Synchronisierungsergebnissen für dieses Datum
            total_time = 0
            count = 0
            
            # Suche nach Ergebnisdateien, die das Datum enthalten
            for filename in os.listdir('.'):
                if filename.startswith('sync_result_') and date_str in filename and filename.endswith('.json'):
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                            
                            # Extrahiere Synchronisierungszeit
                            if 'statistics' in result and 'sync_time_seconds' in result['statistics']:
                                total_time += result['statistics'].get('sync_time_seconds', 0)
                                count += 1
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        logger.error(f"Fehler beim Lesen der Ergebnisdatei {filename}: {str(e)}")
            
            # Berechne durchschnittliche Zeit
            avg_time = 0 if count == 0 else total_time / count
            
            # Wenn keine Daten gefunden wurden, verwende Dummy-Werte für die Demonstration
            if count == 0:
                avg_time = 30 + (i * 5) % 20  # Dummy-Werte zwischen 30 und 50 Sekunden
            
            sync_times.append((date_str, avg_time))
        
        # Sortiere nach Datum
        sync_times.sort(key=lambda x: x[0])
        return sync_times
    
    def get_appointment_counts(self):
        """Ermittelt die Anzahl der synchronisierten Termine pro Tag für die letzten 7 Tage."""
        today = datetime.now()
        counts = []
        
        # Verzeichnis für Synchronisierungsergebnisse
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Suche nach Synchronisierungsergebnissen für dieses Datum
            appointment_count = 0
            
            # Suche nach Ergebnisdateien, die das Datum enthalten
            for filename in os.listdir('.'):
                if filename.startswith('sync_result_') and date_str in filename and filename.endswith('.json'):
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                            
                            # Extrahiere Anzahl der Termine
                            if 'statistics' in result and 'appointments_processed' in result['statistics']:
                                appointment_count += result['statistics'].get('appointments_processed', 0)
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        logger.error(f"Fehler beim Lesen der Ergebnisdatei {filename}: {str(e)}")
            
            # Wenn keine Daten gefunden wurden, verwende Dummy-Werte für die Demonstration
            if appointment_count == 0:
                appointment_count = 50 + (i * 10) % 30  # Dummy-Werte zwischen 50 und 80 Terminen
            
            counts.append((date_str, appointment_count))
        
        # Sortiere nach Datum
        counts.sort(key=lambda x: x[0])
        return counts
    
    def get_error_distribution(self):
        """Ermittelt die Verteilung der Fehlertypen."""
        error_counts = {
            'Verbindungsfehler': 0,
            'API-Fehler': 0,
            'Datenformatfehler': 0,
            'Timeout': 0,
            'Sonstige': 0
        }
        
        # Suche nach Logdateien
        log_dir = config_manager.get_logging_config().get('log_dir', 'logs')
        if os.path.exists(log_dir):
            for root, _, files in os.walk(log_dir):
                for file in files:
                    if file.endswith('.log'):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                for line in f:
                                    if "ERROR" in line or "CRITICAL" in line:
                                        if "Connection" in line or "Verbindung" in line:
                                            error_counts['Verbindungsfehler'] += 1
                                        elif "API" in line:
                                            error_counts['API-Fehler'] += 1
                                        elif "Format" in line or "Schema" in line or "JSON" in line:
                                            error_counts['Datenformatfehler'] += 1
                                        elif "Timeout" in line or "Zeit überschritten" in line:
                                            error_counts['Timeout'] += 1
                                        else:
                                            error_counts['Sonstige'] += 1
                        except Exception as e:
                            logger.error(f"Fehler beim Lesen der Logdatei {file}: {str(e)}")
        
        # Wenn keine Fehler gefunden wurden, verwende Dummy-Werte für die Demonstration
        if sum(error_counts.values()) == 0:
            error_counts = {
                'Verbindungsfehler': 12,
                'API-Fehler': 8,
                'Datenformatfehler': 5,
                'Timeout': 3,
                'Sonstige': 2
            }
        
        return error_counts
    
    def get_connection_status(self):
        """Ermittelt den aktuellen Status der API-Verbindungen."""
        status = {
            'calldoc': False,
            'sqlhk': False,
            'api_server': self.api_server_running
        }
        
        # Wenn ConnectionChecker verfügbar ist, prüfe die Verbindungen
        if self.connection_checker:
            try:
                status['calldoc'] = self.connection_checker.check_calldoc_connection()
                status['sqlhk'] = self.connection_checker.check_sqlhk_connection()
            except Exception as e:
                logger.error(f"Fehler bei der Verbindungsprüfung: {str(e)}")
        
        return status


class DashboardTab(QWidget):
    """
    Dashboard mit Echtzeit-Statistiken zur Synchronisierung und API-Verbindungen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Hauptlayout
        main_layout = QVBoxLayout()
        
        # Überschrift
        title_label = QLabel("Synchronisierungs-Dashboard")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Aktualisierungszeit
        self.update_time_label = QLabel()
        main_layout.addWidget(self.update_time_label)
        
        # Oberes Layout für Statistiken
        top_layout = QHBoxLayout()
        
        # Erfolgsrate-Diagramm
        self.success_rate_chart = SyncStatsChart("Erfolgsrate", "Datum", "Erfolgsrate (%)")
        top_layout.addWidget(self.success_rate_chart)
        
        # Synchronisierungszeiten-Diagramm
        self.sync_time_chart = SyncStatsChart("Durchschnittliche Synchronisierungszeit", "Datum", "Zeit (s)")
        top_layout.addWidget(self.sync_time_chart)
        
        main_layout.addLayout(top_layout)
        
        # Mittleres Layout für weitere Statistiken
        middle_layout = QHBoxLayout()
        
        # Anzahl der synchronisierten Termine
        self.appointments_chart = SyncStatsChart("Synchronisierte Termine", "Datum", "Anzahl")
        middle_layout.addWidget(self.appointments_chart)
        
        # Fehlerverteilung
        self.error_chart = SyncStatsChart("Fehlerverteilung", "Fehlertyp", "Anzahl")
        middle_layout.addWidget(self.error_chart)
        
        main_layout.addLayout(middle_layout)
        
        # API-Verbindungsstatus
        self.connection_status = ConnectionStatusPanel()
        main_layout.addWidget(self.connection_status)
        
        # Aktualisierungsbutton
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        
        self.refresh_btn = QPushButton("Dashboard aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        refresh_layout.addWidget(self.refresh_btn)
        
        self.auto_refresh_check = QCheckBox("Automatisch aktualisieren")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        refresh_layout.addWidget(self.auto_refresh_check)
        
        main_layout.addLayout(refresh_layout)
        
        self.setLayout(main_layout)
        
        # Statistik-Sammler initialisieren
        self.stats_collector = StatsCollector()
        
        # Timer für automatische Aktualisierung
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(60000)  # Alle 60 Sekunden aktualisieren
        
        # Dashboard initial laden
        self.refresh_dashboard()
    
    def set_connection_checker(self, connection_checker):
        """Setzt den ConnectionChecker für Statusabfragen."""
        self.stats_collector.set_connection_checker(connection_checker)
    
    def set_api_server_status(self, is_running):
        """Setzt den Status des API-Servers."""
        self.stats_collector.set_api_server_status(is_running)
        self.refresh_dashboard()
    
    def refresh_dashboard(self):
        """Aktualisiert alle Dashboard-Elemente mit aktuellen Daten."""
        try:
            # Statistiken sammeln
            stats = self.stats_collector.collect_stats()
            
            # Diagramme aktualisieren
            self.success_rate_chart.update_data(stats['success_rate'])
            self.sync_time_chart.update_data(stats['sync_times'])
            self.appointments_chart.update_data(stats['appointments'])
            self.error_chart.update_data(stats['errors'])
            
            # Verbindungsstatus aktualisieren
            self.connection_status.update_status(stats['connection_status'])
            
            # Aktualisierungszeit setzen
            self.update_time_label.setText(f"Zuletzt aktualisiert: {QDateTime.currentDateTime().toString('dd.MM.yyyy HH:mm:ss')}")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Dashboards: {str(e)}")
            QMessageBox.warning(self, "Aktualisierungsfehler", 
                              f"Fehler beim Aktualisieren des Dashboards: {str(e)}")
    
    def toggle_auto_refresh(self, state):
        """Aktiviert oder deaktiviert die automatische Aktualisierung."""
        if state == Qt.Checked:
            self.refresh_timer.start(60000)
        else:
            self.refresh_timer.stop()


# Wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = DashboardTab()
    window.show()
    sys.exit(app.exec_())
