#!/usr/bin/env python3
"""
Interface Discovery Service

Simplified interface discovery system focused on CLI integration.
Uses single command execution ("show interface description | no-more") 
to discover and cache interface information from network devices.

Features:
- Single command discovery ("show int desc | no-more")
- Basic interface parsing (names, status, descriptions)
- Simple database caching with timestamps
- CLI integration for main.py BD editor
- On-demand discovery triggers only

Future Expansion:
- Multiple command discovery
- RESTful API endpoints
- Frontend integration
- Scheduled discovery
- Complex availability analysis
"""

from .data_models import InterfaceDiscoveryData
from .simple_discovery import SimpleInterfaceDiscovery
from .description_parser import InterfaceDescriptionParser
from .smart_filter import SmartInterfaceFilter, InterfaceOption
from .cli_integration import get_device_interface_menu, get_smart_device_interface_menu, enhanced_interface_selection_for_editor

# Enhanced CLI presentation (optional)
try:
    from .enhanced_cli_display import (
        EnhancedDeviceDisplay,
        EnhancedInterfaceDisplay,
        EnhancedSmartSelection,
        enhanced_device_selection,
        enhanced_interface_selection,
        enhanced_smart_selection_complete
    )
    ENHANCED_CLI_AVAILABLE = True
except ImportError:
    ENHANCED_CLI_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "Lab Automation Framework"

__all__ = [
    'InterfaceDiscoveryData',
    'InterfaceOption',
    'SimpleInterfaceDiscovery', 
    'InterfaceDescriptionParser',
    'SmartInterfaceFilter',
    'get_device_interface_menu',
    'get_smart_device_interface_menu',
    'enhanced_interface_selection_for_editor'
]

# Add enhanced CLI exports if available
if ENHANCED_CLI_AVAILABLE:
    __all__.extend([
        'EnhancedDeviceDisplay',
        'EnhancedInterfaceDisplay',
        'EnhancedSmartSelection',
        'enhanced_device_selection',
        'enhanced_interface_selection',
        'enhanced_smart_selection_complete'
    ])

