"""
Bridge Domain Discovery Components

Separated concerns architecture for bridge domain discovery system.

Components:
- BridgeDomainDetector: Detect and parse bridge domains from raw CLI data
- DeviceTypeClassifier: Classify device types (LEAF/SPINE/SUPERSPINE)
- LLDPAnalyzer: Load and analyze LLDP neighbor data
- InterfaceRoleAnalyzer: Determine interface roles using multiple data sources
- GlobalIdentifierExtractor: Extract global identifiers for consolidation
- ConsolidationEngine: Consolidate bridge domains by global identifier
- PathGenerator: Generate network topology paths
- DatabasePopulator: Populate database with discovered topology
- EnhancedDiscoveryOrchestrator: Orchestrate all components
"""

from .bridge_domain_detector import BridgeDomainDetector, BridgeDomainInstance, VLANConfig
from .device_type_classifier import DeviceTypeClassifier, DeviceClassification
from .lldp_analyzer import LLDPAnalyzer, NeighborInfo, ValidationResult, LLDPDataMissingError, InvalidTopologyError
from .interface_role_analyzer import InterfaceRoleAnalyzer, InterfaceInfo
from .global_identifier_extractor import GlobalIdentifierExtractor, GlobalIdentifierResult, ConsolidationScope
from .consolidation_engine import ConsolidationEngine, ConsolidatedBridgeDomain, ConsolidationInfo
from .path_generator import PathGenerator
from .database_populator import DatabasePopulator, SaveResult
from .discovery_orchestrator import EnhancedDiscoveryOrchestrator, run_refactored_enhanced_discovery

__all__ = [
    'BridgeDomainDetector',
    'DeviceTypeClassifier', 
    'LLDPAnalyzer',
    'InterfaceRoleAnalyzer',
    'GlobalIdentifierExtractor',
    'ConsolidationEngine',
    'PathGenerator',
    'DatabasePopulator',
    'EnhancedDiscoveryOrchestrator',
    'run_refactored_enhanced_discovery',
    # Data structures
    'BridgeDomainInstance',
    'DeviceClassification',
    'NeighborInfo',
    'InterfaceInfo',
    'GlobalIdentifierResult',
    'ConsolidatedBridgeDomain',
    'ConsolidationInfo',
    'SaveResult',
    'ValidationResult',
    'VLANConfig',
    'ConsolidationScope',
    # Exceptions
    'LLDPDataMissingError',
    'InvalidTopologyError'
]
