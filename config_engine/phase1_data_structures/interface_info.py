#!/usr/bin/env python3
"""
Phase 1 Interface Information Data Structure
Defines standardized interface representation for topology data
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .enums import InterfaceType, InterfaceRole, ValidationStatus


@dataclass(frozen=True)
class InterfaceInfo:
    """
    Immutable interface information structure for topology data.
    
    This class represents a network interface with all its relevant
    attributes and configuration details.
    """
    
    # Basic interface information
    name: str
    interface_type: InterfaceType
    interface_role: InterfaceRole
    
    # Device association
    device_name: str
    
    # Unique identifier for this interface
    interface_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: Optional[str] = None
    
    # Interface configuration
    vlan_id: Optional[int] = None
    bundle_id: Optional[int] = None
    subinterface_id: Optional[int] = None
    
    # Interface status
    admin_state: str = "enabled"  # enabled, disabled, maintenance
    operational_state: str = "up"  # up, down, testing, not-present
    
    # Physical characteristics
    speed: Optional[str] = None      # 10G, 100G, 1G, etc.
    duplex: Optional[str] = None    # full, half
    media_type: Optional[str] = None  # copper, fiber
    
    # Configuration details
    description: Optional[str] = None
    mtu: Optional[int] = None
    l2_service_enabled: bool = False
    
    # Topology information
    connected_device: Optional[str] = None
    connected_interface: Optional[str] = None
    connection_type: Optional[str] = None  # direct, bundle, lag
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = field(default=1.0, metadata={'min': 0.0, 'max': 1.0})
    
    # Validation status
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Source data (for reverse engineering)
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate interface information after initialization"""
        self._validate_interface_info()
    
    def _validate_interface_info(self):
        """Validate interface information integrity"""
        if not self.name:
            raise ValueError("Interface name cannot be empty")
        
        if not isinstance(self.interface_type, InterfaceType):
            raise ValueError("Interface type must be a valid InterfaceType enum")
        
        if not isinstance(self.interface_role, InterfaceRole):
            raise ValueError("Interface role must be a valid InterfaceRole enum")
        
        if not self.device_name:
            raise ValueError("Device name cannot be empty")
        
        if self.vlan_id is not None and (self.vlan_id < 1 or self.vlan_id > 4094):
            raise ValueError("VLAN ID must be between 1 and 4094")
        
        if self.bundle_id is not None and (self.bundle_id < 1 or self.bundle_id > 64):
            raise ValueError("Bundle ID must be between 1 and 64")
        
        # Note: Subinterface ID validation removed - subinterface IDs are just identifiers
        # and can be any value (e.g., 15005). They are NOT the same as VLAN IDs.
        # VLAN ID validation is handled separately above.
        
        if self.mtu is not None and (self.mtu < 64 or self.mtu > 9216):
            raise ValueError("MTU must be between 64 and 9216")
        
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
    
    @property
    def is_physical(self) -> bool:
        """Check if interface is physical"""
        return self.interface_type == InterfaceType.PHYSICAL
    
    @property
    def is_bundle(self) -> bool:
        """Check if interface is a bundle"""
        return self.interface_type == InterfaceType.BUNDLE
    
    @property
    def is_subinterface(self) -> bool:
        """Check if interface is a subinterface"""
        return self.interface_type == InterfaceType.SUBINTERFACE
    
    @property
    def is_access(self) -> bool:
        """Check if interface is an access interface"""
        return self.interface_role == InterfaceRole.ACCESS
    
    @property
    def is_uplink(self) -> bool:
        """Check if interface is an uplink interface"""
        return self.interface_role == InterfaceRole.UPLINK
    
    @property
    def is_downlink(self) -> bool:
        """Check if interface is a downlink interface"""
        return self.interface_role == InterfaceRole.DOWNLINK
    
    @property
    def is_transport(self) -> bool:
        """Check if interface is a transport interface"""
        return self.interface_role == InterfaceRole.TRANSPORT
    
    @property
    def is_configured(self) -> bool:
        """Check if interface has VLAN configuration"""
        return self.vlan_id is not None
    
    @property
    def is_bundled(self) -> bool:
        """Check if interface is part of a bundle"""
        return self.bundle_id is not None
    
    @property
    def full_name(self) -> str:
        """Get full interface name with all components"""
        if self.is_subinterface and self.bundle_id and self.subinterface_id:
            return f"bundle-{self.bundle_id}.{self.subinterface_id}"
        elif self.is_bundle and self.bundle_id:
            return f"bundle-{self.bundle_id}"
        else:
            return self.name
    
    @property
    def display_name(self) -> str:
        """Get human-readable interface name"""
        if self.is_subinterface:
            return f"{self.name} (VLAN {self.vlan_id})"
        elif self.is_bundle:
            return f"{self.name} (Bundle)"
        else:
            return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert interface info to dictionary for serialization"""
        return {
            'interface_id': self.interface_id,
            'name': self.name,
            'interface_type': self.interface_type.value,
            'interface_role': self.interface_role.value,
            'device_name': self.device_name,
            'device_id': self.device_id,
            'vlan_id': self.vlan_id,
            'bundle_id': self.bundle_id,
            'subinterface_id': self.subinterface_id,
            'admin_state': self.admin_state,
            'operational_state': self.operational_state,
            'speed': self.speed,
            'duplex': self.duplex,
            'media_type': self.media_type,
            'description': self.description,
            'mtu': self.mtu,
            'l2_service_enabled': self.l2_service_enabled,
            'connected_device': self.connected_device,
            'connected_interface': self.connected_interface,
            'connection_type': self.connection_type,
            'discovered_at': self.discovered_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status.value,
            'source_data': self.source_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterfaceInfo':
        """Create InterfaceInfo from dictionary"""
        # Convert enum values back to enum instances
        if 'interface_type' in data and isinstance(data['interface_type'], str):
            from .enums import InterfaceType
            data['interface_type'] = InterfaceType(data['interface_type'])
        
        if 'interface_role' in data and isinstance(data['interface_role'], str):
            from .enums import InterfaceRole
            data['interface_role'] = InterfaceRole(data['interface_role'])
        
        if 'validation_status' in data and isinstance(data['validation_status'], str):
            from .enums import ValidationStatus
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        # Convert datetime strings back to datetime objects
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
