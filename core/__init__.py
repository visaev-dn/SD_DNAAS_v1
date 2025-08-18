#!/usr/bin/env python3
"""
Core Package
Foundation components for the Lab Automation Framework
"""

from . import exceptions
from . import logging
from . import validation
from . import config

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Core framework components for Lab Automation"

__all__ = [
    'exceptions',
    'logging', 
    'validation',
    'config'
]
