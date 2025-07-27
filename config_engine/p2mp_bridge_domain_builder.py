#!/usr/bin/env python3
"""
P2MP Bridge Domain Builder
Main class for building Point-to-Multipoint bridge domain configurations
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .bridge_domain_builder import BridgeDomainBuilder
from .p2mp_path_calculator import P2MPPathCalculator
from .p2mp_config_generator import P2MPConfigGenerator


class P2MPBridgeDomainBuilder:
    """Build P2MP bridge domain configurations"""
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize P2MP bridge domain builder
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = Path(topology_dir)
        self.logger = logging.getLogger('P2MPBridgeDomainBuilder')
        
        # Initialize base bridge domain builder
        self.base_builder = BridgeDomainBuilder(topology_dir)
        
        # Initialize P2MP components
        self.path_calculator = P2MPPathCalculator(self.base_builder.topology_data)
        self.config_generator = P2MPConfigGenerator(self.base_builder)
    
    def build_p2mp_bridge_domain_config(self, service_name: str, vlan_id: int,
                                      source_leaf: str, source_port: str,
                                      destinations: List[Dict]) -> Dict:
        """
        Build P2MP bridge domain configuration
        Automatically determines optimal paths:
        - 2-tier for destinations on same spine as source
        - 3-tier for destinations on different spines
        
        Args:
            service_name: Service identifier (e.g., 'g_visaev_v100')
            vlan_id: VLAN ID
            source_leaf: Source leaf device name
            source_port: Source port interface
            destinations: List of {leaf: str, port: str} dictionaries
            
        Returns:
            Configuration for all devices in the P2MP topology
        """
        self.logger.info(f"Building P2MP bridge domain config for {service_name} (VLAN {vlan_id})")
        self.logger.info(f"Source: {source_leaf}:{source_port}")
        self.logger.info(f"Destinations: {len(destinations)}")
        
        # Extract destination leaf names for path calculation
        dest_leaves = [dest['leaf'] for dest in destinations]
        
        # Calculate optimal paths (automatic strategy)
        path_calculation = self.path_calculator.calculate_p2mp_paths(source_leaf, dest_leaves)
        
        # Validate path calculation results
        if not path_calculation['destinations']:
            self.logger.error("No valid paths found for any destinations")
            return {}
        
        # Generate configuration
        configs = self.config_generator.generate_p2mp_config(
            service_name, vlan_id, source_leaf, source_port, destinations, path_calculation
        )
        
        # Add path calculation metadata to configs
        configs['_metadata'] = {
            'service_name': service_name,
            'vlan_id': vlan_id,
            'source_leaf': source_leaf,
            'destinations': destinations,
            'path_calculation': path_calculation
        }
        
        self.logger.info(f"Generated P2MP configuration for {len(configs)-1} devices")  # -1 for metadata
        return configs
    
    def get_available_leaves(self) -> List[str]:
        """Get list of available leaf devices"""
        return self.base_builder.get_available_leaves()
    
    def get_unavailable_leaves(self) -> Dict[str, Dict]:
        """Get list of unavailable leaf devices with reasons"""
        return self.base_builder.get_unavailable_leaves()
    
    def analyze_source_capabilities(self, source_leaf: str) -> Dict:
        """Analyze source leaf connectivity and capabilities"""
        return self.path_calculator.analyze_source_capabilities(source_leaf)
    
    def calculate_paths_for_destinations(self, source_leaf: str, destinations: List[str]) -> Dict:
        """Calculate paths for given destinations"""
        return self.path_calculator.calculate_p2mp_paths(source_leaf, destinations)
    
    def visualize_p2mp_paths(self, path_calculation: Dict) -> str:
        """
        Generate ASCII visualization of P2MP paths
        
        Args:
            path_calculation: Path calculation results
            
        Returns:
            ASCII string representation of the paths
        """
        if not path_calculation or 'destinations' not in path_calculation:
            return "No paths calculated"
        
        source_leaf = path_calculation.get('source_leaf', 'Unknown')
        destinations = path_calculation['destinations']
        spine_utilization = path_calculation.get('spine_utilization', {})
        metrics = path_calculation.get('optimization_metrics', {})
        
        # Group destinations by spine
        spine_groups = {}
        for dest_name, path_info in destinations.items():
            # Handle both 2-tier and 3-tier paths
            if 'spine' in path_info:
                # 2-tier path
                spine = path_info['spine']
            elif 'source_spine' in path_info:
                # 3-tier path - use source spine for grouping
                spine = path_info['source_spine']
            else:
                # Fallback
                spine = 'Unknown'
            
            if spine not in spine_groups:
                spine_groups[spine] = []
            spine_groups[spine].append(dest_name)
        
        # Build ASCII tree
        lines = []
        lines.append(f"🌐 P2MP Bridge Domain Paths")
        lines.append("═" * 50)
        lines.append(f"Source: {source_leaf}")
        
        # Add spine paths
        spine_names = list(spine_groups.keys())
        for i, (spine, dests) in enumerate(spine_groups.items()):
            if i == len(spine_groups) - 1:
                prefix = "└── "
            else:
                prefix = "├── "
            
            if len(dests) == 1:
                # Single destination
                dest = dests[0]
                lines.append(f"{prefix}{spine} ──→ {dest}")
            else:
                # Multiple destinations sharing spine
                lines.append(f"{prefix}{spine}")
                for j, dest in enumerate(dests):
                    if j == len(dests) - 1:
                        sub_prefix = "    └── "
                    else:
                        sub_prefix = "    ├── "
                    lines.append(f"{sub_prefix}──→ {dest}")
        
        # Add statistics
        lines.append("")
        lines.append("📊 Path Statistics:")
        lines.append(f"   • Total destinations: {len(destinations)}")
        lines.append(f"   • Spines used: {len(spine_groups)}")
        lines.append(f"   • Path efficiency: {metrics.get('path_efficiency', 0):.1%}")
        
        failed_dests = metrics.get('failed_destinations', [])
        if failed_dests:
            lines.append(f"   • Failed destinations: {len(failed_dests)}")
        
        return "\n".join(lines)
    
    def save_configuration(self, configs: Dict, output_file: str = None) -> str:
        """
        Save P2MP bridge domain configuration to YAML file
        
        Args:
            configs: Configuration dictionary
            output_file: Output file name (optional)
            
        Returns:
            Path to saved file
        """
        if not output_file:
            metadata = configs.get('_metadata', {})
            service_name = metadata.get('service_name', 'p2mp_bridge_domain')
            output_file = f"{service_name}_config.yaml"
        
        # Remove metadata before saving
        configs_to_save = {k: v for k, v in configs.items() if k != '_metadata'}
        
        with open(output_file, 'w') as f:
            yaml.dump(configs_to_save, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Configuration saved to: {output_file}")
        return output_file
    
    def get_configuration_summary(self, configs: Dict) -> str:
        """
        Generate configuration summary for display
        
        Args:
            configs: Configuration dictionary
            
        Returns:
            Summary string
        """
        metadata = configs.get('_metadata', {})
        path_calculation = metadata.get('path_calculation', {})
        
        summary_lines = []
        summary_lines.append("📋 P2MP Configuration Summary")
        summary_lines.append("─" * 40)
        
        # Basic info
        summary_lines.append(f"Service Name: {metadata.get('service_name', 'Unknown')}")
        summary_lines.append(f"VLAN ID: {metadata.get('vlan_id', 'Unknown')}")
        summary_lines.append(f"Source: {metadata.get('source_leaf', 'Unknown')}")
        summary_lines.append(f"Destinations: {len(metadata.get('destinations', []))}")
        
        # Path visualization
        if path_calculation:
            summary_lines.append("")
            summary_lines.append("🌐 Bridge Domain Span:")
            source_leaf = path_calculation.get('source_leaf', 'Unknown')
            summary_lines.append(f"Source: {source_leaf}")
            
            destinations = path_calculation.get('destinations', {})
            spine_groups = {}
            for dest_name, path_info in destinations.items():
                # Handle both 2-tier and 3-tier paths
                if 'spine' in path_info:
                    # 2-tier path
                    spine = path_info['spine']
                elif 'source_spine' in path_info:
                    # 3-tier path - use source spine for grouping
                    spine = path_info['source_spine']
                else:
                    # Fallback
                    spine = 'Unknown'
                
                if spine not in spine_groups:
                    spine_groups[spine] = []
                spine_groups[spine].append(dest_name)
            
            spine_names = list(spine_groups.keys())
            for i, (spine, dests) in enumerate(spine_groups.items()):
                if i == len(spine_groups) - 1:
                    prefix = "└── "
                else:
                    prefix = "├── "
                
                if len(dests) == 1:
                    dest = dests[0]
                    summary_lines.append(f"{prefix}{spine} ──→ {dest}")
                else:
                    summary_lines.append(f"{prefix}{spine}")
                    for j, dest in enumerate(dests):
                        if j == len(dests) - 1:
                            sub_prefix = "    └── "
                        else:
                            sub_prefix = "    ├── "
                        summary_lines.append(f"{sub_prefix}──→ {dest}")
        
        # Statistics
        metrics = path_calculation.get('optimization_metrics', {})
        summary_lines.append("")
        summary_lines.append("📊 Statistics:")
        summary_lines.append(f"• Total spines used: {metrics.get('total_spines_used', 0)}")
        summary_lines.append(f"• Path efficiency: {metrics.get('path_efficiency', 0):.1%}")
        
        # Device count
        device_count = len([k for k in configs.keys() if k != '_metadata'])
        summary_lines.append(f"• Devices configured: {device_count}")
        
        return "\n".join(summary_lines) 