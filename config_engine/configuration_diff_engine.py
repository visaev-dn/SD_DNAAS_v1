#!/usr/bin/env python3
"""
Configuration Diff Engine
Analyzes changes between current and new configurations to enable smart incremental deployment.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .smart_deployment_types import DeviceChange, VlanChange, ImpactAssessment, DeploymentDiff, RiskLevel

logger = logging.getLogger(__name__)

@dataclass
class CommandDiff:
    """Represents a difference between old and new commands"""
    command_type: str  # 'add', 'remove', 'modify'
    old_command: Optional[str]
    new_command: Optional[str]
    device: str
    interface: Optional[str]
    vlan_id: Optional[int]

@dataclass
class InterfaceChange:
    """Represents a change to an interface configuration"""
    interface_name: str
    old_config: Dict
    new_config: Dict
    change_type: str  # 'add', 'remove', 'modify'

class ConfigurationDiffEngine:
    """
    Engine for analyzing differences between network configurations.
    
    Features:
    - Device-level change detection
    - Command-level diffing
    - VLAN change analysis
    - Impact assessment
    """
    
    def __init__(self, builder):
        """
        Initialize configuration diff engine.
        
        Args:
            builder: Bridge domain builder instance for topology information
        """
        self.builder = builder
        self.logger = logger
        
        # Command patterns for parsing
        self.vlan_pattern = re.compile(r'vlan\s+(\d+)', re.IGNORECASE)
        self.interface_pattern = re.compile(r'interface\s+([^\s]+)', re.IGNORECASE)
        self.switchport_pattern = re.compile(r'switchport\s+([^\s]+)', re.IGNORECASE)
        
    def analyze_configurations(self, current_config: Dict, new_config: Dict) -> DeploymentDiff:
        """
        Analyze differences between current and new configurations.
        
        Args:
            current_config: Current deployed configuration
            new_config: New configuration to deploy
            
        Returns:
            DeploymentDiff with detailed change analysis
        """
        try:
            self.logger.info("Starting configuration analysis")
            
            # Parse configurations
            current_parsed = self._parse_configuration(current_config)
            new_parsed = self._parse_configuration(new_config)
            
            # Analyze device changes
            devices_to_add = self._find_devices_to_add(current_parsed, new_parsed)
            devices_to_modify = self._find_devices_to_modify(current_parsed, new_parsed)
            devices_to_remove = self._find_devices_to_remove(current_parsed, new_parsed)
            unchanged_devices = self._find_unchanged_devices(current_parsed, new_parsed)
            
            # Analyze VLAN changes
            vlan_changes = self._analyze_vlan_changes(current_parsed, new_parsed)
            
            # Assess impact
            estimated_impact = self._assess_deployment_impact(
                devices_to_add, devices_to_modify, devices_to_remove, vlan_changes
            )
            
            diff = DeploymentDiff(
                devices_to_add=devices_to_add,
                devices_to_modify=devices_to_modify,
                devices_to_remove=devices_to_remove,
                unchanged_devices=unchanged_devices,
                vlan_changes=vlan_changes,
                estimated_impact=estimated_impact
            )
            
            self.logger.info(f"Configuration analysis complete: "
                           f"{len(devices_to_add)} add, {len(devices_to_modify)} modify, "
                           f"{len(devices_to_remove)} remove, {len(vlan_changes)} VLAN changes")
            
            return diff
            
        except Exception as e:
            self.logger.error(f"Error analyzing configurations: {e}")
            raise
    
    def _parse_configuration(self, config: Dict) -> Dict:
        """
        Parse configuration into structured format for analysis.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Parsed configuration with devices, commands, and metadata
        """
        try:
            parsed = {
                'devices': {},
                'vlans': {},
                'metadata': {}
            }
            
            # Handle different configuration formats
            if isinstance(config, dict):
                # Direct device configuration format
                for device_name, device_config in config.items():
                    if isinstance(device_config, dict) and 'commands' in device_config:
                        parsed['devices'][device_name] = {
                            'commands': device_config['commands'],
                            'interfaces': self._extract_interfaces(device_config['commands']),
                            'vlans': self._extract_vlans(device_config['commands'])
                        }
                    elif isinstance(device_config, list):
                        # List of commands format
                        parsed['devices'][device_name] = {
                            'commands': device_config,
                            'interfaces': self._extract_interfaces(device_config),
                            'vlans': self._extract_vlans(device_config)
                        }
            
            # Extract global VLAN information
            parsed['vlans'] = self._extract_global_vlans(config)
            
            # Extract metadata
            if 'metadata' in config:
                parsed['metadata'] = config['metadata']
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing configuration: {e}")
            raise
    
    def _extract_interfaces(self, commands: List[str]) -> Dict[str, Dict]:
        """Extract interface configurations from commands."""
        interfaces = {}
        current_interface = None
        
        for command in commands:
            # Check for interface command
            interface_match = self.interface_pattern.search(command)
            if interface_match:
                current_interface = interface_match.group(1)
                interfaces[current_interface] = {
                    'commands': [],
                    'vlans': set(),
                    'switchport_mode': None
                }
            
            # Add command to current interface
            if current_interface and current_interface in interfaces:
                interfaces[current_interface]['commands'].append(command)
                
                # Extract VLAN information
                vlan_match = self.vlan_pattern.search(command)
                if vlan_match:
                    vlan_id = int(vlan_match.group(1))
                    interfaces[current_interface]['vlans'].add(vlan_id)
                
                # Extract switchport mode
                switchport_match = self.switchport_pattern.search(command)
                if switchport_match:
                    mode = switchport_match.group(1)
                    if 'mode' in mode:
                        interfaces[current_interface]['switchport_mode'] = mode
        
        return interfaces
    
    def _extract_vlans(self, commands: List[str]) -> Dict[int, Dict]:
        """Extract VLAN configurations from commands."""
        vlans = {}
        
        for command in commands:
            vlan_match = self.vlan_pattern.search(command)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
                if vlan_id not in vlans:
                    vlans[vlan_id] = {
                        'commands': [],
                        'interfaces': set()
                    }
                vlans[vlan_id]['commands'].append(command)
        
        return vlans
    
    def _extract_global_vlans(self, config: Dict) -> Dict[int, Dict]:
        """Extract global VLAN information from configuration."""
        vlans = {}
        
        # Look for VLAN definitions in the configuration
        if isinstance(config, dict):
            for key, value in config.items():
                if key == 'vlans' and isinstance(value, dict):
                    vlans = value
                elif key == 'vlan_config' and isinstance(value, dict):
                    vlans = value
        
        return vlans
    
    def _find_devices_to_add(self, current_parsed: Dict, new_parsed: Dict) -> List[DeviceChange]:
        """Find devices that need to be added."""
        devices_to_add = []
        
        for device_name in new_parsed['devices']:
            if device_name not in current_parsed['devices']:
                # New device - extract configuration
                device_config = new_parsed['devices'][device_name]
                
                change = DeviceChange(
                    device_name=device_name,
                    change_type='add',
                    old_commands=[],
                    new_commands=device_config['commands'],
                    affected_interfaces=list(device_config['interfaces'].keys()),
                    vlan_changes=self._extract_vlan_changes_for_device(device_name, {}, device_config)
                )
                
                devices_to_add.append(change)
        
        return devices_to_add
    
    def _find_devices_to_modify(self, current_parsed: Dict, new_parsed: Dict) -> List[DeviceChange]:
        """Find devices that need to be modified."""
        devices_to_modify = []
        
        for device_name in new_parsed['devices']:
            if device_name in current_parsed['devices']:
                current_device = current_parsed['devices'][device_name]
                new_device = new_parsed['devices'][device_name]
                
                # Check if there are actual changes
                if self._has_device_changes(current_device, new_device):
                    # Extract changed commands
                    changed_commands = self._diff_device_commands(current_device, new_device)
                    
                    if changed_commands['added'] or changed_commands['removed'] or changed_commands['modified']:
                        change = DeviceChange(
                            device_name=device_name,
                            change_type='modify',
                            old_commands=current_device['commands'],
                            new_commands=new_device['commands'],
                            affected_interfaces=self._find_affected_interfaces(current_device, new_device),
                            vlan_changes=self._extract_vlan_changes_for_device(device_name, current_device, new_device)
                        )
                        
                        devices_to_modify.append(change)
        
        return devices_to_modify
    
    def _find_devices_to_remove(self, current_parsed: Dict, new_parsed: Dict) -> List[DeviceChange]:
        """Find devices that need to be removed."""
        devices_to_remove = []
        
        for device_name in current_parsed['devices']:
            if device_name not in new_parsed['devices']:
                # Device to be removed
                device_config = current_parsed['devices'][device_name]
                
                change = DeviceChange(
                    device_name=device_name,
                    change_type='remove',
                    old_commands=device_config['commands'],
                    new_commands=[],
                    affected_interfaces=list(device_config['interfaces'].keys()),
                    vlan_changes=self._extract_vlan_changes_for_device(device_name, device_config, {})
                )
                
                devices_to_remove.append(change)
        
        return devices_to_remove
    
    def _find_unchanged_devices(self, current_parsed: Dict, new_parsed: Dict) -> List[str]:
        """Find devices that haven't changed."""
        unchanged = []
        
        for device_name in current_parsed['devices']:
            if device_name in new_parsed['devices']:
                current_device = current_parsed['devices'][device_name]
                new_device = new_parsed['devices'][device_name]
                
                if not self._has_device_changes(current_device, new_device):
                    unchanged.append(device_name)
        
        return unchanged
    
    def _has_device_changes(self, current_device: Dict, new_device: Dict) -> bool:
        """Check if device configuration has changed."""
        # Compare commands
        if current_device['commands'] != new_device['commands']:
            return True
        
        # Compare interfaces
        if current_device['interfaces'] != new_device['interfaces']:
            return True
        
        # Compare VLANs
        if current_device['vlans'] != new_device['vlans']:
            return True
        
        return False
    
    def _diff_device_commands(self, current_device: Dict, new_device: Dict) -> Dict:
        """Diff commands between current and new device configurations."""
        current_commands = set(current_device['commands'])
        new_commands = set(new_device['commands'])
        
        return {
            'added': list(new_commands - current_commands),
            'removed': list(current_commands - new_commands),
            'modified': [],  # Would need more sophisticated diffing for this
            'unchanged': list(current_commands & new_commands)
        }
    
    def _find_affected_interfaces(self, current_device: Dict, new_device: Dict) -> List[str]:
        """Find interfaces that are affected by changes."""
        affected = set()
        
        # Check for interface changes
        current_interfaces = set(current_device['interfaces'].keys())
        new_interfaces = set(new_device['interfaces'].keys())
        
        # Added interfaces
        affected.update(new_interfaces - current_interfaces)
        
        # Removed interfaces
        affected.update(current_interfaces - new_interfaces)
        
        # Modified interfaces
        common_interfaces = current_interfaces & new_interfaces
        for interface in common_interfaces:
            if (current_device['interfaces'][interface] != 
                new_device['interfaces'][interface]):
                affected.add(interface)
        
        return list(affected)
    
    def _extract_vlan_changes_for_device(self, device_name: str, current_device: Dict, new_device: Dict) -> List[Dict]:
        """Extract VLAN changes for a specific device."""
        vlan_changes = []
        
        current_vlans = current_device.get('vlans', {})
        new_vlans = new_device.get('vlans', {})
        
        # Find added VLANs
        for vlan_id in new_vlans:
            if vlan_id not in current_vlans:
                vlan_changes.append({
                    'vlan_id': vlan_id,
                    'change_type': 'add',
                    'device': device_name,
                    'old_config': {},
                    'new_config': new_vlans[vlan_id]
                })
        
        # Find removed VLANs
        for vlan_id in current_vlans:
            if vlan_id not in new_vlans:
                vlan_changes.append({
                    'vlan_id': vlan_id,
                    'change_type': 'remove',
                    'device': device_name,
                    'old_config': current_vlans[vlan_id],
                    'new_config': {}
                })
        
        # Find modified VLANs
        for vlan_id in current_vlans:
            if vlan_id in new_vlans:
                if current_vlans[vlan_id] != new_vlans[vlan_id]:
                    vlan_changes.append({
                        'vlan_id': vlan_id,
                        'change_type': 'modify',
                        'device': device_name,
                        'old_config': current_vlans[vlan_id],
                        'new_config': new_vlans[vlan_id]
                    })
        
        return vlan_changes
    
    def _analyze_vlan_changes(self, current_parsed: Dict, new_parsed: Dict) -> List[VlanChange]:
        """Analyze VLAN-level changes across the configuration."""
        vlan_changes = []
        
        current_vlans = current_parsed.get('vlans', {})
        new_vlans = new_parsed.get('vlans', {})
        
        # Find added VLANs
        for vlan_id in new_vlans:
            if vlan_id not in current_vlans:
                vlan_changes.append(VlanChange(
                    vlan_id=vlan_id,
                    change_type='add',
                    affected_devices=self._find_devices_using_vlan(new_parsed, vlan_id),
                    old_config={},
                    new_config=new_vlans[vlan_id]
                ))
        
        # Find removed VLANs
        for vlan_id in current_vlans:
            if vlan_id not in new_vlans:
                vlan_changes.append(VlanChange(
                    vlan_id=vlan_id,
                    change_type='remove',
                    affected_devices=self._find_devices_using_vlan(current_parsed, vlan_id),
                    old_config=current_vlans[vlan_id],
                    new_config={}
                ))
        
        # Find modified VLANs
        for vlan_id in current_vlans:
            if vlan_id in new_vlans:
                if current_vlans[vlan_id] != new_vlans[vlan_id]:
                    vlan_changes.append(VlanChange(
                        vlan_id=vlan_id,
                        change_type='modify',
                        affected_devices=self._find_devices_using_vlan(new_parsed, vlan_id),
                        old_config=current_vlans[vlan_id],
                        new_config=new_vlans[vlan_id]
                    ))
        
        return vlan_changes
    
    def _find_devices_using_vlan(self, parsed_config: Dict, vlan_id: int) -> List[str]:
        """Find devices that use a specific VLAN."""
        devices = []
        
        for device_name, device_config in parsed_config['devices'].items():
            if vlan_id in device_config['vlans']:
                devices.append(device_name)
        
        return devices
    
    def _assess_deployment_impact(self, devices_to_add: List[DeviceChange], 
                                 devices_to_modify: List[DeviceChange], 
                                 devices_to_remove: List[DeviceChange],
                                 vlan_changes: List[VlanChange]) -> ImpactAssessment:
        """Assess the impact of the deployment."""
        try:
            total_devices = len(devices_to_add) + len(devices_to_modify) + len(devices_to_remove)
            
            # Estimate duration based on operation types
            add_time = len(devices_to_add) * 30      # 30s per device addition
            modify_time = len(devices_to_modify) * 45 # 45s per device modification
            remove_time = len(devices_to_remove) * 20 # 20s per device removal
            
            estimated_duration = add_time + modify_time + remove_time
            
            # Assess risk level
            risk_level = self._calculate_risk_level(total_devices, vlan_changes)
            
            # Identify potential conflicts
            potential_conflicts = self._identify_potential_conflicts(
                devices_to_add, devices_to_modify, devices_to_remove, vlan_changes
            )
            
            # Assess rollback complexity
            rollback_complexity = self._assess_rollback_complexity(
                devices_to_add, devices_to_modify, devices_to_remove
            )
            
            return ImpactAssessment(
                affected_device_count=total_devices,
                estimated_duration=estimated_duration,
                risk_level=risk_level,
                potential_conflicts=potential_conflicts,
                rollback_complexity=rollback_complexity
            )
            
        except Exception as e:
            self.logger.error(f"Error assessing deployment impact: {e}")
            # Return safe defaults
            return ImpactAssessment(
                affected_device_count=0,
                estimated_duration=0,
                risk_level=RiskLevel.HIGH,
                potential_conflicts=["Unable to assess impact"],
                rollback_complexity="Unknown"
            )
    
    def _calculate_risk_level(self, total_devices: int, vlan_changes: List[VlanChange]) -> RiskLevel:
        """Calculate risk level based on deployment scope."""
        risk_score = 0
        
        # Device count risk
        if total_devices > 10:
            risk_score += 3
        elif total_devices > 5:
            risk_score += 2
        elif total_devices > 1:
            risk_score += 1
        
        # VLAN changes risk
        if vlan_changes:
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _identify_potential_conflicts(self, devices_to_add: List[DeviceChange],
                                    devices_to_modify: List[DeviceChange],
                                    devices_to_remove: List[DeviceChange],
                                    vlan_changes: List[VlanChange]) -> List[str]:
        """Identify potential conflicts in the deployment."""
        conflicts = []
        
        # Check for VLAN conflicts
        vlan_ids = set()
        for change in devices_to_add + devices_to_modify:
            for vlan_change in change.vlan_changes:
                if vlan_change['vlan_id'] in vlan_ids:
                    conflicts.append(f"VLAN {vlan_change['vlan_id']} used by multiple devices")
                vlan_ids.add(vlan_change['vlan_id'])
        
        # Check for interface conflicts
        interface_usage = {}
        for change in devices_to_add + devices_to_modify:
            for interface in change.affected_interfaces:
                if interface in interface_usage:
                    conflicts.append(f"Interface {interface} used by multiple devices")
                interface_usage[interface] = change.device_name
        
        # Check for removal conflicts
        if devices_to_remove and (devices_to_add or devices_to_modify):
            conflicts.append("Simultaneous addition/modification and removal may cause conflicts")
        
        return conflicts
    
    def _assess_rollback_complexity(self, devices_to_add: List[DeviceChange],
                                   devices_to_modify: List[DeviceChange],
                                   devices_to_remove: List[DeviceChange]) -> str:
        """Assess the complexity of rolling back the deployment."""
        total_changes = len(devices_to_add) + len(devices_to_modify) + len(devices_to_remove)
        
        if total_changes == 0:
            return "None"
        elif total_changes <= 3:
            return "Low"
        elif total_changes <= 8:
            return "Medium"
        else:
            return "High"
    
    def generate_change_summary(self, diff: DeploymentDiff) -> str:
        """Generate a human-readable summary of changes."""
        try:
            summary_parts = []
            
            if diff.devices_to_add:
                summary_parts.append(f"Add {len(diff.devices_to_add)} new device(s)")
            
            if diff.devices_to_modify:
                summary_parts.append(f"Modify {len(diff.devices_to_modify)} existing device(s)")
            
            if diff.devices_to_remove:
                summary_parts.append(f"Remove {len(diff.devices_to_remove)} device(s)")
            
            if diff.vlan_changes:
                summary_parts.append(f"Update {len(diff.vlan_changes)} VLAN(s)")
            
            if diff.estimated_impact.affected_device_count == 0:
                summary_parts.append("No changes detected")
            
            summary = "; ".join(summary_parts)
            
            # Add impact information
            if diff.estimated_impact.affected_device_count > 0:
                summary += f"\nEstimated duration: {diff.estimated_impact.estimated_duration}s"
                summary += f"\nRisk level: {diff.estimated_impact.risk_level.value}"
                
                if diff.estimated_impact.potential_conflicts:
                    summary += f"\nPotential conflicts: {', '.join(diff.estimated_impact.potential_conflicts)}"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating change summary: {e}")
            return "Unable to generate change summary" 