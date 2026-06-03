"""
Dialog zur Anzeige aller Termin-/Untersuchungsarten aus CallDoc.

Holt die Stammdaten live aus dem CallDoc-Endpunkt /appointment-types/ und zeigt
sie in einer Tabelle. Zusaetzlich wird angezeigt, ob der Typ in constants.py
(APPOINTMENT_TYPES) bekannt ist und ob er in SQLHK auf eine Untersuchungart
gemappt ist (Untersuchungart.appointment_type -> JSON {"1": <calldoc_id>}).

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

from constants import API_BASE_URL, APPOINTMENT_TYPES

logger = logging.getLogger(__name__)

TYPES_URL = f"{API_BASE_URL}/appointment-types/"


class UntersuchungsartenDialog(QDialog):
    """Modaler Dialog: Untersuchungsarten direkt aus CallDoc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Untersuchungsarten aus CallDoc")
        self.setMinimumSize(900, 600)

        self._all_rows = []
        self._sqlhk_map = {}  # calldoc_type_id -> "ID: Name" (SQLHK Untersuchungart)

        self.setup_ui()
        self.load_data()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Lade Untersuchungsarten aus CallDoc ...")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        filter_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Suche nach Typ, Kategorie oder ID ...")
        self.txt_search.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.txt_search)

        self.chk_only_sqlhk = QCheckBox("Nur in SQLHK gemappt")
        self.chk_only_sqlhk.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.chk_only_sqlhk)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "CallDoc-ID", "Typ", "Kategorie (macro_type)",
            "in constants.py", "SQLHK Untersuchungart"
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
            self._sqlhk_map = self._load_sqlhk_mapping()

            resp = requests.get(TYPES_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", [])

            known_ids = set(APPOINTMENT_TYPES.values())
            rows = []
            for d in data:
                tid = d.get("id")
                rows.append({
                    "id": tid,
                    "type": d.get("type") or "",
                    "macro": d.get("macro_type") or "",
                    "in_constants": tid in known_ids,
                    "sqlhk": self._sqlhk_map.get(tid),
                })
            self._all_rows = sorted(rows, key=lambda r: (r["id"] is None, r["id"] or 0))

            mapped = sum(1 for r in self._all_rows if r["sqlhk"])
            self.info_label.setText(
                f"CallDoc /appointment-types/ : {len(self._all_rows)} Typen - "
                f"davon {mapped} in SQLHK auf eine Untersuchungart gemappt. "
                f"Quelle: {TYPES_URL}"
            )
            self.apply_filter()
            logger.info("Untersuchungsarten aus CallDoc geladen: %s", len(self._all_rows))

        except requests.RequestException as e:
            self.info_label.setText("Fehler beim Laden aus CallDoc.")
            QMessageBox.critical(self, "Fehler",
                                 f"CallDoc nicht erreichbar ({TYPES_URL}):\n{e}")
            logger.error("Fehler beim Laden der Untersuchungsarten: %s", e)
        finally:
            QApplication.restoreOverrideCursor()

    def _load_sqlhk_mapping(self):
        """calldoc_type_id -> 'UntersuchungartID: Name' aus SQLHK (best effort)."""
        try:
            from mssql_api_client import MsSqlApiClient
            client = MsSqlApiClient()
            query = (
                "SELECT UntersuchungartID, UntersuchungartName, "
                "JSON_VALUE(appointment_type, '$.\"1\"') AS calldoc_type_id "
                "FROM Untersuchungart WHERE appointment_type IS NOT NULL"
            )
            result = client.execute_sql(query, "SQLHK")
            mapping = {}
            if result.get("success"):
                for row in result.get("rows", []):
                    raw = row.get("calldoc_type_id")
                    if raw in (None, "", "None"):
                        continue
                    try:
                        cid = int(raw)
                    except (TypeError, ValueError):
                        continue
                    mapping[cid] = f"{row.get('UntersuchungartID')}: {row.get('UntersuchungartName')}"
            return mapping
        except Exception as e:
            logger.warning("SQLHK-Untersuchungart-Mapping nicht verfuegbar: %s", e)
            return {}

    # --------------------------------------------------------------- Filter
    def apply_filter(self):
        search = self.txt_search.text().strip().lower()
        only_sqlhk = self.chk_only_sqlhk.isChecked()

        visible = []
        for r in self._all_rows:
            if only_sqlhk and not r["sqlhk"]:
                continue
            if search and search not in r["type"].lower() \
                    and search not in r["macro"].lower() \
                    and search not in str(r["id"]):
                continue
            visible.append(r)
        self._fill_table(visible)

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            is_mapped = bool(r["sqlhk"])
            values = [
                str(r["id"]),
                r["type"],
                r["macro"],
                "JA" if r["in_constants"] else "-",
                r["sqlhk"] if is_mapped else "-",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col in (0,):
                    item.setTextAlignment(Qt.AlignCenter)
                # In SQLHK gemappte Typen gruen hervorheben (sync-relevant)
                if is_mapped:
                    item.setBackground(QBrush(QColor(210, 240, 210)))
                self.table.setItem(i, col, item)
