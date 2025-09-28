#!/usr/bin/env python3
"""
Universal Device Manager

Unified device connection and management using proven patterns
extracted from interface discovery and other working systems.
"""

import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
from .data_models import DeviceInfo, DeviceConnection, DeviceConnectionError

logger = logging.getLogger(__name__)


class UniversalDeviceManager:
    """Unified device management using proven patterns from interface discovery"""
    
    def __init__(self, devices_file: str = "devices.yaml"):
        self.devices_file = devices_file
        self.device_cache = {}
        self.connection_cache = {}
        
    def get_device_info(self, device_name: str) -> Optional[DeviceInfo]:
        """Get device info using proven devices.yaml loading logic"""
        
        try:
            # Use exact proven logic from interface discovery
            with open(self.devices_file, 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                logger.warning(f"Device {device_name} not found in devices.yaml")
                return None
            
            defaults = devices_data.get('defaults', {})
            
            # Build device info using proven pattern
            return DeviceInfo(
                name=device_name,
                mgmt_ip=device_info.get('mgmt_ip', ''),
                username=device_info.get('username', defaults.get('username', '')),
                password=device_info.get('password', defaults.get('password', '')),
                device_type=device_info.get('device_type', defaults.get('device_type', 'unknown')),
                ssh_port=device_info.get('ssh_port', defaults.get('ssh_port', 22)),
                status=device_info.get('status', 'active'),
                location=device_info.get('location', ''),
                role=device_info.get('role', '')
            )
            
        except Exception as e:
            logger.error(f"Error loading device info for {device_name}: {e}")
            return None
    
    def get_all_devices_with_ssh_info(self) -> List[DeviceInfo]:
        """Get all devices with complete SSH connection info (from interface discovery pattern)"""
        
        devices_with_ssh = []
        
        try:
            with open(self.devices_file, 'r') as f:
                devices_data = yaml.safe_load(f)
            
            defaults = devices_data.get('defaults', {})
            
            for device_name, device_info in devices_data.items():
                if device_name == 'defaults' or not isinstance(device_info, dict):
                    continue
                
                # Check for complete SSH info (proven filter from interface discovery)
                mgmt_ip = device_info.get('mgmt_ip')
                username = device_info.get('username', defaults.get('username'))
                password = device_info.get('password', defaults.get('password'))
                
                if mgmt_ip and username and password:
                    device_obj = DeviceInfo(
                        name=device_name,
                        mgmt_ip=mgmt_ip,
                        username=username,
                        password=password,
                        device_type=device_info.get('device_type', defaults.get('device_type', 'unknown')),
                        ssh_port=device_info.get('ssh_port', defaults.get('ssh_port', 22)),
                        status=device_info.get('status', 'active'),
                        location=device_info.get('location', ''),
                        role=device_info.get('role', '')
                    )
                    devices_with_ssh.append(device_obj)
            
            logger.info(f"Found {len(devices_with_ssh)} devices with complete SSH info")
            return devices_with_ssh
            
        except Exception as e:
            logger.error(f"Error loading devices with SSH info: {e}")
            return []
    
    def get_device_connection(self, device_name: str) -> Optional[DeviceConnection]:
        """Get managed connection to device using proven DNOSSSH approach"""
        
        try:
            # Check cache first
            if device_name in self.connection_cache:
                connection = self.connection_cache[device_name]
                if connection.connected:
                    return connection
            
            # Get device info
            device_info = self.get_device_info(device_name)
            if not device_info:
                raise DeviceConnectionError(f"Device {device_name} not found")
            
            # Create connection using proven DNOSSSH
            from utils.dnos_ssh import DNOSSSH
            
            ssh_client = DNOSSSH(
                hostname=device_info.mgmt_ip,
                username=device_info.username,
                password=device_info.password,
                debug=True  # Enable debug for visibility
            )
            
            # Test connection
            if ssh_client.connect():
                connection = DeviceConnection(
                    device_name=device_name,
                    device_info=device_info,
                    ssh_client=ssh_client,
                    connected=True,
                    connection_time=datetime.now()
                )
                
                # Cache connection
                self.connection_cache[device_name] = connection
                
                logger.info(f"Successfully connected to {device_name}")
                return connection
            else:
                raise DeviceConnectionError(f"Failed to connect to {device_name}")
                
        except Exception as e:
            logger.error(f"Error getting connection to {device_name}: {e}")
            raise DeviceConnectionError(f"Connection failed: {e}")
    
    def check_device_reachability(self, device_name: str) -> bool:
        """Check if device is reachable using proven pattern"""
        
        try:
            device_info = self.get_device_info(device_name)
            if not device_info:
                return False
            
            # Use proven reachability check from interface discovery
            from utils.dnos_ssh import DNOSSSH
            
            ssh_client = DNOSSSH(
                hostname=device_info.mgmt_ip,
                username=device_info.username,
                password=device_info.password,
                debug=False  # Disable debug for reachability check
            )
            
            # Quick connection test
            if ssh_client.connect():
                ssh_client.disconnect()
                logger.debug(f"Device {device_name} is reachable")
                return True
            else:
                logger.debug(f"Device {device_name} is not reachable")
                return False
                
        except Exception as e:
            logger.debug(f"Reachability check failed for {device_name}: {e}")
            return False
    
    def check_reachability_batch(self, device_names: List[str]) -> Dict[str, bool]:
        """Check multiple devices using parallel approach from interface discovery"""
        
        try:
            import concurrent.futures
            
            reachability_results = {}
            
            # Use proven parallel pattern from interface discovery
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit reachability checks
                future_to_device = {
                    executor.submit(self.check_device_reachability, device_name): device_name
                    for device_name in device_names
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_device):
                    device_name = future_to_device[future]
                    try:
                        is_reachable = future.result()
                        reachability_results[device_name] = is_reachable
                    except Exception as e:
                        logger.error(f"Reachability check failed for {device_name}: {e}")
                        reachability_results[device_name] = False
            
            return reachability_results
            
        except Exception as e:
            logger.error(f"Batch reachability check failed: {e}")
            return {device: False for device in device_names}
    
    def disconnect_all(self):
        """Disconnect all cached connections"""
        
        for device_name, connection in self.connection_cache.items():
            try:
                if connection.connected and connection.ssh_client:
                    connection.ssh_client.disconnect()
                    connection.connected = False
                    logger.debug(f"Disconnected from {device_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {device_name}: {e}")
        
        self.connection_cache.clear()


# Convenience functions
def get_device_info(device_name: str) -> Optional[DeviceInfo]:
    """Convenience function to get device info"""
    manager = UniversalDeviceManager()
    return manager.get_device_info(device_name)


def check_device_reachability(device_name: str) -> bool:
    """Convenience function to check device reachability"""
    manager = UniversalDeviceManager()
    return manager.check_device_reachability(device_name)


def get_all_reachable_devices() -> List[DeviceInfo]:
    """Get all devices that are reachable"""
    manager = UniversalDeviceManager()
    all_devices = manager.get_all_devices_with_ssh_info()
    
    reachable_devices = []
    for device_info in all_devices:
        if manager.check_device_reachability(device_info.name):
            reachable_devices.append(device_info)
    
    return reachable_devices
