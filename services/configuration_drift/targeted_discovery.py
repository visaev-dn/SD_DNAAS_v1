#!/usr/bin/env python3
"""
Targeted Configuration Discovery (Bridge Domain-First Approach)

Discovers specific bridge domain configurations on devices using the traditional
bridge domain discovery approach, adapted for targeted, efficient discovery.

Based on analysis in: traditional-vs-targeted-bridge-domain-discovery.md
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from .data_models import InterfaceConfig, DeviceConfigSnapshot, TargetedDiscoveryError

logger = logging.getLogger(__name__)


class TargetedConfigurationDiscovery:
    """Discovers specific configurations using bridge domain-first approach"""
    
    def __init__(self):
        # Use universal SSH framework for all device operations
        try:
            from services.universal_ssh import UniversalCommandExecutor, ExecutionMode
            self.command_executor = UniversalCommandExecutor()
            self.ExecutionMode = ExecutionMode  # Store for use in methods
            self.ssh_available = True
        except ImportError:
            self.command_executor = None
            self.ExecutionMode = None
            self.ssh_available = False
            logger.warning("Universal SSH framework not available for targeted discovery")
    
    def discover_bridge_domain_configuration(self, device_name: str, bd_name: str) -> Dict:
        """Discover complete bridge domain configuration on specific device (traditional approach)"""
        
        try:
            if not self.ssh_available:
                raise TargetedDiscoveryError("SSH framework not available")
            
            logger.info(f"Discovering bridge domain {bd_name} on {device_name} using traditional approach")
            
            # Step 1: Use ONLY proven DRIVENETS commands for bridge domain discovery
            # Based on console evidence, use config filtering approach
            bd_command = f"show config | fl | i \"bridge-domain instance {bd_name}\""
            bd_result = self.command_executor.execute_with_mode(
                device_name, [bd_command], self.ExecutionMode.QUERY
            )
            
            if bd_result.success and bd_result.output:
                # Parse bridge domain interfaces using traditional parsing
                bd_interfaces = self._parse_bridge_domain_interfaces(bd_result.output)
                
                print(f"   ✅ Bridge domain {bd_name} found on {device_name}")
                print(f"   📊 Associated interfaces: {len(bd_interfaces)}")
                for interface in bd_interfaces:
                    print(f"      • {interface}")
                
                # Step 2: Get interface VLAN configurations for discovered interfaces
                interface_configs = []
                for interface in bd_interfaces:
                    interface_pattern = interface.split('.')[0]  # Base interface
                    configs = self.discover_interface_configurations_for_bd(device_name, interface_pattern, interface)
                    interface_configs.extend(configs)
                
                return {
                    'bridge_domain_name': bd_name,
                    'device_name': device_name,
                    'interfaces': bd_interfaces,
                    'interface_configurations': interface_configs,
                    'success': True,
                    'discovery_method': 'bridge_domain_first'
                }
            else:
                # Bridge domain doesn't exist on this device
                logger.warning(f"Bridge domain {bd_name} not found on {device_name}")
                return {
                    'bridge_domain_name': bd_name,
                    'device_name': device_name,
                    'success': False,
                    'error_message': "Bridge domain not found on device",
                    'discovery_method': 'bridge_domain_first'
                }
                
        except Exception as e:
            logger.error(f"Bridge domain discovery failed for {bd_name} on {device_name}: {e}")
            return {
                'bridge_domain_name': bd_name,
                'device_name': device_name,
                'success': False,
                'error_message': str(e),
                'discovery_method': 'bridge_domain_first'
            }
    
    def discover_interface_configurations_for_bd(self, device_name: str, interface_pattern: str, 
                                               target_interface: str) -> List[InterfaceConfig]:
        """Discover interface configurations for specific interface in bridge domain context"""
        
        try:
            # Step 1: Get interface details with optimized filtering (your suggested approach)
            interface_command = f"show interfaces | no-more | i {interface_pattern}"
            interface_result = self.command_executor.execute_with_mode(
                device_name, [interface_command], self.ExecutionMode.QUERY
            )
            
            if interface_result.success:
                # Step 2: Get config using ONLY proven DRIVENETS command
                config_command = f"show config | fl | i {interface_pattern}"
                config_result = self.command_executor.execute_with_mode(
                    device_name, [config_command], self.ExecutionMode.QUERY
                )
                
                # Parse both outputs for complete picture
                return self._parse_interface_configurations_comprehensive(
                    interface_result.output, 
                    config_result.output if config_result.success else "", 
                    device_name, 
                    target_interface
                )
            else:
                logger.warning(f"Interface discovery failed for {interface_pattern} on {device_name}")
                return []
                
        except Exception as e:
            logger.error(f"Interface configuration discovery failed: {e}")
            return []
    
    def discover_interface_vlan_configurations(self, device_name: str, 
                                             interface_pattern: str = None) -> List[InterfaceConfig]:
        """Discover interface VLAN configurations (backward compatibility method)"""
        
        try:
            if not self.ssh_available:
                raise TargetedDiscoveryError("SSH framework not available")
            
            logger.info(f"Discovering interface configurations on {device_name} with pattern: {interface_pattern or 'all VLANs'}")
            
            if interface_pattern:
                # Use the enhanced discovery for specific interface
                return self.discover_interface_configurations_for_bd(device_name, interface_pattern, f"{interface_pattern}.251")
            else:
                # General VLAN discovery using ONLY proven DRIVENETS command
                vlan_command = "show config | fl | i vlan"
                result = self.command_executor.execute_with_mode(
                    device_name, [vlan_command], self.ExecutionMode.QUERY
                )
                
                if result.success:
                    return self._parse_vlan_config_output(result.output, device_name)
                else:
                    logger.error(f"VLAN discovery failed for {device_name}: {result.error_message}")
                    raise TargetedDiscoveryError(f"VLAN discovery failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Targeted interface discovery failed: {e}")
            raise TargetedDiscoveryError(f"Discovery failed: {e}")
    
    def _parse_bridge_domain_interfaces(self, bd_output: str) -> List[str]:
        """Parse bridge domain output to extract interface associations (traditional parsing)"""
        
        interfaces = []
        
        try:
            # Parse bridge domain instance output
            # Example: network-services bridge-domain instance g_visaev_v251 interface ge100-0/0/31.251
            lines = bd_output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Look for interface associations in bridge domain output
                interface_match = re.search(r'interface\s+(\S+)', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    interfaces.append(interface_name)
                    logger.debug(f"Found interface association: {interface_name}")
            
            logger.info(f"Parsed {len(interfaces)} interface associations from bridge domain output")
            return interfaces
            
        except Exception as e:
            logger.error(f"Error parsing bridge domain interfaces: {e}")
            return []
    
    def _parse_interface_configurations_comprehensive(self, interface_output: str, config_output: str, 
                                                    device_name: str, target_interface: str) -> List[InterfaceConfig]:
        """Parse interface configurations using both interface table and running config (comprehensive approach)"""
        
        interface_configs = []
        
        try:
            print(f"   🔍 Parsing interface output for {target_interface}")
            print(f"   📊 Interface output length: {len(interface_output)} chars")
            print(f"   📊 Config output length: {len(config_output)} chars")
            
            # Parse interface table output first (this is working from console)
            table_configs = self._parse_interface_table_output(interface_output, device_name)
            print(f"   📋 Table configs found: {len(table_configs)}")
            
            # Parse running config output for VLAN details (if available)
            config_configs = []
            if config_output and 'ERROR:' not in config_output:
                config_configs = self._parse_running_config_output(config_output, device_name)
                print(f"   📋 Config configs found: {len(config_configs)}")
            else:
                print(f"   ⚠️  Config output not available or has errors")
            
            # Focus on target interface and related interfaces
            for table_config in table_configs:
                # Check if this is our target interface or related
                if (table_config.interface_name == target_interface or 
                    table_config.interface_name.startswith(target_interface.split('.')[0])):
                    
                    print(f"   ✅ Found matching interface: {table_config.interface_name}")
                    print(f"      • VLAN: {table_config.vlan_id}")
                    print(f"      • Status: {table_config.admin_status}/{table_config.oper_status}")
                    
                    # Try to find matching config from running config
                    merged_config = table_config  # Start with table data
                    
                    for config_config in config_configs:
                        # Fix interface name matching - remove (L2) suffix for comparison
                        table_interface_clean = table_config.interface_name.replace(' (L2)', '')
                        config_interface_clean = config_config.interface_name
                        
                        if config_interface_clean == table_interface_clean:
                            # Merge table and config data WITH raw CLI commands
                            merged_config = InterfaceConfig(
                                device_name=device_name,
                                interface_name=table_config.interface_name,
                                vlan_id=config_config.vlan_id or table_config.vlan_id,
                                admin_status=table_config.admin_status,
                                oper_status=table_config.oper_status,
                                interface_type="subinterface" if '.' in table_config.interface_name else "physical",
                                l2_service_enabled=config_config.l2_service_enabled,
                                source="targeted_bd_discovery_merged",
                                raw_cli_config=config_config.raw_cli_config  # NEW: Include raw CLI commands
                            )
                            print(f"      • Merged with config data: L2 service {config_config.l2_service_enabled}")
                            print(f"      • Raw CLI commands: {len(config_config.raw_cli_config)} commands")
                            break
                    
                    interface_configs.append(merged_config)
            
            logger.info(f"Parsed {len(interface_configs)} comprehensive interface configurations")
            
            if not interface_configs:
                print(f"   ⚠️  No matching configurations found for {target_interface}")
                print(f"   🔍 Available table configs:")
                for config in table_configs[:3]:
                    print(f"      • {config.interface_name} (VLAN {config.vlan_id})")
            
            return interface_configs
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive interface configurations: {e}")
            return []
    
    def _parse_interface_table_output(self, interface_output: str, device_name: str) -> List[InterfaceConfig]:
        """Parse interface table output (DRIVENETS format)"""
        
        interface_configs = []
        
        try:
            lines = interface_output.split('\n')
            
            for line in lines:
                # Parse table format from "show interfaces | no-more | i pattern"
                if '|' in line and ('ge100-0/0/' in line or 'bundle-' in line):
                    # Clean ANSI color codes (fixed regex)
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                    clean_line = re.sub(r'\[91m|\[0m', '', clean_line)  # Remove specific color codes
                    
                    # Parse table columns
                    columns = [col.strip() for col in clean_line.split('|') if col.strip()]
                    
                    if len(columns) >= 6:
                        interface_name = columns[0].strip()
                        # Clean interface name of any remaining color codes
                        interface_name = re.sub(r'\x1b\[[0-9;]*m', '', interface_name)
                        interface_name = re.sub(r'\[91m|\[0m', '', interface_name)
                        
                        admin_status = columns[1].strip()
                        oper_status = columns[2].strip()
                        
                        # Debug: Print column parsing
                        print(f"   🔍 DEBUG - Parsing interface line: {len(columns)} columns")
                        for i, col in enumerate(columns):
                            print(f"      Column {i}: '{col}'")
                        
                        # Extract VLAN information from table (DRIVENETS format)
                        vlan_id = None
                        interface_type = "physical"
                        
                        # First, check for VLAN in interface name (most reliable)
                        if '.' in interface_name:
                            vlan_part = interface_name.split('.')[-1]
                            # Handle L2 subinterfaces
                            if '(L2)' in vlan_part:
                                vlan_part = vlan_part.replace('(L2)', '').strip()
                                interface_type = "subinterface"
                            
                            if vlan_part.isdigit():
                                vlan_id = int(vlan_part)
                                print(f"   ✅ VLAN from interface name: {vlan_id}")
                        
                        # Second, check for VLAN in dedicated column (column 5 based on console output)
                        if len(columns) > 5:
                            vlan_column = columns[5].strip()  # Column 5 should be VLAN column
                            if vlan_column and vlan_column.isdigit():
                                table_vlan = int(vlan_column)
                                if not vlan_id:  # Only use if not found in interface name
                                    vlan_id = table_vlan
                                print(f"   📊 VLAN from table column: {table_vlan}")
                        
                        # Third, check other columns for VLAN (fallback)
                        if not vlan_id:
                            for i, col in enumerate(columns[3:], 3):  # Start from column 3
                                if col.strip().isdigit() and 1 <= int(col.strip()) <= 4094:
                                    potential_vlan = int(col.strip())
                                    if potential_vlan != 1514 and potential_vlan != 1518:  # Skip MTU values
                                        vlan_id = potential_vlan
                                        print(f"   🔍 VLAN from column {i}: {vlan_id}")
                                        break
                        
                        interface_config = InterfaceConfig(
                            device_name=device_name,
                            interface_name=interface_name,
                            vlan_id=vlan_id,
                            admin_status=admin_status,
                            oper_status=oper_status,
                            interface_type=interface_type,
                            raw_output=line
                        )
                        interface_configs.append(interface_config)
            
            logger.debug(f"Parsed {len(interface_configs)} interface configurations from table output")
            return interface_configs
            
        except Exception as e:
            logger.error(f"Error parsing interface table output: {e}")
            return []
    
    def _parse_running_config_output(self, config_output: str, device_name: str) -> List[InterfaceConfig]:
        """Parse running config output for VLAN and L2 service details (DRIVENETS format)"""
        
        interface_configs = []
        
        try:
            print(f"   🔍 Parsing running config output...")
            lines = config_output.split('\n')
            
            interface_data = {}  # Store interface configurations
            raw_cli_commands = {}  # Store raw CLI commands for each interface
            
            for line in lines:
                line = line.strip()
                
                # Remove ANSI color codes (fixed regex)
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                clean_line = re.sub(r'\[91m|\[0m', '', clean_line)  # Remove specific color codes
                
                # Parse DRIVENETS config format: interfaces ge100-0/0/31.251 vlan-id 251
                vlan_match = re.search(r'interfaces\s+(\S+)\s+vlan-id\s+(\d+)', clean_line)
                if vlan_match:
                    interface_name = vlan_match.group(1)
                    vlan_id = int(vlan_match.group(2))
                    
                    if interface_name not in interface_data:
                        interface_data[interface_name] = {}
                        raw_cli_commands[interface_name] = []
                    
                    interface_data[interface_name]['vlan_id'] = vlan_id
                    raw_cli_commands[interface_name].append(clean_line)  # Store raw command
                    print(f"   ✅ Found VLAN config: {interface_name} -> VLAN {vlan_id}")
                
                # Parse L2 service configuration: interfaces ge100-0/0/31.251 l2-service enabled
                l2_match = re.search(r'interfaces\s+(\S+)\s+l2-service\s+(enabled|disabled)', clean_line)
                if l2_match:
                    interface_name = l2_match.group(1)
                    l2_enabled = l2_match.group(2) == 'enabled'
                    
                    if interface_name not in interface_data:
                        interface_data[interface_name] = {}
                        raw_cli_commands[interface_name] = []
                    
                    interface_data[interface_name]['l2_service_enabled'] = l2_enabled
                    raw_cli_commands[interface_name].append(clean_line)  # Store raw command
                    print(f"   ✅ Found L2 service config: {interface_name} -> {l2_enabled}")
                
                # Parse admin state: interfaces ge100-0/0/31.251 admin-state enabled
                admin_match = re.search(r'interfaces\s+(\S+)\s+admin-state\s+(enabled|disabled)', clean_line)
                if admin_match:
                    interface_name = admin_match.group(1)
                    admin_state = admin_match.group(2)
                    
                    if interface_name not in interface_data:
                        interface_data[interface_name] = {}
                        raw_cli_commands[interface_name] = []
                    
                    interface_data[interface_name]['admin_status'] = admin_state
                    raw_cli_commands[interface_name].append(clean_line)  # Store raw command
                    print(f"   ✅ Found admin state: {interface_name} -> {admin_state}")
            
            # Create InterfaceConfig objects from parsed data
            for interface_name, config_data in interface_data.items():
                interface_config = InterfaceConfig(
                    device_name=device_name,
                    interface_name=interface_name,
                    vlan_id=config_data.get('vlan_id'),
                    admin_status=config_data.get('admin_status', 'unknown'),
                    l2_service_enabled=config_data.get('l2_service_enabled', False),
                    interface_type="subinterface" if '.' in interface_name else "physical",
                    source="running_config_discovery",
                    raw_cli_config=raw_cli_commands.get(interface_name, [])  # NEW: Include raw CLI commands
                )
                interface_configs.append(interface_config)
                
                # Debug: Show collected raw CLI commands
                if raw_cli_commands.get(interface_name):
                    print(f"   📜 Raw CLI commands for {interface_name}:")
                    for cmd in raw_cli_commands[interface_name]:
                        print(f"      • {cmd}")
            
            print(f"   📊 Parsed {len(interface_configs)} interface configurations from running config")
            return interface_configs
            
        except Exception as e:
            logger.error(f"Error parsing running config output: {e}")
            return []
    
    def _parse_vlan_config_output(self, vlan_output: str, device_name: str) -> List[InterfaceConfig]:
        """Parse VLAN configuration output using traditional approach"""
        
        interface_configs = []
        
        try:
            # Parse traditional "show config | fl | i vlan" output
            # Example: interfaces ge100-0/0/31.251 vlan-id 251
            lines = vlan_output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Parse interface VLAN configuration
                vlan_match = re.search(r'interfaces\s+(\S+)\s+vlan-id\s+(\d+)', line)
                if vlan_match:
                    interface_name = vlan_match.group(1)
                    vlan_id = int(vlan_match.group(2))
                    
                    interface_config = InterfaceConfig(
                        device_name=device_name,
                        interface_name=interface_name,
                        vlan_id=vlan_id,
                        interface_type="subinterface" if '.' in interface_name else "physical",
                        source="vlan_config_discovery"
                    )
                    interface_configs.append(interface_config)
                
                # Parse L2 service configuration
                l2_match = re.search(r'interfaces\s+(\S+)\s+l2-service\s+(enabled|disabled)', line)
                if l2_match:
                    interface_name = l2_match.group(1)
                    l2_enabled = l2_match.group(2) == 'enabled'
                    
                    # Find existing config or create new one
                    existing_config = None
                    for config in interface_configs:
                        if config.interface_name == interface_name:
                            existing_config = config
                            break
                    
                    if existing_config:
                        existing_config.l2_service_enabled = l2_enabled
                    else:
                        interface_config = InterfaceConfig(
                            device_name=device_name,
                            interface_name=interface_name,
                            l2_service_enabled=l2_enabled,
                            interface_type="subinterface" if '.' in interface_name else "physical",
                            source="vlan_config_discovery"
                        )
                        interface_configs.append(interface_config)
            
            logger.info(f"Parsed {len(interface_configs)} VLAN configurations from traditional output")
            return interface_configs
            
        except Exception as e:
            logger.error(f"Error parsing VLAN config output: {e}")
            return []
    
    def discover_specific_interface_config(self, device_name: str, interface_name: str) -> Optional[InterfaceConfig]:
        """Discover configuration for a specific interface using bridge domain context"""
        
        try:
            # Extract base interface and VLAN from interface name
            if '.' in interface_name:
                base_interface = interface_name.split('.')[0]
                vlan_part = interface_name.split('.')[-1]
                expected_vlan = int(vlan_part) if vlan_part.isdigit() else None
            else:
                base_interface = interface_name
                expected_vlan = None
            
            logger.info(f"Discovering specific interface {interface_name} on {device_name}")
            
            # Use comprehensive discovery for this interface
            configs = self.discover_interface_configurations_for_bd(device_name, base_interface, interface_name)
            
            # Find exact match
            for config in configs:
                if config.interface_name == interface_name:
                    logger.info(f"Found exact interface config: {interface_name} VLAN {config.vlan_id}")
                    return config
            
            # Find closest match with expected VLAN
            if expected_vlan:
                for config in configs:
                    if config.vlan_id == expected_vlan and base_interface in config.interface_name:
                        logger.info(f"Found VLAN-matched interface config: {config.interface_name} VLAN {config.vlan_id}")
                        return config
            
            logger.warning(f"No configuration found for {interface_name} on {device_name}")
            return None
            
        except Exception as e:
            logger.error(f"Specific interface discovery failed: {e}")
            return None
    
    def discover_device_full_config(self, device_name: str) -> DeviceConfigSnapshot:
        """Comprehensive device configuration discovery using traditional approach"""
        
        try:
            snapshot = DeviceConfigSnapshot(
                device_name=device_name,
                discovery_source="comprehensive_traditional_discovery"
            )
            
            # Step 1: Discover all bridge domains on device (traditional command)
            bd_command = "show network-services bridge-domain | no-more"
            bd_result = self.command_executor.execute_with_mode(
                device_name, [bd_command], self.ExecutionMode.QUERY
            )
            
            if bd_result.success:
                bridge_domains = self._parse_bridge_domain_names(bd_result.output)
                
                # Step 2: For each bridge domain, get detailed configuration
                all_interface_configs = []
                for bd_name in bridge_domains:
                    bd_config = self.discover_bridge_domain_configuration(device_name, bd_name)
                    if bd_config['success']:
                        all_interface_configs.extend(bd_config['interface_configurations'])
                
                snapshot.interface_configs = all_interface_configs
                snapshot.total_interfaces = len(all_interface_configs)
                snapshot.configured_interfaces = len([c for c in all_interface_configs if c.vlan_id])
            
            logger.info(f"Device snapshot completed for {device_name}: {len(snapshot.interface_configs)} interface configs")
            return snapshot
            
        except Exception as e:
            logger.error(f"Device config snapshot failed for {device_name}: {e}")
            raise TargetedDiscoveryError(f"Device snapshot failed: {e}")
    
    def _parse_bridge_domain_names(self, bd_output: str) -> List[str]:
        """Parse bridge domain names from device output (traditional parsing)"""
        
        bridge_domains = []
        
        try:
            # Parse table format output from "show network-services bridge-domain | no-more"
            # Example:
            # | Name                           |
            # |--------------------------------|
            # | g_visaev_v251                  |
            lines = bd_output.split('\n')
            
            for line in lines:
                line = line.strip()
                # Skip header lines and separators
                if line.startswith('|') and 'Name' not in line and '---' not in line and line != '|':
                    # Extract bridge domain name from table format
                    # Format: | g_visaev_v251                  |
                    parts = line.split('|')
                    if len(parts) >= 2:
                        bd_name = parts[1].strip()
                        if bd_name and bd_name != 'Name':
                            bridge_domains.append(bd_name)
            
            logger.info(f"Parsed {len(bridge_domains)} bridge domain names")
            return bridge_domains
            
        except Exception as e:
            logger.error(f"Error parsing bridge domain names: {e}")
            return []
    
    def validate_discovery_accuracy(self, device_name: str, discovered_configs: List[InterfaceConfig]) -> Dict:
        """Validate accuracy of discovered configurations"""
        
        try:
            validation_result = {
                'total_discovered': len(discovered_configs),
                'valid_configs': 0,
                'invalid_configs': 0,
                'warnings': [],
                'accuracy_score': 0.0
            }
            
            for config in discovered_configs:
                # Validate VLAN ID range
                if config.vlan_id and (1 <= config.vlan_id <= 4094):
                    validation_result['valid_configs'] += 1
                else:
                    validation_result['invalid_configs'] += 1
                    validation_result['warnings'].append(f"Invalid VLAN ID: {config.vlan_id} on {config.interface_name}")
                
                # Validate interface name format
                if not re.match(r'^(ge100-0/0/|bundle-)', config.interface_name):
                    validation_result['warnings'].append(f"Unusual interface name: {config.interface_name}")
            
            # Calculate accuracy score
            if validation_result['total_discovered'] > 0:
                validation_result['accuracy_score'] = validation_result['valid_configs'] / validation_result['total_discovered']
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Discovery validation failed: {e}")
            return {'error': str(e)}


# Convenience functions
def discover_interface_configurations(device_name: str, interface_pattern: str = None) -> List[InterfaceConfig]:
    """Convenience function for interface configuration discovery"""
    discovery = TargetedConfigurationDiscovery()
    return discovery.discover_interface_vlan_configurations(device_name, interface_pattern)


def discover_bridge_domain_on_device(device_name: str, bd_name: str) -> Dict:
    """Convenience function for bridge domain discovery on specific device"""
    discovery = TargetedConfigurationDiscovery()
    return discovery.discover_bridge_domain_configuration(device_name, bd_name)


def discover_device_configurations(device_name: str) -> DeviceConfigSnapshot:
    """Convenience function for device configuration discovery"""
    discovery = TargetedConfigurationDiscovery()
    return discovery.discover_device_full_config(device_name)


def discover_specific_interface(device_name: str, interface_name: str) -> Optional[InterfaceConfig]:
    """Convenience function for specific interface discovery"""
    discovery = TargetedConfigurationDiscovery()
    return discovery.discover_specific_interface_config(device_name, interface_name)
