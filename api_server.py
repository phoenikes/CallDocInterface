#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API-Server für die CallDoc-SQLHK Synchronisierung

Diese Datei enthält den FastAPI-Server für die CallDoc-SQLHK Synchronisierungs-API.
Der Server bietet Endpunkte für die Synchronisierung, Konfiguration und Abfrage von Daten.

Autor: Markus
Datum: 03.08.2025
"""

import os
import logging
import threading
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

# API-Endpunkte importieren
from api.endpoints import health, sync, scheduler, data
from api.dependencies import verify_api_key, get_api_key

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI-App erstellen
app = FastAPI(
    title="CallDoc-SQLHK Sync API",
    description="API für die Synchronisierung zwischen CallDoc und SQLHK",
    version="1.0.0",
    docs_url=None,  # Swagger-UI-URL deaktivieren (wird später manuell eingerichtet)
    redoc_url=None  # ReDoc-URL deaktivieren
)

# CORS-Middleware hinzufügen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routen für die API-Endpunkte registrieren
app.include_router(health.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1/sync")
app.include_router(scheduler.router, prefix="/api/v1/scheduler")
app.include_router(data.router, prefix="/api/v1/data")

# Benutzerdefinierte Swagger-UI-Route
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Benutzerdefinierte Swagger-UI-Route mit API-Schlüssel-Authentifizierung.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CallDoc-SQLHK Sync API - Dokumentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/api/v1/apikey", dependencies=[Depends(verify_api_key)])
async def get_current_api_key():
    """
    Gibt den aktuellen API-Schlüssel zurück.
    Nur für autorisierte Benutzer verfügbar.
    """
    return {"api_key": get_api_key()}

@app.get("/")
async def root():
    """
    Root-Endpunkt, der Informationen über die API zurückgibt.
    """
    return {
        "name": "CallDoc-SQLHK Sync API",
        "version": "1.0.0",
        "description": "API für die Synchronisierung zwischen CallDoc und SQLHK",
        "docs_url": "/api/docs"
    }

def start_api_server(host="0.0.0.0", port=8080, reload=False):
    """
    Startet den API-Server im Hintergrund.
    
    Args:
        host: Host-Adresse, standardmäßig 0.0.0.0 (alle Interfaces)
        port: Port, standardmäßig 8080
        reload: Automatisches Neuladen bei Codeänderungen (nur für Entwicklung)
    """
    def run_server():
        """Startet den Uvicorn-Server."""
        uvicorn.run(
            "api_server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    
    # Server in einem separaten Thread starten
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info(f"API-Server gestartet auf http://{host}:{port}")
    logger.info(f"API-Dokumentation verfügbar unter http://{host}:{port}/api/docs")
    
    return server_thread

if __name__ == "__main__":
    # Direkt starten, wenn die Datei als Hauptprogramm ausgeführt wird
    import argparse
    
    parser = argparse.ArgumentParser(description="CallDoc-SQLHK Sync API-Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host-Adresse (Standard: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (Standard: 8080)")
    parser.add_argument("--reload", action="store_true", help="Automatisches Neuladen bei Codeänderungen")
    
    args = parser.parse_args()
    
    print(f"CallDoc-SQLHK Sync API-Server wird gestartet auf http://{args.host}:{args.port}")
    print(f"API-Dokumentation wird verfügbar sein unter http://{args.host}:{args.port}/api/docs")
    
    # Server direkt starten (blockierend)
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
