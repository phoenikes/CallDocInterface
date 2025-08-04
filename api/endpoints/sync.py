#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Synchronisierungsendpunkte für die CallDoc-SQLHK Synchronisierungs-API

Diese Datei enthält die API-Endpunkte für die Synchronisierung zwischen
CallDoc und SQLHK.

Autor: Markus
Datum: 03.08.2025
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List

from ..models import SyncRequest, SyncResult
from ..dependencies import get_sync_service, verify_api_key

router = APIRouter(tags=["Synchronisierung"])

# Speicher für Synchronisierungsverlauf
sync_history = []
current_sync = None

@router.post("/run", response_model=SyncResult, dependencies=[Depends(verify_api_key)])
async def run_sync(
    request: SyncRequest,
    sync_service=Depends(get_sync_service)
):
    """
    Startet eine manuelle Synchronisierung für das angegebene Datum.
    
    Args:
        request: SyncRequest-Objekt mit Datum, Termintyp-ID und Löschflag
    
    Returns:
        SyncResult-Objekt mit den Ergebnissen der Synchronisierung
    """
    global current_sync
    
    # Prüfen, ob bereits eine Synchronisierung läuft
    if current_sync:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Eine Synchronisierung läuft bereits"
        )
    
    try:
        # Aktuelle Synchronisierung setzen
        current_sync = {
            "date": request.date,
            "appointment_type_id": request.appointment_type_id,
            "delete_obsolete": request.delete_obsolete,
            "start_time": datetime.now()
        }
        
        # Synchronisierung durchführen
        result = sync_service.synchronize(
            date=request.date,
            appointment_type_id=request.appointment_type_id,
            delete_obsolete=request.delete_obsolete
        )
        
        # Ergebnis zum Verlauf hinzufügen
        sync_history.append(result)
        
        # Verlauf auf maximal 50 Einträge begrenzen
        if len(sync_history) > 50:
            sync_history.pop(0)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Synchronisierung: {str(e)}"
        )
    
    finally:
        # Aktuelle Synchronisierung zurücksetzen
        current_sync = None

@router.post("/run/async", dependencies=[Depends(verify_api_key)])
async def run_sync_async(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    sync_service=Depends(get_sync_service)
):
    """
    Startet eine asynchrone Synchronisierung für das angegebene Datum.
    
    Args:
        request: SyncRequest-Objekt mit Datum, Termintyp-ID und Löschflag
        background_tasks: BackgroundTasks-Objekt für asynchrone Ausführung
    
    Returns:
        Status der gestarteten Synchronisierung
    """
    global current_sync
    
    # Prüfen, ob bereits eine Synchronisierung läuft
    if current_sync:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Eine Synchronisierung läuft bereits"
        )
    
    # Aktuelle Synchronisierung setzen
    current_sync = {
        "date": request.date,
        "appointment_type_id": request.appointment_type_id,
        "delete_obsolete": request.delete_obsolete,
        "start_time": datetime.now()
    }
    
    # Funktion für die Hintergrundaufgabe
    def background_sync():
        global current_sync
        try:
            # Synchronisierung durchführen
            result = sync_service.synchronize(
                date=request.date,
                appointment_type_id=request.appointment_type_id,
                delete_obsolete=request.delete_obsolete
            )
            
            # Ergebnis zum Verlauf hinzufügen
            sync_history.append(result)
            
            # Verlauf auf maximal 50 Einträge begrenzen
            if len(sync_history) > 50:
                sync_history.pop(0)
        
        except Exception as e:
            # Fehler protokollieren
            import logging
            logging.error(f"Fehler bei der asynchronen Synchronisierung: {str(e)}")
        
        finally:
            # Aktuelle Synchronisierung zurücksetzen
            current_sync = None
    
    # Hintergrundaufgabe starten
    background_tasks.add_task(background_sync)
    
    return {
        "status": "started",
        "message": f"Synchronisierung für {request.date} wurde im Hintergrund gestartet",
        "date": request.date,
        "appointment_type_id": request.appointment_type_id,
        "delete_obsolete": request.delete_obsolete
    }

@router.get("/status", dependencies=[Depends(verify_api_key)])
async def sync_status():
    """
    Gibt den Status der aktuellen Synchronisierung zurück.
    
    Returns:
        Status der aktuellen Synchronisierung oder None, wenn keine läuft
    """
    if current_sync:
        # Laufzeit berechnen
        runtime = (datetime.now() - current_sync["start_time"]).total_seconds()
        
        return {
            "running": True,
            "date": current_sync["date"],
            "appointment_type_id": current_sync["appointment_type_id"],
            "delete_obsolete": current_sync["delete_obsolete"],
            "start_time": current_sync["start_time"],
            "runtime_seconds": runtime
        }
    
    return {
        "running": False
    }

@router.get("/history", dependencies=[Depends(verify_api_key)])
async def sync_history_endpoint(limit: int = 10):
    """
    Gibt den Synchronisierungsverlauf zurück.
    
    Args:
        limit: Maximale Anzahl der zurückzugebenden Einträge
    
    Returns:
        Liste der letzten Synchronisierungsergebnisse
    """
    # Limit auf sinnvollen Bereich beschränken
    if limit < 1:
        limit = 1
    elif limit > 50:
        limit = 50
    
    # Neueste Einträge zuerst zurückgeben
    return sync_history[-limit:][::-1]
