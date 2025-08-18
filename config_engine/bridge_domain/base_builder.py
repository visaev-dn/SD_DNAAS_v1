#!/usr/bin/env python3
"""
Base Bridge Domain Builder
Abstract base class for all bridge domain builders
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from core.logging import get_logger
from core.exceptions import ValidationError, BusinessLogicError
from core.validation import validate_bridge_domain_config


@dataclass
class BridgeDomainConfig:
    """Configuration for building bridge domains"""
    service_name: str
    vlan_id: int
    source_device: str
    source_port: str
    destination_device: str
    destination_port: str
    topology_type: str = "p2p"  # p2p, p2mp
    superspine_support: bool = False
    additional_config: Optional[Dict[str, Any]] = None


@dataclass
class BridgeDomainResult:
    """Result of bridge domain building operation"""
    success: bool
    configs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    service_name: Optional[str] = None
    vlan_id: Optional[int] = None
    topology_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseBridgeDomainBuilder(ABC):
    """
    Abstract base class for all bridge domain builders.
    
    This class provides common functionality and enforces the interface
    that all bridge domain builders must implement.
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize the base builder.
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = topology_dir
        self.logger = get_logger(__name__)
        self.topology_data = {}
        self.bundle_mappings = {}
        
        # Load topology data
        self._load_topology_data()
    
    def _load_topology_data(self) -> None:
        """Load topology data from files"""
        try:
            # This would load topology data from files
            # For now, we'll use placeholder data
            self.topology_data = {}
            self.bundle_mappings = {}
            self.logger.info("Topology data loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load topology data: {e}")
            raise
    
    @abstractmethod
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """
        Build a bridge domain configuration.
        
        Args:
            config: BridgeDomainConfig containing all necessary parameters
            
        Returns:
            BridgeDomainResult with success status and generated configs
        """
        pass
    
    @abstractmethod
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of available source devices.
        
        Returns:
            List of device info dictionaries
        """
        pass
    
    @abstractmethod
    def get_available_destinations(self, source_device: str) -> List[Dict[str, Any]]:
        """
        Get list of available destination devices for a given source.
        
        Args:
            source_device: Source device name
            
        Returns:
            List of device info dictionaries
        """
        pass
    
    def validate_configuration(self, config: BridgeDomainConfig) -> Tuple[bool, List[str]]:
        """
        Validate bridge domain configuration.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # Convert config to dictionary for validation
            config_dict = {
                'service_name': config.service_name,
                'vlan_id': config.vlan_id,
                'source_device': config.source_device,
                'destination_device': config.destination_device
            }
            
            # Use core validation framework
            validation_result = validate_bridge_domain_config(config_dict)
            
            if not validation_result.is_valid:
                return False, validation_result.errors
            
            # Additional business logic validation
            business_errors = self._validate_business_logic(config)
            if business_errors:
                return False, business_errors
            
            return True, []
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_business_logic(self, config: BridgeDomainConfig) -> List[str]:
        """
        Validate business logic rules.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            List of business logic validation errors
        """
        errors = []
        
        # Check if source and destination are different
        if config.source_device == config.destination_device:
            errors.append("Source and destination devices must be different")
        
        # Check if devices exist in topology
        if config.source_device not in self.topology_data:
            errors.append(f"Source device '{config.source_device}' not found in topology")
        
        if config.destination_device not in self.topology_data:
            errors.append(f"Destination device '{config.destination_device}' not found in topology")
        
        # Check VLAN ID range
        if config.vlan_id < 1 or config.vlan_id > 4094:
            errors.append("VLAN ID must be between 1 and 4094")
        
        # Check topology type
        if config.topology_type not in ["p2p", "p2mp"]:
            errors.append("Topology type must be 'p2p' or 'p2mp'")
        
        return errors
    
    def get_device_type(self, device_name: str) -> str:
        """
        Get device type for a device.
        
        Args:
            device_name: Device name
            
        Returns:
            Device type string
        """
        # This would be implemented based on topology data
        # For now, return a default type
        return "leaf"
    
    def get_device_interfaces(self, device_name: str) -> List[str]:
        """
        Get available interfaces for a device.
        
        Args:
            device_name: Device name
            
        Returns:
            List of interface names
        """
        # This would be implemented based on topology data
        # For now, return placeholder interfaces
        return [f"ge100-0/0/{i}" for i in range(1, 5)]
    
    def get_bridge_domain_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get current status of a bridge domain service.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            Dictionary containing status information
        """
        # This would check the actual status
        # For now, return placeholder status
        return {
            "service_name": service_name,
            "status": "unknown",
            "created_at": None,
            "last_modified": None
        }
    
    def delete_bridge_domain(self, service_name: str) -> BridgeDomainResult:
        """
        Delete/remove a bridge domain configuration.
        
        Args:
            service_name: Name of the service to delete
            
        Returns:
            BridgeDomainResult indicating success/failure
        """
        try:
            # This would implement actual deletion logic
            self.logger.info(f"Deleting bridge domain: {service_name}")
            
            return BridgeDomainResult(
                success=True,
                service_name=service_name,
                metadata={"deleted_at": "now"}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to delete bridge domain {service_name}: {e}")
            return BridgeDomainResult(
                success=False,
                service_name=service_name,
                error_message=str(e)
            )
    
    def list_bridge_domains(self) -> List[Dict[str, Any]]:
        """
        List all existing bridge domains.
        
        Returns:
            List of bridge domain information dictionaries
        """
        # This would return actual bridge domain data
        # For now, return empty list
        return []
    
    def export_configuration(self, service_name: str, format_type: str = "json") -> str:
        """
        Export bridge domain configuration in specified format.
        
        Args:
            service_name: Name of the service to export
            format_type: Export format (json, yaml, etc.)
            
        Returns:
            String representation of exported configuration
        """
        try:
            # This would implement actual export logic
            self.logger.info(f"Exporting configuration for {service_name} in {format_type} format")
            
            # Placeholder export
            return f"Configuration for {service_name} in {format_type} format"
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration for {service_name}: {e}")
            raise BusinessLogicError(f"Export failed: {e}")
    
    def get_builder_info(self) -> Dict[str, Any]:
        """
        Get information about this builder.
        
        Returns:
            Dictionary containing builder information
        """
        return {
            "builder_type": self.__class__.__name__,
            "topology_dir": self.topology_dir,
            "supported_topologies": self.get_supported_topologies(),
            "capabilities": self.get_capabilities()
        }
    
    @abstractmethod
    def get_supported_topologies(self) -> List[str]:
        """
        Get list of supported topology types.
        
        Returns:
            List of supported topology type strings
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of builder capabilities.
        
        Returns:
            List of capability strings
        """
        pass
