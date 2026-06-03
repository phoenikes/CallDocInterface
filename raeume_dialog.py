"""
Dialog zur Anzeige aller Raeume aus CallDoc.

Holt die Stammdaten live aus dem CallDoc-Endpunkt /rooms/ und zeigt sie in einer
Tabelle. Zusaetzlich wird angezeigt, ob der Raum in constants.py (ROOMS) bekannt
ist und ob er in SQLHK als Herzkatheter-Labor (Herzkatheter.room_id) hinterlegt
ist.

Der Dialog ist modal (exec_()): Der restliche Ablauf wartet, bis er geschlossen
wird.
"""

import logging
import requests

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QCheckBox, QHeaderView, QMessageBox,
    QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

from constants import API_BASE_URL, ROOMS

logger = logging.getLogger(__name__)

ROOMS_URL = f"{API_BASE_URL}/rooms/"


class RaeumeDialog(QDialog):
    """Modaler Dialog: Raeumeliste direkt aus CallDoc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raeume aus CallDoc")
        self.setMinimumSize(950, 600)

        self._all_rows = []
        self._hk_map = {}  # room_id -> HerzkatheterName (SQLHK)

        self.setup_ui()
        self.load_data()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Lade Raeume aus CallDoc ...")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        filter_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Suche nach Raumname, Standort oder ID ...")
        self.txt_search.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.txt_search)

        self.chk_only_hk = QCheckBox("Nur Herzkatheter-Labore (SQLHK)")
        self.chk_only_hk.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.chk_only_hk)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "CallDoc-ID", "Raumname", "Standort", "Kommentar",
            "in constants.py", "HK-Labor (SQLHK)"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Aktualisieren")
        self.btn_refresh.clicked.connect(self.load_data)
        button_layout.addWidget(self.btn_refresh)
        button_layout.addStretch()
        self.btn_close = QPushButton("Schliessen")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setDefault(True)
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)

    # ---------------------------------------------------------------- Daten
    def load_data(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._hk_map = self._load_hk_mapping()

            resp = requests.get(ROOMS_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", [])

            known_ids = set(ROOMS.values())
            rows = []
            for d in data:
                rid = d.get("id")
                rows.append({
                    "id": rid,
                    "name": d.get("room_name") or "",
                    "location": d.get("location_name") or "",
                    "comment": d.get("comment") or "",
                    "in_constants": rid in known_ids,
                    "hk_name": self._hk_map.get(rid),
                })
            self._all_rows = sorted(rows, key=lambda r: (r["id"] is None, r["id"] or 0))

            hk_count = sum(1 for r in self._all_rows if r["hk_name"])
            self.info_label.setText(
                f"CallDoc /rooms/ : {len(self._all_rows)} Raeume - "
                f"davon {hk_count} als Herzkatheter-Labor in SQLHK hinterlegt. "
                f"Quelle: {ROOMS_URL}"
            )
            self.apply_filter()
            logger.info("Raeume aus CallDoc geladen: %s", len(self._all_rows))

        except requests.RequestException as e:
            self.info_label.setText("Fehler beim Laden aus CallDoc.")
            QMessageBox.critical(self, "Fehler",
                                 f"CallDoc nicht erreichbar ({ROOMS_URL}):\n{e}")
            logger.error("Fehler beim Laden der Raeume: %s", e)
        finally:
            QApplication.restoreOverrideCursor()

    def _load_hk_mapping(self):
        """room_id -> HerzkatheterName aus SQLHK (best effort)."""
        try:
            from mssql_api_client import MsSqlApiClient
            client = MsSqlApiClient()
            query = ("SELECT HerzkatheterName, room_id FROM Herzkatheter "
                     "WHERE room_id IS NOT NULL")
            result = client.execute_sql(query, "SQLHK")
            mapping = {}
            if result.get("success"):
                for row in result.get("rows", []):
                    rid = row.get("room_id")
                    if rid is not None:
                        mapping[rid] = row.get("HerzkatheterName")
            return mapping
        except Exception as e:
            logger.warning("SQLHK-HK-Mapping nicht verfuegbar: %s", e)
            return {}

    # --------------------------------------------------------------- Filter
    def apply_filter(self):
        search = self.txt_search.text().strip().lower()
        only_hk = self.chk_only_hk.isChecked()

        visible = []
        for r in self._all_rows:
            if only_hk and not r["hk_name"]:
                continue
            if search and search not in r["name"].lower() \
                    and search not in r["location"].lower() \
                    and search not in str(r["id"]):
                continue
            visible.append(r)
        self._fill_table(visible)

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            is_hk = bool(r["hk_name"])
            values = [
                str(r["id"]),
                r["name"],
                r["location"],
                r["comment"],
                "JA" if r["in_constants"] else "-",
                r["hk_name"] if is_hk else "-",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col in (0,):
                    item.setTextAlignment(Qt.AlignCenter)
                # HK-Labore gruen hervorheben (sync-relevant)
                if is_hk:
                    item.setBackground(QBrush(QColor(210, 240, 210)))
                self.table.setItem(i, col, item)
