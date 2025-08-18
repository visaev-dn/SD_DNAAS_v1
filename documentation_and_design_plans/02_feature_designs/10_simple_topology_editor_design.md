# Simple Topology Editor Design Plan

## 🎯 **Overview**

A simplified, user-friendly topology editor that allows users to make basic changes to discovered network topologies without overwhelming complexity. The editor focuses on core operations: changing AC interfaces, adding/removing devices, and basic property editing.

## 🏗️ **Core Design Principles**

1. **Simplicity First**: Minimal UI complexity, clear operations
2. **Backend Conformity**: Strictly follows existing backend data structures and logic
3. **Data Integrity**: Never lose original scan data, maintain audit trail
4. **Real-time Validation**: Immediate feedback on changes
5. **Progressive Enhancement**: Start simple, add features incrementally

---

## 🔄 **Backend Integration & Data Flow**

### **Critical: Conform to Existing Backend Logic**

The editor MUST work within the established backend architecture and data flow:

```
Scan Result → Database Storage → Reverse Engineer → Configuration → Edit → Deploy
```

### **Data Structure Conformity**

#### **1. Input Data Format (From Backend)**
```typescript
// The editor receives data in the format the backend provides:
interface BackendTopologyData {
  // After SCAN (preserved format)
  scanData?: {
    devices: {
      [deviceName: string]: {
        device_type: 'leaf' | 'spine' | 'superspine';
        admin_state: 'enabled' | 'disabled';
        interfaces: Array<{
          name: string;
          role: 'access' | 'uplink' | 'downlink';
          type: 'subinterface';
          vlan_id: number;
        }>;
      };
    };
    topology_analysis: {
      access_interfaces: number;
      topology_type: 'p2p' | 'p2mp';
      path_complexity: string;
    };
  };
  
  // After REVERSE ENGINEER (builder format)
  builderData?: {
    builder_input: {
      devices: string[];
      interfaces: Array<{
        device_name: string;
        name: string;
        interface_type: string;
        status: string;
        vlan_id: number;
      }>;
    };
    path_calculation: {
      source_leaf: string;
      destinations: Record<string, any>;
    };
  };
  
  // Final configuration data
  configurationData?: {
    id: number;
    service_name: string;
    vlan_id: number;
    config_source: 'reverse_engineered';
    topology_data: any; // Original scan data
    builder_input: any; // Builder-ready data
  };
}
```

#### **2. Output Data Format (To Backend)**
```typescript
// The editor MUST output data in the format the backend expects:
interface EditorOutputData {
  // For saving changes
  service_name: string;
  vlan_id: number;
  topology_type: 'p2p' | 'p2mp';
  
  // Device-centric format (what backend expects)
  config_data: {
    devices: {
      [deviceName: string]: string[]; // Array of CLI commands
    };
    topology_type: string;
    topology_analysis: {
      total_interfaces: number;
      access_interfaces: number;
      path_complexity: string;
    };
  };
  
  // Metadata for backend processing
  config_source: 'reverse_engineered';
  builder_type: 'unified' | 'p2mp' | 'enhanced';
  derived_from_scan_id: number;
}
```

---

## 🎨 **UI Design & Layout**

### **Simple Layout Structure**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TOPOLOGY EDITOR: g_visaev_v251                                    [SAVE] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        CURRENT TOPOLOGY                                 │ │
│ │                                                                         │ │
│ │  [DNAAS-LEAF-B14] ──── [DNAAS-SPINE-B09] ──── [DNAAS-LEAF-B10]        │ │
│ │      │                        │                        │               │ │
│ │  [ge100-0/0/12]         [bundle-60001]           [ge100-0/0/3]        │ │
│ │      │                        │                        │               │ │
│ │  [VLAN 251]              [VLAN 251]              [VLAN 251]           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        EDITING TOOLS                                   │ │
│ │                                                                         │ │
│ │ [➕ Add Device] [🔌 Add Interface] [✏️ Edit] [🗑️ Remove] [🔄 Reset]    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        VALIDATION                                       │ │
│ │ ✅ Topology valid  ⚠️ 3 devices, 4 interfaces                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Core UI Components**

#### **1. Topology Display (Main Area)**
- **Device Cards**: Simple rectangles showing device info
- **Interface Lists**: Bullet points under each device
- **Connection Lines**: Straight lines between connected devices
- **Color Coding**: Green for AC interfaces, Gray for uplink

#### **2. Simple Toolbar**
- **Add Device**: Add new device to topology
- **Add Interface**: Add new interface to existing device
- **Edit**: Modify existing properties
- **Remove**: Remove device or interface
- **Reset**: Return to original state

#### **3. Validation Panel**
- **Real-time Status**: Shows validation results
- **Simple Indicators**: ✅ ❌ ⚠️ for different states
- **Error Messages**: Clear explanation of issues

---

## 🛠️ **Core Editing Operations**

### **1. 🔌 Change AC Interface**
**Backend Conformity**: Must maintain interface role classification and VLAN consistency

```typescript
// Operation Flow:
1. User clicks on interface name
2. System shows available interfaces from backend scan data
3. User selects new interface
4. System validates:
   - Interface not used elsewhere
   - Interface exists on device
   - VLAN ID consistency maintained
5. Update topology data
6. Regenerate backend-compatible format
```

**Backend Data Impact**:
- Updates `scanData.devices[deviceName].interfaces[]`
- Maintains `topology_analysis.access_interfaces` count
- Preserves `builder_input.interfaces[]` mapping

### **2. ➕ Add Device**
**Backend Conformity**: Must follow existing device naming conventions and add to all relevant data structures

```typescript
// Operation Flow:
1. User clicks "Add Device"
2. System shows available device names from backend inventory
3. User selects device type and name
4. System adds device with default interfaces:
   - AC interface: ge100-0/0/X.251
   - Uplink interface: bundle-XXXXX.251
5. Update all backend data structures
6. Regenerate path calculations
```

**Backend Data Impact**:
- Adds to `scanData.devices`
- Updates `builder_input.devices[]`
- Regenerates `path_calculation.destinations`
- Updates `topology_analysis` counts

### **3. 🔌 Add Interface**
**Backend Conformity**: Must maintain interface naming conventions and add to device configurations

```typescript
// Operation Flow:
1. User clicks "Add Interface"
2. System shows target device selection
3. User chooses interface type and number
4. System adds interface:
   - AC: ge100-0/0/X.251
   - Uplink: bundle-XXXXX.251
5. Update device interface lists
6. Regenerate backend data
```

**Backend Data Impact**:
- Updates `scanData.devices[deviceName].interfaces[]`
- Adds to `builder_input.interfaces[]`
- Updates `topology_analysis.total_interfaces`

### **4. 🗑️ Remove Device**
**Backend Conformity**: Must cleanly remove from all data structures and update path calculations

```typescript
// Operation Flow:
1. User selects device to remove
2. System shows impact analysis:
   - Which interfaces will be removed
   - How paths will be affected
3. User confirms removal
4. System removes device from all data structures
5. Regenerate topology without removed device
6. Update path calculations
```

**Backend Data Impact**:
- Removes from `scanData.devices`
- Updates `builder_input.devices[]`
- Regenerates `path_calculation.destinations`
- Updates `topology_analysis` counts

### **5. ✏️ Edit Basic Properties**
**Backend Conformity**: Must update all related data structures consistently

```typescript
// Operation Flow:
1. User clicks on property (VLAN ID, service name)
2. System shows edit form
3. User makes change
4. System updates all related data:
   - All interfaces get new VLAN ID
   - Service name updates throughout
5. Regenerate backend-compatible format
```

**Backend Data Impact**:
- Updates `scanData.devices[].interfaces[].vlan_id`
- Updates `builder_input.interfaces[].vlan_id`
- Updates `configurationData.vlan_id`
- Updates `configurationData.service_name`

---

## 🔧 **Backend Integration Points**

### **Critical API Endpoints**

#### **1. Load Topology Data**
```typescript
// GET /api/configurations/{id}/topology
// Returns: Complete topology data in backend format
interface LoadTopologyResponse {
  success: boolean;
  scanData: ScanData;
  builderData: BuilderData;
  configurationData: ConfigurationData;
}
```

#### **2. Save Topology Changes**
```typescript
// PUT /api/configurations/{id}/topology
// Sends: Editor output data in backend-compatible format
interface SaveTopologyRequest {
  service_name: string;
  vlan_id: number;
  topology_type: string;
  config_data: {
    devices: Record<string, string[]>;
    topology_type: string;
    topology_analysis: any;
  };
  metadata: {
    config_source: string;
    builder_type: string;
    derived_from_scan_id: number;
  };
}
```

#### **3. Validate Topology**
```typescript
// POST /api/configurations/{id}/validate
// Returns: Validation results
interface ValidationResponse {
  success: boolean;
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}
```

### **Data Transformation Functions**

#### **1. Backend to Editor Format**
```typescript
const transformBackendToEditor = (backendData: BackendTopologyData) => {
  // Transform backend data to editor-friendly format
  // Maintain all original data for backend compatibility
  return {
    devices: extractDevices(backendData),
    interfaces: extractInterfaces(backendData),
    connections: extractConnections(backendData),
    metadata: extractMetadata(backendData)
  };
};
```

#### **2. Editor to Backend Format**
```typescript
const transformEditorToBackend = (editorData: EditorTopologyData) => {
  // Transform editor data back to backend-compatible format
  // This MUST match what the backend expects
  return {
    service_name: editorData.serviceName,
    vlan_id: editorData.vlanId,
    config_data: {
      devices: generateDeviceConfigs(editorData),
      topology_type: editorData.topologyType,
      topology_analysis: generateTopologyAnalysis(editorData)
    }
  };
};
```

---

## ✅ **Validation & Backend Conformity**

### **Critical Validation Rules**

#### **1. Data Structure Validation**
```typescript
const validateBackendConformity = (data: any) => {
  const errors = [];
  
  // Must have required backend fields
  if (!data.config_data?.devices) {
    errors.push('Missing required config_data.devices structure');
  }
  
  // Must maintain device-centric format
  if (typeof data.config_data.devices !== 'object') {
    errors.push('devices must be object with device names as keys');
  }
  
  // Must have CLI commands for each device
  Object.entries(data.config_data.devices).forEach(([device, commands]) => {
    if (!Array.isArray(commands)) {
      errors.push(`Device ${device} must have array of CLI commands`);
    }
  });
  
  return errors;
};
```

#### **2. Interface Consistency Validation**
```typescript
const validateInterfaceConsistency = (data: any) => {
  const errors = [];
  
  // All interfaces must have same VLAN ID
  const vlanIds = new Set();
  Object.values(data.config_data.devices).flat().forEach(command => {
    const vlanMatch = command.match(/vlan-id\s+(\d+)/);
    if (vlanMatch) {
      vlanIds.add(vlanMatch[1]);
    }
  });
  
  if (vlanIds.size > 1) {
    errors.push('All interfaces must use the same VLAN ID');
  }
  
  return errors;
};
```

#### **3. Path Validation**
```typescript
const validatePathIntegrity = (data: any) => {
  const errors = [];
  
  // Must have source and destinations
  if (!data.path_calculation?.source_leaf) {
    errors.push('Missing source leaf device');
  }
  
  if (!data.path_calculation?.destinations) {
    errors.push('Missing destination devices');
  }
  
  // No circular paths
  const hasCircularPath = checkForCircularPaths(data);
  if (hasCircularPath) {
    errors.push('Circular network paths detected');
  }
  
  return errors;
};
```

---

## 🚀 **Implementation Phases**

### **Phase 1: Core Backend Integration (Critical)**
1. **Data Loading**: Load topology data from backend APIs
2. **Data Display**: Show topology in simple card format
3. **Data Saving**: Save changes in backend-compatible format
4. **Basic Validation**: Validate data structure conformity

### **Phase 2: Core Editing Operations**
1. **Change AC Interface**: Modify interface assignments
2. **Add Device**: Add new devices to topology
3. **Add Interface**: Add new interfaces to devices
4. **Remove Device**: Remove devices from topology
5. **Edit Properties**: Modify basic properties

### **Phase 3: Enhanced Features**
1. **Real-time Validation**: Immediate feedback on changes
2. **Conflict Resolution**: Handle concurrent edit conflicts
3. **Undo/Redo**: Basic change history
4. **Export/Import**: Save/load topology configurations

---

## ⚠️ **Critical Backend Conformity Requirements**

### **1. Data Structure Preservation**
- **NEVER** modify the original scan data structure
- **ALWAYS** maintain the device-centric format the backend expects
- **PRESERVE** all metadata fields required by backend

### **2. API Contract Compliance**
- **STRICTLY** follow the API endpoint specifications
- **MAINTAIN** backward compatibility with existing backend
- **VALIDATE** all data before sending to backend

### **3. Error Handling**
- **GRACEFULLY** handle backend errors and timeouts
- **PROVIDE** clear error messages to users
- **MAINTAIN** data integrity even during failures

### **4. Performance Considerations**
- **OPTIMIZE** data transformations for large topologies
- **CACHE** frequently accessed data appropriately
- **MINIMIZE** API calls to backend

---

## 🧪 **Testing Strategy**

### **1. Backend Conformity Testing**
- **Data Format Tests**: Verify output matches backend expectations
- **API Contract Tests**: Test all API endpoints with valid/invalid data
- **Error Handling Tests**: Test backend error scenarios

### **2. Integration Testing**
- **End-to-End Tests**: Test complete edit → save → deploy flow
- **Data Persistence Tests**: Verify changes are properly saved
- **Validation Tests**: Test all validation rules

### **3. User Experience Testing**
- **Usability Tests**: Test with actual network engineers
- **Performance Tests**: Test with large topologies
- **Error Recovery Tests**: Test error scenarios and recovery

---

## 📋 **Success Criteria**

### **1. Backend Integration**
- ✅ All data transformations maintain backend compatibility
- ✅ API calls follow established patterns
- ✅ Error handling matches backend expectations

### **2. User Experience**
- ✅ Users can make basic topology changes easily
- ✅ Changes are validated in real-time
- ✅ Clear feedback on all operations

### **3. Data Integrity**
- ✅ Original scan data is never lost
- ✅ All changes are properly tracked
- ✅ Validation prevents invalid configurations

### **4. Performance**
- ✅ Editor responds quickly to user actions
- ✅ Large topologies are handled efficiently
- ✅ Backend operations complete in reasonable time

---

## 🔮 **Future Considerations**

### **1. Advanced Features**
- **Template System**: Pre-built topology templates
- **Bulk Operations**: Change multiple elements at once
- **Advanced Validation**: Network-specific rule checking

### **2. Collaboration Features**
- **Multi-user Editing**: Collaborative topology editing
- **Change Approval**: Workflow for change approval
- **Version Control**: Track topology versions over time

### **3. Integration Enhancements**
- **Network Monitoring**: Real-time network state integration
- **Automated Validation**: AI-assisted topology validation
- **Deployment Integration**: Direct deployment from editor

---

## 📚 **References**

- [Bridge Domain Topology Editor Design](../01_architecture_designs/01_bridge_domain_topology_editor_design.md)
- [Reverse Engineering Design](../02_feature_designs/05_phase4_25_reverse_engineering_design.md)
- [Enhanced Topology Scanner Design](../02_feature_designs/04_phase4_scan_feature_design.md)
- [Backend API Documentation](../../api_server.py)
- [Database Models](../../models.py)

---

**Note**: This design plan emphasizes backend conformity as the highest priority. The editor must work seamlessly within the existing backend architecture while providing a simple, user-friendly interface for topology modifications. 