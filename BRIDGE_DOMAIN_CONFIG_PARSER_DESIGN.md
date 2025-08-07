# Bridge Domain Configuration Parser Design

## **Overview**

The current bridge domain discovery system finds bridge domains and their basic topology, but it doesn't parse the **actual configuration commands** for each bridge domain. This enhanced parser will extract and parse the specific DNOS configuration commands that create each bridge domain, enabling the topology editor to understand and modify the actual configurations.

## **Current State vs. Enhanced State**

### **Current Discovery (What We Have):**
```yaml
# Current parsed data structure:
bridge_domain_instances:
  - name: "g_visaev_v255"
    admin_state: "enabled"
    interfaces: ["bundle-60000.255", "ge100-0/0/34"]
    # Missing: Actual configuration commands
```

### **Enhanced Discovery (What We Need):**
```yaml
# Enhanced parsed data structure:
bridge_domain_instances:
  - name: "g_visaev_v255"
    admin_state: "enabled"
    interfaces: ["bundle-60000.255", "ge100-0/0/34"]
    configuration_commands:
      - command: "bridge-domain g_visaev_v255"
        context: "config"
        parameters: {}
      - command: "admin-state enable"
        context: "config-bridge-domain"
        parameters: {}
      - command: "interface bundle-60000.255"
        context: "config-bridge-domain"
        parameters: {}
      - command: "interface ge100-0/0/34"
        context: "config-bridge-domain"
        parameters: {}
    # Plus: VLAN configuration, interface details, etc.
```

## **Enhanced Configuration Parser Architecture**

### **1. DNOS Configuration Command Parser**

```python
class DNOSConfigParser:
    """
    Parse DNOS configuration commands for bridge domains
    """
    
    def __init__(self):
        self.command_patterns = {
            'bridge_domain': r'bridge-domain\s+(\S+)',
            'admin_state': r'admin-state\s+(enable|disable)',
            'interface': r'interface\s+(\S+)',
            'vlan': r'vlan\s+(\d+)',
            'subinterface': r'(\S+)\.(\d+)',
            'bundle': r'bundle-(\d+)',
            'physical_interface': r'(ge|et)\d+-\d+/\d+/\d+'
        }
    
    def parse_bridge_domain_config(self, config_text: str) -> Dict:
        """
        Parse bridge domain configuration from DNOS config
        
        Args:
            config_text: Raw DNOS configuration text
            
        Returns:
            Parsed bridge domain configuration with commands
        """
        lines = config_text.split('\n')
        bridge_domains = []
        current_bridge_domain = None
        
        for line in lines:
            line = line.strip()
            
            # Start of bridge domain
            if 'bridge-domain' in line:
                if current_bridge_domain:
                    bridge_domains.append(current_bridge_domain)
                
                match = re.search(self.command_patterns['bridge_domain'], line)
                if match:
                    current_bridge_domain = {
                        'name': match.group(1),
                        'commands': [{'command': line, 'context': 'config'}],
                        'admin_state': 'unknown',
                        'interfaces': [],
                        'vlan_config': {},
                        'raw_config': [line]
                    }
            
            # Admin state
            elif current_bridge_domain and 'admin-state' in line:
                match = re.search(self.command_patterns['admin_state'], line)
                if match:
                    current_bridge_domain['admin_state'] = match.group(1)
                    current_bridge_domain['commands'].append({
                        'command': line,
                        'context': 'config-bridge-domain'
                    })
                    current_bridge_domain['raw_config'].append(line)
            
            # Interface configuration
            elif current_bridge_domain and 'interface' in line:
                match = re.search(self.command_patterns['interface'], line)
                if match:
                    interface_name = match.group(1)
                    current_bridge_domain['interfaces'].append(interface_name)
                    current_bridge_domain['commands'].append({
                        'command': line,
                        'context': 'config-bridge-domain',
                        'interface': interface_name
                    })
                    current_bridge_domain['raw_config'].append(line)
        
        # Add the last bridge domain
        if current_bridge_domain:
            bridge_domains.append(current_bridge_domain)
        
        return {
            'bridge_domains': bridge_domains,
            'parsed_at': datetime.now().isoformat()
        }
    
    def parse_vlan_config(self, config_text: str) -> Dict:
        """
        Parse VLAN configuration commands
        
        Args:
            config_text: Raw DNOS VLAN configuration text
            
        Returns:
            Parsed VLAN configuration
        """
        lines = config_text.split('\n')
        vlan_configs = []
        
        for line in lines:
            line = line.strip()
            
            # VLAN interface configuration
            if 'vlan' in line and 'interface' in line:
                match = re.search(r'interface\s+(\S+)\s+vlan\s+(\d+)', line)
                if match:
                    vlan_configs.append({
                        'interface': match.group(1),
                        'vlan_id': int(match.group(2)),
                        'command': line,
                        'type': 'vlan_assignment'
                    })
            
            # Subinterface VLAN
            elif '.' in line and 'vlan' in line:
                match = re.search(r'(\S+)\.(\d+)\s+vlan\s+(\d+)', line)
                if match:
                    vlan_configs.append({
                        'interface': f"{match.group(1)}.{match.group(2)}",
                        'vlan_id': int(match.group(3)),
                        'command': line,
                        'type': 'subinterface_vlan'
                    })
        
        return {
            'vlan_configurations': vlan_configs,
            'parsed_at': datetime.now().isoformat()
        }
```

### **2. Enhanced Bridge Domain Discovery**

```python
class EnhancedBridgeDomainDiscovery(BridgeDomainDiscovery):
    """
    Enhanced bridge domain discovery with configuration parsing
    """
    
    def __init__(self):
        super().__init__()
        self.config_parser = DNOSConfigParser()
        self.raw_config_dir = Path('topology/configs/raw-config/bridge_domain_raw')
    
    def load_raw_configurations(self) -> Dict[str, Dict]:
        """
        Load raw DNOS configurations for all devices
        
        Returns:
            Dict mapping device names to their raw configurations
        """
        raw_configs = {}
        
        # Load bridge domain instance configurations
        instance_files = list(self.raw_config_dir.glob('*_bridge_domain_instance_raw_*.txt'))
        for file_path in instance_files:
            try:
                device_name = self.extract_device_name_from_filename(file_path.name)
                with open(file_path, 'r') as f:
                    config_text = f.read()
                    raw_configs[device_name] = {
                        'bridge_domain_config': config_text,
                        'parsed': False
                    }
            except Exception as e:
                logger.error(f"Error loading raw config {file_path}: {e}")
        
        # Load VLAN configurations
        vlan_files = list(self.raw_config_dir.glob('*_vlan_config_raw_*.txt'))
        for file_path in vlan_files:
            try:
                device_name = self.extract_device_name_from_filename(file_path.name)
                with open(file_path, 'r') as f:
                    config_text = f.read()
                    if device_name not in raw_configs:
                        raw_configs[device_name] = {}
                    raw_configs[device_name]['vlan_config'] = config_text
            except Exception as e:
                logger.error(f"Error loading VLAN config {file_path}: {e}")
        
        return raw_configs
    
    def parse_device_configurations(self, raw_configs: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Parse raw configurations for all devices
        
        Args:
            raw_configs: Raw configuration data for all devices
            
        Returns:
            Parsed configuration data with commands
        """
        parsed_configs = {}
        
        for device_name, device_configs in raw_configs.items():
            parsed_device = {
                'device': device_name,
                'bridge_domain_instances': [],
                'vlan_configurations': [],
                'parsed_at': datetime.now().isoformat()
            }
            
            # Parse bridge domain configurations
            if 'bridge_domain_config' in device_configs:
                bridge_domain_parsed = self.config_parser.parse_bridge_domain_config(
                    device_configs['bridge_domain_config']
                )
                parsed_device['bridge_domain_instances'] = bridge_domain_parsed['bridge_domains']
            
            # Parse VLAN configurations
            if 'vlan_config' in device_configs:
                vlan_parsed = self.config_parser.parse_vlan_config(
                    device_configs['vlan_config']
                )
                parsed_device['vlan_configurations'] = vlan_parsed['vlan_configurations']
            
            parsed_configs[device_name] = parsed_device
        
        return parsed_configs
    
    def create_enhanced_mapping(self, parsed_configs: Dict[str, Dict]) -> Dict:
        """
        Create enhanced bridge domain mapping with configuration commands
        
        Args:
            parsed_configs: Parsed configuration data with commands
            
        Returns:
            Enhanced mapping with configuration details
        """
        enhanced_mapping = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'devices_scanned': len(parsed_configs),
                'enhanced_parsing': True,
                'configuration_commands_included': True
            },
            'bridge_domains': {},
            'device_configurations': parsed_configs,
            'configuration_summary': {
                'total_commands_parsed': 0,
                'total_bridge_domains': 0,
                'total_vlan_configs': 0
            }
        }
        
        # Process each device's configurations
        for device_name, device_config in parsed_configs.items():
            device_type = self.detect_device_type(device_name)
            
            # Process bridge domain instances
            for bridge_domain in device_config.get('bridge_domain_instances', []):
                service_name = bridge_domain['name']
                
                # Analyze service name pattern
                service_analysis = self.service_analyzer.extract_service_info(service_name)
                
                # Create enhanced bridge domain entry
                enhanced_bridge_domain = {
                    'service_name': service_name,
                    'detected_username': service_analysis.get('username'),
                    'detected_vlan': service_analysis.get('vlan_id'),
                    'confidence': service_analysis.get('confidence', 0),
                    'detection_method': service_analysis.get('method', 'unknown'),
                    'admin_state': bridge_domain['admin_state'],
                    'interfaces': bridge_domain['interfaces'],
                    'configuration_commands': bridge_domain['commands'],
                    'raw_configuration': bridge_domain['raw_config'],
                    'device_type': device_type,
                    'device_name': device_name,
                    'parsed_at': bridge_domain.get('parsed_at', datetime.now().isoformat())
                }
                
                # Add to mapping
                if service_name not in enhanced_mapping['bridge_domains']:
                    enhanced_mapping['bridge_domains'][service_name] = {
                        'service_name': service_name,
                        'detected_username': service_analysis.get('username'),
                        'detected_vlan': service_analysis.get('vlan_id'),
                        'confidence': service_analysis.get('confidence', 0),
                        'detection_method': service_analysis.get('method', 'unknown'),
                        'devices': {},
                        'total_commands': 0,
                        'configuration_commands': []
                    }
                
                # Add device-specific configuration
                enhanced_mapping['bridge_domains'][service_name]['devices'][device_name] = {
                    'device_type': device_type,
                    'admin_state': bridge_domain['admin_state'],
                    'interfaces': bridge_domain['interfaces'],
                    'configuration_commands': bridge_domain['commands'],
                    'raw_configuration': bridge_domain['raw_config']
                }
                
                # Aggregate commands
                enhanced_mapping['bridge_domains'][service_name]['configuration_commands'].extend(
                    bridge_domain['commands']
                )
                enhanced_mapping['bridge_domains'][service_name]['total_commands'] += len(
                    bridge_domain['commands']
                )
                
                # Update summary
                enhanced_mapping['configuration_summary']['total_commands_parsed'] += len(
                    bridge_domain['commands']
                )
                enhanced_mapping['configuration_summary']['total_bridge_domains'] += 1
        
        return enhanced_mapping
    
    def run_enhanced_discovery(self) -> Dict:
        """
        Run enhanced bridge domain discovery with configuration parsing
        
        Returns:
            Enhanced bridge domain mapping with configuration commands
        """
        logger.info("Starting Enhanced Bridge Domain Discovery...")
        
        # Load raw configurations
        logger.info("Loading raw DNOS configurations...")
        raw_configs = self.load_raw_configurations()
        logger.info(f"Loaded raw configs from {len(raw_configs)} devices")
        
        # Parse configurations
        logger.info("Parsing DNOS configurations...")
        parsed_configs = self.parse_device_configurations(raw_configs)
        
        # Create enhanced mapping
        logger.info("Creating enhanced mapping with configuration commands...")
        enhanced_mapping = self.create_enhanced_mapping(parsed_configs)
        
        # Save enhanced mapping
        logger.info("Saving enhanced bridge domain mapping...")
        self.save_enhanced_mapping(enhanced_mapping)
        
        logger.info("Enhanced Bridge Domain Discovery complete!")
        return enhanced_mapping
```

### **3. Configuration Command Generator**

```python
class BridgeDomainConfigGenerator:
    """
    Generate DNOS configuration commands for bridge domains
    """
    
    def __init__(self):
        self.command_templates = {
            'create_bridge_domain': 'bridge-domain {service_name}',
            'enable_bridge_domain': 'admin-state enable',
            'disable_bridge_domain': 'admin-state disable',
            'add_interface': 'interface {interface_name}',
            'remove_interface': 'no interface {interface_name}',
            'set_vlan': 'vlan {vlan_id}',
            'create_subinterface': 'interface {interface_name}.{vlan_id}'
        }
    
    def generate_bridge_domain_config(self, bridge_domain: Dict) -> List[str]:
        """
        Generate DNOS configuration commands for a bridge domain
        
        Args:
            bridge_domain: Bridge domain data with configuration
            
        Returns:
            List of DNOS configuration commands
        """
        commands = []
        service_name = bridge_domain['service_name']
        
        # Create bridge domain
        commands.append(self.command_templates['create_bridge_domain'].format(
            service_name=service_name
        ))
        
        # Set admin state
        admin_state = bridge_domain.get('admin_state', 'enable')
        if admin_state == 'enable':
            commands.append(self.command_templates['enable_bridge_domain'])
        else:
            commands.append(self.command_templates['disable_bridge_domain'])
        
        # Add interfaces
        for interface in bridge_domain.get('interfaces', []):
            commands.append(self.command_templates['add_interface'].format(
                interface_name=interface
            ))
        
        return commands
    
    def generate_diff_commands(self, original_config: Dict, new_config: Dict) -> List[str]:
        """
        Generate configuration commands to transform one bridge domain to another
        
        Args:
            original_config: Original bridge domain configuration
            new_config: New bridge domain configuration
            
        Returns:
            List of DNOS commands to apply changes
        """
        commands = []
        
        # Handle interface changes
        original_interfaces = set(original_config.get('interfaces', []))
        new_interfaces = set(new_config.get('interfaces', []))
        
        # Remove interfaces that are no longer needed
        for interface in original_interfaces - new_interfaces:
            commands.append(self.command_templates['remove_interface'].format(
                interface_name=interface
            ))
        
        # Add new interfaces
        for interface in new_interfaces - original_interfaces:
            commands.append(self.command_templates['add_interface'].format(
                interface_name=interface
            ))
        
        # Handle admin state changes
        if original_config.get('admin_state') != new_config.get('admin_state'):
            if new_config.get('admin_state') == 'enable':
                commands.append(self.command_templates['enable_bridge_domain'])
            else:
                commands.append(self.command_templates['disable_bridge_domain'])
        
        return commands
```

## **Enhanced Data Structure**

### **Bridge Domain Configuration Structure:**

```yaml
# Enhanced bridge domain mapping structure:
bridge_domains:
  g_visaev_v255:
    service_name: "g_visaev_v255"
    detected_username: "visaev"
    detected_vlan: 255
    confidence: 95
    detection_method: "automated_pattern"
    devices:
      DNAAS-LEAF-B13:
        device_type: "leaf"
        admin_state: "enabled"
        interfaces: ["bundle-60000.255", "ge100-0/0/34"]
        configuration_commands:
          - command: "bridge-domain g_visaev_v255"
            context: "config"
            parameters: {}
          - command: "admin-state enable"
            context: "config-bridge-domain"
            parameters: {}
          - command: "interface bundle-60000.255"
            context: "config-bridge-domain"
            parameters: {"interface": "bundle-60000.255"}
          - command: "interface ge100-0/0/34"
            context: "config-bridge-domain"
            parameters: {"interface": "ge100-0/0/34"}
        raw_configuration:
          - "bridge-domain g_visaev_v255"
          - "admin-state enable"
          - "interface bundle-60000.255"
          - "interface ge100-0/0/34"
    total_commands: 4
    configuration_commands:
      - command: "bridge-domain g_visaev_v255"
        context: "config"
        parameters: {}
      - command: "admin-state enable"
        context: "config-bridge-domain"
        parameters: {}
      - command: "interface bundle-60000.255"
        context: "config-bridge-domain"
        parameters: {"interface": "bundle-60000.255"}
      - command: "interface ge100-0/0/34"
        context: "config-bridge-domain"
        parameters: {"interface": "ge100-0/0/34"}
```

## **Integration with Topology Editor**

### **1. Configuration-Aware Topology Editor**

```python
class ConfigurationAwareTopologyEditor(TopologyEditor):
    """
    Topology editor that understands and can modify actual configurations
    """
    
    def __init__(self, bridge_domain: BridgeDomain, user_id: str):
        super().__init__(bridge_domain, user_id)
        self.config_generator = BridgeDomainConfigGenerator()
        self.original_configurations = self.load_original_configurations()
    
    def move_ac_with_config(self, from_node: str, from_interface: str, 
                           to_node: str, to_interface: str) -> TopologyEditResult:
        """
        Move Access Circuit with configuration command generation
        """
        # 1. Validate move
        validation = self.validation_engine.validate_ac_move(
            from_node, from_interface, to_node, to_interface
        )
        
        if not validation.is_valid:
            return TopologyEditResult(
                success=False,
                validation_results=validation,
                error_message=validation.error_message
            )
        
        # 2. Generate configuration changes
        config_changes = self.generate_config_changes_for_ac_move(
            from_node, from_interface, to_node, to_interface
        )
        
        # 3. Update topology
        self.update_topology_ac_move(from_node, from_interface, to_node, to_interface)
        
        # 4. Generate new configurations
        new_configs = self.config_generator.generate_from_topology(self.bridge_domain)
        
        return TopologyEditResult(
            success=True,
            validation_results=validation,
            new_configurations=new_configs,
            configuration_changes=config_changes
        )
    
    def generate_config_changes_for_ac_move(self, from_node: str, from_interface: str,
                                          to_node: str, to_interface: str) -> Dict:
        """
        Generate configuration commands for AC move
        """
        changes = {
            'from_node': from_node,
            'to_node': to_node,
            'commands': {
                from_node: [],
                to_node: []
            }
        }
        
        # Remove interface from source node
        changes['commands'][from_node].append(
            f"no interface {from_interface}"
        )
        
        # Add interface to destination node
        changes['commands'][to_node].append(
            f"interface {to_interface}"
        )
        
        return changes
```

### **2. Configuration Preview in UI**

```typescript
// Configuration preview component
const ConfigurationPreview: React.FC<ConfigurationPreviewProps> = ({
  originalConfig,
  newConfig,
  changes
}) => {
  return (
    <div className="configuration-preview">
      <h3>Configuration Changes</h3>
      
      <div className="config-diff">
        <div className="removed-commands">
          <h4>Commands to Remove:</h4>
          {changes.removedCommands.map((cmd, index) => (
            <div key={index} className="command removed">
              {cmd}
            </div>
          ))}
        </div>
        
        <div className="added-commands">
          <h4>Commands to Add:</h4>
          {changes.addedCommands.map((cmd, index) => (
            <div key={index} className="command added">
              {cmd}
            </div>
          ))}
        </div>
      </div>
      
      <div className="device-specific-changes">
        {Object.entries(changes.deviceCommands).map(([device, commands]) => (
          <div key={device} className="device-changes">
            <h4>{device}:</h4>
            {commands.map((cmd, index) => (
              <div key={index} className="command">
                {cmd}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};
```

## **Implementation Plan**

### **Phase 1: Enhanced Configuration Parser (2-3 weeks)**
1. **DNOS Configuration Parser**
   - Parse bridge domain creation commands
   - Parse interface configuration commands
   - Parse VLAN assignment commands
   - Handle DNOS-specific syntax

2. **Raw Configuration Loading**
   - Load raw DNOS configuration files
   - Extract bridge domain sections
   - Parse command structure and parameters

3. **Enhanced Discovery Integration**
   - Integrate with existing discovery system
   - Add configuration commands to mapping
   - Maintain backward compatibility

### **Phase 2: Configuration Command Generator (1-2 weeks)**
1. **Command Templates**
   - Create DNOS command templates
   - Handle different command contexts
   - Support parameter substitution

2. **Diff Generation**
   - Generate configuration differences
   - Create minimal change commands
   - Validate command syntax

### **Phase 3: Topology Editor Integration (2-3 weeks)**
1. **Configuration-Aware Editor**
   - Integrate configuration parsing
   - Add configuration preview
   - Support configuration validation

2. **Deployment Integration**
   - Generate deployment commands
   - Preview configuration changes
   - Support rollback mechanisms

## **Benefits of Enhanced Configuration Parsing**

### **1. Accurate Topology Understanding**
- **Real configuration commands** instead of inferred topology
- **Exact interface mappings** with VLAN assignments
- **Command-level validation** for topology changes

### **2. Safe Configuration Changes**
- **Precise command generation** for topology modifications
- **Configuration diff preview** before deployment
- **Rollback capability** with original configurations

### **3. Enhanced Topology Editor**
- **Configuration-aware editing** with real command understanding
- **Live configuration preview** during topology changes
- **Validation against actual device configurations**

### **4. Deployment Safety**
- **Minimal configuration changes** for topology modifications
- **Device-specific command generation** for each change
- **Configuration validation** before deployment

This enhanced configuration parsing system will provide the foundation for a truly configuration-aware topology editor that can safely modify bridge domain configurations while maintaining the integrity of the network. 