#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Automatische Synchronisierung für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die Klasse AutoSyncScheduler, die für die automatische
Synchronisierung in regelmäßigen Intervallen verantwortlich ist.

Autor: Markus
Datum: 03.08.2025
"""

import threading
import time
import logging
import datetime
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AutoSyncScheduler:
    """
    Plant und führt automatische Synchronisierungen durch.
    """
    
    def __init__(self, sync_function: Callable, settings: Dict[str, Any]):
        """
        Initialisiert den AutoSyncScheduler.
        
        Args:
            sync_function: Funktion, die für die Synchronisierung aufgerufen wird
            settings: Einstellungen für die automatische Synchronisierung
        """
        self.sync_function = sync_function
        self.settings = settings
        self.running = False
        self.thread = None
        self.next_sync_time = None
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Aktualisiert die Einstellungen für die automatische Synchronisierung.
        
        Args:
            settings: Neue Einstellungen
        """
        self.settings = settings
        logger.info("Einstellungen für automatische Synchronisierung aktualisiert")
        
        # Wenn der Scheduler läuft, neu starten, um die neuen Einstellungen zu übernehmen
        if self.running:
            self.stop()
            self.start()
    
    def start(self) -> None:
        """Startet die automatische Synchronisierung."""
        if self.thread and self.thread.is_alive():
            logger.warning("Automatische Synchronisierung läuft bereits")
            return
        
        if not self.settings.get("ENABLED", False):
            logger.info("Automatische Synchronisierung ist deaktiviert")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        logger.info("Automatische Synchronisierung gestartet")
    
    def stop(self) -> None:
        """Stoppt die automatische Synchronisierung."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            logger.info("Automatische Synchronisierung gestoppt")
    
    def _scheduler_loop(self) -> None:
        """Hauptschleife des Schedulers."""
        while self.running:
            try:
                if self._should_sync_now():
                    logger.info("Automatische Synchronisierung wird ausgeführt")
                    self.sync_function()
                    
                    # Nächste Synchronisierung planen
                    interval_minutes = self.settings.get("INTERVAL_MINUTES", 60)
                    self.next_sync_time = datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)
                    logger.info(f"Nächste automatische Synchronisierung um {self.next_sync_time.strftime('%H:%M:%S')}")
                
                # Alle 10 Sekunden prüfen
                time.sleep(10)
            except Exception as e:
                logger.error(f"Fehler in der Scheduler-Schleife: {str(e)}")
                time.sleep(60)  # Bei Fehlern länger warten
    
    def _should_sync_now(self) -> bool:
        """
        Prüft, ob jetzt eine Synchronisierung durchgeführt werden soll.
        
        Returns:
            True, wenn jetzt synchronisiert werden soll, sonst False
        """
        now = datetime.datetime.now()
        
        # Wenn noch keine nächste Synchronisierungszeit festgelegt wurde
        if self.next_sync_time is None:
            self.next_sync_time = now
            return True
        
        # Wenn die nächste Synchronisierungszeit erreicht ist
        if now >= self.next_sync_time:
            # Prüfen, ob der aktuelle Wochentag in den erlaubten Tagen liegt (1-7, wobei 1=Montag, 7=Sonntag)
            allowed_days = self.settings.get("DAYS", [1, 2, 3, 4, 5])
            current_day = now.isoweekday()
            
            if current_day not in allowed_days:
                logger.info(f"Heute (Tag {current_day}) ist keine automatische Synchronisierung geplant")
                # Nächste Synchronisierung auf morgen verschieben
                tomorrow = now + datetime.timedelta(days=1)
                tomorrow = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
                self.next_sync_time = tomorrow
                return False
            
            # Prüfen, ob die aktuelle Uhrzeit im erlaubten Zeitfenster liegt
            start_time_str = self.settings.get("START_TIME", "08:00")
            end_time_str = self.settings.get("END_TIME", "18:00")
            
            start_hour, start_minute = map(int, start_time_str.split(":"))
            end_hour, end_minute = map(int, end_time_str.split(":"))
            
            start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            if start_time <= now <= end_time:
                return True
            else:
                logger.info(f"Aktuelle Uhrzeit {now.strftime('%H:%M')} liegt außerhalb des erlaubten Zeitfensters ({start_time_str}-{end_time_str})")
                
                # Wenn vor dem Start, auf Startzeit setzen
                if now < start_time:
                    self.next_sync_time = start_time
                # Wenn nach dem Ende, auf morgen verschieben
                else:
                    tomorrow = now + datetime.timedelta(days=1)
                    self.next_sync_time = tomorrow.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                
                return False
        
        return False
    
    def get_next_sync_time(self) -> Optional[datetime.datetime]:
        """
        Gibt die nächste geplante Synchronisierungszeit zurück.
        
        Returns:
            Nächste geplante Synchronisierungszeit oder None, wenn keine geplant ist
        """
        return self.next_sync_time
    
    def is_running(self) -> bool:
        """
        Prüft, ob die automatische Synchronisierung aktiv ist.
        
        Returns:
            True, wenn die automatische Synchronisierung läuft, sonst False
        """
        return self.running and self.thread and self.thread.is_alive()


if __name__ == "__main__":
    # Test
    def dummy_sync():
        print(f"Synchronisierung ausgeführt um {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    settings = {
        "ENABLED": True,
        "INTERVAL_MINUTES": 1,
        "START_TIME": "00:00",
        "END_TIME": "23:59",
        "DAYS": [1, 2, 3, 4, 5, 6, 7]
    }
    
    scheduler = AutoSyncScheduler(dummy_sync, settings)
    scheduler.start()
    
    try:
        while True:
            next_time = scheduler.get_next_sync_time()
            if next_time:
                print(f"Nächste Synchronisierung um: {next_time.strftime('%H:%M:%S')}")
            time.sleep(30)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Beendet")
