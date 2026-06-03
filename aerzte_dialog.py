"""
Dialog zur Anzeige aller Aerzte/Mitarbeiter aus CallDoc.

Holt die Stammdaten live aus dem CallDoc-Endpunkt /doctors/ und zeigt sie in
einer Tabelle. Zusaetzlich wird angezeigt, ob der Arzt bereits in constants.py
(DOCTORS) und in SQLHK (Untersucherabrechnung.employee_id) gemappt ist.

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

from constants import API_BASE_URL, DOCTORS

logger = logging.getLogger(__name__)

DOCTORS_URL = f"{API_BASE_URL}/doctors/"


class AerzteDialog(QDialog):
    """Modaler Dialog: Aerzteliste direkt aus CallDoc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aerzte aus CallDoc")
        self.setMinimumSize(900, 600)

        self._all_rows = []          # roh: Liste der angereicherten Arzt-Dicts
        self._sqlhk_map = {}         # employee_id -> UntersucherAbrechnungID

        self.setup_ui()
        self.load_data()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Lade Aerzte aus CallDoc ...")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Filterzeile
        filter_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Suche nach Name oder ID ...")
        self.txt_search.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.txt_search)

        self.chk_only_doctors = QCheckBox("Nur Aerzte (role=Doctor)")
        self.chk_only_doctors.setChecked(True)
        self.chk_only_doctors.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.chk_only_doctors)

        self.chk_only_unmapped = QCheckBox("Nur nicht in constants.py")
        self.chk_only_unmapped.stateChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.chk_only_unmapped)

        layout.addLayout(filter_layout)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "CallDoc-ID", "Name", "Rolle", "in constants.py", "in SQLHK (ID)"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Buttons
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
        """Holt Aerzte aus CallDoc und (optional) das SQLHK-Mapping."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._sqlhk_map = self._load_sqlhk_mapping()

            resp = requests.get(DOCTORS_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", [])

            mapped_ids = set(DOCTORS.values())
            rows = []
            for d in data:
                did = d.get("id")
                name = " ".join(part for part in [
                    (d.get("title") or "").strip(),
                    (d.get("first_name") or "").strip(),
                    (d.get("last_name") or "").strip(),
                ] if part)
                rows.append({
                    "id": did,
                    "name": name or "(ohne Namen)",
                    "role": d.get("role") or "-",
                    "in_constants": did in mapped_ids,
                    "sqlhk_id": self._sqlhk_map.get(did),
                })
            self._all_rows = sorted(rows, key=lambda r: (r["id"] is None, r["id"] or 0))

            doctors = sum(1 for r in self._all_rows if r["role"] == "Doctor")
            unmapped = sum(1 for r in self._all_rows
                           if r["role"] == "Doctor" and not r["in_constants"])
            self.info_label.setText(
                f"CallDoc /doctors/ : {len(self._all_rows)} Eintraege "
                f"({doctors} Aerzte) - davon {unmapped} nicht in constants.py. "
                f"Quelle: {DOCTORS_URL}"
            )
            self.apply_filter()
            logger.info("Aerzte aus CallDoc geladen: %s", len(self._all_rows))

        except requests.RequestException as e:
            self.info_label.setText("Fehler beim Laden aus CallDoc.")
            QMessageBox.critical(
                self, "Fehler",
                f"CallDoc nicht erreichbar ({DOCTORS_URL}):\n{e}"
            )
            logger.error("Fehler beim Laden der Aerzte: %s", e)
        finally:
            QApplication.restoreOverrideCursor()

    def _load_sqlhk_mapping(self):
        """employee_id -> UntersucherAbrechnungID aus SQLHK (best effort)."""
        try:
            from mssql_api_client import MsSqlApiClient
            client = MsSqlApiClient()
            query = (
                "SELECT UntersucherAbrechnungID, employee_id "
                "FROM Untersucherabrechnung WHERE employee_id IS NOT NULL"
            )
            result = client.execute_sql(query, "SQLHK")
            mapping = {}
            if result.get("success"):
                for row in result.get("rows", []):
                    eid = row.get("employee_id")
                    if eid is not None:
                        mapping[eid] = row.get("UntersucherAbrechnungID")
            return mapping
        except Exception as e:  # DB optional - Dialog funktioniert auch ohne
            logger.warning("SQLHK-Mapping nicht verfuegbar: %s", e)
            return {}

    # --------------------------------------------------------------- Filter
    def apply_filter(self):
        search = self.txt_search.text().strip().lower()
        only_doctors = self.chk_only_doctors.isChecked()
        only_unmapped = self.chk_only_unmapped.isChecked()

        visible = []
        for r in self._all_rows:
            if only_doctors and r["role"] != "Doctor":
                continue
            if only_unmapped and r["in_constants"]:
                continue
            if search and search not in r["name"].lower() and search not in str(r["id"]):
                continue
            visible.append(r)

        self._fill_table(visible)

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            in_const = r["in_constants"]
            sqlhk_id = r["sqlhk_id"]

            values = [
                str(r["id"]),
                r["name"],
                r["role"],
                "JA" if in_const else "FEHLT",
                str(sqlhk_id) if sqlhk_id is not None else "-",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col in (0, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                # Hervorhebung: Arzt, der nicht in constants.py ist -> gelb
                if r["role"] == "Doctor" and not in_const:
                    item.setBackground(QBrush(QColor(255, 245, 200)))
                self.table.setItem(i, col, item)
