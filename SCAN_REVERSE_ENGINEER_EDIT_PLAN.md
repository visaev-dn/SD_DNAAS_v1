# 🔍 Scan→Reverse-Engineer→Edit Workflow: Comprehensive Analysis & Plan

## 📊 **Current State Analysis**

### **What We Currently Have:**
1. **✅ Basic Device Scanning**: `DeviceScanner` can discover devices and basic bridge domain info
2. **✅ Enhanced Topology Scanner**: Framework exists but has gaps in data collection
3. **✅ Database Models**: `PersonalBridgeDomain`, `TopologyScan`, `DeviceInterface` models exist
4. **✅ API Endpoints**: Basic scan and reverse-engineer endpoints implemented
5. **✅ Bridge Domain Builders**: P2P, P2MP, and unified builders ready

### **What's Missing:**
1. **❌ Comprehensive Data Collection**: Current scanning doesn't gather enough topology information
2. **❌ Consistent Data Structure**: No standardized format for topology representation
3. **❌ Path Calculation**: Topology paths not being calculated correctly
4. **❌ Configuration Parsing**: Limited parsing of actual device configs
5. **❌ Edit Capabilities**: No way to modify discovered topologies

## 🎯 **Critical Questions to Answer:**

### **1. Do We Need More Scanning Capabilities?**
**Answer: YES, but strategically focused**

**Current Scanning Gaps:**
- **Interface Details**: Need VLAN assignments, interface roles, bundle configurations
- **Path Information**: Need actual routing and forwarding tables
- **Bridge Domain Configs**: Need complete bridge domain configurations
- **Device Relationships**: Need to understand how devices connect to each other

**What We DON'T Need:**
- Full device configurations (too verbose)
- Historical data (not relevant for topology)
- Performance metrics (not needed for topology)

### **2. Do We Recover Enough Information for Reverse Engineering?**
**Answer: PARTIALLY - We need to enhance data collection**

**Current Recovery:**
- ✅ Device names and basic info
- ✅ Basic bridge domain existence
- ❌ Interface mappings and VLAN assignments
- ❌ Path connectivity between devices
- ❌ Bridge domain configurations

**Required for Reverse Engineering:**
- **Interface Mapping**: Which interfaces belong to which bridge domains
- **VLAN Information**: VLAN IDs and assignments
- **Path Connectivity**: How devices are connected
- **Bridge Domain Configs**: Actual configuration details

## 🏗️ **Proposed Consistent Data Structure**

### **Core Topology Data Structure:**

```python
@dataclass
class TopologyData:
    """Standardized topology data structure"""
    
    # Basic Information
    bridge_domain_name: str
    topology_type: str  # 'p2p', 'p2mp', 'unknown'
    vlan_id: Optional[int]
    confidence_score: float  # 0.0 to 1.0
    
    # Device Information
    devices: List[DeviceInfo]
    
    # Interface Information
    interfaces: List[InterfaceInfo]
    
    # Path Information
    paths: List[PathInfo]
    
    # Bridge Domain Configuration
    bridge_domain_config: BridgeDomainConfig
    
    # Metadata
    discovered_at: datetime
    scan_method: str
    source_data: Dict[str, Any]  # Raw discovery data

@dataclass
class DeviceInfo:
    """Device information structure"""
    name: str
    device_type: str  # 'leaf', 'spine', 'superspine', 'unknown'
    role: str  # 'source', 'destination', 'transit'
    interfaces: List[str]  # Interface names
    capabilities: Dict[str, Any]
    status: str  # 'active', 'inactive', 'unknown'

@dataclass
class InterfaceInfo:
    """Interface information structure"""
    name: str
    device: str
    interface_type: str  # 'ethernet', 'bundle', 'subinterface'
    vlan_id: Optional[int]
    role: str  # 'access', 'uplink', 'downlink', 'transit'
    status: str  # 'up', 'down', 'unknown'
    bundle_member: Optional[str]  # If part of a bundle
    subinterface_id: Optional[int]  # If subinterface

@dataclass
class PathInfo:
    """Path information structure"""
    source_device: str
    destination_device: str
    path_type: str  # 'direct', 'via_spine', 'via_superspine'
    intermediate_devices: List[str]
    interfaces: List[str]  # Interfaces along the path
    bandwidth: Optional[str]
    latency: Optional[str]

@dataclass
class BridgeDomainConfig:
    """Bridge domain configuration structure"""
    name: str
    vlan_id: Optional[int]
    interfaces: List[str]
    routing_instance: Optional[str]
    forwarding_options: Dict[str, Any]
    policies: List[str]
```

## 🚀 **Enhanced Scanning Strategy**

### **Phase 1: Enhanced Data Collection**

```python
class EnhancedTopologyScanner:
    """Enhanced scanner with comprehensive data collection"""
    
    async def scan_bridge_domain_comprehensive(self, bridge_domain_name: str) -> TopologyData:
        """Comprehensive bridge domain scanning"""
        
        # 1. Device Discovery
        devices = await self._discover_devices_in_bridge_domain(bridge_domain_name)
        
        # 2. Interface Mapping
        interfaces = await self._map_interfaces_to_bridge_domain(devices, bridge_domain_name)
        
        # 3. VLAN Discovery
        vlans = await self._discover_vlan_assignments(devices, bridge_domain_name)
        
        # 4. Path Calculation
        paths = await self._calculate_topology_paths(devices, interfaces)
        
        # 5. Bridge Domain Configuration
        bd_config = await self._extract_bridge_domain_config(devices, bridge_domain_name)
        
        # 6. Topology Analysis
        topology_type = self._analyze_topology_type(devices, interfaces, paths)
        confidence = self._calculate_confidence_score(devices, interfaces, paths, bd_config)
        
        return TopologyData(
            bridge_domain_name=bridge_domain_name,
            topology_type=topology_type,
            vlan_id=vlans.get('primary_vlan'),
            confidence_score=confidence,
            devices=devices,
            interfaces=interfaces,
            paths=paths,
            bridge_domain_config=bd_config,
            discovered_at=datetime.now(),
            scan_method='comprehensive',
            source_data={'devices': devices, 'interfaces': interfaces}
        )
    
    async def _discover_devices_in_bridge_domain(self, bridge_domain_name: str) -> List[DeviceInfo]:
        """Discover all devices participating in the bridge domain"""
        # Implementation: Use existing DeviceScanner + enhanced discovery
        pass
    
    async def _map_interfaces_to_bridge_domain(self, devices: List[DeviceInfo], 
                                            bridge_domain_name: str) -> List[InterfaceInfo]:
        """Map all interfaces that belong to the bridge domain"""
        # Implementation: Parse device configs for interface mappings
        pass
    
    async def _discover_vlan_assignments(self, devices: List[DeviceInfo], 
                                       bridge_domain_name: str) -> Dict[str, Any]:
        """Discover VLAN assignments and configurations"""
        # Implementation: Extract VLAN info from device configs
        pass
    
    async def _calculate_topology_paths(self, devices: List[DeviceInfo], 
                                      interfaces: List[InterfaceInfo]) -> List[PathInfo]:
        """Calculate all possible paths between devices"""
        # Implementation: Use routing tables and interface mappings
        pass
    
    async def _extract_bridge_domain_config(self, devices: List[DeviceInfo], 
                                          bridge_domain_name: str) -> BridgeDomainConfig:
        """Extract complete bridge domain configuration"""
        # Implementation: Parse bridge domain configs from devices
        pass
```

### **Phase 2: Configuration Parsing Engine**

```python
class DNOSConfigurationParser:
    """Enhanced DNOS configuration parser"""
    
    def parse_bridge_domain_config(self, config_text: str, bridge_domain_name: str) -> BridgeDomainConfig:
        """Parse bridge domain configuration from device config"""
        # Enhanced parsing with more patterns
        pass
    
    def parse_interface_config(self, config_text: str, interface_name: str) -> InterfaceInfo:
        """Parse interface configuration from device config"""
        # Enhanced parsing with VLAN, bundle, and role detection
        pass
    
    def parse_vlan_config(self, config_text: str) -> List[Dict[str, Any]]:
        """Parse VLAN configurations from device config"""
        # Enhanced VLAN parsing with assignments
        pass
```

## 🔄 **Reverse Engineering Workflow**

### **Enhanced Reverse Engineering Process:**

```python
class EnhancedReverseEngineer:
    """Enhanced reverse engineering with topology data"""
    
    def reverse_engineer_from_topology(self, topology_data: TopologyData) -> Configuration:
        """Reverse engineer configuration from topology data"""
        
        # 1. Validate topology data
        validation_result = self._validate_topology_data(topology_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid topology data: {validation_result.errors}")
        
        # 2. Determine builder type
        builder_type = self._determine_builder_type(topology_data)
        
        # 3. Generate configuration using appropriate builder
        if builder_type == 'p2p':
            config = self._generate_p2p_config(topology_data)
        elif builder_type == 'p2mp':
            config = self._generate_p2mp_config(topology_data)
        else:
            config = self._generate_unified_config(topology_data)
        
        # 4. Validate generated configuration
        config_validation = self._validate_generated_config(config, topology_data)
        
        return Configuration(
            topology_data=topology_data,
            generated_config=config,
            builder_type=builder_type,
            validation_result=config_validation
        )
    
    def _determine_builder_type(self, topology_data: TopologyData) -> str:
        """Determine which builder to use based on topology"""
        # Logic to determine P2P vs P2MP based on device count, interface count, etc.
        pass
```

## ✏️ **Edit Capabilities**

### **Topology Editor Interface:**

```python
class TopologyEditor:
    """Interactive topology editor"""
    
    def edit_topology(self, topology_data: TopologyData, 
                     edits: List[TopologyEdit]) -> TopologyData:
        """Apply edits to topology data"""
        
        # 1. Validate edits
        self._validate_edits(topology_data, edits)
        
        # 2. Apply edits
        modified_topology = self._apply_edits(topology_data, edits)
        
        # 3. Recalculate paths if needed
        if self._paths_affected(edits):
            modified_topology.paths = self._recalculate_paths(modified_topology)
        
        # 4. Update confidence score
        modified_topology.confidence_score = self._recalculate_confidence(modified_topology)
        
        return modified_topology
    
    def _validate_edits(self, topology_data: TopologyData, edits: List[TopologyEdit]):
        """Validate that edits are valid"""
        # Check for conflicts, invalid configurations, etc.
        pass

@dataclass
class TopologyEdit:
    """Represents a topology edit operation"""
    edit_type: str  # 'add_device', 'remove_device', 'modify_interface', 'change_vlan'
    target: str  # What is being edited
    old_value: Any  # Previous value
    new_value: Any  # New value
    validation_rules: List[str]  # Rules to validate this edit
```

## 📋 **Implementation Plan**

### **Phase 1: Data Structure & Models (Week 1)**
1. **Create standardized data classes** for topology representation
2. **Update database models** to use new structures
3. **Create data validation** for topology data

### **Phase 2: Enhanced Scanning (Week 2)**
1. **Implement comprehensive device scanning** with interface mapping
2. **Add VLAN discovery** and assignment mapping
3. **Implement path calculation** using routing tables

### **Phase 3: Configuration Parsing (Week 3)**
1. **Enhance DNOS configuration parser** for bridge domains
2. **Add interface configuration parsing** with role detection
3. **Implement VLAN configuration parsing**

### **Phase 4: Reverse Engineering (Week 4)**
1. **Implement enhanced reverse engineering** using topology data
2. **Add builder type detection** logic
3. **Create configuration validation** system

### **Phase 5: Edit Capabilities (Week 5)**
1. **Implement topology editor** interface
2. **Add edit validation** and conflict detection
3. **Create edit history** and rollback capabilities

### **Phase 6: Integration & Testing (Week 6)**
1. **Integrate all components** into unified workflow
2. **Create comprehensive testing** for entire workflow
3. **Performance optimization** and error handling

## 🎯 **Success Criteria**

### **Scan Capabilities:**
- ✅ **Device Discovery**: Find all devices in bridge domain
- ✅ **Interface Mapping**: Map all interfaces to bridge domain
- ✅ **VLAN Discovery**: Discover VLAN assignments and configurations
- ✅ **Path Calculation**: Calculate all possible paths between devices
- ✅ **Configuration Extraction**: Extract complete bridge domain configs

### **Reverse Engineering:**
- ✅ **Topology Analysis**: Determine topology type (P2P/P2MP)
- ✅ **Builder Selection**: Automatically select appropriate builder
- ✅ **Configuration Generation**: Generate valid configurations
- ✅ **Validation**: Validate generated configurations

### **Edit Capabilities:**
- ✅ **Interactive Editing**: Modify discovered topologies
- ✅ **Validation**: Ensure edits are valid and consistent
- ✅ **Conflict Detection**: Detect and resolve edit conflicts
- ✅ **History**: Track edit history with rollback capability

## 🚀 **Next Steps**

1. **Review and approve** this data structure design
2. **Prioritize implementation phases** based on business needs
3. **Create detailed technical specifications** for each phase
4. **Begin implementation** with Phase 1 (Data Structure & Models)

**This plan provides a solid foundation for a comprehensive Scan→Reverse-Engineer→Edit workflow that will be both powerful and maintainable.**

## ➕ Template Detection & BD Semantics (Integrated)

Enhance scanning to produce template-aware topology:

- After interface parsing, compute:
  - `vlan_expression` from `vlan-id`/`vlan-id list`
  - `ingress_push`, `egress_pop`, `swap_behavior` from `vlan-manipulation`
- Run `TemplateMatcher` per interface → set `applied_template`
- Derive BD-level semantics:
  - `bd_type` = LOCAL (leaf-only) or GLOBAL (uplinks applied)
  - `outer_tag_imposition` = LEAF if push/pop present; else EDGE for double-tag-at-edge
- Populate `BridgeDomainConfig.interface_templates` and `TopologyData.template_summary`

Update Enhanced Scanner flow:
1. Device discovery
2. Interface mapping + normalization
3. VLAN discovery
4. Path calculation
5. BD config extraction
6. Template detection + BD semantics assignment (new)
7. Validation (template + topology)

Validation additions:
- ACCESS/DOT1Q require push (ingress) + pop (egress)
- TRUNK_SINGLE forbids vlan-list; requires subinterface `.VID`
- DOT1Q_ALL requires `1-4094` full range
- DOT1Q_SPLIT requires disjoint ranges across subinterfaces
- GLOBAL BDs enforce unique outer VLANs (policy)
