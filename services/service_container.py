#!/usr/bin/env python3
"""
Service Container
Dependency injection container for all lab automation services
"""

from typing import Dict, Any, Optional
import logging

from .interfaces import (
    BridgeDomainService,
    TopologyService,
    SSHService,
    DiscoveryService,
    UserWorkflowService
)


class ServiceContainer:
    """
    Dependency injection container for all lab automation services.
    
    This container manages the lifecycle and dependencies of all services,
    providing a centralized way to access service instances.
    """
    
    def __init__(self):
        """Initialize the service container"""
        self._services: Dict[str, Any] = {}
        self._service_factories: Dict[str, callable] = {}
        self._logger = logging.getLogger(__name__)
        
        # Register service factories
        self._register_service_factories()
        
        # Initialize core services
        self._initialize_services()
    
    def _register_service_factories(self) -> None:
        """Register factory functions for creating service instances"""
        # Bridge Domain Service factory
        self._service_factories['bridge_domain'] = self._create_bridge_domain_service
        
        # Topology Service factory
        self._service_factories['topology'] = self._create_topology_service
        
        # SSH Service factory
        self._service_factories['ssh'] = self._create_ssh_service
        
        # Discovery Service factory
        self._service_factories['discovery'] = self._create_discovery_service
        
        # User Workflow Service factory
        self._service_factories['user_workflow'] = self._create_user_workflow_service
    
    def _initialize_services(self) -> None:
        """Initialize all core services"""
        try:
            # Initialize services lazily - they'll be created when first accessed
            self._logger.info("Service container initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize service container: {e}")
            raise
    
    def _create_bridge_domain_service(self) -> BridgeDomainService:
        """Create and return a Bridge Domain Service instance"""
        try:
            # Import here to avoid circular imports
            from .implementations.bridge_domain_service_impl import BridgeDomainServiceImpl
            return BridgeDomainServiceImpl()
        except ImportError:
            self._logger.warning("Bridge Domain Service implementation not available")
            # Return a mock service for now
            from .implementations.mock_bridge_domain_service import MockBridgeDomainService
            return MockBridgeDomainService()
    
    def _create_topology_service(self) -> TopologyService:
        """Create and return a Topology Service instance"""
        try:
            from .implementations.topology_service_impl import TopologyServiceImpl
            return TopologyServiceImpl()
        except ImportError:
            self._logger.warning("Topology Service implementation not available")
            from .implementations.mock_topology_service import MockTopologyService
            return MockTopologyService()
    
    def _create_ssh_service(self) -> SSHService:
        """Create and return an SSH Service instance"""
        try:
            from .implementations.ssh_service_impl import SSHServiceImpl
            return SSHServiceImpl()
        except ImportError:
            self._logger.warning("SSH Service implementation not available")
            from .implementations.mock_ssh_service import MockSSHService
            return MockSSHService()
    
    def _create_discovery_service(self) -> DiscoveryService:
        """Create and return a Discovery Service instance"""
        try:
            from .implementations.discovery_service_impl import DiscoveryServiceImpl
            return DiscoveryServiceImpl()
        except ImportError:
            self._logger.warning("Discovery Service implementation not available")
            from .implementations.mock_discovery_service import MockDiscoveryService
            return MockDiscoveryService()
    
    def _create_user_workflow_service(self) -> UserWorkflowService:
        """Create and return a User Workflow Service instance"""
        try:
            from .implementations.user_workflow_service_impl import UserWorkflowServiceImpl
            return UserWorkflowServiceImpl()
        except ImportError:
            self._logger.warning("User Workflow Service implementation not available")
            from .implementations.mock_user_workflow_service import MockUserWorkflowService
            return MockUserWorkflowService()
    
    def get_bridge_domain_service(self) -> BridgeDomainService:
        """Get the Bridge Domain Service instance"""
        if 'bridge_domain' not in self._services:
            self._services['bridge_domain'] = self._service_factories['bridge_domain']()
        return self._services['bridge_domain']
    
    def get_topology_service(self) -> TopologyService:
        """Get the Topology Service instance"""
        if 'topology' not in self._services:
            self._services['topology'] = self._service_factories['topology']()
        return self._services['topology']
    
    def get_ssh_service(self) -> SSHService:
        """Get the SSH Service instance"""
        if 'ssh' not in self._services:
            self._services['ssh'] = self._service_factories['ssh']()
        return self._services['ssh']
    
    def get_discovery_service(self) -> DiscoveryService:
        """Get the Discovery Service instance"""
        if 'discovery' not in self._services:
            self._services['discovery'] = self._service_factories['discovery']()
        return self._services['discovery']
    
    def get_user_workflow_service(self) -> UserWorkflowService:
        """Get the User Workflow Service instance"""
        if 'user_workflow' not in self._services:
            self._services['user_workflow'] = self._service_factories['user_workflow']()
        return self._services['user_workflow']
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name"""
        if service_name not in self._services:
            if service_name in self._service_factories:
                self._services[service_name] = self._service_factories[service_name]()
            else:
                raise ValueError(f"Unknown service: {service_name}")
        return self._services[service_name]
    
    def register_service(self, service_name: str, service_instance: Any) -> None:
        """Register a custom service instance"""
        self._services[service_name] = service_instance
        self._logger.info(f"Registered custom service: {service_name}")
    
    def unregister_service(self, service_name: str) -> None:
        """Unregister a service"""
        if service_name in self._services:
            del self._services[service_name]
            self._logger.info(f"Unregistered service: {service_name}")
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services"""
        return self._services.copy()
    
    def clear_services(self) -> None:
        """Clear all registered services"""
        self._services.clear()
        self._logger.info("All services cleared")
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on all services"""
        health_status = {}
        
        for service_name in self._service_factories.keys():
            try:
                service = self.get_service(service_name)
                # Basic health check - just check if service exists
                health_status[service_name] = service is not None
            except Exception as e:
                self._logger.error(f"Health check failed for {service_name}: {e}")
                health_status[service_name] = False
        
        return health_status
