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
    import PyQt5
    logger.debug(f"PyQt5 Version: {PyQt5.QtCore.QT_VERSION_STR}")
    
    logger.debug("Importiere sync_gui_qt...")
    from sync_gui_qt import SyncApp, main
    
    logger.debug("Starte die Anwendung...")
    main()
    logger.debug("Anwendung beendet")
except Exception as e:
    logger.error(f"FEHLER: {e}")
    traceback.print_exc()
    input("Drücken Sie Enter, um fortzufahren...")
