#!/usr/bin/env python3
"""
Phase 1 Device Information Data Structure
Defines standardized device representation for topology data
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .enums import DeviceType, DeviceRole, ValidationStatus


@dataclass(frozen=True)
class DeviceInfo:
    """
    Immutable device information structure for topology data.
    
    This class represents a network device in the topology with all its
    relevant attributes and metadata.
    """
    
    # Basic device information
    name: str
    device_type: DeviceType
    device_role: DeviceRole
    
    # Unique identifier for this device
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Network information
    ip_address: Optional[str] = None
    management_ip: Optional[str] = None
    
    # Device capabilities and status
    admin_state: str = "enabled"  # enabled, disabled, maintenance
    operational_state: str = "up"  # up, down, testing
    
    # Topology information
    row: Optional[str] = None      # DC row (A, B, C...)
    rack: Optional[str] = None     # Rack number within row
    position: Optional[str] = None  # Position within rack
    
    # Interface information
    total_interfaces: int = 0
    available_interfaces: int = 0
    configured_interfaces: int = 0
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = field(default=1.0, metadata={'min': 0.0, 'max': 1.0})
    
    # Validation status
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Source data (for reverse engineering)
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate device information after initialization"""
        self._validate_device_info()
    
    def _validate_device_info(self):
        """Validate device information integrity"""
        if not self.name:
            raise ValueError("Device name cannot be empty")
        
        if not isinstance(self.device_type, DeviceType):
            raise ValueError("Device type must be a valid DeviceType enum")
        
        if not isinstance(self.device_role, DeviceRole):
            raise ValueError("Device role must be a valid DeviceRole enum")
        
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if self.total_interfaces < 0:
            raise ValueError("Total interfaces cannot be negative")
        
        if self.available_interfaces < 0:
            raise ValueError("Available interfaces cannot be negative")
        
        if self.configured_interfaces < 0:
            raise ValueError("Configured interfaces cannot be negative")
        
        if self.total_interfaces < (self.available_interfaces + self.configured_interfaces):
            raise ValueError("Total interfaces must be >= available + configured")
    
    @property
    def is_leaf(self) -> bool:
        """Check if device is a leaf device"""
        return self.device_type == DeviceType.LEAF
    
    @property
    def is_spine(self) -> bool:
        """Check if device is a spine device"""
        return self.device_type == DeviceType.SPINE
    
    @property
    def is_superspine(self) -> bool:
        """Check if device is a superspine device"""
        return self.device_type == DeviceType.SUPERSPINE
    
    @property
    def is_source(self) -> bool:
        """Check if device is a source device"""
        return self.device_role == DeviceRole.SOURCE
    
    @property
    def is_destination(self) -> bool:
        """Check if device is a destination device"""
        return self.device_role == DeviceRole.DESTINATION
    
    @property
    def is_transport(self) -> bool:
        """Check if device is a transport device"""
        return self.device_role == DeviceRole.TRANSPORT
    
    @property
    def dc_location(self) -> str:
        """Get DC location string (e.g., 'Row A, Rack 01')"""
        if self.row and self.rack:
            return f"Row {self.row}, Rack {self.rack}"
        elif self.row:
            return f"Row {self.row}"
        else:
            return "Unknown"
    
    @property
    def interface_utilization(self) -> float:
        """Get interface utilization percentage"""
        if self.total_interfaces == 0:
            return 0.0
        return (self.configured_interfaces / self.total_interfaces) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device info to dictionary for serialization"""
        return {
            'device_id': self.device_id,
            'name': self.name,
            'device_type': self.device_type.value,
            'device_role': self.device_role.value,
            'ip_address': self.ip_address,
            'management_ip': self.management_ip,
            'admin_state': self.admin_state,
            'operational_state': self.operational_state,
            'row': self.row,
            'rack': self.rack,
            'position': self.position,
            'total_interfaces': self.total_interfaces,
            'available_interfaces': self.available_interfaces,
            'configured_interfaces': self.configured_interfaces,
            'discovered_at': self.discovered_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status.value,
            'source_data': self.source_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceInfo':
        """Create DeviceInfo from dictionary"""
        # Convert enum values back to enum instances
        if 'device_type' in data and isinstance(data['device_type'], str):
            from .enums import DeviceType
            data['device_type'] = DeviceType(data['device_type'])
        
        if 'device_role' in data and isinstance(data['device_role'], str):
            from .enums import DeviceRole
            data['device_role'] = DeviceRole(data['device_role'])
        
        if 'validation_status' in data and isinstance(data['validation_status'], str):
            from .enums import ValidationStatus
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        # Convert datetime strings back to datetime objects
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
