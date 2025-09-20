#!/usr/bin/env python3
"""
Bridge Domain Processing & Classification (BD-PROC) Pipeline

Implements the 7-phase BD-PROC pipeline as documented in:
- BD-PROC_FLOW.md
- BRIDGE_DOMAIN_PROCESSING_DETAILED.md

SINGLE RESPONSIBILITY: Process bridge domains through complete classification pipeline
INPUT: Raw bridge domain data, device types, LLDP data
OUTPUT: Fully processed bridge domains ready for consolidation
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.phase1_data_structures.enums import BridgeDomainType, InterfaceType, DeviceType
from config_engine.service_name_analyzer import ServiceNameAnalyzer

logger = logging.getLogger(__name__)

class ProcessingError(Exception):
    """Exception raised during BD-PROC processing"""
    pass

class DataQualityError(ProcessingError):
    """Exception raised when data quality validation fails"""
    pass

@dataclass
class ProcessingResult:
    """Result of BD-PROC processing for a single bridge domain"""
    success: bool
    bridge_domain: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_phase: str = "unknown"

@dataclass
class BDProcessingStats:
    """Statistics for BD-PROC processing session"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    phase1_errors: int = 0
    phase2_errors: int = 0
    phase3_errors: int = 0
    phase4_errors: int = 0
    phase5_errors: int = 0
    phase6_errors: int = 0
    phase7_errors: int = 0

class BridgeDomainProcessor:
    """
    Bridge Domain Processing & Classification (BD-PROC) Pipeline
    
    Implements the complete 7-phase processing pipeline as documented:
    1. Data Quality Validation
    2. DNAAS Type Classification  
    3. Global Identifier Extraction
    4. Username Extraction
    5. Device Type Classification
    6. Interface Role Assignment
    7. Consolidation Key Generation
    """
    
    def __init__(self):
        self.service_analyzer = ServiceNameAnalyzer()
        self.stats = BDProcessingStats()
        
        # Processing configuration
        self.strict_validation = True
        self.allow_partial_processing = True
        
        logger.info("🔧 BD-PROC Pipeline initialized")
    
    def process_bridge_domain(self, bridge_domain: Dict[str, Any], 
                            device_types_map: Dict[str, str], 
                            lldp_data: Dict[str, Any]) -> ProcessingResult:
        """
        Process a single bridge domain through the complete BD-PROC pipeline
        
        Args:
            bridge_domain: Raw bridge domain data
            device_types_map: Device type classifications
            lldp_data: LLDP neighbor information
            
        Returns:
            ProcessingResult with processed bridge domain or error details
        """
        self.stats.total_processed += 1
        
        try:
            # Phase 1: Data Quality Validation
            validated_bd = self._phase1_data_quality_validation(bridge_domain)
            
            # Phase 2: DNAAS Type Classification
            classified_bd = self._phase2_dnaas_type_classification(validated_bd)
            
            # Phase 3: Global Identifier Extraction
            global_id_bd = self._phase3_global_identifier_extraction(classified_bd)
            
            # Phase 4: Username Extraction
            username_bd = self._phase4_username_extraction(global_id_bd)
            
            # Phase 5: Device Type Classification
            device_type_bd = self._phase5_device_type_classification(username_bd, device_types_map)
            
            # Phase 6: Interface Role Assignment
            interface_bd = self._phase6_interface_role_assignment(device_type_bd, lldp_data)
            
            # Phase 7: Consolidation Key Generation
            final_bd = self._phase7_consolidation_key_generation(interface_bd)
            
            self.stats.successful += 1
            logger.debug(f"✅ BD-PROC completed for: {final_bd.get('name', 'unknown')}")
            
            return ProcessingResult(
                success=True,
                bridge_domain=final_bd,
                processing_phase="complete"
            )
            
        except DataQualityError as e:
            self.stats.failed += 1
            self.stats.phase1_errors += 1
            logger.error(f"❌ Phase 1 error for {bridge_domain.get('name', 'unknown')}: {e}")
            return ProcessingResult(
                success=False,
                errors=[f"Data quality validation failed: {e}"],
                processing_phase="phase1"
            )
            
        except ProcessingError as e:
            self.stats.failed += 1
            logger.error(f"❌ Processing error for {bridge_domain.get('name', 'unknown')}: {e}")
            return ProcessingResult(
                success=False,
                errors=[f"Processing failed: {e}"],
                processing_phase="unknown"
            )
            
        except Exception as e:
            self.stats.failed += 1
            logger.error(f"❌ Unexpected error for {bridge_domain.get('name', 'unknown')}: {e}")
            return ProcessingResult(
                success=False,
                errors=[f"Unexpected error: {e}"],
                processing_phase="unknown"
            )
    
    def _phase1_data_quality_validation(self, bridge_domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 1: Data Quality Validation
        
        Validates that bridge domain data meets minimum quality requirements
        """
        logger.debug(f"🔍 Phase 1: Data quality validation for {bridge_domain.get('name', 'unknown')}")
        
        # Required fields validation
        required_fields = ['name', 'interfaces', 'devices']
        missing_fields = [field for field in required_fields if not bridge_domain.get(field)]
        
        if missing_fields:
            raise DataQualityError(f"Missing required fields: {missing_fields}")
        
        # Name validation
        bd_name = bridge_domain['name']
        if not isinstance(bd_name, str) or not bd_name.strip():
            raise DataQualityError("Bridge domain name must be non-empty string")
        
        # Interfaces validation
        interfaces = bridge_domain['interfaces']
        if not isinstance(interfaces, list) or len(interfaces) == 0:
            raise DataQualityError("Bridge domain must have at least one interface")
        
        # Devices validation
        devices = bridge_domain['devices']
        if not isinstance(devices, list) or len(devices) == 0:
            raise DataQualityError("Bridge domain must have at least one device")
        
        # Interface format validation
        for interface in interfaces:
            if not isinstance(interface, str) or not interface.strip():
                raise DataQualityError(f"Invalid interface format: {interface}")
        
        # Device format validation
        for device in devices:
            if not isinstance(device, str) or not device.strip():
                raise DataQualityError(f"Invalid device format: {device}")
        
        # Add validation metadata
        validated_bd = bridge_domain.copy()
        validated_bd['_bd_proc_metadata'] = {
            'phase1_completed': True,
            'validation_timestamp': self._get_timestamp(),
            'data_quality_score': self._calculate_data_quality_score(bridge_domain)
        }
        
        logger.debug(f"✅ Phase 1 completed for {bd_name}")
        return validated_bd
    
    def _phase2_dnaas_type_classification(self, bridge_domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: DNAAS Type Classification
        
        Classifies bridge domain based on DNAAS configuration patterns
        """
        logger.debug(f"🔍 Phase 2: DNAAS type classification for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        
        # Initialize classification result
        classified_bd = bridge_domain.copy()
        classified_bd['_bd_proc_metadata']['phase2_completed'] = True
        
        # Type 1: Single VLAN (e.g., "vlan_100")
        if re.match(r'^vlan_\d+$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.SINGLE_TAGGED.value
            classified_bd['vlan_id'] = self._extract_vlan_from_name(bd_name)
            classified_bd['classification_confidence'] = 0.9
            
        # Type 2: QinQ (e.g., "qinq_100_200")
        elif re.match(r'^qinq_\d+_\d+$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.QINQ_SINGLE_BD.value
            outer_vlan, inner_vlan = self._extract_qinq_vlans(bd_name)
            classified_bd['outer_vlan'] = outer_vlan
            classified_bd['inner_vlan'] = inner_vlan
            classified_bd['classification_confidence'] = 0.9
            
        # Type 3: VLAN Range (e.g., "vlan_range_100_200")
        elif re.match(r'^vlan_range_\d+_\d+$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.SINGLE_TAGGED_RANGE.value
            start_vlan, end_vlan = self._extract_vlan_range(bd_name)
            classified_bd['vlan_range'] = f"{start_vlan}-{end_vlan}"
            classified_bd['classification_confidence'] = 0.8
            
        # Type 4A: VLAN List (e.g., "vlan_list_100_200_300")
        elif re.match(r'^vlan_list_\d+(?:_\d+)*$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.SINGLE_TAGGED_LIST.value
            vlan_list = self._extract_vlan_list(bd_name)
            classified_bd['vlan_list'] = vlan_list
            classified_bd['classification_confidence'] = 0.8
            
        # Type 4B: VLAN List with Outer VLAN (e.g., "qinq_list_100_200_300")
        elif re.match(r'^qinq_list_\d+(?:_\d+)*$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.QINQ_MULTI_BD.value
            outer_vlan, vlan_list = self._extract_qinq_list(bd_name)
            classified_bd['outer_vlan'] = outer_vlan
            classified_bd['vlan_list'] = vlan_list
            classified_bd['classification_confidence'] = 0.8
            
        # Type 5: Port-Mode (e.g., "port_mode_eth1")
        elif re.match(r'^port_mode_\w+$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.PORT_MODE.value
            port_name = self._extract_port_name(bd_name)
            classified_bd['port_name'] = port_name
            classified_bd['classification_confidence'] = 0.9
            
        # Service-based (e.g., "g_visaev_v251_to_Spirent") - classify as single tagged
        elif re.match(r'^g_\w+_v\d+_to_\w+$', bd_name.lower()):
            classified_bd['dnaas_type'] = BridgeDomainType.SINGLE_TAGGED.value
            service_info = self._extract_service_info(bd_name)
            classified_bd.update(service_info)
            classified_bd['classification_confidence'] = 0.7
            
        # Default: Unknown type
        else:
            classified_bd['dnaas_type'] = 'unknown'
            classified_bd['classification_confidence'] = 0.1
            logger.warning(f"⚠️ Unknown DNAAS type for: {bd_name}")
        
        logger.debug(f"✅ Phase 2 completed for {bd_name}: {classified_bd['dnaas_type']}")
        return classified_bd
    
    def _phase3_global_identifier_extraction(self, bridge_domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 3: Global Identifier Extraction
        
        Extracts global identifiers for consolidation purposes
        """
        logger.debug(f"🔍 Phase 3: Global identifier extraction for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        dnaas_type = bridge_domain.get('dnaas_type')
        
        global_id_bd = bridge_domain.copy()
        global_id_bd['_bd_proc_metadata']['phase3_completed'] = True
        
        # Initialize global identifier
        global_id_bd['global_identifier'] = None
        global_id_bd['consolidation_scope'] = 'local'
        
        if dnaas_type == BridgeDomainType.SINGLE_TAGGED.value:
            # Single VLAN: use VLAN ID as global identifier
            vlan_id = global_id_bd.get('vlan_id')
            if vlan_id:
                global_id_bd['global_identifier'] = f"vlan_{vlan_id}"
                global_id_bd['consolidation_scope'] = 'global'
                
        elif dnaas_type == BridgeDomainType.QINQ_SINGLE_BD.value:
            # QinQ: use outer VLAN as global identifier
            outer_vlan = global_id_bd.get('outer_vlan')
            if outer_vlan:
                global_id_bd['global_identifier'] = f"qinq_{outer_vlan}"
                global_id_bd['consolidation_scope'] = 'global'
                
        elif dnaas_type == BridgeDomainType.SINGLE_TAGGED_RANGE.value:
            # VLAN Range: local only (no global identifier)
            global_id_bd['consolidation_scope'] = 'local'
            
        elif dnaas_type == BridgeDomainType.SINGLE_TAGGED_LIST.value:
            # VLAN List: local only (no global identifier)
            global_id_bd['consolidation_scope'] = 'local'
            
        elif dnaas_type == BridgeDomainType.QINQ_MULTI_BD.value:
            # QinQ List: use outer VLAN if present
            outer_vlan = global_id_bd.get('outer_vlan')
            if outer_vlan:
                global_id_bd['global_identifier'] = f"qinq_{outer_vlan}"
                global_id_bd['consolidation_scope'] = 'global'
            else:
                global_id_bd['consolidation_scope'] = 'local'
                
        elif dnaas_type == BridgeDomainType.PORT_MODE.value:
            # Port-Mode: local only (no global identifier)
            global_id_bd['consolidation_scope'] = 'local'
            
        elif dnaas_type == BridgeDomainType.SINGLE_TAGGED.value and global_id_bd.get('service_name'):
            # Service-based: use service identifier
            service_name = global_id_bd.get('service_name')
            if service_name:
                global_id_bd['global_identifier'] = f"service_{service_name}"
                global_id_bd['consolidation_scope'] = 'global'
        
        logger.debug(f"✅ Phase 3 completed for {bd_name}: {global_id_bd['global_identifier']}")
        return global_id_bd
    
    def _phase4_username_extraction(self, bridge_domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: Username Extraction
        
        Extracts username from bridge domain name using service analyzer
        """
        logger.debug(f"🔍 Phase 4: Username extraction for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        
        username_bd = bridge_domain.copy()
        username_bd['_bd_proc_metadata']['phase4_completed'] = True
        
        try:
            # Use service analyzer to extract username
            service_info = self.service_analyzer.extract_service_info(bd_name)
            username_bd['username'] = service_info.get('username', 'unknown')
            username_bd['scope'] = service_info.get('scope', 'unknown')
            username_bd['confidence'] = service_info.get('confidence', 0.5)
            
        except Exception as e:
            logger.warning(f"⚠️ Username extraction failed for {bd_name}: {e}")
            username_bd['username'] = 'unknown'
            username_bd['scope'] = 'unknown'
            username_bd['confidence'] = 0.0
        
        logger.debug(f"✅ Phase 4 completed for {bd_name}: {username_bd['username']}")
        return username_bd
    
    def _phase5_device_type_classification(self, bridge_domain: Dict[str, Any], 
                                         device_types_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Phase 5: Device Type Classification
        
        Classifies device types for all devices in the bridge domain
        """
        logger.debug(f"🔍 Phase 5: Device type classification for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        devices = bridge_domain.get('devices', [])
        
        device_type_bd = bridge_domain.copy()
        device_type_bd['_bd_proc_metadata']['phase5_completed'] = True
        device_type_bd['device_types'] = {}
        
        for device in devices:
            # Get device type from provided map
            device_type = device_types_map.get(device, 'unknown')
            device_type_bd['device_types'][device] = device_type
            
            # Validate device type
            if device_type not in ['leaf', 'spine', 'superspine', 'unknown']:
                logger.warning(f"⚠️ Unknown device type '{device_type}' for device '{device}'")
                device_type_bd['device_types'][device] = 'unknown'
        
        # Determine primary device type (most common)
        device_type_counts = {}
        for device_type in device_type_bd['device_types'].values():
            device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1
        
        primary_device_type = max(device_type_counts.items(), key=lambda x: x[1])[0]
        device_type_bd['primary_device_type'] = primary_device_type
        
        logger.debug(f"✅ Phase 5 completed for {bd_name}: {device_type_bd['device_types']}")
        return device_type_bd
    
    def _phase6_interface_role_assignment(self, bridge_domain: Dict[str, Any], 
                                        lldp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 6: Interface Role Assignment
        
        Assigns interface roles based on LLDP data and device types
        """
        logger.debug(f"🔍 Phase 6: Interface role assignment for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        interfaces = bridge_domain.get('interfaces', [])
        device_types = bridge_domain.get('device_types', {})
        
        interface_bd = bridge_domain.copy()
        interface_bd['_bd_proc_metadata']['phase6_completed'] = True
        interface_bd['enhanced_interfaces'] = []
        
        for interface in interfaces:
            interface_info = {
                'name': interface,
                'role': 'unknown',
                'assignment_method': 'unknown',
                'confidence': 0.0
            }
            
            # Extract device from interface (assume first device for now)
            device = bridge_domain.get('devices', ['unknown'])[0]
            device_type = device_types.get(device, 'unknown')
            
            # Try LLDP-based assignment first
            try:
                role, method, confidence = self._assign_interface_role_from_lldp(
                    interface, device, device_type, lldp_data
                )
                interface_info['role'] = role
                interface_info['assignment_method'] = method
                interface_info['confidence'] = confidence
                
            except Exception as e:
                logger.debug(f"LLDP assignment failed for {interface}: {e}")
                
                # Fallback to pattern-based assignment
                try:
                    role, method, confidence = self._assign_interface_role_from_pattern(
                        interface, device_type
                    )
                    interface_info['role'] = role
                    interface_info['assignment_method'] = method
                    interface_info['confidence'] = confidence
                    
                except Exception as e:
                    logger.warning(f"Pattern assignment failed for {interface}: {e}")
                    interface_info['role'] = 'unknown'
                    interface_info['assignment_method'] = 'failed'
                    interface_info['confidence'] = 0.0
            
            interface_bd['enhanced_interfaces'].append(interface_info)
        
        logger.debug(f"✅ Phase 6 completed for {bd_name}: {len(interface_bd['enhanced_interfaces'])} interfaces")
        return interface_bd
    
    def _phase7_consolidation_key_generation(self, bridge_domain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 7: Consolidation Key Generation
        
        Generates consolidation key for grouping bridge domains
        """
        logger.debug(f"🔍 Phase 7: Consolidation key generation for {bridge_domain.get('name', 'unknown')}")
        
        bd_name = bridge_domain['name']
        global_identifier = bridge_domain.get('global_identifier')
        username = bridge_domain.get('username', 'unknown')
        consolidation_scope = bridge_domain.get('consolidation_scope', 'local')
        
        final_bd = bridge_domain.copy()
        final_bd['_bd_proc_metadata']['phase7_completed'] = True
        
        # Generate consolidation key
        if consolidation_scope == 'global' and global_identifier:
            # Global consolidation: use global identifier + username
            consolidation_key = f"{global_identifier}_{username}"
        else:
            # Local consolidation: use bridge domain name
            consolidation_key = bd_name
        
        final_bd['consolidation_key'] = consolidation_key
        final_bd['consolidation_scope'] = consolidation_scope
        
        # Generate service signature for deduplication
        service_signature = self._generate_service_signature(final_bd)
        final_bd['service_signature'] = service_signature
        
        logger.debug(f"✅ Phase 7 completed for {bd_name}: {consolidation_key}")
        return final_bd
    
    # Helper methods for phase implementations
    
    def _extract_vlan_from_name(self, bd_name: str) -> Optional[int]:
        """Extract VLAN ID from bridge domain name"""
        match = re.search(r'vlan_(\d+)', bd_name.lower())
        return int(match.group(1)) if match else None
    
    def _extract_qinq_vlans(self, bd_name: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract outer and inner VLANs from QinQ name"""
        match = re.search(r'qinq_(\d+)_(\d+)', bd_name.lower())
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None
    
    def _extract_vlan_range(self, bd_name: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract VLAN range from bridge domain name"""
        match = re.search(r'vlan_range_(\d+)_(\d+)', bd_name.lower())
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None
    
    def _extract_vlan_list(self, bd_name: str) -> List[int]:
        """Extract VLAN list from bridge domain name"""
        match = re.search(r'vlan_list_((?:\d+_?)+)', bd_name.lower())
        if match:
            return [int(x) for x in match.group(1).split('_')]
        return []
    
    def _extract_qinq_list(self, bd_name: str) -> Tuple[Optional[int], List[int]]:
        """Extract outer VLAN and inner VLAN list from QinQ list name"""
        match = re.search(r'qinq_list_(\d+)_((?:\d+_?)+)', bd_name.lower())
        if match:
            outer_vlan = int(match.group(1))
            inner_vlans = [int(x) for x in match.group(2).split('_')]
            return outer_vlan, inner_vlans
        return None, []
    
    def _extract_port_name(self, bd_name: str) -> Optional[str]:
        """Extract port name from port-mode bridge domain name"""
        match = re.search(r'port_mode_(\w+)', bd_name.lower())
        return match.group(1) if match else None
    
    def _extract_service_info(self, bd_name: str) -> Dict[str, Any]:
        """Extract service information from service-based bridge domain name"""
        match = re.search(r'g_(\w+)_v(\d+)_to_(\w+)', bd_name.lower())
        if match:
            return {
                'service_name': match.group(1),
                'vlan_id': int(match.group(2)),
                'destination': match.group(3)
            }
        return {}
    
    def _assign_interface_role_from_lldp(self, interface: str, device: str, 
                                       device_type: str, lldp_data: Dict[str, Any]) -> Tuple[str, str, float]:
        """Assign interface role using LLDP data"""
        # This is a placeholder - will be implemented with full LLDP logic
        # For now, return pattern-based assignment
        return self._assign_interface_role_from_pattern(interface, device_type)
    
    def _assign_interface_role_from_pattern(self, interface: str, device_type: str) -> Tuple[str, str, float]:
        """Assign interface role using pattern matching"""
        interface_lower = interface.lower()
        
        # Bundle interfaces
        if 'bundle' in interface_lower:
            if device_type == 'leaf':
                return 'uplink', 'pattern_bundle_leaf', 0.8
            elif device_type == 'spine':
                return 'downlink', 'pattern_bundle_spine', 0.8
            else:
                return 'transport', 'pattern_bundle_other', 0.6
        
        # Physical interfaces
        elif re.match(r'eth\d+', interface_lower):
            if device_type == 'leaf':
                return 'access', 'pattern_physical_leaf', 0.9
            else:
                return 'transport', 'pattern_physical_other', 0.7
        
        # Subinterfaces
        elif '.' in interface:
            if device_type == 'leaf':
                return 'access', 'pattern_subinterface_leaf', 0.8
            else:
                return 'transport', 'pattern_subinterface_other', 0.6
        
        # Default
        else:
            return 'unknown', 'pattern_default', 0.1
    
    def _generate_service_signature(self, bridge_domain: Dict[str, Any]) -> str:
        """Generate service signature for deduplication"""
        name = bridge_domain.get('name', '')
        global_id = bridge_domain.get('global_identifier', '')
        username = bridge_domain.get('username', '')
        
        return f"{name}|{global_id}|{username}"
    
    def _calculate_data_quality_score(self, bridge_domain: Dict[str, Any]) -> float:
        """Calculate data quality score for bridge domain"""
        score = 0.0
        
        # Name quality
        if bridge_domain.get('name'):
            score += 0.2
        
        # Interface quality
        interfaces = bridge_domain.get('interfaces', [])
        if interfaces:
            score += 0.3
            if len(interfaces) > 1:
                score += 0.1
        
        # Device quality
        devices = bridge_domain.get('devices', [])
        if devices:
            score += 0.3
            if len(devices) > 1:
                score += 0.1
        
        return min(score, 1.0)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_processing_stats(self) -> BDProcessingStats:
        """Get current processing statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.stats = BDProcessingStats()
        logger.info("📊 BD-PROC statistics reset")

# Convenience function for easy usage
def process_bridge_domain(bridge_domain: Dict[str, Any], 
                         device_types_map: Dict[str, str], 
                         lldp_data: Dict[str, Any]) -> ProcessingResult:
    """
    Convenience function to process a single bridge domain
    
    Args:
        bridge_domain: Raw bridge domain data
        device_types_map: Device type classifications
        lldp_data: LLDP neighbor information
        
    Returns:
        ProcessingResult with processed bridge domain or error details
    """
    processor = BridgeDomainProcessor()
    return processor.process_bridge_domain(bridge_domain, device_types_map, lldp_data)

if __name__ == "__main__":
    # Test the BD-PROC pipeline
    logging.basicConfig(level=logging.DEBUG)
    
    # Sample test data
    test_bd = {
        'name': 'g_visaev_v251_to_Spirent',
        'interfaces': ['bundle-60000.251'],
        'devices': ['DNAAS-LEAF-01']
    }
    
    test_device_types = {
        'DNAAS-LEAF-01': 'leaf'
    }
    
    test_lldp_data = {}
    
    # Process the bridge domain
    processor = BridgeDomainProcessor()
    result = processor.process_bridge_domain(test_bd, test_device_types, test_lldp_data)
    
    print(f"Processing result: {result.success}")
    if result.success:
        print(f"Processed BD: {result.bridge_domain}")
    else:
        print(f"Errors: {result.errors}")
