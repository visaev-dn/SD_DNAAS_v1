#!/usr/bin/env python3
"""
Interface Discovery Data Models

Simplified data structures for interface discovery system.
Focused on single command discovery ("show interface description") output.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class InterfaceDiscoveryData:
    """
    Simplified interface discovery data structure.
    
    Contains only essential information extracted from 'show interface description'
    command output, with basic bundle detection and status information.
    """
    
    # Basic Interface Info (from "show int desc")
    device_name: str
    interface_name: str
    interface_type: str = "physical"  # physical, bundle, subinterface (inferred)
    description: str = ""
    
    # Status (from "show int desc" output)
    admin_status: str = "unknown"    # up, down, admin-down
    oper_status: str = "unknown"     # up, down, testing
    
    # Bundle Information (parsed from description/name)
    bundle_id: Optional[str] = None  # Detected from interface name pattern
    is_bundle_member: bool = False   # If interface is part of a bundle
    
    # Discovery Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    device_reachable: bool = True
    discovery_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing to infer interface properties"""
        self._infer_interface_type()
        self._detect_bundle_membership()
    
    def _infer_interface_type(self):
        """Infer interface type from interface name patterns"""
        interface_lower = self.interface_name.lower()
        
        if "bundle" in interface_lower or "be" in interface_lower:
            self.interface_type = "bundle"
        elif "." in self.interface_name and any(char.isdigit() for char in self.interface_name.split(".")[-1]):
            self.interface_type = "subinterface"
        elif any(prefix in interface_lower for prefix in ["ge", "xe", "et", "te"]):
            self.interface_type = "physical"
        else:
            self.interface_type = "unknown"
    
    def _detect_bundle_membership(self):
        """Detect if interface is part of a bundle from description or naming"""
        desc_lower = self.description.lower()
        
        # Check for bundle membership in description
        if "bundle" in desc_lower or "lacp" in desc_lower:
            self.is_bundle_member = True
            # Try to extract bundle ID from description
            import re
            bundle_match = re.search(r'bundle[_\-\s]*(\d+)', desc_lower)
            if bundle_match:
                self.bundle_id = f"bundle-{bundle_match.group(1)}"
        
        # Check for bundle interface naming patterns
        if self.interface_type == "bundle":
            import re
            bundle_match = re.search(r'(?:bundle|be)[_\-]*(\d+)', self.interface_name.lower())
            if bundle_match:
                self.bundle_id = f"bundle-{bundle_match.group(1)}"
    
    def is_available_for_use(self) -> bool:
        """Check if interface is potentially available for BD assignment"""
        # Basic availability check - not admin-down and reachable device
        return (
            self.admin_status.lower() != "admin-down" and 
            self.device_reachable and
            len(self.discovery_errors) == 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'device_name': self.device_name,
            'interface_name': self.interface_name,
            'interface_type': self.interface_type,
            'description': self.description,
            'admin_status': self.admin_status,
            'oper_status': self.oper_status,
            'bundle_id': self.bundle_id,
            'is_bundle_member': self.is_bundle_member,
            'discovered_at': self.discovered_at.isoformat(),
            'device_reachable': self.device_reachable,
            'discovery_errors': json.dumps(self.discovery_errors)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterfaceDiscoveryData':
        """Create instance from dictionary (database retrieval)"""
        # Handle datetime conversion
        discovered_at = data.get('discovered_at')
        if isinstance(discovered_at, str):
            discovered_at = datetime.fromisoformat(discovered_at)
        elif discovered_at is None:
            discovered_at = datetime.now()
        
        # Handle JSON fields
        discovery_errors = data.get('discovery_errors', '[]')
        if isinstance(discovery_errors, str):
            try:
                discovery_errors = json.loads(discovery_errors)
            except json.JSONDecodeError:
                discovery_errors = []
        
        return cls(
            device_name=data.get('device_name', ''),
            interface_name=data.get('interface_name', ''),
            interface_type=data.get('interface_type', 'physical'),
            description=data.get('description', ''),
            admin_status=data.get('admin_status', 'unknown'),
            oper_status=data.get('oper_status', 'unknown'),
            bundle_id=data.get('bundle_id'),
            is_bundle_member=bool(data.get('is_bundle_member', False)),
            discovered_at=discovered_at,
            device_reachable=bool(data.get('device_reachable', True)),
            discovery_errors=discovery_errors
        )
    
    def __str__(self) -> str:
        """String representation for CLI display"""
        status_indicator = "✅" if self.is_available_for_use() else "❌"
        bundle_info = f" [Bundle: {self.bundle_id}]" if self.bundle_id else ""
        
        return (f"{status_indicator} {self.device_name}:{self.interface_name} "
                f"({self.admin_status}/{self.oper_status}){bundle_info} - {self.description}")


@dataclass
class DeviceDiscoveryResult:
    """Results from discovering interfaces on a single device"""
    
    device_name: str
    interfaces: List[InterfaceDiscoveryData]
    discovery_time: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    
    def interface_count(self) -> int:
        """Get total interface count"""
        return len(self.interfaces)
    
    def available_interface_count(self) -> int:
        """Get count of available interfaces"""
        return len([intf for intf in self.interfaces if intf.is_available_for_use()])
    
    def get_interface_names(self) -> List[str]:
        """Get list of interface names for CLI display"""
        return [intf.interface_name for intf in self.interfaces]
    
    def get_available_interface_names(self) -> List[str]:
        """Get list of available interface names for CLI selection"""
        return [intf.interface_name for intf in self.interfaces if intf.is_available_for_use()]


@dataclass 
class DiscoverySession:
    """Simple discovery session tracking"""
    
    session_id: str
    trigger_type: str  # manual, pre-bd-editor, device-specific
    devices_targeted: List[str]
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, partial
    results: Dict[str, DeviceDiscoveryResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def mark_completed(self):
        """Mark session as completed"""
        self.completed_at = datetime.now()
        self.status = "completed"
    
    def mark_failed(self, error: str):
        """Mark session as failed"""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.errors.append(error)
    
    def add_device_result(self, result: DeviceDiscoveryResult):
        """Add device discovery result"""
        self.results[result.device_name] = result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary for reporting"""
        total_interfaces = sum(result.interface_count() for result in self.results.values())
        successful_devices = len([r for r in self.results.values() if r.success])
        
        return {
            'session_id': self.session_id,
            'trigger_type': self.trigger_type,
            'devices_targeted': len(self.devices_targeted),
            'devices_successful': successful_devices,
            'total_interfaces': total_interfaces,
            'status': self.status,
            'duration_seconds': (
                (self.completed_at - self.started_at).total_seconds() 
                if self.completed_at else None
            ),
            'errors': self.errors
        }

