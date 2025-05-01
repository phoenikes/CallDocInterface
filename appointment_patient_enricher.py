from constants import APPOINTMENT_TYPES, DOCTORS, ROOMS
from main import CallDocInterface
import json
from typing import Optional, List
import os
import csv
import logging

class AppointmentPatientEnricher:
    """
    Sucht Termine und reichert sie mit Patientendaten an. Validiert IDs gegen Konstanten.
    Bietet Export- und Utility-Methoden.
    """
    def __init__(self, from_date: str, to_date: str, appointment_type_id: int, doctor_id: Optional[int] = None, room_id: Optional[int] = None, patient_cache: Optional[dict] = None):
        """
        Initialisiert den Enricher für einen bestimmten Zeitraum und Filter.
        - from_date, to_date: Zeitraum im Format YYYY-MM-DD
        - appointment_type_id: Pflicht, muss in APPOINTMENT_TYPES enthalten sein
        - doctor_id, room_id: Optional, falls gesetzt Validierung gegen DOCTORS/ROOMS
        - patient_cache: Optionales Dict für Caching von Patientendaten
        """
        if appointment_type_id not in APPOINTMENT_TYPES.values():
            logging.error(f"Ungültiger appointment_type_id: {appointment_type_id}")
            raise ValueError(f"Ungültiger appointment_type_id: {appointment_type_id}")
        if doctor_id is not None and doctor_id not in DOCTORS.values():
            logging.error(f"Ungültiger doctor_id: {doctor_id}")
            raise ValueError(f"Ungültiger doctor_id: {doctor_id}")
        if room_id is not None and room_id not in ROOMS.values():
            logging.error(f"Ungültiger room_id: {room_id}")
            raise ValueError(f"Ungültiger room_id: {room_id}")
        self.from_date = from_date
        self.to_date = to_date
        self.appointment_type_id = appointment_type_id
        self.doctor_id = doctor_id
        self.room_id = room_id
        self.interface = CallDocInterface(from_date=from_date, to_date=to_date)
        self.raw_appointments = None
        self.enriched_appointments = None
        self.patient_cache = patient_cache if patient_cache is not None else {}

    def fetch_appointments(self):
        """
        Ruft die Termine für den gesetzten Zeitraum und Filter (appointment_type_id, doctor_id, room_id) ab.
        Speichert das Roh-Ergebnis in self.raw_appointments.
        Gibt das Roh-Ergebnis zurück (API-Response als dict).
        """
        params = {"appointment_type_id": self.appointment_type_id}
        if self.doctor_id:
            params["employee_id"] = self.doctor_id
        if self.room_id:
            params["room_id"] = self.room_id
        try:
            self.raw_appointments = self.interface.appointment_search(**params)
            logging.info(f"Termine geladen: {len(self.raw_appointments.get('data', []))} für {self.from_date}")
        except Exception as e:
            logging.error(f"Fehler beim Laden der Termine: {e}")
            self.raw_appointments = {"data": []}
        return self.raw_appointments

    def enrich_with_patients(self):
        """
        Ergänzt alle geladenen Termine um Patientendaten (Name, Vorname, Geburtsdatum) anhand der piz.
        Speichert das angereicherte Ergebnis in self.enriched_appointments.
        Gibt das angereicherte Ergebnis zurück (dict).
        """
        if self.raw_appointments is None:
            self.fetch_appointments()
        appointments = self.raw_appointments.get("data", [])
        piz_set = set()
        for appt in appointments:
            piz = appt.get("piz")
            if piz and piz not in piz_set:
                if piz in self.patient_cache:
                    patient_data = self.patient_cache[piz]
                    logging.debug(f"Patientendaten aus Cache für piz {piz}")
                else:
                    try:
                        patient_data = self.interface.get_patient_by_piz(piz)
                        self.patient_cache[piz] = patient_data
                        logging.info(f"Patientendaten geladen für piz {piz}")
                    except Exception as e:
                        logging.error(f"Fehler beim Laden der Patientendaten für piz {piz}: {e}")
                        patient_data = None
                last_name = first_name = date_of_birth = None
                if patient_data and isinstance(patient_data, dict):
                    patients_list = patient_data.get("patients")
                    if patients_list and isinstance(patients_list, list) and len(patients_list) > 0:
                        pat = patients_list[0]
                        last_name = pat.get("surname")
                        first_name = pat.get("name")
                        date_of_birth = pat.get("date_of_birth")
                appt["last_name"] = last_name
                appt["first_name"] = first_name
                appt["date_of_birth"] = date_of_birth
                piz_set.add(piz)
        self.enriched_appointments = self.raw_appointments
        return self.enriched_appointments

    def get_result(self):
        """
        Gibt das aktuell angereicherte Ergebnis zurück (dict).
        Falls noch nicht angereichert, wird das Roh-Ergebnis geliefert.
        """
        return self.enriched_appointments or self.raw_appointments

    def get_filename(self):
        """
        Erzeugt den Dateinamen für den Export auf Basis der gesetzten Filter und des Zeitraums.
        Format: FROM_TO_APPOINTMENTTYPE_DOCTOR_ROOM.json (0 als Platzhalter falls kein Filter gesetzt)
        """
        atype = self.appointment_type_id if self.appointment_type_id is not None else 0
        doctor = self.doctor_id if self.doctor_id is not None else 0
        room = self.room_id if self.room_id is not None else 0
        return f"{self.from_date}_{self.to_date}_{atype}_{doctor}_{room}.json"

    def to_json(self, directory: str = r"P:/imports/cathlab/json_heydoc"):
        """
        Speichert das angereicherte Ergebnis als JSON-Datei im Zielverzeichnis.
        Der Dateiname wird automatisch generiert.
        """
        filename = self.get_filename()
        path = os.path.join(directory, filename)
        os.makedirs(directory, exist_ok=True)
        data = self.get_result()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Ergebnis wurde nach {path} geschrieben.")

    def to_csv(self, path: str, fields: Optional[List[str]] = None):
        """
        Exportiert das angereicherte Ergebnis als CSV-Datei.
        Felder können vorgegeben werden, sonst werden alle Felder aus dem ersten Termin exportiert.
        """
        data = self.get_result()
        appointments = data.get("data", [])
        if not appointments:
            print("Keine Daten zum Export vorhanden.")
            return
        if fields is None:
            fields = list(appointments[0].keys())
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for appt in appointments:
                writer.writerow({k: appt.get(k, "") for k in fields})
        print(f"CSV wurde nach {path} geschrieben.")

    @staticmethod
    def get_allowed_appointment_types():
        """
        Gibt alle erlaubten Appointment-Typen (dict) zurück.
        """
        return APPOINTMENT_TYPES

    @staticmethod
    def get_allowed_doctors():
        """
        Gibt alle erlaubten Ärzte (dict) zurück.
        """
        return DOCTORS

    @staticmethod
    def get_allowed_rooms():
        """
        Gibt alle erlaubten Räume (dict) zurück.
        """
        return ROOMS
