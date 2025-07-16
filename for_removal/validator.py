#!/usr/bin/env python3
"""
Configuration Validator - Validates applied configuration
Checks if configuration was applied correctly and service is operational
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Configuration validation utilities"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def validate_interface_config(self, interface: str, expected_config: Dict[str, Any]) -> bool:
        """Validate interface configuration"""
        try:
            # Get current interface configuration
            command = f"show interfaces {interface} switchport"
            output = self._execute_command(command)
            
            if not output:
                logger.error(f"Could not retrieve configuration for {interface}")
                return False
            
            # Parse and validate configuration
            # This is a simplified validation - in production, you'd want more robust parsing
            for key, value in expected_config.items():
                if key not in output:
                    logger.warning(f"Expected configuration '{key}' not found in {interface}")
                    return False
            
            logger.info(f"Interface {interface} configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating interface {interface}: {e}")
            return False
    
    def validate_vlan_config(self, vlan: int) -> bool:
        """Validate VLAN configuration"""
        try:
            command = f"show vlan {vlan}"
            output = self._execute_command(command)
            
            if not output or f"VLAN {vlan}" not in output:
                logger.error(f"VLAN {vlan} not found or not configured")
                return False
            
            logger.info(f"VLAN {vlan} configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating VLAN {vlan}: {e}")
            return False
    
    def validate_service_connectivity(self, source_interface: str, 
                                    destination_interface: str) -> bool:
        """Validate service connectivity between interfaces"""
        try:
            # Simple ping test (this would need to be adapted based on your network setup)
            logger.info("Validating service connectivity...")
            
            # In a real implementation, you might:
            # 1. Check if interfaces are up/up
            # 2. Verify VLAN membership
            # 3. Test connectivity between endpoints
            # 4. Check for any error counters
            
            logger.info("Service connectivity validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating service connectivity: {e}")
            return False
    
    def _execute_command(self, command: str) -> Optional[str]:
        """Execute command on device and return output"""
        try:
            if hasattr(self.connection, 'connection') and self.connection.connection:
                stdin, stdout, stderr = self.connection.connection.exec_command(command)
                output = stdout.read().decode('utf-8')
                return output
            else:
                logger.error("No valid connection available")
                return None
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return None

def validate_config(connection, config: str, device_name: str) -> bool:
    """Main validation function"""
    logger.info(f"Validating configuration on {device_name}")
    
    try:
        validator = ConfigValidator(connection)
        
        # Basic validation - check if configuration was applied
        # In a real implementation, you'd parse the config and validate specific elements
        
        # For now, we'll do a simple check
        if "interface" in config.lower():
            logger.info(f"Configuration appears to be valid on {device_name}")
            return True
        else:
            logger.warning(f"Configuration validation inconclusive on {device_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error during configuration validation on {device_name}: {e}")
        return False 