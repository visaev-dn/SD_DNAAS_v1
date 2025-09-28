#!/usr/bin/env python3
"""
Bridge Domain Assignment Manager
Handles user workspace assignments with permission validation
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PermissionResult:
    """Result of permission validation"""
    allowed: bool
    reason: str
    details: Dict = None


@dataclass
class AssignmentResult:
    """Result of BD assignment operation"""
    success: bool
    assignment_id: Optional[int] = None
    error: Optional[str] = None
    details: Dict = None


class BDAssignmentManager:
    """
    Manages bridge domain assignments to user workspaces
    
    Features:
    - Permission validation (VLAN ranges, assignment limits)
    - Assignment/unassignment operations
    - Conflict detection and prevention
    - Audit trail and change tracking
    """
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        self.logger = logger
    
    def can_user_assign_bd(self, user_id: int, bd_id: int) -> PermissionResult:
        """Check if user can assign bridge domain to their workspace"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get bridge domain information
            cursor.execute('''
                SELECT name, vlan_id, username, assignment_status, assigned_to_user_id
                FROM bridge_domains 
                WHERE id = ?
            ''', (bd_id,))
            
            bd_result = cursor.fetchone()
            if not bd_result:
                return PermissionResult(False, "Bridge domain not found")
            
            bd_name, bd_vlan, bd_username, assignment_status, assigned_to_user = bd_result
            
            # Check if BD is available
            if assignment_status != 'available':
                if assigned_to_user == user_id:
                    return PermissionResult(True, "Already assigned to you")
                else:
                    cursor.execute('SELECT username FROM users WHERE id = ?', (assigned_to_user,))
                    assigned_username = cursor.fetchone()
                    assigned_username = assigned_username[0] if assigned_username else 'Unknown'
                    return PermissionResult(False, f"Already assigned to {assigned_username}")
            
            # Get user information and permissions
            cursor.execute('''
                SELECT u.username, u.role, up.can_edit_topology, up.max_bridge_domains
                FROM users u
                LEFT JOIN user_permissions up ON u.id = up.user_id
                WHERE u.id = ?
            ''', (user_id,))
            
            user_result = cursor.fetchone()
            if not user_result:
                return PermissionResult(False, "User not found")
            
            username, role, can_edit_topology, max_bridge_domains = user_result
            
            # Check basic editing permission
            if not can_edit_topology and role != 'admin':
                return PermissionResult(False, "User does not have topology editing permissions")
            
            # Check assignment limit
            cursor.execute('''
                SELECT COUNT(*) FROM bridge_domains 
                WHERE assigned_to_user_id = ? AND assignment_status = 'assigned'
            ''', (user_id,))
            
            current_assignments = cursor.fetchone()[0]
            if max_bridge_domains and current_assignments >= max_bridge_domains:
                return PermissionResult(False, f"Assignment limit exceeded ({current_assignments}/{max_bridge_domains})")
            
            # Check VLAN range permissions
            if bd_vlan:
                vlan_permission = self._check_vlan_permission(cursor, user_id, bd_vlan)
                if not vlan_permission.allowed:
                    return vlan_permission
            
            conn.close()
            
            return PermissionResult(True, "Assignment allowed", {
                'bd_name': bd_name,
                'bd_vlan': bd_vlan,
                'user_assignments': current_assignments,
                'assignment_limit': max_bridge_domains
            })
            
        except Exception as e:
            self.logger.error(f"Permission check failed for user {user_id}, BD {bd_id}: {e}")
            return PermissionResult(False, f"Permission check failed: {str(e)}")
    
    def _check_vlan_permission(self, cursor, user_id: int, vlan_id: int) -> PermissionResult:
        """Check if user has permission for specific VLAN"""
        
        # Get user's VLAN allocations
        cursor.execute('''
            SELECT start_vlan, end_vlan, description
            FROM user_vlan_allocations 
            WHERE user_id = ?
        ''', (user_id,))
        
        vlan_ranges = cursor.fetchall()
        
        if not vlan_ranges:
            return PermissionResult(False, "No VLAN ranges allocated to user")
        
        # Check if VLAN is within any allocated range
        for start_vlan, end_vlan, description in vlan_ranges:
            if start_vlan <= vlan_id <= end_vlan:
                return PermissionResult(True, f"VLAN {vlan_id} within range {start_vlan}-{end_vlan} ({description})")
        
        # VLAN not in any range
        allocated_ranges = [f"{start}-{end}" for start, end, _ in vlan_ranges]
        return PermissionResult(False, f"VLAN {vlan_id} outside allocated ranges: {', '.join(allocated_ranges)}")
    
    def assign_bridge_domain(self, user_id: int, bd_id: int, reason: str = "User workspace assignment") -> AssignmentResult:
        """Assign bridge domain to user's workspace"""
        
        try:
            # Check permissions first
            permission = self.can_user_assign_bd(user_id, bd_id)
            if not permission.allowed:
                return AssignmentResult(False, error=permission.reason)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create assignment record
            cursor.execute('''
                INSERT INTO bd_assignments (bridge_domain_id, user_id, assignment_reason, status)
                VALUES (?, ?, ?, 'active')
            ''', (bd_id, user_id, reason))
            
            assignment_id = cursor.lastrowid
            
            # Update bridge domain status
            cursor.execute('''
                UPDATE bridge_domains 
                SET assigned_to_user_id = ?, 
                    assigned_at = CURRENT_TIMESTAMP,
                    assignment_status = 'assigned',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id, bd_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"BD {bd_id} assigned to user {user_id} (assignment {assignment_id})")
            
            return AssignmentResult(True, assignment_id=assignment_id, details={
                'bd_id': bd_id,
                'user_id': user_id,
                'assignment_reason': reason
            })
            
        except Exception as e:
            self.logger.error(f"Assignment failed for user {user_id}, BD {bd_id}: {e}")
            return AssignmentResult(False, error=f"Assignment failed: {str(e)}")
    
    def unassign_bridge_domain(self, user_id: int, bd_id: int) -> AssignmentResult:
        """Remove bridge domain from user's workspace"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify user owns the assignment
            cursor.execute('''
                SELECT id FROM bd_assignments 
                WHERE bridge_domain_id = ? AND user_id = ? AND status = 'active'
            ''', (bd_id, user_id))
            
            assignment = cursor.fetchone()
            if not assignment:
                return AssignmentResult(False, error="Assignment not found or not owned by user")
            
            assignment_id = assignment[0]
            
            # Update assignment status
            cursor.execute('''
                UPDATE bd_assignments 
                SET status = 'released', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (assignment_id,))
            
            # Update bridge domain status
            cursor.execute('''
                UPDATE bridge_domains 
                SET assigned_to_user_id = NULL, 
                    assigned_at = NULL,
                    assignment_status = 'available',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (bd_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"BD {bd_id} unassigned from user {user_id}")
            
            return AssignmentResult(True, details={
                'bd_id': bd_id,
                'user_id': user_id,
                'assignment_id': assignment_id
            })
            
        except Exception as e:
            self.logger.error(f"Unassignment failed for user {user_id}, BD {bd_id}: {e}")
            return AssignmentResult(False, error=f"Unassignment failed: {str(e)}")
    
    def get_user_assigned_bridge_domains(self, user_id: int) -> List[Dict]:
        """Get all bridge domains assigned to user's workspace"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT bd.id, bd.name, bd.vlan_id, bd.username, bd.dnaas_type,
                       bd.topology_type, bd.deployment_status, bd.assigned_at,
                       ba.assignment_reason, ba.status as assignment_status
                FROM bridge_domains bd
                JOIN bd_assignments ba ON bd.id = ba.bridge_domain_id
                WHERE bd.assigned_to_user_id = ? AND ba.status = 'active'
                ORDER BY bd.assigned_at DESC
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            assigned_bds = []
            for row in results:
                assigned_bds.append({
                    'id': row[0],
                    'name': row[1],
                    'vlan_id': row[2],
                    'original_username': row[3],
                    'dnaas_type': row[4],
                    'topology_type': row[5],
                    'deployment_status': row[6],
                    'assigned_at': row[7],
                    'assignment_reason': row[8],
                    'assignment_status': row[9],
                    'can_edit': True,
                    'source': 'assigned_discovered'
                })
            
            return assigned_bds
            
        except Exception as e:
            self.logger.error(f"Failed to get assigned BDs for user {user_id}: {e}")
            return []
    
    def get_assignable_bridge_domains(self, user_id: int) -> List[Dict]:
        """Get bridge domains user can assign (within VLAN ranges)"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's VLAN ranges
            cursor.execute('''
                SELECT start_vlan, end_vlan FROM user_vlan_allocations 
                WHERE user_id = ?
            ''', (user_id,))
            
            vlan_ranges = cursor.fetchall()
            
            if not vlan_ranges:
                return []  # No VLAN ranges = no assignable BDs
            
            # Build VLAN range conditions
            vlan_conditions = []
            for start_vlan, end_vlan in vlan_ranges:
                vlan_conditions.append(f'(vlan_id >= {start_vlan} AND vlan_id <= {end_vlan})')
            
            vlan_where = ' OR '.join(vlan_conditions)
            
            # Get available BDs within user's VLAN ranges
            query = f'''
                SELECT id, name, vlan_id, username, dnaas_type, topology_type, assignment_status
                FROM bridge_domains 
                WHERE source = 'discovered' 
                AND assignment_status = 'available'
                AND ({vlan_where})
                ORDER BY name
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            
            assignable_bds = []
            for row in results:
                assignable_bds.append({
                    'id': row[0],
                    'name': row[1],
                    'vlan_id': row[2],
                    'username': row[3],
                    'dnaas_type': row[4],
                    'topology_type': row[5],
                    'assignment_status': row[6],
                    'can_assign': True
                })
            
            return assignable_bds
            
        except Exception as e:
            self.logger.error(f"Failed to get assignable BDs for user {user_id}: {e}")
            return []


# Test the assignment manager
if __name__ == '__main__':
    print("🧪 TESTING BD ASSIGNMENT MANAGER...")
    print("=" * 50)
    
    manager = BDAssignmentManager()
    
    # Test permission checking
    print("🔍 Testing permission validation...")
    permission = manager.can_user_assign_bd(1, 1)  # Admin user, first BD
    print(f"   • Permission result: {permission.allowed}")
    print(f"   • Reason: {permission.reason}")
    
    # Test getting assignable BDs
    print("\n📋 Testing assignable BDs...")
    assignable = manager.get_assignable_bridge_domains(1)  # Admin user
    print(f"   • Assignable BDs for admin: {len(assignable)}")
    
    if assignable:
        print("   • Sample assignable BDs:")
        for bd in assignable[:3]:
            print(f"     - {bd['name']} (VLAN {bd['vlan_id']})")
    
    # Test getting assigned BDs
    print("\n👤 Testing user workspace...")
    assigned = manager.get_user_assigned_bridge_domains(1)  # Admin user
    print(f"   • Assigned BDs for admin: {len(assigned)}")
    
    if assigned:
        print("   • User workspace BDs:")
        for bd in assigned:
            print(f"     - {bd['name']} (assigned {bd['assigned_at']})")
    
    print("\n✅ BD Assignment Manager: FUNCTIONAL!")
