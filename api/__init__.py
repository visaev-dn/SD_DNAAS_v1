#!/usr/bin/env python3
"""
Lab Automation API Package
Modular API server for lab automation framework
"""

__version__ = "2.0.0"
__author__ = "Lab Automation Team"
__description__ = "Modular API server for lab automation framework"

# Import core components
from .v1 import api_v1
from .v2 import api_v2
from .websocket import websocket_handlers

# Import middleware components
from .middleware import (
    auth_middleware, error_middleware, rate_limiting, 
    logging_middleware, caching, monitoring
)

__all__ = [
    'api_v1', 'api_v2', 'websocket_handlers',
    'auth_middleware', 'error_middleware', 'rate_limiting',
    'logging_middleware', 'caching', 'monitoring'
]
