#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API-Modelle für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält die Pydantic-Modelle für die API-Anfragen und -Antworten
der CallDoc-SQLHK Synchronisierungs-API.

Autor: Markus
Datum: 03.08.2025
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class HealthResponse(BaseModel):
    """Antwortmodell für den Gesundheitsstatus der API."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    calldoc_connected: Optional[bool] = None
    sqlhk_connected: Optional[bool] = None

class ConnectionStatusResponse(BaseModel):
    """Antwortmodell für den Verbindungsstatus."""
    calldoc_connected: bool
    sqlhk_connected: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = {}

class SyncRequest(BaseModel):
    """Anforderungsmodell für eine manuelle Synchronisierung."""
    date: str = Field(..., description="Datum im Format YYYY-MM-DD")
    appointment_type_id: Optional[int] = Field(None, description="ID des Termintyps")
    delete_obsolete: bool = Field(True, description="Obsolete Untersuchungen löschen")

class SyncResult(BaseModel):
    """Antwortmodell für das Ergebnis einer Synchronisierung."""
    date: str
    total_appointments: int
    new_examinations: int
    updated_examinations: int
    deleted_examinations: int
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None

class SchedulerStatusResponse(BaseModel):
    """Antwortmodell für den Status des Schedulers."""
    enabled: bool
    running: bool
    next_sync_time: Optional[datetime] = None
    interval_minutes: int
    active_days: List[int]
    start_time: str
    end_time: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SchedulerConfigRequest(BaseModel):
    """Anforderungsmodell für die Konfiguration des Schedulers."""
    enabled: bool = Field(..., description="Scheduler aktivieren/deaktivieren")
    interval_minutes: int = Field(..., description="Intervall in Minuten")
    active_days: List[int] = Field(..., description="Aktive Tage (1-7, wobei 1=Montag)")
    start_time: str = Field(..., description="Startzeit im Format HH:MM")
    end_time: str = Field(..., description="Endzeit im Format HH:MM")

class AppointmentResponse(BaseModel):
    """Antwortmodell für einen CallDoc-Termin."""
    id: int
    patient_id: int
    patient_name: str
    scheduled_for: datetime
    appointment_type: str
    appointment_type_id: int
    status: str
    doctor_name: Optional[str] = None
    room_name: Optional[str] = None

class AppointmentListResponse(BaseModel):
    """Antwortmodell für eine Liste von CallDoc-Terminen."""
    count: int
    date: str
    appointments: List[AppointmentResponse]

class ExaminationResponse(BaseModel):
    """Antwortmodell für eine SQLHK-Untersuchung."""
    id: int
    patient_id: int
    patient_name: str
    examination_date: datetime
    examination_type: str
    examination_type_id: int
    status: str
    doctor_name: Optional[str] = None
    room_name: Optional[str] = None

class ExaminationListResponse(BaseModel):
    """Antwortmodell für eine Liste von SQLHK-Untersuchungen."""
    count: int
    date: str
    examinations: List[ExaminationResponse]

class ErrorResponse(BaseModel):
    """Antwortmodell für Fehlermeldungen."""
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)
    code: Optional[str] = None
