#!/usr/bin/env python3
"""
BD Editor Performance Monitor

Monitors and tracks BD editor performance to ensure operations
meet requirements and identify optimization opportunities.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List
from .data_models import PerformanceError

logger = logging.getLogger(__name__)


class BDEditorPerformanceMonitor:
    """Monitor and track BD editor performance"""
    
    def __init__(self):
        self.metrics = {
            'menu_generation_times': [],
            'interface_analysis_times': [],
            'validation_times': [],
            'preview_generation_times': []
        }
        
        # Performance requirements (from implementation plan)
        self.requirements = {
            'menu_generation_max_seconds': 1.0,
            'interface_analysis_max_seconds': 2.0,
            'preview_generation_max_seconds': 3.0,
            'validation_max_seconds': 1.0
        }
    
    def track_menu_generation(self, bd_type: str, interface_count: int, duration: float):
        """Track menu generation performance"""
        
        metric = {
            'bd_type': bd_type,
            'interface_count': interface_count,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat(),
            'meets_requirement': duration <= self.requirements['menu_generation_max_seconds']
        }
        
        self.metrics['menu_generation_times'].append(metric)
        
        # Check performance requirement
        if duration > self.requirements['menu_generation_max_seconds']:
            warning = f"Menu generation slow: {duration:.2f}s for {bd_type} (requirement: {self.requirements['menu_generation_max_seconds']}s)"
            logger.warning(warning)
            print(f"⚠️  {warning}")
        else:
            logger.debug(f"Menu generation performance OK: {duration:.2f}s for {bd_type}")
    
    def track_interface_analysis(self, interface_count: int, duration: float):
        """Track interface analysis performance"""
        
        metric = {
            'interface_count': interface_count,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat(),
            'meets_requirement': duration <= self.requirements['interface_analysis_max_seconds']
        }
        
        self.metrics['interface_analysis_times'].append(metric)
        
        # Check performance requirement
        if duration > self.requirements['interface_analysis_max_seconds']:
            warning = f"Interface analysis slow: {duration:.2f}s for {interface_count} interfaces (requirement: {self.requirements['interface_analysis_max_seconds']}s)"
            logger.warning(warning)
            print(f"⚠️  {warning}")
        else:
            logger.debug(f"Interface analysis performance OK: {duration:.2f}s for {interface_count} interfaces")
    
    def track_validation(self, validation_type: str, duration: float):
        """Track validation performance"""
        
        metric = {
            'validation_type': validation_type,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat(),
            'meets_requirement': duration <= self.requirements['validation_max_seconds']
        }
        
        self.metrics['validation_times'].append(metric)
        
        # Check performance requirement
        if duration > self.requirements['validation_max_seconds']:
            warning = f"Validation slow: {duration:.2f}s for {validation_type} (requirement: {self.requirements['validation_max_seconds']}s)"
            logger.warning(warning)
            print(f"⚠️  {warning}")
    
    def track_preview_generation(self, change_count: int, duration: float):
        """Track preview generation performance"""
        
        metric = {
            'change_count': change_count,
            'duration_ms': duration * 1000,
            'timestamp': datetime.now().isoformat(),
            'meets_requirement': duration <= self.requirements['preview_generation_max_seconds']
        }
        
        self.metrics['preview_generation_times'].append(metric)
        
        # Check performance requirement
        if duration > self.requirements['preview_generation_max_seconds']:
            warning = f"Preview generation slow: {duration:.2f}s for {change_count} changes (requirement: {self.requirements['preview_generation_max_seconds']}s)"
            logger.warning(warning)
            print(f"⚠️  {warning}")
    
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'requirements': self.requirements,
            'metrics_summary': {}
        }
        
        # Analyze menu generation performance
        menu_times = [m['duration_ms'] for m in self.metrics['menu_generation_times']]
        if menu_times:
            report['metrics_summary']['menu_generation'] = {
                'avg_time_ms': sum(menu_times) / len(menu_times),
                'max_time_ms': max(menu_times),
                'min_time_ms': min(menu_times),
                'samples': len(menu_times),
                'requirement_violations': sum(1 for m in self.metrics['menu_generation_times'] if not m['meets_requirement'])
            }
        
        # Analyze interface analysis performance
        analysis_times = [m['duration_ms'] for m in self.metrics['interface_analysis_times']]
        if analysis_times:
            report['metrics_summary']['interface_analysis'] = {
                'avg_time_ms': sum(analysis_times) / len(analysis_times),
                'max_time_ms': max(analysis_times),
                'min_time_ms': min(analysis_times),
                'samples': len(analysis_times),
                'requirement_violations': sum(1 for m in self.metrics['interface_analysis_times'] if not m['meets_requirement'])
            }
        
        # Analyze validation performance
        validation_times = [m['duration_ms'] for m in self.metrics['validation_times']]
        if validation_times:
            report['metrics_summary']['validation'] = {
                'avg_time_ms': sum(validation_times) / len(validation_times),
                'max_time_ms': max(validation_times),
                'min_time_ms': min(validation_times),
                'samples': len(validation_times),
                'requirement_violations': sum(1 for m in self.metrics['validation_times'] if not m['meets_requirement'])
            }
        
        # Analyze preview generation performance
        preview_times = [m['duration_ms'] for m in self.metrics['preview_generation_times']]
        if preview_times:
            report['metrics_summary']['preview_generation'] = {
                'avg_time_ms': sum(preview_times) / len(preview_times),
                'max_time_ms': max(preview_times),
                'min_time_ms': min(preview_times),
                'samples': len(preview_times),
                'requirement_violations': sum(1 for m in self.metrics['preview_generation_times'] if not m['meets_requirement'])
            }
        
        return report
    
    def display_performance_summary(self):
        """Display human-readable performance summary"""
        
        report = self.get_performance_report()
        
        print(f"\n📊 BD EDITOR PERFORMANCE SUMMARY")
        print("="*50)
        
        for operation, metrics in report['metrics_summary'].items():
            if metrics['samples'] > 0:
                avg_time = metrics['avg_time_ms']
                max_time = metrics['max_time_ms']
                violations = metrics['requirement_violations']
                samples = metrics['samples']
                
                print(f"\n🔍 {operation.replace('_', ' ').title()}:")
                print(f"   Average: {avg_time:.1f}ms")
                print(f"   Maximum: {max_time:.1f}ms")
                print(f"   Samples: {samples}")
                
                if violations > 0:
                    print(f"   ⚠️  Requirement violations: {violations}/{samples}")
                else:
                    print(f"   ✅ All samples meet requirements")
    
    def _get_bd_data_for_editing(self, bd_name: str) -> Dict:
        """Get BD data for editing (simplified for Phase 1)"""
        
        try:
            # Get BD from database
            bd_data = self.db_manager.get_bridge_domain_by_name(bd_name)
            
            if not bd_data:
                raise ValueError(f"BD {bd_name} not found")
            
            # Parse discovery data
            discovery_data = bd_data.get('discovery_data', '{}')
            if isinstance(discovery_data, str):
                discovery_data = json.loads(discovery_data)
            
            return {
                'id': bd_data.get('id'),
                'name': bd_data['name'],
                'username': bd_data.get('username'),
                'vlan_id': bd_data.get('vlan_id'),
                'dnaas_type': bd_data.get('dnaas_type'),
                'topology_type': bd_data.get('topology_type'),
                'devices': discovery_data.get('devices', {}),
                'source': bd_data.get('source')
            }
            
        except Exception as e:
            logger.error(f"Error getting BD data for {bd_name}: {e}")
            raise


# Context manager for performance tracking
class PerformanceTracker:
    """Context manager for tracking operation performance"""
    
    def __init__(self, monitor: BDEditorPerformanceMonitor, operation: str, **kwargs):
        self.monitor = monitor
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if self.operation == 'menu_generation':
                self.monitor.track_menu_generation(
                    self.kwargs.get('bd_type', 'unknown'),
                    self.kwargs.get('interface_count', 0),
                    duration
                )
            elif self.operation == 'interface_analysis':
                self.monitor.track_interface_analysis(
                    self.kwargs.get('interface_count', 0),
                    duration
                )
            elif self.operation == 'validation':
                self.monitor.track_validation(
                    self.kwargs.get('validation_type', 'unknown'),
                    duration
                )
            elif self.operation == 'preview_generation':
                self.monitor.track_preview_generation(
                    self.kwargs.get('change_count', 0),
                    duration
                )


# Convenience functions
def create_performance_tracker(monitor: BDEditorPerformanceMonitor, operation: str, **kwargs) -> PerformanceTracker:
    """Create performance tracker context manager"""
    return PerformanceTracker(monitor, operation, **kwargs)
