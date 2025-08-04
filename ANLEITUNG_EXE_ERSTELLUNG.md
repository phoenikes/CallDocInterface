# Anleitung zur Erstellung der ausführbaren Datei (EXE)

Diese Dokumentation beschreibt den Prozess zur Erstellung der ausführbaren Datei `heydok-cathlab-communicator.exe` aus dem Python-Projekt.

## Voraussetzungen

- Python 3.8 oder höher
- PyInstaller (Installation: `pip install pyinstaller`)
- Alle Projektabhängigkeiten müssen installiert sein

## Schritt 1: Spec-Datei erstellen

Die Spec-Datei definiert, wie PyInstaller die ausführbare Datei erstellen soll. Erstelle eine Datei namens `heydok-cathlab-communicator.spec` mit folgendem Inhalt:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['sync_gui_qt.py'],
    pathex=['c:\\Users\\administrator.PRAXIS\\PycharmProjects\\calldocinterface'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'PyQt5',
        'requests',
        'sqlalchemy',
        'urllib3',
        'json',
        'datetime',
        'logging',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='heydok-cathlab-communicator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='',
)
```

### Wichtige Elemente der Spec-Datei:

- **Hauptskript**: `sync_gui_qt.py` ist das Hauptskript, das ausgeführt wird
- **Pfad**: Der absolute Pfad zum Projektverzeichnis
- **Hidden Imports**: Alle Module, die PyInstaller möglicherweise nicht automatisch erkennt
- **Name**: Der Name der ausführbaren Datei (`heydok-cathlab-communicator`)
- **Console**: `False` bedeutet, dass kein Konsolenfenster angezeigt wird

## Schritt 2: Ausführbare Datei erstellen

Führe PyInstaller mit der Spec-Datei aus:

```
pyinstaller heydok-cathlab-communicator.spec
```

Dieser Befehl erstellt die ausführbare Datei im Verzeichnis `dist`.

## Schritt 3: Überprüfung und Verteilung

Die fertige ausführbare Datei befindet sich im Verzeichnis `dist`:

```
dist/heydok-cathlab-communicator.exe
```

Diese Datei kann auf andere Windows-Computer kopiert und dort ausgeführt werden, ohne dass Python installiert sein muss.

## Wichtige Hinweise

1. **Abhängigkeiten**: Alle Abhängigkeiten werden in die EXE eingebettet, daher ist die Datei relativ groß.
2. **Warnungen**: PyInstaller zeigt möglicherweise Warnungen an, die in den meisten Fällen ignoriert werden können.
3. **Kompatibilität**: Die EXE-Datei ist nur mit Windows-Systemen kompatibel.
4. **Antivirenprogramme**: Manche Antivirenprogramme könnten die EXE-Datei fälschlicherweise als Bedrohung einstufen.
5. **Visual C++ Redistributable**: Auf manchen Systemen muss möglicherweise die Visual C++ Redistributable installiert sein.

## Fehlerbehebung

Wenn die ausführbare Datei nicht startet:

1. Überprüfe, ob alle Abhängigkeiten in der `hiddenimports`-Liste enthalten sind
2. Stelle sicher, dass die Visual C++ Redistributable installiert ist
3. Versuche, die ausführbare Datei mit Konsolenfenster zu erstellen (`console=True`), um Fehlermeldungen zu sehen

## Aktualisierung der ausführbaren Datei

Um die ausführbare Datei nach Codeänderungen zu aktualisieren:

1. Aktualisiere den Quellcode
2. Führe erneut `pyinstaller heydok-cathlab-communicator.spec` aus
3. Ersetze die alte ausführbare Datei durch die neue Version

## Versionierung

Es wird empfohlen, die Versionsnummer in den Dateinamen aufzunehmen, z.B. `heydok-cathlab-communicator-v4.0.exe`, um verschiedene Versionen zu unterscheiden.
