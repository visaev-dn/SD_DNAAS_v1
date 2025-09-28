#!/usr/bin/env python3
"""
BD Editor Change Impact Analyzer

Analyzes the impact of BD changes on network services and provides
consequence analysis to help users understand change effects.
"""

import logging
from typing import Dict, List
from .data_models import ImpactAnalysis

logger = logging.getLogger(__name__)


class ChangeImpactAnalyzer:
    """Analyze the impact of BD changes on network and services"""
    
    def __init__(self):
        pass
    
    def analyze_changes(self, bridge_domain: Dict, changes: List[Dict]) -> ImpactAnalysis:
        """Analyze impact of all changes"""
        
        impact = ImpactAnalysis()
        
        try:
            for change in changes:
                action = change.get('action', '')
                
                if action.startswith('add_') and 'interface' in action:
                    change_impact = self._analyze_interface_addition(bridge_domain, change)
                elif action.startswith('remove_') and 'interface' in action:
                    change_impact = self._analyze_interface_removal(bridge_domain, change)
                elif action.startswith('modify_') and 'interface' in action:
                    change_impact = self._analyze_interface_modification(bridge_domain, change)
                else:
                    change_impact = self._analyze_generic_change(bridge_domain, change)
                
                impact.merge(change_impact)
            
            # Analyze overall impact
            impact = self._analyze_overall_impact(bridge_domain, changes, impact)
            
        except Exception as e:
            logger.error(f"Error analyzing change impact: {e}")
            impact.warnings.append(f"Impact analysis error: {e}")
        
        return impact
    
    def _analyze_interface_addition(self, bd: Dict, change: Dict) -> ImpactAnalysis:
        """Analyze impact of adding customer interface"""
        
        impact = ImpactAnalysis()
        
        try:
            interface_info = change.get('interface', {})
            device = interface_info.get('device', 'unknown')
            interface = interface_info.get('interface', 'unknown')
            
            impact.customer_interfaces_affected += 1
            impact.affected_devices.add(device)
            impact.services_impacted.append(f"New customer connectivity on {device}:{interface}")
            impact.estimated_downtime = "None (addition only)"
            
            # Check for potential conflicts
            existing_interfaces = self._get_existing_interfaces_on_device(bd, device)
            interface_name = interface_info.get('interface', '')
            
            if interface_name in existing_interfaces:
                impact.warnings.append(f"Interface {interface_name} may already exist on {device}")
            
            # Check VLAN conflicts
            vlan_conflicts = self._check_vlan_conflicts(bd, interface_info)
            if vlan_conflicts:
                impact.warnings.extend(vlan_conflicts)
            
        except Exception as e:
            logger.error(f"Error analyzing interface addition impact: {e}")
            impact.warnings.append(f"Impact analysis error: {e}")
        
        return impact
    
    def _analyze_interface_removal(self, bd: Dict, change: Dict) -> ImpactAnalysis:
        """Analyze impact of removing customer interface"""
        
        impact = ImpactAnalysis()
        
        try:
            interface_info = change.get('interface', {})
            device = interface_info.get('device', 'unknown')
            interface = interface_info.get('interface', 'unknown')
            
            impact.customer_interfaces_affected += 1
            impact.affected_devices.add(device)
            impact.services_impacted.append(f"Customer disconnection on {device}:{interface}")
            impact.estimated_downtime = "Immediate (service interruption)"
            
            # Check if this is the last customer interface
            remaining_customer_interfaces = self._count_remaining_customer_interfaces(bd, change)
            if remaining_customer_interfaces <= 1:  # Including the one being removed
                impact.warnings.append("Removing last customer interface - BD will have no customer connectivity")
                impact.warnings.append("Consider keeping at least one customer interface for service")
            
            # Check for service dependencies
            service_dependencies = self._check_service_dependencies(bd, interface_info)
            if service_dependencies:
                impact.warnings.extend(service_dependencies)
            
        except Exception as e:
            logger.error(f"Error analyzing interface removal impact: {e}")
            impact.warnings.append(f"Impact analysis error: {e}")
        
        return impact
    
    def _analyze_interface_modification(self, bd: Dict, change: Dict) -> ImpactAnalysis:
        """Analyze impact of modifying customer interface"""
        
        impact = ImpactAnalysis()
        
        try:
            interface_info = change.get('interface', {})
            device = interface_info.get('device', 'unknown')
            interface = interface_info.get('interface', 'unknown')
            
            impact.customer_interfaces_affected += 1
            impact.affected_devices.add(device)
            impact.services_impacted.append(f"Configuration change on {device}:{interface}")
            impact.estimated_downtime = "Brief (configuration update)"
            
            # Check modification type
            modification_type = change.get('modification_type', 'unknown')
            if modification_type == 'vlan_change':
                impact.warnings.append("VLAN change may affect customer traffic tagging")
            elif modification_type == 'manipulation_change':
                impact.warnings.append("VLAN manipulation change may affect QinQ behavior")
            
        except Exception as e:
            logger.error(f"Error analyzing interface modification impact: {e}")
            impact.warnings.append(f"Impact analysis error: {e}")
        
        return impact
    
    def _analyze_generic_change(self, bd: Dict, change: Dict) -> ImpactAnalysis:
        """Analyze impact of generic change"""
        
        impact = ImpactAnalysis()
        
        action = change.get('action', 'unknown')
        description = change.get('description', 'Unknown change')
        
        impact.services_impacted.append(description)
        impact.estimated_downtime = "Unknown"
        impact.warnings.append(f"Generic change: {action} - impact analysis limited")
        
        return impact
    
    def _analyze_overall_impact(self, bridge_domain: Dict, changes: List[Dict], current_impact: ImpactAnalysis) -> ImpactAnalysis:
        """Analyze overall impact of all changes combined"""
        
        try:
            # Calculate overall service impact
            if current_impact.customer_interfaces_affected > 0:
                bd_name = bridge_domain.get('name', 'unknown')
                current_impact.services_impacted.append(f"Bridge domain {bd_name} configuration updated")
            
            # Determine overall downtime estimate
            if any('Immediate' in impact for impact in current_impact.services_impacted):
                current_impact.estimated_downtime = "Immediate (service interruption)"
            elif any('Brief' in impact for impact in current_impact.services_impacted):
                current_impact.estimated_downtime = "Brief (configuration update)"
            elif current_impact.customer_interfaces_affected > 0:
                current_impact.estimated_downtime = "None (addition only)"
            
            # Add overall recommendations
            if len(current_impact.affected_devices) > 1:
                current_impact.warnings.append(f"Changes affect {len(current_impact.affected_devices)} devices - coordinate deployment")
            
            if current_impact.customer_interfaces_affected > 3:
                current_impact.warnings.append(f"Large number of interface changes ({current_impact.customer_interfaces_affected}) - consider phased deployment")
            
        except Exception as e:
            logger.error(f"Error analyzing overall impact: {e}")
            current_impact.warnings.append(f"Overall impact analysis error: {e}")
        
        return current_impact
    
    def _get_existing_interfaces_on_device(self, bd: Dict, device: str) -> List[str]:
        """Get existing interfaces on specific device"""
        
        existing = []
        
        try:
            devices = bd.get('devices', {})
            device_info = devices.get(device, {})
            interfaces = device_info.get('interfaces', [])
            
            for interface in interfaces:
                interface_name = interface.get('name', '')
                if interface_name:
                    existing.append(interface_name)
        
        except Exception as e:
            logger.error(f"Error getting existing interfaces for {device}: {e}")
        
        return existing
    
    def _count_remaining_customer_interfaces(self, bd: Dict, removal_change: Dict) -> int:
        """Count customer interfaces that would remain after removal"""
        
        try:
            from .interface_analyzer import BDInterfaceAnalyzer
            analyzer = BDInterfaceAnalyzer()
            
            # Get current interface analysis
            analysis = analyzer.analyze_bd_interfaces(bd)
            
            # Count customer interfaces (excluding the one being removed)
            customer_count = analysis.summary['customer_count']
            
            # If this change removes a customer interface, subtract 1
            interface_info = removal_change.get('interface', {})
            interface_name = interface_info.get('interface', '')
            
            if interface_name and not analyzer.is_infrastructure_interface(interface_name, ''):
                customer_count -= 1
            
            return customer_count
            
        except Exception as e:
            logger.error(f"Error counting remaining customer interfaces: {e}")
            return 0
    
    def _check_vlan_conflicts(self, bd: Dict, interface_info: Dict) -> List[str]:
        """Check for VLAN conflicts with new interface"""
        
        conflicts = []
        
        try:
            # Check if VLAN is already in use on same device
            device = interface_info.get('device')
            vlan_id = interface_info.get('vlan_id')
            
            if device and vlan_id:
                existing_interfaces = self._get_existing_interfaces_on_device(bd, device)
                
                # Check for VLAN conflicts (simplified check)
                for existing in existing_interfaces:
                    if f".{vlan_id}" in existing:
                        conflicts.append(f"VLAN {vlan_id} may already be in use on {device} (interface: {existing})")
        
        except Exception as e:
            logger.error(f"Error checking VLAN conflicts: {e}")
        
        return conflicts
    
    def _check_service_dependencies(self, bd: Dict, interface_info: Dict) -> List[str]:
        """Check for service dependencies on interface being removed"""
        
        dependencies = []
        
        try:
            # This is a placeholder for service dependency checking
            # In a full implementation, this would check:
            # - Active customer connections
            # - Service level agreements
            # - Traffic patterns
            # - Dependent services
            
            interface = interface_info.get('interface', '')
            device = interface_info.get('device', '')
            
            # Basic check - warn about removing interfaces that might have active services
            if 'ge100-0/0/' in interface:
                dependencies.append(f"Physical interface {device}:{interface} may have active customer services")
        
        except Exception as e:
            logger.error(f"Error checking service dependencies: {e}")
        
        return dependencies


# Convenience functions
def analyze_change_impact(bridge_domain: Dict, changes: List[Dict]) -> ImpactAnalysis:
    """Convenience function to analyze change impact"""
    analyzer = ChangeImpactAnalyzer()
    return analyzer.analyze_changes(bridge_domain, changes)
