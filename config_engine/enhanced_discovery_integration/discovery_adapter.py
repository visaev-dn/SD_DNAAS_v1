#!/usr/bin/env python3
"""
Enhanced Discovery Adapter

Main adapter for converting legacy discovery data to Enhanced Database structures.
This is the core orchestrator for the enhanced discovery integration.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Import Phase 1 data structures
from config_engine.phase1_data_structures import (
    TopologyData, PathInfo, BridgeDomainConfig
)

# Import enhanced discovery components
from .error_handler import EnhancedDiscoveryErrorHandler
from .logging_manager import EnhancedDiscoveryLoggingManager
from .data_converter import EnhancedDataConverter


class EnhancedDiscoveryAdapter:
    """Main adapter for converting legacy discovery data to Enhanced Database structures"""
    
    def __init__(self, legacy_data_path: str, enhanced_db_manager):
        self.legacy_data_path = Path(legacy_data_path)
        self.enhanced_db_manager = enhanced_db_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.error_handler = EnhancedDiscoveryErrorHandler()
        self.logging_manager = EnhancedDiscoveryLoggingManager()
        self.data_converter = EnhancedDataConverter()
        
        self.logger.info("🚀 Enhanced Discovery Adapter initialized")
    
    def convert_lacp_data(self, lacp_files: List[Path]) -> List[TopologyData]:
        """Convert LACP discovery data to Enhanced Database topology structures"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='lacp_conversion',
            details={
                'source_system': 'legacy',
                'target_system': 'enhanced_database',
                'file_count': len(lacp_files)
            }
        )
        
        try:
            self.logger.info(f"Converting {len(lacp_files)} LACP files to Enhanced Database structures")
            
            converted_topologies = []
            
            for lacp_file in lacp_files:
                try:
                    # Load LACP data
                    lacp_data = self._load_lacp_file(lacp_file)
                    
                    # Use enhanced conversion method
                    if hasattr(self.data_converter, 'convert_lacp_data_enhanced'):
                        topology_data_list = self.data_converter.convert_lacp_data_enhanced(lacp_data)
                        converted_topologies.extend(topology_data_list)
                    else:
                        # Fallback to basic conversion
                        converted_data = self.data_converter.convert_lacp_data(lacp_data)
                        topology_data = self._create_topology_from_converted_data(
                            converted_data, 
                            f"LACP-{lacp_file.stem}",
                            'lacp_discovery'
                        )
                        converted_topologies.append(topology_data)
                    
                    self.logger.debug(f"Successfully converted LACP file: {lacp_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert LACP file {lacp_file.name}: {e}")
                    self.error_handler.handle_conversion_error(e, {
                        'operation_id': operation_id,
                        'source_system': 'legacy',
                        'target_system': 'enhanced_database',
                        'data_type': 'lacp_data',
                        'file_path': str(lacp_file)
                    })
                    continue
            
            # Update operation with results
            self.logging_manager.update_operation(operation_id, {
                'record_count': len(converted_topologies)
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=len(converted_topologies)
            )
            
            self.logger.info(f"Successfully converted {len(converted_topologies)} LACP topologies")
            return converted_topologies
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def convert_lldp_data(self, lldp_files: List[Path]) -> List[PathInfo]:
        """Convert LLDP neighbor data to Enhanced Database path structures"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='lldp_conversion',
            details={
                'source_system': 'legacy',
                'target_system': 'enhanced_database',
                'file_count': len(lldp_files)
            }
        )
        
        try:
            self.logger.info(f"Converting {len(lldp_files)} LLDP files to Enhanced Database path structures")
            
            converted_paths = []
            
            for lldp_file in lldp_files:
                try:
                    # Load LLDP data
                    lldp_data = self._load_lldp_file(lldp_file)
                    
                    # Use enhanced conversion method
                    if hasattr(self.data_converter, 'convert_lldp_data_enhanced'):
                        path_info_list = self.data_converter.convert_lldp_data_enhanced(lldp_data)
                        converted_paths.extend(path_info_list)
                    else:
                        # Fallback to basic conversion
                        converted_data = self.data_converter.convert_lldp_data(lldp_data)
                        for item in converted_data:
                            if item['type'] == 'path_segment':
                                path_info = self._create_path_from_segment(item['data'])
                                converted_paths.append(path_info)
                    
                    self.logger.debug(f"Successfully converted LLDP file: {lldp_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert LLDP file {lldp_file.name}: {e}")
                    self.error_handler.handle_conversion_error(e, {
                        'operation_id': operation_id,
                        'source_system': 'legacy',
                        'target_system': 'enhanced_database',
                        'data_type': 'lldp_data',
                        'file_path': str(lldp_file)
                    })
                    continue
            
            # Update operation with results
            self.logging_manager.update_operation(operation_id, {
                'record_count': len(converted_paths)
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=len(converted_paths)
            )
            
            self.logger.info(f"Successfully converted {len(converted_paths)} LLDP paths")
            return converted_paths
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def convert_bridge_domain_data(self, bd_files: List[Path]) -> List[BridgeDomainConfig]:
        """Convert bridge domain data to Enhanced Database bridge domain structures"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='bridge_domain_conversion',
            details={
                'source_system': 'legacy',
                'target_system': 'enhanced_database',
                'file_count': len(bd_files)
            }
        )
        
        try:
            self.logger.info(f"Converting {len(bd_files)} Bridge Domain files to Enhanced Database structures")
            
            converted_bridge_domains = []
            
            for bd_file in bd_files:
                try:
                    # Load Bridge Domain data
                    bd_data = self._load_bridge_domain_file(bd_file)
                    
                    # Use enhanced conversion method
                    if hasattr(self.data_converter, 'convert_bridge_domain_data_enhanced'):
                        topology_data_list = self.data_converter.convert_bridge_domain_data_enhanced(bd_data)
                        # Extract bridge domain configs from topology data
                        for topology in topology_data_list:
                            if topology.bridge_domain_config:
                                converted_bridge_domains.append(topology.bridge_domain_config)
                    else:
                        # Fallback to basic conversion
                        converted_data = self.data_converter.convert_bridge_domain_data(bd_data)
                        for item in converted_data:
                            if item['type'] == 'bridge_domain_config':
                                converted_bridge_domains.append(item['data'])
                    
                    self.logger.debug(f"Successfully converted Bridge Domain file: {bd_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert Bridge Domain file {bd_file.name}: {e}")
                    self.error_handler.handle_conversion_error(e, {
                        'operation_id': operation_id,
                        'source_system': 'legacy',
                        'target_system': 'enhanced_database',
                        'data_type': 'bridge_domain_data',
                        'file_path': str(bd_file)
                    })
                    continue
            
            # Update operation with results
            self.logging_manager.update_operation(operation_id, {
                'record_count': len(converted_bridge_domains)
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=len(converted_bridge_domains)
            )
            
            self.logger.info(f"Successfully converted {len(converted_bridge_domains)} Bridge Domain configs")
            return converted_bridge_domains
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def convert_legacy_database(self, legacy_records: List[Dict]) -> List[TopologyData]:
        """Convert legacy database records to Enhanced Database structures"""
        
        operation_id = self.logging_manager.start_operation(
            operation_type='legacy_database_conversion',
            details={
                'source_system': 'legacy_database',
                'target_system': 'enhanced_database',
                'record_count': len(legacy_records)
            }
        )
        
        try:
            self.logger.info(f"Converting {len(legacy_records)} legacy database records to Enhanced Database structures")
            
            converted_topologies = []
            
            for record in legacy_records:
                try:
                    # Convert based on record type
                    if 'bridge_domain_name' in record:
                        # This is a bridge domain record
                        topology_data = self._convert_bridge_domain_record(record)
                        converted_topologies.append(topology_data)
                    elif 'service_name' in record:
                        # This is a service record
                        topology_data = self._convert_service_record(record)
                        converted_topologies.append(topology_data)
                    else:
                        self.logger.warning(f"Unknown record type: {record.keys()}")
                        continue
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert legacy record: {e}")
                    self.error_handler.handle_conversion_error(e, {
                        'operation_id': operation_id,
                        'source_system': 'legacy_database',
                        'target_system': 'enhanced_database',
                        'data_type': 'legacy_record',
                        'record_data': record
                    })
                    continue
            
            # Update operation with results
            self.logging_manager.update_operation(operation_id, {
                'record_count': len(converted_topologies)
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=len(converted_topologies)
            )
            
            self.logger.info(f"Successfully converted {len(converted_topologies)} legacy database records")
            return converted_topologies
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            raise
    
    def _load_lacp_file(self, file_path: Path) -> Dict[str, Any]:
        """Load LACP data from file"""
        
        try:
            import yaml
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load LACP file {file_path}: {e}")
            raise
    
    def _load_lldp_file(self, file_path: Path) -> Dict[str, Any]:
        """Load LLDP data from file"""
        
        try:
            import yaml
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load LLDP file {file_path}: {e}")
            raise
    
    def _load_bridge_domain_file(self, file_path: Path) -> Dict[str, Any]:
        """Load Bridge Domain data from file"""
        
        try:
            import yaml
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load Bridge Domain file {file_path}: {e}")
            raise
    
    def _create_topology_from_converted_data(self, converted_data: List[Dict], 
                                           topology_name: str, scan_method: str) -> TopologyData:
        """Create TopologyData from converted data"""
        
        # This is a placeholder - will be implemented in Phase 1G.2
        # For now, return a basic topology structure
        
        from config_engine.phase1_data_structures import TopologyType
        
        return TopologyData(
            bridge_domain_name=topology_name,
            topology_type=TopologyType.P2P,
            vlan_id=None,
            devices=[],
            interfaces=[],
            paths=[],
            bridge_domain_config=None,
            discovered_at=datetime.now(),
            scan_method=scan_method
        )
    
    def _create_path_from_segment(self, segment_data: Dict):
        """Create PathInfo from path segment data"""
        
        # This is a placeholder - will be implemented in Phase 1G.2
        # For now, return the segment data as-is
        
        return segment_data
    
    def _convert_bridge_domain_record(self, record: Dict) -> TopologyData:
        """Convert legacy bridge domain record to TopologyData"""
        
        # This is a placeholder - will be implemented in Phase 1G.2
        # For now, return a basic topology structure
        
        from config_engine.phase1_data_structures import TopologyType
        
        return TopologyData(
            bridge_domain_name=record.get('bridge_domain_name', 'unknown'),
            topology_type=TopologyType.P2P,
            vlan_id=record.get('vlan_id'),
            devices=[],
            interfaces=[],
            paths=[],
            bridge_domain_config=None,
            discovered_at=datetime.now(),
            scan_method='legacy_database_migration'
        )
    
    def _convert_service_record(self, record: Dict) -> TopologyData:
        """Convert legacy service record to TopologyData"""
        
        # This is a placeholder - will be implemented in Phase 1G.2
        # For now, return a basic topology structure
        
        from config_engine.phase1_data_structures import TopologyType
        
        return TopologyData(
            bridge_domain_name=record.get('service_name', 'unknown'),
            topology_type=TopologyType.P2P,
            vlan_id=record.get('vlan_id'),
            devices=[],
            interfaces=[],
            paths=[],
            bridge_domain_config=None,
            discovered_at=datetime.now(),
            scan_method='legacy_database_migration'
        )
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics from all components"""
        
        stats = {
            'data_converter': self.data_converter.get_conversion_statistics(),
            'logging_manager': self.logging_manager.generate_operation_summary(),
            'error_handler': self.error_handler.get_error_statistics()
        }
        
        return stats
    
    def generate_troubleshooting_report(self) -> str:
        """Generate comprehensive troubleshooting report"""
        
        return self.error_handler.generate_troubleshooting_report()
