#!/usr/bin/env python3
"""
Topology Discovery Script - Automatically discovers network topology using LLDP data
Usage: python discover_topology.py [--devices devices.yaml] [--output discovered_topology.yaml]
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path
from utils.topology_discovery import discover_and_save_topology

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_devices_from_file(filename: str) -> dict:
    """Load device information from YAML file"""
    try:
        with open(filename, 'r') as f:
            devices_yaml = yaml.safe_load(f)
        devices = devices_yaml['devices']
        # Validate device format
        for device_name, device_info in devices.items():
            required_fields = ['mgmt_ip', 'username', 'password']
            for field in required_fields:
                if field not in device_info:
                    raise ValueError(f"Device {device_name} missing required field: {field}")
        logger.info(f"Loaded {len(devices)} devices from {filename}")
        return devices
        
    except FileNotFoundError:
        logger.error(f"Device file not found: {filename}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing device file {filename}: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid device configuration: {e}")
        sys.exit(1)

def create_sample_devices_file(filename: str = "devices.yaml"):
    """Create a sample devices configuration file"""
    sample_devices = {
        "leaf01": {
            "mgmt_ip": "10.0.0.1",
            "device_type": "arista_eos",
            "username": "admin",
            "password": "admin123",
            "netconf_port": 830
        },
        "leaf02": {
            "mgmt_ip": "10.0.0.2",
            "device_type": "arista_eos",
            "username": "admin",
            "password": "admin123",
            "netconf_port": 830
        },
        "spine01": {
            "mgmt_ip": "10.0.0.254",
            "device_type": "arista_eos",
            "username": "admin",
            "password": "admin123",
            "netconf_port": 830
        },
        "spine02": {
            "mgmt_ip": "10.0.0.253",
            "device_type": "arista_eos",
            "username": "admin",
            "password": "admin123",
            "netconf_port": 830
        }
    }
    
    try:
        with open(filename, 'w') as f:
            yaml.dump(sample_devices, f, default_flow_style=False, indent=2)
        logger.info(f"Sample devices file created: {filename}")
        logger.info("Please update the IP addresses and credentials with your actual device information")
    except Exception as e:
        logger.error(f"Failed to create sample devices file: {e}")

def main():
    """Main function for topology discovery"""
    parser = argparse.ArgumentParser(
        description="Discover network topology using NETCONF LLDP data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover topology using default devices.yaml
  python discover_topology.py
  
  # Discover topology with custom device file
  python discover_topology.py --devices my_devices.yaml
  
  # Discover topology and save to custom output file
  python discover_topology.py --output topology/my_topology.yaml
  
  # Create sample devices file
  python discover_topology.py --create-sample
        """
    )
    
    parser.add_argument(
        '--devices', '-d',
        default='devices.yaml',
        help='YAML file containing device information (default: devices.yaml)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='topology/discovered_topology.yaml',
        help='Output file for discovered topology (default: topology/discovered_topology.yaml)'
    )
    
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create a sample devices.yaml file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create sample file if requested
    if args.create_sample:
        create_sample_devices_file(args.devices)
        return
    
    logger.info("🚀 Network Topology Discovery Tool")
    logger.info("=" * 50)
    
    # Check if devices file exists
    if not Path(args.devices).exists():
        logger.error(f"Devices file not found: {args.devices}")
        logger.info("Use --create-sample to create a sample devices.yaml file")
        sys.exit(1)
    
    try:
        # Load device information
        devices = load_devices_from_file(args.devices)
        
        # Discover topology
        logger.info("Starting topology discovery...")
        topology = discover_and_save_topology(devices, args.output)
        
        # Display summary
        logger.info("\n" + "=" * 50)
        logger.info("🎉 Topology Discovery Summary")
        logger.info("=" * 50)
        
        discovered_devices = topology['devices']
        connections = topology['connections']
        spine_links = topology['spine_links']
        leaf_links = topology['leaf_links']
        
        logger.info(f"📋 Discovered Devices: {len(discovered_devices)}")
        for device_name, device_info in discovered_devices.items():
            logger.info(f"  - {device_name}: {device_info['mgmt_ip']} ({len(device_info['ports'])} ports)")
        
        logger.info(f"🔗 Total Connections: {len(connections)}")
        logger.info(f"🌳 Spine Links: {len(spine_links)}")
        logger.info(f"🍃 Leaf Links: {len(leaf_links)}")
        
        # Show connection details
        if connections:
            logger.info("\n📋 Connection Details:")
            for conn in connections:
                logger.info(f"  {conn['local_device']}:{conn['local_port']} ↔ {conn['remote_device']}:{conn['remote_port']}")
        
        logger.info(f"\n💾 Topology saved to: {args.output}")
        logger.info("✅ Topology discovery completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Topology discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Topology discovery failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 