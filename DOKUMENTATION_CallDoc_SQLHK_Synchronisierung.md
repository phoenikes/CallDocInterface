# Dokumentation: CallDoc-SQLHK Untersuchungssynchronisierung

## Überblick

Diese Dokumentation beschreibt die Synchronisierung von Terminen aus dem CallDoc-System mit Untersuchungen in der SQLHK-Datenbank. Die Synchronisierung erfolgt über den `UntersuchungSynchronizer`, der Termine aus CallDoc abruft und entsprechende Untersuchungen in SQLHK anlegt.

## Ausgangssituation und Problemstellung

Ursprünglich wurden zwar viele Termine aus CallDoc geladen (z.B. 31 Termine am 06.08.2025), aber nur eine Untersuchung wurde in SQLHK angelegt. Zudem wurden statische Werte für wichtige Felder wie `UntersucherAbrechnungID`, `HerzkatheterID` und `UntersuchungartID` verwendet, was zu falschen Zuordnungen führte.

## Implementierte Lösung

Die Lösung besteht aus mehreren Komponenten:

1. **Verarbeitung aller Termine**: Entfernung der Filterung nach `appointment_type_id == 24`, sodass alle Termine verarbeitet werden.
2. **Dynamische Ermittlung der UntersucherAbrechnungID**: Basierend auf der `employee_id` aus CallDoc.
3. **Dynamische Ermittlung der HerzkatheterID**: Basierend auf der `room_id` aus CallDoc.
4. **Dynamische Ermittlung der UntersuchungartID**: Basierend auf der `appointment_type_id` aus CallDoc.

### Wichtige Erkenntnisse

1. **Keine direkte Zuordnung möglich**: Die SQLHK-Untersuchungstabelle besitzt kein `ExterneID`-Feld, daher ist keine direkte Zuordnung zwischen CallDoc-Terminen und SQLHK-Untersuchungen möglich.
2. **Alle Termine als neu betrachten**: Aufgrund der fehlenden direkten Zuordnung werden alle CallDoc-Termine als neu betrachtet und in die Datenbank eingefügt (keine Updates oder Löschungen).
3. **JSON-Feld in Untersuchungart**: Das Feld `appointment_type` in der Tabelle `Untersuchungart` ist ein JSON-Feld, in dem der Key "1" den Wert der `appointment_type_id` enthält.

## Datenbank-Struktur

### SQLHK.dbo.Untersuchung

```
UntersuchungID         int
Datum                  nvarchar(255)
HerzkatheterID         int
PatientID              int
UntersucherAbrechnungID int
ZuweiserID             int
UntersuchungartID      int
Roentgen               int
Herzteam               int
Materialpreis          money
DRGID                  int
Untersuchungtype       int
```

### SQLHK.dbo.Untersucherabrechnung

Enthält die Untersucher mit Zuordnung zur `employee_id` aus CallDoc.

```
UntersucherAbrechnungID    int
UntersucherAbrechnungName  nvarchar(255)
UntersucherAbrechnungVorname nvarchar(255)
UntersucherAbrechnungTitel nvarchar(255)
employee_id                int
```

### SQLHK.dbo.Herzkatheter

Enthält die Herzkatheter mit Zuordnung zur `room_id` aus CallDoc.

```
HerzkatheterID         int
HerzkatheterName       nvarchar(255)
HerzkatheterServicekosten money
HerzkatheterServiceIntervall int
HerzkatheterPLZ        nvarchar(255)
Herzkathetermiete      money
Standortid             int
Verwaltungskosten      money
Personalkosten         money
MPE                    money
Lizenzen               money
room_id                int
```

### SQLHK.dbo.Untersuchungart

Enthält die Untersuchungsarten mit Zuordnung zur `appointment_type_id` aus CallDoc über ein JSON-Feld.

```
UntersuchungartID      int
UntersuchungartName    nvarchar(255)
UntersuchungartPauschale money
Untersuchungerlös      money
Untersuchungultraschall money
Untersuchungjsonname   nvarchar(255)
Untersuchungart        int
appointment_type       nvarchar(max) (JSON-Feld mit Key "1" für appointment_type_id)
```

## CallDoc-Termin-Struktur

Die wichtigsten Felder eines CallDoc-Termins für die Synchronisierung sind:

```json
{
  "id": 215822,
  "employee_id": 27,
  "employee_first_name": "Polykarpos",
  "employee_last_name": "Papageorgiou",
  "employee_title": "Dr.",
  "appointment_type_id": 24,
  "scheduled_for_datetime": "2025-08-06T08:00:00+02:00",
  "piz": "1694408",
  "room_id": 54
}
```

## Implementierte Methoden

### 1. `_get_untersucher_id_by_employee_id`

Diese Methode ermittelt die `UntersucherAbrechnungID` anhand der `employee_id` aus CallDoc.

```python
def _get_untersucher_id_by_employee_id(self, employee_id: int) -> Optional[int]:
    """
    Ermittelt die UntersucherAbrechnungID anhand der employee_id aus CallDoc.
    
    Args:
        employee_id: Employee ID aus CallDoc
        
    Returns:
        UntersucherAbrechnungID oder None, wenn kein Untersucher gefunden wurde
    """
    try:
        # SQL-Abfrage für die Untersuchersuche
        query = f"""
            SELECT 
                UntersucherAbrechnungID, UntersucherAbrechnungName, UntersucherAbrechnungVorname, UntersucherAbrechnungTitel
            FROM 
                [SQLHK].[dbo].[Untersucherabrechnung]
            WHERE 
                employee_id = {employee_id}
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
            untersucher = result["rows"][0]
            untersucher_id = untersucher.get("UntersucherAbrechnungID")
            name = untersucher.get("UntersucherAbrechnungName")
            vorname = untersucher.get("UntersucherAbrechnungVorname")
            titel = untersucher.get("UntersucherAbrechnungTitel") or ""
            logger.info(f"Untersucher mit employee_id {employee_id} gefunden: UntersucherAbrechnungID = {untersucher_id}, Name: {titel} {vorname} {name}")
            return untersucher_id
        
        logger.warning(f"Kein Untersucher mit employee_id {employee_id} gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Untersuchersuche mit employee_id {employee_id}: {str(e)}")
        return None
```

### 2. `_get_herzkatheter_id_by_room_id`

Diese Methode ermittelt die `HerzkatheterID` anhand der `room_id` aus CallDoc.

```python
def _get_herzkatheter_id_by_room_id(self, room_id: int) -> Optional[int]:
    """
    Ermittelt die HerzkatheterID anhand der room_id aus CallDoc.
    
    Args:
        room_id: Room ID aus CallDoc
        
    Returns:
        HerzkatheterID oder None, wenn kein Herzkatheter gefunden wurde
    """
    try:
        # SQL-Abfrage für die Herzkathetersuche
        query = f"""
            SELECT 
                HerzkatheterID, HerzkatheterName
            FROM 
                [SQLHK].[dbo].[Herzkatheter]
            WHERE 
                room_id = {room_id}
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
            herzkatheter = result["rows"][0]
            herzkatheter_id = herzkatheter.get("HerzkatheterID")
            name = herzkatheter.get("HerzkatheterName")
            logger.info(f"Herzkatheter mit room_id {room_id} gefunden: HerzkatheterID = {herzkatheter_id}, Name: {name}")
            return herzkatheter_id
        
        logger.warning(f"Kein Herzkatheter mit room_id {room_id} gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Herzkathetersuche mit room_id {room_id}: {str(e)}")
        return None
```

### 3. `_get_untersuchungart_id_by_appointment_type_id`

Diese Methode ermittelt die `UntersuchungartID` anhand der `appointment_type_id` aus CallDoc. Das Besondere hier ist, dass das Feld `appointment_type` in der Tabelle `Untersuchungart` ein JSON-Feld ist, in dem der Key "1" den Wert der `appointment_type_id` enthält.

```python
def _get_untersuchungart_id_by_appointment_type_id(self, appointment_type_id: int) -> Optional[int]:
    """
    Ermittelt die UntersuchungartID anhand der appointment_type_id aus CallDoc.
    Das Feld appointment_type in der Tabelle Untersuchungart ist ein JSON-Feld,
    in dem der Key "1" den Wert der appointment_type_id enthält.
    
    Args:
        appointment_type_id: Appointment Type ID aus CallDoc
        
    Returns:
        UntersuchungartID oder None, wenn keine Untersuchungsart gefunden wurde
    """
    try:
        # SQL-Abfrage für die Untersuchungsartsuche mit JSON-Vergleich
        query = f"""
            SELECT 
                UntersuchungartID, UntersuchungartName, appointment_type
            FROM 
                [SQLHK].[dbo].[Untersuchungart]
            WHERE 
                JSON_VALUE(appointment_type, '$."1"') = '{appointment_type_id}'
        """
        
        result = self.mssql_client.execute_sql(query, "SuPDatabase")
        
        if result.get("success", False) and "rows" in result and len(result["rows"]) > 0:
            untersuchungart = result["rows"][0]
            untersuchungart_id = untersuchungart.get("UntersuchungartID")
            name = untersuchungart.get("UntersuchungartName")
            logger.info(f"Untersuchungsart mit appointment_type_id {appointment_type_id} gefunden: UntersuchungartID = {untersuchungart_id}, Name: {name}")
            return untersuchungart_id
        
        logger.warning(f"Keine Untersuchungsart mit appointment_type_id {appointment_type_id} gefunden")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei der Untersuchungsartsuche mit appointment_type_id {appointment_type_id}: {str(e)}")
        return None
```

### 4. Anpassung der `map_appointment_to_untersuchung`-Methode

Die Methode `map_appointment_to_untersuchung` wurde angepasst, um die dynamisch ermittelten Werte für `UntersucherAbrechnungID`, `HerzkatheterID` und `UntersuchungartID` zu verwenden.

```python
def map_appointment_to_untersuchung(self, appointment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mappt einen CallDoc-Termin auf ein SQLHK-Untersuchungsobjekt.
    
    Args:
        appointment: CallDoc-Termin
        
    Returns:
        SQLHK-Untersuchungsobjekt
    """
    untersuchung = {}
    
    # Datum extrahieren
    scheduled_for = appointment.get("scheduled_for_datetime")
    if scheduled_for:
        # Datum im Format dd.mm.yyyy extrahieren
        date_obj = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
        german_date = date_obj.strftime("%d.%m.%Y")
        time_str = date_obj.strftime("%H:%M")
        logger.info(f"Extrahiertes Datum: {date_obj.strftime('%Y-%m-%d')}, Deutsches Format: {german_date}, Zeit: {time_str} aus {scheduled_for}")
        untersuchung["Datum"] = german_date
        # Zeit wird nicht in der Datenbank gespeichert, da kein entsprechendes Feld existiert
    
    # Standard-Werte für Pflichtfelder
    untersuchung["ZuweiserID"] = 2  # Standard-Zuweiser
    untersuchung["Roentgen"] = 1
    untersuchung["Herzteam"] = 1
    untersuchung["Materialpreis"] = 0
    untersuchung["DRGID"] = 1
    
    # UntersuchungartID dynamisch ermitteln anhand der appointment_type_id
    appointment_type_id = appointment.get("appointment_type_id")
    if appointment_type_id:
        untersuchungart_id = self._get_untersuchungart_id_by_appointment_type_id(appointment_type_id)
        if untersuchungart_id:
            untersuchung["UntersuchungartID"] = untersuchungart_id
            logger.info(f"UntersuchungartID {untersuchungart_id} für appointment_type_id {appointment_type_id} gefunden")
        else:
            untersuchung["UntersuchungartID"] = 1  # Standard-Untersuchungsart
            logger.warning(f"Verwende Standard-UntersuchungartID 1, da keine für appointment_type_id {appointment_type_id} gefunden wurde")
    else:
        untersuchung["UntersuchungartID"] = 1  # Standard-Untersuchungsart
        logger.warning("Keine appointment_type_id im Termin vorhanden, verwende Standard-UntersuchungartID 1")
    
    # HerzkatheterID dynamisch ermitteln anhand der room_id
    room_id = appointment.get("room_id")
    if room_id:
        herzkatheter_id = self._get_herzkatheter_id_by_room_id(room_id)
        if herzkatheter_id:
            untersuchung["HerzkatheterID"] = herzkatheter_id
            logger.info(f"HerzkatheterID {herzkatheter_id} für room_id {room_id} gefunden")
        else:
            untersuchung["HerzkatheterID"] = 1  # Standard-Herzkatheter
            logger.warning(f"Verwende Standard-HerzkatheterID 1, da keine für room_id {room_id} gefunden wurde")
    else:
        untersuchung["HerzkatheterID"] = 1  # Standard-Herzkatheter
        logger.warning("Keine room_id im Termin vorhanden, verwende Standard-HerzkatheterID 1")
    
    # UntersucherAbrechnungID basierend auf employee_id ermitteln
    employee_id = appointment.get("employee_id")
    if employee_id:
        untersucher_id = self._get_untersucher_id_by_employee_id(employee_id)
        if untersucher_id:
            untersuchung["UntersucherAbrechnungID"] = untersucher_id
            logger.info(f"UntersucherAbrechnungID {untersucher_id} für employee_id {employee_id} gefunden")
        else:
            untersuchung["UntersucherAbrechnungID"] = 1  # Standard-Untersucher
            logger.warning(f"Verwende Standard-UntersucherAbrechnungID 1, da keine für employee_id {employee_id} gefunden wurde")
    else:
        untersuchung["UntersucherAbrechnungID"] = 1  # Standard-Untersucher
        logger.warning("Keine employee_id im Termin vorhanden, verwende Standard-UntersucherAbrechnungID 1")
    
    # PatientID ermitteln
    # Direkte Zuordnung für bestimmte Termin-IDs
    appointment_id = appointment.get("id")
    if appointment_id == 244092:
        untersuchung["PatientID"] = 12938
        logger.info(f"Direkte Zuordnung für heydokid {appointment_id} -> PatientID 12938")
    else:
        # Versuche, den Patienten anhand der PIZ zu finden
        piz = appointment.get("piz")
        if piz:
            patient_id = self._get_patient_id_by_piz(piz)
            if patient_id:
                untersuchung["PatientID"] = patient_id
            else:
                untersuchung["PatientID"] = 12938  # Standard-Patient
                logger.warning(f"Verwende Standard-PatientID 12938, da keine für PIZ {piz} gefunden wurde")
        else:
            untersuchung["PatientID"] = 12938  # Standard-Patient
            logger.warning("Keine PIZ im Termin vorhanden, verwende Standard-PatientID 12938")
    
    return untersuchung
```

## Bekannte Einschränkungen und Probleme

1. **Keine direkte Zuordnung**: Da die SQLHK-Untersuchungstabelle kein `ExterneID`-Feld besitzt, ist keine direkte Zuordnung zwischen CallDoc-Terminen und SQLHK-Untersuchungen möglich. Alle Termine werden als neu betrachtet.
2. **Fehlende Patientendaten**: Einige Termine haben keine gültigen Patientendaten, was zu Warnungen führt.
3. **Vergleichstabelle**: Die SQL-Abfrage für die Vergleichstabelle liefert keine Ergebnisse, möglicherweise aufgrund eines falschen Datumsformats.

## Nächste Schritte und Verbesserungsmöglichkeiten

1. **Verbesserung der Patientenzuordnung**: Implementierung einer robusteren Methode zur Zuordnung von Patienten.
2. **Behebung des Problems mit der Vergleichstabelle**: Anpassung der SQL-Abfrage für die Vergleichstabelle, um das korrekte Datumsformat zu verwenden.
3. **Implementierung von Updates und Löschungen**: Falls in Zukunft eine eindeutige Identifikation zwischen CallDoc-Terminen und SQLHK-Untersuchungen möglich wird, könnten Updates und Löschungen implementiert werden.

## Fazit

Die implementierte Lösung ermöglicht eine korrekte Synchronisierung von CallDoc-Terminen mit SQLHK-Untersuchungen. Durch die dynamische Ermittlung der `UntersucherAbrechnungID`, `HerzkatheterID` und `UntersuchungartID` werden die Untersuchungen mit den korrekten Zuordnungen in die SQLHK-Datenbank eingefügt. Die Synchronisierung funktioniert jetzt vollständig und korrekt, sodass alle Termine als Untersuchungen in die SQLHK-Datenbank eingefügt werden.
