#!/usr/bin/env python3
"""
P2P Bridge Domain Builder
Point-to-point bridge domain configuration builder
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_builder import BaseBridgeDomainBuilder, BridgeDomainConfig, BridgeDomainResult
from core.logging import get_logger


class P2PBridgeDomainBuilder(BaseBridgeDomainBuilder):
    """
    Point-to-point bridge domain builder.
    
    This builder creates simple point-to-point bridge domain configurations
    between two devices (typically leaf switches).
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """Initialize P2P builder"""
        super().__init__(topology_dir)
        self.logger = get_logger(__name__)
        self.logger.info("P2P Bridge Domain Builder initialized")
    
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """
        Build a point-to-point bridge domain configuration.
        
        Args:
            config: BridgeDomainConfig containing P2P parameters
            
        Returns:
            BridgeDomainResult with generated P2P configuration
        """
        try:
            self.logger.info(f"Building P2P bridge domain: {config.service_name}")
            
            # Validate configuration
            is_valid, errors = self.validate_configuration(config)
            if not is_valid:
                return BridgeDomainResult(
                    success=False,
                    error_message=f"P2P configuration validation failed: {', '.join(errors)}",
                    service_name=config.service_name,
                    vlan_id=config.vlan_id
                )
            
            # Generate P2P configuration
            configs = self._generate_p2p_config(config)
            
            self.logger.info(f"P2P bridge domain {config.service_name} built successfully")
            
            return BridgeDomainResult(
                success=True,
                configs=configs,
                service_name=config.service_name,
                vlan_id=config.vlan_id,
                topology_type="p2p",
                metadata={
                    "builder_type": "P2P",
                    "created_at": datetime.now().isoformat(),
                    "source_device": config.source_device,
                    "destination_device": config.destination_device
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build P2P bridge domain {config.service_name}: {e}")
            return BridgeDomainResult(
                success=False,
                error_message=str(e),
                service_name=config.service_name,
                vlan_id=config.vlan_id
            )
    
    def _generate_p2p_config(self, config: BridgeDomainConfig) -> Dict[str, Any]:
        """
        Generate P2P configuration for source and destination devices.
        
        Args:
            config: BridgeDomainConfig for P2P topology
            
        Returns:
            Dictionary containing device configurations
        """
        # Source device configuration
        source_config = {
            "device_name": config.source_device,
            "interface": config.source_port,
            "vlan": config.vlan_id,
            "service": config.service_name,
            "topology_type": "p2p",
            "peer_device": config.destination_device,
            "peer_interface": config.destination_port,
            "config_type": "access",
            "vlan_mode": "access"
        }
        
        # Destination device configuration
        destination_config = {
            "device_name": config.destination_device,
            "interface": config.destination_port,
            "vlan": config.vlan_id,
            "service": config.service_name,
            "topology_type": "p2p",
            "peer_device": config.source_device,
            "peer_interface": config.source_port,
            "config_type": "access",
            "vlan_mode": "access"
        }
        
        return {
            config.source_device: source_config,
            config.destination_device: destination_config
        }
    
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get available source devices for P2P topology"""
        # In P2P, sources are typically leaf devices
        # This would be implemented based on actual topology data
        return [
            {"name": "leaf1", "device_type": "leaf", "capabilities": ["p2p"]},
            {"name": "leaf2", "device_type": "leaf", "capabilities": ["p2p"]},
            {"name": "leaf3", "device_type": "leaf", "capabilities": ["p2p"]}
        ]
    
    def get_available_destinations(self, source_device: str) -> List[Dict[str, Any]]:
        """Get available destination devices for P2P topology"""
        # In P2P, destinations are other leaf devices (excluding source)
        available_devices = self.get_available_sources()
        
        # Filter out the source device
        destinations = [
            device for device in available_devices
            if device["name"] != source_device
        ]
        
        return destinations
    
    def get_supported_topologies(self) -> List[str]:
        """Get supported topology types for P2P builder"""
        return ["p2p"]
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities of P2P builder"""
        return [
            "point_to_point",
            "simple_topology",
            "leaf_to_leaf",
            "access_ports",
            "single_vlan"
        ]
    
    def validate_p2p_specific_rules(self, config: BridgeDomainConfig) -> List[str]:
        """
        Validate P2P-specific business rules.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            List of P2P-specific validation errors
        """
        errors = []
        
        # P2P specific validations
        if config.topology_type != "p2p":
            errors.append("P2P builder only supports 'p2p' topology type")
        
        # Check if devices are of appropriate type for P2P
        source_type = self.get_device_type(config.source_device)
        dest_type = self.get_device_type(config.destination_device)
        
        if source_type not in ["leaf", "access"]:
            errors.append(f"Source device must be a leaf/access device, got: {source_type}")
        
        if dest_type not in ["leaf", "access"]:
            errors.append(f"Destination device must be a leaf/access device, got: {dest_type}")
        
        # Check for superspine usage (not allowed in P2P)
        if config.superspine_support:
            errors.append("P2P topology does not support superspine devices")
        
        return errors
    
    def get_p2p_statistics(self) -> Dict[str, Any]:
        """Get P2P-specific statistics"""
        return {
            "total_p2p_services": len(self.list_bridge_domains()),
            "supported_device_types": ["leaf", "access"],
            "max_vlans_per_device": 4094,
            "topology_complexity": "simple"
        }
