#!/usr/bin/env python3
"""
Phase 1 Integration - CLI Wrapper
Wraps existing CLI functions to use Phase 1 data structures while preserving user experience
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import Phase 1 data structures and transformers
from .data_transformers import DataTransformer, LegacyConfigAdapter
from config_engine.phase1_data_structures import TopologyData, TopologyValidator

# Import existing CLI components
from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
from config_engine.enhanced_menu_system import EnhancedMenuSystem


class Phase1CLIWrapper:
    """
    CLI wrapper that integrates Phase 1 data structures with existing CLI functionality.
    
    This wrapper:
    1. Intercepts CLI inputs
    2. Transforms them to Phase 1 structures
    3. Validates using Phase 1 framework
    4. Calls existing builders with validated data
    5. Transforms outputs back to expected formats
    """
    
    def __init__(self):
        """Initialize the Phase 1 CLI wrapper"""
        self.logger = logging.getLogger('Phase1CLIWrapper')
        self.transformer = DataTransformer()
        self.validator = TopologyValidator()
        self.legacy_adapter = LegacyConfigAdapter()
        
        # Initialize existing components
        self.unified_builder = UnifiedBridgeDomainBuilder()
        self.menu_system = EnhancedMenuSystem()
        
        self.logger.info("🚀 Phase 1 CLI Wrapper initialized")
    
    def wrapped_bridge_domain_builder(self, service_name: str, vlan_id: int,
                                    source_device: str, source_interface: str,
                                    dest_device: str, dest_interface: str) -> Dict:
        """
        Wrapped P2P bridge domain builder with Phase 1 integration.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            dest_device: Destination device name
            dest_interface: Destination interface name
            
        Returns:
            Configuration dictionary (legacy format for compatibility)
        """
        try:
            self.logger.info(f"🔨 Building P2P bridge domain: {service_name}")
            
            # Transform CLI input to Phase 1 format
            destinations = [{'device': dest_device, 'port': dest_interface}]
            topology, passed, errors, warnings = self.transformer.validate_and_transform(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Display validation results
            self._display_validation_results(service_name, passed, errors, warnings)
            
            if not passed and errors:
                self.logger.error("❌ Validation failed with errors. Aborting.")
                return None
            
            # Call existing builder with original parameters (preserve existing logic)
            configs = self.unified_builder.build_bridge_domain_config(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Log Phase 1 benefits
            self._log_phase1_benefits(topology)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"❌ Wrapped bridge domain builder failed: {e}")
            return None
    
    def wrapped_unified_bridge_domain_builder(self, service_name: str, vlan_id: int,
                                            source_device: str, source_interface: str,
                                            destinations: List[Dict[str, str]]) -> Dict:
        """
        Wrapped unified bridge domain builder with Phase 1 integration.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries
            
        Returns:
            Configuration dictionary (legacy format for compatibility)
        """
        try:
            topology_type = "P2P" if len(destinations) == 1 else "P2MP"
            self.logger.info(f"🔨 Building {topology_type} bridge domain: {service_name}")
            
            # Transform CLI input to Phase 1 format
            topology, passed, errors, warnings = self.transformer.validate_and_transform(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Display validation results
            self._display_validation_results(service_name, passed, errors, warnings)
            
            if not passed and errors:
                self.logger.error("❌ Validation failed with errors. Aborting.")
                return None
            
            # Call existing unified builder with original parameters
            configs = self.unified_builder.build_bridge_domain_config(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Log Phase 1 benefits
            self._log_phase1_benefits(topology)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"❌ Wrapped unified bridge domain builder failed: {e}")
            return None
    
    def wrapped_enhanced_menu_system(self) -> bool:
        """
        Wrapped enhanced menu system with Phase 1 integration.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("🔨 Starting enhanced menu system with Phase 1 integration")
            
            # Use existing menu system for user interaction (preserve UX)
            # But add Phase 1 validation hooks
            
            # Get service configuration using existing method
            service_name, vlan_id = self.menu_system.get_service_configuration()
            if not service_name or vlan_id is None:
                return False
            
            # Get source device using existing method
            source_device = self.menu_system.select_source_device()
            if not source_device:
                return False
            
            # Get source interface using existing method
            source_interface = self.menu_system.get_interface_input(source_device, "source")
            if not source_interface:
                return False
            
            # Get destinations using existing method
            destinations = self.menu_system._collect_destinations_interactively(source_device)
            if not destinations:
                return False
            
            # Phase 1 Integration: Transform and validate
            topology, passed, errors, warnings = self.transformer.validate_and_transform(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Display validation results
            self._display_validation_results(service_name, passed, errors, warnings)
            
            if not passed and errors:
                print("❌ Configuration validation failed. Please check the inputs and try again.")
                return False
            
            # Call existing builder logic
            configs = self.unified_builder.build_bridge_domain_config(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            if not configs:
                print("❌ Failed to build bridge domain configuration.")
                return False
            
            # Show configuration summary (existing logic)
            print(f"\n📋 Configuration Summary:")
            summary = self.unified_builder.get_configuration_summary(configs)
            print(summary)
            
            # Phase 1 Enhancement: Show additional insights
            self._show_phase1_insights(topology)
            
            # Save to database (existing logic)
            try:
                from database_manager import DatabaseManager
                db_manager = DatabaseManager()
                
                metadata = configs.get('_metadata', {})
                service_name = metadata.get('service_name', service_name)
                vlan_id = metadata.get('vlan_id', vlan_id)
                
                success = db_manager.save_configuration(
                    service_name=service_name,
                    vlan_id=vlan_id,
                    config_data=configs
                )
                
                if success:
                    print(f"\n✅ Bridge domain configuration built successfully!")
                    print(f"📁 Configuration saved to database")
                    print(f"📋 Service Name: {service_name}")
                    print(f"📋 VLAN ID: {vlan_id}")
                    
                    # Phase 1 Enhancement: Log topology data for future use
                    self._save_phase1_topology(topology, service_name)
                    
                else:
                    print("❌ Failed to save configuration to database")
                    return False
                    
            except Exception as e:
                print(f"❌ Error saving to database: {e}")
                return False
            
            # Show device count (existing logic)
            device_count = len([k for k in configs.keys() if k != '_metadata'])
            print(f"📋 Devices configured: {device_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Wrapped enhanced menu system failed: {e}")
            return False
    
    def _display_validation_results(self, service_name: str, passed: bool, 
                                  errors: List[str], warnings: List[str]) -> None:
        """Display Phase 1 validation results to user"""
        print(f"\n🔍 Phase 1 Validation Results for {service_name}:")
        print("─" * 50)
        
        if passed:
            print("✅ Validation PASSED")
        else:
            print("⚠️ Validation completed with issues")
        
        if warnings:
            print(f"\n⚠️ Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"   • {error}")
        
        if passed and not warnings:
            print("🎉 Configuration meets all Phase 1 standards!")
    
    def _log_phase1_benefits(self, topology: TopologyData) -> None:
        """Log Phase 1 benefits and insights"""
        self.logger.info("📊 Phase 1 Benefits Applied:")
        self.logger.info(f"   • Validated {topology.device_count} devices")
        self.logger.info(f"   • Validated {topology.interface_count} interfaces")
        self.logger.info(f"   • Validated {topology.path_count} paths")
        self.logger.info(f"   • Topology type: {topology.topology_type.value}")
        self.logger.info(f"   • Confidence score: {topology.confidence_score:.2f}")
        self.logger.info(f"   • Validation status: {topology.validation_status.value}")
    
    def _show_phase1_insights(self, topology: TopologyData) -> None:
        """Show Phase 1 insights to user"""
        print(f"\n🔬 Phase 1 Topology Insights:")
        print("─" * 30)
        print(f"📊 Topology Summary: {topology.topology_summary}")
        print(f"🎯 Confidence Score: {topology.confidence_score:.2f}")
        print(f"✅ Validation Status: {topology.validation_status.value}")
        
        # Show device breakdown
        leaf_count = len(topology.leaf_devices)
        spine_count = len(topology.spine_devices)
        superspine_count = len(topology.superspine_devices)
        
        print(f"🌿 Leaf devices: {leaf_count}")
        if spine_count > 0:
            print(f"🌲 Spine devices: {spine_count}")
        if superspine_count > 0:
            print(f"🏔️ Superspine devices: {superspine_count}")
        
        # Show interface breakdown
        access_interfaces = len(topology.access_interfaces)
        transport_interfaces = len(topology.transport_interfaces)
        configured_interfaces = len(topology.configured_interfaces)
        
        print(f"🔌 Access interfaces: {access_interfaces}")
        if transport_interfaces > 0:
            print(f"🚀 Transport interfaces: {transport_interfaces}")
        print(f"⚙️ Configured interfaces: {configured_interfaces}")
    
    def _save_phase1_topology(self, topology: TopologyData, service_name: str) -> None:
        """Save Phase 1 topology data for future use"""
        try:
            # Create topology data directory
            topology_dir = Path("topology/phase1_data")
            topology_dir.mkdir(parents=True, exist_ok=True)
            
            # Save topology data as JSON
            topology_file = topology_dir / f"{service_name}_topology.json"
            topology_dict = topology.to_dict()
            
            import json
            with open(topology_file, 'w') as f:
                json.dump(topology_dict, f, indent=2, default=str)
            
            self.logger.info(f"📁 Phase 1 topology data saved to {topology_file}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save Phase 1 topology data: {e}")
    
    def get_validation_report(self, service_name: str, vlan_id: int,
                            source_device: str, source_interface: str,
                            destinations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get detailed validation report for configuration.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries
            
        Returns:
            Validation report dictionary
        """
        try:
            topology, passed, errors, warnings = self.transformer.validate_and_transform(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            return {
                'service_name': service_name,
                'validation_passed': passed,
                'errors': errors,
                'warnings': warnings,
                'topology_summary': topology.topology_summary if topology else None,
                'confidence_score': topology.confidence_score if topology else 0.0,
                'device_count': topology.device_count if topology else 0,
                'interface_count': topology.interface_count if topology else 0,
                'path_count': topology.path_count if topology else 0
            }
            
        except Exception as e:
            return {
                'service_name': service_name,
                'validation_passed': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'topology_summary': None,
                'confidence_score': 0.0,
                'device_count': 0,
                'interface_count': 0,
                'path_count': 0
            }
    
    def validate_configuration_only(self, service_name: str, vlan_id: int,
                                  source_device: str, source_interface: str,
                                  destinations: List[Dict[str, str]]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration without building it.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries
            
        Returns:
            Tuple of (passed, errors, warnings)
        """
        try:
            topology, passed, errors, warnings = self.transformer.validate_and_transform(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            return passed, errors, warnings
            
        except Exception as e:
            return False, [f"Validation failed: {str(e)}"], []


class Phase1MenuSystemWrapper:
    """
    Wrapper for the enhanced menu system with Phase 1 integration.
    
    This wrapper preserves the exact user experience while adding
    Phase 1 validation and insights behind the scenes.
    """
    
    def __init__(self):
        """Initialize the Phase 1 menu system wrapper"""
        self.cli_wrapper = Phase1CLIWrapper()
        self.logger = logging.getLogger('Phase1MenuSystemWrapper')
    
    def run_enhanced_bridge_domain_builder(self) -> bool:
        """
        Run enhanced bridge domain builder with Phase 1 integration.
        
        This method preserves the exact user experience of the original
        enhanced menu system while adding Phase 1 validation.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "🔨" + "=" * 68)
        print("🔨 UNIFIED BRIDGE-DOMAIN BUILDER (P2P & P2MP) - Phase 1 Enhanced")
        print("🔨" + "=" * 68)
        print("✨ Now with advanced validation and topology insights!")
        
        return self.cli_wrapper.wrapped_enhanced_menu_system()
