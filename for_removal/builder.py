#!/usr/bin/env python3
"""
Configuration Builder - Renders templates with variables
Handles different service types and generates device-specific configurations
"""

import logging
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
import yaml

logger = logging.getLogger(__name__)

class ConfigBuilder:
    def __init__(self, templates_dir: str = "templates"):
        """Initialize configuration builder with template directory"""
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.vlan_counter = 0
        
    def parse_vlan_ranges(self, vlan_spec: List[str]) -> List[int]:
        """Parse VLAN specifications like ['100-105', '200'] into list of VLANs"""
        vlans = []
        for spec in vlan_spec:
            if '-' in spec:
                start, end = map(int, spec.split('-'))
                vlans.extend(range(start, end + 1))
            else:
                vlans.append(int(spec))
        return sorted(vlans)
    
    def allocate_outer_vlan(self, topology: Dict[str, Any]) -> int:
        """Allocate outer VLAN for Q-in-Q services"""
        global_config = topology.get('global_config', {})
        start = global_config.get('qinq_outer_vlan_start', 3000)
        end = global_config.get('qinq_outer_vlan_end', 4000)
        
        # Simple allocation - in production, you'd want to track used VLANs
        self.vlan_counter += 1
        outer_vlan = start + self.vlan_counter
        
        if outer_vlan > end:
            raise ValueError("No available outer VLANs for Q-in-Q")
        
        return outer_vlan
    
    def build_config(self, request: Dict[str, Any], topology: Dict[str, Any], 
                    is_source: bool = True) -> str:
        """Build configuration based on service type and device role"""
        
        service_type = request['service_type']
        logger.info(f"Building {service_type} configuration for {'source' if is_source else 'destination'}")
        
        if service_type == 'qinq':
            return self._build_qinq_config(request, topology, is_source)
        elif service_type == 'single_vlan':
            return self._build_single_vlan_config(request, topology, is_source)
        elif service_type == 'multi_vlan':
            return self._build_multi_vlan_config(request, topology, is_source)
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
    
    def _build_qinq_config(self, request: Dict[str, Any], topology: Dict[str, Any], 
                          is_source: bool) -> str:
        """Build Q-in-Q configuration"""
        template = self.env.get_template('qinq_template.j2')
        
        # Parse VLANs
        inner_vlans = self.parse_vlan_ranges(request['vlans'])
        outer_vlan = self.allocate_outer_vlan(topology)
        
        # Determine remote device
        if is_source:
            local_leaf = request['source_leaf']
            remote_leaf = request['destination_leaf']
            port = request['source_port']
        else:
            local_leaf = request['destination_leaf']
            remote_leaf = request['source_leaf']
            port = request['destination_port']
        
        context = {
            'port': port,
            'remote_leaf': remote_leaf,
            'outer_vlan': outer_vlan,
            'inner_vlans': inner_vlans,
            'encapsulation': request.get('encapsulation', 'dot1q'),
            'description': request.get('description', f'Q-in-Q to {remote_leaf}'),
            'local_leaf': local_leaf
        }
        
        return template.render(**context)
    
    def _build_single_vlan_config(self, request: Dict[str, Any], topology: Dict[str, Any], 
                                 is_source: bool) -> str:
        """Build single VLAN configuration"""
        template = self.env.get_template('single_vlan_template.j2')
        
        vlans = self.parse_vlan_ranges(request['vlans'])
        if len(vlans) != 1:
            raise ValueError("Single VLAN service requires exactly one VLAN")
        
        if is_source:
            local_leaf = request['source_leaf']
            remote_leaf = request['destination_leaf']
            port = request['source_port']
        else:
            local_leaf = request['destination_leaf']
            remote_leaf = request['source_leaf']
            port = request['destination_port']
        
        context = {
            'port': port,
            'remote_leaf': remote_leaf,
            'vlan': vlans[0],
            'description': request.get('description', f'Single VLAN to {remote_leaf}'),
            'local_leaf': local_leaf
        }
        
        return template.render(**context)
    
    def _build_multi_vlan_config(self, request: Dict[str, Any], topology: Dict[str, Any], 
                                is_source: bool) -> str:
        """Build multi-VLAN configuration"""
        template = self.env.get_template('multi_vlan_template.j2')
        
        vlans = self.parse_vlan_ranges(request['vlans'])
        
        if is_source:
            local_leaf = request['source_leaf']
            remote_leaf = request['destination_leaf']
            port = request['source_port']
        else:
            local_leaf = request['destination_leaf']
            remote_leaf = request['source_leaf']
            port = request['destination_port']
        
        context = {
            'port': port,
            'remote_leaf': remote_leaf,
            'vlans': vlans,
            'description': request.get('description', f'Multi-VLAN to {remote_leaf}'),
            'local_leaf': local_leaf
        }
        
        return template.render(**context)

def build_config(request: Dict[str, Any], topology: Dict[str, Any], 
                is_source: bool = True) -> str:
    """Convenience function to build configuration"""
    builder = ConfigBuilder()
    return builder.build_config(request, topology, is_source) 