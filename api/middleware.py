#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Middleware für die CallDoc-SQLHK Sync API

Diese Datei enthält Middleware-Komponenten für die FastAPI-Anwendung,
insbesondere für Logging und Fehlerbehandlung.

Autor: Markus
Datum: 04.08.2025
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from logging_config import get_logger

# Logger für die Middleware
logger = get_logger(__name__)
access_logger = get_logger("api.access")
error_logger = get_logger("api.error")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware für detailliertes Logging von API-Anfragen und -Antworten.
    Protokolliert Anfrage-Details, Verarbeitungszeit und Antwort-Status.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialisiert die Logging-Middleware.
        
        Args:
            app: Die ASGI-Anwendung
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Verarbeitet eine Anfrage und protokolliert Details.
        
        Args:
            request: Die eingehende Anfrage
            call_next: Die nächste Middleware oder Route-Handler
            
        Returns:
            Die Antwort der Anwendung
        """
        # Anfangszeit erfassen
        start_time = time.time()
        
        # Client-Informationen erfassen
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        client_ip = forwarded_for or client_host
        
        # Anfrage-Informationen protokollieren
        access_logger.info(
            f"Eingehende Anfrage | {request.method} {request.url.path} | "
            f"Client: {client_ip} | "
            f"User-Agent: {request.headers.get('User-Agent', 'unknown')}"
        )
        
        # Anfrage verarbeiten und Fehler abfangen
        try:
            response = await call_next(request)
            
            # Verarbeitungszeit berechnen
            process_time = time.time() - start_time
            
            # Antwort-Informationen protokollieren
            access_logger.info(
                f"Antwort gesendet | {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Verarbeitungszeit: {process_time:.4f}s"
            )
            
            # Bei Fehlern zusätzliche Informationen protokollieren
            if response.status_code >= 400:
                error_logger.warning(
                    f"Fehlerhafte Anfrage | {request.method} {request.url.path} | "
                    f"Status: {response.status_code} | "
                    f"Client: {client_ip}"
                )
            
            return response
            
        except Exception as e:
            # Verarbeitungszeit bei Fehler
            process_time = time.time() - start_time
            
            # Fehler protokollieren
            error_logger.error(
                f"Unbehandelte Ausnahme | {request.method} {request.url.path} | "
                f"Client: {client_ip} | "
                f"Fehler: {str(e)} | "
                f"Verarbeitungszeit: {process_time:.4f}s",
                exc_info=True
            )
            
            # Fehler weiterleiten
            raise


class ResponseTimeHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware zum Hinzufügen der Verarbeitungszeit als Header zur Antwort.
    Nützlich für Debugging und Performance-Monitoring.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Verarbeitet eine Anfrage und fügt den X-Process-Time-Header hinzu.
        
        Args:
            request: Die eingehende Anfrage
            call_next: Die nächste Middleware oder Route-Handler
            
        Returns:
            Die Antwort mit dem zusätzlichen Header
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
