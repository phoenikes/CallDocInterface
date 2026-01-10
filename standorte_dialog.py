"""
Dialog zur Verwaltung der Herzkatheter-Standorte.

Ermoeglicht das Anzeigen, Bearbeiten, Hinzufuegen und Deaktivieren von Herzkatheter-Standorten.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QMessageBox, QHeaderView, QFormLayout, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from mssql_api_client import MsSqlApiClient
import logging

logger = logging.getLogger(__name__)

# Bekannte Herzkatheter-Raeume aus CallDoc
KNOWN_ROOMS = {
    18: "Rummelsberg 1",
    19: "Rummelsberg 2",
    54: "Offenbach",
    61: "Braunschweig"
}


class StandorteDialog(QDialog):
    """Hauptdialog zur Verwaltung der Herzkatheter-Standorte."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mssql_client = MsSqlApiClient()
        self.setWindowTitle("Herzkatheter-Standorte verwalten")
        self.setMinimumSize(1000, 500)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Erstellt die Benutzeroberflaeche."""
        layout = QVBoxLayout(self)

        # Info-Label
        info_label = QLabel(
            "Hier koennen Sie die Herzkatheter-Standorte verwalten. "
            "Die room_id muss mit dem CallDoc-Raum uebereinstimmen."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "room_id", "PLZ", "Standort-ID",
            "Miete", "Service", "Personal", "Verwaltung", "MPE", "Lizenzen", "Aktiv"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.on_edit)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("Aktualisieren")
        self.btn_refresh.clicked.connect(self.load_data)
        button_layout.addWidget(self.btn_refresh)

        self.btn_new = QPushButton("Neu")
        self.btn_new.clicked.connect(self.on_new)
        button_layout.addWidget(self.btn_new)

        self.btn_edit = QPushButton("Bearbeiten")
        self.btn_edit.clicked.connect(self.on_edit)
        button_layout.addWidget(self.btn_edit)

        self.btn_toggle_active = QPushButton("Aktivieren/Deaktivieren")
        self.btn_toggle_active.clicked.connect(self.on_toggle_active)
        button_layout.addWidget(self.btn_toggle_active)

        button_layout.addStretch()

        self.btn_close = QPushButton("Schliessen")
        self.btn_close.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)

    def load_data(self):
        """Laedt die Herzkatheter-Daten aus der Datenbank."""
        try:
            query = """
                SELECT HerzkatheterID, HerzkatheterName, room_id, HerzkatheterPLZ,
                       Standortid, Herzkathetermiete, HerzkatheterServicekosten,
                       Personalkosten, Verwaltungskosten, MPE, Lizenzen,
                       COALESCE(Aktiv, 1) as Aktiv
                FROM Herzkatheter
                ORDER BY HerzkatheterID
            """
            result = self.mssql_client.execute_sql(query, "SQLHK")

            if not result.get("success"):
                # Vielleicht gibt es das Aktiv-Feld noch nicht
                query = """
                    SELECT HerzkatheterID, HerzkatheterName, room_id, HerzkatheterPLZ,
                           Standortid, Herzkathetermiete, HerzkatheterServicekosten,
                           Personalkosten, Verwaltungskosten, MPE, Lizenzen,
                           1 as Aktiv
                    FROM Herzkatheter
                    ORDER BY HerzkatheterID
                """
                result = self.mssql_client.execute_sql(query, "SQLHK")

            if result.get("success"):
                rows = result.get("rows", [])
                self.table.setRowCount(len(rows))

                for i, row in enumerate(rows):
                    is_active = row.get("Aktiv", 1) == 1

                    # ID
                    item = QTableWidgetItem(str(row.get("HerzkatheterID", "")))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 0, item)

                    # Name
                    item = QTableWidgetItem(str(row.get("HerzkatheterName", "")))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 1, item)

                    # room_id
                    item = QTableWidgetItem(str(row.get("room_id", "")))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 2, item)

                    # PLZ
                    item = QTableWidgetItem(str(row.get("HerzkatheterPLZ", "")))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 3, item)

                    # Standort-ID
                    item = QTableWidgetItem(str(row.get("Standortid", "")))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 4, item)

                    # Kosten-Felder
                    cost_fields = ["Herzkathetermiete", "HerzkatheterServicekosten",
                                   "Personalkosten", "Verwaltungskosten", "MPE", "Lizenzen"]
                    for j, field in enumerate(cost_fields):
                        value = row.get(field, 0)
                        if value:
                            try:
                                value = f"{float(value):,.2f}"
                            except:
                                value = str(value)
                        else:
                            value = "0.00"
                        item = QTableWidgetItem(value)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        if not is_active:
                            item.setForeground(QBrush(QColor(150, 150, 150)))
                        self.table.setItem(i, 5 + j, item)

                    # Aktiv
                    item = QTableWidgetItem("Ja" if is_active else "Nein")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
                    self.table.setItem(i, 11, item)

                logger.info(f"{len(rows)} Herzkatheter-Standorte geladen")
            else:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Laden: {result.get('error')}")

        except Exception as e:
            logger.error(f"Fehler beim Laden der Standorte: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Standorte:\n{str(e)}")

    def on_new(self):
        """Oeffnet Dialog zum Erstellen eines neuen Standorts."""
        dialog = StandortEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def on_edit(self):
        """Oeffnet Dialog zum Bearbeiten des ausgewaehlten Standorts."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Hinweis", "Bitte waehlen Sie einen Standort aus.")
            return

        row = selected[0].row()
        herzkatheter_id = int(self.table.item(row, 0).text())

        dialog = StandortEditDialog(self, herzkatheter_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def on_toggle_active(self):
        """Aktiviert oder deaktiviert den ausgewaehlten Standort."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Hinweis", "Bitte waehlen Sie einen Standort aus.")
            return

        row = selected[0].row()
        herzkatheter_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        is_active = self.table.item(row, 11).text() == "Ja"

        action = "deaktivieren" if is_active else "aktivieren"
        reply = QMessageBox.question(
            self, "Bestaetigung",
            f"Moechten Sie den Standort '{name}' wirklich {action}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                new_status = 0 if is_active else 1
                query = f"UPDATE Herzkatheter SET Aktiv = {new_status} WHERE HerzkatheterID = {herzkatheter_id}"
                result = self.mssql_client.execute_sql(query, "SQLHK")

                if result.get("success") or "does not return rows" in str(result.get("error", "")):
                    QMessageBox.information(self, "Erfolg", f"Standort wurde {'deaktiviert' if is_active else 'aktiviert'}.")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Fehler", f"Fehler: {result.get('error')}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler: {str(e)}")


class StandortEditDialog(QDialog):
    """Dialog zum Bearbeiten oder Erstellen eines Herzkatheter-Standorts."""

    def __init__(self, parent=None, herzkatheter_id=None):
        super().__init__(parent)
        self.mssql_client = MsSqlApiClient()
        self.herzkatheter_id = herzkatheter_id
        self.is_new = herzkatheter_id is None

        self.setWindowTitle("Neuer Standort" if self.is_new else "Standort bearbeiten")
        self.setMinimumWidth(450)
        self.setup_ui()

        if not self.is_new:
            self.load_data()

    def setup_ui(self):
        """Erstellt die Benutzeroberflaeche."""
        layout = QVBoxLayout(self)

        # Formular
        form_layout = QFormLayout()

        # Name
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("z.B. Muenchen")
        form_layout.addRow("Name:", self.txt_name)

        # room_id mit Dropdown und manueller Eingabe
        room_layout = QHBoxLayout()
        self.cmb_room = QComboBox()
        self.cmb_room.addItem("-- Waehlen oder manuell eingeben --", None)
        for room_id, name in KNOWN_ROOMS.items():
            self.cmb_room.addItem(f"{room_id} - {name}", room_id)
        self.cmb_room.currentIndexChanged.connect(self.on_room_selected)
        room_layout.addWidget(self.cmb_room)

        self.txt_room_id = QSpinBox()
        self.txt_room_id.setRange(1, 999)
        self.txt_room_id.setFixedWidth(80)
        room_layout.addWidget(self.txt_room_id)
        form_layout.addRow("room_id:", room_layout)

        # PLZ
        self.txt_plz = QSpinBox()
        self.txt_plz.setRange(10000, 99999)
        self.txt_plz.setValue(90000)
        form_layout.addRow("PLZ:", self.txt_plz)

        # Standort-ID
        self.txt_standort_id = QSpinBox()
        self.txt_standort_id.setRange(1, 99)
        self.txt_standort_id.setValue(1)
        form_layout.addRow("Standort-ID:", self.txt_standort_id)

        layout.addLayout(form_layout)

        # Kosten-Gruppe
        cost_group = QGroupBox("Kosten (EUR pro Monat)")
        cost_layout = QFormLayout()

        self.txt_miete = QDoubleSpinBox()
        self.txt_miete.setRange(0, 99999)
        self.txt_miete.setDecimals(2)
        self.txt_miete.setValue(0)
        cost_layout.addRow("Miete:", self.txt_miete)

        self.txt_service = QDoubleSpinBox()
        self.txt_service.setRange(0, 99999)
        self.txt_service.setDecimals(2)
        self.txt_service.setValue(0)
        cost_layout.addRow("Servicekosten:", self.txt_service)

        self.txt_personal = QDoubleSpinBox()
        self.txt_personal.setRange(0, 99999)
        self.txt_personal.setDecimals(2)
        self.txt_personal.setValue(0)
        cost_layout.addRow("Personalkosten:", self.txt_personal)

        self.txt_verwaltung = QDoubleSpinBox()
        self.txt_verwaltung.setRange(0, 99999)
        self.txt_verwaltung.setDecimals(2)
        self.txt_verwaltung.setValue(0)
        cost_layout.addRow("Verwaltungskosten:", self.txt_verwaltung)

        self.txt_mpe = QDoubleSpinBox()
        self.txt_mpe.setRange(0, 99999)
        self.txt_mpe.setDecimals(2)
        self.txt_mpe.setValue(0)
        cost_layout.addRow("MPE:", self.txt_mpe)

        self.txt_lizenzen = QDoubleSpinBox()
        self.txt_lizenzen.setRange(0, 99999)
        self.txt_lizenzen.setDecimals(2)
        self.txt_lizenzen.setValue(0)
        cost_layout.addRow("Lizenzen:", self.txt_lizenzen)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        # Service-Intervall
        form_layout2 = QFormLayout()
        self.txt_service_intervall = QSpinBox()
        self.txt_service_intervall.setRange(1, 12)
        self.txt_service_intervall.setValue(4)
        form_layout2.addRow("Service-Intervall (Monate):", self.txt_service_intervall)
        layout.addLayout(form_layout2)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Speichern")
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save.setDefault(True)
        button_layout.addWidget(self.btn_save)

        layout.addLayout(button_layout)

    def on_room_selected(self, index):
        """Aktualisiert das room_id Feld wenn ein bekannter Raum gewaehlt wird."""
        room_id = self.cmb_room.currentData()
        if room_id:
            self.txt_room_id.setValue(room_id)

    def load_data(self):
        """Laedt die Daten des zu bearbeitenden Standorts."""
        try:
            query = f"""
                SELECT * FROM Herzkatheter
                WHERE HerzkatheterID = {self.herzkatheter_id}
            """
            result = self.mssql_client.execute_sql(query, "SQLHK")

            if result.get("success") and result.get("rows"):
                row = result["rows"][0]

                self.txt_name.setText(row.get("HerzkatheterName", ""))

                room_id = row.get("room_id", 0)
                self.txt_room_id.setValue(room_id or 0)

                # Setze Dropdown wenn bekannter Raum
                for i in range(self.cmb_room.count()):
                    if self.cmb_room.itemData(i) == room_id:
                        self.cmb_room.setCurrentIndex(i)
                        break

                self.txt_plz.setValue(row.get("HerzkatheterPLZ", 0) or 0)
                self.txt_standort_id.setValue(row.get("Standortid", 1) or 1)

                # Kosten
                self.txt_miete.setValue(float(row.get("Herzkathetermiete", 0) or 0))
                self.txt_service.setValue(float(row.get("HerzkatheterServicekosten", 0) or 0))
                self.txt_personal.setValue(float(row.get("Personalkosten", 0) or 0))
                self.txt_verwaltung.setValue(float(row.get("Verwaltungskosten", 0) or 0))
                self.txt_mpe.setValue(float(row.get("MPE", 0) or 0))
                self.txt_lizenzen.setValue(float(row.get("Lizenzen", 0) or 0))
                self.txt_service_intervall.setValue(row.get("HerzkatheterServiceIntervall", 4) or 4)

        except Exception as e:
            logger.error(f"Fehler beim Laden des Standorts: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden:\n{str(e)}")

    def on_save(self):
        """Speichert den Standort."""
        # Validierung
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein.")
            return

        room_id = self.txt_room_id.value()
        if room_id < 1:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine gueltige room_id ein.")
            return

        try:
            if self.is_new:
                # INSERT
                query = f"""
                    INSERT INTO Herzkatheter (
                        HerzkatheterName, room_id, HerzkatheterPLZ, Standortid,
                        Herzkathetermiete, HerzkatheterServicekosten, Personalkosten,
                        Verwaltungskosten, MPE, Lizenzen, HerzkatheterServiceIntervall, Aktiv
                    ) VALUES (
                        '{name}', {room_id}, {self.txt_plz.value()}, {self.txt_standort_id.value()},
                        {self.txt_miete.value()}, {self.txt_service.value()}, {self.txt_personal.value()},
                        {self.txt_verwaltung.value()}, {self.txt_mpe.value()}, {self.txt_lizenzen.value()},
                        {self.txt_service_intervall.value()}, 1
                    )
                """
            else:
                # UPDATE
                query = f"""
                    UPDATE Herzkatheter SET
                        HerzkatheterName = '{name}',
                        room_id = {room_id},
                        HerzkatheterPLZ = {self.txt_plz.value()},
                        Standortid = {self.txt_standort_id.value()},
                        Herzkathetermiete = {self.txt_miete.value()},
                        HerzkatheterServicekosten = {self.txt_service.value()},
                        Personalkosten = {self.txt_personal.value()},
                        Verwaltungskosten = {self.txt_verwaltung.value()},
                        MPE = {self.txt_mpe.value()},
                        Lizenzen = {self.txt_lizenzen.value()},
                        HerzkatheterServiceIntervall = {self.txt_service_intervall.value()}
                    WHERE HerzkatheterID = {self.herzkatheter_id}
                """

            result = self.mssql_client.execute_sql(query, "SQLHK")

            # "does not return rows" ist normal bei INSERT/UPDATE
            if result.get("success") or "does not return rows" in str(result.get("error", "")):
                action = "erstellt" if self.is_new else "aktualisiert"
                QMessageBox.information(self, "Erfolg", f"Standort '{name}' wurde {action}.")
                self.accept()
            else:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Speichern:\n{result.get('error')}")

        except Exception as e:
            logger.error(f"Fehler beim Speichern des Standorts: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{str(e)}")
