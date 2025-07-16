#!/usr/bin/env python3
"""
Enhanced Topology Discovery - Future-proof topology discovery with naming normalization
Integrates device name normalization to handle naming inconsistencies automatically.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from .device_name_normalizer import normalizer, DeviceType

logger = logging.getLogger(__name__)

class EnhancedTopologyDiscovery:
    """
    Enhanced topology discovery with automatic naming normalization.
    
    Features:
    - Automatic device name normalization
    - Intelligent spine connection mapping
    - Validation and issue detection
    - Self-healing topology fixes
    - Comprehensive reporting
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """Initialize enhanced topology discovery."""
        self.topology_dir = Path(topology_dir)
        self.normalizer = normalizer
        self.device_mappings = {}
        self.spine_mappings = {}
        self.issues_found = {}
        self.fixes_applied = {}
        
        # Load existing mappings if available
        self._load_existing_mappings()
    
    def _load_existing_mappings(self):
        """Load existing device mappings from file."""
        mappings_file = self.topology_dir / "device_mappings.json"
        if mappings_file.exists():
            try:
                with open(mappings_file, 'r') as f:
                    mappings = json.load(f)
                self.normalizer.import_mappings(mappings)
                logger.info(f"Loaded {len(mappings.get('name_mappings', {}))} device mappings")
            except Exception as e:
                logger.warning(f"Failed to load device mappings: {e}")
    
    def _save_mappings(self):
        """Save device mappings to file."""
        mappings_file = self.topology_dir / "device_mappings.json"
        mappings = self.normalizer.export_mappings()
        
        try:
            with open(mappings_file, 'w') as f:
                json.dump(mappings, f, indent=2)
            logger.info(f"Saved {len(mappings.get('name_mappings', {}))} device mappings")
        except Exception as e:
            logger.error(f"Failed to save device mappings: {e}")
    
    def discover_topology_with_normalization(self, device_status_file: str = "topology/device_status.json") -> Dict:
        """
        Discover topology with automatic naming normalization.
        
        Args:
            device_status_file: Path to device status file
            
        Returns:
            Enhanced topology data with normalized names
        """
        logger.info("Starting enhanced topology discovery with naming normalization...")
        
        # Load device status
        with open(device_status_file, 'r') as f:
            device_status = json.load(f)
        
        # Normalize all device names
        self._normalize_device_names(device_status)
        
        # Load existing topology
        topology_file = self.topology_dir / "complete_topology_v2.json"
        if topology_file.exists():
            with open(topology_file, 'r') as f:
                topology_data = json.load(f)
        else:
            logger.error("No existing topology found")
            return {}
        
        # Apply naming normalization to topology
        normalized_topology = self._apply_normalization_to_topology(topology_data)
        
        # Validate and fix connectivity issues
        self._validate_and_fix_connectivity(normalized_topology)
        
        # Save enhanced topology
        enhanced_topology_file = self.topology_dir / "enhanced_topology.json"
        with open(enhanced_topology_file, 'w') as f:
            json.dump(normalized_topology, f, indent=2)
        
        # Save mappings
        self._save_mappings()
        
        # Generate enhanced summary
        self._generate_enhanced_summary(normalized_topology)
        
        logger.info("Enhanced topology discovery completed")
        return normalized_topology
    
    def _normalize_device_names(self, device_status: Dict):
        """Normalize all device names in device status."""
        devices = device_status.get('devices', {})
        
        for device_name in list(devices.keys()):  # Convert to list to avoid modification during iteration
            normalized_name = self.normalizer.normalize_device_name(device_name)
            if normalized_name != device_name:
                self.device_mappings[device_name] = normalized_name
                logger.info(f"Normalized: {device_name} -> {normalized_name}")
    
    def _apply_normalization_to_topology(self, topology_data: Dict) -> Dict:
        """Apply naming normalization to topology data."""
        normalized_topology = topology_data.copy()
        
        # Normalize device names in devices section
        devices = normalized_topology.get('devices', {})
        normalized_devices = {}
        
        for device_name, device_info in devices.items():
            normalized_name = self.normalizer.normalize_device_name(device_name)
            normalized_devices[normalized_name] = device_info
            
            # Update device name in device info
            device_info['name'] = normalized_name
            
            # Normalize connected spines
            if 'connected_spines' in device_info:
                normalized_spines = []
                for spine in device_info['connected_spines']:
                    if isinstance(spine, dict):
                        # Handle new format with connection details
                        spine_name = spine.get('name', '')
                        normalized_spine_name = self.normalizer.normalize_device_name(spine_name)
                        spine['name'] = normalized_spine_name
                        normalized_spines.append(spine)
                        if normalized_spine_name != spine_name:
                            self.spine_mappings[spine_name] = normalized_spine_name
                    else:
                        # Handle old format with just spine names
                        normalized_spine = self.normalizer.normalize_device_name(spine)
                        normalized_spines.append(normalized_spine)
                        if normalized_spine != spine:
                            self.spine_mappings[spine] = normalized_spine
                device_info['connected_spines'] = normalized_spines
            
            # Normalize external connections
            if 'external_connections' in device_info:
                for conn in device_info['external_connections']:
                    if 'name' in conn:
                        conn['name'] = self.normalizer.normalize_device_name(conn['name'])
        
        normalized_topology['devices'] = normalized_devices
        
        # Normalize device lists
        for key in ['available_leaves', 'unavailable_leaves', 'superspine_devices', 'spine_devices']:
            if key in normalized_topology:
                normalized_list = []
                for device in normalized_topology[key]:
                    normalized_device = self.normalizer.normalize_device_name(device)
                    normalized_list.append(normalized_device)
                normalized_topology[key] = normalized_list
        
        return normalized_topology
    
    def _validate_and_fix_connectivity(self, topology_data: Dict):
        """Validate and fix connectivity issues."""
        logger.info("[CONNECTIVITY] Starting connectivity validation and fixes...")
        
        issues = self.normalizer.validate_device_connectivity(topology_data)
        self.issues_found = issues
        
        logger.info(f"[CONNECTIVITY] Found {len(issues['missing_spine_connections'])} devices with missing spine connections")
        logger.info(f"[CONNECTIVITY] Found {len(issues['unmatched_devices'])} unmatched devices")
        
        # Log detailed issues
        if issues['missing_spine_connections']:
            logger.warning("[CONNECTIVITY] Devices with missing spine connections:")
            for device in issues['missing_spine_connections']:
                logger.warning(f"  - {device}")
        
        if issues['unmatched_devices']:
            logger.warning("[CONNECTIVITY] Unmatched devices:")
            for device in issues['unmatched_devices']:
                logger.warning(f"  - {device}")
        
        # Apply automatic fixes
        fixes = self.normalizer.suggest_fixes(issues)
        self.fixes_applied = fixes
        
        # Apply spine mappings
        for mapping in fixes.get('spine_mappings', []):
            source, target = mapping.split(' -> ')
            normalized_source = self.normalizer.normalize_device_name(source)
            normalized_target = self.normalizer.normalize_device_name(target)
            
            # Update topology with suggested spine connection
            if normalized_source in topology_data.get('devices', {}):
                device_info = topology_data['devices'][normalized_source]
                if 'connected_spines' not in device_info:
                    device_info['connected_spines'] = []
                if normalized_target not in device_info['connected_spines']:
                    device_info['connected_spines'].append(normalized_target)
                    logger.info(f"[CONNECTIVITY] Applied spine mapping: {source} -> {target}")
        
        # Enhanced spine connection fixing based on bundle mappings
        self._fix_spine_connections_from_bundles(topology_data)
        
        # Log final connection summary
        self._log_connection_summary(topology_data)
    
    def _log_connection_summary(self, topology_data: Dict):
        """Log a summary of all connections in the topology."""
        logger.info("[CONNECTIVITY] Connection Summary:")
        
        devices = topology_data.get('devices', {})
        for device_name, device_info in devices.items():
            device_type = device_info.get('type', 'unknown')
            
            if device_type == 'leaf':
                connected_spines = device_info.get('connected_spines', [])
                logger.info(f"  {device_name} (leaf) -> spines: {connected_spines}")
            
            elif device_type == 'spine':
                connected_superspines = device_info.get('connected_superspines', [])
                connected_leaves = []
                for leaf_name, leaf_info in devices.items():
                    if leaf_info.get('type') == 'leaf':
                        leaf_spines = leaf_info.get('connected_spines', [])
                        if device_name in leaf_spines:
                            connected_leaves.append(leaf_name)
                
                logger.info(f"  {device_name} (spine) -> superspines: {[conn['name'] for conn in connected_superspines]}")
                logger.info(f"  {device_name} (spine) -> leaves: {connected_leaves}")
            
            elif device_type == 'superspine':
                connected_spines = device_info.get('connected_spines', [])
                logger.info(f"  {device_name} (superspine) -> spines: {[conn['name'] for conn in connected_spines]}")
    
    def _fix_spine_connections_from_bundles(self, topology_data: Dict):
        """Fix spine connections by analyzing bundle mappings using canonical keys."""
        logger.info("[BUNDLE_FIX] 🔧 Fixing spine connections from bundle mappings using canonical keys...")
        
        # Load bundle mappings
        bundle_file = self.topology_dir / "bundle_mapping_v2.yaml"
        if not bundle_file.exists():
            logger.warning("[BUNDLE_FIX] Bundle mapping file not found, skipping bundle-based spine connection fixes")
            return
        
        try:
            with open(bundle_file, 'r') as f:
                bundle_data = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"[BUNDLE_FIX] Failed to load bundle mappings: {e}")
            return
        
        # Extract bundle connections using canonical keys
        bundle_connections = {}
        bundles = bundle_data.get('bundles', {})
        logger.info(f"[BUNDLE_FIX] Processing {len(bundles)} bundle entries...")
        
        for bundle_name, bundle_info in bundles.items():
            if isinstance(bundle_info, dict) and 'device' in bundle_info and 'connections' in bundle_info:
                device_name = bundle_info['device']
                connections = bundle_info['connections']
                
                # Use canonical key for device lookup
                device_key = self.normalizer.canonical_key(device_name)
                if device_key not in bundle_connections:
                    bundle_connections[device_key] = []
                
                for conn in connections:
                    if isinstance(conn, dict) and 'remote_device' in conn:
                        bundle_connections[device_key].append(conn['remote_device'])
        
        logger.info(f"[BUNDLE_FIX] Found bundle connections for {len(bundle_connections)} devices (by canonical key)")
        
        # Fix spine connections based on bundle data using canonical keys
        devices = topology_data.get('devices', {})
        fixes_applied = 0
        
        for device_name, device_info in devices.items():
            if device_info.get('type') == 'leaf':
                # Use canonical key for device lookup
                device_key = self.normalizer.canonical_key(device_name)
                
                if device_key in bundle_connections:
                    all_bundle_spines = set()
                    for remote_device in bundle_connections[device_key]:
                        if 'SPINE' in remote_device:
                            normalized_spine = self.normalizer.normalize_device_name(remote_device)
                            all_bundle_spines.add(normalized_spine)
                            logger.info(f"[BUNDLE_FIX] Found spine connection for {device_name} (key {device_key}): {remote_device} -> {normalized_spine}")
                    
                    # Update connected_spines if different
                    current_spines = device_info.get('connected_spines', [])
                    # Handle both string and dictionary spine connections
                    current_spine_names = set()
                    for spine in current_spines:
                        if isinstance(spine, dict):
                            spine_name = spine.get('name', '')
                        else:
                            spine_name = str(spine)
                        if spine_name:
                            current_spine_names.add(spine_name)
                    
                    if all_bundle_spines != current_spine_names:
                        device_info['connected_spines'] = list(all_bundle_spines)
                        logger.info(f"[BUNDLE_FIX] Fixed spine connections for {device_name}: {list(all_bundle_spines)}")
                        fixes_applied += 1
                    else:
                        logger.debug(f"[BUNDLE_FIX] No spine connection changes needed for {device_name}")
                else:
                    logger.debug(f"[BUNDLE_FIX] No bundle connections found for {device_name} (key {device_key})")
        
        # Additional fix for spine naming inconsistencies
        # Handle cases like DNAAS-SPINE-NCP1-B08 -> DNAAS-SPINE-B08
        spine_name_fixes = {
            'DNAAS-SPINE-NCP1-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCPL-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCP-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCP1-D14': 'DNAAS-SPINE-D14',
            'DNAAS-SPINE-NCPL-D14': 'DNAAS-SPINE-D14',
            'DNAAS-SPINE-NCP-D14': 'DNAAS-SPINE-D14',
        }
        
        for device_name, device_info in devices.items():
            if device_info.get('type') == 'leaf':
                current_spines = device_info.get('connected_spines', [])
                updated_spines = []
                spine_fixes_applied = False
                
                for spine in current_spines:
                    if isinstance(spine, dict):
                        spine_name = spine.get('name', '')
                        if spine_name in spine_name_fixes:
                            corrected_name = spine_name_fixes[spine_name]
                            updated_spines.append({
                                'name': corrected_name,
                                'local_interface': spine.get('local_interface', ''),
                                'remote_interface': spine.get('remote_interface', '')
                            })
                            logger.info(f"[BUNDLE_FIX] Fixed spine name for {device_name}: {spine_name} -> {corrected_name}")
                            spine_fixes_applied = True
                        else:
                            updated_spines.append(spine)
                    else:
                        spine_name = str(spine)
                        if spine_name in spine_name_fixes:
                            corrected_name = spine_name_fixes[spine_name]
                            updated_spines.append(corrected_name)
                            logger.info(f"[BUNDLE_FIX] Fixed spine name for {device_name}: {spine_name} -> {corrected_name}")
                            spine_fixes_applied = True
                        else:
                            updated_spines.append(spine)
                
                if spine_fixes_applied:
                    device_info['connected_spines'] = updated_spines
                    fixes_applied += 1
        
        logger.info(f"[BUNDLE_FIX] Applied {fixes_applied} spine connection fixes from bundle mappings using canonical keys")
        
        # Update fixes_applied count
        if 'spine_mappings' not in self.fixes_applied:
            self.fixes_applied['spine_mappings'] = []
        self.fixes_applied['bundle_based_fixes'] = fixes_applied
        
        # Extract and add spine-to-superspine connections
        self._extract_spine_to_superspine_connections(topology_data, bundle_data)
    
    def _extract_spine_to_superspine_connections(self, topology_data: Dict, bundle_data: Dict):
        """Extract spine-to-superspine connections from bundle mappings."""
        logger.info("[SUPERSPINE] 🔧 Extracting spine-to-superspine connections from bundle mappings...")
        
        # Extract spine-to-superspine connections from bundle data (not bundle_connections)
        spine_to_superspine = {}
        superspine_to_spine = {}
        
        bundles = bundle_data.get('bundles', {})
        logger.info(f"[SUPERSPINE] Processing {len(bundles)} bundles for spine-superspine mapping...")
        
        for bundle_name, bundle_info in bundles.items():
            if isinstance(bundle_info, dict) and 'device' in bundle_info and 'connections' in bundle_info:
                device_name = bundle_info['device']
                connections = bundle_info['connections']
                
                # Check if this is a spine device
                if 'SPINE' in device_name:
                    spine_name = self.normalizer.normalize_device_name(device_name)
                    
                    for conn in connections:
                        if isinstance(conn, dict) and 'remote_device' in conn:
                            remote_device = conn['remote_device']
                            local_interface = conn.get('local_interface', '')
                            remote_interface = conn.get('remote_interface', '')
                            
                            # Check if remote device is a superspine
                            if 'SUPERSPINE' in remote_device or 'SuperSpine' in remote_device:
                                superspine_name = self.normalizer.normalize_device_name(remote_device)
                                
                                # Handle the case where the bundle connection uses a simplified name
                                # but the actual bundle device has NCC suffix
                                if 'D04' in superspine_name and 'NCC' not in superspine_name:
                                    # Try to find the correct NCC variant
                                    for bundle_name, bundle_info in bundles.items():
                                        if 'SuperSpine' in bundle_name and 'D04' in bundle_name and 'NCC' in bundle_name:
                                            actual_superspine = bundle_info.get('device', '')
                                            if actual_superspine:
                                                superspine_name = self.normalizer.normalize_device_name(actual_superspine)
                                                logger.info(f"[SUPERSPINE] Corrected superspine name: {remote_device} -> {superspine_name}")
                                                break
                                
                                if spine_name not in spine_to_superspine:
                                    spine_to_superspine[spine_name] = []
                                spine_to_superspine[spine_name].append({
                                    'name': superspine_name,
                                    'local_interface': local_interface,
                                    'remote_interface': remote_interface
                                })
                                
                                if superspine_name not in superspine_to_spine:
                                    superspine_to_spine[superspine_name] = []
                                superspine_to_spine[superspine_name].append({
                                    'name': spine_name,
                                    'local_interface': remote_interface,
                                    'remote_interface': local_interface
                                })
                                
                                logger.info(f"[SUPERSPINE] Found spine-to-superspine from bundle: {spine_name} {local_interface} -> {superspine_name} {remote_interface}")
        
        logger.info(f"[SUPERSPINE] Found {len(spine_to_superspine)} spine-to-superspine connections from bundles")
        logger.info(f"[SUPERSPINE] Found {len(superspine_to_spine)} superspine-to-spine connections from bundles")
        
        # Add spine-to-superspine connections to topology data
        devices = topology_data.get('devices', {})
        connections_added = 0
        
        # Add connected_superspines to spine devices
        for spine_name, superspine_conns in spine_to_superspine.items():
            if spine_name in devices:
                devices[spine_name]['connected_superspines'] = superspine_conns
                logger.info(f"[SUPERSPINE] Added superspine connections to {spine_name}: {[conn['name'] for conn in superspine_conns]}")
                connections_added += 1
        
        # Add connected_spines to superspine devices
        for superspine_name, spine_conns in superspine_to_spine.items():
            if superspine_name in devices:
                devices[superspine_name]['connected_spines'] = spine_conns
                logger.info(f"[SUPERSPINE] Added spine connections to {superspine_name}: {[conn['name'] for conn in spine_conns]}")
                connections_added += 1
        
        logger.info(f"[SUPERSPINE] Added {connections_added} spine-superspine connection mappings to topology")
        
        # Update fixes_applied count
        if 'spine_superspine_mappings' not in self.fixes_applied:
            self.fixes_applied['spine_superspine_mappings'] = []
        self.fixes_applied['spine_superspine_connections'] = connections_added
    
    def _generate_enhanced_summary(self, topology_data: Dict):
        """Generate enhanced summary with normalization info."""
        summary = {
            "timestamp": topology_data.get('timestamp', ''),
            "normalization_stats": {
                "total_devices": len(self.device_mappings),
                "normalized_devices": len([k for k, v in self.device_mappings.items() if k != v]),
                "spine_mappings": len(self.spine_mappings),
                "issues_found": len(self.issues_found.get('missing_spine_connections', [])),
                "fixes_applied": len(self.fixes_applied.get('spine_mappings', []))
            },
            "device_mappings": self.device_mappings,
            "spine_mappings": self.spine_mappings,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied
        }
        
        # Save enhanced summary
        summary_file = self.topology_dir / "enhanced_topology_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Enhanced topology summary generated")
    
    def get_device_variations(self, device_name: str) -> List[str]:
        """Get all known variations of a device name."""
        normalized = self.normalizer.normalize_device_name(device_name)
        return self.normalizer.get_all_variations(normalized)
    
    def find_similar_devices(self, device_name: str) -> List[str]:
        """Find devices with similar names."""
        return self.normalizer.find_similar_devices(device_name)
    
    def validate_specific_device(self, device_name: str, topology_data: Dict) -> Dict:
        """Validate connectivity for a specific device."""
        normalized_name = self.normalizer.normalize_device_name(device_name)
        device_info = topology_data.get('devices', {}).get(normalized_name, {})
        
        validation = {
            "device_name": device_name,
            "normalized_name": normalized_name,
            "has_spine_connections": len(device_info.get('connected_spines', [])) > 0,
            "connected_spines": device_info.get('connected_spines', []),
            "device_type": device_info.get('type', 'unknown'),
            "bundles_count": device_info.get('bundles', 0),
            "neighbors_count": device_info.get('neighbors', 0),
            "similar_devices": self.find_similar_devices(device_name),
            "variations": self.get_device_variations(device_name)
        }
        
        return validation
    
    def generate_normalization_report(self) -> str:
        """Generate a comprehensive normalization report."""
        report = []
        report.append("=" * 80)
        report.append("🔧 DEVICE NAME NORMALIZATION REPORT")
        report.append("=" * 80)
        
        # Summary statistics
        total_devices = len(self.device_mappings)
        normalized_devices = len([k for k, v in self.device_mappings.items() if k != v])
        
        report.append(f"📊 SUMMARY:")
        report.append(f"  Total devices processed: {total_devices}")
        report.append(f"  Devices normalized: {normalized_devices}")
        report.append(f"  Normalization rate: {(normalized_devices/total_devices*100):.1f}%" if total_devices > 0 else "  Normalization rate: 0%")
        report.append("")
        
        # Device mappings
        if self.device_mappings:
            report.append("📋 DEVICE MAPPINGS:")
            for original, normalized in sorted(self.device_mappings.items()):
                if original != normalized:
                    report.append(f"  • {original} -> {normalized}")
            report.append("")
        
        # Spine mappings
        if self.spine_mappings:
            report.append("🔄 SPINE MAPPINGS:")
            for original, normalized in sorted(self.spine_mappings.items()):
                report.append(f"  • {original} -> {normalized}")
            report.append("")
        
        # Issues found
        if self.issues_found:
            report.append("⚠️  ISSUES FOUND:")
            for issue_type, issues in self.issues_found.items():
                if issues:
                    report.append(f"  {issue_type.upper()}:")
                    for issue in issues:
                        report.append(f"    • {issue}")
                    report.append("")
        
        # Fixes applied
        if self.fixes_applied:
            report.append("🔧 FIXES APPLIED:")
            for fix_type, fixes in self.fixes_applied.items():
                if fixes:
                    report.append(f"  {fix_type.upper()}:")
                    if isinstance(fixes, list):
                        for fix in fixes:
                            report.append(f"    • {fix}")
                    elif isinstance(fixes, int):
                        report.append(f"    • {fixes} fixes applied")
                    else:
                        report.append(f"    • {fixes}")
                    report.append("")
        
        return "\n".join(report)
    
    def export_normalization_data(self) -> Dict:
        """Export all normalization data for external use."""
        return {
            "device_mappings": self.device_mappings,
            "spine_mappings": self.spine_mappings,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "normalizer_mappings": self.normalizer.export_mappings()
        }

# Global enhanced discovery instance
enhanced_discovery = EnhancedTopologyDiscovery() 