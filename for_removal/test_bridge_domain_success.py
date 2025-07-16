#!/usr/bin/env python3
"""
Test script for bridge domain builder using leaves with spine connections
"""

from config_engine.bridge_domain_builder import BridgeDomainBuilder

# Choose two leaves with spine connections
source_leaf = "DNAAS-LEAF-B10"
dest_leaf = "DNAAS-LEAF-B15"
source_port = "ge100-0/0/10"  # Example port, adjust as needed
dest_port = "ge100-0/0/20"    # Example port, adjust as needed
service_name = "test_service"
vlan_id = 100

print(f"Testing bridge domain build: {source_leaf} ({source_port}) → {dest_leaf} ({dest_port})")

builder = BridgeDomainBuilder()
configs = builder.build_bridge_domain_config(
    service_name, vlan_id,
    source_leaf, source_port,
    dest_leaf, dest_port
)

if configs:
    print("\n✅ Bridge domain configuration built successfully!")
    for device, config_lines in configs.items():
        print(f"\n--- {device} ---")
        for line in config_lines:
            print(line)
else:
    print("\n❌ Failed to build bridge domain configuration.") 