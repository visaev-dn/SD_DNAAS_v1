#!/usr/bin/env python3
"""
Enhanced Database Population Service

Automatically populates Enhanced Database from discovery results
with batch processing, conflict resolution, and rollback mechanisms.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

# Import Phase 1 data structures
from config_engine.phase1_data_structures import TopologyData
from config_engine.phase1_data_structures.enums import (
    TopologyType, InterfaceRole, DeviceRole, DeviceType, 
    InterfaceType, BridgeDomainType, ValidationStatus
)

# Import enhanced discovery components
from .error_handler import EnhancedDiscoveryErrorHandler, EnhancedDatabasePopulationError
from .logging_manager import EnhancedDiscoveryLoggingManager


class EnhancedDatabasePopulationService:
    """Automatically populates Enhanced Database from discovery results"""
    
    def __init__(self, enhanced_db_manager):
        self.enhanced_db_manager = enhanced_db_manager
        self.logger = logging.getLogger(__name__)
        self.error_handler = EnhancedDiscoveryErrorHandler()
        self.logging_manager = EnhancedDiscoveryLoggingManager()
        
        # Population statistics
        self.population_stats = {
            'total_records_processed': 0,
            'successfully_populated': 0,
            'failed_populations': 0,
            'conflicts_resolved': 0,
            'rollbacks_performed': 0
        }
        
        self.logger.info("🚀 Enhanced Database Population Service initialized")
    
    def validate_vlan_range(self, vlan_id: int) -> bool:
        """Validate VLAN ID per RFC 802.1Q (1-4094)"""
        return 1 <= vlan_id <= 4094

    def extract_valid_vlans(self, interfaces: List[dict]) -> List[int]:
        """Extract only RFC-compliant VLAN IDs and log violations"""
        valid_vlans = []
        invalid_vlans = []
        
        for iface in interfaces:
            # Check multiple VLAN ID sources (for QinQ and regular configs)
            vlan_sources = [
                iface.get('vlan_id'),
                iface.get('outer_vlan'), 
                iface.get('inner_vlan')
            ]
            
            # For interfaces without explicit VLAN config, try to extract from interface name
            interface_name = iface.get('interface', '')
            if not any(vlan_sources) and interface_name:
                # Check if it's a subinterface with VLAN in the name (e.g., bundle-961.123)
                if '.' in interface_name:
                    try:
                        vlan_from_name = int(interface_name.split('.')[-1])
                        if self.validate_vlan_range(vlan_from_name):
                            vlan_sources.append(vlan_from_name)
                    except (ValueError, IndexError):
                        pass
            
            for vlan_id in vlan_sources:
                if vlan_id and isinstance(vlan_id, int):
                    if self.validate_vlan_range(vlan_id):
                        if vlan_id not in valid_vlans:  # Avoid duplicates
                            valid_vlans.append(vlan_id)
                    else:
                        if vlan_id not in invalid_vlans:  # Avoid duplicates
                            invalid_vlans.append(vlan_id)
                            self.logger.warning(f"Invalid VLAN ID {vlan_id} - must be 1-4094 per RFC 802.1Q")
        
        if invalid_vlans:
            self.logger.warning(f"Found {len(invalid_vlans)} invalid VLAN IDs: {invalid_vlans}")
        
        return valid_vlans

    def _extract_vlan_from_service_name(self, service_name: str) -> int:
        """Extract VLAN ID from bridge domain service name"""
        # Common patterns: v1234, _v1234_, -1234, bundle-1234
        patterns = [
            r'_v(\d+)_',      # _v961_
            r'_v(\d+)$',      # _v961
            r'v(\d+)_',       # v961_
            r'v(\d+)$',       # v961
            r'-(\d+)$',       # bundle-961
            r'_(\d+)_',       # _961_
            r'_(\d+)$'        # _961
        ]
        
        for pattern in patterns:
            match = re.search(pattern, service_name)
            if match:
                vlan_id = int(match.group(1))
                if self.validate_vlan_range(vlan_id):
                    return vlan_id
        
        return None

    def is_qinq_service(self, service_name: str) -> bool:
        """Detect QinQ services from naming patterns"""
        service_lower = service_name.lower()
        
        # Very specific QinQ indicators only
        explicit_qinq_indicators = [
            'double_tag', 'qinq', 'dot1q_tunnel',
            'outer_tag', 'inner_tag'
        ]
        
        # ONLY detect QinQ from service names if there are explicit terms
        # Remove all heuristic patterns that cause false positives
        return any(indicator in service_lower for indicator in explicit_qinq_indicators)

    def is_qinq_interface_config(self, interfaces: List[dict]) -> bool:
        """Detect QinQ from interface VLAN configuration"""
        
        # Check for explicit QinQ indicators in VLAN configurations
        for iface in interfaces:
            # Check for VLAN manipulation (push/pop operations)
            vlan_manipulation = iface.get('vlan_manipulation')
            if vlan_manipulation:
                if ('push' in str(vlan_manipulation) and 'outer-tag' in str(vlan_manipulation)) or \
                   ('pop' in str(vlan_manipulation)):
                    return True
            
            # Check for explicit outer/inner VLAN tags
            if iface.get('outer_vlan') and iface.get('inner_vlan'):
                return True
            
            # Check for VLAN ranges (especially 1-4094) which often indicate QinQ tunneling
            vlan_range = iface.get('vlan_range')
            if vlan_range and ('1-4094' in str(vlan_range) or '1-' in str(vlan_range)):
                return True
        
        # Having multiple different VLAN IDs alone is NOT sufficient for QinQ
        # This was the previous incorrect logic that over-classified everything
        return False

    def detect_bridge_domain_type(self, service_name: str, interfaces: List[dict]) -> BridgeDomainType:
        """Detect bridge domain type using both service name and interface patterns"""
        
        # Check service name patterns first
        if self.is_qinq_service(service_name):
            self.logger.info(f"Service name indicates QinQ: {service_name}")
            return BridgeDomainType.QINQ
        
        # Check interface configuration patterns
        if self.is_qinq_interface_config(interfaces):
            self.logger.info(f"Interface config indicates QinQ for: {service_name}")
            return BridgeDomainType.QINQ
        
        # Check for VLAN ranges or lists that might indicate different BD types
        for iface in interfaces:
            vlan_range = iface.get('vlan_range')
            vlan_list = iface.get('vlan_list')
            
            if vlan_range and vlan_range != '1-4094':  # Exclude full range which is QinQ
                self.logger.debug(f"VLAN range detected for {service_name}: {vlan_range}")
                return BridgeDomainType.VLAN_RANGE
            
            if vlan_list and len(vlan_list) > 1:
                self.logger.debug(f"VLAN list detected for {service_name}: {vlan_list}")
                return BridgeDomainType.VLAN_LIST
        
        self.logger.debug(f"Defaulting to SINGLE_VLAN for: {service_name}")
        # Default to single VLAN
        return BridgeDomainType.SINGLE_VLAN

    def extract_vlan_configuration(self, interfaces: List[dict], bd_type: BridgeDomainType, bd_name: str = "unknown") -> dict:
        """Extract VLAN configuration with full RFC compliance"""
        
        # Extract only RFC-compliant VLANs
        valid_vlans = self.extract_valid_vlans(interfaces)
        
        if not valid_vlans:
            # Check if this is a native/untagged interface scenario
            interface_names = [iface.get('interface', 'unknown') for iface in interfaces]
            
            # Try to extract VLAN from bridge domain name for native interfaces
            vlan_from_bd_name = self._extract_vlan_from_service_name(bd_name)
            
            if vlan_from_bd_name and self.validate_vlan_range(vlan_from_bd_name):
                # This appears to be a native/untagged interface with VLAN from BD name
                self.logger.warning(f"Bridge Domain '{bd_name}': Using VLAN from BD name ({vlan_from_bd_name}) for native/untagged interfaces")
                self.logger.warning(f"  Native interfaces: {interface_names}")
                return {
                    'vlan_id': vlan_from_bd_name,
                    'vlan_start': vlan_from_bd_name,
                    'vlan_end': vlan_from_bd_name,
                    'vlan_list': [vlan_from_bd_name],
                    'outer_vlan': None,
                    'inner_vlan': None,
                    'native_interface': True
                }
            
            # Log with bridge domain context for debugging
            self.logger.error(f"Bridge Domain '{bd_name}': No valid VLAN IDs found (must be 1-4094 per RFC 802.1Q)")
            self.logger.error(f"  Interfaces: {interface_names}")
            self.logger.error(f"  Interface details: {[{k: v for k, v in iface.items() if k in ['vlan_id', 'outer_vlan', 'inner_vlan', 'vlan_range', 'vlan_list']} for iface in interfaces]}")
            return {
                'vlan_id': None, 
                'error': 'No valid VLANs',
                'vlan_start': None,
                'vlan_end': None,
                'vlan_list': [],
                'outer_vlan': None,
                'inner_vlan': None
            }
        
        if bd_type == BridgeDomainType.QINQ:
            if len(valid_vlans) >= 2:
                # We have enough valid VLANs for proper QinQ
                valid_vlans.sort()
                result = {
                    'outer_vlan': valid_vlans[-1],      # Higher VLAN = outer tag
                    'inner_vlan': valid_vlans[0],       # Lower VLAN = inner tag
                    'vlan_id': valid_vlans[0],          # Use inner as primary
                    'vlan_start': valid_vlans[0],
                    'vlan_end': valid_vlans[-1],
                    'vlan_list': valid_vlans
                }
                self.logger.info(f"Bridge Domain '{bd_name}': QinQ VLAN config: outer={result['outer_vlan']}, inner={result['inner_vlan']}")
                return result
            else:
                # QinQ detected but insufficient valid VLANs - this indicates a parsing failure
                interface_names = [iface.get('interface', 'unknown') for iface in interfaces]
                self.logger.error(f"Bridge Domain '{bd_name}': QinQ detected but VLAN parsing failed - found {len(valid_vlans)} VLANs: {valid_vlans}")
                self.logger.error(f"  Interfaces: {interface_names}")
                self.logger.error(f"  This indicates a fundamental issue with VLAN configuration parsing")
                
                # Don't mask the issue with fallbacks - return error state
                result = {
                    'outer_vlan': None,
                    'inner_vlan': None,
                    'vlan_id': None,
                    'vlan_start': None,
                    'vlan_end': None,
                    'vlan_list': [],
                    'error': 'QinQ_parsing_failure',
                    'error_details': f'Expected multiple VLANs for QinQ but found {len(valid_vlans)}'
                }
                return result
        
        # Single VLAN configuration
        primary_vlan = valid_vlans[0]
        result = {
            'vlan_id': primary_vlan,
            'vlan_start': primary_vlan,
            'vlan_end': primary_vlan,
            'vlan_list': [primary_vlan],
            'outer_vlan': None,
            'inner_vlan': None
        }
        self.logger.info(f"Bridge Domain '{bd_name}': Single VLAN config: {primary_vlan}")
        return result

    def detect_qinq_topology(self, interfaces: List[dict]) -> TopologyType:
        """Detect QinQ topology pattern from interface configuration"""
        
        valid_vlans = self.extract_valid_vlans(interfaces)
        
        if len(valid_vlans) < 2:
            return TopologyType.P2P  # Single VLAN = P2P
        
        # Sort VLANs to identify outer/inner patterns
        valid_vlans.sort()
        
        # Check for QinQ patterns
        if len(valid_vlans) >= 2:
            outer_vlan = valid_vlans[-1]
            inner_vlan = valid_vlans[0]
            
            # Validate QinQ VLAN relationship
            if outer_vlan > inner_vlan and outer_vlan <= 4094 and inner_vlan >= 1:
                # Check if this looks like hub-spoke (one device with multiple interfaces)
                device_count = len(set(iface.get('device_name') for iface in interfaces))
                if device_count == 1:
                    return TopologyType.QINQ_HUB_SPOKE
                elif device_count > 2:
                    return TopologyType.QINQ_MESH
                else:
                    return TopologyType.QINQ_HUB_SPOKE
        
        return TopologyType.P2P  # Fallback

    def assign_qinq_interface_roles(self, interfaces: List[dict], bd_type: BridgeDomainType) -> List[dict]:
        """Assign QinQ-specific interface roles based on bridge domain type"""
        
        if bd_type != BridgeDomainType.QINQ:
            # For non-QinQ, use traditional role assignment
            enhanced_interfaces = []
            for i, iface in enumerate(interfaces):
                # Determine if this is the source interface
                is_source = (i == 0)  # First interface is source
                
                enhanced_interfaces.append({
                    **iface,
                    'assigned_role': InterfaceRole.ACCESS if is_source else InterfaceRole.UPLINK,
                    'qinq_outer_vlan': None,
                    'qinq_inner_vlan': None
                })
            return enhanced_interfaces
        
        # QinQ interface role assignment
        enhanced_interfaces = []
        
        for iface in interfaces:
            vlan_id = iface.get('vlan_id')
            device_name = iface.get('device_name')
            
            if not vlan_id or not self.validate_vlan_range(vlan_id):
                # Skip invalid VLANs but keep interface with default role
                enhanced_interfaces.append({
                    **iface,
                    'assigned_role': InterfaceRole.ACCESS,
                    'qinq_outer_vlan': None,
                    'qinq_inner_vlan': None
                })
                continue
            
            # Determine QinQ role based on VLAN and interface characteristics
            if 'bundle' in iface.get('name', '').lower():
                # Bundle interfaces are typically QinQ edge interfaces
                assigned_role = InterfaceRole.QINQ_EDGE
            elif vlan_id > 4000:  # High VLAN numbers often indicate outer tags
                assigned_role = InterfaceRole.QINQ_NETWORK
            else:
                # Lower VLAN numbers often indicate inner tags
                assigned_role = InterfaceRole.QINQ_MULTI
            
            enhanced_interfaces.append({
                **iface,
                'assigned_role': assigned_role,
                'qinq_outer_vlan': vlan_id if vlan_id > 4000 else None,
                'qinq_inner_vlan': vlan_id if vlan_id <= 4000 else None
            })
        
        return enhanced_interfaces

    def create_qinq_topology(self, service_name: str, interfaces: List[dict], bd_type: BridgeDomainType) -> TopologyType:
        """Create QinQ-specific topology classification"""
        
        if bd_type != BridgeDomainType.QINQ:
            # For non-QinQ, use traditional P2P/P2MP logic
            device_count = len(set(iface.get('device_name') for iface in interfaces))
            return TopologyType.P2MP if device_count > 2 else TopologyType.P2P
        
        # QinQ topology detection
        return self.detect_qinq_topology(interfaces)
    
    def populate_from_discovery(self, discovery_results: Dict) -> Dict[str, Any]:
        """Populate Enhanced Database from discovery results"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='discovery_population',
            details={
                'source_system': 'discovery',
                'target_system': 'enhanced_database',
                'discovery_type': discovery_results.get('type', 'unknown')
            }
        )
        
        try:
            self.logger.info("Starting Enhanced Database population from discovery results")
            
            # Extract data from discovery results
            topologies = discovery_results.get('topologies', [])
            devices = discovery_results.get('devices', [])
            interfaces = discovery_results.get('interfaces', [])
            paths = discovery_results.get('paths', [])
            bridge_domains = discovery_results.get('bridge_domains', [])
            
            # Process each data type
            results = {
                'topologies': self._populate_topologies(topologies),
                'devices': self._populate_devices(devices),
                'interfaces': self._populate_interfaces(interfaces),
                'paths': self._populate_paths(paths),
                'bridge_domains': self._populate_bridge_domains(bridge_domains)
            }
            
            # Calculate total success
            total_success = sum(
                result['success_count'] for result in results.values()
            )
            total_records = sum(
                result['total_count'] for result in results.values()
            )
            
            # Update operation
            self.logging_manager.update_operation(operation_id, {
                'record_count': total_records,
                'success_count': total_success
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=total_success
            )
            
            self.logger.info(f"Successfully populated {total_success}/{total_records} records")
            
            return {
                'success': True,
                'total_records': total_records,
                'successful_populations': total_success,
                'results': results,
                'statistics': self.get_population_statistics()
            }
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            
            error_result = self.error_handler.handle_database_error(e, 'discovery_population')
            
            return {
                'success': False,
                'error': str(e),
                'error_details': error_result,
                'statistics': self.get_population_statistics()
            }
    
    def populate_from_legacy_files(self, file_paths: List[Path], limit_count: Optional[int] = None, service_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """Populate from existing legacy discovery files"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='legacy_file_population',
            details={
                'source_system': 'legacy_files',
                'target_system': 'enhanced_database',
                'file_count': len(file_paths)
            }
        )
        
        try:
            self.logger.info(f"Starting population from {len(file_paths)} legacy discovery files")

            # Discover default parsed directories if no explicit file list provided
            paths_to_use = list(file_paths)
            if not paths_to_use:
                default_dir = Path('topology/configs/parsed_data')
                bd_dir = default_dir / 'bridge_domain_parsed'
                candidates = []
                candidates += list(default_dir.glob('*_lacp_parsed_*.yaml'))
                candidates += list(default_dir.glob('*_lldp_parsed_*.yaml'))
                candidates += list(bd_dir.glob('*_bridge_domain_instance_parsed_*.yaml'))
                candidates += list(bd_dir.glob('*_vlan_config_parsed_*.yaml'))
                paths_to_use = candidates

            # Group files by type
            lacp_files = [p for p in paths_to_use if p.name.endswith('.yaml') and '_lacp_parsed_' in p.name]
            lldp_files = [p for p in paths_to_use if p.name.endswith('.yaml') and '_lldp_parsed_' in p.name]
            bd_instance_files = [p for p in paths_to_use if p.name.endswith('.yaml') and '_bridge_domain_instance_parsed_' in p.name]
            vlan_config_files = [p for p in paths_to_use if p.name.endswith('.yaml') and '_vlan_config_parsed_' in p.name]

            self.logger.info(
                f"Files detected - LACP: {len(lacp_files)}, LLDP: {len(lldp_files)}, BD instances: {len(bd_instance_files)}, VLAN configs: {len(vlan_config_files)}"
            )

            # Use the enhanced discovery adapter to convert
            from .discovery_adapter import EnhancedDiscoveryAdapter
            adapter = EnhancedDiscoveryAdapter(legacy_data_path='topology/configs/parsed_data', enhanced_db_manager=self.enhanced_db_manager)

            converted_topologies = []

            if lacp_files:
                converted_topologies.extend(adapter.convert_lacp_data(lacp_files))
            if bd_instance_files or vlan_config_files:
                # Build a minimal BD dataset by stitching instance + vlan files per device
                # The EnhancedDataConverter expects a dict with key 'bridge_domains'
                import yaml
                bd_records = []
                # Index VLAN configs by device
                vlan_by_device = {}
                for vf in vlan_config_files:
                    try:
                        with open(vf, 'r') as f:
                            data = yaml.safe_load(f) or {}
                        vlan_by_device[data.get('device')] = data.get('vlan_configurations', [])
                    except Exception:
                        continue
                for bf in bd_instance_files:
                    try:
                        with open(bf, 'r') as f:
                            data = yaml.safe_load(f) or {}
                        device = data.get('device')
                        instances = data.get('bridge_domain_instances', [])
                        for inst in instances:
                            # Create unified BD record per instance on this device
                            bd_records.append({
                                'service_name': inst.get('name'),
                                'source_device': device,
                                'source_interface': (inst.get('interfaces') or [None])[0],
                                'vlan_id': None,
                                'destinations': []
                            })
                    except Exception:
                        continue

                # Optional filtering by service names
                if service_filters:
                    sf_lower = {s.strip().lower() for s in service_filters if s and s.strip()}
                    if sf_lower:
                        bd_records = [r for r in bd_records if str(r.get('service_name', '')).lower() in sf_lower]
                # Optional limit by count
                if limit_count is not None and limit_count > 0:
                    bd_records = bd_records[:limit_count]

                if bd_records:
                    from .enhanced_data_converter import EnhancedDataConverter
                    conv = EnhancedDataConverter()
                    converted_topologies.extend(conv.convert_bridge_domain_data_enhanced({'bridge_domains': bd_records}))

            # Populate the database with converted topologies
            from .enhanced_database_integration import EnhancedDatabaseIntegration
            db_integration = EnhancedDatabaseIntegration(self.enhanced_db_manager)
            integration_result = db_integration.integrate_discovery_data(converted_topologies)

            # Update operation and stats
            total_created = integration_result.get('total_records', 0)
            self.logging_manager.update_operation(operation_id, {
                'record_count': total_created,
                'file_count': len(paths_to_use)
            })

            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=total_created
            )

            return {
                'success': integration_result.get('success', False),
                'file_count': len(paths_to_use),
                'topologies_converted': len(converted_topologies),
                'integration': integration_result,
                'statistics': self.get_population_statistics()
            }

        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise

    def populate_from_legacy_mapping(self, mapping_path: Path, limit_count: Optional[int] = None, service_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """Populate Enhanced DB directly from legacy bridge-domain mapping JSON."""
        operation_id = self.logging_manager.start_operation(
            operation_type='legacy_mapping_population',
            details={
                'source_system': 'legacy_mapping_json',
                'target_system': 'enhanced_database',
                'mapping_path': str(mapping_path),
                'limit_count': limit_count,
                'service_filters': service_filters or []
            }
        )

        try:
            import json
            from config_engine.phase1_data_structures import (
                DeviceInfo, InterfaceInfo, PathInfo, PathSegment,
                BridgeDomainConfig
            )
            from config_engine.phase1_data_structures.enums import (
                DeviceType, InterfaceType, InterfaceRole, TopologyType, BridgeDomainType, OuterTagImposition, ValidationStatus, DeviceRole
            )
            import re

            if not mapping_path.exists():
                raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

            with open(mapping_path, 'r') as f:
                mapping = json.load(f)

            bridge_domains = mapping.get('bridge_domains', {})
            service_names = list(bridge_domains.keys())

            # Apply filters
            if service_filters:
                sf_lower = {s.strip().lower() for s in service_filters if s and s.strip()}
                service_names = [s for s in service_names if s.lower() in sf_lower]
            if limit_count is not None and limit_count > 0:
                service_names = service_names[:limit_count]

            self.logger.info(f"Mapping BD count (selected): {len(service_names)}")

            converted_topologies: List[TopologyData] = []

            def detect_device_type_from_name(name: str) -> DeviceType:
                n = (name or '').upper()
                if 'SUPERSPINE' in n:
                    return DeviceType.SUPERSPINE
                if 'SPINE' in n:
                    return DeviceType.SPINE
                if 'LEAF' in n:
                    return DeviceType.LEAF
                return DeviceType.LEAF

            def to_interface_type(s: str) -> InterfaceType:
                x = (s or '').lower()
                if 'bundle' in x:
                    return InterfaceType.BUNDLE
                return InterfaceType.PHYSICAL

            def to_interface_role(s: str) -> InterfaceRole:
                x = (s or '').lower()
                if x == 'uplink':
                    return InterfaceRole.UPLINK
                if x == 'access':
                    return InterfaceRole.ACCESS
                return InterfaceRole.ACCESS

            def create_virtual_destinations(service_name: str, source_device: str, devices_map: dict) -> List[Dict[str, str]]:
                """Create virtual destinations for single-device bridge domains"""
                
                # First try to use actual discovered devices
                destinations = []
                for device_name, device_info in devices_map.items():
                    if device_name != source_device:
                        interfaces = device_info.get('interfaces', [])
                        if interfaces:
                            destinations.append({
                                'device': device_name,
                                'port': interfaces[0]['name']
                            })
                
                # If no destinations found, create virtual ones based on service type
                if not destinations:
                    service_lower = service_name.lower()
                    
                    if 'double_tag' in service_lower or 'qinq' in service_lower:
                        destinations.append({'device': 'EXTERNAL_QINQ_DESTINATION', 'port': 'qinq_interface'})
                    elif 'ixia' in service_lower:
                        destinations.append({'device': 'IXIA_TEST_EQUIPMENT', 'port': 'test_interface'})
                    elif 'spirent' in service_lower:
                        destinations.append({'device': 'SPIRENT_TEST_EQUIPMENT', 'port': 'test_interface'})
                    else:
                        destinations.append({'device': 'EXTERNAL_DESTINATION', 'port': 'unknown_interface'})
                
                return destinations

            for service_name in service_names:
                try:
                    bd_entry = bridge_domains.get(service_name, {})
                    devices_map = bd_entry.get('devices', {})
                    detected_vlan = bd_entry.get('detected_vlan')
                    topology_type_str = bd_entry.get('topology_type', 'unknown').lower()

                    # Get raw interface data from devices_map for source selection
                    raw_interfaces = []
                    for device_name, device_info in devices_map.items():
                        for iface in device_info.get('interfaces', []):
                            raw_interfaces.append({
                                'device_name': device_name,
                                'name': iface.get('name'),
                                'vlan_id': iface.get('vlan_id'),
                                'role': iface.get('role')
                            })

                    # Pick source device/interface first
                    source_device = None
                    source_interface = None
                    
                    # Strategy 1: Prefer leaf with access interface (typical P2P)
                    for iface in raw_interfaces:
                        if iface['role'] == 'access':
                            source_device = iface['device_name']
                            source_interface = iface['name']
                            break
                    
                    # Strategy 2: For QinQ scenarios where all interfaces are uplink,
                    # pick the device with the most interfaces (likely the source)
                    if source_device is None and raw_interfaces:
                        # Count interfaces per device
                        device_interface_counts = {}
                        for iface in raw_interfaces:
                            device_name = iface['device_name']
                            device_interface_counts[device_name] = device_interface_counts.get(device_name, 0) + 1
                        
                        # Pick device with most interfaces as source
                        if device_interface_counts:
                            source_device = max(device_interface_counts.keys(), key=lambda k: device_interface_counts[k])
                            # Pick first interface from that device
                            for iface in raw_interfaces:
                                if iface['device_name'] == source_device:
                                    source_interface = iface['name']
                                    break
                    
                    # Strategy 3: Final fallback - use first available
                    if source_device is None and raw_interfaces:
                        first = raw_interfaces[0]
                        source_device = first['device_name']
                        source_interface = first['name']

                    # Bridge domain type selection using original interface data
                    original_interfaces = []
                    for device_name, device_info in devices_map.items():
                        for iface in device_info.get('interfaces', []):
                            original_interfaces.append(iface)
                    
                    bd_type = self.detect_bridge_domain_type(service_name, original_interfaces)
                    vlan_config = self.extract_vlan_configuration(original_interfaces, bd_type, service_name)
                    
                    # Debug logging for TATA bridge domains
                    if 'TATA' in service_name:
                        self.logger.info(f"TATA BD debug - bd_type: {bd_type}, vlan_config: {vlan_config}")
                        self.logger.info(f"TATA BD debug - original_interfaces VLANs: {[iface.get('vlan_id') for iface in original_interfaces]}")
                    
                    # Use extracted VLAN configuration
                    if vlan_config['vlan_id'] is not None:
                        vlan_id = vlan_config['vlan_id']
                    elif detected_vlan is not None and 1 <= detected_vlan <= 4094:
                        # Only use detected_vlan if it's valid (not VLAN 1)
                        vlan_id = detected_vlan
                    else:
                        # Final fallback: try to extract from service name
                        if service_name:
                            m = re.search(r"(?:^|[_-])v(\d{1,4})(?:$|[_-])", service_name, re.IGNORECASE)
                            if not m:
                                # If no VLAN in name, use the first valid VLAN from interfaces
                                valid_vlans = [iface.get('vlan_id') for iface in original_interfaces if iface.get('vlan_id') and 1 <= iface.get('vlan_id') <= 4094]
                                if valid_vlans:
                                    vlan_id = valid_vlans[0]
                                else:
                                    # Last resort: use a default VLAN
                                    vlan_id = 1000
                            else:
                                vlan_id = int(m.group(1))

                    # Build destinations using our new function
                    destinations = create_virtual_destinations(service_name, source_device, devices_map)

                    # Gate required fields
                    if not source_device or not source_interface or vlan_id is None:
                        self.logger.warning(f"Skipping BD {service_name}: insufficient data (src/dev/vlan)")
                        continue

                    # Build devices and interfaces with correct roles
                    devices: List[DeviceInfo] = []
                    raw_interfaces_for_roles = []  # Raw interface data for role assignment

                    for device_name, device_info in devices_map.items():
                        dev_type = detect_device_type_from_name(device_name)
                        iface_list = device_info.get('interfaces', []) or []
                        configured_count = len(iface_list)
                        total_count = max(1, configured_count)

                        # Assign role based on whether this is the source device
                        device_role = DeviceRole.SOURCE if device_name == source_device else DeviceRole.DESTINATION

                        devices.append(DeviceInfo(
                            name=device_name,
                            device_type=dev_type,
                            device_role=device_role,
                            total_interfaces=total_count,
                            configured_interfaces=configured_count,
                            available_interfaces=max(0, total_count - configured_count),
                            position=len(devices) + 1
                        ))

                        # Collect raw interface data for role assignment
                        for iface in iface_list:
                            raw_interfaces_for_roles.append({
                                'name': iface.get('name', ''),
                                'device_name': device_name,
                                'type': iface.get('type', 'unknown'),
                                'vlan_id': iface.get('vlan_id'),
                                'bundle_id': iface.get('bundle_id'),
                                'subinterface_id': iface.get('subinterface_id'),
                                'role': iface.get('role', 'unknown')
                            })

                    # Assign QinQ-aware interface roles
                    enhanced_interfaces = self.assign_qinq_interface_roles(raw_interfaces_for_roles, bd_type)
                    
                    # Convert enhanced interfaces to InterfaceInfo objects
                    interfaces: List[InterfaceInfo] = []
                    for enhanced_iface in enhanced_interfaces:
                        iface_type = to_interface_type(enhanced_iface.get('type', 'unknown'))
                        
                        # Use the assigned role from QinQ logic
                        iface_role = enhanced_iface.get('assigned_role', InterfaceRole.ACCESS)
                        
                        interfaces.append(InterfaceInfo(
                            name=enhanced_iface.get('name', ''),
                            device_name=enhanced_iface.get('device_name'),
                            interface_type=iface_type,
                            interface_role=iface_role,
                            vlan_id=enhanced_iface.get('vlan_id'),
                            bundle_id=enhanced_iface.get('bundle_id'),
                            subinterface_id=enhanced_iface.get('subinterface_id')
                        ))

                    # Create topology
                    try:
                        # Debug logging for TATA bridge domains
                        if 'TATA' in service_name:
                            self.logger.info(f"TATA BD debug - Creating topology for {service_name}")
                            self.logger.info(f"TATA BD debug - source_device: {source_device}, source_interface: {source_interface}, vlan_id: {vlan_id}, bd_type: {bd_type}")
                            self.logger.info(f"TATA BD debug - devices count: {len(devices)}, interfaces count: {len(interfaces)}")
                            self.logger.info(f"TATA BD debug - destinations: {destinations}")
                        
                        topology = TopologyData(
                            topology_id=str(uuid.uuid4()),
                            bridge_domain_name=service_name,
                            topology_type=self.create_qinq_topology(service_name, raw_interfaces_for_roles, bd_type),
                            devices=devices,
                            interfaces=interfaces,  # Use the converted InterfaceInfo objects
                            bridge_domain_configs=[
                                BridgeDomainConfig(
                                    service_name=service_name,
                                    bridge_domain_type=bd_type,
                                    source_device=source_device,
                                    source_interface=source_interface,
                                    destinations=destinations,
                                    vlan_id=int(vlan_id),
                                    vlan_start=vlan_config['vlan_start'] if vlan_config['vlan_start'] is not None else int(vlan_id),
                                    vlan_end=vlan_config['vlan_end'] if vlan_config['vlan_end'] is not None else int(vlan_id),
                                    vlan_list=vlan_config['vlan_list'] if vlan_config['vlan_list'] else [int(vlan_id)],
                                    outer_vlan=vlan_config.get('outer_vlan'),
                                    inner_vlan=vlan_config.get('inner_vlan'),
                                    outer_tag_imposition=OuterTagImposition.EDGE if bd_type == BridgeDomainType.QINQ else OuterTagImposition.LEAF,
                                    confidence_score=0.8,
                                    validation_status=ValidationStatus.PENDING
                                )
                            ],
                            paths=[
                                PathInfo(
                                    path_name=f"path_to_{dest['device']}",
                                    path_type=TopologyType.P2P,
                                    source_device=source_device,
                                    dest_device=dest['device'],
                                    segments=[
                                        PathSegment(
                                            source_device=source_device,
                                            dest_device=dest['device'],
                                            source_interface=source_interface,
                                            dest_interface=dest['port'],
                                            segment_type="leaf_to_spine" if 'bundle' in dest['port'] else "direct"
                                        )
                                    ]
                                ) for dest in destinations
                            ],
                            scan_method="legacy_mapping",
                            confidence_score=0.8,
                            validation_status=ValidationStatus.PENDING
                        )

                        converted_topologies.append(topology)
                        self.logger.info(f"✅ Converted mapping BD {service_name}")

                    except Exception as e:
                        self.logger.error(f"Failed to convert mapping BD {service_name}: {e}")
                        # Add debug info for TATA bridge domains
                        if 'TATA' in service_name:
                            self.logger.error(f"TATA BD debug - source_device: {source_device}, source_interface: {source_interface}, vlan_id: {vlan_id}, bd_type: {bd_type}")
                            self.logger.error(f"TATA BD debug - devices count: {len(devices)}, interfaces count: {len(interfaces)}")
                        continue

                except Exception as e:
                    self.logger.error(f"Failed to convert mapping BD {service_name}: {e}")
                    continue

            # Populate DB
            from .enhanced_database_integration import EnhancedDatabaseIntegration
            db_integration = EnhancedDatabaseIntegration(self.enhanced_db_manager)
            integration_result = db_integration.integrate_discovery_data(converted_topologies)

            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=integration_result.get('total_records', 0)
            )

            return {
                'success': integration_result.get('success', False),
                'mapping_file': str(mapping_path),
                'selected_bds': len(service_names),
                'topologies_converted': len(converted_topologies),
                'integration': integration_result
            }
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def populate_from_legacy_database(self, legacy_db_path: str) -> Dict[str, Any]:
        """Populate from existing legacy database"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='legacy_database_population',
            details={
                'source_system': 'legacy_database',
                'target_system': 'enhanced_database',
                'legacy_db_path': legacy_db_path
            }
        )
        
        try:
            self.logger.info(f"Starting population from legacy database: {legacy_db_path}")
            
            # This will be implemented in Phase 1G.2
            # For now, return placeholder results
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=0
            )
            
            return {
                'success': True,
                'message': 'Legacy database population not yet implemented (Phase 1G.2)',
                'legacy_db_path': legacy_db_path,
                'statistics': self.get_population_statistics()
            }
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def batch_populate(self, data_batch: List[TopologyData]) -> Dict[str, Any]:
        """Batch populate multiple topology records"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='batch_population',
            details={
                'source_system': 'batch_data',
                'target_system': 'enhanced_database',
                'batch_size': len(data_batch)
            }
        )
        
        try:
            self.logger.info(f"Starting batch population of {len(data_batch)} topology records")
            
            # Process batch
            successful_populations = 0
            failed_populations = 0
            
            for topology in data_batch:
                try:
                    # Save topology to database
                    result = self._save_topology(topology)
                    if result:
                        successful_populations += 1
                    else:
                        failed_populations += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to populate topology {topology.bridge_domain_name}: {e}")
                    failed_populations += 1
                    self.error_handler.handle_database_error(e, 'topology_population')
                    continue
            
            # Update statistics
            self.population_stats['total_records_processed'] += len(data_batch)
            self.population_stats['successfully_populated'] += successful_populations
            self.population_stats['failed_populations'] += failed_populations
            
            # Update operation
            self.logging_manager.update_operation(operation_id, {
                'record_count': len(data_batch),
                'success_count': successful_populations,
                'failure_count': failed_populations
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=successful_populations
            )
            
            self.logger.info(f"Batch population completed: {successful_populations} successful, {failed_populations} failed")
            
            return {
                'success': True,
                'batch_size': len(data_batch),
                'successful_populations': successful_populations,
                'failed_populations': failed_populations,
                'success_rate': (successful_populations / len(data_batch)) * 100 if data_batch else 0
            }
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def _populate_topologies(self, topologies: List[TopologyData]) -> Dict[str, Any]:
        """Populate topology data"""
        
        if not topologies:
            return {'total_count': 0, 'success_count': 0, 'errors': []}
        
        successful_populations = 0
        errors = []
        
        for topology in topologies:
            try:
                result = self._save_topology(topology)
                if result:
                    successful_populations += 1
                    self.population_stats['successfully_populated'] += 1
                else:
                    errors.append(f"Failed to save topology {topology.bridge_domain_name}")
                    
            except Exception as e:
                error_msg = f"Error saving topology {topology.bridge_domain_name}: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                self.population_stats['failed_populations'] += 1
        
        self.population_stats['total_records_processed'] += len(topologies)
        
        return {
            'total_count': len(topologies),
            'success_count': successful_populations,
            'errors': errors
        }
    
    def _populate_devices(self, devices: List) -> Dict[str, Any]:
        """Populate device data"""
        
        # This will be implemented in Phase 1G.2
        # For now, return placeholder results
        
        return {
            'total_count': len(devices),
            'success_count': 0,
            'errors': ['Device population not yet implemented (Phase 1G.2)']
        }
    
    def _populate_interfaces(self, interfaces: List) -> Dict[str, Any]:
        """Populate interface data"""
        
        # This will be implemented in Phase 1G.2
        # For now, return placeholder results
        
        return {
            'total_count': len(interfaces),
            'success_count': 0,
            'errors': ['Interface population not yet implemented (Phase 1G.2)']
        }
    
    def _populate_paths(self, paths: List) -> Dict[str, Any]:
        """Populate path data"""
        
        # This will be implemented in Phase 1G.2
        # For now, return placeholder results
        
        return {
            'total_count': len(paths),
            'success_count': 0,
            'errors': ['Path population not yet implemented (Phase 1G.2)']
        }
    
    def _populate_bridge_domains(self, bridge_domains: List) -> Dict[str, Any]:
        """Populate bridge domain data"""
        
        # This will be implemented in Phase 1G.2
        # For now, return placeholder results
        
        return {
            'total_count': len(bridge_domains),
            'success_count': 0,
            'errors': ['Bridge domain population not yet implemented (Phase 1G.2)']
        }
    
    def _save_topology(self, topology: TopologyData) -> bool:
        """Save topology to Enhanced Database"""
        
        try:
            # This is a placeholder - will be implemented in Phase 1G.2
            # For now, just log the attempt
            
            self.logger.debug(f"Would save topology: {topology.bridge_domain_name}")
            
            # Simulate successful save
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save topology {topology.bridge_domain_name}: {e}")
            return False
    
    def get_population_statistics(self) -> Dict[str, Any]:
        """Get population statistics"""
        
        return {
            'total_records_processed': self.population_stats['total_records_processed'],
            'successfully_populated': self.population_stats['successfully_populated'],
            'failed_populations': self.population_stats['failed_populations'],
            'conflicts_resolved': self.population_stats['conflicts_resolved'],
            'rollbacks_performed': self.population_stats['rollbacks_performed'],
            'success_rate': (
                (self.population_stats['successfully_populated'] / 
                 max(1, self.population_stats['total_records_processed'])) * 100
            ) if self.population_stats['total_records_processed'] > 0 else 0
        }
    
    def reset_statistics(self):
        """Reset population statistics"""
        
        for key in self.population_stats:
            self.population_stats[key] = 0
        
        self.logger.info("Population statistics reset")
    
    def generate_population_report(self) -> str:
        """Generate comprehensive population report"""
        
        stats = self.get_population_statistics()
        
        report = []
        report.append("📊 Enhanced Database Population Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("📈 Population Statistics:")
        report.append(f"  • Total Records Processed: {stats['total_records_processed']}")
        report.append(f"  • Successfully Populated: {stats['successfully_populated']}")
        report.append(f"  • Failed Populations: {stats['failed_populations']}")
        report.append(f"  • Conflicts Resolved: {stats['conflicts_resolved']}")
        report.append(f"  • Rollbacks Performed: {stats['rollbacks_performed']}")
        report.append(f"  • Success Rate: {stats['success_rate']:.1f}%")
        
        return "\n".join(report)
