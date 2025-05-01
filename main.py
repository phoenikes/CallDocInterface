import requests
import json
from constants import (
    PATIENT_SEARCH_URL, 
    APPOINTMENT_SEARCH_URL, 
    APPOINTMENT_TYPES, 
    DOCTORS, 
    ROOMS
)


class CallDocInterface:
    """
    Klasse zur Abfrage der CallDoc API-Schnittstellen für Patienten- und Terminsuche.
    """
    
    def __init__(self, from_date, to_date, **kwargs):
        """
        Initialisiert die CallDocInterface-Klasse mit den erforderlichen Parametern.
        
        Args:
            from_date (str): Startdatum im Format 'YYYY-MM-DD'
            to_date (str): Enddatum im Format 'YYYY-MM-DD'
            **kwargs: Optionale Parameter für die API-Abfragen
        """
        # Pflichtparameter
        self.from_date = from_date
        self.to_date = to_date
        
        # Optionale Parameter
        self.optional_params = kwargs
    
    def patient_search(self, **additional_params):
        """
        Führt eine Patientensuche durch.
        
        Args:
            **additional_params: Zusätzliche Parameter für diese spezifische Abfrage
            
        Returns:
            dict: JSON-Antwort der API
        """
        # Parameter zusammenstellen
        params = {
            "from_date": self.from_date,
            "to_date": self.to_date,
            **self.optional_params,
            **additional_params
        }
        
        # API-Abfrage durchführen
        return self._make_api_request(PATIENT_SEARCH_URL, params)
    
    def appointment_search(self, **additional_params):
        """
        Führt eine Terminsuche durch.
        
        Args:
            **additional_params: Zusätzliche Parameter für diese spezifische Abfrage
            
        Returns:
            dict: JSON-Antwort der API
        """
        # Parameter zusammenstellen
        params = {
            "from_date": self.from_date,
            "to_date": self.to_date,
            **self.optional_params,
            **additional_params
        }
        
        # API-Abfrage durchführen
        return self._make_api_request(APPOINTMENT_SEARCH_URL, params)
    
    def get_patient_by_piz(self, piz):
        """
        Ruft Patientendaten anhand der PIZ-Nummer über die Patienten-API ab.
        Args:
            piz (str|int): Patienten-Identifikationsnummer
        Returns:
            dict: JSON-Antwort der API oder Fehlermeldung
        """
        url = "http://192.168.1.76:3000/patients/search"
        headers = {"Content-Type": "application/json"}
        data = {"piz": str(piz)}
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except requests.RequestException as e:
            return {
                "error": True,
                "message": str(e)
            }
    
    def _make_api_request(self, url, params):
        """
        Führt die API-Anfrage durch und gibt das Ergebnis zurück.
        
        Args:
            url (str): Die URL der API
            params (dict): Die Parameter für die Anfrage
            
        Returns:
            dict: JSON-Antwort der API oder Fehlermeldung
        """
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except requests.RequestException as e:
            return {
                "error": True,
                "message": str(e)
            }


def print_formatted_json(data):
    """Hilfsfunktion zur formatierten Ausgabe von JSON-Daten"""
    print(json.dumps(data, indent=4, ensure_ascii=False))


def enrich_appointments_with_patients(from_date, to_date, appointment_type_id=24, output_path=None):
    """Sucht Termine und ergänzt Patientendaten direkt, optional Speicherung als JSON."""
    interface = CallDocInterface(from_date=from_date, to_date=to_date)
    result = interface.appointment_search(appointment_type_id=appointment_type_id)
    piz_set = set()
    for appt in result.get("data", []):
        piz = appt.get("piz")
        if piz and piz not in piz_set:
            patient_data = interface.get_patient_by_piz(piz)
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
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"Ergebnis wurde nach {output_path} geschrieben.")
    return result


if __name__ == "__main__":
    # Export für alle Werktage der nächsten Woche (appointment_type_id=24)
    from weekly_appointment_exporter import WeeklyAppointmentExporter
    import datetime
    today = datetime.date.today()
    next_week = today.isocalendar().week + 1
    year = today.year
    exporter = WeeklyAppointmentExporter(
        year=year,
        week=next_week,
        appointment_type_id=24
    )
    exporter.export_week()

    # Export für alle Werktage der übernächsten Woche (appointment_type_id=24)
    # Prüfe auf Jahreswechsel
    import calendar
    weeks_in_year = datetime.date(year, 12, 28).isocalendar().week
    week_after_next = next_week + 1
    year2 = year
    if week_after_next > weeks_in_year:
        week_after_next = 1
        year2 = year + 1
    exporter2 = WeeklyAppointmentExporter(
        year=year2,
        week=week_after_next,
        appointment_type_id=24
    )
    exporter2.export_week()
