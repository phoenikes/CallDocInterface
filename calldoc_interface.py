"""
CallDoc API Interface Modul

Diese Datei enthält die CallDocInterface-Klasse zur Abfrage der CallDoc API.
"""

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