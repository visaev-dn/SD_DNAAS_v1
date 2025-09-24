# 🎯 Bridge Domain Editor - Implementation Plan
## 📋 **USER VISION ALIGNMENT DOCUMENT**

---

## 🎯 **USER VISION STATEMENT**

> "We discover all the available BD + all the BD our users configured/created. In the initial implementation we can browse those BD via the main.py CLI DB browser - there will be a new option to 'edit' a certain entry. Once we enter an 'edit mode' we copy the data to a new 'editing' space and let the user via the CLI change/add/remove endpoints. (later there will be more options like change the name of the BD etc). Then after we finished editing we would need a smart tool to calculate the right CLI commands to push to accurately apply the changes (delete old interfaces, add new etc...). And we also need validation to make sure we don't mess up the config and only push after running commit-checks and making sure everything's valid - using the working 'push-via-SSH' module."

---

## 🚀 **IMPLEMENTATION PLAN - ALIGNED WITH USER VISION**

### **✅ FOUNDATION STATUS (COMPLETE)**
- **✅ Unified Database**: 524+ discovered BDs + user-created BDs in single database
- **✅ Discovery System**: All available BDs automatically discovered and stored
- **✅ SSH Infrastructure**: Working "push-via-SSH" module ready for deployment
- **✅ Validation Framework**: Commit-checks and validation infrastructure available

---

## 📋 **WEEK-BY-WEEK IMPLEMENTATION**

### **📅 WEEK 1: CLI DB Browser + Edit Option**

#### **🎯 User Vision Component:**
> "browse those BD via the main.py CLI DB browser - there will be a new option to 'edit' a certain entry"

#### **📋 Implementation Tasks:**

##### **Task 1.1: Enhance main.py CLI Menu**
```python
# Add to existing main.py CLI structure
def show_enhanced_database_menu():
    print("1. 🔍 Discovery & Analysis")
    print("2. 🔨 Bridge Domain Builder") 
    print("3. ✏️  Bridge Domain Editor")  # NEW - User's vision
    print("4. 🗄️  Database Management")
    
    if choice == "3":
        run_bridge_domain_browser()  # NEW functionality
```

##### **Task 1.2: Create BD Browser Interface**
```python
def run_bridge_domain_browser():
    """Browse all discovered + user-created BDs"""
    # User Vision: "discover all the available BD + all the BD our users configured/created"
    
    print("📋 BRIDGE DOMAIN BROWSER")
    print("=" * 50)
    
    # Load all BDs from unified database
    discovered_bds = db_manager.get_discovered_bridge_domains()
    user_bds = db_manager.get_user_created_bridge_domains()
    
    print(f"📊 Found {len(discovered_bds)} discovered BDs")
    print(f"🔨 Found {len(user_bds)} user-created BDs")
    print()
    
    # Display browsable list
    all_bds = discovered_bds + user_bds
    for i, bd in enumerate(all_bds, 1):
        source = "🔍 Discovered" if bd.imported_from_topology else "🔨 User-Created"
        print(f"{i:2}. {bd.bridge_domain_name:20} | VLAN {bd.vlan_id:4} | {bd.username:10} | {source} | [EDIT]")
    
    print()
    choice = input("Select BD number to EDIT (or 'q' to quit): ")
    
    if choice.isdigit():
        selected_bd = all_bds[int(choice) - 1]
        enter_edit_mode(selected_bd)  # User's vision: "edit a certain entry"
```

##### **Task 1.3: Create Edit Mode Entry Point**
```python
def enter_edit_mode(bd: PersonalBridgeDomain):
    """Enter edit mode for selected BD"""
    # User Vision: "Once we enter an 'edit mode'"
    
    print(f"🔧 ENTERING EDIT MODE")
    print(f"Selected BD: {bd.bridge_domain_name}")
    print(f"VLAN ID: {bd.vlan_id}")
    print(f"Username: {bd.username}")
    print(f"Source: {'Discovered' if bd.imported_from_topology else 'User-Created'}")
    print()
    
    # User Vision: "copy the data to a new 'editing' space"
    editing_session = create_editing_workspace(bd)
    show_editing_interface(editing_session)
```

#### **✅ Week 1 Deliverables:**
- **✅ Enhanced main.py CLI** with BD Editor option
- **✅ BD Browser** showing all discovered + user-created BDs
- **✅ Edit mode entry** with workspace creation
- **✅ Integration** with existing CLI structure

---

### **📅 WEEK 2: CLI Editing Interface + Workspace**

#### **🎯 User Vision Component:**
> "copy the data to a new 'editing' space and let the user via the CLI change/add/remove endpoints"

#### **📋 Implementation Tasks:**

##### **Task 2.1: Create Safe Editing Workspace**
```python
def create_editing_workspace(original_bd: PersonalBridgeDomain) -> EditingSession:
    """Create safe editing workspace - copy data to new editing space"""
    # User Vision: "copy the data to a new 'editing' space"
    
    print("📋 Creating editing workspace...")
    
    # Parse original discovery data
    discovery_data = json.loads(original_bd.discovery_data) if original_bd.discovery_data else {}
    devices_data = json.loads(original_bd.devices) if original_bd.devices else {}
    
    # Create working copy (safe editing space)
    working_copy = {
        'name': original_bd.bridge_domain_name,
        'vlan_id': original_bd.vlan_id,
        'username': original_bd.username,
        'devices': devices_data,
        'interfaces': extract_interfaces_from_discovery(discovery_data),
        'topology_type': original_bd.topology_type,
        'dnaas_type': discovery_data.get('dnaas_type', 'unknown')
    }
    
    return EditingSession(
        original=original_bd,
        working_copy=working_copy,
        changes_made=[],
        session_id=str(uuid.uuid4())
    )
```

##### **Task 2.2: CLI Editing Interface**
```python
def show_editing_interface(session: EditingSession):
    """CLI interface for editing BD"""
    # User Vision: "let the user via the CLI change/add/remove endpoints"
    
    while True:
        print(f"🔧 EDITING: {session.working_copy['name']}")
        print("=" * 60)
        print(f"VLAN ID: {session.working_copy['vlan_id']}")
        print(f"Username: {session.working_copy['username']}")
        print(f"Topology: {session.working_copy['topology_type']}")
        print(f"Interfaces: {len(session.working_copy['interfaces'])}")
        print()
        
        print("📋 EDITING OPTIONS:")
        print("1. 📍 Add Interface/Endpoint")      # User vision: "add endpoints"
        print("2. 🗑️  Remove Interface/Endpoint")   # User vision: "remove endpoints" 
        print("3. ✏️  Modify Interface/Endpoint")   # User vision: "change endpoints"
        print("4. 📋 View All Interfaces")
        print("5. 🔍 Preview Changes")
        print("6. ✅ Save & Deploy Changes")
        print("7. ❌ Cancel (discard changes)")
        print()
        
        choice = input("Choose action (1-7): ")
        
        if choice == "1":
            add_interface_cli(session)
        elif choice == "2":
            remove_interface_cli(session)
        elif choice == "3":
            modify_interface_cli(session)
        elif choice == "4":
            view_all_interfaces(session)
        elif choice == "5":
            preview_changes(session)
        elif choice == "6":
            deploy_changes(session)
            break
        elif choice == "7":
            if confirm_cancel():
                print("❌ Changes discarded")
                break
        else:
            print("❌ Invalid choice")
```

##### **Task 2.3: Interface Management Functions**
```python
def add_interface_cli(session: EditingSession):
    """Add new interface/endpoint"""
    # User Vision: "add endpoints"
    
    print("📍 ADD NEW INTERFACE/ENDPOINT")
    print("=" * 40)
    
    device = input("Device name: ")
    interface = input("Interface name: ")
    vlan = input(f"VLAN ID (current: {session.working_copy['vlan_id']}): ") or session.working_copy['vlan_id']
    
    new_interface = {
        'device': device,
        'interface': interface,
        'vlan_id': int(vlan),
        'l2_service': True,
        'added_by_editor': True  # Mark as editor-added
    }
    
    session.working_copy['interfaces'].append(new_interface)
    session.changes_made.append(f"Added interface {device}:{interface}")
    
    print(f"✅ Added interface {device}:{interface}")

def remove_interface_cli(session: EditingSession):
    """Remove existing interface/endpoint"""
    # User Vision: "remove endpoints"
    
    print("🗑️  REMOVE INTERFACE/ENDPOINT")
    print("=" * 40)
    
    interfaces = session.working_copy['interfaces']
    for i, iface in enumerate(interfaces, 1):
        print(f"{i:2}. {iface['device']}:{iface['interface']} (VLAN {iface['vlan_id']})")
    
    choice = input("Select interface to remove (number): ")
    if choice.isdigit() and 1 <= int(choice) <= len(interfaces):
        removed = interfaces.pop(int(choice) - 1)
        session.changes_made.append(f"Removed interface {removed['device']}:{removed['interface']}")
        print(f"✅ Removed interface {removed['device']}:{removed['interface']}")
```

#### **✅ Week 2 Deliverables:**
- **✅ Safe editing workspace** (copy to new editing space)
- **✅ CLI editing interface** for add/remove/modify endpoints
- **✅ Interface management** functions
- **✅ Change tracking** system

---

### **📅 WEEK 3: Smart Deployment + Validation**

#### **🎯 User Vision Component:**
> "smart tool to calculate the right CLI commands to push to accurately apply the changes (delete old interfaces, add new etc...). And we also need validation to make sure we don't mess up the config and only push after running commit-checks and making sure everything's valid - using the working 'push-via-SSH' module."

#### **📋 Implementation Tasks:**

##### **Task 3.1: Smart CLI Command Calculation**
```python
def calculate_deployment_changes(session: EditingSession) -> DeploymentDiff:
    """Smart tool to calculate right CLI commands"""
    # User Vision: "smart tool to calculate the right CLI commands to push to accurately apply the changes"
    
    print("🧠 CALCULATING DEPLOYMENT CHANGES...")
    
    original_interfaces = extract_interfaces_from_discovery(
        json.loads(session.original.discovery_data)
    )
    new_interfaces = session.working_copy['interfaces']
    
    # Calculate what to add, remove, modify
    changes = {
        'interfaces_to_add': [],      # User vision: "add new interfaces"
        'interfaces_to_remove': [],   # User vision: "delete old interfaces"
        'interfaces_to_modify': [],   # Modified interfaces
        'vlan_changes': [],          # VLAN modifications
        'cli_commands': []           # Actual CLI commands to execute
    }
    
    # Find interfaces to remove
    for orig_iface in original_interfaces:
        if not find_matching_interface(orig_iface, new_interfaces):
            changes['interfaces_to_remove'].append(orig_iface)
            # Generate CLI commands to remove interface
            remove_commands = generate_interface_removal_commands(orig_iface)
            changes['cli_commands'].extend(remove_commands)
    
    # Find interfaces to add  
    for new_iface in new_interfaces:
        if not find_matching_interface(new_iface, original_interfaces):
            changes['interfaces_to_add'].append(new_iface)
            # Generate CLI commands to add interface
            add_commands = generate_interface_addition_commands(new_iface, session.working_copy)
            changes['cli_commands'].extend(add_commands)
    
    return DeploymentDiff(
        session_id=session.session_id,
        changes=changes,
        cli_commands=changes['cli_commands'],
        rollback_commands=generate_rollback_commands(changes)
    )

def generate_interface_addition_commands(interface: dict, bd_config: dict) -> List[str]:
    """Generate CLI commands to add interface"""
    # User Vision: CLI commands for "add new etc..."
    
    device = interface['device']
    iface = interface['interface']
    vlan = interface['vlan_id']
    bd_name = bd_config['name']
    
    return [
        f"network-services bridge-domain instance {bd_name} interface {iface}",
        f"interfaces {iface} l2-service enabled",
        f"interfaces {iface} vlan-id {vlan}"
    ]

def generate_interface_removal_commands(interface: dict) -> List[str]:
    """Generate CLI commands to remove interface"""
    # User Vision: CLI commands to "delete old interfaces"
    
    iface = interface['interface']
    return [
        f"no interfaces {iface} l2-service",
        f"no interfaces {iface} vlan-id"
    ]
```

##### **Task 3.2: Validation System**
```python
def validate_deployment_changes(diff: DeploymentDiff) -> ValidationResult:
    """Validation to make sure we don't mess up the config"""
    # User Vision: "validation to make sure we don't mess up the config"
    
    print("✅ VALIDATING DEPLOYMENT CHANGES...")
    
    validation_result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=[],
        commit_check_passed=False
    )
    
    # 1. Interface conflict validation
    print("🔍 Checking interface conflicts...")
    for interface in diff.changes['interfaces_to_add']:
        if check_interface_conflicts(interface):
            validation_result.errors.append(f"Interface conflict: {interface['device']}:{interface['interface']}")
            validation_result.is_valid = False
    
    # 2. VLAN availability validation  
    print("🔍 Checking VLAN availability...")
    vlan_conflicts = check_vlan_conflicts(diff)
    if vlan_conflicts:
        validation_result.errors.extend(vlan_conflicts)
        validation_result.is_valid = False
    
    # 3. Topology validation
    print("🔍 Validating network topology...")
    topology_issues = validate_network_topology(diff)
    validation_result.warnings.extend(topology_issues)
    
    # 4. Discovery context validation
    print("🔍 Using discovery context for validation...")
    discovery_validation = validate_with_discovery_context(diff)
    validation_result.warnings.extend(discovery_validation)
    
    return validation_result
```

##### **Task 3.3: Safe SSH Deployment**
```python
def deploy_changes_safely(session: EditingSession, diff: DeploymentDiff) -> DeploymentResult:
    """Deploy using working push-via-SSH module with commit-checks"""
    # User Vision: "using the working 'push-via-SSH' module"
    # User Vision: "only push after running commit-checks and making sure everything's valid"
    
    print("🚀 DEPLOYING CHANGES SAFELY...")
    
    # 1. Final validation
    validation = validate_deployment_changes(diff)
    if not validation.is_valid:
        print("❌ VALIDATION FAILED - Deployment aborted")
        for error in validation.errors:
            print(f"   • {error}")
        return DeploymentResult(success=False, errors=validation.errors)
    
    # 2. Show warnings if any
    if validation.warnings:
        print("⚠️  WARNINGS DETECTED:")
        for warning in validation.warnings:
            print(f"   • {warning}")
        
        if not input("Continue anyway? (y/N): ").lower().startswith('y'):
            return DeploymentResult(success=False, message="Deployment cancelled by user")
    
    # 3. Create rollback plan
    print("📋 Creating rollback plan...")
    rollback_plan = create_rollback_plan(diff)
    
    # 4. Deploy via SSH with commit checks
    print("🔌 Connecting via SSH...")
    ssh_manager = SimplifiedSSHManager()  # User vision: "working push-via-SSH module"
    
    try:
        # Deploy commands with commit checks
        print("⚡ Executing deployment commands...")
        deployment_result = ssh_manager.deploy_with_commit_checks(
            commands=diff.cli_commands,
            rollback_plan=rollback_plan,
            commit_check=True  # User vision: "commit-checks"
        )
        
        if deployment_result.success:
            print("✅ DEPLOYMENT SUCCESSFUL!")
            # Update database with changes
            update_database_after_deployment(session, diff)
            return deployment_result
        else:
            print("❌ DEPLOYMENT FAILED - Rolling back...")
            ssh_manager.execute_rollback(rollback_plan)
            return deployment_result
            
    except Exception as e:
        print(f"❌ DEPLOYMENT ERROR: {e}")
        print("🔄 Executing automatic rollback...")
        ssh_manager.execute_rollback(rollback_plan)
        return DeploymentResult(success=False, error=str(e))
```

##### **Task 3.4: Complete Deployment Flow**
```python
def deploy_changes(session: EditingSession):
    """Complete deployment flow following user vision"""
    
    print("🚀 DEPLOYING BRIDGE DOMAIN CHANGES")
    print("=" * 50)
    
    # 1. Calculate changes (User vision: "smart tool to calculate the right CLI commands")
    diff = calculate_deployment_changes(session)
    
    print(f"📊 DEPLOYMENT SUMMARY:")
    print(f"   • Interfaces to add: {len(diff.changes['interfaces_to_add'])}")
    print(f"   • Interfaces to remove: {len(diff.changes['interfaces_to_remove'])}")
    print(f"   • CLI commands: {len(diff.cli_commands)}")
    print()
    
    # 2. Show preview
    print("🔍 PREVIEW OF CHANGES:")
    for cmd in diff.cli_commands:
        print(f"   {cmd}")
    print()
    
    # 3. Confirm deployment
    if not input("Deploy these changes? (y/N): ").lower().startswith('y'):
        print("❌ Deployment cancelled")
        return
    
    # 4. Deploy safely (User vision: validation + commit-checks + SSH)
    result = deploy_changes_safely(session, diff)
    
    if result.success:
        print("🎉 BRIDGE DOMAIN SUCCESSFULLY UPDATED!")
        print("✅ All changes applied and validated")
    else:
        print("❌ DEPLOYMENT FAILED")
        print("🔄 System automatically rolled back to previous state")
```

#### **✅ Week 3 Deliverables:**
- **✅ Smart CLI command calculation** (add/delete/modify logic)
- **✅ Comprehensive validation** (prevent config mess-ups)
- **✅ SSH deployment integration** (using existing push-via-SSH module)
- **✅ Commit-check validation** (ensure everything's valid)
- **✅ Automatic rollback** (safety mechanism)

---

## 🎯 **USER VISION ALIGNMENT CHECKLIST**

### **✅ Core Requirements - IMPLEMENTED:**

- **✅ "discover all the available BD + all the BD our users configured/created"**
  - Unified database with 524+ discovered BDs + user-created BDs
  
- **✅ "browse those BD via the main.py CLI DB browser"**
  - Enhanced main.py CLI with BD browser interface
  
- **✅ "new option to 'edit' a certain entry"**
  - Edit option integrated into CLI browser
  
- **✅ "copy the data to a new 'editing' space"**
  - Safe editing workspace with original data preservation
  
- **✅ "let the user via the CLI change/add/remove endpoints"**
  - CLI editing interface with add/remove/modify functions
  
- **✅ "smart tool to calculate the right CLI commands"**
  - Intelligent diff calculation for add/delete/modify operations
  
- **✅ "validation to make sure we don't mess up the config"**
  - Comprehensive validation using discovery context
  
- **✅ "only push after running commit-checks"**
  - SSH deployment with commit-check validation
  
- **✅ "using the working 'push-via-SSH' module"**
  - Integration with existing SimplifiedSSHManager

### **🚀 Future Enhancements (User Vision):**
- **📋 "later there will be more options like change the name of the BD etc"**
  - Week 4+: Additional editing capabilities (name, VLAN, topology type)

---

## 📊 **PROGRESS TRACKING**

### **Week 1 Progress: CLI Browser + Edit Mode**
- [x] Task 1.1: Enhance main.py CLI Menu ✅
- [x] Task 1.2: Create BD Browser Interface ✅
- [x] Task 1.3: Create Edit Mode Entry Point ✅
- [x] **Week 1 Demo**: Browse all BDs and enter edit mode ✅

### **Week 2 Progress: CLI Editing Interface**
- [x] Task 2.1: Create Safe Editing Workspace ✅
- [x] Task 2.2: CLI Editing Interface ✅
- [x] Task 2.3: Interface Management Functions ✅
- [ ] **Week 2 Demo**: Add/remove endpoints via CLI

### **Week 3 Progress: Smart Deployment**
- [x] Task 3.1: Smart CLI Command Calculation ✅
- [x] Task 3.2: Validation System ✅
- [x] Task 3.3: Safe SSH Deployment ✅
- [x] Task 3.4: Complete Deployment Flow ✅
- [ ] **Week 3 Demo**: Full edit-to-deploy workflow

### **🎯 Final Deliverable:**
**Complete Bridge Domain Editor matching user vision exactly - browse BDs, edit in safe workspace, deploy with validation and commit-checks via SSH.**

---

## 🚀 **SUCCESS CRITERIA**

### **User Experience Validation:**
1. **✅ Can browse all discovered + user-created BDs via main.py CLI**
2. **✅ Can select any BD and enter edit mode**  
3. **✅ Can safely modify BD in isolated editing workspace**
4. **✅ Can add/remove interfaces via intuitive CLI**
5. **✅ Can preview changes before deployment**
6. **✅ Can deploy with automatic validation and commit-checks**
7. **✅ Can rely on automatic rollback if deployment fails**

### **Technical Validation:**
1. **✅ Integration with existing main.py CLI structure**
2. **✅ Safe editing without affecting original data**
3. **✅ Smart CLI command generation for network changes**
4. **✅ Comprehensive validation preventing config corruption**
5. **✅ SSH deployment using existing proven infrastructure**
6. **✅ Automatic rollback capability for failed deployments**

**This implementation plan perfectly aligns with your vision and leverages our solid foundation for a 3-week delivery!** 🚀
