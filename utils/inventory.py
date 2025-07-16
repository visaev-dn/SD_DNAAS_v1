#!/usr/bin/env python3
"""
Inventory Management - Maps leaf/port info to device IPs and connection details
Provides device discovery and connection management
"""

import logging
import yaml
from typing import Dict, Any, Optional
from config_engine.deployer import create_connection

logger = logging.getLogger(__name__)

class InventoryManager:
    """Manages network device inventory and connections"""
    
    def __init__(self, topology_file: str = "topology.yaml"):
        self.topology_file = topology_file
        self.topology = self._load_topology()
    
    def _load_topology(self) -> Dict[str, Any]:
        """Load topology configuration from YAML file"""
        try:
            with open(self.topology_file, 'r') as f:
                topology = yaml.safe_load(f)
            logger.info(f"Topology loaded from {self.topology_file}")
            return topology
        except FileNotFoundError:
            logger.error(f"Topology file not found: {self.topology_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing topology file: {e}")
            raise
    
    def get_device_info(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Get device information by name"""
        # Check if it's a leaf device
        if device_name in self.topology:
            return self.topology[device_name]
        
        # Check if it's a spine device
        for spine in self.topology.get('spines', []):
            if spine['name'] == device_name:
                return spine
        
        logger.error(f"Device {device_name} not found in topology")
        return None
    
    def get_device_connection(self, device_name: str) -> Optional[Any]:
        """Get device connection object"""
        device_info = self.get_device_info(device_name)
        if not device_info:
            return None
        
        try:
            connection = create_connection(device_info)
            logger.info(f"Connection object created for {device_name}")
            return connection
        except Exception as e:
            logger.error(f"Failed to create connection for {device_name}: {e}")
            return None
    
    def list_devices(self) -> Dict[str, Any]:
        """List all devices in the topology"""
        devices = {}
        
        # Add leaf devices
        for leaf_name, leaf_info in self.topology.items():
            if leaf_name not in ['spines', 'global_config']:
                devices[leaf_name] = {
                    'type': 'leaf',
                    'mgmt_ip': leaf_info['mgmt_ip'],
                    'device_type': leaf_info.get('device_type', 'unknown')
                }
        
        # Add spine devices
        for spine in self.topology.get('spines', []):
            devices[spine['name']] = {
                'type': 'spine',
                'mgmt_ip': spine['mgmt_ip'],
                'device_type': spine.get('device_type', 'unknown')
            }
        
        return devices
    
    def validate_device_connectivity(self, device_name: str) -> bool:
        """Validate if device is reachable"""
        device_info = self.get_device_info(device_name)
        if not device_info:
            return False
        
        try:
            connection = create_connection(device_info)
            with connection:
                if connection.connection:
                    logger.info(f"Device {device_name} is reachable")
                    return True
                else:
                    logger.error(f"Device {device_name} is not reachable")
                    return False
        except Exception as e:
            logger.error(f"Error validating connectivity to {device_name}: {e}")
            return False
    
    def get_available_ports(self, device_name: str) -> list:
        """Get available ports for a device"""
        device_info = self.get_device_info(device_name)
        if not device_info:
            return []
        
        return device_info.get('ports', [])
    
    def is_port_available(self, device_name: str, port: str) -> bool:
        """Check if a port is available on a device"""
        available_ports = self.get_available_ports(device_name)
        return port in available_ports

# Global inventory manager instance
_inventory_manager = None

def get_inventory_manager() -> InventoryManager:
    """Get global inventory manager instance"""
    global _inventory_manager
    if _inventory_manager is None:
        _inventory_manager = InventoryManager()
    return _inventory_manager

def get_device_connection(device_name: str, topology: Dict[str, Any] = None) -> Optional[Any]:
    """Convenience function to get device connection"""
    if topology:
        # Use provided topology
        device_info = None
        if device_name in topology:
            device_info = topology[device_name]
        else:
            for spine in topology.get('spines', []):
                if spine['name'] == device_name:
                    device_info = spine
                    break
        
        if device_info:
            return create_connection(device_info)
        else:
            logger.error(f"Device {device_name} not found in topology")
            return None
    else:
        # Use inventory manager
        manager = get_inventory_manager()
        return manager.get_device_connection(device_name) 