#!/usr/bin/env python3
"""
Robust XML Config Collector using DNOSSSH
Collects complete XML configs from all devices, retries if incomplete.
"""

import yaml
import logging
import sys
import os
import re
import time
from pathlib import Path

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.dnos_ssh import DNOSSSH

CLOSING_TAG = '</config>'
MAX_RETRIES = 3

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def load_devices(devices_file: str = "devices.yaml") -> dict:
    try:
        with open(devices_file, 'r') as f:
            devices_data = yaml.safe_load(f)
        
        # Get defaults
        defaults = devices_data.get('defaults', {})
        
        # Handle new structure where devices are at root level, not under 'devices' key
        if 'devices' in devices_data:
            devices = devices_data.get('devices', {})
        else:
            # Devices are at root level, exclude 'defaults' key
            devices = {k: v for k, v in devices_data.items() if k != 'defaults'}
        
        # Merge each device config with defaults
        merged_devices = {}
        for device_name, device_config in devices.items():
            # Device-specific values override defaults
            merged_config = {**defaults, **device_config}
            merged_devices[device_name] = merged_config
            
        return merged_devices
            
    except Exception as e:
        print(f"Error loading devices from {devices_file}: {e}")
        return {}

def collect_complete_xml(device_name, device_config, logger):
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Attempt {attempt} collecting config from {device_name} ({device_config['mgmt_ip']})")
        ssh = DNOSSSH(
            hostname=device_config['mgmt_ip'],
            username=device_config['username'],
            password=device_config['password'],
            port=device_config.get('ssh_port', 22),
            debug=False
        )
        try:
            if not ssh.connect():
                logger.error(f"Failed to connect to {device_name}")
                continue
            logger.info(f"Successfully connected to {device_name}")

            # Use the new collect_xml_config method
            xml_output = ssh.collect_xml_config(timeout=180)
            
            # Clean up the output - remove command echo and prompt lines
            lines = xml_output.splitlines()
            cleaned_lines = []
            for line in lines:
                # Skip command echo and prompt lines
                if (line.strip().startswith('show config') or 
                    line.strip().startswith('display-xml') or 
                    line.strip().startswith('no-more') or
                    re.match(r'^[^<]*[#>]\s*$', line.strip())):
                    continue
                cleaned_lines.append(line)
            
            cleaned_xml = '\n'.join(cleaned_lines).strip()

            # Show first few lines for verification
            lines = cleaned_xml.split('\n')
            logger.debug(f"First 5 lines of XML config:")
            for i, line in enumerate(lines[:5]):
                logger.debug(f"  {i+1}: {line}")
            
            # Show last few lines for verification (without XML content)
            logger.debug(f"Last 5 lines of XML config:")
            for i, line in enumerate(lines[-5:]):
                logger.debug(f"  {i+1}: {line}")
            
            return True

        except Exception as e:
            logger.error(f"Error collecting XML config from {device_name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            ssh.disconnect()
    logger.error(f"❌ Failed to collect complete XML config from {device_name} after {MAX_RETRIES} attempts.")
    return False

def validate_xml_files(config_dir='topology/configs', closing_tag=CLOSING_TAG):
    incomplete = []
    for xml_file in Path(config_dir).glob('config_*.xml'):
        with open(xml_file, 'r') as f:
            content = f.read().strip()
        if not content.endswith(closing_tag):
            print(f"⚠️ Incomplete XML: {xml_file}")
            incomplete.append(xml_file)
        else:
            print(f"✅ Complete XML: {xml_file}")
    return incomplete

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Robust XML config collector')
    parser.add_argument('--devices', default='devices.yaml', help='Devices configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    setup_logging(args.debug)
    logger = logging.getLogger('XMLCollector')

    logger.info("🚀 Starting Robust XML Configuration Collection")
    logger.info("=" * 50)

    devices = load_devices(args.devices)
    if not devices:
        logger.error("No devices found in configuration")
        return

    logger.info(f"Found {len(devices)} devices to collect XML configs from")

    successful = 0
    failed = 0

    for device_name, device_config in devices.items():
        logger.info(f"\nProcessing device: {device_name}")
        if collect_complete_xml(device_name, device_config, logger):
            successful += 1
        else:
            failed += 1

    logger.info("\n" + "=" * 50)
    logger.info("📊 XML Configuration Collection Summary")
    logger.info("=" * 50)
    logger.info(f"  Total devices: {len(devices)}")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")

    # Validate all collected files
    logger.info("\nValidating collected XML files...")
    incomplete_files = validate_xml_files()
    if incomplete_files:
        logger.warning("Some XML files are incomplete. Consider re-collecting them.")

if __name__ == "__main__":
    main() 