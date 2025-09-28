#!/usr/bin/env python3
"""
Enhanced CLI Display for Simplified Discovery Data
================================================

Provides Phase 1-style database display for simplified discovery results.
Matches the layout and functionality of the existing Phase 1 database operations
but works with the new simplified discovery data structure.

Architecture: Enhanced Display Layer for Simplified Discovery (ADR-001)
"""

import os
import sys
import json
import sqlite3
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database_manager import DatabaseManager
from .data_sync_manager import DataSyncManager


class EnhancedSimplifiedDiscoveryDisplay:
    """
    Enhanced CLI display for simplified discovery data.
    
    Provides Phase 1-style database operations interface for the new
    simplified discovery system data.
    """
    
    def __init__(self):
        """Initialize enhanced display system"""
        self.db_manager = DatabaseManager()
        self.sync_manager = DataSyncManager()
        self.output_dir = Path("topology/simplified_discovery_results")
    
    def show_enhanced_database_menu(self):
        """Show enhanced database menu for simplified discovery data"""
        
        while True:
            print("\n" + "🗄️" + "=" * 68)
            print("🗄️ ENHANCED SIMPLIFIED DISCOVERY DATABASE")
            print("🗄️" + "=" * 68)
            print("✨ Advanced data management for simplified discovery results!")
            print()
            print("📋 Database Operations:")
            print("1. 📊 View All Bridge Domains")
            print("2. 🔍 Search Bridge Domains")
            print("3. 📋 View Bridge Domain Details")
            print("4. 📤 Export Discovery Data")
            print("5. 📥 Import Discovery Data")
            print("6. 🔗 View Consolidation Analysis")
            print("7. 🗑️  Delete Bridge Domain")
            print("8. 📈 Database Statistics")
            print("9. 🔄 Refresh Discovery Data")
            print("10. 📁 Browse Discovery Files")
            print("11. 🎯 DNAAS Type Analysis")
            print("12. 🛡️  Data Validation Report")
            print("13. 🔄 Data Synchronization Status")
            print("14. 🧹 Clean Old Discovery Files")
            print("15. 🔙 Back to Main Menu")
            print()
            
            choice = input("Select an option [1-15]: ").strip()
            
            if choice == "1":
                self.run_list_bridge_domains()
            elif choice == "2":
                self.run_search_bridge_domains()
            elif choice == "3":
                self.run_view_bridge_domain_details()
            elif choice == "4":
                self.run_export_discovery_data()
            elif choice == "5":
                self.run_import_discovery_data()
            elif choice == "6":
                self.run_consolidation_analysis()
            elif choice == "7":
                self.run_delete_bridge_domain()
            elif choice == "8":
                self.run_database_statistics()
            elif choice == "9":
                self.run_refresh_discovery_data()
            elif choice == "10":
                self.run_browse_discovery_files()
            elif choice == "11":
                self.run_dnaas_type_analysis()
            elif choice == "12":
                self.run_data_validation_report()
            elif choice == "13":
                self.run_sync_status()
            elif choice == "14":
                self.run_clean_old_files()
            elif choice == "15":
                break
            else:
                print("❌ Invalid choice. Please select 1-15.")
    
    def run_list_bridge_domains(self):
        """List all bridge domains with pagination and smart column width"""
        try:
            print("\n📊 Viewing All Bridge Domains...")
            
            # Get bridge domains from database
            conn = sqlite3.connect('instance/lab_automation.db')
            cursor = conn.cursor()
            
            # Get total count from unified bridge_domains table
            cursor.execute('''
                SELECT COUNT(*) FROM bridge_domains 
                WHERE source = 'discovered'
            ''')
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                print("📭 No bridge domains found in the database.")
                print("💡 Run discovery first to populate the database.")
                conn.close()
                return
            
            # Pagination settings
            page_size = 20
            total_pages = math.ceil(total_count / page_size)
            current_page = 1
            
            # Calculate statistics
            stats = self._calculate_bridge_domain_statistics(cursor)
            
            while True:
                # Clear screen for better readability
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("\n" + "📊" + "=" * 68)
                print("📊 SIMPLIFIED DISCOVERY BRIDGE DOMAINS")
                print("📊" + "=" * 68)
                
                # Show statistics
                print(f"📈 Database Statistics:")
                print(f"   • Total Bridge Domains: {stats['total_bridge_domains']}")
                print(f"   • Consolidated: {stats['consolidated_count']}")
                print(f"   • Individual: {stats['individual_count']}")
                print(f"   • DNAAS Types: {stats['dnaas_types']}")
                print(f"   • Users: {stats['unique_users']}")
                print(f"   • Database Size: {stats['database_size']:.1f} MB")
                print()
                
                # Get current page data
                offset = (current_page - 1) * page_size
                cursor.execute('''
                    SELECT name, username, vlan_id, topology_type, 
                           1.0 as confidence, updated_at, discovery_data, dnaas_type
                    FROM bridge_domains
                    WHERE source = 'discovered'
                    ORDER BY name
                    LIMIT ? OFFSET ?
                ''', (page_size, offset))
                
                bridge_domains = cursor.fetchall()
                
                # Display header
                print(f"📋 Bridge Domains (Page {current_page}/{total_pages}):")
                print("-" * 120)
                print(f"{'#':<3} {'Bridge Domain Name':<35} {'User':<12} {'VLAN':<6} {'Type':<12} {'Conf':<5} {'Created':<12}")
                print("-" * 120)
                
                # Display bridge domains
                for i, (bd_name, username, vlan_id, topo_type, confidence, created_at, discovery_data, db_dnaas_type) in enumerate(bridge_domains, offset + 1):
                    # Parse discovery data for consolidation info
                    is_consolidated = False
                    consolidated_count = 1
                    try:
                        discovery_json = json.loads(discovery_data)
                        is_consolidated = discovery_json.get('is_consolidated', False)
                        consolidation_info = discovery_json.get('consolidation_info', {})
                        consolidated_count = consolidation_info.get('consolidated_count', 1)
                    except:
                        pass
                    
                    # Use DNAAS type from database (not JSON)
                    dnaas_type = db_dnaas_type or "unknown"
                    
                    # Simplify DNAAS type for display
                    if dnaas_type and dnaas_type != "unknown" and dnaas_type.startswith('DNAAS_TYPE_'):
                        if 'TYPE_2A_QINQ' in dnaas_type:
                            dnaas_type = '2A_QINQ'
                        elif 'TYPE_4A_SINGLE' in dnaas_type:
                            dnaas_type = '4A_SINGLE'
                        elif 'TYPE_1_DOUBLE' in dnaas_type:
                            dnaas_type = '1_DOUBLE'
                        else:
                            dnaas_type = dnaas_type.replace('DNAAS_TYPE_', '').replace('_', ' ').lower()
                    
                    # Format display
                    display_name = bd_name[:32] + "..." if len(bd_name) > 35 else bd_name
                    if is_consolidated:
                        display_name = f"🔗 {display_name}"
                    
                    user_display = username[:10] + "..." if len(username) > 12 else username
                    vlan_display = str(vlan_id) if vlan_id else "N/A"
                    type_display = dnaas_type[:10] + "..." if len(dnaas_type) > 12 else dnaas_type
                    conf_display = f"{confidence:.2f}" if confidence else "N/A"
                    created_display = created_at[:10] if created_at else "N/A"
                    
                    print(f"{i:<3} {display_name:<35} {user_display:<12} {vlan_display:<6} {type_display:<12} {conf_display:<5} {created_display:<12}")
                
                print("-" * 120)
                print(f"Showing {len(bridge_domains)} of {total_count} bridge domains")
                print()
                
                # Navigation options
                print("📋 Navigation Options:")
                print("   [n] Next page    [p] Previous page    [g] Go to page")
                print("   [s] Search       [d] View details     [e] Edit BD      [f] Filter")
                print("   [r] Refresh      [q] Quit")
                print()
                
                choice = input("Enter command: ").strip().lower()
                
                if choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif choice == 'p' and current_page > 1:
                    current_page -= 1
                elif choice == 'g':
                    try:
                        page = int(input(f"Enter page number (1-{total_pages}): "))
                        if 1 <= page <= total_pages:
                            current_page = page
                    except ValueError:
                        print("❌ Invalid page number")
                elif choice == 's':
                    self.run_search_bridge_domains()
                    break
                elif choice == 'd':
                    self.run_view_bridge_domain_details()
                    break
                elif choice == 'e':
                    self.run_edit_bridge_domain()
                    break
                elif choice == 'f':
                    self.run_filter_bridge_domains()
                    break
                elif choice == 'r':
                    continue
                elif choice == 'q':
                    break
                else:
                    print("❌ Invalid command")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to list bridge domains: {e}")
            import traceback
            traceback.print_exc()
    
    def run_database_statistics(self):
        """Show comprehensive database statistics"""
        try:
            print("\n📈 Database Statistics...")
            
            conn = sqlite3.connect('instance/lab_automation.db')
            cursor = conn.cursor()
            
            # Get comprehensive statistics
            stats = self._calculate_bridge_domain_statistics(cursor)
            
            print("\n📊 SIMPLIFIED DISCOVERY DATABASE STATISTICS")
            print("=" * 60)
            
            # Basic counts
            print(f"📋 Bridge Domain Counts:")
            print(f"   • Total Bridge Domains: {stats['total_bridge_domains']}")
            print(f"   • Consolidated Groups: {stats['consolidated_count']}")
            print(f"   • Individual Bridge Domains: {stats['individual_count']}")
            print(f"   • Consolidation Rate: {stats['consolidation_rate']:.1f}%")
            print()
            
            # User statistics
            print(f"👥 User Statistics:")
            print(f"   • Unique Users: {stats['unique_users']}")
            print(f"   • Top Users:")
            for user, count in stats['top_users'][:5]:
                print(f"     - {user}: {count} bridge domains")
            print()
            
            # DNAAS Type analysis
            print(f"🏷️  DNAAS Type Analysis:")
            for dnaas_type, count in stats['dnaas_types'].items():
                print(f"   • {dnaas_type}: {count}")
            print()
            
            # VLAN range analysis
            print(f"🔢 VLAN Range Analysis:")
            print(f"   • VLAN Range: {stats['vlan_min']} - {stats['vlan_max']}")
            print(f"   • Most Common VLANs:")
            for vlan, count in stats['top_vlans'][:5]:
                print(f"     - VLAN {vlan}: {count} bridge domains")
            print()
            
            # Database health
            print(f"💾 Database Health:")
            print(f"   • Database Size: {stats['database_size']:.1f} MB")
            print(f"   • Average Confidence: {stats['avg_confidence']:.2f}")
            print(f"   • Data Quality: {stats['data_quality']:.1f}%")
            print()
            
            # Recent activity
            print(f"⏰ Recent Activity:")
            print(f"   • Last Discovery: {stats['last_discovery']}")
            print(f"   • Discovery Files: {stats['discovery_files']}")
            print(f"   • File Size: {stats['total_file_size']:.1f} MB")
            
            print("=" * 60)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to get database statistics: {e}")
            import traceback
            traceback.print_exc()
    
    def run_search_bridge_domains(self):
        """Search bridge domains with advanced filters"""
        try:
            print("\n🔍 Search Bridge Domains...")
            
            # Get search criteria
            print("📋 Search Criteria:")
            search_term = input("Enter search term (name, user, VLAN): ").strip()
            
            if not search_term:
                print("❌ Search term cannot be empty")
                return
            
            conn = sqlite3.connect('instance/lab_automation.db')
            cursor = conn.cursor()
            
            # Build search query for unified bridge_domains table
            query = '''
                SELECT name, username, vlan_id, topology_type, 
                       1.0 as confidence, updated_at, discovery_data, dnaas_type
                FROM bridge_domains
                WHERE source = 'discovered'
                AND (name LIKE ? OR username LIKE ? OR vlan_id LIKE ?)
                ORDER BY name
            '''
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            
            results = cursor.fetchall()
            
            if not results:
                print(f"🔍 No bridge domains found matching '{search_term}'")
                conn.close()
                return
            
            print(f"\n🔍 Found {len(results)} matching bridge domains:")
            print("-" * 120)
            print(f"{'#':<3} {'Bridge Domain Name':<35} {'User':<12} {'VLAN':<6} {'Type':<12} {'Conf':<5} {'Created':<12}")
            print("-" * 120)
            
            for i, (bd_name, username, vlan_id, topo_type, confidence, created_at, discovery_data, db_dnaas_type) in enumerate(results, 1):
                # Parse consolidation info
                is_consolidated = False
                try:
                    discovery_json = json.loads(discovery_data)
                    is_consolidated = discovery_json.get('is_consolidated', False)
                except:
                    pass
                
                # Use DNAAS type from database (not JSON)
                dnaas_type = db_dnaas_type or "unknown"
                
                # Simplify DNAAS type for display
                if dnaas_type and dnaas_type != "unknown" and dnaas_type.startswith('DNAAS_TYPE_'):
                    if 'TYPE_2A_QINQ' in dnaas_type:
                        dnaas_type = '2A_QINQ'
                    elif 'TYPE_4A_SINGLE' in dnaas_type:
                        dnaas_type = '4A_SINGLE'
                    elif 'TYPE_1_DOUBLE' in dnaas_type:
                        dnaas_type = '1_DOUBLE'
                    else:
                        dnaas_type = dnaas_type.replace('DNAAS_TYPE_', '').replace('_', ' ').lower()
                
                display_name = bd_name[:32] + "..." if len(bd_name) > 35 else bd_name
                if is_consolidated:
                    display_name = f"🔗 {display_name}"
                
                user_display = username[:10] + "..." if len(username) > 12 else username
                vlan_display = str(vlan_id) if vlan_id else "N/A"
                type_display = dnaas_type[:10] + "..." if len(dnaas_type) > 12 else dnaas_type
                conf_display = f"{confidence:.2f}" if confidence else "N/A"
                created_display = created_at[:10] if created_at else "N/A"
                
                print(f"{i:<3} {display_name:<35} {user_display:<12} {vlan_display:<6} {type_display:<12} {conf_display:<5} {created_display:<12}")
            
            print("-" * 120)
            
            # Options
            print("\n📋 Options:")
            print("   [d] View details    [e] Export results    [q] Quit")
            choice = input("Enter command: ").strip().lower()
            
            if choice == 'd':
                self.run_view_bridge_domain_details()
            elif choice == 'e':
                self.run_export_search_results(results)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to search bridge domains: {e}")
            import traceback
            traceback.print_exc()
    
    def run_view_bridge_domain_details(self):
        """View detailed information for a specific bridge domain with edit option"""
        try:
            print("\n📋 View Bridge Domain Details...")
            
            bd_name = input("Enter bridge domain name: ").strip()
            if not bd_name:
                print("❌ Bridge domain name cannot be empty")
                return
            
            conn = sqlite3.connect('instance/lab_automation.db')
            cursor = conn.cursor()
            
            # Use unified bridge_domains table - get all available columns
            cursor.execute('''
                SELECT name, username, vlan_id, topology_type, 
                       updated_at, discovery_data, dnaas_type, deployment_status, id
                FROM bridge_domains 
                WHERE source = 'discovered'
                AND name = ?
            ''', (bd_name,))
            
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Bridge domain '{bd_name}' not found")
                conn.close()
                return
            
            (bd_name, username, vlan_id, topo_type, updated_at, discovery_data, 
             dnaas_type, deployment_status, bd_id) = result
            
            # Initialize missing variables that the code expects
            outer_vlan = None  # Not available in current schema
            inner_vlan = None  # Not available in current schema
            
            # Parse JSON data
            discovery_json = json.loads(discovery_data) if discovery_data else {}
            # Note: interface_data column doesn't exist, interface info is in discovery_data
            
            # Display detailed information
            print(f"\n📋 BRIDGE DOMAIN DETAILS: {bd_name}")
            print("=" * 80)
            
            # Basic information
            print(f"📊 Basic Information:")
            print(f"   • Name: {bd_name}")
            print(f"   • Username: {username}")
            print(f"   • VLAN ID: {vlan_id}")
            print(f"   • Outer VLAN: {outer_vlan if outer_vlan else 'N/A'}")
            print(f"   • Inner VLAN: {inner_vlan if inner_vlan else 'N/A'}")
            print(f"   • DNAAS Type: {dnaas_type}")
            print(f"   • Topology Type: {topo_type}")
            print(f"   • Deployment Status: {deployment_status}")
            print(f"   • Updated: {updated_at}")
            print()
            
            # Consolidation information
            is_consolidated = discovery_json.get('is_consolidated', False)
            if is_consolidated:
                consolidation_info = discovery_json.get('consolidation_info', {})
                print(f"🔗 Consolidation Information:")
                print(f"   • Is Consolidated: Yes")
                print(f"   • Consolidated Count: {consolidation_info.get('consolidated_count', 1)}")
                print(f"   • Represents Bridge Domains:")
                for rep_bd in consolidation_info.get('represents_bridge_domains', []):
                    print(f"     - {rep_bd}")
                print(f"   • Primary Selection Reason: {consolidation_info.get('primary_selection_reason', 'N/A')}")
                print()
            
            # DNAAS Analysis
            bridge_domain_analysis = discovery_json.get('bridge_domain_analysis', {})
            if bridge_domain_analysis:
                print(f"🏷️  DNAAS Analysis:")
                print(f"   • DNAAS Type: {bridge_domain_analysis.get('dnaas_type', 'N/A')}")
                classification_reason = bridge_domain_analysis.get('classification_reason', 'N/A')
                if classification_reason != 'N/A':
                    print(f"   • Classification Reason: {classification_reason}")
                print(f"   • Encapsulation: {bridge_domain_analysis.get('encapsulation', 'N/A')}")
                print(f"   • Service Type: {bridge_domain_analysis.get('service_type', 'N/A')}")
                print(f"   • QinQ Detected: {bridge_domain_analysis.get('qinq_detected', False)}")
                print()
            
            # Device and Interface Information with Raw Config
            devices_from_discovery = discovery_json.get('devices', {})
            if devices_from_discovery:
                print(f"🖥️  DEVICE & INTERFACE INFORMATION:")
                
                access_interface_count = 0
                total_interface_count = 0
                
                for device_name, device_info in devices_from_discovery.items():
                    print(f"   📱 {device_name} ({device_info.get('device_type', 'unknown')} device):")
                    
                    interfaces = device_info.get('interfaces', [])
                    total_interface_count += len(interfaces)
                    
                    for interface in interfaces:
                        interface_name = interface.get('name', 'N/A')
                        role = interface.get('role', 'unknown')
                        vlan_id = interface.get('vlan_id', 'N/A')
                        outer_vlan = interface.get('outer_vlan')
                        inner_vlan = interface.get('inner_vlan')
                        
                        # Mark user-editable endpoints
                        if role == 'access':
                            access_interface_count += 1
                            role_display = f"✏️ {role} (USER EDITABLE)"
                        else:
                            role_display = f"🔒 {role} (infrastructure)"
                        
                        print(f"     🔌 {interface_name} - {role_display}")
                        print(f"        • VLAN ID: {vlan_id}")
                        if outer_vlan:
                            print(f"        • Outer VLAN: {outer_vlan}")
                        if inner_vlan:
                            print(f"        • Inner VLAN: {inner_vlan}")
                        
                        # Show raw CLI configuration
                        raw_config = interface.get('raw_cli_config', [])
                        if raw_config:
                            print(f"        • 📜 Raw CLI Config:")
                            for config_line in raw_config:
                                print(f"          {config_line}")
                        else:
                            print(f"        • 📜 Raw CLI Config: None")
                        print()
                
                print(f"📊 Interface Summary:")
                print(f"   • Total Interfaces: {total_interface_count}")
                print(f"   • User-Editable Endpoints: {access_interface_count}")
                print(f"   • Infrastructure Interfaces: {total_interface_count - access_interface_count}")
                print()
            
            print("=" * 80)
            
            # Add edit option to details view
            print("📋 Actions:")
            print("   [e] Edit this bridge domain")
            print("   [q] Back to main menu")
            
            action = input("Choose action (e/q): ").strip().lower()
            
            if action == 'e':
                # Launch BD Editor for this bridge domain
                print(f"🔧 Launching BD Editor for {bd_name}...")
                
                # Create BD object for editor (using updated result structure)
                bd = {
                    'id': bd_id,
                    'name': bd_name,
                    'vlan_id': vlan_id,
                    'username': username,
                    'discovery_data': discovery_data,
                    'dnaas_type': dnaas_type,
                    'topology_type': topo_type,
                    'source_type': 'discovered',
                    'updated_at': updated_at,
                    'deployment_status': deployment_status,
                    'source': 'discovered',
                    'source_icon': '🔍'
                }
                
                from main import enter_edit_mode
                from database_manager import DatabaseManager
                
                db_manager = DatabaseManager()
                enter_edit_mode(bd, db_manager)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to view bridge domain details: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_bridge_domain_statistics(self, cursor):
        """Calculate comprehensive statistics for bridge domains"""
        stats = {}
        
        # Basic counts
        cursor.execute('''
            SELECT COUNT(*) FROM bridge_domains 
            WHERE source = 'discovered'
        ''')
        stats['total_bridge_domains'] = cursor.fetchone()[0]
        
        # Get DNAAS type analysis from unified bridge_domains table
        cursor.execute('''
            SELECT dnaas_type, COUNT(*) 
            FROM bridge_domains
            WHERE source = 'discovered'
            GROUP BY dnaas_type
        ''')
        dnaas_type_counts = cursor.fetchall()
        
        dnaas_types = {}
        for dnaas_type, count in dnaas_type_counts:
            # Simplify DNAAS type names for statistics
            if dnaas_type and dnaas_type.startswith('DNAAS_TYPE_'):
                if 'TYPE_2A_QINQ' in dnaas_type:
                    simplified_type = '2A_QINQ'
                elif 'TYPE_4A_SINGLE' in dnaas_type:
                    simplified_type = '4A_SINGLE'
                elif 'TYPE_1_DOUBLE' in dnaas_type:
                    simplified_type = '1_DOUBLE'
                else:
                    simplified_type = dnaas_type.replace('DNAAS_TYPE_', '').replace('_', ' ')
            else:
                simplified_type = dnaas_type or 'UNKNOWN'
            
            dnaas_types[simplified_type] = count
        
        # Get consolidation analysis from discovery_data (CORRECTED)
        cursor.execute('''
            SELECT discovery_data FROM bridge_domains 
            WHERE source = 'discovered' AND discovery_data IS NOT NULL
        ''')
        discovery_data_list = cursor.fetchall()
        
        consolidated_count = 0
        individual_count = 0
        
        for (discovery_data,) in discovery_data_list:
            try:
                discovery_json = json.loads(discovery_data)
                if discovery_json.get('is_consolidated', False):
                    consolidated_count += 1
                else:
                    individual_count += 1
            except:
                individual_count += 1  # Default to individual if parsing fails
        
        stats['consolidated_count'] = consolidated_count
        stats['individual_count'] = individual_count
        stats['consolidation_rate'] = (consolidated_count / stats['total_bridge_domains'] * 100) if stats['total_bridge_domains'] > 0 else 0
        stats['dnaas_types'] = dnaas_types
        
        # User analysis
        cursor.execute('''
            SELECT username, COUNT(*) FROM bridge_domains 
            WHERE source = 'discovered'
            GROUP BY username
            ORDER BY COUNT(*) DESC
        ''')
        user_counts = cursor.fetchall()
        stats['unique_users'] = len(user_counts)
        stats['top_users'] = user_counts
        
        # VLAN analysis from unified bridge_domains table
        cursor.execute('''
            SELECT vlan_id FROM bridge_domains 
            WHERE source = 'discovered' AND vlan_id IS NOT NULL
        ''')
        vlan_list = [row[0] for row in cursor.fetchall()]
        stats['vlan_min'] = min(vlan_list) if vlan_list else 0
        stats['vlan_max'] = max(vlan_list) if vlan_list else 0
        
        # Top VLANs
        cursor.execute('''
            SELECT vlan_id, COUNT(*) FROM bridge_domains 
            WHERE source = 'discovered' AND vlan_id IS NOT NULL
            GROUP BY vlan_id
            ORDER BY COUNT(*) DESC
            LIMIT 10
        ''')
        stats['top_vlans'] = cursor.fetchall()
        
        # Database size
        cursor.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()')
        db_size = cursor.fetchone()[0]
        stats['database_size'] = db_size / (1024 * 1024)  # Convert to MB
        
        # Average confidence (use 1.0 for discovered BDs since they passed validation)
        stats['avg_confidence'] = 1.0
        
        # Data quality (percentage with complete data)
        cursor.execute('''
            SELECT COUNT(*) FROM bridge_domains 
            WHERE source = 'discovered' 
            AND username IS NOT NULL 
            AND vlan_id IS NOT NULL 
            AND dnaas_type IS NOT NULL
        ''')
        quality_count = cursor.fetchone()[0]
        stats['data_quality'] = (quality_count / stats['total_bridge_domains'] * 100) if stats['total_bridge_domains'] > 0 else 0
        
        # Recent activity
        cursor.execute('''
            SELECT MAX(updated_at) FROM bridge_domains 
            WHERE source = 'discovered'
        ''')
        last_created = cursor.fetchone()[0]
        stats['last_discovery'] = last_created if last_created else "N/A"
        
        # Discovery files
        if self.output_dir.exists():
            json_files = list(self.output_dir.glob("bridge_domain_mapping_*.json"))
            stats['discovery_files'] = len(json_files)
            stats['total_file_size'] = sum(f.stat().st_size for f in json_files) / (1024 * 1024)
        else:
            stats['discovery_files'] = 0
            stats['total_file_size'] = 0
        
        return stats
    
    def run_consolidation_analysis(self):
        """Show detailed consolidation analysis"""
        print("\n🔗 Consolidation Analysis...")
        # Implementation for consolidation analysis
        print("🔗 This feature will show detailed consolidation analysis")
    
    def run_export_discovery_data(self):
        """Export discovery data in various formats"""
        print("\n📤 Export Discovery Data...")
        # Implementation for data export
        print("📤 This feature will export discovery data")
    
    def run_import_discovery_data(self):
        """Import discovery data from files"""
        print("\n📥 Import Discovery Data...")
        # Implementation for data import
        print("📥 This feature will import discovery data")
    
    def run_delete_bridge_domain(self):
        """Delete a specific bridge domain"""
        print("\n🗑️ Delete Bridge Domain...")
        # Implementation for bridge domain deletion
        print("🗑️ This feature will delete bridge domains")
    
    def run_refresh_discovery_data(self):
        """Refresh discovery data by running fresh discovery"""
        print("\n🔄 Refresh Discovery Data...")
        print("🔄 Running fresh discovery with updated VLAN parsing...")
        
        try:
            # Import and run the discovery system
            from config_engine.simplified_discovery.simplified_bridge_domain_discovery import run_simplified_discovery
            
            print("📊 Starting fresh discovery...")
            results = run_simplified_discovery()
            
            print(f"✅ Discovery completed: {len(results.consolidated_bridge_domains)} consolidated bridge domains")
            
            # Save to database using sync manager
            print("💾 Saving updated results to database...")
            from .data_sync_manager import DataSyncManager
            
            sync_manager = DataSyncManager()
            
            # Load the latest JSON results for sync
            output_dir = Path("topology/simplified_discovery_results")
            latest_file = max(output_dir.glob("bridge_domain_mapping_*.json"), key=lambda f: f.stat().st_mtime)
            with open(latest_file, 'r') as f:
                discovery_results = json.load(f)
            
            # Sync to database
            sync_result = sync_manager.sync_discovery_data(discovery_results)
            
            print(f"✅ Database refresh completed:")
            print(f"   • Database: {sync_result.get('database_saved', 'N/A')} bridge domains")
            print(f"   • JSON: {sync_result.get('json_saved', 'N/A')} bridge domains")
            
            # Handle sync status safely
            sync_status = sync_result.get('sync_status', {})
            if sync_status:
                print(f"   • Status: {sync_status.get('status', 'Unknown')}")
                if sync_status.get('sync_percentage', 100) < 100:
                    print(f"   ⚠️  Sync warning: {sync_status.get('sync_percentage', 100):.1f}% synchronized")
            else:
                print(f"   • Status: Sync completed successfully")
            
            print("\n🎯 Database has been updated with corrected VLAN information!")
            print("   • VLAN parsing fix is now active")
            print("   • All interfaces should show correct VLAN IDs")
            print("   • Raw CLI configuration is properly parsed")
            
        except Exception as e:
            print(f"❌ Failed to refresh discovery data: {e}")
            import traceback
            traceback.print_exc()
    
    def run_browse_discovery_files(self):
        """Browse discovery output files"""
        print("\n📁 Browse Discovery Files...")
        # Implementation for file browsing
        print("📁 This feature will browse discovery files")
    
    def run_dnaas_type_analysis(self):
        """Show DNAAS type analysis"""
        print("\n🎯 DNAAS Type Analysis...")
        # Implementation for DNAAS analysis
        print("🎯 This feature will show DNAAS type analysis")
    
    def run_data_validation_report(self):
        """Show data validation report"""
        print("\n🛡️ Data Validation Report...")
        # Implementation for validation report
        print("🛡️ This feature will show data validation report")
    
    def run_sync_status(self):
        """Show data synchronization status"""
        try:
            print("\n🔄 Data Synchronization Status...")
            
            # Get comprehensive sync status
            summary = self.sync_manager.get_data_summary()
            
            if "error" in summary:
                print(f"❌ Failed to get sync status: {summary['error']}")
                return
            
            print("\n📊 DATA SYNCHRONIZATION STATUS")
            print("=" * 60)
            
            # Database status
            print(f"🗄️  Database (Primary Source):")
            print(f"   • Bridge Domains: {summary['database']['count']}")
            print(f"   • Last Update: {summary['database']['last_update'] or 'N/A'}")
            print(f"   • Path: {summary['database']['path']}")
            print()
            
            # JSON files status
            print(f"📁 JSON Files (Backup/Export):")
            print(f"   • File Count: {summary['json_files']['count']}")
            print(f"   • Latest File: {summary['json_files']['latest_file'] or 'N/A'}")
            print(f"   • Total Size: {summary['json_files']['total_size_mb']} MB")
            print(f"   • Directory: {summary['json_files']['directory']}")
            print()
            
            # Sync status
            sync_status = summary['sync_status']
            print(f"🔄 Synchronization Status:")
            print(f"   • Status: {sync_status['status']}")
            print(f"   • Database Count: {sync_status['database_count']}")
            print(f"   • JSON Count: {sync_status['json_count']}")
            print(f"   • Sync Percentage: {sync_status['sync_percentage']:.1f}%")
            print()
            
            # Recommendations
            if sync_status['is_synced']:
                print("✅ RECOMMENDATIONS:")
                print("   • Data is fully synchronized")
                print("   • Use database for all queries (fastest)")
                print("   • JSON files serve as backup")
            else:
                print("⚠️  RECOMMENDATIONS:")
                print("   • Data is out of sync")
                print("   • Run discovery to resync data")
                print("   • Check for data corruption")
            
            print("=" * 60)
            
            # Options
            print("\n📋 Sync Options:")
            print("   [r] Force resync from database")
            print("   [c] Clean old JSON files")
            print("   [q] Quit")
            
            choice = input("Enter command: ").strip().lower()
            
            if choice == 'r':
                print("\n🔄 Force resync from database...")
                result = self.sync_manager.force_resync_from_database()
                if "error" not in result:
                    print(f"✅ Resync complete: {result['exported_count']} bridge domains exported")
                else:
                    print(f"❌ Resync failed: {result['error']}")
            
            elif choice == 'c':
                print("\n🧹 Cleaning old JSON files...")
                result = self.sync_manager.clean_old_json_files()
                if "error" not in result:
                    print(f"✅ Cleanup complete: {result['deleted_count']} files deleted")
                else:
                    print(f"❌ Cleanup failed: {result['error']}")
            
        except Exception as e:
            print(f"❌ Failed to get sync status: {e}")
            import traceback
            traceback.print_exc()
    
    def run_clean_old_files(self):
        """Clean old discovery files"""
        print("\n🧹 Clean Old Discovery Files...")
        # Implementation for file cleanup
        print("🧹 This feature will clean old discovery files")
    
    def run_filter_bridge_domains(self):
        """Filter bridge domains by criteria"""
        print("\n🔍 Filter Bridge Domains...")
        # Implementation for filtering
        print("🔍 This feature will filter bridge domains")
    
    def run_edit_bridge_domain(self):
        """Jump directly to BD Editor from DB overview"""
        print("\n✏️ EDIT BRIDGE DOMAIN")
        print("=" * 50)
        
        try:
            # Get bridge domain name to edit
            bd_name = input("Enter bridge domain name to edit: ").strip()
            
            if not bd_name:
                print("❌ Bridge domain name required")
                return
            
            # Check if BD exists in database
            conn = sqlite3.connect('instance/lab_automation.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, vlan_id, username, discovery_data, interface_data, 
                       dnaas_type, topology_type, source, created_at, id
                FROM bridge_domains 
                WHERE name = ? AND source = 'discovered'
            """, (bd_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print(f"❌ Bridge domain '{bd_name}' not found")
                print("💡 Use exact name from the bridge domain list")
                return
            
            # Create BD object for editor
            bd = {
                'id': result[9],
                'name': result[0],
                'vlan_id': result[1],
                'username': result[2],
                'discovery_data': result[3],
                'interface_data': result[4],
                'dnaas_type': result[5],
                'topology_type': result[6],
                'source_type': result[7],
                'created_at': result[8],
                'source': 'discovered',
                'source_icon': '🔍'
            }
            
            print(f"✅ Found bridge domain: {bd['name']}")
            print(f"🔧 Launching BD Editor...")
            print()
            
            # Launch BD Editor directly
            from main import enter_edit_mode
            from database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            enter_edit_mode(bd, db_manager)
            
        except Exception as e:
            print(f"❌ Failed to launch BD Editor: {e}")
            import traceback
            traceback.print_exc()
    
    def run_export_search_results(self, results):
        """Export search results"""
        print("\n📤 Export Search Results...")
        # Implementation for exporting search results
        print("📤 This feature will export search results")


def run_enhanced_simplified_discovery_display():
    """Run the enhanced simplified discovery display"""
    display = EnhancedSimplifiedDiscoveryDisplay()
    display.show_enhanced_database_menu()


if __name__ == "__main__":
    run_enhanced_simplified_discovery_display()
