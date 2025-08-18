# Bridge Domain Editor Design Plan

## 🎯 **Core Concept**

A focused editor that allows users to modify existing bridge domain configurations by editing only the user-configurable parts (AC interfaces and devices), while leveraging your proven `BridgeDomainBuilder` logic and integrating seamlessly with your Smart Deployment system.

## 🏗️ **System Architecture & Data Flow**

### **1. Data Storage Strategy**

#### **Where to Store Edited Configs:**
```typescript
// Option A: Extend Existing Configuration Model (RECOMMENDED)
interface Configuration {
  id: number;
  service_name: string;
  vlan_id: number;
  status: 'pending' | 'deployed' | 'failed' | 'deleted' | 'edited';
  
  // Original configuration (for rollback)
  original_config_id?: number;
  
  // Current edited state
  current_config: BridgeDomainConfig;
  
  // Builder input for regeneration
  builder_input: {
    source_leaf: string;
    source_port: string;
    destinations: Array<{
      device: string;
      port: string;
    }>;
  };
  
  // Metadata
  config_source: 'manual' | 'reverse_engineered' | 'edited';
  derived_from_scan_id?: number;
  edited_at?: string;
  edited_by?: number;
}
```

#### **Database Schema Changes:**
```sql
-- Add to existing Configuration table
ALTER TABLE configurations ADD COLUMN original_config_id INTEGER REFERENCES configurations(id);
ALTER TABLE configurations ADD COLUMN edited_at TIMESTAMP;
ALTER TABLE configurations ADD COLUMN edited_by INTEGER REFERENCES users(id);

-- New table for edit history
CREATE TABLE configuration_edit_history (
    id INTEGER PRIMARY KEY,
    config_id INTEGER REFERENCES configurations(id),
    edit_type TEXT, -- 'interface_change', 'device_add', 'device_remove', 'vlan_change'
    old_value TEXT,
    new_value TEXT,
    edited_at TIMESTAMP,
    edited_by INTEGER REFERENCES users(id)
);
```

### **2. Integration with Smart Deployment System**

#### **Workflow Integration:**
```
Edit Config → Generate New Config → Smart Deploy → Deploy Changes
     ↓              ↓                ↓            ↓
User modifies   Use existing    Smart diff    Deploy only
AC interfaces   BridgeDomain    analysis      what changed
& devices      Builder logic    & planning    (incremental)
```

#### **Smart Deployment Integration Points:**
```typescript
// 1. Configuration Diff Engine Integration
interface ConfigurationDiff {
  // What changed in the bridge domain
  sourceDeviceChanges: {
    old: string;
    new: string;
  };
  sourceInterfaceChanges: {
    old: string;
    new: string;
  };
  destinationChanges: {
    added: Array<{device: string, port: string}>;
    removed: Array<{device: string, port: string}>;
    modified: Array<{
      device: string;
      oldPort: string;
      newPort: string;
    }>;
  };
  
  // Impact on network devices
  devicesToAdd: string[];
  devicesToModify: string[];
  devicesToRemove: string[];
  
  // Configuration commands that changed
  commandsToAdd: Record<string, string[]>;
  commandsToRemove: Record<string, string[]>;
  commandsToModify: Record<string, string[]>;
}
```

#### **Smart Deployment Preparation:**
```typescript
// 2. Deployment Plan Generation
const prepareForSmartDeployment = async (editedConfig: Configuration) => {
  // Step 1: Generate new configuration using existing BridgeDomainBuilder
  const newConfig = await bridgeDomainBuilder.build_bridge_domain_config(
    editedConfig.service_name,
    editedConfig.vlan_id,
    editedConfig.builder_input.source_leaf,
    editedConfig.builder_input.source_port,
    editedConfig.builder_input.destinations
  );
  
  // Step 2: Analyze differences for smart deployment
  const diff = await configurationDiffEngine.analyzeChanges(
    currentDeployedConfig,
    newConfig
  );
  
  // Step 3: Generate deployment plan
  const deploymentPlan = await smartDeploymentManager.generateDeploymentPlan(diff);
  
  // Step 4: Prepare rollback configuration
  const rollbackConfig = await rollbackManager.prepareRollback(
    currentDeployedConfig,
    editedConfig.id
  );
  
  return {
    newConfig,
    diff,
    deploymentPlan,
    rollbackConfig
  };
};
```

## 🎨 **Editor Interface Design**

### **Simple, Focused Interface:**
```typescript
// BridgeDomainEditor.tsx
interface BridgeDomainEditorProps {
  configId: number;
  onSave: (editedConfig: any) => void;
  onDeploy: (deploymentPlan: any) => void;
}

interface EditableBridgeDomain {
  service_name: string;
  vlan_id: number;
  
  // User-configurable parts
  source: {
    device: string;
    interface: string;
  };
  
  destinations: Array<{
    device: string;
    interface: string;
    status: 'active' | 'inactive';
  }>;
  
  // Auto-calculated parts (read-only)
  topology_type: 'p2p' | 'p2mp';
  path_calculation: any;
  bundle_mappings: any;
}
```

### **UI Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Bridge Domain Editor: g_visaev_v251                    [💾] [📤] │
├─────────────────────────────────────────────────────────────────┤
│                                                               │
│ Service Name: [g_visaev_v251]  VLAN ID: [251]                │
│                                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                        SOURCE                              │ │
│ │ Device: [DNAAS-LEAF-B14 ▼]                                │ │
│ │ Interface: [ge100-0/0/12 ▼]                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                     DESTINATIONS                           │ │
│ │                                                             │ │
│ │ [1] Device: [DNAAS-LEAF-B10 ▼]  Interface: [ge100-0/0/3 ▼] │
│ │     Status: [Active ▼]  [🗑️]                               │ │
│ │                                                             │ │
│ │ [2] Device: [DNAAS-LEAF-B12 ▼]  Interface: [ge100-0/0/5 ▼] │
│ │     Status: [Active ▼]  [🗑️]                               │ │
│ │                                                             │ │
│ │ [➕ Add Destination]                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                    AUTO-CALCULATED                         │ │
│ │ Topology Type: P2MP (read-only)                           │ │
│ │ Path: DNAAS-LEAF-B14 → DNAAS-SPINE-B09 → DNAAS-LEAF-B10   │ │
│ │ Bundle Mappings: bundle-60001, bundle-60002               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                               │
│ [💾 Save Changes] [📤 Prepare for Deployment] [🔄 Reset]     │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 **Configuration Generation & Validation**

### **Reusing BridgeDomainBuilder Logic:**
```typescript
// Integration with existing proven logic
const generateNewConfiguration = async (editedConfig: EditableBridgeDomain) => {
  try {
    // Step 1: Validate user inputs
    const validationErrors = validateUserInputs(editedConfig);
    if (validationErrors.length > 0) {
      throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
    }
    
    // Step 2: Call existing BridgeDomainBuilder.build_bridge_domain_config()
    const newConfig = await bridgeDomainBuilder.build_bridge_domain_config(
      editedConfig.service_name,
      editedConfig.vlan_id,
      editedConfig.source.device,
      editedConfig.source.interface,
      editedConfig.destinations[0].device, // For P2P
      editedConfig.destinations[0].interface
    );
    
    // Step 3: Handle P2MP scenarios
    if (editedConfig.destinations.length > 1) {
      // Use your existing P2MP logic
      const p2mpConfig = await bridgeDomainBuilder.build_p2mp_config(
        editedConfig.service_name,
        editedConfig.vlan_id,
        editedConfig.source.device,
        editedConfig.source.interface,
        editedConfig.destinations
      );
      return p2mpConfig;
    }
    
    return newConfig;
    
  } catch (error) {
    console.error('Configuration generation failed:', error);
    throw error;
  }
};
```

### **Validation Rules:**
```typescript
const validateUserInputs = (config: EditableBridgeDomain): string[] => {
  const errors: string[] = [];
  
  // Service name validation
  if (!config.service_name.match(/^[a-zA-Z0-9_-]+$/)) {
    errors.push('Service name must contain only letters, numbers, underscores, and hyphens');
  }
  
  // VLAN ID validation
  if (config.vlan_id < 1 || config.vlan_id > 4094) {
    errors.push('VLAN ID must be between 1 and 4094');
  }
  
  // Source validation
  if (!config.source.device || !config.source.interface) {
    errors.push('Source device and interface are required');
  }
  
  // Destinations validation
  if (config.destinations.length === 0) {
    errors.push('At least one destination is required');
  }
  
  // Interface format validation
  const interfacePattern = /^(ge100-0\/0\/\d+|bundle-\d+)$/;
  if (!interfacePattern.test(config.source.interface)) {
    errors.push('Source interface must be in format ge100-0/0/X or bundle-X');
  }
  
  config.destinations.forEach((dest, index) => {
    if (!dest.device || !dest.interface) {
      errors.push(`Destination ${index + 1} must have both device and interface`);
    }
    if (!interfacePattern.test(dest.interface)) {
      errors.push(`Destination ${index + 1} interface must be in format ge100-0/0/X or bundle-X`);
    }
  });
  
  return errors;
};
```

## 📤 **Smart Deployment Preparation**

### **Configuration Diff Analysis:**
```typescript
// What the Smart Deployment system needs to know
const prepareForSmartDeployment = async (editedConfig: Configuration) => {
  // 1. Get current deployed state
  const currentDeployedState = await getCurrentDeployedState(editedConfig.id);
  
  // 2. Generate new configuration
  const newConfiguration = await generateNewConfiguration(editedConfig);
  
  // 3. Analyze differences
  const diff = await analyzeConfigurationDifferences(
    currentDeployedState,
    newConfiguration
  );
  
  // 4. Generate deployment plan
  const deploymentPlan = await smartDeploymentManager.generateDeploymentPlan(diff);
  
  // 5. Prepare rollback
  const rollbackConfig = await rollbackManager.prepareRollback(
    currentDeployedState,
    editedConfig.id
  );
  
  return {
    newConfiguration,
    diff,
    deploymentPlan,
    rollbackConfig,
    readyForDeployment: true
  };
};
```

### **Deployment Plan Structure:**
```typescript
interface BridgeDomainDeploymentPlan {
  // What will be deployed
  newConfiguration: BridgeDomainConfig;
  
  // Smart deployment analysis
  diff: ConfigurationDiff;
  
  // Deployment strategy
  deploymentPlan: {
    executionGroups: ExecutionGroup[];
    estimatedDuration: number;
    riskLevel: 'low' | 'medium' | 'high';
  };
  
  // Safety measures
  rollbackConfig: RollbackConfig;
  validationSteps: ValidationStep[];
  
  // User approval
  requiresUserApproval: boolean;
  approvalReason?: string;
}
```

## 💾 **Data Persistence & State Management**

### **Edit History Tracking:**
```typescript
// Track all changes for audit purposes
interface EditHistoryEntry {
  id: number;
  config_id: number;
  edit_type: 'interface_change' | 'device_add' | 'device_remove' | 'vlan_change';
  field_name: string;
  old_value: string;
  new_value: string;
  edited_at: string;
  edited_by: number;
  reason?: string;
}

// Save edit history when user makes changes
const saveEditHistory = async (configId: number, changes: EditChange[]) => {
  for (const change of changes) {
    await db.execute(`
      INSERT INTO configuration_edit_history 
      (config_id, edit_type, field_name, old_value, new_value, edited_by, edited_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `, [configId, change.type, change.field, change.oldValue, change.newValue, userId, new Date().toISOString()]);
  }
};
```

### **Configuration State Management:**
```typescript
// State transitions
enum ConfigurationStatus {
  PENDING = 'pending',
  DEPLOYED = 'deployed',
  FAILED = 'failed',
  DELETED = 'deleted',
  EDITED = 'edited',           // New status
  READY_FOR_DEPLOYMENT = 'ready_for_deployment'  // New status
}

// State machine
const updateConfigurationStatus = async (configId: number, newStatus: ConfigurationStatus) => {
  await db.execute(`
    UPDATE configurations 
    SET status = ?, updated_at = ? 
    WHERE id = ?
  `, [newStatus, new Date().toISOString(), configId]);
  
  // Log status change
  await logStatusChange(configId, newStatus);
};
```

## 🔄 **User Experience Flow**

### **Complete User Journey:**
```
1. User opens existing configuration
   ↓
2. Editor loads current state (AC interfaces, devices, auto-calculated paths)
   ↓
3. User makes changes (modify interfaces, add/remove destinations)
   ↓
4. Editor validates changes in real-time
   ↓
5. User saves changes (creates new configuration record)
   ↓
6. System generates new configuration using existing BridgeDomainBuilder
   ↓
7. System analyzes differences for smart deployment
   ↓
8. User reviews deployment plan and rollback configuration
   ↓
9. User approves deployment
   ↓
10. Smart deployment system executes changes incrementally
    ↓
11. System validates deployment and updates configuration status
```

### **Error Handling & Recovery:**
```typescript
// Comprehensive error handling
const handleEditError = async (error: Error, context: string) => {
  // Log error
  await logError(error, context);
  
  // User-friendly error messages
  const userMessage = getUserFriendlyErrorMessage(error);
  
  // Recovery options
  const recoveryOptions = getRecoveryOptions(error);
  
  // Show error dialog with recovery options
  showErrorDialog({
    title: 'Edit Error',
    message: userMessage,
    recoveryOptions,
    onRetry: () => retryOperation(context),
    onReset: () => resetToLastSaved(),
    onCancel: () => closeEditor()
  });
};
```

## 🎯 **Key Benefits of This Design**

### **1. Leverages Existing Proven Logic**
- ✅ Reuses your working `BridgeDomainBuilder.build_bridge_domain_config()`
- ✅ Integrates with existing smart deployment system
- ✅ Maintains data consistency with current models

### **2. Clean Separation of Concerns**
- ✅ **Editor**: Only handles user-configurable parts
- ✅ **Builder**: Generates configurations using proven logic
- ✅ **Smart Deployment**: Handles deployment orchestration
- ✅ **Database**: Tracks edit history and configuration states

### **3. Smart Deployment Integration**
- ✅ **Incremental Changes**: Only deploys what actually changed
- ✅ **Rollback Ready**: Pre-generated rollback configurations
- ✅ **Validation**: Multi-level validation throughout the process
- ✅ **User Control**: Clear visibility and approval process

### **4. User Experience**
- ✅ **Simple Interface**: Focus on what users actually need to edit
- ✅ **Real-time Validation**: Immediate feedback on changes
- ✅ **Clear Workflow**: Edit → Save → Deploy → Validate
- ✅ **Safety**: Rollback and validation at every step

## 🚀 **Implementation Priority**

### **Phase 1: Core Editor (Week 1-2)**
- Basic editor interface
- Configuration loading and editing
- Integration with BridgeDomainBuilder

### **Phase 2: Smart Deployment Integration (Week 3-4)**
- Configuration diff analysis
- Deployment plan generation
- Rollback preparation

### **Phase 3: Advanced Features (Week 5-6)**
- Edit history tracking
- Advanced validation
- Error handling and recovery

### **Phase 4: Testing & Refinement (Week 7-8)**
- End-to-end testing
- User experience optimization
- Performance tuning

## 💡 **What Else to Consider?**

### **1. Performance & Scalability**
- **Large Topologies**: Handle configurations with many destinations
- **Real-time Validation**: Efficient validation for complex configurations
- **Caching**: Cache topology data and bundle mappings

### **2. Security & Access Control**
- **User Permissions**: Who can edit which configurations
- **Change Approval**: Workflow for critical changes
- **Audit Trail**: Complete history of all changes

### **3. Integration Points**
- **Topology Scanner**: Refresh from latest scan data
- **Device Inventory**: Real-time device availability
- **Configuration Templates**: Reusable configuration patterns

### **4. Advanced Features**
- **Bulk Operations**: Edit multiple configurations at once
- **Configuration Comparison**: Side-by-side diff views
- **Automated Testing**: Validate configurations before deployment

## 🔗 **Integration with Smart Deployment System**

### **Leveraging Your Existing Smart Deployment Design:**

This Bridge Domain Editor integrates seamlessly with your existing Smart Incremental Deployment system by:

1. **Configuration Diff Engine**: Uses your existing `ConfigurationDiffEngine` to analyze changes
2. **Smart Deployment Manager**: Integrates with your `SmartDeploymentManager` for deployment orchestration
3. **Rollback Manager**: Leverages your `RollbackManager` for safety
4. **Validation Framework**: Uses your `ValidationFramework` for comprehensive validation

### **Data Flow Integration:**
```
Bridge Domain Editor → Configuration Diff → Smart Deployment → Device Deployment
       ↓                       ↓                    ↓              ↓
   User edits config    Analyze changes    Generate plan    Execute changes
   (AC interfaces &     (what changed)     (how to deploy)   (incremental)
    devices only)       (impact analysis)  (rollback prep)   (validation)
```

### **Key Integration Points:**

1. **`/api/configurations/<id>/smart-deploy/analyze`** - Analyze configuration changes
2. **`/api/configurations/<id>/smart-deploy/plan`** - Generate deployment plan
3. **`/api/configurations/<id>/smart-deploy/execute`** - Execute deployment
4. **`/api/configurations/<id>/smart-deploy/rollback`** - Execute rollback

## 📋 **Conclusion**

This Bridge Domain Editor design provides a clean, focused way to edit existing bridge domain configurations while:

- **Building on your proven logic** (BridgeDomainBuilder)
- **Integrating seamlessly** with your Smart Deployment system
- **Maintaining data integrity** with comprehensive validation
- **Providing user safety** with rollback and approval workflows
- **Supporting your workflow** from discovery to deployment

The editor focuses on what users actually need to edit (AC interfaces and devices) while letting your existing systems handle the complex parts (path calculation, bundle mapping, deployment orchestration).

This design gives you the missing "EDIT" piece in your workflow: **Discovery → Scan → Reverse Engineer → 🎯 EDIT → Deploy** 