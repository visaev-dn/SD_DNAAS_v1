#!/usr/bin/env python3
"""
Phase 1 Data Structures Package
Standardized, validated data structures for topology operations
"""

# Core data structures
from .topology_data import TopologyData
from .device_info import DeviceInfo
from .interface_info import InterfaceInfo
from .path_info import PathInfo, PathSegment
from .bridge_domain_config import BridgeDomainConfig

# Enums
from .enums import (
    TopologyType,
    DeviceType,
    InterfaceType,
    InterfaceRole,
    DeviceRole,
    ValidationStatus,
    BridgeDomainType,
    OuterTagImposition,
    # Helper functions
    get_enum_values,
    get_enum_names,
    validate_enum_value,
    get_enum_by_value
)

# Validation framework
from .validator import TopologyValidator

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Phase 1 standardized data structures for topology operations"

# Public API
__all__ = [
    # Core data structures
    'TopologyData',
    'DeviceInfo',
    'InterfaceInfo',
    'PathInfo',
    'PathSegment',
    'BridgeDomainConfig',
    
    # Enums
    'TopologyType',
    'DeviceType',
    'InterfaceType',
    'InterfaceRole',
    'DeviceRole',
    'ValidationStatus',
    'BridgeDomainType',
    'OuterTagImposition',
    
    # Helper functions
    'get_enum_values',
    'get_enum_names',
    'validate_enum_value',
    'get_enum_by_value',
    
    # Validation
    'TopologyValidator',
    
    # Metadata
    '__version__',
    '__author__',
    '__description__'
]

# Convenience imports for common use cases
from typing import List, Dict
from datetime import datetime

def create_p2p_topology(
    bridge_domain_name: str,
    vlan_id: int,
    source_device: str,
    source_interface: str,
    dest_device: str,
    dest_interface: str,
    **kwargs
) -> TopologyData:
    """
    Convenience function to create a P2P topology data structure.
    
    Args:
        bridge_domain_name: Name of the bridge domain
        vlan_id: VLAN ID for the bridge domain
        source_device: Source device name
        source_interface: Source interface name
        dest_device: Destination device name
        dest_interface: Destination interface name
        **kwargs: Additional arguments for TopologyData
        
    Returns:
        TopologyData instance configured for P2P topology
    """
    from .enums import TopologyType, BridgeDomainType, DeviceType, DeviceRole, InterfaceRole
    
    # Create bridge domain configuration
    bridge_domain_config = BridgeDomainConfig(
        service_name=bridge_domain_name,
        bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
        vlan_id=vlan_id,
        source_device=source_device,
        source_interface=source_interface,
        destinations=[{'device': dest_device, 'port': dest_interface}]
    )
    
    # Create device information
    devices = [
        DeviceInfo(
            name=source_device,
            device_type=DeviceType.LEAF,
            device_role=DeviceRole.SOURCE
        ),
        DeviceInfo(
            name=dest_device,
            device_type=DeviceType.LEAF,
            device_role=DeviceRole.DESTINATION
        )
    ]
    
    # Create interface information
    interfaces = [
        InterfaceInfo(
            name=source_interface,
            interface_type=InterfaceType.PHYSICAL,
            interface_role=InterfaceRole.ACCESS,
            device_name=source_device,
            vlan_id=vlan_id
        ),
        InterfaceInfo(
            name=dest_interface,
            interface_type=InterfaceType.PHYSICAL,
            interface_role=InterfaceRole.ACCESS,
            device_name=dest_device,
            vlan_id=vlan_id
        )
    ]
    
    # Create path information
    path_segment = PathSegment(
        source_device=source_device,
        dest_device=dest_device,
        source_interface=source_interface,
        dest_interface=dest_interface,
        segment_type="leaf_to_leaf"
    )
    
    path = PathInfo(
        path_name=f"{source_device}_to_{dest_device}",
        path_type=TopologyType.P2P,
        source_device=source_device,
        dest_device=dest_device,
        segments=[path_segment]
    )
    
    # Create topology data
    return TopologyData(
        bridge_domain_name=bridge_domain_name,
        topology_type=TopologyType.P2P,
        vlan_id=vlan_id,
        devices=devices,
        interfaces=interfaces,
        paths=[path],
        bridge_domain_config=bridge_domain_config,
        discovered_at=datetime.now(),
        scan_method="manual_creation",
        **kwargs
    )


def create_p2mp_topology(
    bridge_domain_name: str,
    vlan_id: int,
    source_device: str,
    source_interface: str,
    destinations: List[Dict[str, str]],
    **kwargs
) -> TopologyData:
    """
    Convenience function to create a P2MP topology data structure.
    
    Args:
        bridge_domain_name: Name of the bridge domain
        vlan_id: VLAN ID for the bridge domain
        source_device: Source device name
        source_interface: Source interface name
        destinations: List of destination dictionaries with 'device' and 'port' keys
        **kwargs: Additional arguments for TopologyData
        
    Returns:
        TopologyData instance configured for P2MP topology
    """
    from .enums import TopologyType, BridgeDomainType, DeviceType, DeviceRole, InterfaceRole
    
    # Create bridge domain configuration
    bridge_domain_config = BridgeDomainConfig(
        service_name=bridge_domain_name,
        bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
        vlan_id=vlan_id,
        source_device=source_device,
        source_interface=source_interface,
        destinations=destinations
    )
    
    # Create device information
    devices = [
        DeviceInfo(
            name=source_device,
            device_type=DeviceType.LEAF,
            device_role=DeviceRole.SOURCE
        )
    ]
    
    # Add destination devices
    for dest in destinations:
        devices.append(DeviceInfo(
            name=dest['device'],
            device_type=DeviceType.LEAF,
            device_role=DeviceRole.DESTINATION
        ))
    
    # Create interface information
    interfaces = [
        InterfaceInfo(
            name=source_interface,
            interface_type=InterfaceType.PHYSICAL,
            interface_role=InterfaceRole.ACCESS,
            device_name=source_device,
            vlan_id=vlan_id
        )
    ]
    
    # Add destination interfaces
    for dest in destinations:
        interfaces.append(InterfaceInfo(
            name=dest['port'],
            interface_type=InterfaceType.PHYSICAL,
            interface_role=InterfaceRole.ACCESS,
            device_name=dest['device'],
            vlan_id=vlan_id
        ))
    
    # Create path information (one path per destination)
    paths = []
    for dest in destinations:
        path_segment = PathSegment(
            source_device=source_device,
            dest_device=dest['device'],
            source_interface=source_interface,
            dest_interface=dest['port'],
            segment_type="leaf_to_leaf"
        )
        
        path = PathInfo(
            path_name=f"{source_device}_to_{dest['device']}",
            path_type=TopologyType.P2P,  # Individual paths are P2P
            source_device=source_device,
            dest_device=dest['device'],
            segments=[path_segment]
        )
        paths.append(path)
    
    # Create topology data
    return TopologyData(
        bridge_domain_name=bridge_domain_name,
        topology_type=TopologyType.P2MP,
        vlan_id=vlan_id,
        devices=devices,
        interfaces=interfaces,
        paths=paths,
        bridge_domain_config=bridge_domain_config,
        discovered_at=datetime.now(),
        scan_method="manual_creation",
        **kwargs
    )


# Add convenience functions to __all__
__all__.extend([
    'create_p2p_topology',
    'create_p2mp_topology'
])
