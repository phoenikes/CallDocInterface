#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gesundheits- und Verbindungsendpunkte für die CallDoc-SQLHK Synchronisierungs-API

Diese Datei enthält die API-Endpunkte für den Gesundheitsstatus und die Verbindungsprüfung.

Autor: Markus
Datum: 03.08.2025
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models import HealthResponse, ConnectionStatusResponse
from ..dependencies import get_connection_checker, verify_api_key

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Gibt den Gesundheitsstatus der API zurück.
    
    Diese Endpunkt erfordert keine Authentifizierung und kann zur Überprüfung
    verwendet werden, ob die API-Server läuft.
    """
    return {
        "status": "online",
        "version": "1.0.0",
        "calldoc_connected": None,
        "sqlhk_connected": None
    }

@router.get("/health/full", response_model=HealthResponse, dependencies=[Depends(verify_api_key)])
async def full_health_check(connection_checker=Depends(get_connection_checker)):
    """
    Gibt den vollständigen Gesundheitsstatus der API zurück, einschließlich Verbindungsstatus.
    
    Dieser Endpunkt erfordert Authentifizierung und prüft auch die Verbindungen zu
    CallDoc und SQLHK.
    """
    calldoc_success, _ = connection_checker.check_calldoc_connection()
    sqlhk_success, _ = connection_checker.check_sqlhk_connection()
    
    return {
        "status": "online",
        "version": "1.0.0",
        "calldoc_connected": calldoc_success,
        "sqlhk_connected": sqlhk_success
    }

@router.get("/connections/status", response_model=ConnectionStatusResponse, dependencies=[Depends(verify_api_key)])
async def connection_status(connection_checker=Depends(get_connection_checker)):
    """
    Gibt den Status der Verbindungen zu CallDoc und SQLHK zurück.
    """
    calldoc_success, calldoc_error = connection_checker.check_calldoc_connection()
    sqlhk_success, sqlhk_error = connection_checker.check_sqlhk_connection()
    
    details = {}
    if not calldoc_success:
        details["calldoc_error"] = calldoc_error
    if not sqlhk_success:
        details["sqlhk_error"] = sqlhk_error
    
    return {
        "calldoc_connected": calldoc_success,
        "sqlhk_connected": sqlhk_success,
        "details": details
    }

@router.get("/connections/calldoc", dependencies=[Depends(verify_api_key)])
async def check_calldoc_connection(connection_checker=Depends(get_connection_checker)):
    """
    Prüft die Verbindung zum CallDoc-Server.
    """
    success, error = connection_checker.check_calldoc_connection()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CallDoc-Server nicht erreichbar: {error}"
        )
    
    return {"status": "connected", "message": "CallDoc-Server ist erreichbar"}

@router.get("/connections/sqlhk", dependencies=[Depends(verify_api_key)])
async def check_sqlhk_connection(connection_checker=Depends(get_connection_checker)):
    """
    Prüft die Verbindung zum SQLHK-Server.
    """
    success, error = connection_checker.check_sqlhk_connection()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SQLHK-Server nicht erreichbar: {error}"
        )
    
    return {"status": "connected", "message": "SQLHK-Server ist erreichbar"}
