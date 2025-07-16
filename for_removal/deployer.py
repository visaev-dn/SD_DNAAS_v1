#!/usr/bin/env python3
"""
Configuration Deployer - Sends configuration to network devices
Supports multiple connection methods: SSH, NETCONF, RESTCONF
"""

import logging
import time
from typing import Dict, Any, Optional
import paramiko
import yaml

logger = logging.getLogger(__name__)

class DeviceConnection:
    """Base class for device connections"""
    
    def __init__(self, device_info: Dict[str, Any]):
        self.device_info = device_info
        self.connection = None
    
    def connect(self) -> bool:
        """Establish connection to device"""
        raise NotImplementedError
    
    def disconnect(self):
        """Close connection to device"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def send_config(self, config: str) -> bool:
        """Send configuration to device"""
        raise NotImplementedError
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

class SSHConnection(DeviceConnection):
    """SSH-based device connection"""
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.connection = paramiko.SSHClient()
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.connection.connect(
                hostname=self.device_info['mgmt_ip'],
                username=self.device_info['username'],
                password=self.device_info['password'],
                timeout=30
            )
            
            logger.info(f"SSH connection established to {self.device_info['mgmt_ip']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish SSH connection to {self.device_info['mgmt_ip']}: {e}")
            return False
    
    def send_config(self, config: str) -> bool:
        """Send configuration via SSH"""
        if not self.connection:
            logger.error("No SSH connection established")
            return False
        
        try:
            # Get shell channel
            shell = self.connection.invoke_shell()
            time.sleep(1)
            
            # Enter enable mode
            shell.send('enable\n')
            time.sleep(1)
            
            # Enter configuration mode
            shell.send('configure terminal\n')
            time.sleep(1)
            
            # Send configuration line by line
            config_lines = config.strip().split('\n')
            for line in config_lines:
                if line.strip():
                    shell.send(f'{line}\n')
                    time.sleep(0.1)
            
            # Exit configuration mode
            shell.send('end\n')
            time.sleep(1)
            
            # Save configuration
            shell.send('write memory\n')
            time.sleep(2)
            
            logger.info(f"Configuration sent successfully to {self.device_info['mgmt_ip']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send configuration to {self.device_info['mgmt_ip']}: {e}")
            return False

class NETCONFConnection(DeviceConnection):
    """NETCONF-based device connection (placeholder)"""
    
    def connect(self) -> bool:
        """Establish NETCONF connection"""
        logger.warning("NETCONF connection not implemented yet")
        return False
    
    def send_config(self, config: str) -> bool:
        """Send configuration via NETCONF"""
        logger.warning("NETCONF configuration not implemented yet")
        return False

class RESTCONFConnection(DeviceConnection):
    """RESTCONF-based device connection (placeholder)"""
    
    def connect(self) -> bool:
        """Establish RESTCONF connection"""
        logger.warning("RESTCONF connection not implemented yet")
        return False
    
    def send_config(self, config: str) -> bool:
        """Send configuration via RESTCONF"""
        logger.warning("RESTCONF configuration not implemented yet")
        return False

def create_connection(device_info: Dict[str, Any]) -> DeviceConnection:
    """Factory function to create appropriate connection type"""
    device_type = device_info.get('device_type', 'ssh')
    
    if device_type == 'ssh' or device_type == 'arista_eos':
        return SSHConnection(device_info)
    elif device_type == 'netconf':
        return NETCONFConnection(device_info)
    elif device_type == 'restconf':
        return RESTCONFConnection(device_info)
    else:
        raise ValueError(f"Unsupported device type: {device_type}")

def push_config(connection: DeviceConnection, config: str, device_name: str) -> bool:
    """Push configuration to device"""
    logger.info(f"Pushing configuration to {device_name}")
    
    try:
        with connection:
            if connection.connection:
                success = connection.send_config(config)
                if success:
                    logger.info(f"Configuration successfully deployed to {device_name}")
                else:
                    logger.error(f"Failed to deploy configuration to {device_name}")
                return success
            else:
                logger.error(f"Failed to establish connection to {device_name}")
                return False
                
    except Exception as e:
        logger.error(f"Error deploying configuration to {device_name}: {e}")
        return False 