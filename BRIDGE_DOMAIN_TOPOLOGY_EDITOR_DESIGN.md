# Bridge Domain Topology Editor Design

## **Overview**

The Bridge Domain Topology Editor is an advanced feature that combines bridge domain building and discovery capabilities to enable dynamic editing of existing bridge domains. Users can visually modify topology, move Access Circuits (AC) between nodes, and deploy changes safely.

**Key Innovation: Multi-User Workspace System**
- **Global View**: Complete network topology with all 444 bridge domains
- **Personal Workspace**: Engineers load only their allocated VLAN-range bridge domains
- **Access Control**: VLAN-range-based permissions for secure editing
- **Isolated Editing**: Safe personal workspace for topology modifications

## **Core Concept**

### **Workflow: Discover → Filter → Load → Edit → Deploy**
1. **Discovery**: Scan network for all bridge domains (444 total)
2. **Filter**: Load only bridge domains within user's VLAN range
3. **Load**: Load filtered bridge domains into personal workspace
4. **Edit**: Modify topology using drag-and-drop interface
5. **Validate**: Check for conflicts and topology issues
6. **Deploy**: Safely deploy changes to network devices

## **User Management & Access Control**

### **1. VLAN Range Allocation System**

```python
class UserVlanAllocation:
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        self.vlan_ranges = []  # List of VlanRange objects
        self.permissions = UserPermissions()
        self.created_at = datetime.now()
        self.last_access = datetime.now()

class VlanRange:
    def __init__(self, start_vlan: int, end_vlan: int, description: str = ""):
        self.start_vlan = start_vlan
        self.end_vlan = end_vlan
        self.description = description
        self.is_active = True
        self.created_at = datetime.now()

class UserPermissions:
    def __init__(self):
        self.can_edit_topology = True
        self.can_deploy_changes = True
        self.can_view_global = False  # Can see all bridge domains
        self.can_edit_others = False  # Can edit other users' bridge domains
        self.max_bridge_domains = 50  # Maximum bridge domains per user
        self.require_approval = False  # Require approval for deployments
```

### **2. Personal Workspace Management**

```python
class PersonalWorkspace:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.loaded_bridge_domains = {}  # service_name -> BridgeDomain
        self.workspace_settings = WorkspaceSettings()
        self.edit_history = []  # List of EditHistoryEntry
        self.last_saved = datetime.now()
    
    def load_user_bridge_domains(self, vlan_ranges: List[VlanRange]) -> List[BridgeDomain]:
        """
        Load bridge domains that fall within user's VLAN ranges
        
        Args:
            vlan_ranges: User's allocated VLAN ranges
            
        Returns:
            List of BridgeDomain objects within user's scope
        """
        # 1. Discover all bridge domains in network
        all_bridge_domains = self.topology_parser.discover_all_bridge_domains()
        
        # 2. Filter by VLAN ranges
        user_bridge_domains = []
        for bridge_domain in all_bridge_domains:
            if self.is_vlan_in_ranges(bridge_domain.vlan_id, vlan_ranges):
                user_bridge_domains.append(bridge_domain)
        
        # 3. Load into personal workspace
        for bridge_domain in user_bridge_domains:
            self.loaded_bridge_domains[bridge_domain.service_name] = bridge_domain
        
        return user_bridge_domains
    
    def is_vlan_in_ranges(self, vlan_id: int, vlan_ranges: List[VlanRange]) -> bool:
        """Check if VLAN ID falls within any of the user's allocated ranges"""
        for vlan_range in vlan_ranges:
            if vlan_range.is_active and vlan_range.start_vlan <= vlan_id <= vlan_range.end_vlan:
                return True
        return False
    
    def save_workspace_state(self):
        """Save current workspace state to database"""
        workspace_data = {
            'user_id': self.user_id,
            'loaded_bridge_domains': list(self.loaded_bridge_domains.keys()),
            'workspace_settings': self.workspace_settings.to_dict(),
            'last_saved': datetime.now()
        }
        self.db_manager.save_workspace_state(workspace_data)
    
    def restore_workspace_state(self):
        """Restore workspace state from database"""
        workspace_data = self.db_manager.get_workspace_state(self.user_id)
        if workspace_data:
            # Restore loaded bridge domains
            for service_name in workspace_data['loaded_bridge_domains']:
                bridge_domain = self.topology_parser.parse_existing_bridge_domain(service_name)
                self.loaded_bridge_domains[service_name] = bridge_domain
            
            # Restore workspace settings
            self.workspace_settings.from_dict(workspace_data['workspace_settings'])
```

### **3. Global vs Personal Views**

```python
class TopologyViewManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_view = ViewType.PERSONAL  # PERSONAL or GLOBAL
        self.personal_workspace = PersonalWorkspace(user_id)
        self.global_view_cache = {}  # Cache for global view data
    
    def switch_to_personal_view(self) -> List[BridgeDomain]:
        """
        Switch to personal workspace view
        
        Returns:
            List of bridge domains in user's VLAN ranges
        """
        self.current_view = ViewType.PERSONAL
        user_vlan_ranges = self.get_user_vlan_ranges(self.user_id)
        return self.personal_workspace.load_user_bridge_domains(user_vlan_ranges)
    
    def switch_to_global_view(self) -> List[BridgeDomain]:
        """
        Switch to global view (read-only for most users)
        
        Returns:
            List of all bridge domains in network
        """
        self.current_view = ViewType.GLOBAL
        
        # Check if user has global view permissions
        user_permissions = self.get_user_permissions(self.user_id)
        if not user_permissions.can_view_global:
            raise PermissionError("User does not have global view permissions")
        
        # Load all bridge domains (cached for performance)
        if not self.global_view_cache:
            self.global_view_cache = self.topology_parser.discover_all_bridge_domains()
        
        return self.global_view_cache
    
    def get_available_bridge_domains(self) -> Dict[str, List[BridgeDomain]]:
        """
        Get bridge domains available to user
        
        Returns:
            Dictionary with 'personal' and 'global' bridge domain lists
        """
        user_vlan_ranges = self.get_user_vlan_ranges(self.user_id)
        personal_domains = self.personal_workspace.load_user_bridge_domains(user_vlan_ranges)
        
        # Get global domains if user has permission
        global_domains = []
        user_permissions = self.get_user_permissions(self.user_id)
        if user_permissions.can_view_global:
            global_domains = self.topology_parser.discover_all_bridge_domains()
        
        return {
            'personal': personal_domains,
            'global': global_domains
        }
```

## **Architecture Design**

### **1. Node-Based Topology System**

```python
class TopologyNode:
    def __init__(self, device_name: str, device_type: DeviceType):
        self.device_name = device_name
        self.device_type = device_type  # LEAF, SPINE, SUPERSPINE
        self.interfaces = []  # List of Interface objects
        self.connections = []  # List of Connection objects
        self.bridge_domains = []  # List of BridgeDomain objects
        self.position_x = 0.0  # Visual position
        self.position_y = 0.0  # Visual position
        self.owner_user_id = None  # User who owns this node (if applicable)

class Interface:
    def __init__(self, name: str, interface_type: InterfaceType):
        self.name = name
        self.interface_type = interface_type  # USER_PORT, SPINE_PORT, BUNDLE
        self.bridge_domains = []  # Which bridge domains use this interface
        self.connected_to = None  # Which interface this connects to
        self.vlan_id = None  # VLAN ID if configured
        self.owner_user_id = None  # User who owns this interface (if applicable)

class BridgeDomain:
    def __init__(self, service_name: str, vlan_id: int):
        self.service_name = service_name
        self.vlan_id = vlan_id
        self.nodes = []  # List of TopologyNode objects
        self.paths = []  # List of Path objects
        self.status = BridgeDomainStatus.PENDING
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.owner_user_id = None  # User who owns this bridge domain
        self.vlan_range = None  # VlanRange this belongs to

class TopologyConnection:
    def __init__(self, from_node: str, to_node: str, 
                 from_interface: str, to_interface: str):
        self.from_node = from_node
        self.to_node = to_node
        self.from_interface = from_interface
        self.to_interface = to_interface
        self.connection_type = ConnectionType.SPINE_TO_LEAF
        self.bridge_domains = []  # Which bridge domains use this connection
        self.owner_user_id = None  # User who owns this connection (if applicable)
```

### **2. Topology Discovery & Parsing**

```python
class TopologyParser:
    def parse_existing_bridge_domain(self, service_name: str) -> BridgeDomain:
        """
        Parse existing bridge domain from network devices
        
        Args:
            service_name: Service name to discover
            
        Returns:
            BridgeDomain object with complete topology
        """
        # 1. Discover all devices in the network
        devices = self.device_scanner.scan_all_devices()
        
        # 2. Parse bridge domain configurations on each device
        bridge_domain_configs = {}
        for device in devices:
            configs = self.parse_device_bridge_domains(device)
            bridge_domain_configs[device] = configs
        
        # 3. Find all configurations for the target service
        service_configs = self.extract_service_configs(bridge_domain_configs, service_name)
        
        # 4. Build topology graph
        topology = self.build_topology_graph(service_configs)
        
        # 5. Validate topology consistency
        self.validate_topology_consistency(topology)
        
        return topology
    
    def discover_all_bridge_domains(self) -> List[BridgeDomain]:
        """
        Discover all bridge domains in the network
        
        Returns:
            List of BridgeDomain objects
        """
        # Scan all devices
        # Parse all bridge domain configurations
        # Group by service name
        # Build complete topology map
        pass
    
    def discover_bridge_domains_by_vlan_ranges(self, vlan_ranges: List[VlanRange]) -> List[BridgeDomain]:
        """
        Discover bridge domains within specific VLAN ranges
        
        Args:
            vlan_ranges: List of VLAN ranges to search within
            
        Returns:
            List of BridgeDomain objects within specified ranges
        """
        all_bridge_domains = self.discover_all_bridge_domains()
        filtered_domains = []
        
        for bridge_domain in all_bridge_domains:
            if self.is_vlan_in_ranges(bridge_domain.vlan_id, vlan_ranges):
                filtered_domains.append(bridge_domain)
        
        return filtered_domains
```

### **3. Visual Topology Editor**

```python
class TopologyEditor:
    def __init__(self, bridge_domain: BridgeDomain, user_id: str):
        self.bridge_domain = bridge_domain
        self.nodes = bridge_domain.nodes
        self.connections = bridge_domain.connections
        self.validation_engine = TopologyValidator()
        self.user_id = user_id
        self.user_permissions = self.get_user_permissions(user_id)
    
    def move_ac(self, from_node: str, from_interface: str, 
                to_node: str, to_interface: str) -> TopologyEditResult:
        """
        Move Access Circuit from one node to another
        
        Args:
            from_node: Source device name
            from_interface: Source interface name
            to_node: Destination device name
            to_interface: Destination interface name
            
        Returns:
            TopologyEditResult with success/failure and validation results
        """
        # 1. Check user permissions
        if not self.user_permissions.can_edit_topology:
            return TopologyEditResult(
                success=False,
                error_message="User does not have edit permissions"
            )
        
        # 2. Validate move is possible
        validation = self.validation_engine.validate_ac_move(
            from_node, from_interface, to_node, to_interface
        )
        
        if not validation.is_valid:
            return TopologyEditResult(
                success=False,
                validation_results=validation,
                error_message=validation.error_message
            )
        
        # 3. Update topology
        self.update_topology_ac_move(from_node, from_interface, to_node, to_interface)
        
        # 4. Regenerate configurations
        new_configs = self.config_generator.generate_from_topology(self.bridge_domain)
        
        # 5. Validate new topology
        final_validation = self.validation_engine.validate_topology(self.bridge_domain)
        
        return TopologyEditResult(
            success=True,
            validation_results=final_validation,
            new_configurations=new_configs
        )
    
    def add_node(self, device_name: str, device_type: DeviceType) -> TopologyEditResult:
        """Add new node to topology"""
        pass
    
    def remove_node(self, device_name: str) -> TopologyEditResult:
        """Remove node from topology"""
        pass
    
    def modify_connection(self, from_node: str, to_node: str, 
                         new_from_interface: str, new_to_interface: str) -> TopologyEditResult:
        """Modify connection between nodes"""
        pass
```

## **Frontend Design**

### **React Components Structure:**

```typescript
// Main Topology Editor Component with User Management
interface TopologyEditorProps {
  user: User;
  bridgeDomain: BridgeDomain;
  viewType: ViewType;  // 'personal' or 'global'
  onTopologyChange: (topology: BridgeDomain) => void;
  onValidationChange: (validation: ValidationResult) => void;
  onViewChange: (viewType: ViewType) => void;
}

const TopologyEditor: React.FC<TopologyEditorProps> = ({ 
  user, 
  bridgeDomain, 
  viewType,
  onTopologyChange, 
  onValidationChange,
  onViewChange
}) => {
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResult | null>(null);
  const [availableBridgeDomains, setAvailableBridgeDomains] = useState<BridgeDomain[]>([]);
  
  return (
    <div className="topology-editor">
      <UserWorkspaceHeader 
        user={user}
        viewType={viewType}
        onViewChange={onViewChange}
        availableBridgeDomains={availableBridgeDomains}
        onBridgeDomainSelect={handleBridgeDomainSelect}
      />
      
      <TopologyToolbar 
        onSave={handleSave}
        onDeploy={handleDeploy}
        onUndo={handleUndo}
        onRedo={handleRedo}
        userPermissions={user.permissions}
        viewType={viewType}
      />
      
      <div className="topology-workspace">
        <TopologyCanvas 
          nodes={bridgeDomain.nodes}
          connections={bridgeDomain.connections}
          selectedNode={selectedNode}
          onNodeSelect={setSelectedNode}
          onNodeMove={handleNodeMove}
          onConnectionChange={handleConnectionChange}
          onAcMove={handleAcMove}
          userPermissions={user.permissions}
          viewType={viewType}
        />
        
        <TopologyPanel 
          selectedNode={selectedNode}
          onNodeEdit={handleNodeEdit}
          onInterfaceEdit={handleInterfaceEdit}
          onNodeDelete={handleNodeDelete}
          userPermissions={user.permissions}
        />
      </div>
      
      <ValidationPanel 
        validationResults={validationResults}
        onFixIssues={handleFixIssues}
        onIgnoreIssues={handleIgnoreIssues}
      />
      
      <DeploymentPanel 
        bridgeDomain={bridgeDomain}
        onDeploy={handleDeploy}
        onPreview={handlePreview}
        userPermissions={user.permissions}
        viewType={viewType}
      />
    </div>
  );
};

// User Workspace Header Component
const UserWorkspaceHeader: React.FC<UserWorkspaceHeaderProps> = ({
  user,
  viewType,
  onViewChange,
  availableBridgeDomains,
  onBridgeDomainSelect
}) => {
  return (
    <div className="user-workspace-header">
      <div className="user-info">
        <span className="username">{user.username}</span>
        <span className="vlan-ranges">
          VLAN Ranges: {user.vlanRanges.map(range => 
            `${range.startVlan}-${range.endVlan}`
          ).join(', ')}
        </span>
      </div>
      
      <div className="view-controls">
        <button 
          className={`view-btn ${viewType === 'personal' ? 'active' : ''}`}
          onClick={() => onViewChange('personal')}
        >
          Personal Workspace ({user.personalBridgeDomains.length})
        </button>
        
        {user.permissions.canViewGlobal && (
          <button 
            className={`view-btn ${viewType === 'global' ? 'active' : ''}`}
            onClick={() => onViewChange('global')}
          >
            Global View ({availableBridgeDomains.length})
          </button>
        )}
      </div>
      
      <div className="bridge-domain-selector">
        <select onChange={(e) => onBridgeDomainSelect(e.target.value)}>
          <option value="">Select Bridge Domain...</option>
          {availableBridgeDomains.map(bd => (
            <option key={bd.serviceName} value={bd.serviceName}>
              {bd.serviceName} (VLAN {bd.vlanId})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
```

### **Visual Elements:**

#### **1. Node Representation:**
- **Leaf nodes**: Green circles with device name
- **Spine nodes**: Blue squares with device name
- **Superspine nodes**: Purple diamonds with device name
- **Interface indicators**: Small colored dots on node perimeter
- **Status indicators**: Border color (green=healthy, red=error, yellow=warning)
- **Ownership indicators**: Border style (solid=owned, dashed=shared, dotted=read-only)

#### **2. Connection Lines:**
- **Solid lines**: Active connections
- **Dashed lines**: Potential connections
- **Color-coded**: By VLAN/Service
- **Thickness**: Based on bandwidth/importance
- **Arrows**: Show traffic direction
- **Ownership**: Line style indicates ownership

#### **3. Interface Indicators:**
- **User ports**: Blue dots
- **Spine ports**: Green dots
- **Bundle ports**: Orange dots
- **Hover tooltips**: Show interface details
- **Click to edit**: Open interface editor
- **Permission indicators**: Color coding for edit permissions

## **API Design**

### **New API Endpoints:**

```python
# User Management & Authentication
GET /api/user/profile
GET /api/user/vlan-ranges
PUT /api/user/vlan-ranges
GET /api/user/permissions

# Workspace Management
GET /api/workspace/personal
POST /api/workspace/personal/save
GET /api/workspace/personal/restore
DELETE /api/workspace/personal/clear

# Bridge Domain Discovery (Filtered by User)
GET /api/topology/discover/personal
GET /api/topology/discover/global
GET /api/topology/discover/{service_name}/check-access

# Topology Discovery
GET /api/topology/discover/{service_name}
GET /api/topology/discover-all
GET /api/topology/available-services

# Topology Loading
GET /api/topology/{service_name}/load
POST /api/topology/{service_name}/save
DELETE /api/topology/{service_name}

# Topology Editing
POST /api/topology/{service_name}/move-ac
POST /api/topology/{service_name}/add-node
DELETE /api/topology/{service_name}/remove-node
POST /api/topology/{service_name}/modify-connection
POST /api/topology/{service_name}/add-connection
DELETE /api/topology/{service_name}/remove-connection

# Topology Validation
POST /api/topology/{service_name}/validate
GET /api/topology/{service_name}/conflicts
POST /api/topology/{service_name}/fix-conflicts

# Topology Deployment
POST /api/topology/{service_name}/deploy-changes
GET /api/topology/{service_name}/deployment-status
POST /api/topology/{service_name}/rollback
GET /api/topology/{service_name}/deployment-history

# Topology Visualization
GET /api/topology/{service_name}/visualization
GET /api/topology/{service_name}/export-svg
GET /api/topology/{service_name}/export-png
```

### **Request/Response Examples:**

```python
# Get User Profile
GET /api/user/profile
Response:
{
    "user_id": "user123",
    "username": "john_engineer",
    "vlan_ranges": [
        {"start_vlan": 100, "end_vlan": 199, "description": "Primary range"},
        {"start_vlan": 300, "end_vlan": 399, "description": "Secondary range"}
    ],
    "permissions": {
        "can_edit_topology": true,
        "can_deploy_changes": true,
        "can_view_global": false,
        "can_edit_others": false,
        "max_bridge_domains": 50,
        "require_approval": false
    }
}

# Get Personal Bridge Domains
GET /api/topology/discover/personal
Response:
{
    "bridge_domains": [
        {
            "service_name": "g_visaev_v255",
            "vlan_id": 255,
            "owner_user_id": "user123",
            "status": "active",
            "nodes_count": 3,
            "last_modified": "2024-01-15T10:30:00Z"
        },
        {
            "service_name": "g_visaev_v256", 
            "vlan_id": 256,
            "owner_user_id": "user123",
            "status": "active",
            "nodes_count": 2,
            "last_modified": "2024-01-14T15:45:00Z"
        }
    ],
    "total_count": 2,
    "vlan_ranges_used": [255, 256]
}

# Move AC Request (with permission check)
POST /api/topology/g_visaev_v255/move-ac
{
    "from_node": "DNAAS-LEAF-B13",
    "from_interface": "ge100-0/0/34",
    "to_node": "DNAAS-LEAF-B14", 
    "to_interface": "ge100-0/0/35"
}

# Move AC Response
{
    "success": true,
    "validation_results": {
        "is_valid": true,
        "warnings": [],
        "errors": []
    },
    "new_configurations": {
        "DNAAS-LEAF-B13": [...],
        "DNAAS-LEAF-B14": [...],
        "DNAAS-SPINE-B09": [...]
    },
    "topology_changes": {
        "moved_ac": "ge100-0/0/34",
        "affected_nodes": ["DNAAS-LEAF-B13", "DNAAS-LEAF-B14"]
    },
    "permission_check": {
        "can_edit": true,
        "owner_user_id": "user123",
        "vlan_range": "255-255"
    }
}
```

## **Database Schema Extensions**

```sql
-- User management table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- User VLAN allocations table
CREATE TABLE user_vlan_allocations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_vlan INTEGER NOT NULL,
    end_vlan INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User permissions table
CREATE TABLE user_permissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    can_edit_topology BOOLEAN DEFAULT TRUE,
    can_deploy_changes BOOLEAN DEFAULT TRUE,
    can_view_global BOOLEAN DEFAULT FALSE,
    can_edit_others BOOLEAN DEFAULT FALSE,
    max_bridge_domains INTEGER DEFAULT 50,
    require_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Personal workspace table
CREATE TABLE personal_workspaces (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    workspace_data JSON NOT NULL,  -- Serialized workspace state
    last_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Topology nodes table (with ownership)
CREATE TABLE topology_nodes (
    id INTEGER PRIMARY KEY,
    bridge_domain_id INTEGER,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    position_x REAL DEFAULT 0.0,
    position_y REAL DEFAULT 0.0,
    owner_user_id INTEGER,  -- User who owns this node
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bridge_domain_id) REFERENCES configurations(id),
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);

-- Topology connections table (with ownership)
CREATE TABLE topology_connections (
    id INTEGER PRIMARY KEY,
    bridge_domain_id INTEGER,
    from_node_id INTEGER,
    to_node_id INTEGER,
    from_interface TEXT NOT NULL,
    to_interface TEXT NOT NULL,
    connection_type TEXT NOT NULL,
    vlan_id INTEGER,
    owner_user_id INTEGER,  -- User who owns this connection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bridge_domain_id) REFERENCES configurations(id),
    FOREIGN KEY (from_node_id) REFERENCES topology_nodes(id),
    FOREIGN KEY (to_node_id) REFERENCES topology_nodes(id),
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);

-- Topology edit history table (with user tracking)
CREATE TABLE topology_edit_history (
    id INTEGER PRIMARY KEY,
    bridge_domain_id INTEGER,
    user_id INTEGER NOT NULL,  -- User who made the edit
    edit_type TEXT NOT NULL,  -- 'move_ac', 'add_node', 'remove_node', etc.
    edit_data JSON NOT NULL,  -- Detailed edit information
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bridge_domain_id) REFERENCES configurations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Topology validation results table
CREATE TABLE topology_validation_results (
    id INTEGER PRIMARY KEY,
    bridge_domain_id INTEGER,
    user_id INTEGER NOT NULL,  -- User who requested validation
    validation_type TEXT NOT NULL,  -- 'topology', 'conflicts', 'deployment'
    validation_data JSON NOT NULL,  -- Detailed validation results
    is_valid BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bridge_domain_id) REFERENCES configurations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## **Implementation Phases**

### **Phase 1: User Management & Access Control (Foundation)**
**Timeline: 2-3 weeks**

1. **User Management System**
   - User authentication and authorization
   - VLAN range allocation system
   - Permission management
   - User profile management

2. **Personal Workspace System**
   - Personal workspace creation and management
   - Bridge domain filtering by VLAN ranges
   - Workspace state persistence
   - User-specific settings

3. **Access Control Layer**
   - Permission checking for all operations
   - VLAN range validation
   - User isolation mechanisms
   - Audit logging

### **Phase 2: Discovery & Parsing (Enhanced)**
**Timeline: 2-3 weeks**

1. **Enhanced Device Scanner**
   - Parse existing bridge domain configurations
   - Extract topology information with ownership
   - Build device relationship map
   - Filter by user VLAN ranges

2. **Topology Parser (User-Aware)**
   - Convert configurations to node-based topology
   - Handle different topology types (P2P, P2MP, Mixed)
   - Validate topology consistency
   - Assign ownership to topology elements

3. **Conflict Detector (User-Aware)**
   - Identify topology issues within user scope
   - Detect configuration conflicts
   - Validate path requirements
   - Check cross-user conflicts

### **Phase 3: Visual Editor (Multi-User)**
**Timeline: 3-4 weeks**

1. **React Topology Canvas (User-Aware)**
   - Drag-and-drop interface with permission checks
   - Node visualization with ownership indicators
   - Connection management with user isolation
   - Personal vs global view switching

2. **Node Management (User-Aware)**
   - Add/remove/edit nodes with permission checks
   - Interface management within user scope
   - Position tracking per user
   - Ownership visualization

3. **Connection Management (User-Aware)**
   - Modify connections between nodes
   - Connection validation within user scope
   - Path optimization
   - Cross-user conflict detection

### **Phase 4: Validation & Deployment (User-Aware)**
**Timeline: 2-3 weeks**

1. **Real-time Validation (User-Aware)**
   - Check topology changes within user scope
   - Conflict detection with other users
   - Dependency validation
   - Cross-user impact analysis

2. **Configuration Generator (User-Aware)**
   - Generate new configs from topology
   - Incremental configuration updates
   - Rollback support per user
   - User-specific deployment strategies

3. **Deployment Manager (User-Aware)**
   - Safe deployment of topology changes
   - Progress tracking per user
   - Error handling with user context
   - Approval workflows if required

## **Key Challenges & Solutions**

### **1. User Isolation & Security**
**Challenge:** Ensuring users can only access and modify their allocated bridge domains
**Solution:**
- VLAN range-based access control
- Permission checking at every operation
- User-specific workspace isolation
- Audit logging for all user actions

### **2. Cross-User Conflict Detection**
**Challenge:** Detecting when one user's changes might affect another user's bridge domains
**Solution:**
- Shared resource conflict detection
- Cross-user dependency mapping
- Real-time conflict notification
- Collaborative conflict resolution

### **3. Performance with Multiple Users**
**Challenge:** Handling multiple users accessing the system simultaneously
**Solution:**
- User-specific caching strategies
- Incremental updates per user
- Efficient filtering by VLAN ranges
- Optimized database queries

### **4. Workspace State Management**
**Challenge:** Maintaining consistent workspace state across user sessions
**Solution:**
- Persistent workspace state storage
- Automatic workspace restoration
- Conflict resolution for concurrent edits
- Version control for workspace changes

### **5. Global vs Personal View Coordination**
**Challenge:** Coordinating between global network view and personal workspace
**Solution:**
- Separate view modes with clear indicators
- Permission-based view switching
- Cached global view for performance
- Real-time synchronization when needed

## **User Workflow**

### **1. User Authentication & Workspace Setup**
```
User logs in with credentials
↓
System loads user profile and VLAN ranges
↓
System creates/restores personal workspace
↓
System loads bridge domains within user's VLAN ranges
↓
User sees personal workspace with filtered bridge domains
```

### **2. Discovery Phase (Personal)**
```
User clicks "Discover My Bridge Domains"
↓
System scans network devices
↓
Filters bridge domains by user's VLAN ranges
↓
Parses bridge domain configurations
↓
Builds topology graph for user's domains only
↓
Displays list of user's bridge domains
```

### **3. Global View Access (If Permitted)**
```
User clicks "Global View" (if has permission)
↓
System loads all bridge domains in network
↓
Displays read-only global topology
↓
User can view but not edit others' domains
↓
User can switch back to personal workspace
```

### **4. Loading Phase (Personal)**
```
User selects bridge domain from personal list
↓
System loads topology into personal editor
↓
Displays visual topology with ownership indicators
↓
Shows current configuration details
↓
Enables editing based on user permissions
```

### **5. Editing Phase (Personal)**
```
User makes topology changes within scope
↓
Real-time validation within user's VLAN ranges
↓
Conflict detection with other users
↓
Configuration regeneration
↓
Preview of changes
```

### **6. Validation Phase (User-Aware)**
```
System validates all changes within user scope
↓
Checks for conflicts with other users
↓
Analyzes impact on shared resources
↓
Provides fix suggestions
↓
User resolves issues
```

### **7. Deployment Phase (User-Aware)**
```
User approves changes
↓
System generates deployment plan for user's domains
↓
Shows deployment preview
↓
User confirms deployment
↓
System deploys changes with user context
↓
Monitors deployment progress
```

## **Success Metrics**

### **Technical Metrics:**
- **User Isolation**: % of successful access control enforcement
- **Discovery Accuracy**: % of correctly parsed bridge domains per user
- **Validation Speed**: Time to validate topology changes per user
- **Deployment Success Rate**: % of successful deployments per user
- **Performance**: Response time for topology operations per user

### **User Experience Metrics:**
- **Time to Edit**: Time from login to first edit per user
- **Error Rate**: % of validation errors per edit per user
- **User Satisfaction**: Feedback on personal workspace usability
- **Adoption Rate**: % of users actively using personal workspace
- **Cross-User Conflicts**: Frequency of conflicts between users

## **Future Enhancements**

### **Advanced Features:**
1. **Collaborative Editing**: Real-time collaboration between users
2. **User Groups**: Team-based VLAN range allocations
3. **Advanced Permissions**: Granular permission system
4. **User Analytics**: Usage analytics per user
5. **Workspace Templates**: Pre-configured workspace layouts

### **Integration Features:**
1. **LDAP Integration**: Enterprise user directory integration
2. **SSO Support**: Single sign-on authentication
3. **Role-Based Access**: Advanced role-based permissions
4. **Audit Trail**: Comprehensive audit logging
5. **User Notifications**: Real-time notifications for conflicts

---

*This enhanced design document now includes comprehensive user management and access control features, enabling secure multi-user operation of the Bridge Domain Topology Editor with personal workspaces and VLAN-range-based access control.* 