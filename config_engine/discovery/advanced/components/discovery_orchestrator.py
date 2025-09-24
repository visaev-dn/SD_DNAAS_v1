#!/usr/bin/env python3
"""
Enhanced Discovery Orchestrator

SINGLE RESPONSIBILITY: Orchestrate the complete discovery process using separated components

INPUT: None (manages the entire discovery workflow)
OUTPUT: Complete discovery results
DEPENDENCIES: All separated components
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .bridge_domain_detector import BridgeDomainDetector, BridgeDomainInstance
from .device_type_classifier import DeviceTypeClassifier, DeviceClassification
from .lldp_analyzer import LLDPAnalyzer, NeighborInfo, ValidationResult
from .interface_role_analyzer import InterfaceRoleAnalyzer, InterfaceInfo
from .global_identifier_extractor import GlobalIdentifierExtractor, GlobalIdentifierResult
from .consolidation_engine import ConsolidationEngine, ConsolidatedBridgeDomain
from .path_generator import PathGenerator
from .database_populator import DatabasePopulator, SaveResult

logger = logging.getLogger(__name__)

class EnhancedDiscoveryOrchestrator:
    """
    Enhanced Discovery Orchestrator
    
    SINGLE RESPONSIBILITY: Orchestrate the complete discovery process using separated components
    """
    
    def __init__(self):
        # Initialize all separated components
        self.bridge_domain_detector = BridgeDomainDetector()
        self.device_type_classifier = DeviceTypeClassifier()
        self.lldp_analyzer = LLDPAnalyzer()
        self.interface_role_analyzer = InterfaceRoleAnalyzer()
        self.global_identifier_extractor = GlobalIdentifierExtractor()
        self.consolidation_engine = ConsolidationEngine()
        self.path_generator = PathGenerator()
        self.database_populator = DatabasePopulator()
        
        # Discovery session tracking
        self.discovery_session_id = self._generate_discovery_session_id()
        self.discovery_start_time = datetime.now()
        
        # Output directory setup
        self.output_dir = Path('topology/enhanced_bridge_domain_discovery')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_enhanced_discovery(self) -> Dict[str, Any]:
        """
        Orchestrate the complete discovery process
        
        Returns:
            Complete discovery results with statistics
        """
        logger.info("🚀 Starting Enhanced Bridge Domain Discovery (Refactored Architecture)...")
        logger.info(f"📋 Discovery Session ID: {self.discovery_session_id}")
        
        try:
            # Phase 1: Data collection & classification
            bridge_domains, device_types, neighbor_maps = self._phase1_data_collection()
            
            # Phase 2: Interface analysis
            enhanced_bridge_domains = self._phase2_interface_analysis(
                bridge_domains, device_types, neighbor_maps
            )
            
            # Phase 3: Consolidation
            consolidated_bds = self._phase3_consolidation(enhanced_bridge_domains)
            
            # Phase 4: Paths & persistence
            results = self._phase4_paths_and_persistence(consolidated_bds)
            
            # Generate summary
            summary = self._generate_discovery_summary(results)
            
            logger.info("🚀 Enhanced Bridge Domain Discovery complete!")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Enhanced discovery failed: {e}")
            raise
    
    def _phase1_data_collection(self) -> tuple:
        """Phase 1: Data collection & classification"""
        logger.info("📋 Phase 1: Data Collection & Classification")
        
        # Step 1: Load and detect bridge domains
        parsed_data = self.bridge_domain_detector.load_parsed_data()
        bridge_domains = self.bridge_domain_detector.detect_bridge_domains(parsed_data)
        logger.info(f"✅ Detected {len(bridge_domains)} bridge domains")
        
        # Step 2: Classify device types
        all_devices = set()
        for bd in bridge_domains:
            all_devices.update(bd.devices)
        
        device_types = self.device_type_classifier.classify_all_devices(list(all_devices))
        logger.info(f"✅ Classified {len(device_types)} devices")
        
        # Step 3: Load LLDP data
        neighbor_maps = self.lldp_analyzer.load_all_lldp_data(list(all_devices))
        logger.info(f"✅ Loaded LLDP data for {len(neighbor_maps)} devices")
        
        return bridge_domains, device_types, neighbor_maps
    
    def _phase2_interface_analysis(self, bridge_domains: List[BridgeDomainInstance],
                                 device_types: Dict[str, DeviceClassification],
                                 neighbor_maps: Dict[str, Dict[str, NeighborInfo]]) -> Dict[str, List[InterfaceInfo]]:
        """Phase 2: Interface role assignment"""
        logger.info("🎯 Phase 2: Interface Analysis")
        
        enhanced_interfaces = {}
        
        for bd in bridge_domains:
            try:
                # Assign interface roles for this bridge domain
                interfaces = self.interface_role_analyzer.assign_roles_for_bridge_domain(
                    bd.name, bd.interfaces, device_types, neighbor_maps
                )
                enhanced_interfaces[bd.name] = interfaces
                logger.debug(f"✅ Assigned roles for {len(interfaces)} interfaces in {bd.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to assign interface roles for {bd.name}: {e}")
                enhanced_interfaces[bd.name] = []
        
        total_interfaces = sum(len(interfaces) for interfaces in enhanced_interfaces.values())
        logger.info(f"🎯 Interface analysis complete: {total_interfaces} interfaces processed")
        
        return enhanced_interfaces
    
    def _phase3_consolidation(self, enhanced_interfaces: Dict[str, List[InterfaceInfo]]) -> List[ConsolidatedBridgeDomain]:
        """Phase 3: Consolidation by global identifier"""
        logger.info("🔄 Phase 3: Consolidation")
        
        # Get bridge domains from detector
        bridge_domains = []
        for bd_name, interfaces in enhanced_interfaces.items():
            # Find the original bridge domain
            for bd in self.bridge_domain_detector.detect_bridge_domains(
                self.bridge_domain_detector.load_parsed_data()
            ):
                if bd.name == bd_name:
                    bridge_domains.append(bd)
                    break
        
        # Consolidate bridge domains
        consolidated_bds = self.consolidation_engine.consolidate_bridge_domains(
            bridge_domains, enhanced_interfaces
        )
        
        logger.info(f"🔄 Consolidation complete: {len(consolidated_bds)} consolidated domains")
        return consolidated_bds
    
    def _phase4_paths_and_persistence(self, consolidated_bds: List[ConsolidatedBridgeDomain]) -> Dict[str, Any]:
        """Phase 4: Path generation and database persistence"""
        logger.info("🛤️ Phase 4: Paths & Persistence")
        
        # Generate paths for each consolidated bridge domain
        for bd in consolidated_bds:
            try:
                paths = self.path_generator.generate_paths_for_bridge_domain(bd)
                bd.paths = paths
                logger.debug(f"✅ Generated {len(paths)} paths for {bd.consolidated_name}")
            except Exception as e:
                logger.error(f"❌ Failed to generate paths for {bd.consolidated_name}: {e}")
                bd.paths = []
        
        # Save to database
        save_results = self.database_populator.save_bridge_domains(consolidated_bds)
        
        # Save JSON output
        json_output = self._create_json_output(consolidated_bds, save_results)
        self._save_json_output(json_output)
        
        logger.info("🛤️ Paths & persistence complete")
        
        return {
            'consolidated_bridge_domains': consolidated_bds,
            'save_results': save_results,
            'json_output': json_output
        }
    
    def _generate_discovery_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive discovery summary"""
        
        consolidated_bds = results['consolidated_bridge_domains']
        save_results = results['save_results']
        
        # Calculate statistics
        total_bds = len(consolidated_bds)
        successful_saves = sum(1 for result in save_results if result.success)
        total_devices = len(set().union(*[bd.devices for bd in consolidated_bds]))
        total_interfaces = sum(len(bd.interfaces) for bd in consolidated_bds)
        
        # Create summary
        summary = {
            'discovery_metadata': {
                'session_id': self.discovery_session_id,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.discovery_start_time).total_seconds(),
                'discovery_type': 'enhanced_refactored_architecture'
            },
            'statistics': {
                'bridge_domains_discovered': total_bds,
                'bridge_domains_saved': successful_saves,
                'devices_involved': total_devices,
                'interfaces_processed': total_interfaces,
                'success_rate': (successful_saves / total_bds) * 100 if total_bds > 0 else 0
            },
            'consolidated_bridge_domains': [
                {
                    'name': bd.consolidated_name,
                    'global_identifier': bd.global_identifier,
                    'scope': bd.consolidation_scope.value,
                    'device_count': len(bd.devices),
                    'interface_count': len(bd.interfaces),
                    'source_count': len(bd.source_bridge_domains) if bd.source_bridge_domains else 1
                }
                for bd in consolidated_bds
            ]
        }
        
        return summary
    
    def _create_json_output(self, consolidated_bds: List[ConsolidatedBridgeDomain], 
                          save_results: List[SaveResult]) -> Dict[str, Any]:
        """Create JSON output in Legacy+ format"""
        
        json_output = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'session_id': self.discovery_session_id,
                'discovery_type': 'enhanced_refactored_architecture',
                'bridge_domains_found': len(consolidated_bds),
                'architecture': 'separated_concerns'
            },
            'bridge_domains': {}
        }
        
        for bd in consolidated_bds:
            # Create Legacy+ format entry
            bd_entry = {
                'service_name': bd.consolidated_name,
                'global_identifier': bd.global_identifier,
                'consolidation_scope': bd.consolidation_scope.value,
                'device_count': len(bd.devices),
                'interface_count': len(bd.interfaces),
                'confidence': bd.confidence,
                'devices': {}
            }
            
            # Add consolidation info if applicable
            if bd.consolidation_info:
                bd_entry['consolidation_info'] = {
                    'original_names': bd.consolidation_info.source_bridge_domains,
                    'consolidation_key': bd.consolidation_info.consolidation_key,
                    'consolidated_count': bd.consolidation_info.consolidated_count
                }
            
            # Group interfaces by device
            device_interfaces = {}
            for interface in bd.interfaces:
                if interface.device_name not in device_interfaces:
                    device_interfaces[interface.device_name] = []
                device_interfaces[interface.device_name].append(interface)
            
            # Add device information
            for device_name in bd.devices:
                interfaces = device_interfaces.get(device_name, [])
                
                bd_entry['devices'][device_name] = {
                    'interfaces': [
                        {
                            'name': iface.name,
                            'type': iface.interface_type.value,
                            'role': iface.interface_role.value,
                            'vlan_id': iface.vlan_id,
                            'confidence': iface.role_confidence,
                            'assignment_method': iface.role_assignment_method
                        }
                        for iface in interfaces
                    ],
                    'device_type': self._get_device_type_string(device_name),
                    'interface_count': len(interfaces)
                }
            
            json_output['bridge_domains'][bd.consolidated_name] = bd_entry
        
        return json_output
    
    def _save_json_output(self, json_output: Dict[str, Any]) -> None:
        """Save JSON output to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"enhanced_bridge_domain_mapping_refactored_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(json_output, f, indent=2)
        
        logger.info(f"💾 JSON output saved to: {output_file}")
    
    def _get_device_type_string(self, device_name: str) -> str:
        """Get device type as string"""
        classification = self.device_type_classifier.classify_device_type(device_name)
        return classification.device_type.value
    
    def _generate_discovery_session_id(self) -> str:
        """Generate unique discovery session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"refactored_discovery_{timestamp}"

# Convenience function for external usage
def run_refactored_enhanced_discovery() -> Dict[str, Any]:
    """
    Convenience function to run the refactored enhanced discovery
    
    Returns:
        Complete discovery results
    """
    orchestrator = EnhancedDiscoveryOrchestrator()
    return orchestrator.run_enhanced_discovery()
