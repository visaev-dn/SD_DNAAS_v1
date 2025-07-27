#!/usr/bin/env python3
"""
Service Name Analyzer

This module provides pattern recognition and analysis for bridge domain service names.
It extracts usernames and VLAN IDs from various naming conventions with confidence scoring.
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ServiceNameAnalyzer:
    """
    Service Name Analyzer
    
    Analyzes bridge domain service names to extract usernames and VLAN IDs
    using pattern recognition with confidence scoring.
    """
    
    def __init__(self):
        # Define patterns in order of confidence (highest to lowest)
        self.patterns = [
            # Automated patterns (highest confidence)
            {
                'pattern': r'^g_(\w+)_v(\d+)$',
                'method': 'automated_pattern',
                'confidence': 100,
                'description': 'Automated format: g_username_vvlan',
                'scope': 'global'
            },
            # Complex descriptive patterns (high confidence)
            {
                'pattern': r'^g_(\w+)_v(\d+)_(.+)$',
                'method': 'complex_descriptive_pattern',
                'confidence': 95,
                'description': 'Complex format: g_username_vvlan_description',
                'scope': 'global'
            },
            {
                'pattern': r'^g_(\w+)_v(\d+)-(.+)$',
                'method': 'complex_hyphen_pattern',
                'confidence': 95,
                'description': 'Complex format: g_username_vvlan-description',
                'scope': 'global'
            },
            # L-prefix patterns (high confidence) - Local scope
            # More specific patterns first
            {
                'pattern': r'^l_([a-zA-Z0-9_-]+?)_v(\d+)_(.+)$',
                'method': 'l_prefix_vlan_pattern',
                'confidence': 90,
                'description': 'L-prefix with VLAN: l_username_vvlan_description (Local scope)',
                'scope': 'local'
            },
            {
                'pattern': r'^l_([a-zA-Z0-9_-]+?)_v(\d+)$',
                'method': 'l_prefix_simple_vlan_pattern',
                'confidence': 90,
                'description': 'L-prefix simple VLAN: l_username_vvlan (Local scope)',
                'scope': 'local'
            },
            {
                'pattern': r'^l_([a-zA-Z0-9_-]+?)_(.+)$',
                'method': 'l_prefix_pattern',
                'confidence': 90,
                'description': 'L-prefix format: l_username_description (Local scope)',
                'scope': 'local'
            },
            # Manual patterns (high confidence)
            {
                'pattern': r'^M_(\w+)_(\d+)$',
                'method': 'manual_pattern',
                'confidence': 95,
                'description': 'Manual format: M_username_vlan',
                'scope': 'manual'
            },
            {
                'pattern': r'^(\w+)_(\d+)$',
                'method': 'simple_pattern',
                'confidence': 85,
                'description': 'Simple format: username_vlan',
                'scope': 'unknown'
            },
            # Descriptive patterns (medium confidence)
            {
                'pattern': r'^user_(\w+)_vlan_(\d+)$',
                'method': 'descriptive_pattern',
                'confidence': 80,
                'description': 'Descriptive format: user_username_vlan_vlan',
                'scope': 'unknown'
            },
            {
                'pattern': r'^(\w+)-(\d+)$',
                'method': 'hyphen_pattern',
                'confidence': 75,
                'description': 'Hyphen format: username-vlan',
                'scope': 'unknown'
            },
            # Complex patterns (lower confidence)
            {
                'pattern': r'^(\w+)(\d+)$',
                'method': 'concatenated_pattern',
                'confidence': 60,
                'description': 'Concatenated format: usernamevlan',
                'scope': 'unknown'
            }
        ]
    
    def extract_service_info(self, bridge_domain_name: str) -> Dict:
        """
        Extract username and VLAN ID from bridge domain name.
        
        Args:
            bridge_domain_name: The bridge domain name to analyze
            
        Returns:
            Dict containing extracted information and confidence score
        """
        if not bridge_domain_name:
            return {
                'username': None,
                'vlan_id': None,
                'confidence': 0,
                'method': 'empty_name',
                'scope': 'unknown',
                'description': 'Empty bridge domain name'
            }
        
        # Try each pattern in order of confidence
        for pattern_info in self.patterns:
            match = re.match(pattern_info['pattern'], bridge_domain_name)
            if match:
                # Handle different pattern types
                if pattern_info['method'] in ['complex_descriptive_pattern', 'complex_hyphen_pattern']:
                    # g_username_vvlan_description format
                    username = match.group(1)
                    vlan_id = int(match.group(2))
                    description = match.group(3)
                    scope = pattern_info.get('scope', 'global')
                elif pattern_info['method'] in ['l_prefix_pattern']:
                    # l_username_description format - no VLAN ID
                    username = match.group(1)
                    description = match.group(2)
                    vlan_id = None
                    scope = pattern_info.get('scope', 'local')
                elif pattern_info['method'] in ['l_prefix_vlan_pattern', 'l_prefix_simple_vlan_pattern']:
                    # l_username_vvlan_description or l_username_vvlan format
                    username = match.group(1)
                    vlan_id = int(match.group(2))
                    description = match.group(3) if len(match.groups()) > 2 else None
                    scope = pattern_info.get('scope', 'local')
                else:
                    # Standard patterns with username and VLAN ID
                    username = match.group(1)
                    vlan_id = int(match.group(2))
                    scope = pattern_info.get('scope', 'unknown')
                
                # Validate extracted data
                validation_score = self._validate_extracted_data(username, vlan_id, scope)
                final_confidence = min(pattern_info['confidence'], validation_score)
                
                return {
                    'username': username,
                    'vlan_id': vlan_id,
                    'confidence': final_confidence,
                    'method': pattern_info['method'],
                    'description': pattern_info['description'],
                    'scope': scope
                }
        
        # No pattern matched
        return {
            'username': None,
            'vlan_id': None,
            'confidence': 0,
            'method': 'unknown_format',
            'description': f'Unknown format: {bridge_domain_name}',
            'scope': 'unknown'
        }
    
    def _validate_extracted_data(self, username: str, vlan_id: Optional[int], scope: str) -> int:
        """
        Validate extracted username and VLAN ID to adjust confidence score.
        
        Args:
            username: Extracted username
            vlan_id: Extracted VLAN ID (can be None for L-prefix patterns)
            scope: Scope of the bridge domain ('global', 'local', 'manual', 'unknown')
            
        Returns:
            Validation score (0-100)
        """
        score = 100
        
        # Validate username
        if not username or len(username) < 2:
            score -= 20
        elif len(username) > 20:
            score -= 10
        elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
            score -= 15
        
        # Validate VLAN ID (if present)
        if vlan_id is not None:
            if vlan_id < 1 or vlan_id > 4094:
                score -= 30
            elif vlan_id < 100:
                score -= 10  # Lower confidence for very low VLAN IDs
            elif vlan_id > 3000:
                score -= 5   # Slightly lower confidence for very high VLAN IDs
        else:
            # L-prefix patterns don't have VLAN IDs, which is expected for local scope
            if scope == 'local':
                score -= 0  # No penalty for local scope without VLAN ID
            else:
                score -= 5  # Small penalty for missing VLAN ID in other scopes
        
        # Validate scope
        if scope == 'unknown':
            score -= 10  # Penalty for unknown scope
        
        return max(0, score)
    
    def calculate_confidence(self, match_result: Dict) -> int:
        """
        Calculate confidence score for a pattern match.
        
        Args:
            match_result: Result from extract_service_info
            
        Returns:
            Confidence score (0-100)
        """
        return match_result.get('confidence', 0)
    
    def get_scope_description(self, scope: str) -> str:
        """
        Get human-readable description of the scope.
        
        Args:
            scope: Scope string ('global', 'local', 'manual', 'unknown')
            
        Returns:
            Human-readable description
        """
        scope_descriptions = {
            'global': 'Globally significant VLAN ID, can be configured everywhere',
            'local': 'Local scope - configured locally on a leaf and bridge local AC interfaces',
            'manual': 'Manually configured bridge domain',
            'unknown': 'Unknown scope - unable to determine'
        }
        return scope_descriptions.get(scope, 'Unknown scope')
    
    def get_pattern_statistics(self, bridge_domain_names: list) -> Dict:
        """
        Get statistics about pattern recognition for a list of bridge domain names.
        
        Args:
            bridge_domain_names: List of bridge domain names to analyze
            
        Returns:
            Statistics about pattern recognition
        """
        stats = {
            'total_names': len(bridge_domain_names),
            'pattern_matches': {},
            'scope_distribution': {
                'global': 0,
                'local': 0,
                'manual': 0,
                'unknown': 0
            },
            'confidence_distribution': {
                'high': 0,    # 80-100%
                'medium': 0,  # 50-79%
                'low': 0,     # 1-49%
                'none': 0     # 0%
            },
            'unmatched_formats': []
        }
        
        for name in bridge_domain_names:
            result = self.extract_service_info(name)
            method = result.get('method', 'unknown')
            confidence = result.get('confidence', 0)
            scope = result.get('scope', 'unknown')
            
            # Count pattern matches
            if method not in stats['pattern_matches']:
                stats['pattern_matches'][method] = 0
            stats['pattern_matches'][method] += 1
            
            # Count scope distribution
            if scope in stats['scope_distribution']:
                stats['scope_distribution'][scope] += 1
            
            # Count confidence distribution
            if confidence >= 80:
                stats['confidence_distribution']['high'] += 1
            elif confidence >= 50:
                stats['confidence_distribution']['medium'] += 1
            elif confidence > 0:
                stats['confidence_distribution']['low'] += 1
            else:
                stats['confidence_distribution']['none'] += 1
                stats['unmatched_formats'].append(name)
        
        return stats
    
    def suggest_improvements(self, bridge_domain_names: list) -> Dict:
        """
        Suggest improvements for bridge domain naming conventions.
        
        Args:
            bridge_domain_names: List of bridge domain names to analyze
            
        Returns:
            Suggestions for improving naming conventions
        """
        stats = self.get_pattern_statistics(bridge_domain_names)
        suggestions = {
            'high_confidence_percentage': 0,
            'recommended_pattern': 'g_username_vvlan',
            'issues_found': [],
            'recommendations': [],
            'scope_analysis': {}
        }
        
        total = stats['total_names']
        if total > 0:
            high_confidence = stats['confidence_distribution']['high']
            suggestions['high_confidence_percentage'] = (high_confidence / total) * 100
        
        # Analyze scope distribution
        suggestions['scope_analysis'] = {
            'global_scope_percentage': (stats['scope_distribution']['global'] / total) * 100 if total > 0 else 0,
            'local_scope_percentage': (stats['scope_distribution']['local'] / total) * 100 if total > 0 else 0,
            'manual_scope_percentage': (stats['scope_distribution']['manual'] / total) * 100 if total > 0 else 0,
            'unknown_scope_percentage': (stats['scope_distribution']['unknown'] / total) * 100 if total > 0 else 0
        }
        
        # Identify issues
        if stats['confidence_distribution']['none'] > 0:
            suggestions['issues_found'].append(f"{stats['confidence_distribution']['none']} bridge domains with unrecognized formats")
        
        if stats['confidence_distribution']['low'] > 0:
            suggestions['issues_found'].append(f"{stats['confidence_distribution']['low']} bridge domains with low confidence patterns")
        
        if stats['scope_distribution']['unknown'] > 0:
            suggestions['issues_found'].append(f"{stats['scope_distribution']['unknown']} bridge domains with unknown scope")
        
        # Provide recommendations
        if suggestions['high_confidence_percentage'] < 80:
            suggestions['recommendations'].append("Consider standardizing bridge domain naming to 'g_username_vvlan' format for global scope")
        
        if stats['scope_distribution']['local'] > 0:
            suggestions['recommendations'].append(f"Found {stats['scope_distribution']['local']} local scope bridge domains - ensure proper local configuration")
        
        if stats['unmatched_formats']:
            suggestions['recommendations'].append(f"Review {len(stats['unmatched_formats'])} unrecognized formats for standardization")
        
        return suggestions

if __name__ == "__main__":
    # Test the analyzer
    analyzer = ServiceNameAnalyzer()
    
    test_names = [
        "g_visaev_v253",      # Automated format (global)
        "l_gshafir_ISIS_R51_to_IXIA02",  # L-prefix format (local)
        "l_cchiriac_v1285_sysp65-kmv94_mxvmx5",  # L-prefix with VLAN (local)
        "M_kazakov_1360",     # Manual format
        "visaev_253",         # Simple format
        "user_visaev_vlan_253", # Descriptive format
        "visaev-253",         # Hyphen format
        "visaev253",          # Concatenated format
        "unknown_service_123", # Unknown format
        "",                   # Empty
    ]
    
    print("Service Name Analyzer Test")
    print("=" * 50)
    
    for name in test_names:
        result = analyzer.extract_service_info(name)
        print(f"Name: {name}")
        print(f"  Username: {result['username']}")
        print(f"  VLAN ID: {result['vlan_id']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Method: {result['method']}")
        print(f"  Scope: {result['scope']} - {analyzer.get_scope_description(result['scope'])}")
        print()
    
    # Test statistics
    stats = analyzer.get_pattern_statistics(test_names)
    print("Pattern Statistics:")
    print(f"  Total names: {stats['total_names']}")
    print(f"  Pattern matches: {stats['pattern_matches']}")
    print(f"  Scope distribution: {stats['scope_distribution']}")
    print(f"  Confidence distribution: {stats['confidence_distribution']}")
    print(f"  Unmatched formats: {stats['unmatched_formats']}")
    
    # Test suggestions
    suggestions = analyzer.suggest_improvements(test_names)
    print("\nSuggestions:")
    print(f"  High confidence percentage: {suggestions['high_confidence_percentage']:.1f}%")
    print(f"  Scope analysis: {suggestions['scope_analysis']}")
    print(f"  Issues found: {suggestions['issues_found']}")
    print(f"  Recommendations: {suggestions['recommendations']}") 