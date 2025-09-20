#!/usr/bin/env python3
"""
Simplified Bridge Domain Discovery System
========================================

Implementation of the 3-Step Simplified Workflow for bridge domain discovery.
This system addresses all the logic flaws identified in the architectural analysis
by providing a clear, consistent, and maintainable approach.

Architecture: 3-Step Simplified Workflow (ADR-001)

Step 1: Load and Validate Data
Step 2: Process Bridge Domains (BD-PROC Pipeline)  
Step 3: Consolidate and Save Results
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our standardized data structures
from config_engine.simplified_discovery.data_structures import (
    # Step 1 structures
    RawBridgeDomain, ValidationResult, LoadedData,
    
    # Step 2 structures  
    VLANConfiguration, InterfaceInfo, ProcessedBridgeDomain,
    
    # Step 3 structures
    ConsolidationGroup, ConsolidatedBridgeDomain, DiscoveryResults,
    
    # Error handling
    DiscoveryError, DataQualityError, ClassificationError, ConsolidationError,
    
    # Validation helpers
    validate_data_flow_step1_to_step2, validate_data_flow_step2_to_step3
)

# Import existing components we'll reuse
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, DeviceType, ValidationStatus, BridgeDomainScope
)

logger = logging.getLogger(__name__)


class SimplifiedBridgeDomainDiscovery:
    """
    Simplified Bridge Domain Discovery System
    
    Implements the 3-step workflow with proper guided rails to prevent
    the architectural logic flaws identified in the analysis.
    """
    
    def __init__(self, config_dir: str = "topology/configs/parsed_data"):
        """
        Initialize the simplified discovery system
        
        Args:
            config_dir: Directory containing parsed configuration data
        """
        self.config_dir = Path(config_dir)
        self.bridge_domain_parsed_dir = self.config_dir / "bridge_domain_parsed"
        self.lldp_data_dir = Path("topology/lldp_data")
        
        # Processing statistics
        self.stats = {
            'total_discovered': 0,
            'total_processed': 0, 
            'total_consolidated': 0,
            'total_errors': 0,
            'processing_time': 0.0
        }
        
        # Guided rails: Ensure directories exist
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate that required directories and files exist"""
        if not self.bridge_domain_parsed_dir.exists():
            raise DiscoveryError(f"Bridge domain parsed directory not found: {self.bridge_domain_parsed_dir}")
        
        logger.info(f"✅ Environment validated - using config dir: {self.config_dir}")
    
    # =========================================================================
    # MAIN 3-STEP WORKFLOW
    # =========================================================================
    
    def discover_all_bridge_domains(self) -> DiscoveryResults:
        """
        Main entry point for the 3-step simplified workflow
        
        Returns:
            Complete discovery results with all bridge domains and statistics
        """
        logger.info("🚀 Starting Simplified Bridge Domain Discovery (3-Step Workflow)")
        start_time = datetime.now()
        
        try:
            # Step 1: Load and validate data
            logger.info("📋 Step 1: Loading and validating data...")
            loaded_data = self._step1_load_and_validate_data()
            
            # Guided rail: Validate data flow between steps
            step1_validation = validate_data_flow_step1_to_step2(loaded_data)
            if not step1_validation.is_valid:
                raise DataQualityError(f"Step 1 to Step 2 validation failed: {step1_validation.errors}")
            
            # Step 2: Process each bridge domain (BD-PROC Pipeline)
            logger.info("🔄 Step 2: Processing bridge domains (BD-PROC Pipeline)...")
            processed_bds = self._step2_process_bridge_domains(loaded_data)
            
            # Guided rail: Validate data flow between steps
            step2_validation = validate_data_flow_step2_to_step3(processed_bds)
            if not step2_validation.is_valid:
                raise ConsolidationError(f"Step 2 to Step 3 validation failed: {step2_validation.errors}")
            
            # Step 3: Consolidate and save results
            logger.info("🎯 Step 3: Consolidating and saving results...")
            final_results = self._step3_consolidate_and_save(processed_bds)
            
            # Finalize results and statistics
            final_results.finalize_results()
            
            # Update internal statistics
            self.stats['total_discovered'] = final_results.total_bridge_domains_discovered
            self.stats['total_processed'] = final_results.total_bridge_domains_processed
            self.stats['total_consolidated'] = final_results.total_bridge_domains_consolidated
            self.stats['total_errors'] = final_results.total_errors
            self.stats['processing_time'] = final_results.total_processing_time or 0.0
            
            logger.info("🎉 Simplified Bridge Domain Discovery completed successfully!")
            logger.info(f"📊 Results: {len(final_results.consolidated_bridge_domains)} consolidated, "
                       f"{len(final_results.individual_bridge_domains)} individual")
            logger.info(f"⏱️ Processing time: {final_results.total_processing_time:.2f} seconds")
            logger.info(f"✅ Success rate: {final_results.success_rate:.1%}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            # Return partial results if possible
            return self._create_error_results(str(e), start_time)
    
    # =========================================================================
    # STEP 1: LOAD AND VALIDATE DATA
    # =========================================================================
    
    def _step1_load_and_validate_data(self) -> LoadedData:
        """
        Step 1: Load and validate all required data
        
        Returns:
            LoadedData containing all validated data for Step 2
        """
        logger.info("🔍 Loading bridge domain data...")
        
        # Load bridge domains from parsed data
        bridge_domains = self._load_bridge_domains()
        logger.info(f"✅ Loaded {len(bridge_domains)} bridge domains")
        
        # Load device type data
        device_types = self._load_device_types(bridge_domains)
        logger.info(f"✅ Loaded device types for {len(device_types)} devices")
        
        # Load LLDP data
        lldp_data = self._load_lldp_data(bridge_domains)
        logger.info(f"✅ Loaded LLDP data for {len(lldp_data)} devices")
        
        # Validate data quality
        validation_results = self._validate_loaded_data(bridge_domains)
        
        # Create LoadedData structure
        loaded_data = LoadedData(
            bridge_domains=bridge_domains,
            device_types=device_types,
            lldp_data=lldp_data,
            validation_results=validation_results
        )
        
        logger.info(f"📊 Step 1 complete: {loaded_data.total_devices} devices, "
                   f"{loaded_data.total_interfaces} interfaces")
        
        return loaded_data
    
    def _load_bridge_domains(self) -> List[RawBridgeDomain]:
        """Load bridge domains from parsed configuration files and aggregate by name"""
        
        # First, collect all bridge domain instances from all devices
        all_bd_instances = {}  # bd_name -> list of (device_name, bd_instance, source_file)
        
        # Look for parsed bridge domain files (YAML format)
        for bd_file in self.bridge_domain_parsed_dir.glob("*bridge_domain_instance_parsed*.yaml"):
            try:
                import yaml
                with open(bd_file, 'r') as f:
                    bd_data = yaml.safe_load(f) or {}
                
                # Extract device name from filename
                device_name = bd_file.stem.split('_bridge_domain_instance_parsed')[0]
                
                # Load corresponding VLAN configuration file (flexible timestamp matching)
                vlan_configs = {}
                
                # Try exact timestamp match first
                exact_timestamp = bd_data.get('timestamp', '20250901_174145')
                vlan_config_file = bd_file.parent / f"{device_name}_vlan_config_parsed_{exact_timestamp}.yaml"
                
                # If exact match fails, find any VLAN config file for this device
                if not vlan_config_file.exists():
                    vlan_files = list(bd_file.parent.glob(f"{device_name}_vlan_config_parsed_*.yaml"))
                    if vlan_files:
                        vlan_config_file = vlan_files[0]  # Use the first available
                
                if vlan_config_file.exists():
                    with open(vlan_config_file, 'r') as f:
                        vlan_data = yaml.safe_load(f) or {}
                        # Index VLAN configs by interface name for quick lookup
                        for vlan_config in vlan_data.get('vlan_configurations', []):
                            interface_name = vlan_config.get('interface')
                            if interface_name:
                                vlan_configs[interface_name] = vlan_config
                
                # Process each bridge domain instance in the file
                bridge_domain_instances = bd_data.get('bridge_domain_instances', [])
                
                for bd_instance in bridge_domain_instances:
                    bd_name = bd_instance.get('name')
                    if not bd_name:
                        continue
                    
                    # Group by bridge domain name across all devices
                    if bd_name not in all_bd_instances:
                        all_bd_instances[bd_name] = []
                    
                    all_bd_instances[bd_name].append({
                        'device_name': device_name,
                        'bd_instance': bd_instance,
                        'vlan_configs': vlan_configs,  # Add VLAN config data
                        'source_file': str(bd_file)
                    })
                    
            except Exception as e:
                logger.error(f"Failed to load bridge domain from {bd_file}: {e}")
                continue
        
        # Now aggregate bridge domains by name
        bridge_domains = []
        
        for bd_name, device_instances in all_bd_instances.items():
            # Aggregate all devices and interfaces for this bridge domain
            all_devices = []
            all_interfaces = []
            all_source_files = []
            
            for device_data in device_instances:
                device_name = device_data['device_name']
                bd_instance = device_data['bd_instance']
                vlan_configs = device_data['vlan_configs']
                source_file = device_data['source_file']
                
                all_devices.append(device_name)
                all_source_files.append(source_file)
                
                # Add interfaces with device context and ACTUAL VLAN configuration
                for interface_name in bd_instance.get('interfaces', []):
                    # Get actual VLAN configuration from CLI data
                    vlan_config = vlan_configs.get(interface_name, {})
                    
                    interface_data = {
                        'interface': interface_name,
                        'device': device_name,
                        'admin_state': bd_instance.get('admin_state', 'enabled'),
                        'source_bd_name': bd_name,
                        # ADD ACTUAL CLI CONFIGURATION DATA
                        'vlan_id': vlan_config.get('vlan_id'),
                        'outer_vlan': vlan_config.get('outer_vlan'),
                        'inner_vlan': vlan_config.get('inner_vlan'),
                        'vlan_type': vlan_config.get('type'),
                        'raw_config': vlan_config.get('raw_config', []),
                        'l2_service': vlan_config.get('l2_service', False)
                    }
                    all_interfaces.append(interface_data)
            
            # Remove duplicate devices while preserving order
            unique_devices = list(dict.fromkeys(all_devices))
            unique_source_files = list(dict.fromkeys(all_source_files))
            
            # Only create bridge domain if it has interfaces
            if all_interfaces:
                # Convert to RawBridgeDomain structure
                raw_bd = RawBridgeDomain(
                    name=bd_name,
                    devices=unique_devices,
                    interfaces=all_interfaces,
                    raw_config={'aggregated_from_devices': len(device_instances)},
                    source_files=unique_source_files
                )
                
                bridge_domains.append(raw_bd)
        
        self.stats['total_discovered'] = len(bridge_domains)
        return bridge_domains
    
    def _classify_bridge_domain_type(self, cbd: ConsolidatedBridgeDomain) -> Dict[str, Any]:
        """Classify bridge domain type based on VLAN configuration and topology"""
        
        # Analyze VLAN configurations across all interfaces
        vlan_analysis = self._analyze_vlan_configurations(cbd.all_interfaces)
        
        # Determine DNAAS type based on VLAN patterns
        dnaas_type = self._determine_dnaas_type(vlan_analysis)
        
        # Analyze encapsulation
        encapsulation = self._determine_encapsulation(vlan_analysis)
        
        # Determine service type
        service_type = self._determine_service_type(cbd, vlan_analysis)
        
        return {
            "dnaas_type": dnaas_type,
            "encapsulation": encapsulation,
            "service_type": service_type,
            "vlan_analysis": vlan_analysis,
            "qinq_detected": vlan_analysis.get("has_qinq", False),
            "vlan_manipulation_detected": vlan_analysis.get("has_vlan_manipulation", False),
            "interface_types": vlan_analysis.get("interface_types", {}),
            "vlan_consistency": vlan_analysis.get("consistency_score", 1.0)
        }
    
    def _classify_bridge_domain_type_individual(self, ibd: ProcessedBridgeDomain) -> Dict[str, Any]:
        """Classify individual bridge domain type"""
        
        # Analyze VLAN configurations
        vlan_analysis = self._analyze_vlan_configurations(ibd.interfaces)
        
        # Determine DNAAS type
        dnaas_type = self._determine_dnaas_type(vlan_analysis)
        
        # Analyze encapsulation
        encapsulation = self._determine_encapsulation(vlan_analysis)
        
        # Determine service type
        service_type = self._determine_service_type_individual(ibd, vlan_analysis)
        
        return {
            "dnaas_type": dnaas_type,
            "encapsulation": encapsulation,
            "service_type": service_type,
            "vlan_analysis": vlan_analysis,
            "qinq_detected": vlan_analysis.get("has_qinq", False),
            "vlan_manipulation_detected": vlan_analysis.get("has_vlan_manipulation", False),
            "interface_types": vlan_analysis.get("interface_types", {}),
            "vlan_consistency": vlan_analysis.get("consistency_score", 1.0)
        }
    
    def _analyze_vlan_configurations(self, interfaces: List[InterfaceInfo]) -> Dict[str, Any]:
        """Analyze VLAN configurations across interfaces to determine patterns"""
        
        analysis = {
            "total_interfaces": len(interfaces),
            "vlan_ids": set(),
            "outer_vlans": set(),
            "inner_vlans": set(),
            "has_qinq": False,
            "has_vlan_manipulation": False,
            "interface_types": {},
            "consistency_score": 1.0
        }
        
        for interface in interfaces:
            # Collect VLAN IDs
            if interface.vlan_config.vlan_id:
                analysis["vlan_ids"].add(interface.vlan_config.vlan_id)
            if interface.vlan_config.outer_vlan:
                analysis["outer_vlans"].add(interface.vlan_config.outer_vlan)
            if interface.vlan_config.inner_vlan:
                analysis["inner_vlans"].add(interface.vlan_config.inner_vlan)
            
            # Detect QinQ
            if interface.vlan_config.outer_vlan and interface.vlan_config.inner_vlan:
                analysis["has_qinq"] = True
            
            # Detect VLAN manipulation
            if interface.vlan_config.has_vlan_manipulation():
                analysis["has_vlan_manipulation"] = True
            
            # Count interface types
            iface_type = interface.interface_type
            analysis["interface_types"][iface_type] = analysis["interface_types"].get(iface_type, 0) + 1
        
        # Convert sets to lists for JSON serialization
        analysis["vlan_ids"] = sorted(list(analysis["vlan_ids"]))
        analysis["outer_vlans"] = sorted(list(analysis["outer_vlans"]))
        analysis["inner_vlans"] = sorted(list(analysis["inner_vlans"]))
        
        return analysis
    
    def _determine_dnaas_type(self, vlan_analysis: Dict[str, Any]) -> str:
        """Determine DNAAS type based on VLAN analysis"""
        
        has_qinq = vlan_analysis.get("has_qinq", False)
        vlan_ids = vlan_analysis.get("vlan_ids", [])
        outer_vlans = vlan_analysis.get("outer_vlans", [])
        inner_vlans = vlan_analysis.get("inner_vlans", [])
        
        if has_qinq:
            if len(outer_vlans) == 1 and len(inner_vlans) > 1:
                return "DNAAS_TYPE_4_QINQ_MULTI_BD"  # Multiple BDs under one service VLAN
            elif len(outer_vlans) == 1 and len(inner_vlans) == 1:
                return "DNAAS_TYPE_3_QINQ_SINGLE_BD"  # Single BD with QinQ
            else:
                return "DNAAS_TYPE_5_QINQ_COMPLEX"  # Complex QinQ configuration
        
        elif len(vlan_ids) == 1:
            return "DNAAS_TYPE_1_SINGLE_TAGGED"  # Standard single-tagged
        
        elif len(vlan_ids) > 1:
            return "DNAAS_TYPE_2_MULTI_TAGGED"  # Multiple VLANs in one BD
        
        else:
            return "DNAAS_TYPE_UNTAGGED"  # Untagged/unknown
    
    def _determine_encapsulation(self, vlan_analysis: Dict[str, Any]) -> str:
        """Determine encapsulation type"""
        
        if vlan_analysis.get("has_qinq", False):
            return "qinq"
        elif vlan_analysis.get("vlan_ids"):
            return "dot1q"
        else:
            return "untagged"
    
    def _determine_service_type(self, cbd: ConsolidatedBridgeDomain, vlan_analysis: Dict[str, Any]) -> str:
        """Determine service type for consolidated bridge domain"""
        
        interface_count = vlan_analysis.get("total_interfaces", 0)
        device_count = len(set(iface.device_name for iface in cbd.all_interfaces))
        
        if device_count == 1:
            return "local_switching"
        elif interface_count == 2 and device_count == 2:
            return "p2p_service"
        elif interface_count > 2:
            return "p2mp_broadcast_domain"
        else:
            return "unknown_service"
    
    def _determine_service_type_individual(self, ibd: ProcessedBridgeDomain, vlan_analysis: Dict[str, Any]) -> str:
        """Determine service type for individual bridge domain"""
        
        interface_count = vlan_analysis.get("total_interfaces", 0)
        device_count = len(set(iface.device_name for iface in ibd.interfaces))
        
        if device_count == 1:
            return "local_switching"
        elif interface_count == 2 and device_count == 2:
            return "p2p_service"
        elif interface_count > 2:
            return "p2mp_broadcast_domain"
        else:
            return "unknown_service"
    
    def _clean_raw_config(self, raw_config: List[str]) -> List[str]:
        """Clean raw CLI configuration by removing ANSI escape codes and formatting"""
        import re
        
        cleaned_config = []
        for config_line in raw_config:
            if isinstance(config_line, str):
                # Remove ANSI escape codes (color codes)
                cleaned_line = re.sub(r'\x1b\[[0-9;]*m', '', config_line)
                
                # Remove device prompts and extra whitespace
                cleaned_line = re.sub(r'^[A-Z0-9_-]+#\s*', '', cleaned_line.strip())
                
                # Only add non-empty lines
                if cleaned_line:
                    cleaned_config.append(cleaned_line)
        
        return cleaned_config
    
    def _select_primary_bridge_domain_name(self, bridge_domain_names: List[str]) -> str:
        """Select the best standard-format name to represent consolidated group"""
        import re
        
        def score_name(name):
            score = 0
            
            # STRONGLY prefer standard format: g_user_v123 or l_user_v123
            if re.match(r'^[gl]_\w+_v\d+$', name):
                score += 20  # Highest priority for clean standard format
            
            # Prefer global scope over local
            if name.startswith('g_'):
                score += 10
            elif name.startswith('l_'):
                score += 5
            
            # PREFER shorter names (less verbose)
            score -= len(name.split('_'))  # Subtract for longer names
            
            # Slight preference for names without extra descriptions
            if not any(desc in name.lower() for desc in ['to_', '_wan', '_test', '_spirent', '_ixia']):
                score += 3  # Bonus for clean, simple names
            
            return score
        
        # Return highest scoring name (clean, standard format preferred)
        return max(bridge_domain_names, key=score_name)
    
    def _extract_vlan_from_interface_name(self, interface_name: str) -> Optional[int]:
        """Extract VLAN ID from interface name (e.g., bundle-60000.998 → 998)"""
        try:
            if '.' in interface_name:
                vlan_part = interface_name.split('.')[-1]
                return int(vlan_part)
        except (ValueError, IndexError):
            pass
        return None
    
    def _extract_vlan_from_bridge_domain_name(self, bd_name: str) -> Optional[int]:
        """Extract VLAN ID from bridge domain name (e.g., g_visaev_v251 → 251)"""
        try:
            # Look for _v{number} pattern
            import re
            match = re.search(r'_v(\d+)', bd_name)
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass
        return None
    
    def _load_device_types(self, bridge_domains: List[RawBridgeDomain]) -> Dict[str, DeviceType]:
        """Load and classify device types from bridge domain data"""
        device_types = {}
        
        # Collect all unique devices
        all_devices = set()
        for bd in bridge_domains:
            all_devices.update(bd.devices)
        
        # Classify each device by name pattern
        for device_name in all_devices:
            device_type = self._classify_device_by_name(device_name)
            device_types[device_name] = device_type
        
        return device_types
    
    def _classify_device_by_name(self, device_name: str) -> DeviceType:
        """Classify device type based on naming patterns"""
        device_lower = device_name.lower()
        
        if 'superspine' in device_lower:
            return DeviceType.SUPERSPINE
        elif 'spine' in device_lower:
            return DeviceType.SPINE
        elif 'leaf' in device_lower:
            return DeviceType.LEAF
        else:
            # Default to LEAF for unknown devices
            logger.warning(f"Unknown device type for {device_name}, defaulting to LEAF")
            return DeviceType.LEAF
    
    def _load_lldp_data(self, bridge_domains: List[RawBridgeDomain]) -> Dict[str, Dict[str, Any]]:
        """Load LLDP neighbor data for devices"""
        lldp_data = {}
        
        # Collect all unique devices
        all_devices = set()
        for bd in bridge_domains:
            all_devices.update(bd.devices)
        
        # Try to load LLDP data for each device
        for device_name in all_devices:
            lldp_file = self.lldp_data_dir / f"{device_name}_lldp.yaml"
            
            if lldp_file.exists():
                try:
                    import yaml
                    with open(lldp_file, 'r') as f:
                        device_lldp = yaml.safe_load(f) or {}
                    lldp_data[device_name] = device_lldp
                except Exception as e:
                    logger.warning(f"Failed to load LLDP data for {device_name}: {e}")
                    lldp_data[device_name] = {}
            else:
                logger.debug(f"No LLDP data file found for {device_name}")
                lldp_data[device_name] = {}
        
        return lldp_data
    
    def _validate_loaded_data(self, bridge_domains: List[RawBridgeDomain]) -> Dict[str, ValidationResult]:
        """Validate loaded bridge domain data quality"""
        validation_results = {}
        
        for bd in bridge_domains:
            result = ValidationResult(is_valid=True)
            
            # Validate required fields
            if not bd.name:
                result.add_error("Missing bridge domain name")
            
            if not bd.devices:
                result.add_error("No devices found")
            
            if not bd.interfaces:
                result.add_error("No interfaces found")
            
            # Validate VLAN configuration quality
            vlan_configs_found = 0
            for interface in bd.interfaces:
                if any(key in interface for key in ['vlan_id', 'outer_vlan', 'inner_vlan', 'vlan_range']):
                    vlan_configs_found += 1
            
            if vlan_configs_found == 0:
                result.add_error("No VLAN configurations found in any interface")
            elif vlan_configs_found < len(bd.interfaces) * 0.5:
                result.add_warning("Less than 50% of interfaces have VLAN configuration")
            
            validation_results[bd.name] = result
        
        return validation_results
    
    # =========================================================================
    # STEP 2: PROCESS BRIDGE DOMAINS (BD-PROC PIPELINE)
    # =========================================================================
    
    def _step2_process_bridge_domains(self, loaded_data: LoadedData) -> List[ProcessedBridgeDomain]:
        """
        Step 2: Process each bridge domain through the BD-PROC pipeline
        
        Args:
            loaded_data: Validated data from Step 1
            
        Returns:
            List of processed bridge domains ready for consolidation
        """
        processed_bds = []
        
        for bd in loaded_data.bridge_domains:
            try:
                # Run BD-PROC pipeline for this bridge domain
                processed_bd = self._bd_proc_pipeline(bd, loaded_data.device_types, loaded_data.lldp_data)
                processed_bds.append(processed_bd)
                
            except Exception as e:
                logger.error(f"BD-PROC pipeline failed for {bd.name}: {e}")
                # Create error bridge domain to track the failure
                error_bd = self._create_error_bridge_domain(bd, str(e))
                processed_bds.append(error_bd)
                continue
        
        self.stats['total_processed'] = len([bd for bd in processed_bds 
                                           if bd.validation_status != ValidationStatus.INVALID])
        
        logger.info(f"🔄 BD-PROC pipeline complete: {len(processed_bds)} bridge domains processed")
        return processed_bds
    
    def _bd_proc_pipeline(self, bd: RawBridgeDomain, device_types: Dict[str, DeviceType], 
                         lldp_data: Dict[str, Dict[str, Any]]) -> ProcessedBridgeDomain:
        """
        Complete BD-PROC pipeline for a single bridge domain
        
        Phases:
        1. Data Quality Validation
        2. DNAAS Type Classification
        3. Global Identifier Extraction
        4. Username Extraction
        5. Device Type Classification
        6. Interface Role Assignment
        7. Consolidation Key Generation
        """
        
        # Phase 1: Data Quality Validation
        validated_bd = self._bd_proc_phase1_validation(bd)
        
        # Phase 2: DNAAS Type Classification
        classified_bd = self._bd_proc_phase2_classification(validated_bd)
        
        # Phase 3: Global Identifier Extraction
        global_id_bd = self._bd_proc_phase3_global_identifier(classified_bd)
        
        # Phase 4: Username Extraction
        username_bd = self._bd_proc_phase4_username(global_id_bd)
        
        # Phase 5: Device Type Classification
        device_type_bd = self._bd_proc_phase5_devices(username_bd, device_types)
        
        # Phase 6: Interface Role Assignment
        interface_bd = self._bd_proc_phase6_interfaces(device_type_bd, lldp_data)
        
        # Phase 7: Consolidation Key Generation
        final_bd = self._bd_proc_phase7_consolidation_key(interface_bd)
        
        return final_bd
    
    def _bd_proc_phase1_validation(self, bd: RawBridgeDomain) -> ProcessedBridgeDomain:
        """Phase 1: Data Quality Validation"""
        
        # Create initial ProcessedBridgeDomain
        processed_bd = ProcessedBridgeDomain(
            name=bd.name,
            devices=bd.devices.copy(),
            interfaces=[],  # Will be populated in later phases
            bridge_domain_type=BridgeDomainType.SINGLE_VLAN,  # Default, will be classified
            processing_phase="phase1_validation"
        )
        
        # Validate required data
        if not bd.name:
            processed_bd.add_processing_error("Missing bridge domain name")
        
        if not bd.devices:
            processed_bd.add_processing_error("No devices found")
        
        if not bd.interfaces:
            processed_bd.add_processing_error("No interfaces found")
        
        # Convert raw interfaces to structured format
        for interface_data in bd.interfaces:
            try:
                vlan_config = self._extract_vlan_configuration(interface_data)
                interface_info = InterfaceInfo(
                    name=interface_data.get('interface', 'unknown'),
                    device_name=interface_data.get('device', 'unknown'),
                    vlan_config=vlan_config,
                    raw_config=self._clean_raw_config(interface_data.get('raw_config', []))  # Clean and add raw CLI configuration
                )
                processed_bd.interfaces.append(interface_info)
            except Exception as e:
                processed_bd.add_processing_warning(f"Failed to process interface {interface_data}: {e}")
        
        if not processed_bd.interfaces:
            processed_bd.add_processing_error("No valid interfaces after processing")
        
        return processed_bd
    
    def _extract_vlan_configuration(self, interface_data: Dict[str, Any]) -> VLANConfiguration:
        """Extract VLAN configuration from interface data - ONLY from actual config, not names"""
        
        return VLANConfiguration(
            vlan_id=interface_data.get('vlan_id'),  # Only from actual config
            outer_vlan=interface_data.get('outer_vlan'),  # Only from actual config
            inner_vlan=interface_data.get('inner_vlan'),
            vlan_range_start=interface_data.get('vlan_range_start'),
            vlan_range_end=interface_data.get('vlan_range_end'),
            vlan_list=interface_data.get('vlan_list', []),
            vlan_manipulation=interface_data.get('vlan_manipulation')
        )
    
    def _bd_proc_phase2_classification(self, bd: ProcessedBridgeDomain) -> ProcessedBridgeDomain:
        """Phase 2: DNAAS Type Classification"""
        
        # Analyze VLAN patterns across all interfaces
        has_single_vlan = any(iface.vlan_config.has_single_vlan() for iface in bd.interfaces)
        has_qinq_tags = any(iface.vlan_config.has_qinq_tags() for iface in bd.interfaces)
        has_manipulation = any(iface.vlan_config.has_vlan_manipulation() for iface in bd.interfaces)
        has_physical_only = all(iface.is_physical_interface() and not iface.vlan_config.vlan_id 
                               for iface in bd.interfaces)
        
        # Classify according to DNAAS types
        if has_physical_only:
            bd.bridge_domain_type = BridgeDomainType.PORT_MODE  # Type 5
        elif has_manipulation and has_qinq_tags:
            bd.bridge_domain_type = BridgeDomainType.QINQ_SINGLE_BD  # Type 2A (simplified)
        elif has_qinq_tags:
            bd.bridge_domain_type = BridgeDomainType.DOUBLE_TAGGED  # Type 1
        elif has_single_vlan:
            bd.bridge_domain_type = BridgeDomainType.SINGLE_TAGGED  # Type 4A
        else:
            bd.bridge_domain_type = BridgeDomainType.SINGLE_TAGGED  # Default fallback
        
        bd.processing_phase = "phase2_classification"
        return bd
    
    def _bd_proc_phase3_global_identifier(self, bd: ProcessedBridgeDomain) -> ProcessedBridgeDomain:
        """Phase 3: Global Identifier Extraction - ONLY from CLI config data"""
        
        # Extract global identifier ONLY from actual interface configuration
        if bd.bridge_domain_type in [BridgeDomainType.DOUBLE_TAGGED, 
                                    BridgeDomainType.QINQ_SINGLE_BD,
                                    BridgeDomainType.QINQ_MULTI_BD]:
            # QinQ types: Use outer VLAN as service identifier
            outer_vlans = [iface.vlan_config.outer_vlan for iface in bd.interfaces 
                          if iface.vlan_config.outer_vlan is not None]
            if outer_vlans:
                bd.global_identifier = max(set(outer_vlans), key=outer_vlans.count)
        
        elif bd.bridge_domain_type == BridgeDomainType.SINGLE_TAGGED:
            # Single-tagged: Use VLAN ID as broadcast domain identifier
            vlan_ids = [iface.vlan_config.vlan_id for iface in bd.interfaces 
                       if iface.vlan_config.vlan_id is not None]
            if vlan_ids:
                bd.global_identifier = max(set(vlan_ids), key=vlan_ids.count)
        
        # NO fallback to name extraction - follow Golden Rule strictly
        
        # Determine if this BD can be consolidated
        bd.can_consolidate = bd.global_identifier is not None
        
        bd.processing_phase = "phase3_global_identifier"
        return bd
    
    def _bd_proc_phase4_username(self, bd: ProcessedBridgeDomain) -> ProcessedBridgeDomain:
        """Phase 4: Username Extraction"""
        
        # Extract username from bridge domain name
        bd.username = self._extract_username_from_name(bd.name)
        
        # Determine bridge domain scope
        if bd.name.startswith('g_'):
            bd.bridge_domain_scope = BridgeDomainScope.GLOBAL
        elif bd.name.startswith('l_'):
            bd.bridge_domain_scope = BridgeDomainScope.LOCAL
        else:
            bd.bridge_domain_scope = BridgeDomainScope.UNSPECIFIED
        
        bd.processing_phase = "phase4_username"
        return bd
    
    def _extract_username_from_name(self, bd_name: str) -> Optional[str]:
        """Extract username from bridge domain name using common patterns"""
        
        # Pattern 1: g_username_v123 or l_username_v123
        if bd_name.startswith(('g_', 'l_')):
            parts = bd_name.split('_')
            if len(parts) >= 2:
                return parts[1]
        
        # Pattern 2: username_v123 or username-123
        parts = bd_name.replace('-', '_').split('_')
        if len(parts) >= 2:
            # Look for username-like part (alphabetic, not numeric)
            for part in parts:
                if part.isalpha() and len(part) > 2:
                    return part
        
        return None
    
    def _bd_proc_phase5_devices(self, bd: ProcessedBridgeDomain, 
                               device_types: Dict[str, DeviceType]) -> ProcessedBridgeDomain:
        """Phase 5: Device Type Classification"""
        
        # Classify all devices in this bridge domain
        for device_name in bd.devices:
            device_type = device_types.get(device_name, DeviceType.LEAF)
            bd.device_types[device_name] = device_type
        
        bd.processing_phase = "phase5_devices"
        return bd
    
    def _bd_proc_phase6_interfaces(self, bd: ProcessedBridgeDomain, 
                                  lldp_data: Dict[str, Dict[str, Any]]) -> ProcessedBridgeDomain:
        """Phase 6: Interface Role Assignment"""
        
        # Assign roles to all interfaces
        for interface in bd.interfaces:
            try:
                # Get device type for this interface
                device_type = bd.device_types.get(interface.device_name, DeviceType.LEAF)
                
                # Assign interface role
                interface.interface_role = self._determine_interface_role(
                    interface, device_type, lldp_data.get(interface.device_name, {})
                )
                
                bd.interface_roles[interface.name] = interface.interface_role
                
            except Exception as e:
                bd.add_processing_warning(f"Failed to assign role for interface {interface.name}: {e}")
                interface.interface_role = "unknown"
        
        bd.processing_phase = "phase6_interfaces"
        return bd
    
    def _determine_interface_role(self, interface: InterfaceInfo, device_type: DeviceType, 
                                 lldp_data: Dict[str, Any]) -> str:
        """Determine interface role using hybrid approach"""
        
        # Bundle interfaces: Use pattern-based logic (proven reliable)
        if interface.is_bundle_interface():
            if device_type == DeviceType.LEAF:
                return "uplink"
            elif device_type == DeviceType.SPINE:
                return "downlink"
            else:
                return "transport"
        
        # Physical interfaces: Try LLDP-based logic, fallback to pattern
        if interface.is_physical_interface():
            # Try to get neighbor information from LLDP
            neighbor_info = lldp_data.get(interface.name, {})
            neighbor_device = neighbor_info.get('neighbor_device', '')
            
            if neighbor_device and neighbor_device != '|':
                # LLDP data available - use neighbor-based logic
                neighbor_type = self._classify_device_by_name(neighbor_device)
                
                if device_type == DeviceType.LEAF and neighbor_type == DeviceType.SPINE:
                    return "uplink"
                elif device_type == DeviceType.SPINE and neighbor_type == DeviceType.LEAF:
                    return "downlink"
                elif device_type == DeviceType.SPINE and neighbor_type == DeviceType.SPINE:
                    return "transport"
            
            # Fallback to pattern-based logic
            return "access"  # Default for physical interfaces
        
        # Default for other interface types
        return "access"
    
    def _bd_proc_phase7_consolidation_key(self, bd: ProcessedBridgeDomain) -> ProcessedBridgeDomain:
        """Phase 7: Consolidation Key Generation - ONLY from CLI config data"""
        
        # Generate consolidation key based on username and VLAN ID from actual config
        if bd.username and bd.global_identifier:
            # Global consolidation by username + VLAN ID (from actual config only)
            bd.consolidation_key = f"{bd.username}_{bd.global_identifier}"
            bd.can_consolidate = True
        elif bd.username:
            # Local consolidation by username only (for local bridge domains)
            bd.consolidation_key = f"local_{bd.username}"
            bd.can_consolidate = True
        else:
            # No consolidation - individual bridge domain (follow Golden Rule)
            bd.consolidation_key = f"individual_{bd.name}"
            bd.can_consolidate = False
        
        bd.processing_phase = "complete"
        return bd
    
    def _create_error_bridge_domain(self, bd: RawBridgeDomain, error: str) -> ProcessedBridgeDomain:
        """Create an error bridge domain for tracking processing failures"""
        error_bd = ProcessedBridgeDomain(
            name=bd.name,
            devices=bd.devices.copy(),
            interfaces=[],
            bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
            validation_status=ValidationStatus.INVALID,
            processing_phase="error"
        )
        error_bd.add_processing_error(error)
        return error_bd
    
    # =========================================================================
    # STEP 3: CONSOLIDATE AND SAVE RESULTS
    # =========================================================================
    
    def _step3_consolidate_and_save(self, processed_bds: List[ProcessedBridgeDomain]) -> DiscoveryResults:
        """
        Step 3: Consolidate related bridge domains and save results
        
        Args:
            processed_bds: List of processed bridge domains from Step 2
            
        Returns:
            Complete discovery results
        """
        
        # Filter valid bridge domains
        valid_bds = [bd for bd in processed_bds if bd.validation_status != ValidationStatus.INVALID]
        
        # Group bridge domains for consolidation
        consolidation_groups = self._group_for_consolidation(valid_bds)
        
        # Consolidate each group
        consolidated_bds = []
        individual_bds = []
        
        for group in consolidation_groups:
            if len(group.bridge_domains) > 1 and group.can_merge_safely:
                # Consolidate multiple bridge domains
                consolidated_bd = self._consolidate_bridge_domain_group(group)
                consolidated_bds.append(consolidated_bd)
            else:
                # Keep as individual bridge domains
                individual_bds.extend(group.bridge_domains)
        
        # Create final results
        results = DiscoveryResults(
            consolidated_bridge_domains=consolidated_bds,
            individual_bridge_domains=individual_bds,
            total_bridge_domains_discovered=len(processed_bds),
            total_bridge_domains_processed=len(valid_bds),
            total_bridge_domains_consolidated=len(consolidated_bds)
        )
        
        # Save results to files
        self._save_discovery_results(results)
        
        logger.info(f"🎯 Step 3 complete: {len(consolidated_bds)} consolidated, "
                   f"{len(individual_bds)} individual bridge domains")
        
        return results
    
    def _group_for_consolidation(self, processed_bds: List[ProcessedBridgeDomain]) -> List[ConsolidationGroup]:
        """Group bridge domains by consolidation key"""
        
        groups_dict = {}
        
        for bd in processed_bds:
            if bd.can_consolidate and bd.consolidation_key:
                key = bd.consolidation_key
                if key not in groups_dict:
                    groups_dict[key] = ConsolidationGroup(
                        consolidation_key=key,
                        bridge_domains=[]
                    )
                groups_dict[key].bridge_domains.append(bd)
            else:
                # Individual bridge domain (no consolidation)
                individual_key = f"individual_{bd.name}"
                groups_dict[individual_key] = ConsolidationGroup(
                    consolidation_key=individual_key,
                    bridge_domains=[bd],
                    consolidation_method="individual"
                )
        
        return list(groups_dict.values())
    
    def _consolidate_bridge_domain_group(self, group: ConsolidationGroup) -> ConsolidatedBridgeDomain:
        """Consolidate a group of related bridge domains"""
        
        bds = group.bridge_domains
        first_bd = bds[0]
        
        # Collect all devices and interfaces
        all_devices = []
        all_interfaces = []
        source_bd_names = []
        
        for bd in bds:
            all_devices.extend(bd.devices)
            all_interfaces.extend(bd.interfaces)
            source_bd_names.append(bd.name)
        
        # Remove duplicates while preserving order
        unique_devices = list(dict.fromkeys(all_devices))
        # For interfaces, we need to be more careful about duplicates
        unique_interfaces = self._deduplicate_interfaces(all_interfaces)
        
        # Select primary bridge domain name using standard format preference
        primary_name = self._select_primary_bridge_domain_name([bd.name for bd in group.bridge_domains])
        
        # Create consolidated bridge domain with real name
        consolidated_bd = ConsolidatedBridgeDomain(
            consolidated_name=primary_name,  # Use real BD name, not artificial "consolidated_" name
            consolidation_key=group.consolidation_key,
            global_identifier=first_bd.global_identifier,
            username=first_bd.username,
            all_devices=unique_devices,
            all_interfaces=unique_interfaces,
            bridge_domain_type=first_bd.bridge_domain_type,
            bridge_domain_scope=first_bd.bridge_domain_scope,
            source_bridge_domains=source_bd_names,
            consolidation_method=group.consolidation_method
        )
        
        return consolidated_bd
    
    def _deduplicate_interfaces(self, interfaces: List[InterfaceInfo]) -> List[InterfaceInfo]:
        """Remove duplicate interfaces while preserving the best information"""
        
        unique_interfaces = {}
        
        for interface in interfaces:
            key = f"{interface.device_name}:{interface.name}"
            
            if key not in unique_interfaces:
                unique_interfaces[key] = interface
            else:
                # Keep the interface with more complete information
                existing = unique_interfaces[key]
                if interface.confidence > existing.confidence:
                    unique_interfaces[key] = interface
        
        return list(unique_interfaces.values())
    
    def _save_discovery_results(self, results: DiscoveryResults):
        """Save discovery results to JSON files in legacy-compatible format"""
        
        output_dir = Path("topology/simplified_discovery_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save consolidated results in legacy-compatible format
        consolidated_file = output_dir / f"bridge_domain_mapping_{timestamp}.json"
        
        # Create legacy-compatible structure
        legacy_format = {
            "discovery_metadata": {
                "timestamp": datetime.now().isoformat(),
                "devices_scanned": results.total_devices,
                "bridge_domains_found": len(results.consolidated_bridge_domains) + len(results.individual_bridge_domains),
                "confidence_threshold": 70,
                "discovery_method": "simplified_3_step_workflow",
                "processing_time": results.total_processing_time
            },
            "bridge_domains": {},
            "topology_summary": {
                "total_consolidated": len(results.consolidated_bridge_domains),
                "total_individual": len(results.individual_bridge_domains),
                "total_devices": results.total_devices,
                "total_interfaces": results.total_interfaces,
                "success_rate": results.success_rate
            }
        }
        
        # Process consolidated bridge domains
        for cbd in results.consolidated_bridge_domains:
            bd_data = self._create_legacy_bridge_domain_structure(cbd)
            legacy_format["bridge_domains"][cbd.consolidated_name] = bd_data
        
        # Process individual bridge domains
        for ibd in results.individual_bridge_domains:
            bd_data = self._create_legacy_individual_bridge_domain_structure(ibd)
            legacy_format["bridge_domains"][ibd.name] = bd_data
        
        with open(consolidated_file, 'w') as f:
            json.dump(legacy_format, f, indent=2)
        
        logger.info(f"💾 Results saved to {consolidated_file}")
    
    def _create_legacy_bridge_domain_structure(self, cbd: ConsolidatedBridgeDomain):
        """Create legacy-compatible bridge domain structure"""
        
        # Group interfaces by device
        devices_dict = {}
        
        for interface in cbd.all_interfaces:
            device_name = interface.device_name
            
            if device_name not in devices_dict:
                devices_dict[device_name] = {
                    "interfaces": [],
                    "admin_state": "enabled",
                    "device_type": self._get_device_type_string(device_name)
                }
            
            # Add interface with full metadata including raw CLI config
            interface_data = {
                "name": interface.name,
                "type": self._determine_interface_type(interface.name),
                "vlan_id": getattr(interface.vlan_config, 'vlan_id', None),
                "outer_vlan": getattr(interface.vlan_config, 'outer_vlan', None),
                "inner_vlan": getattr(interface.vlan_config, 'inner_vlan', None),
                "role": interface.interface_role,
                "raw_cli_config": getattr(interface, 'raw_config', [])  # Preserve actual CLI commands
            }
            
            devices_dict[device_name]["interfaces"].append(interface_data)
        
        # Calculate topology analysis
        topology_analysis = self._calculate_topology_analysis(cbd)
        
        # Add bridge domain type classification
        bridge_domain_analysis = self._classify_bridge_domain_type(cbd)
        
        # Determine consolidation status and selection reason
        is_consolidated = len(cbd.source_bridge_domains) > 1
        selection_reason = "standard_format_preferred" if is_consolidated else "single_bridge_domain"
        
        return {
            "service_name": cbd.consolidated_name,
            "detected_username": cbd.username or "unknown",
            "detected_vlan": cbd.global_identifier,
            "confidence": int(cbd.consolidation_confidence * 100),
            "detection_method": "simplified_workflow",
            "scope": cbd.bridge_domain_scope.value if cbd.bridge_domain_scope else "unknown",
            "scope_description": self._get_scope_description(cbd.bridge_domain_scope),
            "topology_type": self._determine_topology_type(cbd),
            "is_consolidated": is_consolidated,  # Clear consolidation indicator
            "bridge_domain_analysis": bridge_domain_analysis,  # Add DNAAS type classification
            "devices": devices_dict,
            "topology_analysis": topology_analysis,
            "consolidation_info": {
                "represents_bridge_domains": cbd.source_bridge_domains,  # All original names
                "primary_selection_reason": selection_reason,  # Why this name was chosen
                "consolidation_key": cbd.consolidation_key,
                "consolidated_count": cbd.source_count
            }
        }
    
    def _create_legacy_individual_bridge_domain_structure(self, ibd: ProcessedBridgeDomain):
        """Create legacy-compatible structure for individual bridge domains"""
        
        # Group interfaces by device
        devices_dict = {}
        
        for interface in ibd.interfaces:
            device_name = interface.device_name
            
            if device_name not in devices_dict:
                devices_dict[device_name] = {
                    "interfaces": [],
                    "admin_state": "enabled", 
                    "device_type": self._get_device_type_string(device_name)
                }
            
            # Add interface with full metadata including raw CLI config
            interface_data = {
                "name": interface.name,
                "type": self._determine_interface_type(interface.name),
                "vlan_id": getattr(interface.vlan_config, 'vlan_id', None),
                "outer_vlan": getattr(interface.vlan_config, 'outer_vlan', None),
                "inner_vlan": getattr(interface.vlan_config, 'inner_vlan', None),
                "role": interface.interface_role,
                "raw_cli_config": getattr(interface, 'raw_config', [])  # Preserve actual CLI commands
            }
            
            devices_dict[device_name]["interfaces"].append(interface_data)
        
        # Calculate topology analysis for individual BD
        topology_analysis = self._calculate_individual_topology_analysis(ibd)
        
        # Add bridge domain type classification
        bridge_domain_analysis = self._classify_bridge_domain_type_individual(ibd)
        
        return {
            "service_name": ibd.name,
            "detected_username": ibd.username or "unknown",
            "detected_vlan": ibd.global_identifier,
            "confidence": int(ibd.confidence_score * 100),
            "detection_method": "simplified_workflow",
            "scope": ibd.bridge_domain_scope.value if ibd.bridge_domain_scope else "unknown",
            "scope_description": self._get_scope_description(ibd.bridge_domain_scope),
            "topology_type": self._determine_individual_topology_type(ibd),
            "is_consolidated": False,  # Individual bridge domain, not consolidated
            "bridge_domain_analysis": bridge_domain_analysis,  # Add DNAAS type classification
            "devices": devices_dict,
            "topology_analysis": topology_analysis,
            "consolidation_info": {
                "represents_bridge_domains": [ibd.name],  # Consistent naming with consolidated
                "primary_selection_reason": "individual_bridge_domain",
                "consolidation_key": ibd.consolidation_key or f"individual_{ibd.name}",
                "consolidated_count": 1
            }
        }
    
    def _get_device_type_string(self, device_name: str) -> str:
        """Get device type as string for legacy compatibility"""
        device_type = self._classify_device_by_name(device_name)
        return device_type.value.lower()
    
    def _determine_interface_type(self, interface_name: str) -> str:
        """Determine interface type for legacy compatibility"""
        if '.' in interface_name:
            return "subinterface"
        elif interface_name.lower().startswith('bundle'):
            return "physical"  # Bundle interfaces are physical in legacy format
        else:
            return "physical"
    
    def _get_scope_description(self, scope) -> str:
        """Get scope description for legacy compatibility"""
        if not scope:
            return "Unknown scope - unable to determine"
        
        scope_descriptions = {
            "global": "Globally significant VLAN ID, can be configured everywhere",
            "local": "Local scope - configured locally on a leaf and bridge local AC interfaces",
            "unspecified": "Unknown scope - unable to determine"
        }
        
        return scope_descriptions.get(scope.value if hasattr(scope, 'value') else str(scope), 
                                    "Unknown scope - unable to determine")
    
    def _determine_topology_type(self, cbd: ConsolidatedBridgeDomain) -> str:
        """Determine topology type based on devices and interfaces"""
        leaf_count = sum(1 for device in cbd.all_devices 
                        if self._classify_device_by_name(device).value == 'leaf')
        spine_count = sum(1 for device in cbd.all_devices 
                         if self._classify_device_by_name(device).value == 'spine')
        
        access_interfaces = sum(1 for interface in cbd.all_interfaces 
                               if interface.interface_role == 'access')
        
        if leaf_count <= 1 and spine_count == 0:
            return "unknown"  # Local topology
        elif leaf_count == 1 and access_interfaces <= 2:
            return "p2p"
        elif leaf_count > 1 or access_interfaces > 2:
            return "p2mp"
        else:
            return "unknown"
    
    def _determine_individual_topology_type(self, ibd: ProcessedBridgeDomain) -> str:
        """Determine topology type for individual bridge domain"""
        leaf_count = sum(1 for device in ibd.devices 
                        if self._classify_device_by_name(device).value == 'leaf')
        spine_count = sum(1 for device in ibd.devices 
                         if self._classify_device_by_name(device).value == 'spine')
        
        access_interfaces = sum(1 for interface in ibd.interfaces 
                               if interface.interface_role == 'access')
        
        if leaf_count <= 1 and spine_count == 0:
            return "unknown"  # Local topology
        elif leaf_count == 1 and access_interfaces <= 2:
            return "p2p"
        elif leaf_count > 1 or access_interfaces > 2:
            return "p2mp"
        else:
            return "unknown"
    
    def _calculate_topology_analysis(self, cbd: ConsolidatedBridgeDomain) -> dict:
        """Calculate topology analysis for consolidated bridge domain"""
        
        leaf_devices = sum(1 for device in cbd.all_devices 
                          if self._classify_device_by_name(device).value == 'leaf')
        spine_devices = sum(1 for device in cbd.all_devices 
                           if self._classify_device_by_name(device).value == 'spine')
        superspine_devices = sum(1 for device in cbd.all_devices 
                                if self._classify_device_by_name(device).value == 'superspine')
        
        access_interfaces = sum(1 for interface in cbd.all_interfaces 
                               if interface.interface_role == 'access')
        
        # Determine path complexity
        if spine_devices == 0:
            path_complexity = "local"
        elif superspine_devices > 0:
            path_complexity = "3-tier"
        else:
            path_complexity = "2-tier"
        
        # Estimate bandwidth (10G per interface)
        estimated_bandwidth = f"{len(cbd.all_interfaces) * 10}G"
        
        return {
            "topology_type": self._determine_topology_type(cbd),
            "path_complexity": path_complexity,
            "leaf_devices": leaf_devices,
            "spine_devices": spine_devices,
            "superspine_devices": superspine_devices,
            "total_interfaces": len(cbd.all_interfaces),
            "access_interfaces": access_interfaces,
            "estimated_bandwidth": estimated_bandwidth
        }
    
    def _calculate_individual_topology_analysis(self, ibd: ProcessedBridgeDomain) -> dict:
        """Calculate topology analysis for individual bridge domain"""
        
        leaf_devices = sum(1 for device in ibd.devices 
                          if self._classify_device_by_name(device).value == 'leaf')
        spine_devices = sum(1 for device in ibd.devices 
                           if self._classify_device_by_name(device).value == 'spine')
        superspine_devices = sum(1 for device in ibd.devices 
                                if self._classify_device_by_name(device).value == 'superspine')
        
        access_interfaces = sum(1 for interface in ibd.interfaces 
                               if interface.interface_role == 'access')
        
        # Determine path complexity
        if spine_devices == 0:
            path_complexity = "local"
        elif superspine_devices > 0:
            path_complexity = "3-tier"
        else:
            path_complexity = "2-tier"
        
        # Estimate bandwidth (10G per interface)
        estimated_bandwidth = f"{len(ibd.interfaces) * 10}G"
        
        return {
            "topology_type": self._determine_individual_topology_type(ibd),
            "path_complexity": path_complexity,
            "leaf_devices": leaf_devices,
            "spine_devices": spine_devices,
            "superspine_devices": superspine_devices,
            "total_interfaces": len(ibd.interfaces),
            "access_interfaces": access_interfaces,
            "estimated_bandwidth": estimated_bandwidth
        }
    
    def _create_error_results(self, error_message: str, start_time: datetime) -> DiscoveryResults:
        """Create error results when discovery fails"""
        results = DiscoveryResults(
            consolidated_bridge_domains=[],
            individual_bridge_domains=[],
            discovery_start_time=start_time
        )
        results.finalize_results()
        return results


# =============================================================================
# GUIDED RAILS: WORKFLOW VALIDATION
# =============================================================================

def validate_simplified_workflow():
    """
    Validate that the simplified workflow follows architectural guidelines
    """
    
    # Check that all required methods exist
    required_methods = [
        'discover_all_bridge_domains',
        '_step1_load_and_validate_data',
        '_step2_process_bridge_domains', 
        '_step3_consolidate_and_save'
    ]
    
    for method in required_methods:
        if not hasattr(SimplifiedBridgeDomainDiscovery, method):
            raise WorkflowError(f"Missing required method: {method}")
    
    # Check BD-PROC pipeline phases
    bd_proc_phases = [
        '_bd_proc_phase1_validation',
        '_bd_proc_phase2_classification',
        '_bd_proc_phase3_global_identifier',
        '_bd_proc_phase4_username',
        '_bd_proc_phase5_devices',
        '_bd_proc_phase6_interfaces',
        '_bd_proc_phase7_consolidation_key'
    ]
    
    for phase in bd_proc_phases:
        if not hasattr(SimplifiedBridgeDomainDiscovery, phase):
            raise WorkflowError(f"Missing BD-PROC phase: {phase}")
    
    print("✅ Simplified workflow validation passed")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_simplified_discovery(config_dir: str = "topology/configs/parsed_data") -> DiscoveryResults:
    """
    Main entry point for simplified bridge domain discovery
    
    Args:
        config_dir: Directory containing parsed configuration data
        
    Returns:
        Complete discovery results
    """
    
    # Validate workflow before running
    validate_simplified_workflow()
    
    # Create and run discovery system
    discovery_system = SimplifiedBridgeDomainDiscovery(config_dir)
    results = discovery_system.discover_all_bridge_domains()
    
    return results


if __name__ == "__main__":
    # Run the simplified discovery system
    try:
        results = run_simplified_discovery()
        print(f"🎉 Discovery completed successfully!")
        print(f"📊 Results: {len(results.consolidated_bridge_domains)} consolidated, "
              f"{len(results.individual_bridge_domains)} individual")
        print(f"⏱️ Processing time: {results.total_processing_time:.2f} seconds")
        print(f"✅ Success rate: {results.success_rate:.1%}")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()
