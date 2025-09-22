"""
Erstellt einen Desktop-Shortcut für die CallDocSync.exe auf dem Netzlaufwerk P:
"""

import os
import win32com.client
import pythoncom

def create_network_shortcut():
    """Erstellt einen Desktop-Shortcut für die Netzwerk-Deployment"""
    
    # Desktop-Pfad
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    
    # Shortcut-Pfad
    shortcut_path = os.path.join(desktop, 'CallDocSync (Netzwerk).lnk')
    
    # Ziel-Pfad auf dem Netzlaufwerk
    target_path = r'P:\MCP\Calldocinterface\CallDocSync.exe'
    icon_path = r'P:\MCP\Calldocinterface\sync_app.ico'
    working_dir = r'P:\MCP\Calldocinterface'
    
    # COM-Objekt initialisieren
    pythoncom.CoInitialize()
    
    try:
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        
        # Shortcut-Eigenschaften setzen
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = working_dir
        shortcut.IconLocation = icon_path
        shortcut.Description = 'CallDoc-SQLHK Synchronisation (Netzwerk-Version)'
        shortcut.WindowStyle = 1  # Normal window
        
        # Shortcut speichern
        shortcut.save()
        
        print(f"Desktop-Shortcut für Netzwerk-Version erstellt: {shortcut_path}")
        print(f"Ziel: {target_path}")
        print(f"Icon: {icon_path}")
        print(f"Arbeitsverzeichnis: {working_dir}")
        
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    create_network_shortcut()