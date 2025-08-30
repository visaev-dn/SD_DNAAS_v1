#!/usr/bin/env python3
"""
Phase 1 Bridge Domain Configuration Data Structure
Defines standardized bridge domain configuration representation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .enums import BridgeDomainType, OuterTagImposition, ValidationStatus, BridgeDomainScope


@dataclass(frozen=True)
class BridgeDomainConfig:
    """
    Immutable bridge domain configuration structure for topology data.
    
    This class represents a complete bridge domain configuration with
    all its parameters, interfaces, and metadata.
    """
    
    # Basic configuration information (required fields)
    service_name: str
    bridge_domain_type: BridgeDomainType
    source_device: str
    source_interface: str
    destinations: List[Dict[str, str]] = field(default_factory=list)  # List of {device, port}
    
    # Optional fields with defaults
    vlan_id: Optional[int] = None
    vlan_start: Optional[int] = None      # For VLAN range
    vlan_end: Optional[int] = None        # For VLAN range
    vlan_list: Optional[List[int]] = None # For VLAN list
    outer_vlan: Optional[int] = None      # For QinQ
    inner_vlan: Optional[int] = None      # For QinQ
    outer_tag_imposition: OuterTagImposition = OuterTagImposition.EDGE
    bridge_domain_scope: BridgeDomainScope = field(default=None)  # Auto-detect from service_name
    bundle_id: Optional[int] = None
    interface_number: Optional[int] = None
    is_active: bool = True
    is_deployed: bool = False
    deployment_status: str = "pending"  # pending, deploying, deployed, failed
    created_by: Optional[str] = None
    confidence_score: float = field(default=1.0, metadata={'min': 0.0, 'max': 1.0})
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Metadata with defaults
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate bridge domain configuration after initialization"""
        # Auto-detect scope if not provided
        if self.bridge_domain_scope is None:
            object.__setattr__(self, 'bridge_domain_scope', BridgeDomainScope.detect_from_name(self.service_name))
        
        self._validate_bridge_domain_config()
    
    def _validate_bridge_domain_config(self):
        """Validate bridge domain configuration integrity"""
        if not self.service_name:
            raise ValueError("Service name cannot be empty")
        
        if not isinstance(self.bridge_domain_type, BridgeDomainType):
            raise ValueError("Bridge domain type must be a valid BridgeDomainType enum")
        
        if not self.source_device:
            raise ValueError("Source device cannot be empty")
        
        if not self.source_interface:
            raise ValueError("Source interface cannot be empty")
        
        if not isinstance(self.outer_tag_imposition, OuterTagImposition):
            raise ValueError("Outer tag imposition must be a valid OuterTagImposition enum")
        
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Validate VLAN configuration based on bridge domain type
        self._validate_vlan_configuration()
        
        # Validate destinations
        self._validate_destinations()
    
    def _validate_vlan_configuration(self):
        """Validate VLAN configuration based on bridge domain type"""
        if self.bridge_domain_type == BridgeDomainType.SINGLE_VLAN:
            if self.vlan_id is None:
                raise ValueError("Single VLAN bridge domain must have VLAN ID")
            if not (1 <= self.vlan_id <= 4094):
                raise ValueError("VLAN ID must be between 1 and 4094")
        
        elif self.bridge_domain_type == BridgeDomainType.VLAN_RANGE:
            if self.vlan_start is None or self.vlan_end is None:
                raise ValueError("VLAN range bridge domain must have start and end VLAN IDs")
            if not (1 <= self.vlan_start <= 4094) or not (1 <= self.vlan_end <= 4094):
                raise ValueError("VLAN range must be between 1 and 4094")
            if self.vlan_start >= self.vlan_end:
                raise ValueError("VLAN start must be less than VLAN end")
        
        elif self.bridge_domain_type == BridgeDomainType.VLAN_LIST:
            if not self.vlan_list:
                raise ValueError("VLAN list bridge domain must have VLAN list")
            for vlan_id in self.vlan_list:
                if not (1 <= vlan_id <= 4094):
                    raise ValueError(f"VLAN ID {vlan_id} must be between 1 and 4094")
        
        # QinQ validation for all QinQ types
        elif self.bridge_domain_type in [BridgeDomainType.DOUBLE_TAGGED, BridgeDomainType.QINQ_SINGLE_BD, 
                                        BridgeDomainType.QINQ_MULTI_BD, BridgeDomainType.HYBRID, 
                                        BridgeDomainType.QINQ]:  # Legacy support
            
            # Type 1 (DOUBLE_TAGGED) requires both outer and inner VLANs
            if self.bridge_domain_type == BridgeDomainType.DOUBLE_TAGGED:
                if self.outer_vlan is None or self.inner_vlan is None:
                    raise ValueError("Type 1 (Double-Tagged) bridge domain must have outer and inner VLAN IDs")
                if not (1 <= self.outer_vlan <= 4094) or not (1 <= self.inner_vlan <= 4094):
                    raise ValueError("Type 1 VLAN IDs must be between 1 and 4094")
            
            # Types 2A, 2B, 3 (LEAF-managed) - more flexible validation
            else:
                # At least outer VLAN should be present for LEAF-managed QinQ
                if self.outer_vlan is not None and not (1 <= self.outer_vlan <= 4094):
                    raise ValueError("QinQ outer VLAN must be between 1 and 4094")
                if self.inner_vlan is not None and not (1 <= self.inner_vlan <= 4094):
                    raise ValueError("QinQ inner VLAN must be between 1 and 4094")
    
    def _validate_destinations(self):
        """Validate destination configuration"""
        if not self.destinations:
            raise ValueError("Bridge domain must have at least one destination")
        
        for dest in self.destinations:
            if not isinstance(dest, dict):
                raise ValueError("Each destination must be a dictionary")
            
            if 'device' not in dest or 'port' not in dest:
                raise ValueError("Each destination must have 'device' and 'port' keys")
            
            if not dest['device'] or not dest['port']:
                raise ValueError("Destination device and port cannot be empty")
    
    @property
    def is_single_vlan(self) -> bool:
        """Check if bridge domain is single VLAN"""
        return self.bridge_domain_type == BridgeDomainType.SINGLE_VLAN
    
    @property
    def is_vlan_range(self) -> bool:
        """Check if bridge domain is VLAN range"""
        return self.bridge_domain_type == BridgeDomainType.VLAN_RANGE
    
    @property
    def is_vlan_list(self) -> bool:
        """Check if bridge domain is VLAN list"""
        return self.bridge_domain_type == BridgeDomainType.VLAN_LIST
    
    @property
    def is_qinq(self) -> bool:
        """Check if bridge domain is QinQ type"""
        return self.bridge_domain_type in [
            BridgeDomainType.DOUBLE_TAGGED,
            BridgeDomainType.QINQ_SINGLE_BD,
            BridgeDomainType.QINQ_MULTI_BD,
            BridgeDomainType.HYBRID,
            BridgeDomainType.QINQ  # Legacy support
        ]
    
    @property
    def is_local_scope(self) -> bool:
        """Check if bridge domain is local scope"""
        return self.bridge_domain_scope == BridgeDomainScope.LOCAL
    
    @property
    def is_global_scope(self) -> bool:
        """Check if bridge domain is global scope"""
        return self.bridge_domain_scope == BridgeDomainScope.GLOBAL
    
    @property
    def is_p2p(self) -> bool:
        """Check if bridge domain is point-to-point"""
        return len(self.destinations) == 1
    
    @property
    def is_p2mp(self) -> bool:
        """Check if bridge domain is point-to-multipoint"""
        return len(self.destinations) > 1
    
    @property
    def destination_count(self) -> int:
        """Get number of destinations"""
        return len(self.destinations)
    
    @property
    def vlan_count(self) -> int:
        """Get total number of VLANs in this bridge domain"""
        if self.is_single_vlan:
            return 1
        elif self.is_vlan_range:
            return self.vlan_end - self.vlan_start + 1
        elif self.is_vlan_list:
            return len(self.vlan_list)
        elif self.is_qinq:
            return 1  # QinQ uses one outer-inner pair
        else:
            return 0
    
    @property
    def vlan_summary(self) -> str:
        """Get human-readable VLAN summary"""
        if self.is_single_vlan:
            return f"VLAN {self.vlan_id}"
        elif self.is_vlan_range:
            return f"VLANs {self.vlan_start}-{self.vlan_end} ({self.vlan_count} VLANs)"
        elif self.is_vlan_list:
            return f"VLANs {', '.join(map(str, self.vlan_list))} ({self.vlan_count} VLANs)"
        elif self.is_qinq:
            return f"QinQ {self.outer_vlan}.{self.inner_vlan}"
        else:
            return "Unknown VLAN configuration"
    
    @property
    def topology_summary(self) -> str:
        """Get human-readable topology summary"""
        if self.is_p2p:
            dest = self.destinations[0]
            return f"{self.source_device} → {dest['device']} (P2P)"
        else:
            dest_count = len(self.destinations)
            return f"{self.source_device} → {dest_count} destinations (P2MP)"
    
    @property
    def configuration_summary(self) -> str:
        """Get complete configuration summary"""
        return f"{self.service_name}: {self.vlan_summary} - {self.topology_summary}"
    
    def get_destination_devices(self) -> List[str]:
        """Get list of destination device names"""
        return [dest['device'] for dest in self.destinations]
    
    def get_destination_ports(self) -> List[str]:
        """Get list of destination port names"""
        return [dest['port'] for dest in self.destinations]
    
    def has_destination(self, device_name: str) -> bool:
        """Check if device is a destination"""
        return device_name in self.get_destination_devices()
    
    def get_destination_port(self, device_name: str) -> Optional[str]:
        """Get port for specific destination device"""
        for dest in self.destinations:
            if dest['device'] == device_name:
                return dest['port']
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bridge domain config to dictionary for serialization"""
        return {
            'config_id': self.config_id,
            'service_name': self.service_name,
            'bridge_domain_type': self.bridge_domain_type.value,
            'vlan_id': self.vlan_id,
            'vlan_start': self.vlan_start,
            'vlan_end': self.vlan_end,
            'vlan_list': self.vlan_list,
            'outer_vlan': self.outer_vlan,
            'inner_vlan': self.inner_vlan,
            'source_device': self.source_device,
            'source_interface': self.source_interface,
            'destinations': self.destinations,
            'outer_tag_imposition': self.outer_tag_imposition.value,
            'bundle_id': self.bundle_id,
            'interface_number': self.interface_number,
            'is_active': self.is_active,
            'is_deployed': self.is_deployed,
            'deployment_status': self.deployment_status,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'created_by': self.created_by,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status.value,
            'source_data': self.source_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BridgeDomainConfig':
        """Create BridgeDomainConfig from dictionary"""
        # Convert enum values back to enum instances
        if 'bridge_domain_type' in data and isinstance(data['bridge_domain_type'], str):
            from .enums import BridgeDomainType
            data['bridge_domain_type'] = BridgeDomainType(data['bridge_domain_type'])
        
        if 'outer_tag_imposition' in data and isinstance(data['outer_tag_imposition'], str):
            from .enums import OuterTagImposition
            data['outer_tag_imposition'] = OuterTagImposition(data['outer_tag_imposition'])
        
        if 'validation_status' in data and isinstance(data['validation_status'], str):
            from .enums import ValidationStatus
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        # Convert datetime strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
