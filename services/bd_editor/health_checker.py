#!/usr/bin/env python3
"""
BD Editor Health Checker

Comprehensive BD health checking system that validates BD state
before editing and identifies potential issues.
"""

import logging
from typing import Dict, List
from .data_models import HealthReport
from .interface_analyzer import BDInterfaceAnalyzer

logger = logging.getLogger(__name__)


class BDHealthChecker:
    """Check BD health before editing"""
    
    def __init__(self):
        self.interface_analyzer = BDInterfaceAnalyzer()
    
    def check_bd_health(self, bridge_domain: Dict) -> HealthReport:
        """Comprehensive BD health check"""
        
        health_report = HealthReport()
        
        try:
            # Check data integrity
            integrity_report = self._check_data_integrity(bridge_domain)
            health_report.merge(integrity_report)
            
            # Check interface consistency
            interface_report = self._check_interface_consistency(bridge_domain)
            health_report.merge(interface_report)
            
            # Check configuration validity
            config_report = self._check_configuration_validity(bridge_domain)
            health_report.merge(config_report)
            
            # Check topology coherence
            topology_report = self._check_topology_coherence(bridge_domain)
            health_report.merge(topology_report)
            
            # Check editability
            editability_report = self._check_editability(bridge_domain)
            health_report.merge(editability_report)
            
        except Exception as e:
            logger.error(f"Error during BD health check: {e}")
            health_report.add_error(f"Health check system error: {e}")
        
        return health_report
    
    def display_health_report(self, health_report: HealthReport, bridge_domain: Dict):
        """Display human-readable health report"""
        
        bd_name = bridge_domain.get('name', 'Unknown BD')
        
        print(f"\n📊 BD HEALTH CHECK: {bd_name}")
        print("="*60)
        
        # Overall health status
        if health_report.is_healthy:
            print("✅ OVERALL HEALTH: Good - BD is ready for editing")
        else:
            print("❌ OVERALL HEALTH: Issues detected - review before editing")
        
        # Show errors
        if health_report.errors:
            print(f"\n🔴 ERRORS ({len(health_report.errors)}):")
            for error in health_report.errors:
                print(f"   • {error}")
        
        # Show warnings
        if health_report.warnings:
            print(f"\n🟡 WARNINGS ({len(health_report.warnings)}):")
            for warning in health_report.warnings:
                print(f"   • {warning}")
        
        # Show recommendations
        if health_report.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(health_report.recommendations)}):")
            for recommendation in health_report.recommendations:
                print(f"   • {recommendation}")
        
        # Summary
        if not health_report.errors and not health_report.warnings:
            print(f"\n✅ BD is in excellent health for editing")
        elif health_report.errors:
            print(f"\n⚠️  BD has issues that should be resolved before editing")
        else:
            print(f"\n💡 BD is healthy with minor considerations")
    
    def _check_data_integrity(self, bd: Dict) -> HealthReport:
        """Check basic data integrity"""
        
        report = HealthReport()
        
        try:
            # Required fields
            required_fields = ['name', 'vlan_id', 'username', 'dnaas_type']
            for field in required_fields:
                if not bd.get(field):
                    report.add_error(f"Missing required field: {field}")
            
            # VLAN ID validation
            vlan_id = bd.get('vlan_id')
            if vlan_id:
                if not isinstance(vlan_id, int) or not (1 <= vlan_id <= 4094):
                    report.add_error(f"Invalid VLAN ID: {vlan_id} (must be 1-4094)")
            
            # Username validation
            username = bd.get('username')
            if username and not isinstance(username, str):
                report.add_error(f"Invalid username format: {username}")
            
            # Device data validation
            devices = bd.get('devices', {})
            if not devices:
                report.add_warning("BD has no device data")
            elif not isinstance(devices, dict):
                report.add_error("Device data is not in correct format")
            else:
                # Check each device
                for device_name, device_data in devices.items():
                    if not isinstance(device_data, dict):
                        report.add_error(f"Device {device_name} data is not in correct format")
                        continue
                    
                    interfaces = device_data.get('interfaces', [])
                    if not interfaces:
                        report.add_warning(f"Device {device_name} has no interfaces")
                    elif not isinstance(interfaces, list):
                        report.add_error(f"Device {device_name} interfaces data is not in correct format")
            
        except Exception as e:
            report.add_error(f"Data integrity check error: {e}")
        
        return report
    
    def _check_interface_consistency(self, bd: Dict) -> HealthReport:
        """Check interface configuration consistency"""
        
        report = HealthReport()
        
        try:
            bd_type = bd.get('dnaas_type', 'unknown')
            expected_vlan = bd.get('vlan_id')
            devices = bd.get('devices', {})
            
            total_interfaces = 0
            customer_interfaces = 0
            infrastructure_interfaces = 0
            
            for device_name, device_data in devices.items():
                interfaces = device_data.get('interfaces', [])
                total_interfaces += len(interfaces)
                
                for interface in interfaces:
                    interface_name = interface.get('name', '')
                    interface_vlan = interface.get('vlan_id')
                    interface_role = interface.get('role', '')
                    
                    # Categorize interface
                    if self.interface_analyzer.is_infrastructure_interface(interface_name, interface_role):
                        infrastructure_interfaces += 1
                    else:
                        customer_interfaces += 1
                    
                    # Check VLAN consistency for single-tagged BDs
                    if bd_type == 'DNAAS_TYPE_4A_SINGLE_TAGGED':
                        if interface_vlan and interface_vlan != expected_vlan:
                            # This might be normal for infrastructure interfaces
                            if not self.interface_analyzer.is_infrastructure_interface(interface_name, interface_role):
                                report.add_warning(f"Customer interface {interface_name} VLAN mismatch: {interface_vlan} vs expected {expected_vlan}")
            
            # Check interface distribution
            if total_interfaces == 0:
                report.add_error("BD has no interfaces")
            elif customer_interfaces == 0:
                report.add_warning("BD has no customer interfaces - only infrastructure")
                report.add_recommendation("Consider adding customer interfaces for service connectivity")
            elif infrastructure_interfaces == 0:
                report.add_warning("BD has no infrastructure interfaces")
                report.add_recommendation("Verify BD has proper fabric connectivity")
            
            # Check reasonable interface counts
            if total_interfaces > 50:
                report.add_warning(f"BD has many interfaces ({total_interfaces}) - may be complex to edit")
            
        except Exception as e:
            report.add_error(f"Interface consistency check error: {e}")
        
        return report
    
    def _check_configuration_validity(self, bd: Dict) -> HealthReport:
        """Check configuration validity"""
        
        report = HealthReport()
        
        try:
            bd_type = bd.get('dnaas_type', 'unknown')
            
            # Type-specific configuration checks
            if bd_type == 'DNAAS_TYPE_4A_SINGLE_TAGGED':
                type_report = self._check_single_tagged_config(bd)
            elif bd_type == 'DNAAS_TYPE_2A_QINQ_SINGLE_BD':
                type_report = self._check_qinq_single_config(bd)
            elif bd_type == 'DNAAS_TYPE_1_DOUBLE_TAGGED':
                type_report = self._check_double_tagged_config(bd)
            else:
                type_report = self._check_generic_config(bd)
            
            report.merge(type_report)
            
        except Exception as e:
            report.add_error(f"Configuration validity check error: {e}")
        
        return report
    
    def _check_topology_coherence(self, bd: Dict) -> HealthReport:
        """Check topology coherence"""
        
        report = HealthReport()
        
        try:
            topology_type = bd.get('topology_type', 'unknown')
            devices = bd.get('devices', {})
            
            device_count = len(devices)
            
            # Check topology type consistency
            if topology_type == 'p2p' and device_count > 2:
                report.add_warning(f"P2P topology has {device_count} devices - may be p2mp")
            elif topology_type == 'p2mp' and device_count < 3:
                report.add_warning(f"P2MP topology has only {device_count} devices")
            
            # Check device types
            device_types = set()
            for device_name, device_data in devices.items():
                device_type = device_data.get('device_type', 'unknown')
                device_types.add(device_type)
            
            if 'unknown' in device_types:
                report.add_warning("Some devices have unknown device type")
            
            # Check for reasonable topology
            if 'leaf' in device_types and 'spine' not in device_types and device_count > 1:
                report.add_recommendation("Multi-leaf BD without spine - verify topology is correct")
            
        except Exception as e:
            report.add_error(f"Topology coherence check error: {e}")
        
        return report
    
    def _check_editability(self, bd: Dict) -> HealthReport:
        """Check BD editability"""
        
        report = HealthReport()
        
        try:
            # Analyze interfaces for editability
            analysis = self.interface_analyzer.analyze_bd_interfaces(bd)
            
            customer_count = analysis.summary['customer_count']
            infrastructure_count = analysis.summary['infrastructure_count']
            total_count = analysis.summary['total_interfaces']
            
            if customer_count == 0:
                report.add_warning("BD has no customer interfaces available for editing")
                report.add_recommendation("All interfaces are infrastructure - limited editing capabilities")
            elif customer_count == total_count:
                report.add_warning("BD has no infrastructure interfaces")
                report.add_recommendation("Verify BD has proper fabric connectivity")
            else:
                editability_pct = analysis.summary['editability_percentage']
                report.add_recommendation(f"BD has {customer_count} customer interfaces ({editability_pct:.1f}% editable)")
            
        except Exception as e:
            report.add_error(f"Editability check error: {e}")
        
        return report
    
    def _check_single_tagged_config(self, bd: Dict) -> HealthReport:
        """Check single-tagged BD specific configuration"""
        
        report = HealthReport()
        
        try:
            # Check that interfaces don't have manipulation or double-tags
            devices = bd.get('devices', {})
            
            for device_name, device_data in devices.items():
                interfaces = device_data.get('interfaces', [])
                
                for interface in interfaces:
                    config = interface.get('raw_cli_config', [])
                    config_str = ' '.join(config) if config else ''
                    
                    if 'vlan-manipulation' in config_str:
                        interface_name = interface.get('name', 'unknown')
                        if not self.interface_analyzer.is_infrastructure_interface(interface_name, interface.get('role', '')):
                            report.add_warning(f"Single-tagged BD has VLAN manipulation on {interface_name}")
                    
                    if 'outer-tag' in config_str and 'inner-tag' in config_str:
                        interface_name = interface.get('name', 'unknown')
                        report.add_warning(f"Single-tagged BD has double-tag config on {interface_name}")
            
        except Exception as e:
            report.add_error(f"Single-tagged config check error: {e}")
        
        return report
    
    def _check_qinq_single_config(self, bd: Dict) -> HealthReport:
        """Check QinQ single BD specific configuration"""
        
        report = HealthReport()
        
        try:
            # Check for proper QinQ configuration
            devices = bd.get('devices', {})
            has_manipulation = False
            
            for device_name, device_data in devices.items():
                interfaces = device_data.get('interfaces', [])
                
                for interface in interfaces:
                    config = interface.get('raw_cli_config', [])
                    config_str = ' '.join(config) if config else ''
                    interface_name = interface.get('name', '')
                    
                    # Customer interfaces should have manipulation
                    if self.interface_analyzer.is_customer_interface(interface_name, interface.get('role', '')):
                        if 'vlan-manipulation' in config_str:
                            has_manipulation = True
                        else:
                            report.add_warning(f"QinQ BD customer interface {interface_name} lacks VLAN manipulation")
            
            if not has_manipulation:
                report.add_warning("QinQ single BD has no VLAN manipulation - may be misclassified")
                report.add_recommendation("Verify BD type is correct for configuration")
            
        except Exception as e:
            report.add_error(f"QinQ single config check error: {e}")
        
        return report
    
    def _check_double_tagged_config(self, bd: Dict) -> HealthReport:
        """Check double-tagged BD specific configuration"""
        
        report = HealthReport()
        
        try:
            # Check for proper double-tag configuration
            devices = bd.get('devices', {})
            has_double_tags = False
            
            for device_name, device_data in devices.items():
                interfaces = device_data.get('interfaces', [])
                
                for interface in interfaces:
                    config = interface.get('raw_cli_config', [])
                    config_str = ' '.join(config) if config else ''
                    
                    if 'outer-tag' in config_str and 'inner-tag' in config_str:
                        has_double_tags = True
                    elif 'vlan-manipulation' in config_str:
                        interface_name = interface.get('name', '')
                        report.add_warning(f"Double-tagged BD has VLAN manipulation on {interface_name}")
            
            if not has_double_tags:
                report.add_warning("Double-tagged BD has no double-tag configuration - may be misclassified")
                report.add_recommendation("Verify BD type is correct for configuration")
            
        except Exception as e:
            report.add_error(f"Double-tagged config check error: {e}")
        
        return report
    
    def _check_generic_config(self, bd: Dict) -> HealthReport:
        """Check generic BD configuration"""
        
        report = HealthReport()
        
        try:
            bd_type = bd.get('dnaas_type', 'unknown')
            
            if bd_type == 'unknown':
                report.add_warning("BD type is unknown - limited editing capabilities")
                report.add_recommendation("Analyze BD configuration to determine correct type")
            else:
                report.add_warning(f"BD type {bd_type} uses generic editing - limited validation")
                report.add_recommendation("Use caution when editing specialized BD types")
            
        except Exception as e:
            report.add_error(f"Generic config check error: {e}")
        
        return report
    
    def check_editing_readiness(self, bridge_domain: Dict) -> bool:
        """Quick check if BD is ready for editing"""
        
        try:
            health_report = self.check_bd_health(bridge_domain)
            
            # BD is ready if it has no critical errors
            critical_errors = [
                error for error in health_report.errors 
                if any(keyword in error.lower() for keyword in ['missing required', 'invalid vlan', 'corrupted'])
            ]
            
            return len(critical_errors) == 0
            
        except Exception as e:
            logger.error(f"Error checking editing readiness: {e}")
            return False
    
    def suggest_health_improvements(self, bridge_domain: Dict) -> List[str]:
        """Suggest improvements for BD health"""
        
        suggestions = []
        
        try:
            health_report = self.check_bd_health(bridge_domain)
            
            # Convert errors to suggestions
            for error in health_report.errors:
                if 'missing required field' in error.lower():
                    field = error.split(':')[-1].strip()
                    suggestions.append(f"Add missing field: {field}")
                elif 'invalid vlan' in error.lower():
                    suggestions.append("Correct VLAN ID to valid range (1-4094)")
            
            # Add recommendations
            suggestions.extend(health_report.recommendations)
            
            # Add general suggestions based on analysis
            analysis = self.interface_analyzer.analyze_bd_interfaces(bridge_domain)
            customer_count = analysis.summary['customer_count']
            
            if customer_count == 0:
                suggestions.append("Add customer interfaces for service connectivity")
            elif customer_count > 10:
                suggestions.append("Consider organizing interfaces for easier management")
            
        except Exception as e:
            logger.error(f"Error generating health suggestions: {e}")
            suggestions.append("Review BD configuration for potential issues")
        
        return suggestions


# Convenience functions
def check_bd_health(bridge_domain: Dict) -> HealthReport:
    """Convenience function to check BD health"""
    checker = BDHealthChecker()
    return checker.check_bd_health(bridge_domain)


def is_bd_ready_for_editing(bridge_domain: Dict) -> bool:
    """Convenience function to check if BD is ready for editing"""
    checker = BDHealthChecker()
    return checker.check_editing_readiness(bridge_domain)


def display_bd_health_report(bridge_domain: Dict):
    """Convenience function to display BD health report"""
    checker = BDHealthChecker()
    health_report = checker.check_bd_health(bridge_domain)
    checker.display_health_report(health_report, bridge_domain)
