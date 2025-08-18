#!/usr/bin/env python3
"""
Topology Models Package
Data structures and models for topology representation
"""

from .device_types import (
    DeviceType,
    InterfaceType,
    DeviceCapabilities,
    DeviceClassifier,
    get_device_classifier,
    detect_device_type,
    classify_interface
)

from .topology_models import (
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
    TopologyValidator
)

from .network_models import (
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
__description__ = "Data structures and models for topology representation"
