#!/usr/bin/env python3
"""
Phase 1 Topology Data Structure
Defines the main standardized topology data container
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .enums import TopologyType, ValidationStatus, BridgeDomainScope
from .device_info import DeviceInfo
from .interface_info import InterfaceInfo
from .path_info import PathInfo
from .bridge_domain_config import BridgeDomainConfig


@dataclass(frozen=True)
class TopologyData:
    """
    Immutable topology data structure - the single source of truth
    for all topology operations in the system.
    
    This class consolidates all topology information into a single,
    validated, and consistent data structure.
    """
    
    # Basic Information (required fields)
    bridge_domain_name: str
    topology_type: TopologyType
    vlan_id: Optional[int]
    devices: List[DeviceInfo]
    interfaces: List[InterfaceInfo]
    paths: List[PathInfo]
    bridge_domain_config: BridgeDomainConfig
    discovered_at: datetime
    scan_method: str
    
    # Optional fields with defaults
    confidence_score: float = field(default=0.0, metadata={'min': 0.0, 'max': 1.0})
    schema_version: str = field(default="1.0.0")
    validation_status: ValidationStatus = ValidationStatus.PENDING
    template_summary: Dict[str, int] = field(default_factory=dict)
    
    # Metadata with defaults
    topology_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate topology data integrity after initialization"""
        self._validate_topology_data()
    
    def _validate_topology_data(self):
        """Validate topology data integrity"""
        if not self.bridge_domain_name:
            raise ValueError("Bridge domain name cannot be empty")
        
        if not isinstance(self.topology_type, TopologyType):
            raise ValueError("Topology type must be a valid TopologyType enum")
        
        if not isinstance(self.validation_status, ValidationStatus):
            raise ValueError("Validation status must be a valid ValidationStatus enum")
        
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not self.devices:
            raise ValueError("Topology must have at least one device")
        
        if not self.interfaces:
            raise ValueError("Topology must have at least one interface")
        
        if not self.paths:
            raise ValueError("Topology must have at least one path")
        
        if not self.bridge_domain_config:
            raise ValueError("Bridge domain configuration is required")
        
        # Validate data consistency
        self._validate_data_consistency()
    
    def _validate_data_consistency(self):
        """Validate consistency between different data components"""
        # Check that all devices referenced in interfaces exist
        device_names = {device.name for device in self.devices}
        for interface in self.interfaces:
            if interface.device_name not in device_names:
                raise ValueError(f"Interface {interface.name} references unknown device {interface.device_name}")
        
        # Check that all devices referenced in paths exist
        for path in self.paths:
            if path.source_device not in device_names:
                raise ValueError(f"Path {path.path_name} references unknown source device {path.source_device}")
            if path.dest_device not in device_names:
                raise ValueError(f"Path {path.path_name} references unknown destination device {path.dest_device}")
        
        # Check that bridge domain config references exist
        if self.bridge_domain_config.source_device not in device_names:
            raise ValueError(f"Bridge domain config references unknown source device {self.bridge_domain_config.source_device}")
        
        for dest in self.bridge_domain_config.destinations:
            if dest['device'] not in device_names:
                raise ValueError(f"Bridge domain config references unknown destination device {dest['device']}")
    
    @property
    def is_p2p(self) -> bool:
        """Check if topology is point-to-point"""
        return self.topology_type == TopologyType.P2P
    
    @property
    def is_p2mp(self) -> bool:
        """Check if topology is point-to-multipoint"""
        return self.topology_type == TopologyType.P2MP
    
    @property
    def device_count(self) -> int:
        """Get total number of devices"""
        return len(self.devices)
    
    @property
    def interface_count(self) -> int:
        """Get total number of interfaces"""
        return len(self.interfaces)
    
    @property
    def path_count(self) -> int:
        """Get total number of paths"""
        return len(self.paths)
    
    @property
    def leaf_devices(self) -> List[DeviceInfo]:
        """Get all leaf devices"""
        from .enums import DeviceType
        return [device for device in self.devices if device.device_type == DeviceType.LEAF]
    
    @property
    def spine_devices(self) -> List[DeviceInfo]:
        """Get all spine devices"""
        from .enums import DeviceType
        return [device for device in self.devices if device.device_type == DeviceType.SPINE]
    
    @property
    def superspine_devices(self) -> List[DeviceInfo]:
        """Get all superspine devices"""
        from .enums import DeviceType
        return [device for device in self.devices if device.device_type == DeviceType.SUPERSPINE]
    
    @property
    def source_devices(self) -> List[DeviceInfo]:
        """Get all source devices"""
        from .enums import DeviceRole
        return [device for device in self.devices if device.device_role == DeviceRole.SOURCE]
    
    @property
    def destination_devices(self) -> List[DeviceInfo]:
        """Get all destination devices"""
        from .enums import DeviceRole
        return [device for device in self.devices if device.device_role == DeviceRole.DESTINATION]
    
    @property
    def transport_devices(self) -> List[DeviceInfo]:
        """Get all transport devices"""
        from .enums import DeviceRole
        return [device for device in self.devices if device.device_role == DeviceRole.TRANSPORT]
    
    @property
    def access_interfaces(self) -> List[InterfaceInfo]:
        """Get all access interfaces"""
        from .enums import InterfaceRole
        return [interface for interface in self.interfaces if interface.interface_role == InterfaceRole.ACCESS]
    
    @property
    def transport_interfaces(self) -> List[InterfaceInfo]:
        """Get all transport interfaces"""
        from .enums import InterfaceRole
        return [interface for interface in self.interfaces if interface.interface_role == InterfaceRole.TRANSPORT]
    
    @property
    def configured_interfaces(self) -> List[InterfaceInfo]:
        """Get all interfaces with VLAN configuration"""
        return [interface for interface in self.interfaces if interface.is_configured]
    
    @property
    def bundle_interfaces(self) -> List[InterfaceInfo]:
        """Get all bundle interfaces"""
        return [interface for interface in self.interfaces if interface.is_bundle]
    
    @property
    def subinterfaces(self) -> List[InterfaceInfo]:
        """Get all subinterfaces"""
        return [interface for interface in self.interfaces if interface.is_subinterface]
    
    def get_device_by_name(self, device_name: str) -> Optional[DeviceInfo]:
        """Get device by name"""
        for device in self.devices:
            if device.name == device_name:
                return device
        return None
    
    def get_interfaces_by_device(self, device_name: str) -> List[InterfaceInfo]:
        """Get all interfaces for a specific device"""
        return [interface for interface in self.interfaces if interface.device_name == device_name]
    
    def get_paths_by_device(self, device_name: str) -> List[PathInfo]:
        """Get all paths that include a specific device"""
        paths = []
        for path in self.paths:
            if device_name in path.all_devices:
                paths.append(path)
        return paths
    
    def get_device_interfaces_by_role(self, device_name: str, role: str) -> List[InterfaceInfo]:
        """Get interfaces for a device with specific role"""
        from .enums import InterfaceRole
        if isinstance(role, str):
            role = InterfaceRole(role)
        
        device_interfaces = self.get_interfaces_by_device(device_name)
        return [interface for interface in device_interfaces if interface.interface_role == role]
    
    def get_device_paths_by_type(self, device_name: str, path_type: str) -> List[PathInfo]:
        """Get paths for a device with specific type"""
        from .enums import TopologyType
        if isinstance(path_type, str):
            path_type = TopologyType(path_type)
        
        device_paths = self.get_paths_by_device(device_name)
        return [path for path in device_paths if path.path_type == path_type]
    
    @property
    def topology_summary(self) -> str:
        """Get human-readable topology summary"""
        device_summary = f"{self.device_count} devices ({len(self.leaf_devices)} leaf, {len(self.spine_devices)} spine, {len(self.superspine_devices)} superspine)"
        interface_summary = f"{self.interface_count} interfaces ({len(self.configured_interfaces)} configured)"
        path_summary = f"{self.path_count} paths"
        
        return f"{self.bridge_domain_name}: {device_summary}, {interface_summary}, {path_summary}"
    
    @property
    def validation_summary(self) -> str:
        """Get validation status summary"""
        valid_devices = len([d for d in self.devices if d.validation_status == ValidationStatus.VALID])
        valid_interfaces = len([i for i in self.interfaces if i.validation_status == ValidationStatus.VALID])
        valid_paths = len([p for p in self.paths if p.validation_status == ValidationStatus.VALID])
        
        return f"Validation: {valid_devices}/{self.device_count} devices, {valid_interfaces}/{self.interface_count} interfaces, {valid_paths}/{self.path_count} paths"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert topology data to dictionary for serialization"""
        return {
            'topology_id': self.topology_id,
            'bridge_domain_name': self.bridge_domain_name,
            'topology_type': self.topology_type.value,
            'vlan_id': self.vlan_id,
            'confidence_score': self.confidence_score,
            'devices': [device.to_dict() for device in self.devices],
            'interfaces': [interface.to_dict() for interface in self.interfaces],
            'paths': [path.to_dict() for path in self.paths],
            'bridge_domain_config': self.bridge_domain_config.to_dict(),
            'discovered_at': self.discovered_at.isoformat(),
            'scan_method': self.scan_method,
            'source_data': self.source_data,
            'schema_version': self.schema_version,
            'validation_status': self.validation_status.value,
            'template_summary': self.template_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopologyData':
        """Create TopologyData from dictionary"""
        # Convert enum values back to enum instances
        if 'topology_type' in data and isinstance(data['topology_type'], str):
            from .enums import TopologyType
            data['topology_type'] = TopologyType(data['topology_type'])
        
        if 'validation_status' in data and isinstance(data['validation_status'], str):
            from .enums import ValidationStatus
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        # Convert component lists back to objects
        if 'devices' in data and isinstance(data['devices'], list):
            data['devices'] = [DeviceInfo.from_dict(device) for device in data['devices']]
        
        if 'interfaces' in data and isinstance(data['interfaces'], list):
            data['interfaces'] = [InterfaceInfo.from_dict(interface) for interface in data['interfaces']]
        
        if 'paths' in data and isinstance(data['paths'], list):
            data['paths'] = [PathInfo.from_dict(path) for path in data['paths']]
        
        if 'bridge_domain_config' in data and isinstance(data['bridge_domain_config'], dict):
            data['bridge_domain_config'] = BridgeDomainConfig.from_dict(data['bridge_domain_config'])
        
        # Convert datetime strings back to datetime objects
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate the entire topology data structure"""
        try:
            self._validate_topology_data()
            return True
        except ValueError:
            return False
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors"""
        errors = []
        try:
            self._validate_topology_data()
        except ValueError as e:
            errors.append(str(e))
        
        # Check individual component validation
        for device in self.devices:
            if device.validation_status == ValidationStatus.INVALID:
                errors.append(f"Device {device.name} validation failed")
        
        for interface in self.interfaces:
            if interface.validation_status == ValidationStatus.INVALID:
                errors.append(f"Interface {interface.name} validation failed")
        
        for path in self.paths:
            if path.validation_status == ValidationStatus.INVALID:
                errors.append(f"Path {path.path_name} validation failed")
        
        return errors
    
    def validate_bridge_domain_scope(self) -> List[str]:
        """
        Validate bridge domain scope configuration against actual device deployment
        
        Returns:
            List of scope misconfiguration warnings
        """
        warnings = []
        
        if not self.bridge_domain_config:
            return warnings
            
        scope = self.bridge_domain_config.bridge_domain_scope
        
        # Get unique devices involved in this bridge domain
        unique_devices = set()
        
        # Add source device
        if self.bridge_domain_config.source_device:
            unique_devices.add(self.bridge_domain_config.source_device)
            
        # Add destination devices
        for dest in self.bridge_domain_config.destinations:
            if isinstance(dest, dict) and dest.get('device'):
                unique_devices.add(dest['device'])
                
        # Add devices from topology data
        for device in self.devices:
            unique_devices.add(device.name)
            
        device_count = len(unique_devices)
        
        # Check for scope misconfigurations
        if scope == BridgeDomainScope.LOCAL:
            if device_count > 1:
                device_list = ', '.join(sorted(unique_devices))
                warnings.append(
                    f"⚠️ LOCAL SCOPE MISCONFIGURATION: Bridge domain '{self.bridge_domain_name}' "
                    f"is marked as LOCAL (l_ prefix) but configured across {device_count} devices: {device_list}. "
                    f"Local BDs should be leaf-only to avoid VLAN ID conflicts."
                )
        elif scope == BridgeDomainScope.GLOBAL:
            # Global BDs can span multiple devices - this is expected
            if device_count == 1:
                warnings.append(
                    f"💡 GLOBAL SCOPE OPTIMIZATION: Bridge domain '{self.bridge_domain_name}' "
                    f"is marked as GLOBAL (g_ prefix) but only configured on 1 device ({list(unique_devices)[0]}). "
                    f"Consider using LOCAL (l_ prefix) for better VLAN ID management."
                )
        
        return warnings