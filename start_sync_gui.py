#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Einfacher Starter für die Synchronisierungs-GUI ohne API-Server
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from sync_gui_qt import SyncApp

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sync_gui_einfach.log")
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starte Synchronisierungs-GUI ohne API-Server")
    
    # Deaktiviere API-Server-Integration
    import sys
    sys.modules['api_integration'] = type('', (), {
        'ApiServerManager': type('', (), {
            '__init__': lambda *args, **kwargs: None,
            'start_server': lambda *args, **kwargs: None,
            'stop_server': lambda *args, **kwargs: None,
            'is_running': lambda *args, **kwargs: False
        })
    })
    
    # Starte die GUI
    app = QApplication(sys.argv)
    window = SyncApp()
    window.show()
    sys.exit(app.exec_())
