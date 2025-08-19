#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug-Skript für die CallDoc-SQLHK Synchronisierungs-GUI
"""

import sys
import traceback

try:
    from sync_gui_qt import main
    print("Starte die Anwendung...")
    main()
except Exception as e:
    print(f"FEHLER: {e}")
    traceback.print_exc()
    input("Drücken Sie Enter, um fortzufahren...")
