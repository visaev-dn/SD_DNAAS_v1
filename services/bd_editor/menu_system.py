#!/usr/bin/env python3
"""
Intelligent BD Editor Menu System

Core intelligent menu system that creates type-appropriate menu adapters
based on BD type and provides the main menu orchestration.
"""

import time
import logging
from typing import Dict, Optional
from .data_models import BDEditingComplexity, BDTypeProfile
from .interface_analyzer import BDInterfaceAnalyzer, BDTypeRegistry
from .data_models import ValidationResult, InterfaceAnalysis

logger = logging.getLogger(__name__)


class IntelligentBDEditorMenu:
    """Core intelligent menu system that adapts to BD types"""
    
    def __init__(self):
        self.type_registry = BDTypeRegistry()
        self.interface_analyzer = BDInterfaceAnalyzer()
        
        # Performance monitoring
        try:
            from .performance_monitor import BDEditorPerformanceMonitor
            self.performance_monitor = BDEditorPerformanceMonitor()
            self.monitoring_enabled = True
        except ImportError:
            self.performance_monitor = None
            self.monitoring_enabled = False
    
    def create_menu_for_bd(self, bridge_domain: Dict, session: Dict) -> 'MenuAdapter':
        """Factory method to create appropriate menu adapter"""
        
        start_time = time.time()
        
        try:
            dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
            
            # Analyze interfaces for editability
            interface_analysis = self.interface_analyzer.analyze_bd_interfaces(bridge_domain)
            
            # Create appropriate menu adapter
            menu_adapter = self._create_menu_adapter(dnaas_type, bridge_domain, session, interface_analysis)
            
            # Track performance
            if self.monitoring_enabled:
                duration = time.time() - start_time
                interface_count = interface_analysis.summary['total_interfaces']
                self.performance_monitor.track_menu_generation(dnaas_type, interface_count, duration)
            
            return menu_adapter
            
        except Exception as e:
            logger.error(f"Error creating menu for BD {bridge_domain.get('name', 'unknown')}: {e}")
            # Fallback to generic menu
            from .menu_adapters import GenericMenuAdapter
            return GenericMenuAdapter(bridge_domain, session, InterfaceAnalysis())
    
    def _create_menu_adapter(self, dnaas_type: str, bridge_domain: Dict, session: Dict, interface_analysis: InterfaceAnalysis) -> 'MenuAdapter':
        """Create specific menu adapter based on BD type"""
        
        if dnaas_type == "DNAAS_TYPE_4A_SINGLE_TAGGED":
            from .menu_adapters import SingleTaggedMenuAdapter
            return SingleTaggedMenuAdapter(bridge_domain, session, interface_analysis)
        elif dnaas_type == "DNAAS_TYPE_2A_QINQ_SINGLE_BD":
            from .menu_adapters import QinQSingleMenuAdapter
            return QinQSingleMenuAdapter(bridge_domain, session, interface_analysis)
        elif dnaas_type == "DNAAS_TYPE_1_DOUBLE_TAGGED":
            from .menu_adapters import DoubleTaggedMenuAdapter
            return DoubleTaggedMenuAdapter(bridge_domain, session, interface_analysis)
        else:
            from .menu_adapters import GenericMenuAdapter
            return GenericMenuAdapter(bridge_domain, session, interface_analysis)
    
    def display_bd_editing_header(self, bridge_domain: Dict, session: Dict):
        """Display intelligent BD editing header with type info"""
        
        print(f"\n🧠 INTELLIGENT BD EDITOR")
        print("="*60)
        
        # Display BD type information
        self.type_registry.display_bd_type_info(bridge_domain)
        
        # Display interface analysis
        self.interface_analyzer.display_interface_categorization(bridge_domain)
        
        # Display session info
        changes_count = len(session.get('changes_made', []))
        session_id = session.get('session_id', 'unknown')
        
        print(f"\n📋 EDITING SESSION:")
        print(f"Session ID: {session_id}")
        print(f"Changes Made: {changes_count}")
        
        if changes_count > 0:
            print(f"💡 Use 'Preview Changes' to see CLI commands before deployment")


# Convenience functions for external use
def create_intelligent_menu(bridge_domain: Dict, session: Dict) -> 'MenuAdapter':
    """Convenience function to create intelligent menu"""
    menu_system = IntelligentBDEditorMenu()
    return menu_system.create_menu_for_bd(bridge_domain, session)


def display_intelligent_header(bridge_domain: Dict, session: Dict):
    """Convenience function to display intelligent header"""
    menu_system = IntelligentBDEditorMenu()
    menu_system.display_bd_editing_header(bridge_domain, session)
