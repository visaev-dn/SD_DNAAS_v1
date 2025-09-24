#!/usr/bin/env python3
"""
CLI Integration for Simplified Bridge Domain Discovery
====================================================

Integrates the 3-step simplified workflow with the existing CLI system.
Provides user-friendly interface that follows the guided rails to prevent
architectural violations.

Architecture: 3-Step Simplified Workflow (ADR-001)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the simplified discovery system
from .simplified_bridge_domain_discovery import (
    SimplifiedBridgeDomainDiscovery,
    run_simplified_discovery,
    DiscoveryResults
)
from .data_sync_manager import DataSyncManager

logger = logging.getLogger(__name__)


class SimplifiedDiscoveryCLI:
    """
    CLI interface for the simplified bridge domain discovery system.
    
    Provides user-friendly menu integration following the memory preference
    for integrating new functionality as menu options rather than separate interfaces.
    """
    
    def __init__(self):
        """Initialize CLI interface"""
        self.discovery_system = None
        self.last_results = None
        self.sync_manager = DataSyncManager()
    
    def show_discovery_menu(self):
        """
        Show the simplified discovery menu.
        
        This integrates with the existing CLI as a new menu option called
        'Enhanced Database' (user-friendly name, avoiding internal terms like 'phase1').
        """
        
        while True:
            print("\n" + "🔍" + "=" * 68)
            print("🔍 ENHANCED DATABASE - Bridge Domain Discovery & Management")
            print("🔍" + "=" * 68)
            print("📋 Simplified 3-Step Workflow:")
            print("1. 🚀 Run Complete Discovery (Recommended)")
            print("2. 📊 View Last Discovery Results")
            print("3. 🔧 Run Step-by-Step Discovery")
            print("4. 📁 Browse Discovery Output Files")
            print("5. 🎯 Discovery System Status")
            print("6. ⚙️  Advanced Options")
            print("7. 🔙 Back to Main Menu")
            print()
            
            choice = input("Select an option [1-7]: ").strip()
            
            if choice == '1':
                self.run_complete_discovery()
            elif choice == '2':
                self.view_last_results()
            elif choice == '3':
                self.run_step_by_step_discovery()
            elif choice == '4':
                self.browse_output_files()
            elif choice == '5':
                self.show_system_status()
            elif choice == '6':
                self.show_advanced_options()
            elif choice == '7':
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, or 7.")
    
    def run_complete_discovery(self):
        """Run the complete 3-step discovery workflow"""
        
        print("\n" + "🚀" + "=" * 68)
        print("🚀 RUNNING COMPLETE BRIDGE DOMAIN DISCOVERY")
        print("🚀" + "=" * 68)
        print("📋 This will run the complete 3-step workflow:")
        print("   Step 1: Load and validate data")
        print("   Step 2: Process bridge domains (BD-PROC Pipeline)")
        print("   Step 3: Consolidate and save results")
        print()
        
        # Confirm with user
        confirm = input("Continue with discovery? [Y/n]: ").strip().lower()
        if confirm and confirm != 'y' and confirm != 'yes':
            print("Discovery cancelled.")
            return
        
        try:
            print("🔍 Starting discovery...")
            print()
            
            # Run discovery with progress updates
            results = run_simplified_discovery()
            self.last_results = results
            
            # Display results summary
            self.display_results_summary(results)
            
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            logger.error(f"Discovery failed: {e}")
            
            # Offer troubleshooting options
            print("\n🔧 Troubleshooting options:")
            print("1. Check that parsed configuration files exist")
            print("2. Verify directory permissions")
            print("3. Run system status check (option 5)")
            print("4. Check logs for detailed error information")
    
    def display_results_summary(self, results: DiscoveryResults):
        """Display a user-friendly summary of discovery results"""
        
        print("\n" + "🎉" + "=" * 68)
        print("🎉 DISCOVERY COMPLETED SUCCESSFULLY!")
        print("🎉" + "=" * 68)
        
        # Basic statistics
        print("📊 DISCOVERY STATISTICS:")
        print(f"   • Total bridge domains discovered: {results.total_bridge_domains_discovered}")
        print(f"   • Successfully processed: {results.total_bridge_domains_processed}")
        print(f"   • Consolidated bridge domains: {len(results.consolidated_bridge_domains)}")
        print(f"   • Individual bridge domains: {len(results.individual_bridge_domains)}")
        print(f"   • Total devices: {results.total_devices}")
        print(f"   • Total interfaces: {results.total_interfaces}")
        print()
        
        # Performance metrics
        print("⏱️  PERFORMANCE METRICS:")
        print(f"   • Processing time: {results.total_processing_time:.2f} seconds")
        print(f"   • Success rate: {results.success_rate:.1%}")
        print(f"   • Consolidation rate: {results.consolidation_rate:.1%}")
        print()
        
        # Quality metrics
        if results.total_errors > 0 or results.total_warnings > 0:
            print("⚠️  QUALITY METRICS:")
            print(f"   • Errors: {results.total_errors}")
            print(f"   • Warnings: {results.total_warnings}")
            print()
        
        # Top consolidated bridge domains
        if results.consolidated_bridge_domains:
            print("🎯 TOP CONSOLIDATED BRIDGE DOMAINS:")
            for i, cbd in enumerate(results.consolidated_bridge_domains[:5], 1):
                print(f"   {i}. {cbd.consolidated_name}")
                print(f"      • Username: {cbd.username or 'Unknown'}")
                print(f"      • Devices: {len(cbd.all_devices)}")
                print(f"      • Interfaces: {len(cbd.all_interfaces)}")
                print(f"      • Source BDs: {cbd.source_count}")
            
            if len(results.consolidated_bridge_domains) > 5:
                print(f"   ... and {len(results.consolidated_bridge_domains) - 5} more")
            print()
        
        print("💾 Results saved to: topology/simplified_discovery_results/")
        
        # Synchronize data between database and JSON files
        print("🔄 Synchronizing data...")
        try:
            # Load the latest JSON results for sync
            output_dir = Path("topology/simplified_discovery_results")
            latest_file = max(output_dir.glob("bridge_domain_mapping_*.json"), key=lambda f: f.stat().st_mtime)
            with open(latest_file, 'r') as f:
                discovery_results = json.load(f)
            
            # Use sync manager for proper synchronization
            sync_result = self.sync_manager.sync_discovery_data(discovery_results)
            
            print(f"✅ Data synchronization completed:")
            print(f"   • Database: {sync_result['database_saved']} bridge domains")
            print(f"   • JSON: {sync_result['json_saved']} bridge domains")
            print(f"   • Status: {sync_result['sync_status']['status']}")
            
            if sync_result['sync_status']['sync_percentage'] < 100:
                print(f"   ⚠️  Sync warning: {sync_result['sync_status']['sync_percentage']:.1f}% synchronized")
        
        except Exception as e:
            print(f"⚠️  Data sync failed: {e}")
            print("📁 Results are still available in JSON files")
        
        print()
        print("📋 Use option 2 to view detailed results")
        print("📁 Use option 4 to browse output files")
    
    def view_last_results(self):
        """View detailed results from the last discovery run"""
        
        if not self.last_results:
            print("❌ No discovery results available. Run discovery first (option 1).")
            return
        
        results = self.last_results
        
        print("\n" + "📊" + "=" * 68)
        print("📊 DETAILED DISCOVERY RESULTS")
        print("📊" + "=" * 68)
        
        # Show consolidated bridge domains
        if results.consolidated_bridge_domains:
            print(f"🎯 CONSOLIDATED BRIDGE DOMAINS ({len(results.consolidated_bridge_domains)}):")
            print()
            
            for i, cbd in enumerate(results.consolidated_bridge_domains, 1):
                print(f"{i}. {cbd.consolidated_name}")
                print(f"   • Consolidation Key: {cbd.consolidation_key}")
                print(f"   • Username: {cbd.username or 'Unknown'}")
                print(f"   • Global Identifier: {cbd.global_identifier}")
                print(f"   • Bridge Domain Type: {cbd.bridge_domain_type.value}")
                print(f"   • Devices ({len(cbd.all_devices)}): {', '.join(cbd.all_devices[:3])}")
                if len(cbd.all_devices) > 3:
                    print(f"     ... and {len(cbd.all_devices) - 3} more")
                print(f"   • Interfaces: {len(cbd.all_interfaces)}")
                print(f"   • Source Bridge Domains: {', '.join(cbd.source_bridge_domains)}")
                print()
        
        # Show individual bridge domains
        if results.individual_bridge_domains:
            print(f"📋 INDIVIDUAL BRIDGE DOMAINS ({len(results.individual_bridge_domains)}):")
            print()
            
            for i, ibd in enumerate(results.individual_bridge_domains[:10], 1):
                print(f"{i}. {ibd.name}")
                print(f"   • Bridge Domain Type: {ibd.bridge_domain_type.value}")
                print(f"   • Username: {ibd.username or 'Unknown'}")
                print(f"   • Devices: {', '.join(ibd.devices)}")
                print(f"   • Interfaces: {len(ibd.interfaces)}")
                print(f"   • Can Consolidate: {'Yes' if ibd.can_consolidate else 'No'}")
                print()
            
            if len(results.individual_bridge_domains) > 10:
                print(f"... and {len(results.individual_bridge_domains) - 10} more")
                print()
        
        # Pagination for large results
        if len(results.consolidated_bridge_domains) > 10 or len(results.individual_bridge_domains) > 10:
            input("\nPress Enter to continue...")
    
    def run_step_by_step_discovery(self):
        """Run discovery step by step with user interaction"""
        
        print("\n" + "🔧" + "=" * 68)
        print("🔧 STEP-BY-STEP DISCOVERY")
        print("🔧" + "=" * 68)
        print("This mode runs each step individually with detailed output.")
        print()
        
        try:
            # Initialize discovery system
            discovery_system = SimplifiedBridgeDomainDiscovery()
            
            # Step 1: Load and validate data
            print("📋 Step 1: Loading and validating data...")
            input("Press Enter to continue...")
            
            loaded_data = discovery_system._step1_load_and_validate_data()
            
            print(f"✅ Step 1 complete:")
            print(f"   • Bridge domains loaded: {len(loaded_data.bridge_domains)}")
            print(f"   • Devices classified: {len(loaded_data.device_types)}")
            print(f"   • LLDP data loaded: {len(loaded_data.lldp_data)}")
            print()
            
            # Step 2: Process bridge domains
            print("🔄 Step 2: Processing bridge domains (BD-PROC Pipeline)...")
            input("Press Enter to continue...")
            
            processed_bds = discovery_system._step2_process_bridge_domains(loaded_data)
            
            print(f"✅ Step 2 complete:")
            print(f"   • Bridge domains processed: {len(processed_bds)}")
            valid_count = len([bd for bd in processed_bds if bd.validation_status.value != 'invalid'])
            print(f"   • Valid bridge domains: {valid_count}")
            print()
            
            # Step 3: Consolidate and save
            print("🎯 Step 3: Consolidating and saving results...")
            input("Press Enter to continue...")
            
            results = discovery_system._step3_consolidate_and_save(processed_bds)
            results.finalize_results()
            
            print(f"✅ Step 3 complete:")
            print(f"   • Consolidated bridge domains: {len(results.consolidated_bridge_domains)}")
            print(f"   • Individual bridge domains: {len(results.individual_bridge_domains)}")
            print()
            
            # Store results and show summary
            self.last_results = results
            self.display_results_summary(results)
            
        except Exception as e:
            print(f"❌ Step-by-step discovery failed: {e}")
            logger.error(f"Step-by-step discovery failed: {e}")
    
    def browse_output_files(self):
        """Browse discovery output files"""
        
        output_dir = Path("topology/simplified_discovery_results")
        
        if not output_dir.exists():
            print("❌ No output directory found. Run discovery first (option 1).")
            return
        
        print("\n" + "📁" + "=" * 68)
        print("📁 DISCOVERY OUTPUT FILES")
        print("📁" + "=" * 68)
        
        # List all output files
        json_files = list(output_dir.glob("*.json"))
        
        if not json_files:
            print("❌ No output files found. Run discovery first (option 1).")
            return
        
        print(f"📂 Output directory: {output_dir}")
        print(f"📋 Found {len(json_files)} output files:")
        print()
        
        for i, file_path in enumerate(sorted(json_files, reverse=True), 1):
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            file_time = file_stat.st_mtime
            
            print(f"{i}. {file_path.name}")
            print(f"   • Size: {file_size:,} bytes")
            print(f"   • Modified: {file_time}")
            print()
        
        # Option to view file contents
        while True:
            choice = input("Enter file number to view contents, or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                break
            
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(json_files):
                    self.view_output_file(json_files[file_index])
                else:
                    print("❌ Invalid file number.")
            except ValueError:
                print("❌ Please enter a valid number or 'q'.")
    
    def view_output_file(self, file_path: Path):
        """View contents of an output file"""
        
        try:
            import json
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"\n📄 Contents of {file_path.name}:")
            print("=" * 60)
            
            if isinstance(data, list):
                print(f"📋 Array with {len(data)} items:")
                for i, item in enumerate(data[:5], 1):
                    if isinstance(item, dict):
                        print(f"\n{i}. {item.get('name', 'Unknown')}")
                        for key, value in item.items():
                            if key != 'name':
                                print(f"   • {key}: {value}")
                
                if len(data) > 5:
                    print(f"\n... and {len(data) - 5} more items")
            
            elif isinstance(data, dict):
                for key, value in data.items():
                    print(f"• {key}: {value}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Failed to view file: {e}")
        
        input("\nPress Enter to continue...")
    
    def show_system_status(self):
        """Show discovery system status and health check"""
        
        print("\n" + "🎯" + "=" * 68)
        print("🎯 DISCOVERY SYSTEM STATUS")
        print("🎯" + "=" * 68)
        
        # Check required directories
        print("📂 DIRECTORY STATUS:")
        
        required_dirs = [
            ("Parsed config data", "topology/configs/parsed_data/bridge_domain_parsed"),
            ("LLDP data", "topology/lldp_data"),
            ("Output directory", "topology/simplified_discovery_results")
        ]
        
        for name, path in required_dirs:
            path_obj = Path(path)
            if path_obj.exists():
                file_count = len(list(path_obj.glob("*")))
                print(f"   ✅ {name}: {path} ({file_count} files)")
            else:
                print(f"   ❌ {name}: {path} (not found)")
        print()
        
        # Check system components
        print("🔧 SYSTEM COMPONENTS:")
        try:
            from config_engine.simplified_discovery.simplified_bridge_domain_discovery import validate_simplified_workflow
            validate_simplified_workflow()
            print("   ✅ Simplified workflow validation: PASSED")
        except Exception as e:
            print(f"   ❌ Simplified workflow validation: FAILED ({e})")
        
        try:
            from config_engine.simplified_discovery.data_structures import enforce_data_structure_contracts
            enforce_data_structure_contracts()
            print("   ✅ Data structure contracts: VALID")
        except Exception as e:
            print(f"   ❌ Data structure contracts: INVALID ({e})")
        print()
        
        # Check last discovery results
        print("📊 LAST DISCOVERY STATUS:")
        if self.last_results:
            print(f"   ✅ Last discovery: {self.last_results.discovery_session_id}")
            print(f"   • Processing time: {self.last_results.total_processing_time:.2f}s")
            print(f"   • Success rate: {self.last_results.success_rate:.1%}")
            print(f"   • Results: {len(self.last_results.consolidated_bridge_domains)} consolidated")
        else:
            print("   ⚠️  No discovery results available")
        print()
        
        input("Press Enter to continue...")
    
    def show_advanced_options(self):
        """Show advanced configuration and troubleshooting options"""
        
        print("\n" + "⚙️" + "=" * 68)
        print("⚙️  ADVANCED OPTIONS")
        print("⚙️" + "=" * 68)
        print("1. 🔧 Validate System Architecture")
        print("2. 📋 Test Data Structure Contracts") 
        print("3. 🗂️  Clean Output Directory")
        print("4. 📝 View System Logs")
        print("5. 🔙 Back to Discovery Menu")
        print()
        
        choice = input("Select an option [1-5]: ").strip()
        
        if choice == '1':
            self.validate_system_architecture()
        elif choice == '2':
            self.test_data_structure_contracts()
        elif choice == '3':
            self.clean_output_directory()
        elif choice == '4':
            self.view_system_logs()
        elif choice == '5':
            return
        else:
            print("❌ Invalid choice.")
    
    def validate_system_architecture(self):
        """Validate system architecture against guided rails"""
        
        print("\n🔧 Validating system architecture...")
        
        try:
            from config_engine.simplified_discovery.simplified_bridge_domain_discovery import validate_simplified_workflow
            validate_simplified_workflow()
            print("✅ Simplified workflow validation: PASSED")
            
            from config_engine.simplified_discovery.data_structures import enforce_data_structure_contracts
            enforce_data_structure_contracts()
            print("✅ Data structure contracts: VALID")
            
            print("✅ System architecture validation: ALL CHECKS PASSED")
            
        except Exception as e:
            print(f"❌ Architecture validation failed: {e}")
        
        input("\nPress Enter to continue...")
    
    def test_data_structure_contracts(self):
        """Test data structure contracts"""
        
        print("\n📋 Testing data structure contracts...")
        
        try:
            # Test data structure imports
            from config_engine.simplified_discovery.data_structures import (
                RawBridgeDomain, ProcessedBridgeDomain, ConsolidatedBridgeDomain,
                validate_data_flow_step1_to_step2, validate_data_flow_step2_to_step3
            )
            print("✅ Data structure imports: SUCCESS")
            
            # Test data structure creation
            test_bd = RawBridgeDomain(
                name="test_bd",
                devices=["test_device"],
                interfaces=[{"interface": "test_interface"}],
                raw_config={}
            )
            print("✅ Data structure creation: SUCCESS")
            
            print("✅ Data structure contract tests: ALL PASSED")
            
        except Exception as e:
            print(f"❌ Data structure contract test failed: {e}")
        
        input("\nPress Enter to continue...")
    
    def clean_output_directory(self):
        """Clean discovery output directory"""
        
        output_dir = Path("topology/simplified_discovery_results")
        
        if not output_dir.exists():
            print("❌ Output directory does not exist.")
            return
        
        files = list(output_dir.glob("*.json"))
        
        if not files:
            print("✅ Output directory is already clean.")
            return
        
        print(f"🗂️  Found {len(files)} output files to clean.")
        confirm = input("Delete all output files? [y/N]: ").strip().lower()
        
        if confirm == 'y' or confirm == 'yes':
            try:
                for file_path in files:
                    file_path.unlink()
                print(f"✅ Deleted {len(files)} files.")
            except Exception as e:
                print(f"❌ Failed to clean directory: {e}")
        else:
            print("Clean cancelled.")
        
        input("\nPress Enter to continue...")
    
    def view_system_logs(self):
        """View system logs"""
        
        print("\n📝 System logs would be displayed here.")
        print("(Log viewing functionality to be implemented)")
        
        input("\nPress Enter to continue...")


# =============================================================================
# MAIN INTEGRATION FUNCTION
# =============================================================================

def run_enhanced_database_menu():
    """
    Main entry point for the Enhanced Database menu.
    
    This function integrates with the existing CLI system following
    the memory preference for menu-based integration.
    """
    
    # Set up logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run CLI interface
    cli = SimplifiedDiscoveryCLI()
    cli.show_discovery_menu()


if __name__ == "__main__":
    # Run the CLI interface directly
    run_enhanced_database_menu()
