import datetime
from appointment_patient_enricher import AppointmentPatientEnricher
from typing import List, Optional

class WeeklyAppointmentExporter:
    """
    Exportiert für eine Kalenderwoche (Mo-Fr, optional ohne Feiertage) für einen bestimmten appointment_type_id
die angereicherten Termine als JSON (je Tag eine Datei), nutzt AppointmentPatientEnricher.
    """
    def __init__(self, year: int, week: int, appointment_type_id: int, doctor_id: Optional[int] = None, room_id: Optional[int] = None, skip_holidays: bool = False, holidays: Optional[List[datetime.date]] = None):
        self.year = year
        self.week = week
        self.appointment_type_id = appointment_type_id
        self.doctor_id = doctor_id
        self.room_id = room_id
        self.skip_holidays = skip_holidays
        self.holidays = holidays or []

    def get_weekdays(self) -> List[datetime.date]:
        # Liefert Montag-Freitag der Kalenderwoche
        days = []
        for weekday in range(1, 6):  # 1=Montag, 5=Freitag
            day = datetime.date.fromisocalendar(self.year, self.week, weekday)
            days.append(day)
        return days

    def is_holiday(self, day: datetime.date) -> bool:
        return day in self.holidays

    def export_week(self):
        for day in self.get_weekdays():
            if self.skip_holidays and self.is_holiday(day):
                print(f"{day} ist Feiertag – übersprungen.")
                continue
            date_str = day.strftime("%Y-%m-%d")
            enricher = AppointmentPatientEnricher(
                from_date=date_str,
                to_date=date_str,
                appointment_type_id=self.appointment_type_id,
                doctor_id=self.doctor_id,
                room_id=self.room_id
            )
            enricher.fetch_appointments()
            enricher.enrich_with_patients()
            enricher.to_json()
            print(f"Export für {date_str} abgeschlossen.")

    @staticmethod
    def get_german_public_holidays(year: int) -> List[datetime.date]:
        # Optional: Feiertagsberechnung mit 'holidays'-Paket
        try:
            import holidays
            de_holidays = holidays.country_holidays('DE', years=year, subdiv='BY')
            return [d for d in de_holidays.keys()]
        except ImportError:
            print("Modul 'holidays' nicht installiert – Feiertage werden nicht berücksichtigt.")
            return []
