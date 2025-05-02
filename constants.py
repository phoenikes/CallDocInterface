"""
Konstanten und zentrale Einstellungen für die CallDoc-Schnittstelle und Export-Logik.

Dieses Modul enthält:
- Die zentralen API-URLs für Patientensuche und Terminsuche
- Die Zuordnung von sprechenden Namen zu Appointment-Typ-IDs
- (Erweiterbar: Konstanten für Ärzte, Räume etc.)

Verwendung:
- Die Konstanten werden in der gesamten Anwendung verwendet, um konsistente und wartbare Filter und API-Aufrufe zu ermöglichen.
- Änderungen an den IDs oder neuen Typen werden zentral gepflegt.

API-Basis-URL:
- Die Basis-URL verweist auf das Backend des CallDoc-Systems.

Appointment-Typen:
- Die Zuordnung APPOINTMENT_TYPES ermöglicht es, sprechende Namen im Code zu verwenden und so die Lesbarkeit zu erhöhen.
- Beispiel: APPOINTMENT_TYPES["HERZKATHETERUNTERSUCHUNG"] ergibt 24

Erweiterung:
- Für Ärzte, Räume etc. können weitere Dictionaries analog gepflegt werden.
"""

# API URLs
API_BASE_URL = "http://192.168.1.76:8001/api/v1/frontend"
PATIENT_SEARCH_URL = f"{API_BASE_URL}/patient_search/"
APPOINTMENT_SEARCH_URL = f"{API_BASE_URL}/appointment_search/"

# Konstanten für die Appointment-Typen mit lesbaren Namen
APPOINTMENT_TYPES = {
    "SPRECHSTUNDE_KARDIOLOGIE": 1,
    "STRESSECHO": 2,
    "SPRECHSTUNDE_PULMOLOGIE": 4,
    "LANGZEIT_EKG_ANLEGEN": 5,
    "LANGZEIT_BLUTDRUCK_ANLEGEN": 6,
    "BODY": 7,
    "BODY_BGA": 8,
    "BODY_ACT": 9,
    "HERZKATHETER_VORGESPRÄCH": 11,
    "HERZKATHETER_NACHGESPRÄCH": 12,
    "HERZULTRASCHALL": 13,
    "LZ_EKG_BLOCKER": 14,
    "OSA_ANLEGEN": 15,
    "OSA_ABNEHMEN": 16,
    "OSA_BESPRECHUNG": 17,
    "PROVOKATIONSTEST": 18,
    "VIDEOSPRECHSTUNDE": 19,
    "LANGZEIT_EKG_ABNEHMEN": 20,
    "LANGZEIT_BLUTDRUCK_ABNEHMEN": 21,
    "KARDIOLOGISCHE_UNTERSUCHUNG": 22,
    "LABORKONTROLLE": 23,
    "HERZKATHETERUNTERSUCHUNG": 24,
    "HERZKATHETER RUMMELSBERG": 25
}

# Konstanten für die Ärzte
DOCTORS = {
    "SANDROCK": 18,
    "DEUBNER": 19,
    "GASPLMAYR": 20,
    "KLOPF": 21,
    "WEICHSEL": 22,
    "GAWEHN": 24,
    "DUCKHEIM": 25,
    "DOSCHAT": 26,
    "PAPAGEORGIOU": 27,
    "LINDEMANN": 28,
    "NEUMANN": 29,
    "ANGER": 30,
    "BLASZEK": 31,
    "STEFAN": 32,
    "REGENFUS": 33
}

# Konstanten für Räume
ROOMS = {
    "LZ_EKG_RR_OSA": 4,
    "SPRECHZIMMER_KARDIO_1": 5,
    "FUNKTION_1_STRESSECHO_1": 6,
    "SPRECHZIMMER_4": 7,
    "SPRECHZIMMER_KARDIO_2": 8,
    "FUNKTION_2_STRESSECHO_2": 9,
    "BODY": 10,
    "SPRECHZIMMER_PULMO": 11,
    "OSA": 12,
    "LABOR": 17,
    "HERZKATHETER_1": 18,
    "HERZKATHETER_2": 19,
    "FUNKTION_1": 20,
    "FUNKTION_2": 21,
    "SPRECHZIMMER_1": 22
}
