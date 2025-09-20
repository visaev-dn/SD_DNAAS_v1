#!/usr/bin/env python3
"""
Simplified Discovery Workflow

Implements the simplified 3-step workflow as documented in:
- REFACTORED_DISCOVERY_WORKFLOW_REVISED.md

SINGLE RESPONSIBILITY: Provide simple, reliable discovery workflow
INPUT: None (manages complete discovery process)
OUTPUT: Complete discovery results with statistics
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.bd_proc_pipeline import BridgeDomainProcessor, ProcessingResult, BDProcessingStats
from config_engine.service_name_analyzer import ServiceNameAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class DiscoveryResult:
    """Result of simplified discovery workflow"""
    success: bool
    processed_bridge_domains: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    errors: List[str] = None
    warnings: List[str] = None

class SimplifiedDiscoveryWorkflow:
    """
    Simplified Discovery Workflow
    
    Implements the 3-step workflow:
    1. Load and validate data
    2. Process bridge domains (BD-PROC)
    3. Consolidate and save results
    """
    
    def __init__(self):
        self.bd_processor = BridgeDomainProcessor()
        self.service_analyzer = ServiceNameAnalyzer()
        
        # Data paths
        self.parsed_data_dir = Path('topology/configs/parsed_data')
        self.bridge_domain_parsed_dir = self.parsed_data_dir / 'bridge_domain_parsed'
        self.vlan_config_parsed_dir = self.parsed_data_dir / 'vlan_config_parsed'
        self.lldp_parsed_dir = self.parsed_data_dir / 'lldp_parsed'
        
        # Output directory
        self.output_dir = Path('topology/simplified_discovery')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Discovery session tracking
        self.discovery_session_id = self._generate_discovery_session_id()
        self.discovery_start_time = datetime.now()
        
        logger.info("🚀 Simplified Discovery Workflow initialized")
    
    def run_discovery(self) -> DiscoveryResult:
        """
        Run the complete simplified discovery process
        
        Returns:
            DiscoveryResult with processed bridge domains and statistics
        """
        logger.info("🚀 Starting Simplified Discovery Workflow...")
        logger.info(f"📋 Discovery Session ID: {self.discovery_session_id}")
        
        try:
            # Step 1: Load and validate data
            logger.info("📥 Step 1: Loading and validating data...")
            data = self.load_and_validate_data()
            
            # Step 2: Process bridge domains (BD-PROC)
            logger.info("🔧 Step 2: Processing bridge domains...")
            processed_bds = self.process_bridge_domains(data)
            
            # Step 3: Consolidate and save results
            logger.info("💾 Step 3: Consolidating and saving results...")
            results = self.consolidate_and_save(processed_bds)
            
            # Generate statistics
            statistics = self._generate_discovery_statistics(results)
            
            logger.info("✅ Simplified Discovery Workflow completed successfully!")
            
            return DiscoveryResult(
                success=True,
                processed_bridge_domains=results['bridge_domains'],
                statistics=statistics,
                warnings=results.get('warnings', [])
            )
            
        except Exception as e:
            logger.error(f"❌ Simplified discovery failed: {e}")
            return DiscoveryResult(
                success=False,
                processed_bridge_domains=[],
                statistics={},
                errors=[f"Discovery failed: {e}"]
            )
    
    def load_and_validate_data(self) -> Dict[str, Any]:
        """
        Step 1: Load and validate all required data
        
        Returns:
            Dictionary containing validated bridge domains, device types, and LLDP data
        """
        logger.debug("🔍 Loading bridge domain data...")
        
        # Load bridge domain data
        bridge_domains = self._load_bridge_domain_data()
        if not bridge_domains:
            raise ValueError("No bridge domain data found")
        
        # Load device type data
        logger.debug("🔍 Loading device type data...")
        device_types_map = self._load_device_type_data()
        
        # Load LLDP data
        logger.debug("🔍 Loading LLDP data...")
        lldp_data = self._load_lldp_data()
        
        # Validate data quality
        self._validate_loaded_data(bridge_domains, device_types_map, lldp_data)
        
        logger.info(f"✅ Data loaded successfully: {len(bridge_domains)} bridge domains")
        
        return {
            'bridge_domains': bridge_domains,
            'device_types_map': device_types_map,
            'lldp_data': lldp_data
        }
    
    def process_bridge_domains(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Step 2: Process each bridge domain through BD-PROC pipeline
        
        Args:
            data: Loaded and validated data
            
        Returns:
            List of processed bridge domains
        """
        bridge_domains = data['bridge_domains']
        device_types_map = data['device_types_map']
        lldp_data = data['lldp_data']
        
        processed_bds = []
        processing_errors = []
        
        logger.info(f"🔧 Processing {len(bridge_domains)} bridge domains...")
        
        for i, bd in enumerate(bridge_domains):
            try:
                logger.debug(f"Processing BD {i+1}/{len(bridge_domains)}: {bd.get('name', 'unknown')}")
                
                # Process through BD-PROC pipeline
                result = self.bd_processor.process_bridge_domain(bd, device_types_map, lldp_data)
                
                if result.success:
                    processed_bds.append(result.bridge_domain)
                    logger.debug(f"✅ Processed: {result.bridge_domain.get('name', 'unknown')}")
                else:
                    error_msg = f"Failed to process {bd.get('name', 'unknown')}: {', '.join(result.errors)}"
                    processing_errors.append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Unexpected error processing {bd.get('name', 'unknown')}: {e}"
                processing_errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Log processing summary
        stats = self.bd_processor.get_processing_stats()
        logger.info(f"📊 Processing complete: {stats.successful} successful, {stats.failed} failed")
        
        if processing_errors:
            logger.warning(f"⚠️ {len(processing_errors)} processing errors occurred")
        
        return processed_bds
    
    def consolidate_and_save(self, processed_bds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 3: Consolidate and save results
        
        Args:
            processed_bds: List of processed bridge domains
            
        Returns:
            Dictionary containing consolidated results and metadata
        """
        logger.info(f"🔄 Consolidating {len(processed_bds)} processed bridge domains...")
        
        # Group by consolidation key
        consolidation_groups = {}
        for bd in processed_bds:
            consolidation_key = bd.get('consolidation_key', bd.get('name', 'unknown'))
            if consolidation_key not in consolidation_groups:
                consolidation_groups[consolidation_key] = []
            consolidation_groups[consolidation_key].append(bd)
        
        # Create consolidated bridge domains
        consolidated_bds = []
        for key, group in consolidation_groups.items():
            if len(group) == 1:
                # Single bridge domain - no consolidation needed
                consolidated_bds.append(group[0])
            else:
                # Multiple bridge domains - consolidate
                consolidated_bd = self._consolidate_bridge_domain_group(group)
                consolidated_bds.append(consolidated_bd)
        
        # Save results
        self._save_discovery_results(consolidated_bds)
        
        logger.info(f"✅ Consolidation complete: {len(consolidated_bds)} consolidated bridge domains")
        
        return {
            'bridge_domains': consolidated_bds,
            'consolidation_groups': len(consolidation_groups),
            'warnings': []
        }
    
    def _load_bridge_domain_data(self) -> List[Dict[str, Any]]:
        """Load bridge domain data from parsed files"""
        bridge_domains = []
        
        if not self.bridge_domain_parsed_dir.exists():
            logger.warning("Bridge domain parsed directory not found")
            return bridge_domains
        
        # Load all bridge domain instance files
        for bd_file in self.bridge_domain_parsed_dir.glob('*_bridge_domain_instance_parsed_*.yaml'):
            try:
                with open(bd_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                device = data.get('device')
                instances = data.get('bridge_domain_instances', [])
                
                for instance in instances:
                    # Create bridge domain record
                    bd_record = {
                        'name': instance.get('name'),
                        'interfaces': instance.get('interfaces', []),
                        'devices': [device] if device else [],
                        'raw_data': instance
                    }
                    
                    # Only add if it has required fields
                    if bd_record['name'] and bd_record['interfaces']:
                        bridge_domains.append(bd_record)
                    else:
                        logger.warning(f"Skipping bridge domain with missing data: {bd_record}")
                    
            except Exception as e:
                logger.warning(f"Failed to load bridge domain file {bd_file}: {e}")
                continue
        
        return bridge_domains
    
    def _load_device_type_data(self) -> Dict[str, str]:
        """Load device type data"""
        device_types = {}
        
        # Simple device type detection based on naming patterns
        # This is a placeholder - in real implementation, this would load from actual data
        for bd_file in self.bridge_domain_parsed_dir.glob('*_bridge_domain_instance_parsed_*.yaml'):
            try:
                with open(bd_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                device = data.get('device')
                if device:
                    device_type = self._detect_device_type(device)
                    device_types[device] = device_type
                    
            except Exception as e:
                logger.warning(f"Failed to load device type from {bd_file}: {e}")
                continue
        
        return device_types
    
    def _load_lldp_data(self) -> Dict[str, Any]:
        """Load LLDP data"""
        lldp_data = {}
        
        if not self.lldp_parsed_dir.exists():
            logger.warning("LLDP parsed directory not found")
            return lldp_data
        
        # Load LLDP data files
        for lldp_file in self.lldp_parsed_dir.glob('*_lldp_parsed_*.yaml'):
            try:
                with open(lldp_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                device = data.get('device')
                if device:
                    lldp_data[device] = data
                    
            except Exception as e:
                logger.warning(f"Failed to load LLDP file {lldp_file}: {e}")
                continue
        
        return lldp_data
    
    def _detect_device_type(self, device_name: str) -> str:
        """Detect device type based on device name"""
        device_name_upper = device_name.upper()
        
        if 'SUPERSPINE' in device_name_upper:
            return 'superspine'
        elif 'SPINE' in device_name_upper:
            return 'spine'
        elif 'LEAF' in device_name_upper:
            return 'leaf'
        else:
            return 'unknown'
    
    def _validate_loaded_data(self, bridge_domains: List[Dict], 
                            device_types_map: Dict[str, str], 
                            lldp_data: Dict[str, Any]) -> None:
        """Validate loaded data quality"""
        
        # Validate bridge domains
        if not bridge_domains:
            raise ValueError("No bridge domain data loaded")
        
        # Check for required fields
        for bd in bridge_domains:
            if not bd.get('name'):
                raise ValueError("Bridge domain missing name")
            if not bd.get('interfaces'):
                raise ValueError(f"Bridge domain {bd.get('name')} missing interfaces")
            if not bd.get('devices'):
                raise ValueError(f"Bridge domain {bd.get('name')} missing devices")
        
        logger.debug("✅ Data validation passed")
    
    def _consolidate_bridge_domain_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate a group of bridge domains with the same consolidation key"""
        if not group:
            return {}
        
        # Use the first bridge domain as base
        consolidated = group[0].copy()
        
        # Merge interfaces from all bridge domains
        all_interfaces = []
        all_devices = []
        
        for bd in group:
            all_interfaces.extend(bd.get('interfaces', []))
            all_devices.extend(bd.get('devices', []))
        
        # Remove duplicates
        consolidated['interfaces'] = list(set(all_interfaces))
        consolidated['devices'] = list(set(all_devices))
        
        # Add consolidation metadata
        consolidated['_consolidation_metadata'] = {
            'consolidated_count': len(group),
            'original_bridge_domains': [bd.get('name') for bd in group],
            'consolidation_timestamp': self._get_timestamp()
        }
        
        return consolidated
    
    def _save_discovery_results(self, consolidated_bds: List[Dict[str, Any]]) -> None:
        """Save discovery results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON output
        json_file = self.output_dir / f"simplified_discovery_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'discovery_session_id': self.discovery_session_id,
                'discovery_timestamp': self.discovery_start_time.isoformat(),
                'bridge_domains': consolidated_bds,
                'statistics': self._generate_discovery_statistics({'bridge_domains': consolidated_bds})
            }, f, indent=2)
        
        # Save summary report
        summary_file = self.output_dir / f"simplified_discovery_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(self._generate_summary_report(consolidated_bds))
        
        logger.info(f"💾 Results saved to {json_file}")
        logger.info(f"📊 Summary saved to {summary_file}")
    
    def _generate_discovery_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate discovery statistics"""
        bridge_domains = results.get('bridge_domains', [])
        bd_stats = self.bd_processor.get_processing_stats()
        
        # Count by DNAAS type
        dnaas_type_counts = {}
        for bd in bridge_domains:
            dnaas_type = bd.get('dnaas_type', 'unknown')
            dnaas_type_counts[dnaas_type] = dnaas_type_counts.get(dnaas_type, 0) + 1
        
        # Count by device type
        device_type_counts = {}
        for bd in bridge_domains:
            device_types = bd.get('device_types', {})
            for device_type in device_types.values():
                device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1
        
        # Count by consolidation scope
        consolidation_scope_counts = {}
        for bd in bridge_domains:
            scope = bd.get('consolidation_scope', 'unknown')
            consolidation_scope_counts[scope] = consolidation_scope_counts.get(scope, 0) + 1
        
        return {
            'total_bridge_domains': len(bridge_domains),
            'bd_proc_stats': {
                'total_processed': bd_stats.total_processed,
                'successful': bd_stats.successful,
                'failed': bd_stats.failed,
                'success_rate': bd_stats.successful / max(bd_stats.total_processed, 1)
            },
            'dnaas_type_distribution': dnaas_type_counts,
            'device_type_distribution': device_type_counts,
            'consolidation_scope_distribution': consolidation_scope_counts,
            'discovery_session_id': self.discovery_session_id,
            'discovery_duration': (datetime.now() - self.discovery_start_time).total_seconds()
        }
    
    def _generate_summary_report(self, consolidated_bds: List[Dict[str, Any]]) -> str:
        """Generate summary report"""
        stats = self._generate_discovery_statistics({'bridge_domains': consolidated_bds})
        
        report = []
        report.append("=" * 80)
        report.append("SIMPLIFIED DISCOVERY WORKFLOW SUMMARY")
        report.append("=" * 80)
        report.append(f"Discovery Session ID: {stats['discovery_session_id']}")
        report.append(f"Discovery Duration: {stats['discovery_duration']:.2f} seconds")
        report.append("")
        
        report.append("BRIDGE DOMAIN PROCESSING STATISTICS:")
        report.append("-" * 40)
        bd_stats = stats['bd_proc_stats']
        report.append(f"Total Processed: {bd_stats['total_processed']}")
        report.append(f"Successful: {bd_stats['successful']}")
        report.append(f"Failed: {bd_stats['failed']}")
        report.append(f"Success Rate: {bd_stats['success_rate']:.2%}")
        report.append("")
        
        report.append("DNAAS TYPE DISTRIBUTION:")
        report.append("-" * 30)
        for dnaas_type, count in stats['dnaas_type_distribution'].items():
            report.append(f"{dnaas_type}: {count}")
        report.append("")
        
        report.append("DEVICE TYPE DISTRIBUTION:")
        report.append("-" * 30)
        for device_type, count in stats['device_type_distribution'].items():
            report.append(f"{device_type}: {count}")
        report.append("")
        
        report.append("CONSOLIDATION SCOPE DISTRIBUTION:")
        report.append("-" * 35)
        for scope, count in stats['consolidation_scope_distribution'].items():
            report.append(f"{scope}: {count}")
        report.append("")
        
        report.append("BRIDGE DOMAINS:")
        report.append("-" * 15)
        for i, bd in enumerate(consolidated_bds, 1):
            name = bd.get('name', 'unknown')
            dnaas_type = bd.get('dnaas_type', 'unknown')
            scope = bd.get('consolidation_scope', 'unknown')
            interfaces = len(bd.get('interfaces', []))
            devices = len(bd.get('devices', []))
            
            report.append(f"{i:2d}. {name}")
            report.append(f"    Type: {dnaas_type}, Scope: {scope}")
            report.append(f"    Interfaces: {interfaces}, Devices: {devices}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_discovery_session_id(self) -> str:
        """Generate unique discovery session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"simplified_discovery_{timestamp}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        return datetime.now().isoformat()

# Convenience function for easy usage
def run_simplified_discovery() -> DiscoveryResult:
    """
    Convenience function to run simplified discovery
    
    Returns:
        DiscoveryResult with processed bridge domains and statistics
    """
    workflow = SimplifiedDiscoveryWorkflow()
    return workflow.run_discovery()

if __name__ == "__main__":
    # Test the simplified discovery workflow
    logging.basicConfig(level=logging.INFO)
    
    # Run discovery
    workflow = SimplifiedDiscoveryWorkflow()
    result = workflow.run_discovery()
    
    if result.success:
        print(f"✅ Discovery completed successfully!")
        print(f"📊 Processed {len(result.processed_bridge_domains)} bridge domains")
        print(f"📈 Success rate: {result.statistics['bd_proc_stats']['success_rate']:.2%}")
    else:
        print(f"❌ Discovery failed: {result.errors}")
