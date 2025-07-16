#!/usr/bin/env python3
"""
Unified Inventory Management Script
Handles all inventory-related operations:
- Populate devices.yaml from Excel inventory
- Clean/fix devices.yaml structure
- Create test inventory file
"""

import sys
import pandas as pd
import yaml
import requests
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
import argparse

class InventoryManager:
    """Unified inventory management for devices.yaml"""
    
    def __init__(self):
        self.logger = logging.getLogger('InventoryManager')
        self.inventory_url = "https://drivenets-my.sharepoint.com/:x:/r/personal/nchuosho_drivenets_com/Documents/shared/IL%20LAB/ICT/DNAAS%20Inventory.xlsx?d=w3b24c7c659154f90ad46b0c85b43ae67&csf=1&web=1&e=xA6zXa"
        self.devices_file = Path("devices.yaml")
        self.local_inventory_file = Path("inventory/DNAAS_Inventory.xlsx")
        
        # Define defaults
        self.defaults = {
            'username': 'sisaev',
            'password': 'Drive1234!',
            'ssh_port': 22,
            'netconf_port': 830,
            'device_type': 'arista_eos'
        }
        
    def download_inventory_file(self) -> Optional[Path]:
        """Download the inventory Excel file from SharePoint"""
        try:
            self.logger.info("Attempting to download inventory file from SharePoint...")
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            temp_path = Path(temp_file.name)
            
            response = requests.get(self.inventory_url, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded inventory file to: {temp_path}")
            return temp_path
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                self.logger.warning("SharePoint access denied (403). This is expected for SharePoint URLs.")
                self.logger.info("Please manually download the inventory file and place it in the 'inventory' folder.")
                return None
            else:
                self.logger.error(f"HTTP error downloading inventory file: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to download inventory file: {e}")
            return None
    
    def find_inventory_file(self) -> Optional[Path]:
        """Find inventory file in local directories"""
        possible_locations = [
            self.local_inventory_file,
            Path("DNAAS_Inventory.xlsx"),
            Path("inventory/DNAAS Inventory.xlsx"),
            Path("DNAAS Inventory.xlsx")
        ]
        
        for location in possible_locations:
            if location.exists():
                self.logger.info(f"Found inventory file: {location}")
                return location
        
        self.logger.warning("No inventory file found in expected locations:")
        for location in possible_locations:
            self.logger.warning(f"  - {location}")
        
        return None
    
    def get_inventory_file(self) -> Optional[Path]:
        """Get inventory file either by download or from local storage"""
        excel_file = self.download_inventory_file()
        if excel_file:
            return excel_file
        
        self.logger.info("Looking for local inventory file...")
        excel_file = self.find_inventory_file()
        if excel_file:
            return excel_file
        
        self.logger.error("No inventory file available.")
        self.logger.info("Please:")
        self.logger.info("1. Download the inventory file from SharePoint manually")
        self.logger.info("2. Place it in the 'inventory' folder as 'DNAAS_Inventory.xlsx'")
        self.logger.info("3. Run this script again")
        
        return None
    
    def parse_excel_inventory(self, excel_file: Path) -> List[Dict]:
        """Parse Excel file and extract deployed devices"""
        try:
            self.logger.info(f"Parsing Excel file: {excel_file}")
            
            df = pd.read_excel(excel_file)
            self.logger.info(f"Found {len(df)} total devices in inventory")
            
            # Filter for deployed devices
            status_columns = ['Status', 'Deployment Status', 'Deployment_Status', 'status']
            status_col = None
            
            for col in status_columns:
                if col in df.columns:
                    status_col = col
                    break
            
            if status_col is None:
                self.logger.warning("No status column found. Available columns:")
                for col in df.columns:
                    self.logger.warning(f"  - {col}")
                return []
            
            # Filter for deployed devices
            deployed_df = df[df[status_col].str.lower().str.contains('deployed', na=False)]
            self.logger.info(f"Found {len(deployed_df)} deployed devices")
            
            # Extract device information
            devices = []
            column_mappings = {
                'hostname': ['Name', 'Hostname', 'Device Name', 'hostname'],
                'mgmt_ip': ['IP Adress', 'Management IP', 'IP Address', 'Management_IP', 'mgmt_ip'],
                'device_type': ['Device Type', 'Type', 'Model', 'device_type'],
                'location': ['Location', 'Site', 'Rack', 'location'],
                'role': ['Role', 'Function', 'role']
            }
            
            for _, row in deployed_df.iterrows():
                device = {}
                
                # Extract fields using column mappings
                for field, possible_columns in column_mappings.items():
                    for col in possible_columns:
                        if col in df.columns and pd.notna(row[col]):
                            device[field] = str(row[col]).strip()
                            break
                
                # Only add device if it has required fields
                if device.get('hostname') and device.get('mgmt_ip'):
                    devices.append(device)
                else:
                    self.logger.warning(f"Skipping device with missing required fields: {row.to_dict()}")
            
            self.logger.info(f"Successfully parsed {len(devices)} devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to parse Excel file: {e}")
            return []
    
    def clean_devices_yaml(self) -> bool:
        """Clean devices.yaml structure and add defaults"""
        try:
            if not self.devices_file.exists():
                self.logger.info("devices.yaml not found, will create new one")
                return True
            
            with open(self.devices_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Handle case where devices are nested under 'devices' key
            if 'devices' in data and isinstance(data['devices'], dict):
                devices_data = data['devices']
            else:
                devices_data = data
            
            # Remove per-device connection fields
            cleaned = {}
            for hostname, device in devices_data.items():
                if hostname == 'defaults':
                    continue
                if not isinstance(device, dict):
                    cleaned[hostname] = device
                    continue
                cleaned[hostname] = {k: v for k, v in device.items() if k not in self.defaults}
            
            # Write back with defaults at the top
            output = {'defaults': self.defaults}
            output.update(cleaned)
            with open(self.devices_file, 'w') as f:
                yaml.dump(output, f, default_flow_style=False, sort_keys=False)
            
            self.logger.info("✅ Cleaned devices.yaml and added defaults section")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clean devices.yaml: {e}")
            return False
    
    def update_devices_yaml(self, devices: List[Dict]) -> bool:
        """Update devices.yaml with new device information"""
        try:
            # Load existing devices.yaml if it exists
            existing_devices = {}
            if self.devices_file.exists():
                with open(self.devices_file, 'r') as f:
                    existing_devices = yaml.safe_load(f)
                    if not isinstance(existing_devices, dict):
                        existing_devices = {}
            
            # Remove any old per-device connection fields
            updated_devices = {}
            for hostname, device in existing_devices.items():
                if hostname == 'defaults':
                    continue
                # Remove connection fields if present
                device = {k: v for k, v in device.items() if k not in self.defaults}
                updated_devices[hostname] = device
            
            # Add/Update with new devices
            for device in devices:
                hostname = device['hostname']
                mgmt_ip = device['mgmt_ip']
                # Only keep device-specific fields
                updated_devices[hostname] = {
                    'mgmt_ip': mgmt_ip,
                    'device_type': device.get('device_type', 'unknown'),
                    'location': device.get('location', 'unknown'),
                    'role': device.get('role', 'unknown'),
                    'status': 'active'
                }
            
            # Write updated devices.yaml with defaults at the top
            output = {'defaults': self.defaults}
            output.update(updated_devices)
            with open(self.devices_file, 'w') as f:
                yaml.dump(output, f, default_flow_style=False, sort_keys=False)
            
            self.logger.info(f"Updated devices.yaml with {len(devices)} devices and defaults section")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update devices.yaml: {e}")
            return False
    
    def create_test_inventory(self) -> bool:
        """Create a test inventory Excel file"""
        try:
            # Sample inventory data
            data = {
                'Hostname': [
                    'spine01', 'spine02', 'leaf_b14', 'leaf_b15', 'leaf_b16',
                    'DNAAS-SPINE-B09', 'DNAAS-LEAF-A01', 'DNAAS-LEAF-A02'
                ],
                'Management IP': [
                    '192.168.1.10', '192.168.1.11', '192.168.1.20', '192.168.1.21',
                    '192.168.1.22', '192.168.1.30', '192.168.1.40', '192.168.1.41'
                ],
                'Device Type': [
                    'DNOS-Spine', 'DNOS-Spine', 'DNOS-Leaf', 'DNOS-Leaf', 'DNOS-Leaf',
                    'DNOS-Spine', 'DNOS-Leaf', 'DNOS-Leaf'
                ],
                'Location': ['IL LAB'] * 8,
                'Role': ['Spine', 'Spine', 'Leaf', 'Leaf', 'Leaf', 'Spine', 'Leaf', 'Leaf'],
                'Status': [
                    'Deployed', 'Deployed', 'Deployed', 'Deployed', 'Planning',
                    'Deployed', 'Deployed', 'Planning'
                ]
            }
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Create inventory directory if it doesn't exist
            inventory_dir = Path("inventory")
            inventory_dir.mkdir(exist_ok=True)
            
            # Save to Excel file
            output_file = inventory_dir / "DNAAS_Inventory.xlsx"
            df.to_excel(output_file, index=False)
            
            self.logger.info(f"✅ Created test inventory file: {output_file}")
            self.logger.info(f"📊 Contains {len(df)} devices, {len(df[df['Status'] == 'Deployed'])} deployed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create test inventory: {e}")
            return False
    
    def populate_from_inventory(self) -> bool:
        """Main function to populate devices from inventory"""
        try:
            self.logger.info("Starting inventory population process...")
            
            # Get inventory file
            excel_file = self.get_inventory_file()
            if not excel_file:
                return False
            
            try:
                # Parse Excel file
                devices = self.parse_excel_inventory(excel_file)
                if not devices:
                    self.logger.error("No deployed devices found in inventory")
                    return False
                
                # Update devices.yaml
                success = self.update_devices_yaml(devices)
                return success
                
            finally:
                # Clean up temporary file if it was downloaded
                if excel_file.name.startswith('/tmp') or excel_file.name.startswith('/var/tmp'):
                    if excel_file.exists():
                        excel_file.unlink()
                        self.logger.info("Cleaned up temporary inventory file")
            
        except Exception as e:
            self.logger.error(f"Inventory population failed: {e}")
            return False

def main():
    """Main entry point with command line interface"""
    parser = argparse.ArgumentParser(description='Inventory Management Tool')
    parser.add_argument('action', choices=['populate', 'clean', 'test', 'create-test'], 
                       help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize manager
    manager = InventoryManager()
    
    # Perform requested action
    if args.action == 'populate':
        success = manager.populate_from_inventory()
        if success:
            print("✅ Successfully populated devices.yaml from inventory")
        else:
            print("❌ Failed to populate devices.yaml from inventory")
            sys.exit(1)
    
    elif args.action == 'clean':
        success = manager.clean_devices_yaml()
        if success:
            print("✅ Successfully cleaned devices.yaml")
        else:
            print("❌ Failed to clean devices.yaml")
            sys.exit(1)
    
    elif args.action == 'test':
        success = manager.create_test_inventory()
        if success:
            print("✅ Successfully created test inventory")
        else:
            print("❌ Failed to create test inventory")
            sys.exit(1)
    
    elif args.action == 'create-test':
        # Create test inventory and then populate
        if manager.create_test_inventory():
            print("✅ Created test inventory, now populating devices.yaml...")
            success = manager.populate_from_inventory()
            if success:
                print("✅ Successfully populated devices.yaml from test inventory")
            else:
                print("❌ Failed to populate devices.yaml from test inventory")
                sys.exit(1)
        else:
            print("❌ Failed to create test inventory")
            sys.exit(1)

if __name__ == "__main__":
    main() 