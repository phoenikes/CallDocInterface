"""
Skript zum Überprüfen der Patientenstruktur in CallDoc und SQLHK.
"""
import json
import requests
from constants import API_BASE_URL, SQLHK_API_BASE_URL
from calldoc_interface import CallDocInterface
from datetime import datetime

def get_calldoc_patient_structure():
    """Ruft die Struktur eines CallDoc-Patienten ab."""
    print("Suche nach CallDoc-Patienten...")
    
    # Versuche, einen Patienten über die Suche zu finden
    interface = CallDocInterface(
        from_date=datetime.now().strftime('%Y-%m-%d'),
        to_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    # Suche nach einem beliebigen Patienten
    search_result = requests.get(f"{API_BASE_URL}/patient_search/?search=a")
    search_data = search_result.json()
    
    if search_data and "patients" in search_data and search_data["patients"]:
        patient = search_data["patients"][0]
        print("\nPatient-Struktur in CallDoc:")
        print(json.dumps(patient, indent=2, ensure_ascii=False))
        return patient
    else:
        print("Keine Patienten in CallDoc gefunden.")
        return None

def get_sqlhk_patient_structure():
    """Ruft die Struktur eines SQLHK-Patienten ab."""
    print("\nSuche nach SQLHK-Patienten...")
    
    try:
        # Versuche, einen Patienten über die API zu finden
        response = requests.get(f"{SQLHK_API_BASE_URL}/patient/schema")
        
        if response.status_code == 200:
            schema = response.json()
            print("\nPatient-Schema in SQLHK:")
            print(json.dumps(schema, indent=2, ensure_ascii=False))
            return schema
        else:
            print(f"Fehler beim Abrufen des SQLHK-Schemas: {response.status_code}")
            
            # Versuche, einen konkreten Patienten zu finden
            patients_response = requests.get(f"{SQLHK_API_BASE_URL}/patient")
            
            if patients_response.status_code == 200:
                patients = patients_response.json()
                if patients and len(patients) > 0:
                    patient = patients[0]
                    print("\nBeispiel-Patient in SQLHK:")
                    print(json.dumps(patient, indent=2, ensure_ascii=False))
                    return patient
                else:
                    print("Keine Patienten in SQLHK gefunden.")
            else:
                print(f"Fehler beim Abrufen der SQLHK-Patienten: {patients_response.status_code}")
    
    except Exception as e:
        print(f"Fehler beim Zugriff auf die SQLHK-API: {str(e)}")
    
    return None

def get_sqlhk_tables():
    """Ruft die verfügbaren Tabellen in SQLHK ab."""
    print("\nVerfügbare Tabellen in SQLHK:")
    
    try:
        response = requests.get(f"{SQLHK_API_BASE_URL}/tables")
        
        if response.status_code == 200:
            tables = response.json()
            print(json.dumps(tables, indent=2, ensure_ascii=False))
            return tables
        else:
            print(f"Fehler beim Abrufen der SQLHK-Tabellen: {response.status_code}")
    
    except Exception as e:
        print(f"Fehler beim Zugriff auf die SQLHK-API: {str(e)}")
    
    return None

def main():
    """Hauptfunktion."""
    print("Überprüfe Patientenstruktur in CallDoc und SQLHK...\n")
    
    # CallDoc-Patientenstruktur abrufen
    calldoc_patient = get_calldoc_patient_structure()
    
    # SQLHK-Tabellen abrufen
    sqlhk_tables = get_sqlhk_tables()
    
    # SQLHK-Patientenstruktur abrufen
    sqlhk_patient = get_sqlhk_patient_structure()
    
    # Mapping vorschlagen
    if calldoc_patient and sqlhk_patient:
        print("\n\nVorschlag für Feld-Mapping zwischen CallDoc und SQLHK:")
        print("=" * 80)
        print(f"{'CallDoc-Feld':<30} | {'SQLHK-Feld':<30} | {'Bemerkung':<20}")
        print("-" * 80)
        
        # Hier könnten wir ein automatisches Mapping basierend auf Feldnamen vorschlagen
        # Dies ist jedoch nur ein Beispiel und muss manuell überprüft werden
        calldoc_fields = calldoc_patient.keys()
        sqlhk_fields = sqlhk_patient.keys() if isinstance(sqlhk_patient, dict) else []
        
        # Einfaches Mapping basierend auf ähnlichen Feldnamen
        mappings = [
            ("id", "PatientID", "Primärschlüssel"),
            ("surname", "Nachname", ""),
            ("name", "Vorname", ""),
            ("date_of_birth", "Geburtsdatum", "Format beachten"),
            ("gender", "Geschlecht", "Werte konvertieren"),
            ("street", "Strasse", ""),
            ("zip", "PLZ", ""),
            ("city", "Ort", ""),
            ("phone", "Telefon", ""),
            ("mobile", "Mobil", ""),
            ("email", "Email", ""),
            ("insurance", "Versicherung", ""),
            ("insurance_number", "VersicherungsNr", "")
        ]
        
        for calldoc_field, sqlhk_field, comment in mappings:
            in_calldoc = calldoc_field in calldoc_fields
            in_sqlhk = sqlhk_field in sqlhk_fields
            status = ""
            
            if in_calldoc and in_sqlhk:
                status = "✓"
            elif in_calldoc:
                status = "Nur in CallDoc"
            elif in_sqlhk:
                status = "Nur in SQLHK"
            else:
                status = "Nicht gefunden"
            
            print(f"{calldoc_field:<30} | {sqlhk_field:<30} | {status:<20}")
        
        print("=" * 80)
        print("Hinweis: Dieses Mapping ist ein Vorschlag und muss manuell überprüft werden.")

if __name__ == "__main__":
    main()
