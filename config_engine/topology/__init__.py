#!/usr/bin/env python3
"""
Topology Package
Consolidated topology management for the Lab Automation Framework
"""

from .base_topology_manager import (
    BaseTopologyManager,
    DeviceInfo,
    InterfaceInfo,
    TopologyNode,
    TopologyLink,
    TopologyData,
    DiscoveryConfig,
    DiscoveryResult
)

from .models import (
    # Device types
    DeviceType,
    InterfaceType,
    DeviceCapabilities,
    DeviceClassifier,
    get_device_classifier,
    detect_device_type,
    classify_interface,
    
    # Topology models
    TopologyStatus,
    DiscoveryMethod,
    NetworkSegment,
    BundleInterface,
    VLANInfo,
    BridgeDomainInfo,
    PathSegment,
    NetworkPath,
    TopologyMetrics,
    DiscoverySession,
    TopologyGraph,
    TopologyValidator,
    
    # Network models
    NetworkProtocol,
    NetworkStatus,
    IPAddress,
    Subnet,
    RoutingTable,
    NetworkInterface,
    NetworkDevice,
    NetworkTopology,
    NetworkAnalyzer
)

__all__ = [
    # Base topology manager
    'BaseTopologyManager',
    'DeviceInfo',
    'InterfaceInfo',
    'TopologyNode',
    'TopologyLink',
    'TopologyData',
    'DiscoveryConfig',
    'DiscoveryResult',
    
    # Device types
    'DeviceType',
    'InterfaceType',
    'DeviceCapabilities',
    'DeviceClassifier',
    'get_device_classifier',
    'detect_device_type',
    'classify_interface',
    
    # Topology models
    'TopologyStatus',
    'DiscoveryMethod',
    'NetworkSegment',
    'BundleInterface',
    'VLANInfo',
    'BridgeDomainInfo',
    'PathSegment',
    'NetworkPath',
    'TopologyMetrics',
    'DiscoverySession',
    'TopologyGraph',
    'TopologyValidator',
    
    # Network models
    'NetworkProtocol',
    'NetworkStatus',
    'IPAddress',
    'Subnet',
    'RoutingTable',
    'NetworkInterface',
    'NetworkDevice',
    'NetworkTopology',
    'NetworkAnalyzer'
]

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Consolidated topology management with comprehensive models and validation"
