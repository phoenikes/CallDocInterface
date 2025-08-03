# -*- coding: utf-8 -*-

"""
Mapping zwischen CallDoc-Terminen und SQLHK-Untersuchungen

Dieses Modul stellt Funktionen und Konstanten bereit, um CallDoc-Termine in SQLHK-Untersuchungen umzuwandeln.

Autor: Markus
Datum: 03.08.2025
"""

# Konstanten für die Appointment-Typen mit lesbaren Namen
APPOINTMENT_TYPES = {
    "SPRECHSTUNDE_KARDIOLOGIE": 1,
    "SPRECHSTUNDE_PULMOLOGIE": 4,
    "STRESSECHO": 2,
    "BODY": 7,
    "NOTFALL": 43,
    "HERZULTRASCHALL": 13,
    "LANGZEIT_EKG_ANLEGEN": 5,
    "HERZKATHETER_NACHGESPRÄCH": 12,
    "HERZKATHETERUNTERSUCHUNG": 24,
    "KONTROLLE_WERTE": 91,
    "HERZKATHETER_VORGESPRÄCH": 11,
    "OSA_BESPRECHUNG": 17,
    "LANGZEIT_EKG_ABNEHMEN": 20,
    "DMP_DIABETES": 59,
    "OSA": 47,
    "OSA_ANLEGEN": 15,
    "KARDIOLOGISCHE_UNTERSUCHUNG": 22,
    "LANGZEIT_BLUTDRUCK_ANLEGEN": 6,
    "BLUTENTNAHME": 48,
    "LABORKONTROLLE": 23,
    "HAUSARZTGESPRÄCH_20MIN": 61,
    "AKUTTERMIN": 34,
    "SPRECHSTUNDE_INNERE": 10082,
    "LANGZEIT_BLUTDRUCK_ABNEHMEN": 21,
    "NACHGESPRÄCH_SCHLAFLABOR": 51,
    "SPRECHSTUNDE_RHYTHMOLOGIE": 27,
    "PROVOKATIONSTEST": 18,
    "LANGZEIT_EKG": 45,
    "DIABETOLOGIE_BERATUNG": 82,
    "DIABETOLOGIE_GESPRÄCH": 83,
    "LANGZEIT_EKG_GESPRÄCH": 39,
    "SCHLAFLABOR": 63,
    "VIDEOSPRECHSTUNDE": 19,
    "TEE": 26,
    "BODY_+_DIFF": 36,
    "DMP_PULMO": 66,
    "SCHRITTMACHERKONTROLLE": 44,
    "BODY_+_BGA": 8,
    "ALLERGIETEST": 64,
    "DIABETOLOGIE_NEUPATIENT": 92,
    "KARDIOVERSION_UND_TEE": 29,
    "BEFUNDBESPRECHUNG": 88,
    "FUSS": 84,
    "LANGZEIT_RR_GESPRÄCH": 40,
    "COROLABOR": 74,
    "SONO_CAROTIS": 33,
    "ABLATION": 25,
    "LANGZEIT_BLUTDRUCK": 46,
    "SONO_SD": 69,
    "BODY_+_ACT": 9,
    "DMP_SPRECHSTUNDE": 68,
    "TEE_VORGESPRÄCH": 30,
    "MASKENSPRECHSTUNDE": 67,
    "SONO_ARTERIE": 32,
    "SPIROERGO": 49,
    "TEE_NACHGESPRÄCH": 31,
    "OSA_ABNEHMEN": 16,
    "BGA": 52,
    "QUICKKONTROLLE": 77,
    "OGTT": 87,
    "ABDOMEN": 54,
    "EKG": 35,
    "IMPFUNG_STANDARD": 76,
    "VERBAND": 71,
    "KARDIOVERSION": 28,
    "TTE": 53,
}


def map_appointment_to_untersuchung(appointment):
    """
    Wandelt einen CallDoc-Termin in ein SQLHK-Untersuchungsobjekt um.
    
    Args:
        appointment (dict): Ein CallDoc-Termin als Dictionary
        
    Returns:
        dict: Ein SQLHK-Untersuchungsobjekt mit den entsprechenden Feldern
    """
    # Extrahiere relevante Daten aus dem Termin
    patient_id = appointment.get('patient_id')
    appointment_id = appointment.get('id')
    appointment_type_id = appointment.get('appointment_type_id')
    scheduled_for = appointment.get('scheduled_for_datetime')
    doctor_id = appointment.get('doctor_id')
    room_id = appointment.get('room_id')
    notes = appointment.get('notes', '')
    
    # Erstelle das Untersuchungsobjekt
    untersuchung = {
        'PatientID': patient_id,
        'CallDocAppointmentID': appointment_id,
        'UntersuchungsTypID': appointment_type_id,  # Direkte Übernahme der ID
        'Datum': scheduled_for.split('T')[0] if scheduled_for else None,  # Nur das Datum extrahieren
        'Uhrzeit': scheduled_for.split('T')[1][:5] if scheduled_for else None,  # Nur die Uhrzeit (HH:MM) extrahieren
        'ArztID': doctor_id,
        'RaumID': room_id,
        'Notizen': notes,
        'Status': 'Geplant'  # Standardstatus für neue Untersuchungen
    }
    
    return untersuchung
