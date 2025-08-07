# Phase 4: Enhanced Topology Scanner & Bridge Domain Editor

## Overview

Phase 4 focuses on implementing advanced scanning, parsing, and visualization capabilities for bridge domains. This phase builds upon the existing bridge domain discovery and user management systems to provide comprehensive topology analysis and editing capabilities.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 4 Components                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Enhanced Topology Scanner                              │
│ 2. Bridge Domain Editor (Visual)                          │
│ 3. Configuration Parsing Engine                           │
│ 4. Interactive Topology Visualization                     │
└─────────────────────────────────────────────────────────────┘
```

## 1. Enhanced Topology Scanner

### 1.1 Current State Analysis

**Existing Components:**
- `config_engine/bridge_domain_discovery.py` - Basic discovery prototype
- `config_engine/device_scanner.py` - Device scanning capabilities
- `api_server.py` - Placeholder scan endpoint (`/api/configurations/<name>/scan`)

**Gaps to Address:**
- No actual configuration parsing from devices
- No topology reverse engineering
- No path calculation
- No device interface mapping

### 1.2 Enhanced Scanner Design

#### Core Components:

```python
# Enhanced Scanner Architecture
class EnhancedTopologyScanner:
    def __init__(self):
        self.device_scanner = DeviceScanner()
        self.config_parser = ConfigurationParser()
        self.topology_builder = TopologyBuilder()
        self.path_calculator = PathCalculator()
    
    async def scan_bridge_domain(self, bridge_domain_name: str) -> TopologyResult:
        # 1. Discover all devices involved
        # 2. Parse configurations from each device
        # 3. Extract interface mappings and VLAN configurations
        # 4. Build topology graph
        # 5. Calculate paths and connections
        # 6. Generate topology visualization data
        pass
```

#### Database Schema Extensions:

```sql
-- New tables for topology scanning
CREATE TABLE topology_scans (
    id INTEGER PRIMARY KEY,
    bridge_domain_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    scan_status TEXT DEFAULT 'pending',
    scan_started_at TIMESTAMP,
    scan_completed_at TIMESTAMP,
    topology_data JSON,
    device_mappings JSON,
    path_calculations JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE device_interfaces (
    id INTEGER PRIMARY KEY,
    device_name TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    vlan_id INTEGER,
    bridge_domain_name TEXT,
    interface_type TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE topology_paths (
    id INTEGER PRIMARY KEY,
    bridge_domain_name TEXT NOT NULL,
    source_device TEXT NOT NULL,
    destination_device TEXT NOT NULL,
    path_data JSON,
    hop_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 Implementation Plan

#### Phase 4.1: Enhanced Scanner Core
1. **Device Discovery Enhancement**
   - Extend existing `DeviceScanner` to discover all devices in a bridge domain
   - Implement VLAN-based device filtering
   - Add device connectivity mapping

2. **Configuration Parsing**
   - Parse actual DNOS configurations from devices
   - Extract VLAN configurations, interface mappings
   - Parse routing tables and forwarding information

3. **Topology Building**
   - Build graph representation of bridge domain topology
   - Map device interconnections
   - Identify access circuits and core paths

#### Phase 4.2: Path Calculation
1. **Path Discovery**
   - Calculate all possible paths between devices
   - Identify primary and backup paths
   - Map VLAN forwarding paths

2. **Interface Mapping**
   - Map device interfaces to bridge domain
   - Track interface status and configurations
   - Identify interface types (access, trunk, etc.)

## 2. Bridge Domain Editor (Visual)

### 2.1 Current State Analysis

**Existing Components:**
- Basic bridge domain builders (P2P, P2MP, Unified)
- Configuration generation capabilities
- No visual editing interface

**Gaps to Address:**
- No visual topology editor
- No drag-and-drop interface
- No real-time topology validation
- No visual configuration preview

### 2.2 Visual Editor Design

#### Core Components:

```typescript
// Visual Editor Architecture
interface TopologyNode {
  id: string;
  type: 'device' | 'interface' | 'vlan';
  position: { x: number; y: number };
  data: {
    name: string;
    deviceType?: string;
    interfaceType?: string;
    vlanId?: number;
    status: 'active' | 'inactive' | 'error';
  };
}

interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  type: 'p2p' | 'p2mp' | 'access';
  data: {
    bandwidth?: number;
    status: 'active' | 'inactive';
    vlanId?: number;
  };
}

interface TopologyEditor {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  selectedElements: string[];
  zoom: number;
  pan: { x: number; y: number };
}
```

#### React Components:

```typescript
// Main Editor Components
<TopologyCanvas>
  <TopologyToolbar />
  <TopologyGraph>
    <DeviceNode />
    <InterfaceNode />
    <VlanNode />
    <ConnectionEdge />
  </TopologyGraph>
  <TopologyPanel />
</TopologyCanvas>
```

### 2.3 Implementation Plan

#### Phase 4.3: Visual Editor Foundation
1. **Canvas Implementation**
   - React Flow or D3.js for graph visualization
   - Drag-and-drop node placement
   - Connection drawing and validation

2. **Node Types**
   - Device nodes (spine, leaf, superspine)
   - Interface nodes (access circuits)
   - VLAN nodes (bridge domains)

3. **Interaction Features**
   - Node selection and editing
   - Connection creation and deletion
   - Real-time validation

#### Phase 4.4: Editor Functionality
1. **Topology Operations**
   - Add/remove devices and interfaces
   - Modify connections and paths
   - Change VLAN assignments

2. **Configuration Generation**
   - Real-time configuration preview
   - Validation against device capabilities
   - Conflict detection and resolution

## 3. Configuration Parsing Engine

### 3.1 Current State Analysis

**Existing Components:**
- Basic configuration generation in builders
- No actual device configuration parsing
- No reverse engineering from live devices

**Gaps to Address:**
- No parsing of actual DNOS configurations
- No extraction of interface and VLAN information
- No topology reverse engineering

### 3.2 Parser Design

#### Core Components:

```python
class DNOSConfigurationParser:
    def __init__(self):
        self.ssh_manager = SSHManager()
        self.config_patterns = self._load_patterns()
    
    def parse_device_config(self, device_name: str) -> DeviceConfig:
        # Connect to device via SSH
        # Retrieve running configuration
        # Parse interface configurations
        # Extract VLAN information
        # Parse routing and forwarding tables
        pass
    
    def extract_vlan_config(self, config_text: str) -> List[VlanConfig]:
        # Parse VLAN configurations
        # Extract interface assignments
        # Map VLAN to bridge domains
        pass
    
    def extract_interface_config(self, config_text: str) -> List[InterfaceConfig]:
        # Parse interface configurations
        # Extract VLAN assignments
        # Map interface types and status
        pass
```

#### Configuration Patterns:

```python
# DNOS Configuration Patterns
CONFIG_PATTERNS = {
    'vlan': r'vlan\s+(\d+)\s*{([^}]+)}',
    'interface': r'interface\s+(\S+)\s*{([^}]+)}',
    'bridge_domain': r'bridge-domain\s+(\S+)\s*{([^}]+)}',
    'routing': r'ip\s+route\s+(\S+)\s+(\S+)',
    'forwarding': r'forwarding\s+(\S+)\s+(\S+)',
}
```

### 3.3 Implementation Plan

#### Phase 4.5: Parser Core
1. **SSH Integration**
   - Extend existing SSH manager
   - Add configuration retrieval
   - Implement error handling

2. **Pattern Matching**
   - Implement DNOS-specific patterns
   - Parse VLAN configurations
   - Extract interface mappings

3. **Data Extraction**
   - Build configuration data structures
   - Map VLAN to bridge domains
   - Extract topology information

#### Phase 4.6: Reverse Engineering
1. **Topology Reconstruction**
   - Build topology from parsed configurations
   - Map device interconnections
   - Identify bridge domain boundaries

2. **Path Analysis**
   - Calculate forwarding paths
   - Identify access circuits
   - Map VLAN forwarding

## 4. Interactive Topology Visualization

### 4.1 Current State Analysis

**Existing Components:**
- Basic dashboard with statistics
- No interactive topology diagrams
- No real-time topology updates

**Gaps to Address:**
- No visual topology representation
- No interactive exploration
- No real-time status updates

### 4.2 Visualization Design

#### Core Components:

```typescript
interface TopologyVisualization {
  // Graph representation
  nodes: DeviceNode[];
  edges: ConnectionEdge[];
  
  // Interaction state
  selectedNode?: string;
  hoveredNode?: string;
  zoomLevel: number;
  panOffset: { x: number; y: number };
  
  // Real-time updates
  deviceStatus: Map<string, DeviceStatus>;
  connectionStatus: Map<string, ConnectionStatus>;
}
```

#### React Components:

```typescript
// Visualization Components
<TopologyViewer>
  <TopologyGraph>
    <DeviceNode />
    <ConnectionEdge />
    <VlanOverlay />
  </TopologyGraph>
  <TopologyControls>
    <ZoomControls />
    <FilterControls />
    <StatusLegend />
  </TopologyControls>
  <TopologyDetails />
</TopologyViewer>
```

### 4.3 Implementation Plan

#### Phase 4.7: Visualization Foundation
1. **Graph Rendering**
   - Implement graph visualization library
   - Device and connection rendering
   - Zoom and pan controls

2. **Interactive Features**
   - Node selection and highlighting
   - Connection path highlighting
   - Tooltip information display

3. **Real-time Updates**
   - WebSocket integration for live updates
   - Device status indicators
   - Connection status visualization

#### Phase 4.8: Advanced Features
1. **Topology Exploration**
   - Path highlighting and tracing
   - VLAN overlay visualization
   - Device grouping and filtering

2. **Performance Optimization**
   - Large topology handling
   - Efficient rendering
   - Memory management

## Implementation Timeline

### Week 1-2: Enhanced Scanner Core
- [ ] Extend device scanner for bridge domain discovery
- [ ] Implement configuration parsing from devices
- [ ] Build topology graph construction
- [ ] Add database schema for topology data

### Week 3-4: Path Calculation & Interface Mapping
- [ ] Implement path calculation algorithms
- [ ] Add interface mapping and status tracking
- [ ] Build VLAN forwarding path analysis
- [ ] Create topology validation logic

### Week 5-6: Visual Editor Foundation
- [ ] Set up React Flow or D3.js integration
- [ ] Implement basic canvas and node rendering
- [ ] Add drag-and-drop functionality
- [ ] Create node and edge components

### Week 7-8: Editor Functionality
- [ ] Implement topology operations (add/remove/modify)
- [ ] Add real-time configuration preview
- [ ] Build validation and conflict detection
- [ ] Create configuration generation from visual editor

### Week 9-10: Configuration Parsing Engine
- [ ] Extend SSH manager for configuration retrieval
- [ ] Implement DNOS configuration patterns
- [ ] Build data extraction and mapping
- [ ] Add reverse engineering capabilities

### Week 11-12: Interactive Visualization
- [ ] Implement graph visualization
- [ ] Add interactive features and controls
- [ ] Integrate real-time updates
- [ ] Build topology exploration features

## Technical Considerations

### 1. Performance
- **Large Topologies**: Handle networks with 100+ devices
- **Real-time Updates**: WebSocket integration for live status
- **Memory Management**: Efficient graph rendering and updates

### 2. Scalability
- **Database Optimization**: Efficient topology data storage
- **Caching**: Cache parsed configurations and topology data
- **Async Processing**: Background scanning and parsing

### 3. Security
- **SSH Authentication**: Secure device access
- **Data Validation**: Validate parsed configurations
- **Access Control**: User-based topology access

### 4. Integration
- **Existing Systems**: Leverage current bridge domain builders
- **User Management**: Integrate with Phase 3 user system
- **API Consistency**: Maintain API design patterns

## Success Metrics

### 1. Functionality
- [ ] Successfully scan and parse bridge domain topologies
- [ ] Visual editor allows topology modification
- [ ] Real-time topology visualization
- [ ] Configuration generation from visual editor

### 2. Performance
- [ ] Scan completion within 30 seconds for typical topologies
- [ ] Visual editor responsive with 100+ device topologies
- [ ] Real-time updates with <1 second latency

### 3. Usability
- [ ] Intuitive visual editor interface
- [ ] Clear topology visualization
- [ ] Effective error handling and feedback

## Risk Mitigation

### 1. Technical Risks
- **Complex Parsing**: Start with simple DNOS patterns, expand gradually
- **Visual Editor Complexity**: Use proven libraries (React Flow/D3.js)
- **Performance Issues**: Implement progressive loading and optimization

### 2. Integration Risks
- **Existing Code**: Maintain backward compatibility
- **Database Changes**: Use migrations for schema updates
- **API Changes**: Version APIs appropriately

### 3. User Experience Risks
- **Complex UI**: Start with basic features, add complexity gradually
- **Learning Curve**: Provide tutorials and documentation
- **Error Handling**: Comprehensive error messages and recovery

## Next Steps

1. **Review and Approve Design**: Confirm approach with stakeholders
2. **Set Up Development Environment**: Prepare tools and libraries
3. **Begin Phase 4.1**: Start with Enhanced Scanner Core
4. **Regular Reviews**: Weekly progress reviews and adjustments

---

This design provides a comprehensive roadmap for implementing advanced scanning, editing, and visualization capabilities while building upon existing systems and maintaining consistency with the current architecture. 