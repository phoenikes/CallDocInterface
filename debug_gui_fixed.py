#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Erweitertes Debug-Skript für die CallDoc-SQLHK Synchronisierungs-GUI
"""

import sys
import traceback
import logging

# Konfiguriere Logging für detaillierte Ausgabe
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Starte Debug-Skript")

try:
    logger.debug("Importiere Module...")
    from PyQt5 import QtCore
    logger.debug(f"PyQt5 Version: {QtCore.QT_VERSION_STR}")
    
    logger.debug("Importiere log_viewer und dashboard...")
    try:
        from log_viewer import LogViewerTab
        logger.debug("LogViewerTab erfolgreich importiert")
    except Exception as e:
        logger.error(f"Fehler beim Importieren von LogViewerTab: {e}")
        traceback.print_exc()
    
    try:
        from dashboard import DashboardTab
        logger.debug("DashboardTab erfolgreich importiert")
    except Exception as e:
        logger.error(f"Fehler beim Importieren von DashboardTab: {e}")
        traceback.print_exc()
    
    logger.debug("Importiere sync_gui_qt...")
    from sync_gui_qt import SyncApp, main
    
    logger.debug("Starte die Anwendung...")
    main()
    logger.debug("Anwendung beendet")
except Exception as e:
    logger.error(f"FEHLER: {e}")
    traceback.print_exc()
    print("Drücken Sie Enter, um fortzufahren...")
    sys.stdin.readline()
