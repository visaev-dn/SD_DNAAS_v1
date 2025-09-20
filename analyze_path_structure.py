#!/usr/bin/env python3
"""
Analyze Path Structure and Source/Dest Classification Issues
"""

import sys
import os
import traceback
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_path_structure():
    """Analyze the exact path structure and source/dest classification issues"""
    
    print("🔍 ANALYZING PATH STRUCTURE & SOURCE/DEST CLASSIFICATION ISSUES")
    print("=" * 80)
    
    try:
        # Import the necessary modules
        from config_engine.phase1_database import create_phase1_database_manager
        
        print("✅ Successfully imported database modules")
        
        # Create database manager
        db_manager = create_phase1_database_manager()
        print("✅ Successfully created database manager")
        
        # Phase 1: Analyze the specific failing topology
        print("\n🔍 PHASE 1: ANALYZING THE FAILING TOPOLOGY")
        print("-" * 60)
        
        try:
            import sqlite3
            
            db_path = "instance/lab_automation.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get the specific failing topology: g_visaev_v251_to_Spirent
                print("🔍 Investigating g_visaev_v251_to_Spirent topology structure...")
                
                cursor.execute("""
                    SELECT id, bridge_domain_name, topology_type, vlan_id, discovered_at, scan_method
                    FROM phase1_topology_data 
                    WHERE bridge_domain_name = 'g_visaev_v251_to_Spirent'
                """)
                
                topology_result = cursor.fetchone()
                if topology_result:
                    topology_id = topology_result[0]
                    print(f"✅ Found topology: ID={topology_id}, Name={topology_result[1]}")
                    print(f"   Type: {topology_result[2]}, VLAN: {topology_result[3]}")
                    
                    # Get the bridge domain config
                    cursor.execute("""
                        SELECT id, topology_id, service_name, bridge_domain_type, source_device, source_interface
                        FROM phase1_bridge_domain_config 
                        WHERE topology_id = ?
                    """, (topology_id,))
                    
                    config_result = cursor.fetchone()
                    if config_result:
                        print(f"✅ Bridge domain config: ID={config_result[0]}")
                        print(f"   Service: {config_result[2]}, Type: {config_result[3]}")
                        print(f"   Source Device: {config_result[4]}, Source Interface: {config_result[5]}")
                        
                        # Get all path segments for this topology
                        # First get the path_info, then get the segments
                        cursor.execute("""
                            SELECT id, path_name, path_type, source_device, dest_device
                            FROM phase1_path_info 
                            WHERE topology_id = ?
                        """, (topology_id,))
                        
                        path_info = cursor.fetchone()
                        if path_info:
                            path_id = path_info[0]
                            print(f"✅ Path info: ID={path_id}, Name={path_info[1]}, Type={path_info[2]}")
                            print(f"   Source: {path_info[3]}, Dest: {path_info[4]}")
                            
                            # Now get the path segments
                            cursor.execute("""
                                SELECT id, segment_type, source_device, source_interface, 
                                       dest_device, dest_interface, bandwidth
                                FROM phase1_path_segments 
                                WHERE path_id = ?
                                ORDER BY id
                            """, (path_id,))
                            
                            path_segments = cursor.fetchall()
                            print(f"\n🔍 Path segments found: {len(path_segments)}")
                            
                            if path_segments:
                                print("📋 Path segment analysis:")
                                for i, segment in enumerate(path_segments):
                                    print(f"   Segment {i}:")
                                    print(f"     Type: {segment[1]}")
                                    print(f"     Source: {segment[2]} ({segment[3]})")
                                    print(f"     Dest: {segment[4]} ({segment[5]})")
                                    print(f"     Bandwidth: {segment[6]}")
                                
                                # Analyze the path continuity issue
                                print(f"\n🔍 PATH CONTINUITY ANALYSIS:")
                                print("The validation error suggests:")
                                print("   'segment 0 ends at DNAAS-LEAF-B14, segment 1 starts at DNAAS-LEAF-B15'")
                                
                                if len(path_segments) >= 2:
                                    segment0_dest = path_segments[0][4]  # dest_device of first segment
                                    segment1_source = path_segments[1][2]  # source_device of second segment
                                    
                                    print(f"\n🔍 ACTUAL PATH DATA:")
                                    print(f"   Segment 0 destination: {segment0_dest}")
                                    print(f"   Segment 1 source: {segment1_source}")
                                    
                                    if segment0_dest != segment1_source:
                                        print(f"   ❌ PATH DISCONTINUITY CONFIRMED!")
                                        print(f"      Segment 0 ends at: {segment0_dest}")
                                        print(f"      Segment 1 starts at: {segment1_source}")
                                        print(f"      These should be the same device!")
                                    else:
                                        print(f"   ✅ Path appears continuous in database")
                                        
                                        # Check if there's a mismatch between what's stored and what's expected
                                        print(f"\n🔍 VALIDATION EXPECTATION vs REALITY:")
                                        print(f"   Database shows: {segment0_dest} -> {segment1_source}")
                                        print(f"   Validation expects: DNAAS-LEAF-B14 -> DNAAS-LEAF-B15")
                                        print(f"   This suggests a device name mismatch or validation logic error")
                            else:
                                print("❌ No path segments found for this path")
                        else:
                            print("❌ No path info found for this topology")
                    else:
                        print("❌ No bridge domain config found for this topology")
                else:
                    print("❌ Topology g_visaev_v251_to_Spirent not found")
                
                # Phase 2: Compare with a working topology
                print("\n🔍 PHASE 2: COMPARING WITH WORKING TOPOLOGY")
                print("-" * 60)
                
                print("🔍 Now let's look at the working topology: g_visaev_v251")
                
                cursor.execute("""
                    SELECT id, bridge_domain_name, topology_type, vlan_id
                    FROM phase1_topology_data 
                    WHERE bridge_domain_name = 'g_visaev_v251'
                """)
                
                working_topology = cursor.fetchone()
                if working_topology:
                    working_id = working_topology[0]
                    print(f"✅ Working topology: ID={working_id}, Name={working_topology[1]}")
                    
                    # Get path info for working topology
                    cursor.execute("""
                        SELECT id, path_name, path_type, source_device, dest_device
                        FROM phase1_path_info 
                        WHERE topology_id = ?
                    """, (working_id,))
                    
                    working_path_info = cursor.fetchone()
                    if working_path_info:
                        working_path_id = working_path_info[0]
                        print(f"✅ Working path info: ID={working_path_id}, Name={working_path_info[1]}")
                        
                        # Get path segments for working topology
                        cursor.execute("""
                            SELECT id, segment_type, source_device, source_interface, 
                                   dest_device, dest_interface
                            FROM phase1_path_segments 
                            WHERE path_id = ?
                            ORDER BY id
                        """, (working_path_id,))
                        
                        working_segments = cursor.fetchall()
                        print(f"🔍 Working topology path segments: {len(working_segments)}")
                        
                        if working_segments:
                            print("📋 Working path structure:")
                            for i, segment in enumerate(working_segments):
                                print(f"   Segment {i}: {segment[2]} -> {segment[4]}")
                            
                            # Check path continuity for working topology
                            if len(working_segments) > 1:
                                print(f"\n🔍 Working topology path continuity:")
                                for i in range(len(working_segments) - 1):
                                    current_dest = working_segments[i][4]
                                    next_source = working_segments[i + 1][2]
                                    if current_dest == next_source:
                                        print(f"   ✅ Segment {i} -> {i+1}: {current_dest} -> {next_source}")
                                    else:
                                        print(f"   ❌ Segment {i} -> {i+1}: {current_dest} -> {next_source}")
                
                conn.close()
                
            else:
                print(f"❌ Database file not found at: {db_path}")
                
        except Exception as e:
            print(f"❌ Error during path analysis: {e}")
            traceback.print_exc()
        
        # Phase 3: Brainstorm the solution
        print("\n🧠 PHASE 3: BRAINSTORMING THE RELIABLE SOLUTION")
        print("-" * 60)
        
        print("🎯 UNDERSTANDING THE PROBLEM:")
        print("Based on the analysis, the issue is NOT with source/dest classification between topologies.")
        print("The issue is with PATH CONTINUITY within a single topology.")
        print()
        print("🔍 WHAT'S HAPPENING:")
        print("1. Each topology has a 'source_device' (where the service starts)")
        print("2. Each topology has path segments that should form a continuous path")
        print("3. The validation expects: segment N ends at device X, segment N+1 starts at device X")
        print("4. But the data shows: segment 0 ends at DNAAS-LEAF-B14, segment 1 starts at DNAAS-LEAF-B15")
        print()
        print("🎯 THE REAL PROBLEM:")
        print("This is a PATH DATA INTEGRITY issue, not a source/dest classification issue.")
        print("The path segments don't connect properly within the topology.")
        print()
        print("🚀 RELIABLE SOLUTION APPROACHES:")
        print()
        print("1. 🔧 FIX THE DATA (Most Reliable):")
        print("   - Ensure path segments actually connect")
        print("   - Fix device name mismatches")
        print("   - Validate path continuity during discovery")
        print()
        print("2. 🔍 IMPROVE VALIDATION (More Robust):")
        print("   - Better error reporting for path issues")
        print("   - Automatic path repair suggestions")
        print("   - Graceful degradation for broken paths")
        print()
        print("3. 🎯 RELAX VALIDATION FOR CONSOLIDATION:")
        print("   - Allow consolidation even with path issues")
        print("   - Focus on VLAN identity, not path perfection")
        print("   - Mark path issues for later review")
        print()
        print("4. 🔄 HYBRID APPROACH (Recommended):")
        print("   - Fix obvious path issues automatically")
        print("   - Allow consolidation with path warnings")
        print("   - Provide clear reporting of what's broken")
        print()
        print("🎯 MY RECOMMENDATION:")
        print("The issue is NOT source/dest classification between topologies.")
        print("It's PATH CONTINUITY within individual topologies.")
        print("We should fix the path data AND improve validation reporting.")
        
    except Exception as e:
        print(f"❌ Fatal error during analysis: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    analyze_path_structure()
