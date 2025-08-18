#!/usr/bin/env python3
"""
Bridge Domain Service Interface
Abstract base class defining the contract for bridge domain operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class BridgeDomainConfig:
    """Configuration data for building bridge domains"""
    service_name: str
    vlan_id: int
    source_device: str
    source_port: str
    destination_device: str
    destination_port: str
    topology_type: str = "p2p"  # p2p or p2mp
    superspine_support: bool = False


@dataclass
class BridgeDomainResult:
    """Result of bridge domain operations"""
    success: bool
    configs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    service_name: Optional[str] = None
    vlan_id: Optional[int] = None


class BridgeDomainService(ABC):
    """
    Abstract base class for bridge domain services.
    
    This interface defines the contract that all bridge domain services
    must implement, ensuring consistency across different implementations.
    """
    
    @abstractmethod
    def build_bridge_domain(self, config: BridgeDomainConfig) -> BridgeDomainResult:
        """
        Build a bridge domain configuration based on the provided config.
        
        Args:
            config: BridgeDomainConfig containing all necessary parameters
            
        Returns:
            BridgeDomainResult with success status and generated configs
        """
        pass
    
    @abstractmethod
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of available source devices for bridge domain creation.
        
        Returns:
            List of device dictionaries with name and type information
        """
        pass
    
    @abstractmethod
    def get_available_destinations(self, source_device: str) -> List[Dict[str, Any]]:
        """
        Get list of available destination devices for a given source.
        
        Args:
            source_device: Name of the source device
            
        Returns:
            List of device dictionaries with name and type information
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: BridgeDomainConfig) -> Tuple[bool, List[str]]:
        """
        Validate bridge domain configuration before building.
        
        Args:
            config: BridgeDomainConfig to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def get_bridge_domain_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get current status of a bridge domain service.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            Dictionary containing status information
        """
        pass
    
    @abstractmethod
    def delete_bridge_domain(self, service_name: str) -> BridgeDomainResult:
        """
        Delete/remove a bridge domain configuration.
        
        Args:
            service_name: Name of the service to delete
            
        Returns:
            BridgeDomainResult indicating success/failure
        """
        pass
    
    @abstractmethod
    def list_bridge_domains(self) -> List[Dict[str, Any]]:
        """
        List all existing bridge domains.
        
        Returns:
            List of bridge domain information dictionaries
        """
        pass
