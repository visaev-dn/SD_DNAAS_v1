#!/usr/bin/env python3
"""
Enhanced Topology Discovery Script
Runs enhanced topology discovery with device name normalization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.enhanced_topology_discovery import enhanced_discovery

def main():
    """Run enhanced topology discovery with normalization."""
    print("🔧 Enhanced Topology Discovery with Normalization")
    print("=" * 60)
    
    try:
        # Run enhanced topology discovery
        enhanced_topology = enhanced_discovery.discover_topology_with_normalization()
        
        if enhanced_topology:
            print("✅ Enhanced topology discovery completed successfully!")
            
            # Show normalization statistics
            stats = enhanced_discovery.export_normalization_data()
            print(f"\n📊 Normalization Statistics:")
            print(f"  • Device mappings: {len(stats['device_mappings'])}")
            print(f"  • Spine mappings: {len(stats['spine_mappings'])}")
            print(f"  • Issues found: {len(stats['issues_found'].get('missing_spine_connections', []))}")
            print(f"  • Fixes applied: {len(stats['fixes_applied'].get('spine_mappings', []))}")
            
            # Generate and display normalization report
            report = enhanced_discovery.generate_normalization_report()
            print(f"\n📋 Normalization Report:")
            print(report)
            
            print(f"\n📁 Files generated:")
            print(f"  • topology/enhanced_topology.json - Enhanced topology with normalization")
            print(f"  • topology/enhanced_topology_summary.json - Normalization summary")
            print(f"  • topology/device_mappings.json - Device name mappings")
            
        else:
            print("❌ Enhanced topology discovery failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error during enhanced topology discovery: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 