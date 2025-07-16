#!/usr/bin/env python3
import json

# Load topology data
with open('topology/complete_topology_v2.json', 'r') as f:
    data = json.load(f)

devices = data.get('devices', {})
print(f"Total devices: {len(devices)}")

# Find leaf devices with spine connections
leaves_with_spines = []
leaves_without_spines = []

for name, info in devices.items():
    if info.get('type') == 'leaf':
        connected_spines = info.get('connected_spines', [])
        if connected_spines:
            leaves_with_spines.append(name)
            print(f"\n{name} has {len(connected_spines)} spine connections:")
            for spine in connected_spines:
                print(f"  - {spine['name']} ({spine['local_interface']} <-> {spine['remote_interface']})")
        else:
            leaves_without_spines.append(name)

print(f"\n=== SUMMARY ===")
print(f"Leaves WITH spine connections: {len(leaves_with_spines)}")
print(f"Leaves WITHOUT spine connections: {len(leaves_without_spines)}")

if leaves_with_spines:
    print(f"\nYou can use these leaves for bridge domain testing:")
    for leaf in leaves_with_spines:
        print(f"  - {leaf}")
else:
    print(f"\n❌ No leaves have spine connections in the topology file!")
    print("This means the topology discovery/parsing is not working correctly.") 