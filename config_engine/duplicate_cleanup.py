#!/usr/bin/env python3
"""
Duplicate Cleanup for Service Signature-Based Deduplication
Cleans up existing duplicates using the new service signature system
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

from config_engine.phase1_database import create_phase1_database_manager
from config_engine.service_signature import ServiceSignatureGenerator
from config_engine.phase1_database.models import Phase1TopologyData

logger = logging.getLogger(__name__)


class DuplicateCleanup:
    """
    Handles cleanup of duplicate bridge domains using service signatures
    """
    
    def __init__(self):
        self.db_manager = create_phase1_database_manager()
        self.signature_generator = ServiceSignatureGenerator()
        self.cleanup_stats = {
            'total_analyzed': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'services_consolidated': 0,
            'errors': 0
        }
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_duplicates(self) -> Dict:
        """
        Analyze existing duplicates by VLAN ID and bridge domain name
        
        Returns:
            Dictionary with duplicate analysis results
        """
        self.logger.info("🔍 Analyzing existing duplicates...")
        
        try:
            with self.db_manager.SessionLocal() as session:
                from sqlalchemy import func
                
                # Find VLAN-based duplicates
                vlan_duplicates = session.query(
                    Phase1TopologyData.vlan_id,
                    func.count(Phase1TopologyData.id).label('count')
                ).group_by(
                    Phase1TopologyData.vlan_id
                ).having(
                    func.count(Phase1TopologyData.id) > 1
                ).all()
                
                # Find name-based duplicates
                name_duplicates = session.query(
                    Phase1TopologyData.bridge_domain_name,
                    func.count(Phase1TopologyData.id).label('count')
                ).group_by(
                    Phase1TopologyData.bridge_domain_name
                ).having(
                    func.count(Phase1TopologyData.id) > 1
                ).all()
                
                analysis = {
                    'vlan_duplicates': len(vlan_duplicates),
                    'name_duplicates': len(name_duplicates),
                    'total_duplicate_vlans': sum(count - 1 for _, count in vlan_duplicates),
                    'total_duplicate_names': sum(count - 1 for _, count in name_duplicates),
                    'vlan_groups': vlan_duplicates,
                    'name_groups': name_duplicates
                }
                
                self.logger.info(f"✅ Analysis complete: {analysis['vlan_duplicates']} VLAN groups, {analysis['name_duplicates']} name groups")
                return analysis
                
        except Exception as e:
            self.logger.error(f"❌ Duplicate analysis failed: {e}")
            return {}
    
    def generate_signatures_for_existing_data(self) -> Dict[str, List[int]]:
        """
        Generate service signatures for all existing topologies
        
        Returns:
            Dictionary mapping service signatures to topology IDs
        """
        self.logger.info("🎯 Generating service signatures for existing data...")
        
        signature_groups = defaultdict(list)
        
        try:
            with self.db_manager.SessionLocal() as session:
                # Get all topologies without service signatures
                topologies = session.query(Phase1TopologyData).filter(
                    Phase1TopologyData.service_signature.is_(None)
                ).all()
                
                self.logger.info(f"📊 Processing {len(topologies)} topologies without signatures...")
                
                processed = 0
                for topology in topologies:
                    try:
                        # Generate service signature based on VLAN and name analysis
                        signature = self._generate_signature_for_db_topology(topology)
                        
                        if signature:
                            signature_groups[signature].append(topology.id)
                            
                            # Update the database record with the signature
                            topology.service_signature = signature
                            topology.signature_classification = self._classify_topology(topology)
                            topology.signature_confidence = 0.95  # High confidence for VLAN-based signatures
                            
                        processed += 1
                        if processed % 100 == 0:
                            self.logger.info(f"   Processed {processed}/{len(topologies)} topologies...")
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to generate signature for topology {topology.id}: {e}")
                        self.cleanup_stats['errors'] += 1
                
                # Commit the signature updates
                session.commit()
                self.logger.info(f"✅ Generated signatures for {processed} topologies")
                
                # Return only groups with duplicates
                duplicate_signatures = {sig: ids for sig, ids in signature_groups.items() if len(ids) > 1}
                self.logger.info(f"🎯 Found {len(duplicate_signatures)} service signatures with duplicates")
                
                return duplicate_signatures
                
        except Exception as e:
            self.logger.error(f"❌ Signature generation failed: {e}")
            return {}
    
    def _generate_signature_for_db_topology(self, topology: Phase1TopologyData) -> str:
        """Generate service signature for a database topology record"""
        try:
            # Extract username from bridge domain name
            username = self._extract_username(topology.bridge_domain_name)
            
            if topology.vlan_id and topology.vlan_id > 0:
                # VLAN-based signature
                if username and topology.bridge_domain_name.startswith('l_'):
                    # Local scope
                    return f"local_{username}_vlan_{topology.vlan_id}"
                else:
                    # Global scope  
                    return f"global_vlan_{topology.vlan_id}"
            else:
                # Port-mode or unknown VLAN
                if username:
                    return f"portmode_{username}"
                else:
                    # Fallback to bridge domain name hash
                    import hashlib
                    name_hash = hashlib.md5(topology.bridge_domain_name.encode()).hexdigest()[:8]
                    return f"unknown_{name_hash}"
                    
        except Exception as e:
            self.logger.warning(f"Failed to generate signature for {topology.bridge_domain_name}: {e}")
            return None
    
    def _extract_username(self, bridge_domain_name: str) -> str:
        """Extract username from bridge domain name"""
        try:
            # Handle common patterns: g_username_*, l_username_*, etc.
            if '_' in bridge_domain_name:
                parts = bridge_domain_name.split('_')
                if len(parts) >= 2 and parts[0] in ['g', 'l']:
                    return parts[1]
                elif len(parts) >= 1:
                    return parts[0]
            return bridge_domain_name.split('_')[0] if '_' in bridge_domain_name else bridge_domain_name
        except:
            return 'unknown'
    
    def _classify_topology(self, topology: Phase1TopologyData) -> str:
        """Classify topology based on naming and VLAN patterns"""
        name = topology.bridge_domain_name.lower()
        
        if name.startswith('l_'):
            return 'local_scope'
        elif name.startswith('g_'):
            return 'global_scope'
        elif 'qinq' in name or 'double' in name:
            return 'qinq_service'
        elif 'portmode' in name or topology.vlan_id is None:
            return 'port_mode'
        else:
            return 'vlan_service'
    
    def consolidate_duplicates(self, signature_groups: Dict[str, List[int]]) -> Dict:
        """
        Consolidate duplicate topologies based on service signatures
        
        Args:
            signature_groups: Dictionary mapping signatures to topology ID lists
            
        Returns:
            Dictionary with consolidation results
        """
        self.logger.info(f"🔗 Consolidating {len(signature_groups)} service signature groups...")
        
        consolidation_results = {
            'consolidated_services': 0,
            'removed_duplicates': 0,
            'consolidation_details': []
        }
        
        try:
            with self.db_manager.SessionLocal() as session:
                for signature, topology_ids in signature_groups.items():
                    if len(topology_ids) <= 1:
                        continue
                    
                    # Get all topologies for this signature
                    topologies = session.query(Phase1TopologyData).filter(
                        Phase1TopologyData.id.in_(topology_ids)
                    ).order_by(Phase1TopologyData.discovered_at.desc()).all()
                    
                    if len(topologies) <= 1:
                        continue
                    
                    # Keep the most recent one, mark others for removal
                    primary_topology = topologies[0]  # Most recent
                    duplicates_to_remove = topologies[1:]  # Older ones
                    
                    # Update primary topology with consolidation info
                    primary_topology.discovery_count = len(topologies)
                    primary_topology.review_required = True
                    primary_topology.review_reason = f"Consolidated {len(duplicates_to_remove)} duplicates"
                    
                    # Log consolidation details
                    consolidation_detail = {
                        'signature': signature,
                        'primary_id': primary_topology.id,
                        'primary_name': primary_topology.bridge_domain_name,
                        'removed_ids': [t.id for t in duplicates_to_remove],
                        'removed_names': [t.bridge_domain_name for t in duplicates_to_remove],
                        'consolidation_count': len(duplicates_to_remove)
                    }
                    consolidation_results['consolidation_details'].append(consolidation_detail)
                    
                    # Remove duplicates (mark as inactive or delete)
                    for dup in duplicates_to_remove:
                        session.delete(dup)
                    
                    consolidation_results['consolidated_services'] += 1
                    consolidation_results['removed_duplicates'] += len(duplicates_to_remove)
                    
                    self.logger.info(f"   ✅ Consolidated {signature}: kept ID {primary_topology.id}, removed {len(duplicates_to_remove)} duplicates")
                
                # Commit all changes
                session.commit()
                self.logger.info(f"🎯 Consolidation complete: {consolidation_results['consolidated_services']} services consolidated")
                
                return consolidation_results
                
        except Exception as e:
            self.logger.error(f"❌ Consolidation failed: {e}")
            return consolidation_results
    
    def run_full_cleanup(self) -> Dict:
        """
        Run the complete duplicate cleanup process
        
        Returns:
            Dictionary with cleanup results
        """
        self.logger.info("🚀 Starting full duplicate cleanup process...")
        
        try:
            # Step 1: Analyze existing duplicates
            analysis = self.analyze_duplicates()
            
            # Step 2: Generate service signatures
            signature_groups = self.generate_signatures_for_existing_data()
            
            # Step 3: Consolidate duplicates
            consolidation_results = self.consolidate_duplicates(signature_groups)
            
            # Step 4: Final statistics
            final_results = {
                'analysis': analysis,
                'signature_groups': len(signature_groups),
                'consolidation': consolidation_results,
                'stats': self.cleanup_stats
            }
            
            self.logger.info("🎯 Full duplicate cleanup completed!")
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ Full cleanup failed: {e}")
            return {'error': str(e)}


def run_duplicate_cleanup():
    """Run the duplicate cleanup process"""
    cleanup = DuplicateCleanup()
    return cleanup.run_full_cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧹 Service Signature-Based Duplicate Cleanup")
    print("=" * 50)
    
    results = run_duplicate_cleanup()
    
    if 'error' not in results:
        print("✅ Cleanup completed successfully!")
        print(f"📊 Results: {results}")
    else:
        print(f"❌ Cleanup failed: {results['error']}")
