#!/usr/bin/env python3
"""
BD Editor Advanced Change Tracker

Advanced change tracking system with undo/redo support, change impact analysis,
and comprehensive change history management.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from .data_models import SessionError

logger = logging.getLogger(__name__)


class AdvancedChangeTracker:
    """Advanced change tracking with undo/redo support"""
    
    def __init__(self, session: Dict):
        self.session = session
        self.change_stack = session.get('changes_made', [])
        self.undo_stack = session.get('undo_stack', [])
        
        # Ensure session has required fields
        if 'changes_made' not in session:
            session['changes_made'] = []
        if 'undo_stack' not in session:
            session['undo_stack'] = []
    
    def track_change(self, change: Dict) -> str:
        """Track a change and return change ID"""
        
        try:
            change_id = self._generate_change_id()
            
            # Capture current BD state before change
            bd_state_before = self._capture_bd_state()
            
            change_record = {
                'id': change_id,
                'change': change,
                'timestamp': datetime.now().isoformat(),
                'bd_state_before': bd_state_before,
                'reversible': self._is_change_reversible(change),
                'applied': True
            }
            
            # Add to change stack
            self.change_stack.append(change_record)
            self.session['changes_made'] = self.change_stack
            
            # Clear undo stack when new change is made
            self.undo_stack.clear()
            self.session['undo_stack'] = self.undo_stack
            
            logger.info(f"Tracked change {change_id}: {change.get('description', 'Unknown change')}")
            return change_id
            
        except Exception as e:
            logger.error(f"Error tracking change: {e}")
            raise SessionError(f"Failed to track change: {e}")
    
    def undo_last_change(self) -> bool:
        """Undo the last change if possible"""
        
        try:
            if not self.change_stack:
                print("❌ No changes to undo")
                return False
            
            last_change = self.change_stack.pop()
            
            if not last_change['reversible']:
                print(f"❌ Cannot undo change: {last_change['change']['description']}")
                print("💡 This change type is not reversible")
                self.change_stack.append(last_change)  # Put it back
                return False
            
            # Restore previous BD state
            self._restore_bd_state(last_change['bd_state_before'])
            
            # Move to undo stack
            last_change['applied'] = False
            self.undo_stack.append(last_change)
            
            # Update session
            self.session['changes_made'] = self.change_stack
            self.session['undo_stack'] = self.undo_stack
            
            print(f"✅ Undid change: {last_change['change']['description']}")
            logger.info(f"Undid change {last_change['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error undoing change: {e}")
            print(f"❌ Failed to undo change: {e}")
            return False
    
    def redo_last_undo(self) -> bool:
        """Redo the last undone change"""
        
        try:
            if not self.undo_stack:
                print("❌ No changes to redo")
                return False
            
            change_to_redo = self.undo_stack.pop()
            
            # Reapply change
            self._reapply_change(change_to_redo['change'])
            
            # Move back to change stack
            change_to_redo['applied'] = True
            self.change_stack.append(change_to_redo)
            
            # Update session
            self.session['changes_made'] = self.change_stack
            self.session['undo_stack'] = self.undo_stack
            
            print(f"✅ Redid change: {change_to_redo['change']['description']}")
            logger.info(f"Redid change {change_to_redo['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error redoing change: {e}")
            print(f"❌ Failed to redo change: {e}")
            return False
    
    def get_change_history(self) -> List[Dict]:
        """Get complete change history"""
        
        history = []
        
        # Applied changes
        for change_record in self.change_stack:
            # Handle both old format (direct change) and new format (change wrapper)
            if 'change' in change_record:
                description = change_record['change']['description']
            else:
                description = change_record.get('description', 'Unknown change')
            
            history.append({
                'id': change_record.get('id', 'unknown'),
                'description': description,
                'timestamp': change_record.get('timestamp', 'unknown'),
                'status': 'applied',
                'reversible': change_record.get('reversible', True)
            })
        
        # Undone changes
        for change_record in self.undo_stack:
            # Handle both old format (direct change) and new format (change wrapper)
            if 'change' in change_record:
                description = change_record['change']['description']
            else:
                description = change_record.get('description', 'Unknown change')
            
            history.append({
                'id': change_record.get('id', 'unknown'),
                'description': description,
                'timestamp': change_record.get('timestamp', 'unknown'),
                'status': 'undone',
                'reversible': change_record.get('reversible', True)
            })
        
        # Sort by timestamp
        history.sort(key=lambda x: x['timestamp'])
        
        return history
    
    def display_change_history(self):
        """Display human-readable change history"""
        
        print(f"\n📋 CHANGE HISTORY")
        print("="*50)
        
        history = self.get_change_history()
        
        if not history:
            print("💡 No changes made yet")
            return
        
        applied_count = len([h for h in history if h['status'] == 'applied'])
        undone_count = len([h for h in history if h['status'] == 'undone'])
        
        print(f"📊 Summary: {applied_count} applied, {undone_count} undone")
        print()
        
        for i, change in enumerate(history, 1):
            status_icon = "✅" if change['status'] == 'applied' else "↶"
            reversible_icon = "🔄" if change['reversible'] else "🔒"
            
            print(f"{i:2d}. {status_icon} {change['description']}")
            print(f"     {reversible_icon} {change['timestamp'][:19]} ({change['status']})")
        
        if applied_count > 0:
            print(f"\n💡 Use 'undo' to reverse last change")
        if undone_count > 0:
            print(f"💡 Use 'redo' to reapply last undone change")
    
    def _generate_change_id(self) -> str:
        """Generate unique change ID"""
        return str(uuid.uuid4())[:8]
    
    def _capture_bd_state(self) -> Dict:
        """Capture current BD state for undo purposes"""
        
        try:
            working_copy = self.session.get('working_copy', {})
            
            # Create deep copy of current state
            state_snapshot = {
                'interfaces': json.loads(json.dumps(working_copy.get('interfaces', []))),
                'bd_data': json.loads(json.dumps({
                    k: v for k, v in working_copy.items() 
                    if k not in ['interfaces']
                })),
                'captured_at': datetime.now().isoformat()
            }
            
            return state_snapshot
            
        except Exception as e:
            logger.error(f"Error capturing BD state: {e}")
            return {}
    
    def _restore_bd_state(self, bd_state: Dict):
        """Restore BD state from snapshot"""
        
        try:
            working_copy = self.session.get('working_copy', {})
            
            # Restore interfaces
            if 'interfaces' in bd_state:
                working_copy['interfaces'] = bd_state['interfaces']
            
            # Restore BD data
            if 'bd_data' in bd_state:
                working_copy.update(bd_state['bd_data'])
            
            logger.debug("BD state restored from snapshot")
            
        except Exception as e:
            logger.error(f"Error restoring BD state: {e}")
            raise SessionError(f"Failed to restore BD state: {e}")
    
    def _is_change_reversible(self, change: Dict) -> bool:
        """Check if change can be reversed"""
        
        action = change.get('action', '')
        
        # Most interface changes are reversible
        reversible_actions = [
            'add_customer_interface',
            'add_qinq_customer_interface', 
            'add_double_tagged_customer_interface',
            'remove_customer_interface',
            'modify_customer_interface',
            'move_customer_interface'
        ]
        
        # Some actions are not easily reversible
        non_reversible_actions = [
            'deploy_changes',
            'save_to_database',
            'bulk_operation'
        ]
        
        if action in reversible_actions:
            return True
        elif action in non_reversible_actions:
            return False
        else:
            # Default to reversible for safety
            return True
    
    def _reapply_change(self, change: Dict):
        """Reapply a change (for redo functionality)"""
        
        try:
            working_copy = self.session.get('working_copy', {})
            action = change.get('action', '')
            
            if action.startswith('add_') and 'interface' in action:
                # Reapply interface addition
                interface_info = change.get('interface', {})
                if 'interfaces' not in working_copy:
                    working_copy['interfaces'] = []
                working_copy['interfaces'].append(interface_info)
                
            elif action.startswith('remove_') and 'interface' in action:
                # Reapply interface removal
                interface_info = change.get('interface', {})
                device = interface_info.get('device')
                interface = interface_info.get('interface')
                
                # Remove matching interface
                working_copy['interfaces'] = [
                    intf for intf in working_copy.get('interfaces', [])
                    if not (intf.get('device') == device and intf.get('interface') == interface)
                ]
            
            logger.debug(f"Reapplied change: {change.get('description', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error reapplying change: {e}")
            raise SessionError(f"Failed to reapply change: {e}")
    
    def get_change_statistics(self) -> Dict:
        """Get statistics about changes made"""
        
        stats = {
            'total_changes': len(self.change_stack),
            'undone_changes': len(self.undo_stack),
            'reversible_changes': sum(1 for c in self.change_stack if c.get('reversible', True)),
            'change_types': {},
            'affected_devices': set(),
            'first_change': None,
            'last_change': None
        }
        
        # Analyze change types
        for change_record in self.change_stack:
            # Handle both old format (direct change) and new format (change wrapper)
            if 'change' in change_record:
                action = change_record['change'].get('action', 'unknown')
            else:
                action = change_record.get('action', 'unknown')
            
            stats['change_types'][action] = stats['change_types'].get(action, 0) + 1
            
            # Track affected devices
            if 'change' in change_record:
                interface_info = change_record['change'].get('interface', {})
            else:
                interface_info = change_record.get('interface', {})
            
            device = interface_info.get('device')
            if device:
                stats['affected_devices'].add(device)
        
        # Get first and last change timestamps
        if self.change_stack:
            stats['first_change'] = self.change_stack[0]['timestamp']
            stats['last_change'] = self.change_stack[-1]['timestamp']
        
        # Convert set to list for JSON serialization
        stats['affected_devices'] = list(stats['affected_devices'])
        
        return stats


# Convenience functions
def create_change_tracker(session: Dict) -> AdvancedChangeTracker:
    """Convenience function to create change tracker"""
    return AdvancedChangeTracker(session)


def track_bd_change(session: Dict, change: Dict) -> str:
    """Convenience function to track a change"""
    tracker = AdvancedChangeTracker(session)
    return tracker.track_change(change)
