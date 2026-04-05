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

# SQLHK API URL
SQLHK_API_BASE_URL = "http://192.168.1.67:7007/api"

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
    "ABLATION": 25
}

# Konstanten für die Ärzte (CallDoc employee_id)
# Mapping zu SQLHK UntersucherAbrechnungID erfolgt über DB-Tabelle Untersucherabrechnung
DOCTORS = {
    # Praxis-Ärzte
    "SANDROCK": 18,           # SQLHK ID 1
    "DEUBNER": 19,            # SQLHK ID 7
    "WEICHSEL": 22,           # SQLHK ID 5
    "DUCKHEIM": 25,           # SQLHK ID 6
    "DOSCHAT": 26,            # SQLHK ID 20
    "PAPAGEORGIOU": 27,       # SQLHK ID 2
    "LINDEMANN": 28,          # SQLHK ID 23
    "ANGER": 30,              # SQLHK ID 11
    "BLAZEK": 31,             # SQLHK ID 24
    "STEPHAN": 32,            # SQLHK ID 16
    "REGENFUS": 33,           # SQLHK ID 21
    "KNOPP": 34,              # SQLHK ID 4
    "BÖTZL": 36,              # SQLHK ID 3
    "MEKKALA": 38,            # SQLHK ID 14
    "PANNU": 49,              # SQLHK ID 13
    "KOCH": 50,               # SQLHK ID 12
    "STIEFEL": 51,            # SQLHK ID 17
    "SCHÄFFER": 52,           # SQLHK ID 19
    "TILLMANNS": 56,          # SQLHK ID 22
    "GREINWALD": 57,          # SQLHK ID 28
    "GÖTZ": 66,               # SQLHK ID 15
    "NEUMANN": 81,            # SQLHK ID 25
    # Neue Ärzte (2026)
    "POESCH": 10081,          # SQLHK ID 30
    "VUKANINOVIC": 10082,     # SQLHK ID 29
    "PLATSCHEK": 10091,       # SQLHK ID 31
    "MOHAMMED": 10097,        # SQLHK ID 32
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
    "HERZKATHETER_3": 54,   
    "HERZKATHETER_4": 61,
    "FUNKTION_1": 20,
    "FUNKTION_2": 21,
    "SPRECHZIMMER_1": 22
}
