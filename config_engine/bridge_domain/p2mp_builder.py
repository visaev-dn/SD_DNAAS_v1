#!/usr/bin/env python3
"""
P2MP Bridge Domain Builder
Point-to-multipoint bridge domain configuration builder with superspine support
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_builder import BaseBridgeDomainBuilder, BridgeDomainConfig, BridgeDomainResult
from core.logging import get_logger
from core.exceptions import BusinessLogicError


class P2MPBridgeDomainBuilder(BaseBridgeDomainBuilder):
    """
    Point-to-multipoint bridge domain builder.
    
    This builder creates point-to-multipoint bridge domain configurations
    that can include superspine devices as destinations.
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """Initialize P2MP builder"""
        super().__init__(topology_dir)
        self.logger = get_logger(__name__)
        self.logger.info("P2MP Bridge Domain Builder initialized")
    
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """
        Build a point-to-multipoint bridge domain configuration.
        
        Args:
            config: BridgeDomainConfig containing P2MP parameters
            
        Returns:
            BridgeDomainResult with generated P2MP configuration
        """
        try:
            self.logger.info(f"Building P2MP bridge domain: {config.service_name}")
            
            # Validate configuration
            is_valid, errors = self.validate_configuration(config)
            if not is_valid:
                return BridgeDomainResult(
                    success=False,
                    error_message=f"P2MP configuration validation failed: {', '.join(errors)}",
                    service_name=config.service_name,
                    vlan_id=config.vlan_id
                )
            
            # Additional P2MP-specific validation
            p2mp_errors = self._validate_p2mp_specific_rules(config)
            if p2mp_errors:
                return BridgeDomainResult(
                    success=False,
                    error_message=f"P2MP-specific validation failed: {', '.join(p2mp_errors)}",
                    service_name=config.service_name,
                    vlan_id=config.vlan_id
                )
            
            # Generate P2MP configuration
            configs = self._generate_p2mp_config(config)
            
            self.logger.info(f"P2MP bridge domain {config.service_name} built successfully")
            
            return BridgeDomainResult(
                success=True,
                configs=configs,
                service_name=config.service_name,
                vlan_id=config.vlan_id,
                topology_type="p2mp",
                metadata={
                    "builder_type": "P2MP",
                    "created_at": datetime.now().isoformat(),
                    "source_device": config.source_device,
                    "destination_device": config.destination_device,
                    "superspine_support": config.superspine_support
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build P2MP bridge domain {config.service_name}: {e}")
            return BridgeDomainResult(
                success=False,
                error_message=str(e),
                service_name=config.service_name,
                vlan_id=config.vlan_id
            )
    
    def _generate_p2mp_config(self, config: BridgeDomainConfig) -> Dict[str, Any]:
        """
        Generate P2MP configuration for source and destination devices.
        
        Args:
            config: BridgeDomainConfig for P2MP topology
            
        Returns:
            Dictionary containing device configurations
        """
        configs = {}
        
        # Source device configuration (always leaf)
        source_config = {
            "device_name": config.source_device,
            "interface": config.source_port,
            "vlan": config.vlan_id,
            "service": config.service_name,
            "topology_type": "p2mp",
            "config_type": "access",
            "vlan_mode": "access",
            "multipoint": True
        }
        configs[config.source_device] = source_config
        
        # Destination device configuration
        dest_device_type = self.get_device_type(config.destination_device)
        
        if dest_device_type == "superspine":
            # Superspine destination - transport only, no AC interface
            dest_config = {
                "device_name": config.destination_device,
                "interface": config.destination_port,
                "vlan": config.vlan_id,
                "service": config.service_name,
                "topology_type": "p2mp",
                "config_type": "transport",
                "vlan_mode": "trunk",
                "multipoint": True,
                "transport_only": True,
                "no_ac_interface": True
            }
        else:
            # Regular destination (leaf/spine)
            dest_config = {
                "device_name": config.destination_device,
                "interface": config.destination_port,
                "vlan": config.vlan_id,
                "service": config.service_name,
                "topology_type": "p2mp",
                "config_type": "access",
                "vlan_mode": "access",
                "multipoint": True
            }
        
        configs[config.destination_device] = dest_config
        
        return configs
    
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get available source devices for P2MP topology"""
        # In P2MP, sources are typically leaf devices
        return [
            {"name": "leaf1", "device_type": "leaf", "capabilities": ["p2mp"]},
            {"name": "leaf2", "device_type": "leaf", "capabilities": ["p2mp"]},
            {"name": "leaf3", "device_type": "leaf", "capabilities": ["p2mp"]}
        ]
    
    def get_available_destinations(self, source_device: str) -> List[Dict[str, Any]]:
        """Get available destination devices for P2MP topology"""
        # In P2MP, destinations can be leafs, spines, or superspines
        available_devices = [
            {"name": "leaf1", "device_type": "leaf", "capabilities": ["p2mp"]},
            {"name": "leaf2", "device_type": "leaf", "capabilities": ["p2mp"]},
            {"name": "leaf3", "device_type": "leaf", "capabilities": ["p2mp"]},
            {"name": "spine1", "device_type": "spine", "capabilities": ["p2mp"]},
            {"name": "spine2", "device_type": "spine", "capabilities": ["p2mp"]},
            {"name": "superspine1", "device_type": "superspine", "capabilities": ["p2mp", "transport_only"]},
            {"name": "superspine2", "device_type": "superspine", "capabilities": ["p2mp", "transport_only"]}
        ]
        
        # Filter out the source device
        destinations = [
            device for device in available_devices
            if device["name"] != source_device
        ]
        
        return destinations
    
    def get_supported_topologies(self) -> List[str]:
        """Get supported topology types for P2MP builder"""
        return ["p2mp"]
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities of P2MP builder"""
        return [
            "point_to_multipoint",
            "complex_topology",
            "superspine_support",
            "transport_interfaces",
            "multipoint_vlans",
            "leaf_to_spine",
            "leaf_to_superspine"
        ]
    
    def _validate_p2mp_specific_rules(self, config: BridgeDomainConfig) -> List[str]:
        """
        Validate P2MP-specific business rules.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            List of P2MP-specific validation errors
        """
        errors = []
        
        # P2MP specific validations
        if config.topology_type != "p2mp":
            errors.append("P2MP builder only supports 'p2mp' topology type")
        
        # Check if source device is appropriate for P2MP
        source_type = self.get_device_type(config.source_device)
        if source_type not in ["leaf", "access"]:
            errors.append(f"Source device must be a leaf/access device, got: {source_type}")
        
        # Check destination device type
        dest_type = self.get_device_type(config.destination_device)
        if dest_type not in ["leaf", "spine", "superspine"]:
            errors.append(f"Destination device must be leaf, spine, or superspine, got: {dest_type}")
        
        # Validate superspine usage
        if dest_type == "superspine":
            if not config.superspine_support:
                errors.append("Superspine destination requires superspine_support=True")
            
            # Check for superspine-to-superspine (not allowed)
            if source_type == "superspine":
                errors.append("Superspine-to-superspine topologies are not supported")
        
        return errors
    
    def get_p2mp_statistics(self) -> Dict[str, Any]:
        """Get P2MP-specific statistics"""
        return {
            "total_p2mp_services": len(self.list_bridge_domains()),
            "supported_device_types": ["leaf", "spine", "superspine"],
            "max_vlans_per_device": 4094,
            "topology_complexity": "complex",
            "superspine_support": True
        }
    
    def get_path_calculation(self, source: str, destination: str) -> List[str]:
        """
        Calculate path between source and destination for P2MP topology.
        
        Args:
            source: Source device name
            destination: Destination device name
            
        Returns:
            List of devices in the path
        """
        try:
            # This would implement actual path calculation logic
            # For now, return a simple path
            source_type = self.get_device_type(source)
            dest_type = self.get_device_type(destination)
            
            if dest_type == "superspine":
                # Path: leaf -> spine -> superspine
                return [source, "spine1", destination]
            elif dest_type == "spine":
                # Path: leaf -> spine
                return [source, destination]
            else:
                # Path: leaf -> leaf (through spine)
                return [source, "spine1", destination]
                
        except Exception as e:
            self.logger.error(f"Path calculation failed: {e}")
            return []
    
    def validate_superspine_constraints(self, config: BridgeDomainConfig) -> List[str]:
        """
        Validate superspine-specific constraints.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            List of superspine constraint validation errors
        """
        errors = []
        
        dest_type = self.get_device_type(config.destination_device)
        
        if dest_type == "superspine":
            # Superspine destinations cannot have AC interfaces
            if "ac_interface" in config.additional_config or config.additional_config:
                errors.append("Superspine destinations cannot have AC interfaces")
            
            # Check if superspine is available for this service
            available_superspines = [
                device for device in self.get_available_destinations(config.source_device)
                if device["device_type"] == "superspine"
            ]
            
            if not available_superspines:
                errors.append("No superspine devices available for this topology")
        
        return errors
