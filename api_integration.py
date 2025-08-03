#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API-Integration für die CallDoc-SQLHK Synchronisierungs-GUI

Diese Datei enthält die Integration der API in die bestehende GUI-Anwendung.
Sie ermöglicht das Starten und Stoppen des API-Servers aus der GUI heraus.

Autor: Markus
Datum: 03.08.2025
"""

import logging
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from api_server import start_api_server

# Logger konfigurieren
logger = logging.getLogger(__name__)

class ApiServerThread(QThread):
    """Thread für den API-Server, der in der GUI verwendet werden kann."""
    
    status_changed = pyqtSignal(str)
    
    def __init__(self, host="0.0.0.0", port=8080, parent=None):
        """
        Initialisiert den API-Server-Thread.
        
        Args:
            host: Host-Adresse, standardmäßig 0.0.0.0 (alle Interfaces)
            port: Port, standardmäßig 8080
            parent: Elternobjekt für Qt
        """
        super().__init__(parent)
        self.host = host
        self.port = port
        self.running = False
        self.server_thread = None
    
    def run(self):
        """Startet den API-Server im Hintergrund."""
        try:
            self.running = True
            self.status_changed.emit(f"API-Server wird gestartet auf http://{self.host}:{self.port}...")
            
            # Server starten
            self.server_thread = start_api_server(self.host, self.port, reload=False)
            
            self.status_changed.emit(f"API-Server läuft auf http://{self.host}:{self.port}")
            self.status_changed.emit(f"API-Dokumentation verfügbar unter http://{self.host}:{self.port}/api/docs")
            
            # Thread am Leben halten, solange der Server läuft
            while self.running:
                time.sleep(1)
        
        except Exception as e:
            self.status_changed.emit(f"Fehler beim Starten des API-Servers: {str(e)}")
            logger.error(f"Fehler beim Starten des API-Servers: {str(e)}")
            self.running = False
    
    def stop(self):
        """Stoppt den API-Server."""
        self.running = False
        self.status_changed.emit("API-Server wird gestoppt...")
        # Der Thread wird automatisch beendet, wenn running=False ist
        # und die Schleife in run() verlassen wird

class ApiServerManager(QObject):
    """Manager für den API-Server, der in der GUI verwendet werden kann."""
    
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialisiert den API-Server-Manager.
        
        Args:
            parent: Elternobjekt für Qt
        """
        super().__init__(parent)
        self.server_thread = None
        self.host = "0.0.0.0"
        self.port = 8080
    
    def start_server(self, host=None, port=None):
        """
        Startet den API-Server.
        
        Args:
            host: Optional, Host-Adresse
            port: Optional, Port
        """
        if self.server_thread and self.server_thread.running:
            self.status_changed.emit("API-Server läuft bereits")
            return
        
        # Host und Port aktualisieren, falls angegeben
        if host:
            self.host = host
        if port:
            self.port = port
        
        # Server-Thread erstellen und starten
        self.server_thread = ApiServerThread(self.host, self.port)
        self.server_thread.status_changed.connect(self.status_changed)
        self.server_thread.start()
    
    def stop_server(self):
        """Stoppt den API-Server."""
        if not self.server_thread or not self.server_thread.running:
            self.status_changed.emit("API-Server läuft nicht")
            return
        
        # Server stoppen
        self.server_thread.stop()
        self.server_thread.wait(5000)  # Maximal 5 Sekunden warten
        
        if self.server_thread.isRunning():
            self.status_changed.emit("API-Server konnte nicht sauber beendet werden")
        else:
            self.status_changed.emit("API-Server wurde gestoppt")
            self.server_thread = None
    
    def is_running(self):
        """Gibt zurück, ob der API-Server läuft."""
        return self.server_thread is not None and self.server_thread.running
    
    def get_url(self):
        """Gibt die URL des API-Servers zurück."""
        if self.is_running():
            return f"http://{self.host}:{self.port}"
        return None
    
    def get_docs_url(self):
        """Gibt die URL der API-Dokumentation zurück."""
        if self.is_running():
            return f"http://{self.host}:{self.port}/api/docs"
        return None
