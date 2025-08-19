#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Erweiterter Log-Viewer für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält einen erweiterten Log-Viewer mit Filterfunktionen,
farblicher Hervorhebung und Suchfunktionen für die Logs der Anwendung.

Autor: Markus
Datum: 04.08.2025
"""

import os
import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QPushButton, QTextEdit, QLineEdit,
                            QDateEdit, QFileDialog, QMessageBox, QSplitter,
                            QTreeWidget, QTreeWidgetItem, QCheckBox)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from config_manager import config_manager
from logging_config import get_logger

logger = get_logger(__name__)


class LogFilterPanel(QWidget):
    """Panel mit Filtermöglichkeiten für Logs."""
    
    filterChanged = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Komponenten-Filter
        self.component_combo = QComboBox()
        self.component_combo.addItem("Alle Komponenten")
        layout.addWidget(QLabel("Komponente:"))
        layout.addWidget(self.component_combo)
        
        # Log-Level-Filter
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALLE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addWidget(QLabel("Log-Level:"))
        layout.addWidget(self.level_combo)
        
        # Zeitraum-Filter
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(QLabel("Von:"))
        layout.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Bis:"))
        layout.addWidget(self.end_date)
        
        # Filter anwenden
        self.apply_btn = QPushButton("Filter anwenden")
        self.apply_btn.clicked.connect(self.emit_filter_changed)
        layout.addWidget(self.apply_btn)
        
        self.setLayout(layout)
    
    def update_components(self, components):
        """Aktualisiert die Liste der verfügbaren Komponenten."""
        self.component_combo.clear()
        self.component_combo.addItem("Alle Komponenten")
        self.component_combo.addItems(components)
    
    def emit_filter_changed(self):
        """Sendet Signal mit aktuellen Filtereinstellungen."""
        filters = {
            'component': self.component_combo.currentText() if self.component_combo.currentIndex() > 0 else None,
            'level': self.level_combo.currentText() if self.level_combo.currentText() != "ALLE" else None,
            'start_date': self.start_date.date().toPyDate(),
            'end_date': self.end_date.date().toPyDate()
        }
        self.filterChanged.emit(filters)


class LogViewerTab(QWidget):
    """
    Erweiterter Log-Viewer mit Filterfunktionen, Suche und farblicher Hervorhebung.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Hauptlayout
        main_layout = QVBoxLayout()
        
        # Filter-Panel
        self.filter_panel = LogFilterPanel()
        self.filter_panel.filterChanged.connect(self.apply_filters)
        main_layout.addWidget(self.filter_panel)
        
        # Suchleiste
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Suche in Logs...")
        self.search_bar.textChanged.connect(self.highlight_search_results)
        search_layout.addWidget(self.search_bar)
        
        self.search_next_btn = QPushButton("Nächster")
        self.search_next_btn.clicked.connect(self.find_next)
        search_layout.addWidget(self.search_next_btn)
        
        self.search_prev_btn = QPushButton("Vorheriger")
        self.search_prev_btn.clicked.connect(self.find_previous)
        search_layout.addWidget(self.search_prev_btn)
        
        main_layout.addLayout(search_layout)
        
        # Splitter für Dateiliste und Log-Anzeige
        splitter = QSplitter(Qt.Horizontal)
        
        # Log-Dateien-Baum
        self.log_files_tree = QTreeWidget()
        self.log_files_tree.setHeaderLabels(["Log-Dateien"])
        self.log_files_tree.setMinimumWidth(200)
        self.log_files_tree.itemClicked.connect(self.on_log_file_selected)
        splitter.addWidget(self.log_files_tree)
        
        # Log-Anzeige mit Syntax-Highlighting
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        self.log_display.setFont(QFont("Courier New", 10))
        splitter.addWidget(self.log_display)
        
        # Splitter-Größen setzen
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)
        
        # Aktionsleiste
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        action_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Exportieren...")
        self.export_btn.clicked.connect(self.export_logs)
        action_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("Leeren")
        self.clear_btn.clicked.connect(self.clear_logs)
        action_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(action_layout)
        
        self.setLayout(main_layout)
        
        # Initialisierung
        self.log_files = {}
        self.current_log_file = None
        self.search_results = []
        self.current_search_index = -1
        
        # Log-Dateien laden
        self.load_log_files()
    
    def load_log_files(self):
        """Lädt verfügbare Log-Dateien aus dem Log-Verzeichnis."""
        log_dir = config_manager.get_logging_config().get('log_dir', 'logs')
        self.log_files = {}
        self.log_files_tree.clear()
        
        if os.path.exists(log_dir):
            # Root-Item für das Log-Verzeichnis
            root_item = QTreeWidgetItem(self.log_files_tree, [log_dir])
            
            # Komponenten-Verzeichnisse durchsuchen
            components = []
            for item in os.listdir(log_dir):
                item_path = os.path.join(log_dir, item)
                if os.path.isdir(item_path):
                    # Komponenten-Verzeichnis gefunden
                    component_item = QTreeWidgetItem(root_item, [item])
                    components.append(item)
                    
                    # Log-Dateien in diesem Verzeichnis suchen
                    for file in os.listdir(item_path):
                        if file.endswith('.log'):
                            file_path = os.path.join(item_path, file)
                            file_item = QTreeWidgetItem(component_item, [file])
                            file_item.setData(0, Qt.UserRole, file_path)
                else:
                    # Log-Datei direkt im Log-Verzeichnis
                    if item.endswith('.log'):
                        file_path = os.path.join(log_dir, item)
                        file_item = QTreeWidgetItem(root_item, [item])
                        file_item.setData(0, Qt.UserRole, file_path)
            
            # Komponenten-Liste für Filter aktualisieren
            self.filter_panel.update_components(components)
            
            # Baum expandieren
            self.log_files_tree.expandAll()
    
    def on_log_file_selected(self, item, column):
        """Wird aufgerufen, wenn eine Log-Datei im Baum ausgewählt wird."""
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.current_log_file = file_path
            self.load_log_content(file_path)
    
    def load_log_content(self, file_path):
        """Lädt den Inhalt einer Log-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Anzeige mit farblicher Hervorhebung
            self.display_logs(content)
            
            # Suchbegriff erneut anwenden, falls vorhanden
            if self.search_bar.text():
                self.highlight_search_results(self.search_bar.text())
        except Exception as e:
            logger.error(f"Fehler beim Laden der Log-Datei {file_path}: {str(e)}")
            self.log_display.setPlainText(f"Fehler beim Laden der Log-Datei: {str(e)}")
    
    def apply_filters(self, filters):
        """Wendet Filter auf die Log-Anzeige an."""
        if not self.current_log_file:
            return
            
        try:
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            filtered_content = []
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            
            for line in content:
                # Nach Log-Level filtern
                if filters['level']:
                    if filters['level'] not in line:
                        continue
                
                # Nach Zeitraum filtern
                if filters['start_date'] or filters['end_date']:
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        line_date_str = date_match.group(0)
                        try:
                            line_date = datetime.strptime(line_date_str, '%Y-%m-%d').date()
                            if filters['start_date'] and line_date < filters['start_date']:
                                continue
                            if filters['end_date'] and line_date > filters['end_date']:
                                continue
                        except ValueError:
                            pass
                
                # Nach Komponente filtern
                if filters['component'] and filters['component'] != "Alle Komponenten":
                    if filters['component'] not in line:
                        continue
                
                filtered_content.append(line)
            
            self.display_logs(''.join(filtered_content))
        except Exception as e:
            logger.error(f"Fehler beim Anwenden der Filter: {str(e)}")
            self.log_display.setPlainText(f"Fehler beim Anwenden der Filter: {str(e)}")
    
    def display_logs(self, log_content):
        """Zeigt Logs mit farblicher Hervorhebung an."""
        self.log_display.clear()
        
        # HTML für farbliche Hervorhebung
        html_content = log_content
        
        # Farbliche Hervorhebung nach Log-Level
        html_content = re.sub(r'(ERROR|CRITICAL).*?(?=\n|$)', 
                             r'<span style="color:red">\g<0></span>', 
                             html_content)
        html_content = re.sub(r'WARNING.*?(?=\n|$)', 
                             r'<span style="color:orange">\g<0></span>', 
                             html_content)
        html_content = re.sub(r'INFO.*?(?=\n|$)', 
                             r'<span style="color:green">\g<0></span>', 
                             html_content)
        html_content = re.sub(r'DEBUG.*?(?=\n|$)', 
                             r'<span style="color:blue">\g<0></span>', 
                             html_content)
        
        # HTML-Inhalt setzen
        self.log_display.setHtml(f"<pre>{html_content}</pre>")
    
    def highlight_search_results(self, search_text):
        """Hebt Suchergebnisse hervor und navigiert zum ersten Treffer."""
        if not search_text:
            return
        
        # Suche im aktuellen Text
        cursor = self.log_display.textCursor()
        cursor.setPosition(0)
        self.log_display.setTextCursor(cursor)
        
        # Suchoptionen
        options = QTextDocument.FindFlags()
        
        # Alle Treffer finden und hervorheben
        self.search_results = []
        self.current_search_index = -1
        
        cursor = self.log_display.document().find(search_text, 0, options)
        while not cursor.isNull():
            self.search_results.append(cursor)
            cursor = self.log_display.document().find(search_text, cursor, options)
        
        # Zum ersten Treffer navigieren, wenn vorhanden
        if self.search_results:
            self.current_search_index = 0
            self.log_display.setTextCursor(self.search_results[0])
            self.log_display.ensureCursorVisible()
    
    def find_next(self):
        """Navigiert zum nächsten Suchergebnis."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.log_display.setTextCursor(self.search_results[self.current_search_index])
        self.log_display.ensureCursorVisible()
    
    def find_previous(self):
        """Navigiert zum vorherigen Suchergebnis."""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.log_display.setTextCursor(self.search_results[self.current_search_index])
        self.log_display.ensureCursorVisible()
    
    def refresh_logs(self):
        """Aktualisiert die Log-Anzeige."""
        self.load_log_files()
        if self.current_log_file:
            self.load_log_content(self.current_log_file)
    
    def export_logs(self):
        """Öffnet Dialog zum Exportieren der aktuellen Log-Ansicht."""
        if not self.current_log_file:
            QMessageBox.warning(self, "Export nicht möglich", 
                              "Bitte wählen Sie zuerst eine Log-Datei aus.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Log exportieren", "", "Log-Dateien (*.log);;Text-Dateien (*.txt);;Alle Dateien (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                
                QMessageBox.information(self, "Export erfolgreich", 
                                      f"Die Logs wurden erfolgreich nach {file_path} exportiert.")
            except Exception as e:
                logger.error(f"Fehler beim Exportieren der Logs: {str(e)}")
                QMessageBox.critical(self, "Exportfehler", 
                                   f"Fehler beim Exportieren der Logs: {str(e)}")
    
    def clear_logs(self):
        """Leert die Log-Anzeige."""
        self.log_display.clear()


# Wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = LogViewerTab()
    window.show()
    sys.exit(app.exec_())
