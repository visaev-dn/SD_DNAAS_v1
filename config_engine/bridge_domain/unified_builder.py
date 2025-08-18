#!/usr/bin/env python3
"""
Unified Bridge Domain Builder
Main facade for all bridge domain operations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_builder import BaseBridgeDomainBuilder, BridgeDomainConfig, BridgeDomainResult
from .builder_factory import get_builder_factory, create_bridge_domain_builder
from core.logging import get_logger
from core.exceptions import BusinessLogicError


class UnifiedBridgeDomainBuilder:
    """
    Unified bridge domain builder that serves as the main facade.
    
    This class provides a single interface for all bridge domain operations,
    automatically selecting the appropriate builder based on topology requirements.
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize the unified builder.
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = topology_dir
        self.logger = get_logger(__name__)
        self.factory = get_builder_factory()
        self.logger.info("Unified Bridge Domain Builder initialized")
    
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """
        Build a bridge domain configuration using the appropriate builder.
        
        Args:
            config: BridgeDomainConfig containing all necessary parameters
            
        Returns:
            BridgeDomainResult with success status and generated configs
        """
        try:
            self.logger.info(f"Building bridge domain: {config.service_name}")
            
            # Determine topology type if not specified
            if not config.topology_type:
                config.topology_type = self._determine_topology_type(config)
            
            # Create appropriate builder
            builder = create_bridge_domain_builder(
                config.topology_type,
                config.superspine_support,
                self.topology_dir
            )
            
            # Build bridge domain using the selected builder
            result = builder.build_bridge_domain(config)
            
            # Add unified builder metadata
            if result.success and result.metadata:
                result.metadata["unified_builder"] = True
                result.metadata["builder_factory_used"] = builder.__class__.__name__
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to build bridge domain {config.service_name}: {e}")
            return BridgeDomainResult(
                success=False,
                error_message=str(e),
                service_name=config.service_name,
                vlan_id=config.vlan_id
            )
    
    def _determine_topology_type(self, config: BridgeDomainConfig) -> str:
        """
        Automatically determine the appropriate topology type.
        
        Args:
            config: BridgeDomainConfig to analyze
            
        Returns:
            Recommended topology type
        """
        requirements = {
            'superspine_support': config.superspine_support,
            'complexity': 'simple'  # Default to simple
        }
        
        # Check if destination is superspine
        if self._is_superspine_device(config.destination_device):
            requirements['superspine_support'] = True
            requirements['complexity'] = 'complex'
        
        # Check if source is superspine
        if self._is_superspine_device(config.source_device):
            requirements['complexity'] = 'complex'
        
        # Get recommendation from factory
        return self.factory.get_recommended_topology(
            config.source_device,
            config.destination_device,
            requirements
        )
    
    def _is_superspine_device(self, device_name: str) -> bool:
        """
        Check if a device is a superspine device.
        
        Args:
            device_name: Device name to check
            
        Returns:
            True if device is superspine, False otherwise
        """
        # This would be implemented based on actual topology data
        # For now, use a simple naming convention
        return "superspine" in device_name.lower()
    
    def get_available_sources(self, topology_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available source devices for the specified topology type.
        
        Args:
            topology_type: Optional topology type to filter by
            
        Returns:
            List of available source devices
        """
        try:
            if topology_type:
                # Get sources for specific topology type
                builder = create_bridge_domain_builder(topology_type, False, self.topology_dir)
                return builder.get_available_sources()
            else:
                # Get all available sources from all topology types
                all_sources = {}
                
                for topo_type in self.factory.get_available_topologies():
                    builder = create_bridge_domain_builder(topo_type, False, self.topology_dir)
                    sources = builder.get_available_sources()
                    
                    for source in sources:
                        source_name = source["name"]
                        if source_name not in all_sources:
                            all_sources[source_name] = source
                            all_sources[source_name]["supported_topologies"] = []
                        
                        all_sources[source_name]["supported_topologies"].append(topo_type)
                
                return list(all_sources.values())
                
        except Exception as e:
            self.logger.error(f"Failed to get available sources: {e}")
            return []
    
    def get_available_destinations(self, 
                                 source_device: str, 
                                 topology_type: Optional[str] = None,
                                 superspine_support: bool = False) -> List[Dict[str, Any]]:
        """
        Get available destination devices for a given source.
        
        Args:
            source_device: Source device name
            topology_type: Optional topology type to filter by
            superspine_support: Whether superspine support is required
            
        Returns:
            List of available destination devices
        """
        try:
            if topology_type:
                # Get destinations for specific topology type
                builder = create_bridge_domain_builder(topology_type, superspine_support, self.topology_dir)
                return builder.get_available_destinations(source_device)
            else:
                # Get all available destinations from all topology types
                all_destinations = {}
                
                for topo_type in self.factory.get_available_topologies():
                    # Skip P2P if superspine support is required
                    if superspine_support and topo_type == "p2p":
                        continue
                    
                    builder = create_bridge_domain_builder(topo_type, superspine_support, self.topology_dir)
                    destinations = builder.get_available_destinations(source_device)
                    
                    for dest in destinations:
                        dest_name = dest["name"]
                        if dest_name not in all_destinations:
                            all_destinations[dest_name] = dest
                            all_destinations[dest_name]["supported_topologies"] = []
                        
                        all_destinations[dest_name]["supported_topologies"].append(topo_type)
                
                return list(all_destinations.values())
                
        except Exception as e:
            self.logger.error(f"Failed to get available destinations: {e}")
            return []
    
    def validate_configuration(self, config: BridgeDomainConfig) -> Dict[str, Any]:
        """
        Validate bridge domain configuration for all topology types.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            Dictionary containing validation results for all topology types
        """
        try:
            validation_results = {}
            
            # Validate for each topology type
            for topology_type in self.factory.get_available_topologies():
                # Skip P2P if superspine support is required
                if config.superspine_support and topology_type == "p2p":
                    validation_results[topology_type] = {
                        "is_valid": False,
                        "errors": ["P2P topology does not support superspine devices"]
                    }
                    continue
                
                # Get validation result for this topology type
                result = self.factory.validate_topology_requirements(
                    topology_type,
                    config.source_device,
                    config.destination_device,
                    config.superspine_support
                )
                
                validation_results[topology_type] = result
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return {
                "error": f"Validation failed: {str(e)}"
            }
    
    def get_builder_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all available builders"""
        return self.factory.get_all_builder_capabilities()
    
    def get_recommended_topology(self, 
                               source_device: str,
                               destination_device: str,
                               requirements: Dict[str, Any]) -> str:
        """
        Get recommended topology type based on requirements and devices.
        
        Args:
            source_device: Source device name
            destination_device: Destination device name
            requirements: Dictionary of requirements
            
        Returns:
            Recommended topology type
        """
        return self.factory.get_recommended_topology(source_device, destination_device, requirements)
    
    def create_simple_p2p_config(self, 
                               service_name: str,
                               vlan_id: int,
                               source_device: str,
                               source_port: str,
                               destination_device: str,
                               destination_port: str) -> BridgeDomainConfig:
        """
        Create a simple P2P configuration.
        
        Args:
            service_name: Name of the service
            vlan_id: VLAN ID for the service
            source_device: Source device name
            source_port: Source port
            destination_device: Destination device name
            destination_port: Destination port
            
        Returns:
            BridgeDomainConfig for P2P topology
        """
        return BridgeDomainConfig(
            service_name=service_name,
            vlan_id=vlan_id,
            source_device=source_device,
            source_port=source_port,
            destination_device=destination_device,
            destination_port=destination_port,
            topology_type="p2p",
            superspine_support=False
        )
    
    def create_p2mp_config(self, 
                          service_name: str,
                          vlan_id: int,
                          source_device: str,
                          source_port: str,
                          destination_device: str,
                          destination_port: str,
                          superspine_support: bool = False) -> BridgeDomainConfig:
        """
        Create a P2MP configuration.
        
        Args:
            service_name: Name of the service
            vlan_id: VLAN ID for the service
            source_device: Source device name
            source_port: Source port
            destination_device: Destination device name
            destination_port: Destination port
            superspine_support: Whether superspine support is required
            
        Returns:
            BridgeDomainConfig for P2MP topology
        """
        return BridgeDomainConfig(
            service_name=service_name,
            vlan_id=vlan_id,
            source_device=source_device,
            source_port=source_port,
            destination_device=destination_device,
            destination_port=destination_port,
            topology_type="p2mp",
            superspine_support=superspine_support
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about all builders"""
        try:
            stats = {
                "total_builders": len(self.factory.get_available_topologies()),
                "available_topologies": self.factory.get_available_topologies(),
                "builder_capabilities": self.get_builder_capabilities()
            }
            
            # Add statistics from individual builders
            for topology_type in self.factory.get_available_topologies():
                try:
                    builder = create_bridge_domain_builder(topology_type, False, self.topology_dir)
                    
                    if hasattr(builder, 'get_p2p_statistics'):
                        stats[f"{topology_type}_statistics"] = builder.get_p2p_statistics()
                    elif hasattr(builder, 'get_p2mp_statistics'):
                        stats[f"{topology_type}_statistics"] = builder.get_p2mp_statistics()
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get statistics for {topology_type}: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
