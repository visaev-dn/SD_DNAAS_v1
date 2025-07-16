#!/usr/bin/env python3
"""
Full Topology Refresh Script (With Config Pull)
Complete topology refresh including device configuration collection, bundle parsing, and LLDP discovery
"""

import subprocess
import sys
import os
import time
import yaml
import json
from pathlib import Path
from datetime import datetime
from io import StringIO
import contextlib

class OutputCapture:
    """Class to capture all console output"""
    def __init__(self):
        self.output = []
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def write(self, text):
        """Capture written text"""
        self.output.append(text)
        self.original_stdout.write(text)
    
    def flush(self):
        """Flush the original stdout"""
        self.original_stdout.flush()
    
    def get_output(self):
        """Get captured output as string"""
        return ''.join(self.output)
    
    def clear(self):
        """Clear captured output"""
        self.output = []

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"   Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_prerequisites():
    """Check if required files and directories exist"""
    print("🔍 Checking prerequisites...")
    
    # Check if devices.yaml exists
    devices_file = Path("devices.yaml")
    if not devices_file.exists():
        print("❌ devices.yaml not found in current directory")
        print("   Please ensure you're running from the lab_automation directory")
        return False
    
    # Check if topology directory exists
    topology_dir = Path("topology")
    if not topology_dir.exists():
        print("📁 Creating topology directory...")
        topology_dir.mkdir(parents=True, exist_ok=True)
    
    print("✅ Prerequisites check passed")
    return True

def cleanup_temp_files():
    """Clean up temporary XML files"""
    print("\n🧹 Cleaning up temporary files...")
    
    topology_dir = Path("topology")
    temp_files = list(topology_dir.glob("temp_config_*.xml"))
    
    for temp_file in temp_files:
        try:
            temp_file.unlink()
            print(f"   Deleted: {temp_file.name}")
        except Exception as e:
            print(f"   Warning: Could not delete {temp_file.name}: {e}")
    
    print("✅ Cleanup completed")
    print("💾 XML config files preserved in topology/configs/")

def save_topology_json(analysis_data):
    """Save complete topology as JSON file"""
    if not analysis_data:
        return
    
    topology_json = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'refresh_type': 'full_refresh',
            'description': 'Complete topology with bundle mappings and spine-leaf connections'
        },
        'summary': {
            'spine_devices': analysis_data.get('spine_devices', []),
            'leaf_devices': analysis_data.get('leaf_devices', []),
            'total_connections': analysis_data.get('total_connections', 0),
            'spine_leaf_connections': len(analysis_data.get('spine_leaf_connections', [])),
            'bundle_connections': len(analysis_data.get('bundle_connections', [])),
            'bundle_count': len(analysis_data.get('bundle_mappings', {}))
        },
        'bundle_mappings': analysis_data.get('bundle_mappings', {}),
        'spine_leaf_connections': analysis_data.get('spine_leaf_connections', []),
        'bundle_connections': analysis_data.get('bundle_connections', []),
        'visualization': generate_visualization(analysis_data)
    }
    
    json_file = Path("topology/complete_topology.json")
    with open(json_file, 'w') as f:
        json.dump(topology_json, f, indent=2)
    
    print(f"💾 Complete topology saved to: {json_file}")

def generate_visualization(analysis_data):
    """Generate a visual representation of the topology"""
    if not analysis_data:
        return {}
    
    visualization = {
        'spine_devices': {},
        'leaf_devices': {},
        'connections': [],
        'bundle_groups': {}
    }
    
    # Process spine devices
    for spine in analysis_data.get('spine_devices', []):
        visualization['spine_devices'][spine] = {
            'type': 'spine',
            'connections': []
        }
    
    # Process leaf devices
    for leaf in analysis_data.get('leaf_devices', []):
        visualization['leaf_devices'][leaf] = {
            'type': 'leaf',
            'connections': []
        }
    
    # Process spine-leaf connections
    for conn in analysis_data.get('spine_leaf_connections', []):
        if conn['device1'].startswith('spine'):
            spine = conn['device1']
            leaf = conn['device2']
            spine_intf = conn['interface1']
            leaf_intf = conn['interface2']
        else:
            spine = conn['device2']
            leaf = conn['device1']
            spine_intf = conn['interface2']
            leaf_intf = conn['interface1']
        
        connection_info = {
            'spine': spine,
            'spine_interface': spine_intf,
            'leaf': leaf,
            'leaf_interface': leaf_intf,
            'bundle': None
        }
        
        # Check if this connection uses a bundle
        bundle_mappings = analysis_data.get('bundle_mappings', {})
        if spine in bundle_mappings and spine_intf in bundle_mappings[spine]:
            connection_info['bundle'] = bundle_mappings[spine][spine_intf]
        
        visualization['connections'].append(connection_info)
        
        # Add to device connection lists
        if spine in visualization['spine_devices']:
            visualization['spine_devices'][spine]['connections'].append(connection_info)
        if leaf in visualization['leaf_devices']:
            visualization['leaf_devices'][leaf]['connections'].append(connection_info)
    
    # Group by bundles
    bundle_mappings = analysis_data.get('bundle_mappings', {})
    for device, mappings in bundle_mappings.items():
        for phys_intf, bundle_name in mappings.items():
            if bundle_name not in visualization['bundle_groups']:
                visualization['bundle_groups'][bundle_name] = []
            visualization['bundle_groups'][bundle_name].append({
                'device': device,
                'interface': phys_intf
            })
    
    return visualization

def save_refresh_summary(analysis_data):
    """Save a summary of the topology refresh"""
    if not analysis_data:
        return
    
    summary = {
        'refresh_timestamp': datetime.now().isoformat(),
        'refresh_type': 'full_refresh',
        'summary': {
            'spine_devices': analysis_data.get('spine_devices', []),
            'leaf_devices': analysis_data.get('leaf_devices', []),
            'total_connections': analysis_data.get('total_connections', 0),
            'spine_leaf_connections': len(analysis_data.get('spine_leaf_connections', [])),
            'bundle_connections': len(analysis_data.get('bundle_connections', [])),
            'bundle_count': len(analysis_data.get('bundle_mappings', {}))
        },
        'files_generated': [
            'topology/temp_config_*.xml',
            'topology/bundle_interface_mapping.yaml',
            'topology/discovered_topology_bundles.yaml',
            'topology/complete_topology.json',
            'topology/topology_refresh_full_summary.yaml'
        ]
    }
    
    summary_file = Path("topology/topology_refresh_full_summary.yaml")
    with open(summary_file, 'w') as f:
        yaml.dump(summary, f, default_flow_style=False, indent=2)
    
    print(f"\n💾 Full refresh summary saved to: {summary_file}")

def main():
    """Main function to orchestrate the full topology refresh"""
    # Initialize output capture
    output_capture = OutputCapture()
    sys.stdout = output_capture
    sys.stderr = output_capture
    
    try:
        print("🚀 Full Topology Refresh (XML Collection & Bundle Mapping Only)")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check prerequisites
        if not check_prerequisites():
            print("\n❌ Prerequisites check failed. Exiting.")
            save_discovery_summary(output_capture.get_output())
            sys.exit(1)
        
        # Step 1: Collect XML configurations
        if not run_command(
            "python scripts/collect_complete_xml_configs.py",
            "Collecting XML configurations from all devices"
        ):
            print("\n❌ XML collection failed. Exiting.")
            save_discovery_summary(output_capture.get_output())
            sys.exit(1)
        
        # Step 2: Parse bundle mappings
        if not run_command(
            "python scripts/parse_bundle_mapping_from_xml.py",
            "Parsing bundle mappings from XML configurations"
        ):
            print("\n❌ Bundle parsing failed. Exiting.")
            save_discovery_summary(output_capture.get_output())
            sys.exit(1)
        
        # Step 3: Map complete topology (bundle-based only)
        print("\n🔄 Mapping complete topology with bundle mappings")
        print("-" * 60)
        
        try:
            # Import and run the mapping function
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from scripts.map_complete_topology import analyze_topology
            
            analysis_data = analyze_topology()
            
            if analysis_data:
                print("✅ Complete topology mapping completed successfully")
            else:
                print("❌ Complete topology mapping failed")
                save_discovery_summary(output_capture.get_output())
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Complete topology mapping failed with exception: {e}")
            save_discovery_summary(output_capture.get_output())
            sys.exit(1)
        
        # Save topology as JSON
        save_topology_json(analysis_data)
        
        # Optional: Clean up temporary files
        cleanup_temp_files()
        
        # Save refresh summary
        save_refresh_summary(analysis_data)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎉 Full Topology Refresh Completed Successfully!")
        print("=" * 80)
        
        if analysis_data:
            print(f"📊 Topology Summary:")
            print(f"   • Spine devices: {len(analysis_data.get('spine_devices', []))}")
            print(f"   • Leaf devices: {len(analysis_data.get('leaf_devices', []))}")
            print(f"   • Total connections: {analysis_data.get('total_connections', 0)}")
            print(f"   • Spine-leaf connections: {len(analysis_data.get('spine_leaf_connections', []))}")
            print(f"   • Bundle connections: {len(analysis_data.get('bundle_connections', []))}")
        
        print(f"\n📁 Generated files:")
        print(f"   • topology/bundle_interface_mapping.yaml")
        print(f"   • topology/discovered_topology_bundles.yaml")
        print(f"   • topology/complete_topology.json")
        print(f"   • topology/topology_refresh_full_summary.yaml")
        print(f"   • topology/discovery_summary_detailed.txt")
        
        print(f"\n⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save the complete discovery summary
        save_discovery_summary(output_capture.get_output())
        
        return 0
        
    finally:
        # Restore original stdout
        sys.stdout = output_capture.original_stdout
        sys.stderr = output_capture.original_stderr

def save_discovery_summary(output_text):
    """Save detailed discovery summary to text file"""
    summary_file = Path("topology/discovery_summary_detailed.txt")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(summary_file, 'w') as f:
            f.write(output_text)
        print(f"\n💾 Detailed discovery summary saved to: {summary_file}")
    except Exception as e:
        print(f"❌ Failed to save discovery summary: {e}")

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Full topology refresh interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 