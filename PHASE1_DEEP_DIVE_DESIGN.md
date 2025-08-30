# 🏗️ Phase 1: Data Structure & Models - Deep Dive Design Plan

## 🎯 **Phase 1 Overview**

**Phase 1 is the foundation** of our entire Scan→Reverse-Engineer→Edit workflow. We will create a **standardized, consistent, and extensible data structure** that all components can rely on. This phase will define how topology data is represented, stored, and validated throughout the system.

## 📊 **Current Data Structure Problems**

### **Problem 1: Inconsistent Data Formats**
```python
# Current: Different components use different formats
# DeviceScanner returns: Dict[str, Any]
# EnhancedTopologyScanner returns: Dict[str, Any]  
# BridgeDomainDiscovery returns: Dict[str, Any]
# API endpoints expect: Various formats

# Result: Data transformation hell, bugs, maintenance nightmare
```

### **Problem 2: Missing Data Validation**
```python
# Current: No validation of data integrity
# Result: Runtime errors, corrupted data, unpredictable behavior
```

### **Problem 3: No Type Safety**
```python
# Current: Everything is Dict[str, Any]
# Result: IDE can't help, runtime errors, hard to debug
```

### **Problem 4: Database Model Mismatch**
```python
# Current: Database models don't match the data we actually need
# Result: Data loss, inefficient storage, complex queries
```

## 🏗️ **Proposed Solution: Standardized Data Architecture**

### **Core Design Principles:**
1. **Single Source of Truth**: One data structure for all topology operations
2. **Type Safety**: Use Python dataclasses with proper typing
3. **Validation**: Built-in data validation at every level
4. **Extensibility**: Easy to add new fields without breaking existing code
5. **Serialization**: Easy to convert to/from JSON for API and storage
6. **Immutable by Default**: Prevent accidental data corruption

## 📋 **Detailed Data Structure Design**

### **1. Core Topology Data Structure**

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid

@dataclass(frozen=True)
class TopologyData:
    """
    Immutable topology data structure - the single source of truth
    for all topology operations in the system.
    """
    
    # Unique identifier for this topology
    topology_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    bridge_domain_name: str
    topology_type: 'TopologyType'
    vlan_id: Optional[int]
    confidence_score: float = field(default=0.0, metadata={'min': 0.0, 'max': 1.0})
    
    # Core Components
    devices: List['DeviceInfo']
    interfaces: List['InterfaceInfo']
    paths: List['PathInfo']
    bridge_domain_config: 'BridgeDomainConfig'
    
    # Metadata
    discovered_at: datetime
    scan_method: str
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    # Version and validation
    schema_version: str = field(default="1.0.0")
    validation_status: 'ValidationStatus' = field(default='ValidationStatus.PENDING')
    
    # DNAAS Bridge-Domain Semantics (Additions)
    template_summary: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate data integrity after initialization"""
        self._validate_topology_data()
    
    def _validate_topology_data(self):
        """Validate topology data integrity"""
        if not self.bridge_domain_name:
            raise ValueError("Bridge domain name cannot be empty")
        
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if not self.devices:
            raise ValueError("Topology must have at least one device")
        
        if not self.interfaces:
            raise ValueError("Topology must have at least one interface")
        
        # Validate device-interface relationships
        device_names = {d.name for d in self.devices}
        for interface in self.interfaces:
            if interface.device not in device_names:
                raise ValueError(f"Interface {interface.name} references unknown device {interface.device}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'topology_id': self.topology_id,
            'bridge_domain_name': self.bridge_domain_name,
            'topology_type': self.topology_type.value,
            'vlan_id': self.vlan_id,
            'confidence_score': self.confidence_score,
            'devices': [d.to_dict() for d in self.devices],
            'interfaces': [i.to_dict() for i in self.interfaces],
            'paths': [p.to_dict() for p in self.paths],
            'bridge_domain_config': self.bridge_domain_config.to_dict(),
            'discovered_at': self.discovered_at.isoformat(),
            'scan_method': self.scan_method,
            'schema_version': self.schema_version,
            'validation_status': self.validation_status.value,
            'template_summary': self.template_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopologyData':
        """Create TopologyData from dictionary"""
        # Convert string enums back to enum values
        if 'topology_type' in data and isinstance(data['topology_type'], str):
            data['topology_type'] = TopologyType(data['topology_type'])
        
        if 'validation_status' in data and isinstance(data['validation_status'], str):
            data['validation_status'] = ValidationStatus(data['validation_status'])
        
        # Convert ISO string back to datetime
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        return cls(**data)
```

### **2. Enums for Type Safety**

```python
class TopologyType(Enum):
    """Topology type enumeration"""
    P2P = "p2p"                    # Point-to-point
    P2MP = "p2mp"                  # Point-to-multipoint
    UNKNOWN = "unknown"             # Unknown topology type

class DeviceType(Enum):
    """Device type enumeration"""
    LEAF = "leaf"                   # Access layer device
    SPINE = "spine"                 # Aggregation layer device
    SUPERSPINE = "superspine"       # Core layer device
    UNKNOWN = "unknown"             # Unknown device type

class InterfaceType(Enum):
    """Interface type enumeration"""
    PHYSICAL = "physical"           # Standard physical interface
    BUNDLE = "bundle"               # Link aggregation bundle
    SUBINTERFACE = "subinterface"   # Subinterface (e.g., xe-0/0/0.100)
    LOOPBACK = "loopback"           # Loopback interface
    MANAGEMENT = "management"       # Management interface
    UNKNOWN = "unknown"             # Unknown interface type

class InterfaceRole(Enum):
    """Interface role enumeration"""
    ACCESS = "access"               # Access interface (end device connection)
    UPLINK = "uplink"               # Uplink interface (toward core)
    DOWNLINK = "downlink"           # Downlink interface (toward access)
    TRANSIT = "transit"             # Transit interface (between core devices)
    UNKNOWN = "unknown"             # Unknown interface role

class DeviceRole(Enum):
    """Device role in topology"""
    SOURCE = "source"               # Source device (traffic origin)
    DESTINATION = "destination"     # Destination device (traffic target)
    TRANSIT = "transit"             # Transit device (traffic forwarding)
    UNKNOWN = "unknown"             # Unknown device role

class ValidationStatus(Enum):
    """Data validation status"""
    PENDING = "pending"             # Not yet validated
    VALID = "valid"                 # Passed validation
    INVALID = "invalid"             # Failed validation
    PARTIAL = "partial"             # Partially valid (with warnings)

## DNAAS Bridge-Domain Semantics (Additions)

To accurately represent DNAAS BDs:

```python
class BridgeDomainType(Enum):
    LOCAL = "local"     # intra-rack (leaf only)
    GLOBAL = "global"    # inter-rack (uplinks applied)

class OuterTagImposition(Enum):
    EDGE = "edge"       # double-tag at edge device
    LEAF = "leaf"       # outer-tag push/pop at leaf
```

Extend `BridgeDomainConfig`:
```python
@dataclass(frozen=True)
class BridgeDomainConfig:
    # ... existing fields ...
    bd_type: Optional[BridgeDomainType] = None
    outer_tag_imposition: Optional[OuterTagImposition] = None
    # optional per-interface template mapping (see templates design)
    interface_templates: Dict[str, Any] = field(default_factory=dict)
```

Extend `TopologyData`:
```python
@dataclass(frozen=True)
class TopologyData:
    # ... existing fields ...
    template_summary: Dict[str, int] = field(default_factory=dict)
```

Extend `InterfaceInfo` (normalization for discovery):
```python
@dataclass(frozen=True)
class InterfaceInfo:
    # ... existing fields ...
    vlan_expression: Optional[str] = None    # single/list/range canonical form
    ingress_push: Optional[Dict[str, Any]] = None
    egress_pop: Optional[bool] = None
    swap_behavior: Optional[bool] = None
    applied_template: Optional[Dict[str, Any]] = None  # TemplateRef serialization
```

Guidelines:
- Prefer P2P membership (2 members per BD) unless multihoming; warn otherwise.
- GLOBAL BDs require globally unique outer VLANs (enforced by policy/validator).
- Mixed interface modes within a BD are permitted; template validator must ensure consistent VLAN behavior.

```

### **3. Device Information Structure**

```python
@dataclass(frozen=True)
class DeviceInfo:
    """Comprehensive device information"""
    
    # Basic Information
    name: str
    device_type: DeviceType
    role: DeviceRole
    
    # Interface Information
    interfaces: List[str] = field(default_factory=list)  # Interface names
    
    # Capabilities and Status
    capabilities: Dict[str, Any] = field(default_factory=dict)
    status: str = field(default="unknown")  # 'active', 'inactive', 'unknown'
    
    # Device Metadata
    model: Optional[str] = None
    serial_number: Optional[str] = None
    software_version: Optional[str] = None
    
    # Topology Information
    layer: Optional[int] = None  # Network layer (1=access, 2=aggregation, 3=core)
    position: Optional[Dict[str, float]] = None  # X,Y coordinates for visualization
    
    def __post_init__(self):
        """Validate device information"""
        if not self.name:
            raise ValueError("Device name cannot be empty")
        
        if not isinstance(self.device_type, DeviceType):
            raise ValueError("Device type must be a DeviceType enum")
        
        if not isinstance(self.role, DeviceRole):
            raise ValueError("Device role must be a DeviceRole enum")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'device_type': self.device_type.value,
            'role': self.role.value,
            'interfaces': self.interfaces,
            'capabilities': self.capabilities,
            'status': self.status,
            'model': self.model,
            'serial_number': self.serial_number,
            'software_version': self.software_version,
            'layer': self.layer,
            'position': self.position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceInfo':
        """Create DeviceInfo from dictionary"""
        # Convert string enums back to enum values
        if 'device_type' in data and isinstance(data['device_type'], str):
            data['device_type'] = DeviceType(data['device_type'])
        
        if 'role' in data and isinstance(data['role'], str):
            data['role'] = DeviceRole(data['role'])
        
        return cls(**data)
```

### **4. Interface Information Structure**

```python
@dataclass(frozen=True)
class InterfaceInfo:
    """Comprehensive interface information"""
    
    # Basic Information
    name: str
    device: str  # Device name this interface belongs to
    
    # Interface Properties
    interface_type: InterfaceType
    role: InterfaceRole
    status: str = field(default="unknown")  # 'up', 'down', 'unknown'
    
    # VLAN and Network Information
    vlan_id: Optional[int] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    
    # Bundle and Subinterface Information
    bundle_member: Optional[str] = None  # If part of a bundle
    subinterface_id: Optional[int] = None  # If subinterface
    
    # Physical Properties
    speed: Optional[str] = None  # e.g., "10G", "100G"
    duplex: Optional[str] = None  # "full", "half"
    media_type: Optional[str] = None  # "copper", "fiber"
    
    # Configuration
    description: Optional[str] = None
    mtu: Optional[int] = None
    policies: List[str] = field(default_factory=list)
    
    # Topology Information
    connected_to: Optional[str] = None  # Interface it connects to
    connection_type: Optional[str] = None  # "direct", "via_switch", etc.
    
    # DNAAS Bridge-Domain Semantics (Additions)
    vlan_expression: Optional[str] = None    # single/list/range canonical form
    ingress_push: Optional[Dict[str, Any]] = None
    egress_pop: Optional[bool] = None
    swap_behavior: Optional[bool] = None
    applied_template: Optional[Dict[str, Any]] = None  # TemplateRef serialization
    
    def __post_init__(self):
        """Validate interface information"""
        if not self.name:
            raise ValueError("Interface name cannot be empty")
        
        if not self.device:
            raise ValueError("Device name cannot be empty")
        
        if not isinstance(self.interface_type, InterfaceType):
            raise ValueError("Interface type must be an InterfaceType enum")
        
        if not isinstance(self.role, InterfaceRole):
            raise ValueError("Interface role must be an InterfaceRole enum")
        
        # Validate VLAN ID if present
        if self.vlan_id is not None and not (1 <= self.vlan_id <= 4094):
            raise ValueError("VLAN ID must be between 1 and 4094")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'device': self.device,
            'interface_type': self.interface_type.value,
            'role': self.role.value,
            'status': self.status,
            'vlan_id': self.vlan_id,
            'ip_address': self.ip_address,
            'subnet_mask': self.subnet_mask,
            'bundle_member': self.bundle_member,
            'subinterface_id': self.subinterface_id,
            'speed': self.speed,
            'duplex': self.duplex,
            'media_type': self.media_type,
            'description': self.description,
            'mtu': self.mtu,
            'policies': self.policies,
            'connected_to': self.connected_to,
            'connection_type': self.connection_type,
            'vlan_expression': self.vlan_expression,
            'ingress_push': self.ingress_push,
            'egress_pop': self.egress_pop,
            'swap_behavior': self.swap_behavior,
            'applied_template': self.applied_template
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterfaceInfo':
        """Create InterfaceInfo from dictionary"""
        # Convert string enums back to enum values
        if 'interface_type' in data and isinstance(data['interface_type'], str):
            data['interface_type'] = InterfaceType(data['interface_type'])
        
        if 'role' in data and isinstance(data['role'], str):
            data['role'] = InterfaceRole(data['role'])
        
        return cls(**data)
```

### **5. Path Information Structure**

```python
@dataclass(frozen=True)
class PathInfo:
    """Path information between devices"""
    
    # Path Identification
    path_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Endpoints
    source_device: str
    destination_device: str
    
    # Path Properties
    path_type: str = field(default="unknown")  # 'direct', 'via_spine', 'via_superspine'
    intermediate_devices: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)  # Interfaces along the path
    
    # Performance Metrics
    bandwidth: Optional[str] = None  # e.g., "10G", "100G"
    latency: Optional[str] = None  # e.g., "1ms", "5ms"
    
    # Path Status
    status: str = field(default="unknown")  # 'active', 'inactive', 'failed'
    primary: bool = field(default=False)  # Is this the primary path?
    
    # Path Metadata
    cost: Optional[int] = None  # Path cost/weight
    hops: Optional[int] = None  # Number of hops
    
    def __post_init__(self):
        """Validate path information"""
        if not self.source_device:
            raise ValueError("Source device cannot be empty")
        
        if not self.destination_device:
            raise ValueError("Destination device cannot be empty")
        
        if self.source_device == self.destination_device:
            raise ValueError("Source and destination devices cannot be the same")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'path_id': self.path_id,
            'source_device': self.source_device,
            'destination_device': self.destination_device,
            'path_type': self.path_type,
            'intermediate_devices': self.intermediate_devices,
            'interfaces': self.interfaces,
            'bandwidth': self.bandwidth,
            'latency': self.latency,
            'status': self.status,
            'primary': self.primary,
            'cost': self.cost,
            'hops': self.hops
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathInfo':
        """Create PathInfo from dictionary"""
        return cls(**data)
```

### **6. Bridge Domain Configuration Structure**

```python
@dataclass(frozen=True)
class BridgeDomainConfig:
    """Bridge domain configuration information"""
    
    # Basic Information
    name: str
    vlan_id: Optional[int] = None
    
    # Interface Configuration
    interfaces: List[str] = field(default_factory=list)
    
    # Routing and Forwarding
    routing_instance: Optional[str] = None
    forwarding_options: Dict[str, Any] = field(default_factory=dict)
    
    # Policies and Security
    policies: List[str] = field(default_factory=list)
    security_options: Dict[str, Any] = field(default_factory=dict)
    
    # Quality of Service
    qos_options: Dict[str, Any] = field(default_factory=dict)
    
    # Configuration Metadata
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    # DNAAS Bridge-Domain Semantics (Additions)
    bd_type: Optional[BridgeDomainType] = None
    outer_tag_imposition: Optional[OuterTagImposition] = None
    # optional per-interface template mapping (see templates design)
    interface_templates: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate bridge domain configuration"""
        if not self.name:
            raise ValueError("Bridge domain name cannot be empty")
        
        # Validate VLAN ID if present
        if self.vlan_id is not None and not (1 <= self.vlan_id <= 4094):
            raise ValueError("VLAN ID must be between 1 and 4094")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'vlan_id': self.vlan_id,
            'interfaces': self.interfaces,
            'routing_instance': self.routing_instance,
            'forwarding_options': self.forwarding_options,
            'policies': self.policies,
            'security_options': self.security_options,
            'qos_options': self.qos_options,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'created_by': self.created_by,
            'bd_type': self.bd_type.value if self.bd_type else None,
            'outer_tag_imposition': self.outer_tag_imposition.value if self.outer_tag_imposition else None,
            'interface_templates': self.interface_templates
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BridgeDomainConfig':
        """Create BridgeDomainConfig from dictionary"""
        # Convert ISO strings back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'modified_at' in data and isinstance(data['modified_at'], str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        
        # Convert string enums back to enum values
        if 'bd_type' in data and isinstance(data['bd_type'], str):
            data['bd_type'] = BridgeDomainType(data['bd_type'])
        
        if 'outer_tag_imposition' in data and isinstance(data['outer_tag_imposition'], str):
            data['outer_tag_imposition'] = OuterTagImposition(data['outer_tag_imposition'])
        
        return cls(**data)
```

## 📋 **Implementation Checklist**

### **Week 1: Data Structure & Models**

#### **Day 1-2: Core Data Structures**
- [ ] Create `TopologyData` dataclass
- [ ] Create `DeviceInfo` dataclass
- [ ] Create `InterfaceInfo` dataclass
- [ ] Create `PathInfo` dataclass
- [ ] Create `BridgeDomainConfig` dataclass
- [ ] Create all enum classes

#### **Day 3-4: Validation Framework**
- [ ] Create `TopologyValidator` class
- [ ] Implement validation rules
- [ ] Create `ValidationResult` dataclass
- [ ] Add validation to all data classes

#### **Day 5: Database Models**
- [ ] Update `PersonalBridgeDomain` model
- [ ] Create `TopologyDataModel` model
- [ ] Implement data migration strategy
- [ ] Test database operations

#### **Day 6-7: Testing & Documentation**
- [ ] Write comprehensive unit tests
- [ ] Write integration tests
- [ ] Create data migration tests
- [ ] Document all data structures
- [ ] Create usage examples

## 🎯 **Success Criteria for Phase 1**

### **Data Structure Completeness:**
- ✅ **All topology components** represented with proper data classes
- ✅ **Type safety** with Python typing and enums
- ✅ **Data validation** at creation and modification
- ✅ **Serialization/deserialization** for API and storage

### **Database Integration:**
- ✅ **Updated models** using new data structures
- ✅ **Data migration** from old to new format
- ✅ **Backward compatibility** maintained
- ✅ **Efficient storage** and retrieval

### **Validation & Testing:**
- ✅ **Comprehensive validation** rules implemented
- ✅ **Unit tests** for all data structures
- ✅ **Integration tests** with database
- ✅ **Error handling** for invalid data

### **Documentation:**
- ✅ **API documentation** for all data structures
- ✅ **Usage examples** and best practices
- ✅ **Migration guide** for existing data
- ✅ **Validation rules** documentation

## 🚀 **Next Steps After Phase 1**

Once Phase 1 is complete, we'll have:

1. **Solid Foundation**: Standardized data structures for all topology operations
2. **Type Safety**: Compile-time and runtime type checking
3. **Data Validation**: Built-in validation preventing data corruption
4. **Database Integration**: Efficient storage and retrieval
5. **Testing Framework**: Comprehensive test coverage

**This will enable us to move confidently into Phase 2 (Enhanced Scanning) knowing that all data will be properly structured, validated, and stored.**

**Phase 1 is the critical foundation - getting this right will make all subsequent phases much easier and more reliable.**
