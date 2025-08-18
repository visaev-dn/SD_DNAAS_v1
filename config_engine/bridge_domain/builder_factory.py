#!/usr/bin/env python3
"""
Bridge Domain Builder Factory
Factory for creating appropriate bridge domain builders
"""

from typing import Dict, Type, Optional, List, Any
from enum import Enum

from .base_builder import BaseBridgeDomainBuilder, BridgeDomainConfig
from .p2p_builder import P2PBridgeDomainBuilder
from .p2mp_builder import P2MPBridgeDomainBuilder
from core.logging import get_logger
from core.exceptions import BusinessLogicError


class TopologyType(Enum):
    """Supported topology types"""
    P2P = "p2p"
    P2MP = "p2mp"


class BuilderFactory:
    """
    Factory for creating bridge domain builders.
    
    This factory determines the appropriate builder based on topology type
    and other requirements, ensuring the correct builder is used for each use case.
    """
    
    def __init__(self):
        """Initialize the builder factory"""
        self.logger = get_logger(__name__)
        self._builders: Dict[TopologyType, Type[BaseBridgeDomainBuilder]] = {
            TopologyType.P2P: P2PBridgeDomainBuilder,
            TopologyType.P2MP: P2MPBridgeDomainBuilder
        }
        self.logger.info("Bridge Domain Builder Factory initialized")
    
    def create_builder(self, 
                      topology_type: str, 
                      superspine_support: bool = False,
                      topology_dir: str = "topology") -> BaseBridgeDomainBuilder:
        """
        Create a bridge domain builder based on topology type and requirements.
        
        Args:
            topology_type: Type of topology ("p2p" or "p2mp")
            superspine_support: Whether superspine support is required
            topology_dir: Directory containing topology files
            
        Returns:
            Appropriate bridge domain builder instance
            
        Raises:
            BusinessLogicError: If topology type is not supported
        """
        try:
            # Normalize topology type
            topology_type = topology_type.lower()
            
            # Validate topology type
            if topology_type not in [t.value for t in TopologyType]:
                raise BusinessLogicError(f"Unsupported topology type: {topology_type}")
            
            # Convert to enum
            topology_enum = TopologyType(topology_type)
            
            # Get builder class
            builder_class = self._builders.get(topology_enum)
            if not builder_class:
                raise BusinessLogicError(f"No builder available for topology type: {topology_type}")
            
            # Validate superspine support
            if superspine_support and topology_type == "p2p":
                raise BusinessLogicError("P2P topology does not support superspine devices")
            
            # Create builder instance
            builder = builder_class(topology_dir)
            
            self.logger.info(f"Created {builder_class.__name__} for {topology_type} topology")
            
            return builder
            
        except Exception as e:
            self.logger.error(f"Failed to create builder for {topology_type}: {e}")
            raise BusinessLogicError(f"Builder creation failed: {e}")
    
    def get_available_topologies(self) -> List[str]:
        """Get list of available topology types"""
        return [t.value for t in TopologyType]
    
    def get_builder_capabilities(self, topology_type: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific builder type.
        
        Args:
            topology_type: Type of topology to get capabilities for
            
        Returns:
            Dictionary containing builder capabilities
        """
        try:
            builder = self.create_builder(topology_type)
            return {
                "topology_type": topology_type,
                "capabilities": builder.get_capabilities(),
                "supported_topologies": builder.get_supported_topologies(),
                "builder_info": builder.get_builder_info()
            }
        except Exception as e:
            self.logger.error(f"Failed to get capabilities for {topology_type}: {e}")
            return {
                "topology_type": topology_type,
                "error": str(e)
            }
    
    def get_all_builder_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all available builders"""
        capabilities = {}
        
        for topology_type in self.get_available_topologies():
            capabilities[topology_type] = self.get_builder_capabilities(topology_type)
        
        return capabilities
    
    def validate_topology_requirements(self, 
                                    topology_type: str, 
                                    source_device: str,
                                    destination_device: str,
                                    superspine_support: bool = False) -> Dict[str, Any]:
        """
        Validate if a topology type meets the requirements for given devices.
        
        Args:
            topology_type: Type of topology to validate
            source_device: Source device name
            destination_device: Destination device name
            superspine_support: Whether superspine support is required
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Create builder to get validation logic
            builder = self.create_builder(topology_type, superspine_support)
            
            # Create test configuration
            test_config = BridgeDomainConfig(
                service_name="validation_test",
                vlan_id=100,
                source_device=source_device,
                source_port="test_port",
                destination_device=destination_device,
                destination_port="test_port",
                topology_type=topology_type,
                superspine_support=superspine_support
            )
            
            # Validate configuration
            is_valid, errors = builder.validate_configuration(test_config)
            
            # Get additional topology-specific validation
            if hasattr(builder, '_validate_p2mp_specific_rules') and topology_type == "p2mp":
                p2mp_errors = builder._validate_p2mp_specific_rules(test_config)
                errors.extend(p2mp_errors)
                is_valid = is_valid and len(p2mp_errors) == 0
            
            return {
                "topology_type": topology_type,
                "is_valid": is_valid,
                "errors": errors,
                "source_device": source_device,
                "destination_device": destination_device,
                "superspine_support": superspine_support
            }
            
        except Exception as e:
            return {
                "topology_type": topology_type,
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "source_device": source_device,
                "destination_device": destination_device,
                "superspine_support": superspine_support
            }
    
    def get_recommended_topology(self, 
                               source_device: str,
                               destination_device: str,
                               requirements: Dict[str, Any]) -> str:
        """
        Get recommended topology type based on requirements and devices.
        
        Args:
            source_device: Source device name
            destination_device: Destination device name
            requirements: Dictionary of requirements (superspine_support, complexity, etc.)
            
        Returns:
            Recommended topology type
        """
        try:
            superspine_support = requirements.get('superspine_support', False)
            complexity = requirements.get('complexity', 'simple')
            
            # Simple requirements -> P2P
            if not superspine_support and complexity == 'simple':
                return "p2p"
            
            # Complex requirements or superspine support -> P2MP
            if superspine_support or complexity == 'complex':
                return "p2mp"
            
            # Default to P2P for simple cases
            return "p2p"
            
        except Exception as e:
            self.logger.error(f"Failed to get recommended topology: {e}")
            return "p2p"  # Default fallback
    
    def register_builder(self, topology_type: str, builder_class: Type[BaseBridgeDomainBuilder]) -> None:
        """
        Register a custom builder for a topology type.
        
        Args:
            topology_type: Topology type to register builder for
            builder_class: Builder class to register
        """
        try:
            # Validate that the builder class inherits from BaseBridgeDomainBuilder
            if not issubclass(builder_class, BaseBridgeDomainBuilder):
                raise BusinessLogicError("Builder class must inherit from BaseBridgeDomainBuilder")
            
            # Add to builders dictionary
            self._builders[TopologyType(topology_type)] = builder_class
            
            self.logger.info(f"Registered custom builder {builder_class.__name__} for {topology_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to register builder for {topology_type}: {e}")
            raise BusinessLogicError(f"Builder registration failed: {e}")


# Global factory instance
_builder_factory: Optional[BuilderFactory] = None


def get_builder_factory() -> BuilderFactory:
    """Get global builder factory instance"""
    global _builder_factory
    if _builder_factory is None:
        _builder_factory = BuilderFactory()
    return _builder_factory


def create_bridge_domain_builder(topology_type: str, 
                               superspine_support: bool = False,
                               topology_dir: str = "topology") -> BaseBridgeDomainBuilder:
    """
    Convenience function to create a bridge domain builder.
    
    Args:
        topology_type: Type of topology ("p2p" or "p2mp")
        superspine_support: Whether superspine support is required
        topology_dir: Directory containing topology files
        
    Returns:
        Appropriate bridge domain builder instance
    """
    return get_builder_factory().create_builder(topology_type, superspine_support, topology_dir)
