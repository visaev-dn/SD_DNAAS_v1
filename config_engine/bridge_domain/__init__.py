#!/usr/bin/env python3
"""
Bridge Domain Package
Consolidated bridge domain builders for the Lab Automation Framework
"""

from .base_builder import (
    BaseBridgeDomainBuilder,
    BridgeDomainConfig,
    BridgeDomainResult
)

from .p2p_builder import P2PBridgeDomainBuilder
from .p2mp_builder import P2MPBridgeDomainBuilder
from .builder_factory import (
    BuilderFactory,
    TopologyType,
    get_builder_factory,
    create_bridge_domain_builder
)
from .unified_builder import UnifiedBridgeDomainBuilder

__all__ = [
    # Base classes
    'BaseBridgeDomainBuilder',
    'BridgeDomainConfig',
    'BridgeDomainResult',
    
    # Specific builders
    'P2PBridgeDomainBuilder',
    'P2MPBridgeDomainBuilder',
    
    # Factory
    'BuilderFactory',
    'TopologyType',
    'get_builder_factory',
    'create_bridge_domain_builder',
    
    # Main facade
    'UnifiedBridgeDomainBuilder'
]

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Consolidated bridge domain builders with P2P and P2MP support"
