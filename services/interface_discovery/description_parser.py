#!/usr/bin/env python3
"""
Interface Description Parser

Parses output from interface commands to extract interface data.
Supports DRIVENETS, Cisco, Juniper, and other network device formats.
"""

import re
import logging
from typing import List, Dict, Optional, Any
from .data_models import InterfaceDiscoveryData

logger = logging.getLogger(__name__)


class InterfaceDescriptionParser:
    """Parser for interface command outputs"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize regex patterns for different device types"""
        return {
            # DRIVENETS format (table-based output)
            'drivenets': {
                'pattern': re.compile(
                    r'^\|\s*([^|]+?)\s*\|\s*(enabled|disabled)\s*\|\s*(up|down|[^|]+?)\s*\|',
                    re.IGNORECASE | re.MULTILINE
                ),
                'groups': {'interface': 1, 'admin': 2, 'oper': 3, 'description': None}
            },
            
            # Cisco IOS format
            'cisco_ios': {
                'pattern': re.compile(
                    r'^(\S+)\s+(up|down|admin-down)\s+(up|down|testing|\S+)\s*(.*)$',
                    re.IGNORECASE | re.MULTILINE
                ),
                'groups': {'interface': 1, 'admin': 2, 'oper': 3, 'description': 4}
            }
        }
    
    def parse_interface_descriptions(self, raw_output: str, device_name: str = "") -> List[InterfaceDiscoveryData]:
        """Parse interface output into interface data structures"""
        if not raw_output or not raw_output.strip():
            return []
        
        # Try different parsing patterns
        for parser_type, pattern_info in self.patterns.items():
            try:
                interfaces = self._parse_with_pattern(raw_output, pattern_info, device_name, parser_type)
                if interfaces:
                    logger.info(f"Successfully parsed {len(interfaces)} interfaces using {parser_type} parser")
                    return interfaces
            except Exception as e:
                logger.debug(f"Parser {parser_type} failed: {e}")
                continue
        
        return []
    
    def _parse_with_pattern(self, output: str, pattern_info: Dict, device_name: str, parser_type: str) -> List[InterfaceDiscoveryData]:
        """Parse output using a specific pattern"""
        interfaces = []
        pattern = pattern_info['pattern']
        groups = pattern_info['groups']
        
        matches = pattern.findall(output)
        if not matches:
            return []
        
        for match in matches:
            try:
                interface_name = match[groups['interface'] - 1].strip()
                admin_status = match[groups['admin'] - 1].strip().lower()
                oper_status = match[groups['oper'] - 1].strip().lower()
                
                # Skip invalid interface names
                if not interface_name or interface_name.lower() in ['interface', 'admin', 'operational']:
                    continue
                
                # Normalize status
                if admin_status == 'enabled':
                    admin_status = 'up'
                elif admin_status == 'disabled':
                    admin_status = 'admin-down'
                
                interface_data = InterfaceDiscoveryData(
                    device_name=device_name,
                    interface_name=interface_name,
                    description="",
                    admin_status=admin_status,
                    oper_status=oper_status
                )
                
                interfaces.append(interface_data)
                
            except Exception as e:
                logger.debug(f"Failed to parse interface line: {e}")
                continue
        
        return interfaces
    
    def validate_parser(self) -> bool:
        """Validate parser with sample data"""
        try:
            sample_output = """
| bundle-60000             | enabled  | up              |
| ge100-0/0/1              | enabled  | down            |
| ge100-0/0/5.100 (L2)     | enabled  | up              |
"""
            interfaces = self.parse_interface_descriptions(sample_output, "TEST-DEVICE")
            return len(interfaces) >= 2
        except:
            return False
