#!/usr/bin/env python3
"""
Unified Database Manager
=======================

Single, clean interface for all bridge domain database operations.
Replaces fragmented database managers with unified approach.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BridgeDomain:
    """Unified bridge domain data structure"""
    id: Optional[int]
    name: str
    source: str  # 'discovered', 'created', 'imported', 'edited'
    username: Optional[str]
    vlan_id: Optional[int]
    topology_type: Optional[str]
    dnaas_type: Optional[str]
    configuration_data: Dict[str, Any]
    deployment_status: str = 'pending'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class BridgeDomainInterface:
    """Bridge domain interface information"""
    device_name: str
    interface_name: str
    interface_type: str
    vlan_id: Optional[int]
    raw_cli_commands: List[str]

@dataclass
class DeploymentRecord:
    """Bridge domain deployment record"""
    bridge_domain_id: int
    deployment_type: str
    deployment_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    deployment_log: Optional[str]

class UnifiedDatabaseManager:
    """
    Unified database manager for all bridge domain operations.
    
    Provides clean, simple interface for:
    - Bridge domain CRUD operations
    - Discovery data management
    - Configuration storage
    - Deployment tracking
    """
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        self.logger = logger
    
    # =========================================================================
    # BRIDGE DOMAIN OPERATIONS
    # =========================================================================
    
    def save_bridge_domain(self, bd: BridgeDomain) -> int:
        """Save bridge domain to unified schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if bd.id:
                # Update existing
                cursor.execute("""
                    UPDATE bridge_domains 
                    SET name = ?, username = ?, vlan_id = ?, topology_type = ?,
                        dnaas_type = ?, configuration_data = ?, deployment_status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    bd.name, bd.username, bd.vlan_id, bd.topology_type,
                    bd.dnaas_type, json.dumps(bd.configuration_data), bd.deployment_status,
                    bd.id
                ))
                bd_id = bd.id
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO bridge_domains 
                    (name, source, username, vlan_id, topology_type, dnaas_type,
                     configuration_data, deployment_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    bd.name, bd.source, bd.username, bd.vlan_id, bd.topology_type,
                    bd.dnaas_type, json.dumps(bd.configuration_data), bd.deployment_status
                ))
                bd_id = cursor.lastrowid
            
            conn.commit()
            return bd_id
            
        finally:
            conn.close()
    
    def get_bridge_domain(self, bd_id: int) -> Optional[BridgeDomain]:
        """Get bridge domain by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM bridge_domains WHERE id = ?", (bd_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_bridge_domain(cursor, row)
            return None
            
        finally:
            conn.close()
    
    def get_bridge_domain_by_name(self, name: str) -> Optional[BridgeDomain]:
        """Get bridge domain by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM bridge_domains WHERE name = ? AND is_latest_version = TRUE", (name,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_bridge_domain(cursor, row)
            return None
            
        finally:
            conn.close()
    
    def list_bridge_domains(self, filters: Dict[str, Any] = None) -> List[BridgeDomain]:
        """List bridge domains with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM bridge_domains WHERE is_latest_version = TRUE"
            params = []
            
            if filters:
                if 'source' in filters:
                    query += " AND source = ?"
                    params.append(filters['source'])
                if 'username' in filters:
                    query += " AND username = ?"
                    params.append(filters['username'])
                if 'deployment_status' in filters:
                    query += " AND deployment_status = ?"
                    params.append(filters['deployment_status'])
                if 'dnaas_type' in filters:
                    query += " AND dnaas_type = ?"
                    params.append(filters['dnaas_type'])
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_bridge_domain(cursor, row) for row in rows]
            
        finally:
            conn.close()
    
    def delete_bridge_domain(self, bd_id: int) -> bool:
        """Delete bridge domain (mark as archived)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE bridge_domains 
                SET deployment_status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (bd_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    # =========================================================================
    # DISCOVERY DATA OPERATIONS
    # =========================================================================
    
    def save_discovery_results(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Save discovery results to unified schema"""
        self.logger.info("🚀 Saving discovery results to unified schema...")
        
        results = {
            'total_bridge_domains': 0,
            'saved_successfully': 0,
            'failed_saves': 0,
            'errors': []
        }
        
        try:
            bridge_domains = discovery_results.get('bridge_domains', {})
            results['total_bridge_domains'] = len(bridge_domains)
            
            for bd_name, bd_data in bridge_domains.items():
                try:
                    # Extract data for unified schema
                    bridge_analysis = bd_data.get('bridge_domain_analysis', {})
                    
                    bd = BridgeDomain(
                        id=None,
                        name=bd_name,
                        source='discovered',
                        username=bd_data.get('detected_username'),
                        vlan_id=bd_data.get('detected_vlan'),
                        topology_type=bd_data.get('topology_type'),
                        dnaas_type=bridge_analysis.get('dnaas_type'),
                        configuration_data=bd_data,
                        deployment_status='discovered'
                    )
                    
                    self.save_bridge_domain(bd)
                    results['saved_successfully'] += 1
                    
                except Exception as e:
                    results['failed_saves'] += 1
                    results['errors'].append(f"Failed to save {bd_name}: {str(e)}")
                    self.logger.error(f"❌ Failed to save {bd_name}: {e}")
            
            self.logger.info(f"✅ Discovery results saved: {results['saved_successfully']}/{results['total_bridge_domains']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Discovery save failed: {e}")
            results['errors'].append(f"Discovery save failed: {str(e)}")
            return results
    
    # =========================================================================
    # DEPLOYMENT OPERATIONS
    # =========================================================================
    
    def record_deployment(self, bd_id: int, deployment_type: str, status: str, log: str = "") -> int:
        """Record bridge domain deployment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO bridge_domain_deployments 
                (bridge_domain_id, deployment_type, deployment_status, deployment_log, deployed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (bd_id, deployment_type, status, log, 1))
            
            # Update bridge domain status
            if status == 'success':
                cursor.execute("""
                    UPDATE bridge_domains 
                    SET deployment_status = 'deployed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (bd_id,))
            
            conn.commit()
            return cursor.lastrowid
            
        finally:
            conn.close()
    
    def get_deployment_history(self, bd_id: int) -> List[DeploymentRecord]:
        """Get deployment history for bridge domain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT bridge_domain_id, deployment_type, deployment_status,
                       started_at, completed_at, deployment_log
                FROM bridge_domain_deployments 
                WHERE bridge_domain_id = ?
                ORDER BY started_at DESC
            """, (bd_id,))
            
            rows = cursor.fetchall()
            
            deployments = []
            for row in rows:
                deployments.append(DeploymentRecord(
                    bridge_domain_id=row[0],
                    deployment_type=row[1],
                    deployment_status=row[2],
                    started_at=datetime.fromisoformat(row[3]) if row[3] else None,
                    completed_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    deployment_log=row[5]
                ))
            
            return deployments
            
        finally:
            conn.close()
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _row_to_bridge_domain(self, cursor, row) -> BridgeDomain:
        """Convert database row to BridgeDomain object"""
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        
        return BridgeDomain(
            id=data['id'],
            name=data['name'],
            source=data['source'],
            username=data.get('username'),
            vlan_id=data.get('vlan_id'),
            topology_type=data.get('topology_type'),
            dnaas_type=data.get('dnaas_type'),
            configuration_data=json.loads(data.get('configuration_data', '{}')),
            deployment_status=data.get('deployment_status', 'pending'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Bridge domain counts
            cursor.execute("SELECT COUNT(*) FROM bridge_domains WHERE is_latest_version = TRUE")
            stats['total_bridge_domains'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT source, COUNT(*) FROM bridge_domains WHERE is_latest_version = TRUE GROUP BY source")
            stats['by_source'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT deployment_status, COUNT(*) FROM bridge_domains WHERE is_latest_version = TRUE GROUP BY deployment_status")
            stats['by_status'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT dnaas_type, COUNT(*) FROM bridge_domains WHERE is_latest_version = TRUE GROUP BY dnaas_type")
            stats['by_dnaas_type'] = dict(cursor.fetchall())
            
            return stats
            
        finally:
            conn.close()

# Compatibility function for existing code
def create_unified_database_manager(db_path: str = "instance/lab_automation.db") -> UnifiedDatabaseManager:
    """Factory function for creating unified database manager"""
    return UnifiedDatabaseManager(db_path)


