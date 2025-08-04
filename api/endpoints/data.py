#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Daten-Endpunkte für die CallDoc-SQLHK Synchronisierungs-API

Diese Datei enthält die API-Endpunkte für den Zugriff auf CallDoc-Termine
und SQLHK-Untersuchungen.

Autor: Markus
Datum: 03.08.2025
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from ..models import AppointmentListResponse, ExaminationListResponse
from ..dependencies import verify_api_key, get_config_manager

router = APIRouter(tags=["Daten"])

@router.get("/appointments", response_model=AppointmentListResponse, dependencies=[Depends(verify_api_key)])
async def get_appointments(
    date: str = Query(..., description="Datum im Format YYYY-MM-DD"),
    appointment_type_id: Optional[int] = Query(None, description="ID des Termintyps"),
    config_manager=Depends(get_config_manager)
):
    """
    Gibt die CallDoc-Termine für das angegebene Datum zurück.
    
    Args:
        date: Datum im Format YYYY-MM-DD
        appointment_type_id: Optional, ID des Termintyps
    
    Returns:
        AppointmentListResponse-Objekt mit den gefundenen Terminen
    """
    try:
        # Hier würde die tatsächliche Implementierung die Termine aus CallDoc abrufen
        # Dies ist ein Platzhalter für die tatsächliche Implementierung
        
        # In einer realen Implementierung würden wir hier die bestehende CallDocInterface verwenden
        # und die Ergebnisse zurückgeben
        
        # Beispielergebnis (in der realen Implementierung würden hier die tatsächlichen Termine stehen)
        appointments = [
            {
                "id": 1,
                "patient_id": 12345,
                "patient_name": "Mustermann, Max",
                "scheduled_for": datetime.fromisoformat(f"{date}T09:00:00"),
                "appointment_type": "Herzkatheteruntersuchung",
                "appointment_type_id": 24,
                "status": "confirmed",
                "doctor_name": "Dr. Schmidt",
                "room_name": "HKL 1"
            },
            {
                "id": 2,
                "patient_id": 67890,
                "patient_name": "Musterfrau, Maria",
                "scheduled_for": datetime.fromisoformat(f"{date}T10:30:00"),
                "appointment_type": "Herzkatheteruntersuchung",
                "appointment_type_id": 24,
                "status": "confirmed",
                "doctor_name": "Dr. Müller",
                "room_name": "HKL 2"
            }
        ]
        
        # Wenn ein Termintyp angegeben wurde, filtern wir die Termine
        if appointment_type_id:
            appointments = [a for a in appointments if a["appointment_type_id"] == appointment_type_id]
        
        return {
            "count": len(appointments),
            "date": date,
            "appointments": appointments
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Termine: {str(e)}"
        )

@router.get("/examinations", response_model=ExaminationListResponse, dependencies=[Depends(verify_api_key)])
async def get_examinations(
    date: str = Query(..., description="Datum im Format YYYY-MM-DD"),
    examination_type_id: Optional[int] = Query(None, description="ID des Untersuchungstyps"),
    config_manager=Depends(get_config_manager)
):
    """
    Gibt die SQLHK-Untersuchungen für das angegebene Datum zurück.
    
    Args:
        date: Datum im Format YYYY-MM-DD
        examination_type_id: Optional, ID des Untersuchungstyps
    
    Returns:
        ExaminationListResponse-Objekt mit den gefundenen Untersuchungen
    """
    try:
        # Hier würde die tatsächliche Implementierung die Untersuchungen aus SQLHK abrufen
        # Dies ist ein Platzhalter für die tatsächliche Implementierung
        
        # In einer realen Implementierung würden wir hier die bestehende SQLHK-Schnittstelle verwenden
        # und die Ergebnisse zurückgeben
        
        # Beispielergebnis (in der realen Implementierung würden hier die tatsächlichen Untersuchungen stehen)
        examinations = [
            {
                "id": 1,
                "patient_id": 12345,
                "patient_name": "Mustermann, Max",
                "examination_date": datetime.fromisoformat(f"{date}T09:00:00"),
                "examination_type": "Herzkatheteruntersuchung",
                "examination_type_id": 24,
                "status": "scheduled",
                "doctor_name": "Dr. Schmidt",
                "room_name": "HKL 1"
            },
            {
                "id": 2,
                "patient_id": 67890,
                "patient_name": "Musterfrau, Maria",
                "examination_date": datetime.fromisoformat(f"{date}T10:30:00"),
                "examination_type": "Herzkatheteruntersuchung",
                "examination_type_id": 24,
                "status": "scheduled",
                "doctor_name": "Dr. Müller",
                "room_name": "HKL 2"
            }
        ]
        
        # Wenn ein Untersuchungstyp angegeben wurde, filtern wir die Untersuchungen
        if examination_type_id:
            examinations = [e for e in examinations if e["examination_type_id"] == examination_type_id]
        
        return {
            "count": len(examinations),
            "date": date,
            "examinations": examinations
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Untersuchungen: {str(e)}"
        )

@router.get("/appointments/{appointment_id}", dependencies=[Depends(verify_api_key)])
async def get_appointment(appointment_id: int):
    """
    Gibt einen einzelnen CallDoc-Termin zurück.
    
    Args:
        appointment_id: ID des Termins
    
    Returns:
        Der gefundene Termin oder 404, wenn nicht gefunden
    """
    # Hier würde die tatsächliche Implementierung den Termin aus CallDoc abrufen
    # Dies ist ein Platzhalter für die tatsächliche Implementierung
    
    # Beispielergebnis (in der realen Implementierung würde hier der tatsächliche Termin stehen)
    if appointment_id == 1:
        return {
            "id": 1,
            "patient_id": 12345,
            "patient_name": "Mustermann, Max",
            "scheduled_for": datetime.fromisoformat("2025-08-03T09:00:00"),
            "appointment_type": "Herzkatheteruntersuchung",
            "appointment_type_id": 24,
            "status": "confirmed",
            "doctor_name": "Dr. Schmidt",
            "room_name": "HKL 1"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Termin mit ID {appointment_id} nicht gefunden"
    )

@router.get("/examinations/{examination_id}", dependencies=[Depends(verify_api_key)])
async def get_examination(examination_id: int):
    """
    Gibt eine einzelne SQLHK-Untersuchung zurück.
    
    Args:
        examination_id: ID der Untersuchung
    
    Returns:
        Die gefundene Untersuchung oder 404, wenn nicht gefunden
    """
    # Hier würde die tatsächliche Implementierung die Untersuchung aus SQLHK abrufen
    # Dies ist ein Platzhalter für die tatsächliche Implementierung
    
    # Beispielergebnis (in der realen Implementierung würde hier die tatsächliche Untersuchung stehen)
    if examination_id == 1:
        return {
            "id": 1,
            "patient_id": 12345,
            "patient_name": "Mustermann, Max",
            "examination_date": datetime.fromisoformat("2025-08-03T09:00:00"),
            "examination_type": "Herzkatheteruntersuchung",
            "examination_type_id": 24,
            "status": "scheduled",
            "doctor_name": "Dr. Schmidt",
            "room_name": "HKL 1"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Untersuchung mit ID {examination_id} nicht gefunden"
    )
