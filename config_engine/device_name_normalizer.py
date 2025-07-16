#!/usr/bin/env python3
"""
Device Name Normalizer - Future-proof solution for naming inconsistencies
Handles various naming patterns, suffixes, prefixes, and variations in network device names.
"""

import re
import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Device type enumeration."""
    LEAF = "leaf"
    SPINE = "spine"
    SUPERSPINE = "superspine"
    UNKNOWN = "unknown"

@dataclass
class NamePattern:
    """Represents a naming pattern with its components."""
    pattern: str
    device_type: DeviceType
    base_name: str
    suffix: Optional[str] = None
    prefix: Optional[str] = None
    location: Optional[str] = None
    rack: Optional[str] = None
    position: Optional[str] = None
    variant: Optional[str] = None

class DeviceNameNormalizer:
    """
    Comprehensive device name normalization system.
    
    Handles various naming inconsistencies:
    - Different separators (hyphens, underscores, spaces)
    - Suffixes (NCPL, NCP1, etc.)
    - Prefixes and location codes
    - Rack and position variations
    - Case sensitivity
    - Special characters
    - Parenthesis suffixes with spaces, hyphens, or no separators
    """
    
    def canonical_key(self, device_name: str) -> str:
        """Compute a canonical key for a device name: strip non-alphanumerics, normalize suffixes, uppercase."""
        if not device_name:
            return ''
        # Remove all non-alphanumerics
        key = re.sub(r'[^A-Za-z0-9]', '', device_name.upper())
        # Normalize known suffixes (e.g., NCPL, NCP, NCP1, etc. to NCP1)
        for suffix, canonical in self.suffix_mappings.items():
            if key.endswith(suffix):
                key = key[: -len(suffix)] + canonical
        return key

    def __init__(self):
        """Initialize the device name normalizer."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize caches
        self._normalization_cache = {}
        self.name_mappings = {}
        self.reverse_mappings = {}
        self.canonical_to_variants = defaultdict(set)
        
        # Define normalization patterns
        self.normalization_patterns = [
            # Spine patterns
            (re.compile(r'DNAAS-SPINE-NCP1-(\w+)'), r'DNAAS-SPINE-\1'),
            (re.compile(r'DNAAS-SPINE-NCPL-(\w+)'), r'DNAAS-SPINE-\1'),
            (re.compile(r'DNAAS-SPINE-NCP-(\w+)'), r'DNAAS-SPINE-\1'),
            # Superspine patterns
            (re.compile(r'DNAAS-SUPERSPINE-(\w+)-(\w+)'), r'DNAAS-SUPERSPINE-\1-\2'),
            # Leaf patterns
            (re.compile(r'DNAAS-LEAF-(\w+)'), r'DNAAS-LEAF-\1'),
        ]
        
        # Define specific name fixes
        self.name_fixes = {
            'DNAAS-SPINE-NCP1-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCPL-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCP-B08': 'DNAAS-SPINE-B08',
            'DNAAS-SPINE-NCP1-D14': 'DNAAS-SPINE-D14',
            'DNAAS-SPINE-NCPL-D14': 'DNAAS-SPINE-D14',
            'DNAAS-SPINE-NCP-D14': 'DNAAS-SPINE-D14',
        }
        
        # Enhanced naming patterns with better parenthesis handling
        self.patterns = [
            # Standard patterns
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)$",  # DNAAS-LEAF-B06-1
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-LEAF-B06-2
            
            # Parenthesis suffix patterns (various formats)
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)\s*\(([A-Z0-9]+)\)$",  # DNAAS-LEAF-B06-2 (NCPL)
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)\s*\(([A-Z0-9]+)\)$",  # DNAAS-LEAF-B06-2 (NCPL)
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)\(([A-Z0-9]+)\)$",  # DNAAS-LEAF-B06-2(NCPL)
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)\(([A-Z0-9]+)\)$",  # DNAAS-LEAF-B06-2(NCPL)
            
            # Hyphenated suffix patterns
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-LEAF-B06-2-NCP1
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-LEAF-B06-2-NCP1
            
            # Spine patterns
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)$",  # DNAAS-SPINE-B08
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-SPINE-NCP1-B08
            r"^([A-Z]+)_([A-Z]+)_([A-Z0-9]+)$",  # DNAAS_SPINE_B08
            
            # Superspine patterns
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-SuperSpine-D04-NCC0
            r"^([A-Z]+)-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)-([A-Z0-9]+)$",  # DNAAS-SuperSpine-D04-NCC1
            
            # Generic patterns
            r"^([A-Z0-9]+)-([A-Z0-9]+)-([A-Z0-9]+)$",
            r"^([A-Z0-9]+)_([A-Z0-9]+)_([A-Z0-9]+)$",
            r"^([A-Z0-9]+)-([A-Z0-9]+)-([A-Z0-9]+)-([A-Z0-9]+)$",
        ]
        
        # Enhanced suffix mappings with more variations
        self.suffix_mappings = {
            # NCP variations
            "NCPL": "NCP1",
            "NCP1": "NCP1", 
            "NCP": "NCP1",
            "NCP0": "NCP1",
            "NCP2": "NCP1",
            
            # NCC variations
            "NCC0": "NCC0",
            "NCC1": "NCC1",
            "NCC": "NCC0",
            
            # Other common suffixes
            "L": "NCP1",  # Sometimes just L is used
            "1": "NCP1",
            "0": "NCC0",
        }
        
        # Common prefixes to normalize
        self.prefix_mappings = {
            "DNAAS": "DNAAS",
            "DNA": "DNAAS",
        }
        
        # Device type indicators
        self.device_type_indicators = {
            "LEAF": DeviceType.LEAF,
            "SPINE": DeviceType.SPINE,
            "SUPERSPINE": DeviceType.SUPERSPINE,
            "SUPER": DeviceType.SUPERSPINE,
        }
        
        # Location codes
        self.location_codes = {
            "A": "A",
            "B": "B", 
            "C": "C",
            "D": "D",
            "E": "E",
            "F": "F",
        }
    
    def normalize_device_name(self, device_name: str) -> str:
        """
        Normalize device name to canonical form.
        
        Args:
            device_name: Original device name
            
        Returns:
            Normalized device name
        """
        if not device_name:
            return device_name
        
        # Check if we have a cached result
        if device_name in self._normalization_cache:
            self.logger.debug(f"[NORMALIZE] Cached result: {device_name} -> {self._normalization_cache[device_name]}")
            return self._normalization_cache[device_name]
        
        original_name = device_name
        normalized = device_name
        
        # Step 1: Basic cleaning
        normalized = normalized.upper()
        normalized = normalized.replace('_', '-')
        normalized = normalized.replace(' ', '-')
        
        # Step 2: Apply regex patterns
        for pattern, replacement in self.normalization_patterns:
            if pattern.search(normalized):
                old_normalized = normalized
                normalized = pattern.sub(replacement, normalized)
                self.logger.debug(f"[NORMALIZE] Applied pattern {pattern.pattern}: {old_normalized} -> {normalized}")
        
        # Step 3: Apply specific fixes
        for old_name, new_name in self.name_fixes.items():
            if normalized == old_name:
                old_normalized = normalized
                normalized = new_name
                self.logger.debug(f"[NORMALIZE] Applied name fix: {old_normalized} -> {normalized}")
                break
        
        # Step 4: Generate canonical key
        canonical_key = self.canonical_key(normalized)
        
        # Cache the result
        self._normalization_cache[original_name] = normalized
        
        # Log the transformation
        if original_name != normalized:
            self.logger.info(f"[NORMALIZE] Device name normalized: {original_name} -> {normalized} (canonical: {canonical_key})")
        else:
            self.logger.debug(f"[NORMALIZE] Device name unchanged: {original_name} (canonical: {canonical_key})")
        
        return normalized
    
    def _clean_device_name(self, device_name: str) -> str:
        """Clean and standardize device name."""
        # Remove extra whitespace
        cleaned = device_name.strip()
        
        # Normalize separators
        cleaned = re.sub(r'[_\s]+', '-', cleaned)
        
        # Remove special characters except hyphens and parentheses
        cleaned = re.sub(r'[^A-Za-z0-9\-\(\)]', '', cleaned)
        
        # Normalize case
        cleaned = cleaned.upper()
        
        # Special handling for parenthesis suffixes - convert to hyphenated format
        parenthesis_pattern = r'^([A-Z0-9\-]+)\s*\(([A-Z0-9]+)\)$'
        match = re.match(parenthesis_pattern, cleaned)
        if match:
            base_name = match.group(1)
            suffix = match.group(2)
            normalized_suffix = self.suffix_mappings.get(suffix, suffix)
            cleaned = f"{base_name}-{normalized_suffix}"
        
        # Unify hyphenated suffixes for B06-2 and similar
        # e.g. DNAAS-LEAF-B06-2-NCPL, DNAAS-LEAF-B06-2-NCP, DNAAS-LEAF-B06-2-NCP1
        b06_suffix_pattern = r'^(DNAAS-LEAF-B06-2)-(NCPL|NCP1|NCP|NCP0|NCP2)$'
        match = re.match(b06_suffix_pattern, cleaned)
        if match:
            cleaned = f"DNAAS-LEAF-B06-2-NCP1"
        
        # Remove any accidental double hyphens
        cleaned = re.sub(r'-+', '-', cleaned)
        
        return cleaned
    
    def _parse_device_name(self, device_name: str) -> Optional[NamePattern]:
        """Parse device name into components."""
        for pattern in self.patterns:
            match = re.match(pattern, device_name)
            if match:
                groups = match.groups()
                return self._build_name_pattern(groups, device_name)
        
        return None
    
    def _build_name_pattern(self, groups: Tuple[str, ...], original: str) -> NamePattern:
        """Build a NamePattern from regex groups."""
        if len(groups) >= 3:
            prefix = groups[0]
            device_type_str = groups[1]
            location = groups[2]
            
            # Determine device type
            device_type = self.device_type_indicators.get(device_type_str, DeviceType.UNKNOWN)
            
            # Extract base name and suffix
            base_name = None
            suffix = None
            variant = None
            
            if len(groups) >= 4:
                base_name = groups[3]
                
                if len(groups) >= 5:
                    # Check if it's a suffix or variant
                    if groups[4] in self.suffix_mappings:
                        suffix = groups[4]
                    else:
                        variant = groups[4]
                
                if len(groups) >= 6:
                    # Handle parentheses suffixes like (NCPL)
                    if groups[5]:
                        suffix = groups[5]
            
            return NamePattern(
                pattern=original,
                device_type=device_type,
                base_name=base_name or "",
                suffix=suffix,
                prefix=prefix,
                location=location,
                variant=variant
            )
        
        return None
    
    def _build_normalized_name(self, parsed: NamePattern) -> str:
        """Build normalized name from parsed components."""
        parts = []
        
        # Add prefix
        if parsed.prefix:
            parts.append(parsed.prefix)
        
        # Add device type
        parts.append(parsed.device_type.value.upper())
        
        # Add location
        if parsed.location:
            parts.append(parsed.location)
        
        # Add base name
        if parsed.base_name:
            parts.append(parsed.base_name)
        
        # Add variant
        if parsed.variant:
            parts.append(parsed.variant)
        
        # Add suffix (normalized)
        if parsed.suffix:
            normalized_suffix = self.suffix_mappings.get(parsed.suffix, parsed.suffix)
            parts.append(normalized_suffix)
        
        return "-".join(parts)
    
    def get_original_name(self, normalized_name: str) -> Optional[str]:
        """Get the original name from a normalized name."""
        return self.reverse_mappings.get(normalized_name)
    
    def get_all_variants_by_key(self, device_name: str) -> list:
        """Return all known variants for a device name via its canonical key."""
        key = self.canonical_key(device_name)
        return list(self.canonical_to_variants.get(key, []))
    
    def create_device_mapping(self, original_names: List[str]) -> Dict[str, str]:
        """
        Create a comprehensive device mapping from a list of original names.
        
        Args:
            original_names: List of device names to normalize
            
        Returns:
            Mapping from original names to normalized names
        """
        mapping = {}
        for name in original_names:
            normalized = self.normalize_device_name(name)
            mapping[name] = normalized
        return mapping
    
    def find_similar_devices(self, device_name: str, threshold: float = 0.8) -> List[str]:
        """
        Find devices with similar names using fuzzy matching.
        
        Args:
            device_name: The device name to find similar devices for
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar device names
        """
        from difflib import SequenceMatcher
        
        normalized_target = self.normalize_device_name(device_name)
        similar_devices = []
        
        for original_name in self.name_mappings.keys():
            normalized_other = self.normalize_device_name(original_name)
            similarity = SequenceMatcher(None, normalized_target, normalized_other).ratio()
            
            if similarity >= threshold and original_name != device_name:
                similar_devices.append(original_name)
        
        return similar_devices
    
    def validate_device_connectivity(self, topology_data: Dict) -> Dict[str, List[str]]:
        """
        Validate device connectivity and identify naming issues.
        
        Args:
            topology_data: The topology data to validate
            
        Returns:
            Dictionary of issues found
        """
        issues = {
            "missing_spine_connections": [],
            "unmatched_devices": [],
            "naming_inconsistencies": []
        }
        
        devices = topology_data.get('devices', {})
        
        for device_name, device_info in devices.items():
            if device_info.get('type') == 'leaf':
                connected_spines = device_info.get('connected_spines', [])
                
                if not connected_spines:
                    issues["missing_spine_connections"].append(device_name)
                
                # Check for naming inconsistencies in spine connections
                for spine in connected_spines:
                    spine_name = spine
                    if isinstance(spine, dict):
                        spine_name = spine.get('name', '')
                    
                    if spine_name and spine_name not in devices:
                        issues["unmatched_devices"].append(f"{device_name} -> {spine_name}")
        
        return issues
    
    def suggest_fixes(self, issues: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Suggest fixes for identified issues.
        
        Args:
            issues: Issues found by validate_device_connectivity
            
        Returns:
            Dictionary of suggested fixes
        """
        fixes = {
            "spine_mappings": [],
            "device_mappings": [],
            "collection_fixes": []
        }
        
        for device in issues.get("missing_spine_connections", []):
            # Find potential spine connections
            similar_devices = self.find_similar_devices(device)
            for similar in similar_devices:
                fixes["spine_mappings"].append(f"{device} -> {similar}")
        
        for unmatched in issues.get("unmatched_devices", []):
            source, target = unmatched.split(" -> ")
            normalized_target = self.normalize_device_name(target)
            fixes["device_mappings"].append(f"{target} -> {normalized_target}")
        
        return fixes
    
    def export_mappings(self) -> Dict[str, Dict[str, str]]:
        """Export all mappings for persistence."""
        return {
            "name_mappings": self.name_mappings,
            "reverse_mappings": self.reverse_mappings,
            "suffix_mappings": self.suffix_mappings,
            "prefix_mappings": self.prefix_mappings
        }
    
    def import_mappings(self, mappings: Dict[str, Dict[str, str]]):
        """Import mappings from persistence."""
        self.name_mappings.update(mappings.get("name_mappings", {}))
        self.reverse_mappings.update(mappings.get("reverse_mappings", {}))
        self.suffix_mappings.update(mappings.get("suffix_mappings", {}))
        self.prefix_mappings.update(mappings.get("prefix_mappings", {}))

# Global normalizer instance
normalizer = DeviceNameNormalizer() 