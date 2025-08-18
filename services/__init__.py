#!/usr/bin/env python3
"""
Services Package
Core service layer for the Lab Automation Framework
"""

from .service_container import ServiceContainer
from .interfaces import *

__all__ = [
    'ServiceContainer',
    # All interfaces are exported from .interfaces
]

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Service layer for Lab Automation Framework"
