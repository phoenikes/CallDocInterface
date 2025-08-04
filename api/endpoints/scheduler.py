#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduler-Endpunkte für die CallDoc-SQLHK Synchronisierungs-API

Diese Datei enthält die API-Endpunkte für die Verwaltung des automatischen
Synchronisierungs-Schedulers.

Autor: Markus
Datum: 03.08.2025
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models import SchedulerStatusResponse, SchedulerConfigRequest
from ..dependencies import get_config_manager, verify_api_key

router = APIRouter(tags=["Scheduler"])

# Globale Variable für den Scheduler-Status
scheduler_running = False

@router.get("/status", response_model=SchedulerStatusResponse, dependencies=[Depends(verify_api_key)])
async def scheduler_status(config_manager=Depends(get_config_manager)):
    """
    Gibt den aktuellen Status des Schedulers zurück.
    
    Returns:
        SchedulerStatusResponse-Objekt mit dem aktuellen Status des Schedulers
    """
    auto_sync_settings = config_manager.get_auto_sync_settings()
    
    return {
        "enabled": auto_sync_settings["ENABLED"],
        "running": scheduler_running,
        "next_sync_time": None,  # Hier könnte die nächste geplante Synchronisierung berechnet werden
        "interval_minutes": auto_sync_settings["INTERVAL_MINUTES"],
        "active_days": auto_sync_settings["DAYS"],
        "start_time": auto_sync_settings["START_TIME"],
        "end_time": auto_sync_settings["END_TIME"]
    }

@router.put("/config", dependencies=[Depends(verify_api_key)])
async def update_scheduler_config(
    config: SchedulerConfigRequest,
    config_manager=Depends(get_config_manager)
):
    """
    Aktualisiert die Konfiguration des Schedulers.
    
    Args:
        config: SchedulerConfigRequest-Objekt mit der neuen Konfiguration
    
    Returns:
        Die aktualisierte Konfiguration
    """
    # Konfiguration aktualisieren
    config_manager.set_value("AUTO_SYNC", "ENABLED", str(config.enabled))
    config_manager.set_value("AUTO_SYNC", "INTERVAL_MINUTES", str(config.interval_minutes))
    config_manager.set_value("AUTO_SYNC", "DAYS", ",".join(map(str, config.active_days)))
    config_manager.set_value("AUTO_SYNC", "START_TIME", config.start_time)
    config_manager.set_value("AUTO_SYNC", "END_TIME", config.end_time)
    
    # Konfiguration speichern
    config_manager.save_config()
    
    return {
        "status": "success",
        "message": "Scheduler-Konfiguration aktualisiert",
        "config": {
            "enabled": config.enabled,
            "interval_minutes": config.interval_minutes,
            "active_days": config.active_days,
            "start_time": config.start_time,
            "end_time": config.end_time
        }
    }

@router.put("/start", dependencies=[Depends(verify_api_key)])
async def start_scheduler():
    """
    Startet den Scheduler.
    
    Returns:
        Status des Scheduler-Starts
    """
    global scheduler_running
    
    if scheduler_running:
        return {
            "status": "warning",
            "message": "Scheduler läuft bereits"
        }
    
    # Hier würde der tatsächliche Scheduler-Start erfolgen
    # In der realen Implementierung würde hier der AutoSyncScheduler gestartet werden
    scheduler_running = True
    
    return {
        "status": "success",
        "message": "Scheduler gestartet"
    }

@router.put("/stop", dependencies=[Depends(verify_api_key)])
async def stop_scheduler():
    """
    Stoppt den Scheduler.
    
    Returns:
        Status des Scheduler-Stopps
    """
    global scheduler_running
    
    if not scheduler_running:
        return {
            "status": "warning",
            "message": "Scheduler läuft nicht"
        }
    
    # Hier würde der tatsächliche Scheduler-Stopp erfolgen
    # In der realen Implementierung würde hier der AutoSyncScheduler gestoppt werden
    scheduler_running = False
    
    return {
        "status": "success",
        "message": "Scheduler gestoppt"
    }
