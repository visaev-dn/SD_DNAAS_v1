#!/usr/bin/env python3
"""
Lab Automation Framework - API Package
Modular API structure with versioning and middleware support
"""

__version__ = "2.0.0"
__author__ = "Lab Automation Team"
__description__ = "Modular API server for lab automation framework"

from .v1 import api_v1
from .websocket import websocket_handlers
from .middleware import auth_middleware, error_middleware

__all__ = [
    'api_v1',
    'websocket_handlers', 
    'auth_middleware',
    'error_middleware'
]
