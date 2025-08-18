#!/usr/bin/env python3
"""
Mock Bridge Domain Service Implementation
Simple mock implementation for testing the service architecture
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..interfaces.bridge_domain_service import (
    BridgeDomainService,
    BridgeDomainConfig,
    BridgeDomainResult
)


class MockBridgeDomainService(BridgeDomainService):
    """
    Mock implementation of BridgeDomainService for testing.
    
    This provides a working implementation that can be used to test
    the service architecture without requiring the full implementation.
    """
    
    def __init__(self):
        """Initialize the mock service"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Mock Bridge Domain Service initialized")
        
        # Mock data storage
        self._mock_configs = {}
        self._mock_devices = {
            "leaf1": {"name": "leaf1", "device_type": "leaf"},
            "leaf2": {"name": "leaf2", "device_type": "leaf"},
            "spine1": {"name": "spine1", "device_type": "spine"},
            "superspine1": {"name": "superspine1", "device_type": "superspine"}
        }
    
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """Mock implementation of bridge domain building"""
        try:
            self.logger.info(f"Mock: Building bridge domain for service {config.service_name}")
            
            # Validate configuration
            is_valid, errors = self.validate_configuration(config)
            if not is_valid:
                return BridgeDomainResult(
                    success=False,
                    error_message=f"Configuration validation failed: {', '.join(errors)}",
                    service_name=config.service_name,
                    vlan_id=config.vlan_id
                )
            
            # Mock configuration generation
            mock_configs = {
                config.source_device: {
                    "interface": config.source_port,
                    "vlan": config.vlan_id,
                    "service": config.service_name
                },
                config.destination_device: {
                    "interface": config.destination_port,
                    "vlan": config.vlan_id,
                    "service": config.service_name
                }
            }
            
            # Store mock configuration
            self._mock_configs[config.service_name] = {
                "config": config,
                "generated_configs": mock_configs,
                "timestamp": datetime.now().isoformat()
            }
            
            return BridgeDomainResult(
                success=True,
                configs=mock_configs,
                service_name=config.service_name,
                vlan_id=config.vlan_id
            )
            
        except Exception as e:
            self.logger.error(f"Mock: Error building bridge domain: {e}")
            return BridgeDomainResult(
                success=False,
                error_message=str(e),
                service_name=config.service_name,
                vlan_id=config.vlan_id
            )
    
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """Mock implementation of getting available sources"""
        # Return only leaf devices as sources
        return [
            device for device in self._mock_devices.values()
            if device["device_type"] == "leaf"
        ]
    
    def get_available_destinations(self, source_device: str) -> List[Dict[str, Any]]:
        """Mock implementation of getting available destinations"""
        # Return all devices except the source
        return [
            device for name, device in self._mock_devices.items()
            if name != source_device
        ]
    
    def validate_configuration(self, config: BridgeDomainConfig) -> Tuple[bool, List[str]]:
        """Mock implementation of configuration validation"""
        errors = []
        
        # Basic validation
        if not config.service_name:
            errors.append("Service name is required")
        
        if config.vlan_id < 1 or config.vlan_id > 4094:
            errors.append("VLAN ID must be between 1 and 4094")
        
        if not config.source_device:
            errors.append("Source device is required")
        
        if not config.destination_device:
            errors.append("Destination device is required")
        
        if config.source_device == config.destination_device:
            errors.append("Source and destination devices must be different")
        
        # Check if devices exist
        if config.source_device not in self._mock_devices:
            errors.append(f"Source device '{config.source_device}' not found")
        
        if config.destination_device not in self._mock_devices:
            errors.append(f"Destination device '{config.destination_device}' not found")
        
        return len(errors) == 0, errors
    
    def get_bridge_domain_status(self, service_name: str) -> Dict[str, Any]:
        """Mock implementation of getting bridge domain status"""
        if service_name in self._mock_configs:
            config_data = self._mock_configs[service_name]
            return {
                "service_name": service_name,
                "status": "active",
                "created_at": config_data["timestamp"],
                "config": config_data["config"].__dict__,
                "generated_configs": config_data["generated_configs"]
            }
        else:
            return {
                "service_name": service_name,
                "status": "not_found",
                "error": "Service not found"
            }
    
    def delete_bridge_domain(self, service_name: str) -> BridgeDomainResult:
        """Mock implementation of deleting bridge domain"""
        if service_name in self._mock_configs:
            deleted_config = self._mock_configs.pop(service_name)
            return BridgeDomainResult(
                success=True,
                service_name=service_name,
                vlan_id=deleted_config["config"].vlan_id
            )
        else:
            return BridgeDomainResult(
                success=False,
                error_message=f"Service '{service_name}' not found",
                service_name=service_name
            )
    
    def list_bridge_domains(self) -> List[Dict[str, Any]]:
        """Mock implementation of listing bridge domains"""
        return [
            {
                "service_name": name,
                "vlan_id": config["config"].vlan_id,
                "source_device": config["config"].source_device,
                "destination_device": config["config"].destination_device,
                "created_at": config["timestamp"],
                "status": "active"
            }
            for name, config in self._mock_configs.items()
        ]
