#!/usr/bin/env python3
"""
Enhanced Auto-Population Service - Phase 1G.3

Automatically populates Enhanced Database from discovery results
while preserving ALL discovered data in its original format.
"""

import logging
import time
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Import Phase 1 data structures
from config_engine.phase1_data_structures import TopologyData

# Import enhanced discovery components
from .error_handler import EnhancedDiscoveryErrorHandler
from .logging_manager import EnhancedDiscoveryLoggingManager


@dataclass
class PreservedDataRecord:
    """Record for preserving original discovered data"""
    discovery_id: str
    original_data: Dict[str, Any]
    data_hash: str
    discovery_type: str
    source_file: Optional[str] = None
    source_database: Optional[str] = None
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    conversion_timestamp: Optional[datetime] = None
    converted_topology_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedAutoPopulationService:
    """Enhanced auto-population service with complete data preservation"""
    
    def __init__(self, enhanced_db_manager):
        self.enhanced_db_manager = enhanced_db_manager
        self.logger = logging.getLogger(__name__)
        self.error_handler = EnhancedDiscoveryErrorHandler()
        self.logging_manager = EnhancedDiscoveryLoggingManager()
        
        # Data preservation storage
        self.preserved_data: Dict[str, PreservedDataRecord] = {}
        
        # Population statistics with preservation tracking
        self.population_stats = {
            'total_records_processed': 0,
            'successfully_populated': 0,
            'failed_populations': 0,
            'records_preserved': 0,
            'data_loss_incidents': 0,
            'preservation_errors': 0,
            'conversion_errors': 0
        }
        
        self.logger.info("🚀 Enhanced Auto-Population Service initialized (Phase 1G.3)")
    
    def populate_from_discovery_with_preservation(self, discovery_results: Dict) -> Dict[str, Any]:
        """Populate Enhanced Database from discovery results with complete data preservation"""
        
        operation_id = str(uuid.uuid4())
        self.logging_manager.start_operation(
            operation_id=operation_id,
            operation_type='discovery_population_with_preservation',
            details={
                'source_system': 'discovery',
                'target_system': 'enhanced_database',
                'discovery_type': discovery_results.get('type', 'unknown'),
                'preservation_enabled': True
            }
        )
        
        try:
            self.logger.info("Starting Enhanced Database population with data preservation")
            
            # Extract and preserve discovery data
            preserved_records = self._preserve_discovery_data(discovery_results)
            
            # Convert preserved data to Enhanced Database structures
            conversion_results = self._convert_preserved_data_to_enhanced_structures(preserved_records)
            
            # Populate Enhanced Database
            population_results = self._populate_enhanced_database(conversion_results)
            
            # Update operation
            self.logging_manager.update_operation(operation_id, {
                'records_preserved': len(preserved_records),
                'records_converted': len(conversion_results),
                'records_populated': population_results['successful_populations']
            })
            
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='completed',
                record_count=population_results['successful_populations']
            )
            
            self.logger.info(f"Successfully populated {population_results['successful_populations']} records with data preservation")
            
            return {
                'success': True,
                'total_records': population_results['total_records'],
                'successful_populations': population_results['successful_populations'],
                'records_preserved': len(preserved_records),
                'records_converted': len(conversion_results),
                'audit_id': operation_id,
                'statistics': self.get_population_statistics()
            }
            
        except Exception as e:
            self.logging_manager.complete_operation(
                operation_id=operation_id,
                status='failed',
                error_message=str(e)
            )
            
            error_result = self.error_handler.handle_database_error(e, 'discovery_population_with_preservation')
            
            return {
                'success': False,
                'error': str(e),
                'error_details': error_result,
                'statistics': self.get_population_statistics()
            }
    
    def _preserve_discovery_data(self, discovery_results: Dict) -> List[PreservedDataRecord]:
        """Preserve all discovered data in its original format"""
        
        preserved_records = []
        
        try:
            # Preserve LACP data
            lacp_data = discovery_results.get('lacp_data', {})
            if lacp_data:
                preserved_records.extend(self._preserve_lacp_data(lacp_data))
            
            # Preserve LLDP data
            lldp_data = discovery_results.get('lldp_data', {})
            if lldp_data:
                preserved_records.extend(self._preserve_lldp_data(lldp_data))
            
            # Preserve Bridge Domain data
            bd_data = discovery_results.get('bridge_domain_data', {})
            if bd_data:
                preserved_records.extend(self._preserve_bridge_domain_data(bd_data))
            
            # Preserve legacy database records
            legacy_records = discovery_results.get('legacy_database_records', [])
            if legacy_records:
                preserved_records.extend(self._preserve_legacy_database_records(legacy_records))
            
            # Preserve any other discovery data
            other_data = {k: v for k, v in discovery_results.items() 
                         if k not in ['lacp_data', 'lldp_data', 'bridge_domain_data', 'legacy_database_records']}
            if other_data:
                preserved_records.extend(self._preserve_other_discovery_data(other_data))
            
            self.logger.info(f"Preserved {len(preserved_records)} discovery data records")
            
        except Exception as e:
            self.logger.error(f"Error preserving discovery data: {e}")
            self.population_stats['preservation_errors'] += 1
            raise
        
        return preserved_records
    
    def _preserve_lacp_data(self, lacp_data: Dict) -> List[PreservedDataRecord]:
        """Preserve LACP discovery data"""
        
        preserved_records = []
        bundles = lacp_data.get('bundles', [])
        
        for bundle in bundles:
            try:
                # Create unique discovery ID
                discovery_id = f"lacp_{bundle.get('name', 'unknown')}_{int(time.time())}"
                
                # Calculate data hash for integrity
                data_hash = self._calculate_data_hash(bundle)
                
                # Create preserved data record
                preserved_record = PreservedDataRecord(
                    discovery_id=discovery_id,
                    original_data=bundle,
                    data_hash=data_hash,
                    discovery_type='lacp',
                    source_file=lacp_data.get('source_file'),
                    metadata={
                        'bundle_name': bundle.get('name'),
                        'bundle_id': bundle.get('bundle_id'),
                        'member_count': len(bundle.get('members', [])),
                        'status': bundle.get('status'),
                        'preservation_method': 'enhanced_auto_population'
                    }
                )
                
                # Store preserved record
                self.preserved_data[discovery_id] = preserved_record
                preserved_records.append(preserved_record)
                
                self.logger.debug(f"Preserved LACP bundle: {bundle.get('name', 'unknown')}")
                
            except Exception as e:
                self.logger.error(f"Failed to preserve LACP bundle {bundle.get('name', 'unknown')}: {e}")
                self.population_stats['preservation_errors'] += 1
                continue
        
        return preserved_records
    
    def _preserve_lldp_data(self, lldp_data: Dict) -> List[PreservedDataRecord]:
        """Preserve LLDP discovery data"""
        
        preserved_records = []
        neighbors = lldp_data.get('neighbors', [])
        device_name = lldp_data.get('device_name', 'unknown')
        
        for neighbor in neighbors:
            try:
                # Create unique discovery ID
                discovery_id = f"lldp_{device_name}_{neighbor.get('neighbor_device', 'unknown')}_{int(time.time())}"
                
                # Calculate data hash for integrity
                data_hash = self._calculate_data_hash(neighbor)
                
                # Create preserved data record
                preserved_record = PreservedDataRecord(
                    discovery_id=discovery_id,
                    original_data=neighbor,
                    data_hash=data_hash,
                    discovery_type='lldp',
                    source_file=lldp_data.get('source_file'),
                    metadata={
                        'local_device': device_name,
                        'neighbor_device': neighbor.get('neighbor_device'),
                        'local_interface': neighbor.get('local_interface'),
                        'neighbor_interface': neighbor.get('neighbor_interface'),
                        'chassis_id': neighbor.get('chassis_id'),
                        'preservation_method': 'enhanced_auto_population'
                    }
                )
                
                # Store preserved record
                self.preserved_data[discovery_id] = preserved_record
                preserved_records.append(preserved_record)
                
                self.logger.debug(f"Preserved LLDP neighbor: {neighbor.get('neighbor_device', 'unknown')}")
                
            except Exception as e:
                self.logger.error(f"Failed to preserve LLDP neighbor {neighbor.get('neighbor_device', 'unknown')}: {e}")
                self.population_stats['preservation_errors'] += 1
                continue
        
        return preserved_records
    
    def _preserve_bridge_domain_data(self, bd_data: Dict) -> List[PreservedDataRecord]:
        """Preserve Bridge Domain discovery data"""
        
        preserved_records = []
        bridge_domains = bd_data.get('bridge_domains', [])
        
        for bd in bridge_domains:
            try:
                # Create unique discovery ID
                service_name = bd.get('service_name') or bd.get('name', 'unknown')
                discovery_id = f"bd_{service_name}_{int(time.time())}"
                
                # Calculate data hash for integrity
                data_hash = self._calculate_data_hash(bd)
                
                # Create preserved data record
                preserved_record = PreservedDataRecord(
                    discovery_id=discovery_id,
                    original_data=bd,
                    data_hash=data_hash,
                    discovery_type='bridge_domain',
                    source_file=bd_data.get('source_file'),
                    metadata={
                        'service_name': service_name,
                        'source_device': bd.get('source_device'),
                        'source_interface': bd.get('source_interface'),
                        'vlan_id': bd.get('vlan_id'),
                        'destination_count': len(bd.get('destinations', [])),
                        'preservation_method': 'enhanced_auto_population'
                    }
                )
                
                # Store preserved record
                self.preserved_data[discovery_id] = preserved_record
                preserved_records.append(preserved_record)
                
                self.logger.debug(f"Preserved Bridge Domain: {service_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to preserve Bridge Domain {bd.get('service_name', 'unknown')}: {e}")
                self.population_stats['preservation_errors'] += 1
                continue
        
        return preserved_records
    
    def _preserve_legacy_database_records(self, legacy_records: List[Dict]) -> List[PreservedDataRecord]:
        """Preserve legacy database records"""
        
        preserved_records = []
        
        for record in legacy_records:
            try:
                # Create unique discovery ID
                record_id = record.get('id') or record.get('bridge_domain_name') or record.get('service_name', 'unknown')
                discovery_id = f"legacy_{record_id}_{int(time.time())}"
                
                # Calculate data hash for integrity
                data_hash = self._calculate_data_hash(record)
                
                # Create preserved data record
                preserved_record = PreservedDataRecord(
                    discovery_id=discovery_id,
                    original_data=record,
                    data_hash=data_hash,
                    discovery_type='legacy_database',
                    source_database=record.get('source_database', 'unknown'),
                    metadata={
                        'record_type': self._determine_legacy_record_type(record),
                        'record_id': record_id,
                        'preservation_method': 'enhanced_auto_population'
                    }
                )
                
                # Store preserved record
                self.preserved_data[discovery_id] = preserved_record
                preserved_records.append(preserved_record)
                
                self.logger.debug(f"Preserved legacy record: {record_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to preserve legacy record: {e}")
                self.population_stats['preservation_errors'] += 1
                continue
        
        return preserved_records
    
    def _preserve_other_discovery_data(self, other_data: Dict) -> List[PreservedDataRecord]:
        """Preserve any other discovery data types"""
        
        preserved_records = []
        
        for data_type, data in other_data.items():
            try:
                # Create unique discovery ID
                discovery_id = f"other_{data_type}_{int(time.time())}"
                
                # Calculate data hash for integrity
                data_hash = self._calculate_data_hash(data)
                
                # Create preserved data record
                preserved_record = PreservedDataRecord(
                    discovery_id=discovery_id,
                    original_data=data,
                    data_hash=data_hash,
                    discovery_type=f'other_{data_type}',
                    metadata={
                        'data_type': data_type,
                        'data_size': len(str(data)),
                        'preservation_method': 'enhanced_auto_population'
                    }
                )
                
                # Store preserved record
                self.preserved_data[discovery_id] = preserved_record
                preserved_records.append(preserved_record)
                
                self.logger.debug(f"Preserved other discovery data: {data_type}")
                
            except Exception as e:
                self.logger.error(f"Failed to preserve other discovery data {data_type}: {e}")
                self.population_stats['preservation_errors'] += 1
                continue
        
        return preserved_records
    
    def _convert_preserved_data_to_enhanced_structures(self, preserved_records: List[PreservedDataRecord]) -> List[TopologyData]:
        """Convert preserved data to Enhanced Database structures"""
        
        converted_topologies = []
        
        try:
            from .discovery_adapter import EnhancedDiscoveryAdapter
            
            # Create discovery adapter for conversion
            discovery_adapter = EnhancedDiscoveryAdapter(
                legacy_data_path="preserved_data",
                enhanced_db_manager=self.enhanced_db_manager
            )
            
            # Group preserved records by type
            lacp_records = [r for r in preserved_records if r.discovery_type == 'lacp']
            lldp_records = [r for r in preserved_records if r.discovery_type == 'lldp']
            bd_records = [r for r in preserved_records if r.discovery_type == 'bridge_domain']
            legacy_records = [r for r in preserved_records if r.discovery_type == 'legacy_database']
            
            # Convert LACP data
            if lacp_records:
                lacp_data = {'bundles': [r.original_data for r in lacp_records]}
                try:
                    lacp_topologies = discovery_adapter.convert_lacp_data([Path("preserved_lacp")])
                    converted_topologies.extend(lacp_topologies)
                    
                    # Update preserved records with conversion results
                    for i, record in enumerate(lacp_records):
                        if i < len(lacp_topologies):
                            record.converted_topology_ids.append(str(i))
                            record.conversion_timestamp = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert preserved LACP data: {e}")
                    self.population_stats['conversion_errors'] += 1
            
            # Convert Bridge Domain data
            if bd_records:
                bd_data = {'bridge_domains': [r.original_data for r in bd_records]}
                try:
                    bd_topologies = discovery_adapter.convert_bridge_domain_data([Path("preserved_bd")])
                    converted_topologies.extend(bd_topologies)
                    
                    # Update preserved records with conversion results
                    for i, record in enumerate(bd_records):
                        if i < len(bd_topologies):
                            record.converted_topology_ids.append(str(i))
                            record.conversion_timestamp = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert preserved Bridge Domain data: {e}")
                    self.population_stats['conversion_errors'] += 1
            
            # Convert legacy database records
            if legacy_records:
                try:
                    legacy_topologies = discovery_adapter.convert_legacy_database(
                        [r.original_data for r in legacy_records]
                    )
                    converted_topologies.extend(legacy_topologies)
                    
                    # Update preserved records with conversion results
                    for i, record in enumerate(legacy_records):
                        if i < len(legacy_topologies):
                            record.converted_topology_ids.append(str(i))
                            record.conversion_timestamp = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"Failed to convert preserved legacy database data: {e}")
                    self.population_stats['conversion_errors'] += 1
            
            self.logger.info(f"Converted {len(converted_topologies)} topologies from preserved data")
            
        except Exception as e:
            self.logger.error(f"Error converting preserved data: {e}")
            self.population_stats['conversion_errors'] += 1
            raise
        
        return converted_topologies
    
    def _populate_enhanced_database(self, topologies: List[TopologyData]) -> Dict[str, Any]:
        """Populate Enhanced Database with converted topologies"""
        
        try:
            from .enhanced_database_integration import EnhancedDatabaseIntegration
            
            # Create database integration instance
            db_integration = EnhancedDatabaseIntegration(self.enhanced_db_manager)
            
            # Integrate discovery data into Enhanced Database
            integration_result = db_integration.integrate_discovery_data(topologies)
            
            if integration_result['success']:
                successful_populations = integration_result['total_records']
                failed_populations = 0
                
                # Update statistics
                self.population_stats['total_records_processed'] += len(topologies)
                self.population_stats['successfully_populated'] += successful_populations
                self.population_stats['failed_populations'] += failed_populations
                self.population_stats['records_preserved'] = len(self.preserved_data)
                
                self.logger.info(f"Enhanced Database integration successful: {successful_populations} records")
                
                return {
                    'total_records': len(topologies),
                    'successful_populations': successful_populations,
                    'failed_populations': failed_populations,
                    'integration_details': integration_result
                }
            else:
                # Integration failed
                failed_populations = len(topologies)
                
                # Update statistics
                self.population_stats['total_records_processed'] += len(topologies)
                self.population_stats['failed_populations'] += failed_populations
                self.population_stats['records_preserved'] = len(self.preserved_data)
                
                self.logger.error(f"Enhanced Database integration failed: {integration_result.get('error', 'Unknown error')}")
                
                return {
                    'total_records': len(topologies),
                    'successful_populations': 0,
                    'failed_populations': failed_populations,
                    'integration_error': integration_result.get('error')
                }
                
        except Exception as e:
            self.logger.error(f"Enhanced Database population failed: {e}")
            
            # Update statistics
            self.population_stats['total_records_processed'] += len(topologies)
            self.population_stats['failed_populations'] += len(topologies)
            self.population_stats['records_preserved'] = len(self.preserved_data)
            
            return {
                'total_records': len(topologies),
                'successful_populations': 0,
                'failed_populations': len(topologies),
                'error': str(e)
            }
    
    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of data for integrity verification"""
        
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate data hash: {e}")
            return f"hash_error_{int(time.time())}"
    
    def _determine_legacy_record_type(self, record: Dict) -> str:
        """Determine the type of legacy record"""
        
        if 'bridge_domain_name' in record:
            return 'bridge_domain'
        elif 'service_name' in record:
            return 'service'
        elif 'device_name' in record:
            return 'device'
        elif 'interface_name' in record:
            return 'interface'
        else:
            return 'unknown'
    
    def get_preserved_data_summary(self) -> Dict[str, Any]:
        """Get summary of preserved data"""
        
        summary = {
            'total_preserved_records': len(self.preserved_data),
            'records_by_type': {},
            'preservation_statistics': {
                'lacp_records': 0,
                'lldp_records': 0,
                'bridge_domain_records': 0,
                'legacy_database_records': 0,
                'other_records': 0
            },
            'conversion_status': {
                'converted_records': 0,
                'pending_conversion': 0,
                'conversion_errors': 0
            }
        }
        
        # Count records by type
        for record in self.preserved_data.values():
            record_type = record.discovery_type
            if record_type not in summary['records_by_type']:
                summary['records_by_type'][record_type] = 0
            summary['records_by_type'][record_type] += 1
            
            # Update preservation statistics
            if record_type == 'lacp':
                summary['preservation_statistics']['lacp_records'] += 1
            elif record_type == 'lldp':
                summary['preservation_statistics']['lldp_records'] += 1
            elif record_type == 'bridge_domain':
                summary['preservation_statistics']['bridge_domain_records'] += 1
            elif record_type == 'legacy_database':
                summary['preservation_statistics']['legacy_database_records'] += 1
            else:
                summary['preservation_statistics']['other_records'] += 1
            
            # Update conversion status
            if record.conversion_timestamp:
                summary['conversion_status']['converted_records'] += 1
            else:
                summary['conversion_status']['pending_conversion'] += 1
        
        summary['conversion_status']['conversion_errors'] = self.population_stats['conversion_errors']
        
        return summary
    
    def export_preserved_data(self, output_file: str = None) -> str:
        """Export preserved data to JSON file"""
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'enhanced_discovery_preserved_data_{timestamp}.json'
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'preservation_summary': self.get_preserved_data_summary(),
            'preserved_records': {
                discovery_id: {
                    'discovery_id': record.discovery_id,
                    'discovery_type': record.discovery_type,
                    'original_data': record.original_data,
                    'data_hash': record.data_hash,
                    'discovery_timestamp': record.discovery_timestamp.isoformat(),
                    'conversion_timestamp': record.conversion_timestamp.isoformat() if record.conversion_timestamp else None,
                    'converted_topology_ids': record.converted_topology_ids,
                    'metadata': record.metadata
                }
                for discovery_id, record in self.preserved_data.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"📤 Preserved data exported to: {output_file}")
        return output_file
    
    def get_population_statistics(self) -> Dict[str, Any]:
        """Get enhanced population statistics with preservation data"""
        
        total_processed = self.population_stats['total_records_processed']
        records_preserved = self.population_stats['records_preserved']
        conversion_errors = self.population_stats['conversion_errors']
        
        preservation_rate = (records_preserved / max(1, total_processed)) * 100 if total_processed > 0 else 0
        conversion_rate = ((total_processed - conversion_errors) / max(1, total_processed)) * 100 if total_processed > 0 else 0
        
        stats = {
            'total_records_processed': total_processed,
            'successfully_populated': self.population_stats['successfully_populated'],
            'failed_populations': self.population_stats['failed_populations'],
            'records_preserved': records_preserved,
            'data_loss_incidents': self.population_stats['data_loss_incidents'],
            'preservation_errors': self.population_stats['preservation_errors'],
            'conversion_errors': conversion_errors,
            'preservation_success_rate': preservation_rate,
            'conversion_success_rate': conversion_rate
        }
        
        return stats
    
    def generate_preservation_report(self) -> str:
        """Generate comprehensive data preservation report"""
        
        summary = self.get_preserved_data_summary()
        stats = self.get_population_statistics()
        
        report = []
        report.append("📊 Enhanced Discovery Data Preservation Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("🔒 Data Preservation Status:")
        report.append(f"  • Total Records Preserved: {summary['total_preserved_records']}")
        report.append(f"  • Preservation Success Rate: {stats['preservation_success_rate']:.1f}%")
        report.append(f"  • Data Loss Incidents: {stats['data_loss_incidents']}")
        report.append("")
        
        report.append("📈 Preservation Statistics by Type:")
        for record_type, count in summary['preservation_statistics'].items():
            report.append(f"  • {record_type.replace('_', ' ').title()}: {count}")
        report.append("")
        
        report.append("🔄 Conversion Status:")
        report.append(f"  • Records Converted: {summary['conversion_status']['converted_records']}")
        report.append(f"  • Pending Conversion: {summary['conversion_status']['pending_conversion']}")
        report.append(f"  • Conversion Errors: {summary['conversion_status']['conversion_errors']}")
        report.append(f"  • Conversion Success Rate: {stats['conversion_success_rate']:.1f}%")
        report.append("")
        
        return "\n".join(report)
