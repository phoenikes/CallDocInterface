import logging
try:
    import holidays
except ImportError:
    holidays = None
import json
import os
from datetime import datetime, timedelta
from appointment_patient_enricher import AppointmentPatientEnricher
from constants import APPOINTMENT_TYPES, DOCTORS, ROOMS

class WeeklyAppointmentExporter:
    """
    Exportiert Termine für eine Kalenderwoche (Mo-Fr), optional ohne Feiertage.
    Feiertage werden automatisch erkannt (falls holidays installiert).
    """
    def __init__(self, week_start: str, appointment_type_id: int, doctor_id: int = None, room_id: int = None, skip_holidays: bool = True, export_directory: str = None, country: str = "DE", subdiv: str = "BY"): 
        """
        week_start: Montag der Zielwoche (YYYY-MM-DD)
        skip_holidays: Wenn True, werden Feiertage übersprungen
        country, subdiv: Für Feiertagsprüfung (z.B. DE, BY)
        """
        self.week_start = datetime.strptime(week_start, "%Y-%m-%d")
        self.appointment_type_id = appointment_type_id
        self.doctor_id = doctor_id
        self.room_id = room_id
        self.skip_holidays = skip_holidays
        self.export_directory = export_directory or r"P:/imports/cathlab/json_heydoc"
        self.country = country
        self.subdiv = subdiv
        self.holiday_set = set()
        if holidays:
            self.holiday_set = set(holidays.country_holidays(country, subdiv=subdiv, years=[self.week_start.year, self.week_start.year+1]))
        else:
            if skip_holidays:
                logging.warning("Feiertagsprüfung nicht möglich: Paket 'holidays' nicht installiert.")

    def get_weekdays(self):
        """
        Gibt eine Liste aller Wochentage (Mo-Fr) als datetime-Objekte zurück.
        """
        return [self.week_start + timedelta(days=i) for i in range(5)]

    def is_holiday(self, day):
        """
        Prüft, ob der Tag ein Feiertag ist (sofern holidays verfügbar).
        """
        if not self.skip_holidays:
            return False
        if holidays:
            return day in self.holiday_set
        return False

    def export_week(self):
        """
        Exportiert für jeden Werktag die Termine (außer Feiertage, falls aktiviert).
        Loggt Fehler und Fortschritt.
        """
        patient_cache = {}
        for day in self.get_weekdays():
            date_str = day.strftime("%Y-%m-%d")
            if self.skip_holidays and self.is_holiday(day):
                logging.info(f"{date_str} ist ein Feiertag. Wird übersprungen.")
                continue
            try:
                enricher = AppointmentPatientEnricher(
                    from_date=date_str,
                    to_date=date_str,
                    appointment_type_id=self.appointment_type_id,
                    doctor_id=self.doctor_id,
                    room_id=self.room_id,
                    patient_cache=patient_cache
                )
                enricher.fetch_appointments()
                enricher.enrich_with_patients()
                enricher.to_json(directory=self.export_directory)
                logging.info(f"Export erfolgreich für {date_str}")
            except Exception as e:
                logging.error(f"Fehler beim Export für {date_str}: {e}")
