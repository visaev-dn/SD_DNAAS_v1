#!/usr/bin/env python3
"""
Parse bundle-to-physical interface mapping from device XML configs
Handles incomplete XML by using regex pattern matching
Saves the result as a YAML file.
"""
import os
import glob
import re
import logging
import yaml

def parse_bundle_mapping(xml_file):
    """Parse a single XML config file and return {physical_interface: bundle_name} mapping"""
    mapping = {}
    try:
        with open(xml_file, 'r') as f:
            xml_content = f.read()
        
        # Find all LACP bundle interfaces and their members using regex
        # Pattern to match: <interface><name>bundle-XXXX</name><members>...</members></interface>
        bundle_pattern = r'<interface>\s*<name>(bundle-\d+)</name>\s*<members>(.*?)</members>'
        
        for bundle_match in re.finditer(bundle_pattern, xml_content, re.DOTALL):
            bundle_name = bundle_match.group(1)
            members_section = bundle_match.group(2)
            
            # Find all member interfaces within this bundle
            member_pattern = r'<member>\s*<interface>(ge\d+-\d+/\d+/\d+)</interface>'
            
            for member_match in re.finditer(member_pattern, members_section, re.DOTALL):
                physical_interface = member_match.group(1)
                mapping[physical_interface] = bundle_name
                logging.debug(f"Found mapping: {physical_interface} -> {bundle_name}")
        
        logging.info(f"Parsed {len(mapping)} bundle mappings from {xml_file}")
        
    except Exception as e:
        logging.error(f"Failed to parse {xml_file}: {e}")
    
    return mapping

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Look for XML files in the topology/configs directory
    topology_dir = os.path.join(os.path.dirname(__file__), '..', 'topology')
    configs_dir = os.path.join(topology_dir, 'configs')
    xml_files = glob.glob(os.path.join(configs_dir, 'config_*.xml'))
    
    if not xml_files:
        print("No config_*.xml files found in topology/configs directory.")
        return
    
    print("🔍 Parsing bundle mappings from XML configs...")
    print("=" * 60)
    
    all_mappings = {}
    for xml_file in xml_files:
        device = os.path.basename(xml_file).replace('config_', '').replace('.xml', '')
        mapping = parse_bundle_mapping(xml_file)
        all_mappings[device] = mapping
        print(f"\n📋 Device: {device}")
        if mapping:
            print("Physical interface -> Bundle mapping:")
            for phys, bundle in sorted(mapping.items()):
                print(f"  {phys} -> {bundle}")
        else:
            print("  No bundle mappings found.")
    
    # Save to YAML file in topology directory
    yaml_file = os.path.join(topology_dir, 'bundle_interface_mapping.yaml')
    with open(yaml_file, 'w') as f:
        yaml.dump(all_mappings, f, default_flow_style=False, indent=2)
    print(f"\n✅ Bundle mappings saved to {yaml_file}")
    print("\n" + "=" * 60)
    print("✅ Bundle mapping parsing completed!")

if __name__ == "__main__":
    main() 