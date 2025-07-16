# SSH Configuration Push System - Design Plan

## **1. Configuration Management**
- **Config Repository**: Create a `configs/` folder structure:
  ```
  configs/
  ├── bridge_domains/
  │   ├── g_visaev_v253.yaml
  │   ├── g_visaev_v254.yaml
  │   └── ...
  ├── pending/          # Configs ready to push
  ├── deployed/         # Successfully pushed configs
  └── failed/           # Failed push attempts
  ```

## **2. Pre-Push Validation System**
- **Device Availability Check**: Verify SSH connectivity before pushing
- **Interface Validation**: 
  - Check if interfaces exist on target devices
  - Verify interfaces are not already configured
  - Validate VLAN IDs don't conflict
- **Configuration Syntax Check**: Validate YAML structure
- **Dependency Validation**: Ensure all referenced devices/ports are available

## **3. Interactive User Interface**
```
=== SSH Configuration Push Menu ===
📁 Available Configurations:
1. g_visaev_v253.yaml (Bridge Domain - 2 devices)
2. g_visaev_v254.yaml (Bridge Domain - 2 devices)
3. g_visaev_v255.yaml (Bridge Domain - 2 devices)

Options:
- [P]ush selected config
- [V]alidate selected config
- [D]eploy all pending configs
- [S]how config details
- [R]efresh config list
- [B]ack to main menu

=== Deployed Configurations ===
📋 Currently Deployed:
1. g_visaev_v253.yaml (Deployed: 2024-01-15 14:30)
2. g_visaev_v254.yaml (Deployed: 2024-01-15 15:45)

Options:
- [R]emove selected deployed config
- [S]how deployment details
- [B]ack to main menu
```

## **4. Safety Features**
- **Dry Run Mode**: Show what would be pushed without actually pushing
- **Rollback Capability**: Store previous configs for quick rollback
- **Confirmation Prompts**: "Are you sure you want to push to 2 devices?"
- **Progress Tracking**: Real-time status updates during push
- **Error Recovery**: Continue with remaining devices if one fails

## **5. Advanced Features**
- **Batch Operations**: Push multiple configs at once
- **Audit Trail**: Log all push operations with timestamps
- **Configuration Templates**: Reusable templates for common scenarios
- **Parallel Execution**: Push to multiple devices simultaneously

## **6. Remove/Decommission System**
- **Deployed Config Tracking**: Maintain list of currently deployed configurations
- **Safe Removal Process**:
  - Validate config is actually deployed before removal
  - Check for dependencies (other services using same VLAN/interfaces)
  - Generate removal commands (opposite of deployment commands)
  - Confirm removal with user
- **Removal Validation**:
  - Verify interfaces are still accessible
  - Check if VLAN is in use by other services
  - Validate removal commands before execution
- **Post-Removal Cleanup**:
  - Move config from `deployed/` to `removed/` folder
  - Update deployment tracking
  - Log removal operation with timestamp
- **Emergency Rollback**: Quick restore of removed configurations

## **7. Validation Mechanisms**
```python
class ConfigValidator:
    def validate_device_connectivity(self, devices)
    def validate_interface_availability(self, device, interface)
    def validate_vlan_conflicts(self, vlan_id, devices)
    def validate_config_syntax(self, config_yaml)
    def check_dependencies(self, config)

class RemovalValidator:
    def validate_deployment_exists(self, config_name)
    def check_vlan_dependencies(self, vlan_id, devices)
    def validate_removal_commands(self, removal_config)
    def check_interface_status(self, device, interface)
```

## **8. User Experience Flow**
1. **Select Config**: Browse available configurations with preview
2. **Pre-Validation**: Automatic checks before pushing
3. **Review & Confirm**: Show summary of what will be pushed
4. **Execute**: Push with progress indicators
5. **Post-Push**: Show results and any warnings

**For Removal:**
1. **Select Deployed Config**: Browse currently deployed configurations
2. **Dependency Check**: Verify no conflicts with removal
3. **Review Removal Plan**: Show what will be removed
4. **Confirm Removal**: Final confirmation with warnings
5. **Execute Removal**: Remove with progress indicators
6. **Post-Removal**: Show results and cleanup status

## **9. Error Handling**
- **Graceful Failures**: Continue with other devices if one fails
- **Detailed Error Messages**: Clear explanations of what went wrong
- **Recovery Suggestions**: "Try reconnecting to device X"
- **Partial Success Handling**: Show what succeeded vs failed

## **Implementation Priority**
1. **Configuration file management** (organizing saved configs)
2. **Basic validation framework** (device connectivity, interface checks)
3. **Interactive menu system** (similar to existing main menu)
4. **SSH connection management** (reusing existing device connectivity)
5. **Deployment tracking system** (track what's deployed)
6. **Removal system** (safe decommissioning)

## **Integration Points**
- Integrate with existing `main.py` menu system
- Reuse device connectivity from existing scripts
- Leverage topology data for validation
- Connect with bridge domain builder output 