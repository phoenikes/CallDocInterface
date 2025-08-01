"""
Synchronisierungs-GUI für CallDoc-Untersuchungen

Diese Datei enthält eine einfache GUI für die Synchronisierung von Untersuchungsdaten
zwischen dem CallDoc-System und der SQLHK-Datenbank.

Autor: Markus
Datum: 31.07.2025
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import json
import logging
from typing import Dict, Any

from calldoc_interface import CallDocInterface
from mssql_api_client import MsSqlApiClient
from untersuchung_synchronizer import UntersuchungSynchronizer

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

class SynchronizationApp:
    """
    GUI-Anwendung für die Synchronisierung von CallDoc-Untersuchungen mit der SQLHK-Datenbank.
    """
    
    def __init__(self, root):
        """
        Initialisiert die GUI-Anwendung.
        
        Args:
            root: Tkinter-Root-Fenster
        """
        self.root = root
        self.root.title("CallDoc-SQLHK Synchronisierung")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variablen
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.status_var = tk.StringVar(value="Bereit")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.log_text = None
        
        # GUI erstellen
        self._create_widgets()
        
        # Synchronizer initialisieren
        self.mssql_client = MsSqlApiClient()
        self.synchronizer = None
        
        # Thread für die Synchronisierung
        self.sync_thread = None
    
    def _create_widgets(self):
        """
        Erstellt die GUI-Elemente.
        """
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Oberer Bereich: Datumswahl und Buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # Datum-Label und -Eingabe
        date_label = ttk.Label(top_frame, text="Datum (YYYY-MM-DD):")
        date_label.pack(side=tk.LEFT, padx=5)
        
        date_entry = ttk.Entry(top_frame, textvariable=self.date_var, width=15)
        date_entry.pack(side=tk.LEFT, padx=5)
        
        # Datum-Buttons
        yesterday_btn = ttk.Button(top_frame, text="Gestern", command=self._set_yesterday)
        yesterday_btn.pack(side=tk.LEFT, padx=5)
        
        today_btn = ttk.Button(top_frame, text="Heute", command=self._set_today)
        today_btn.pack(side=tk.LEFT, padx=5)
        
        tomorrow_btn = ttk.Button(top_frame, text="Morgen", command=self._set_tomorrow)
        tomorrow_btn.pack(side=tk.LEFT, padx=5)
        
        # Synchronisierungs-Button
        sync_btn = ttk.Button(top_frame, text="Synchronisieren", command=self._start_sync)
        sync_btn.pack(side=tk.RIGHT, padx=5)
        
        # Mittlerer Bereich: Status und Fortschritt
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.X, pady=10)
        
        # Status-Label
        status_label = ttk.Label(middle_frame, text="Status:")
        status_label.pack(side=tk.LEFT, padx=5)
        
        status_value = ttk.Label(middle_frame, textvariable=self.status_var)
        status_value.pack(side=tk.LEFT, padx=5)
        
        # Fortschrittsbalken
        progress_bar = ttk.Progressbar(middle_frame, variable=self.progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=5, pady=5, expand=True)
        
        # Unterer Bereich: Log-Ausgabe
        log_frame = ttk.LabelFrame(main_frame, text="Log-Ausgabe")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Log-Text
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar für Log-Text
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Log-Handler konfigurieren
        self._setup_log_handler()
    
    def _setup_log_handler(self):
        """
        Richtet einen Handler für das Logging ein, der die Ausgabe in das Log-Textfeld schreibt.
        """
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                
                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.configure(state='disabled')
                    self.text_widget.see(tk.END)
                
                self.text_widget.after(0, append)
        
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logger = logging.getLogger()
        logger.addHandler(text_handler)
    
    def _set_yesterday(self):
        """
        Setzt das Datum auf gestern.
        """
        yesterday = datetime.now() - timedelta(days=1)
        self.date_var.set(yesterday.strftime("%Y-%m-%d"))
    
    def _set_today(self):
        """
        Setzt das Datum auf heute.
        """
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
    
    def _set_tomorrow(self):
        """
        Setzt das Datum auf morgen.
        """
        tomorrow = datetime.now() + timedelta(days=1)
        self.date_var.set(tomorrow.strftime("%Y-%m-%d"))
    
    def _start_sync(self):
        """
        Startet die Synchronisierung in einem separaten Thread.
        """
        if self.sync_thread and self.sync_thread.is_alive():
            messagebox.showwarning("Warnung", "Eine Synchronisierung läuft bereits.")
            return
        
        date_str = self.date_var.get()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiges Datumsformat. Bitte verwenden Sie YYYY-MM-DD.")
            return
        
        self.status_var.set("Synchronisierung läuft...")
        self.progress_var.set(0)
        
        # Log-Text leeren
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        # Thread starten
        self.sync_thread = threading.Thread(target=self._run_sync, args=(date_str,))
        self.sync_thread.daemon = True
        self.sync_thread.start()
    
    def _run_sync(self, date_str):
        """
        Führt die Synchronisierung durch.
        
        Args:
            date_str: Datum im Format YYYY-MM-DD
        """
        try:
            logger.info(f"Starte Synchronisierung für {date_str}")
            
            # Fortschritt aktualisieren
            self.progress_var.set(10)
            
            # CallDoc-Interface initialisieren
            calldoc_interface = CallDocInterface(from_date=date_str, to_date=date_str)
            
            # Fortschritt aktualisieren
            self.progress_var.set(20)
            
            # Synchronizer initialisieren
            self.synchronizer = UntersuchungSynchronizer(calldoc_interface, self.mssql_client)
            
            # Fortschritt aktualisieren
            self.progress_var.set(30)
            
            # Synchronisierung durchführen
            stats = self.synchronizer.compare_and_sync(date_str)
            
            # Fortschritt aktualisieren
            self.progress_var.set(100)
            
            # Status aktualisieren
            self.root.after(0, lambda: self._update_status("Synchronisierung abgeschlossen", stats))
            
        except Exception as e:
            logger.error(f"Fehler bei der Synchronisierung: {str(e)}")
            self.root.after(0, lambda: self._update_status(f"Fehler: {str(e)}", {}))
    
    def _update_status(self, status, stats):
        """
        Aktualisiert den Status und zeigt die Statistik an.
        
        Args:
            status: Statustext
            stats: Statistik der Synchronisierung
        """
        self.status_var.set(status)
        
        if stats:
            logger.info("\nSynchronisierung abgeschlossen:")
            logger.info(f"CallDoc-Termine: {stats.get('total_calldoc', 0)}")
            logger.info(f"SQLHK-Untersuchungen: {stats.get('total_sqlhk', 0)}")
            logger.info(f"Neue Untersuchungen: {stats.get('inserted', 0)}/{stats.get('to_insert', 0)}")
            logger.info(f"Aktualisierte Untersuchungen: {stats.get('updated', 0)}/{stats.get('to_update', 0)}")
            logger.info(f"Gelöschte Untersuchungen: {stats.get('deleted', 0)}/{stats.get('to_delete', 0)}")
            logger.info(f"Fehler: {stats.get('errors', 0)}")
            
            # Zusammenfassung anzeigen
            message = (
                f"Synchronisierung abgeschlossen:\n\n"
                f"CallDoc-Termine: {stats.get('total_calldoc', 0)}\n"
                f"SQLHK-Untersuchungen: {stats.get('total_sqlhk', 0)}\n\n"
                f"Neue Untersuchungen: {stats.get('inserted', 0)}/{stats.get('to_insert', 0)}\n"
                f"Aktualisierte Untersuchungen: {stats.get('updated', 0)}/{stats.get('to_update', 0)}\n"
                f"Gelöschte Untersuchungen: {stats.get('deleted', 0)}/{stats.get('to_delete', 0)}\n\n"
                f"Fehler: {stats.get('errors', 0)}"
            )
            messagebox.showinfo("Synchronisierung abgeschlossen", message)


def main():
    """
    Hauptfunktion für den Start der Anwendung.
    """
    root = tk.Tk()
    app = SynchronizationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
