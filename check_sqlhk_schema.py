"""
Skript zum Überprüfen der SQLHK-Datenbankstruktur und Erstellen eines Mappings zwischen CallDoc und SQLHK.
"""
import json
import requests
from constants import SQLHK_API_BASE_URL

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

def get_sqlhk_table_schema(table_name):
    """Ruft das Schema einer SQLHK-Tabelle ab."""
    print(f"\nSchema der Tabelle '{table_name}':")
    
    try:
        response = requests.get(f"{SQLHK_API_BASE_URL}/table/{table_name}/schema")
        
        if response.status_code == 200:
            schema = response.json()
            print(json.dumps(schema, indent=2, ensure_ascii=False))
            return schema
        else:
            print(f"Fehler beim Abrufen des Schemas für {table_name}: {response.status_code}")
    
    except Exception as e:
        print(f"Fehler beim Zugriff auf die SQLHK-API: {str(e)}")
    
    return None

def get_sqlhk_patient_example():
    """Ruft ein Beispiel eines SQLHK-Patienten ab."""
    print("\nBeispiel eines SQLHK-Patienten:")
    
    try:
        # Versuche, einen Patienten über die API zu finden
        response = requests.get(f"{SQLHK_API_BASE_URL}/patient")
        
        if response.status_code == 200:
            patients = response.json()
            if patients and len(patients) > 0:
                patient = patients[0]
                print(json.dumps(patient, indent=2, ensure_ascii=False))
                return patient
            else:
                print("Keine Patienten in SQLHK gefunden.")
        else:
            print(f"Fehler beim Abrufen der SQLHK-Patienten: {response.status_code}")
    
    except Exception as e:
        print(f"Fehler beim Zugriff auf die SQLHK-API: {str(e)}")
    
    return None

def create_mapping():
    """Erstellt ein Mapping zwischen CallDoc und SQLHK-Patientenfeldern."""
    # CallDoc-Felder basierend auf dem Beispiel
    calldoc_fields = [
        "id", "piz", "name", "surname", "first_name", "last_name", 
        "date_of_birth", "gender", "city_code", "email", "phone_number",
        "insurance_provider", "insurance_number", "insured_type",
        "billing_vknr", "cost_bearer_id", "emails", "phones"
    ]
    
    # SQLHK-Felder (müssen aus dem Schema abgerufen werden)
    sqlhk_schema = get_sqlhk_table_schema("Patient")
    sqlhk_fields = []
    
    if sqlhk_schema:
        for column in sqlhk_schema:
            sqlhk_fields.append(column["name"])
    
    # Mapping erstellen
    print("\n\nVorschlag für Feld-Mapping zwischen CallDoc und SQLHK:")
    print("=" * 80)
    print(f"{'CallDoc-Feld':<30} | {'SQLHK-Feld':<30} | {'Bemerkung':<20}")
    print("-" * 80)
    
    # Vordefiniertes Mapping basierend auf Feldnamen
    mappings = [
        ("id", "PatientID", "Primärschlüssel"),
        ("piz", "PatientID", "PIZ als Primärschlüssel"),
        ("surname", "Nachname", ""),
        ("last_name", "Nachname", "Alternative zu surname"),
        ("name", "Vorname", ""),
        ("first_name", "Vorname", "Alternative zu name"),
        ("date_of_birth", "Geburtsdatum", "Format beachten"),
        ("gender", "Geschlecht", "Werte konvertieren"),
        ("city_code", "PLZ", ""),
        ("email", "Email", ""),
        ("phone_number", "Telefon", ""),
        ("insurance_provider", "Versicherung", ""),
        ("insurance_number", "VersicherungsNr", ""),
        ("insured_type", "VersichertenStatus", ""),
        ("billing_vknr", "VKNR", ""),
        ("cost_bearer_id", "KostentraegerID", "")
    ]
    
    for calldoc_field, sqlhk_field, comment in mappings:
        in_calldoc = calldoc_field in calldoc_fields
        in_sqlhk = sqlhk_field in sqlhk_fields if sqlhk_fields else False
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

def main():
    """Hauptfunktion."""
    print("Überprüfe SQLHK-Datenbankstruktur und erstelle Mapping...\n")
    
    # SQLHK-Tabellen abrufen
    tables = get_sqlhk_tables()
    
    # Schema der Patiententabelle abrufen
    patient_schema = get_sqlhk_table_schema("Patient")
    
    # Beispiel eines SQLHK-Patienten abrufen
    patient_example = get_sqlhk_patient_example()
    
    # Mapping erstellen
    create_mapping()

if __name__ == "__main__":
    main()
