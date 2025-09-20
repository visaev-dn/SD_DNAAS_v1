#!/usr/bin/env python3
"""
Phase 1 Data Structure Enums
Defines all enumeration types for standardized data representation
"""

from enum import Enum
from typing import List


class TopologyType(Enum):
    """Topology type enumeration"""
    P2P = "p2p"           # Point-to-point: one source, one destination
    P2MP = "p2mp"         # Point-to-multipoint: one source, multiple destinations
    QINQ_HUB_SPOKE = "qinq_hub_spoke"  # QinQ hub-and-spoke topology
    QINQ_MESH = "qinq_mesh"            # QinQ mesh topology
    QINQ_RING = "qinq_ring"            # QinQ ring topology


class DeviceType(Enum):
    """Device type enumeration"""
    LEAF = "leaf"          # Access layer device
    SPINE = "spine"        # Aggregation layer device
    SUPERSPINE = "superspine"  # Core layer device


class InterfaceType(Enum):
    """Interface type enumeration"""
    PHYSICAL = "physical"      # Physical interface (e.g., ge100-0/0/13)
    BUNDLE = "bundle"          # Port-channel/bundle interface (e.g., bundle-60000)
    SUBINTERFACE = "subinterface"  # VLAN subinterface (e.g., bundle-60000.257)


class InterfaceRole(Enum):
    """Interface role in bridge domain"""
    ACCESS = "access"          # User-facing interface
    UPLINK = "uplink"          # Interface to upstream device
    DOWNLINK = "downlink"      # Interface to downstream device
    TRANSPORT = "transport"    # Transport interface (spine/superspine)
    QINQ_MULTI = "qinq_multi"  # QinQ interface with multiple VLAN roles
    QINQ_EDGE = "qinq_edge"    # QinQ edge interface (outer tag imposition)
    QINQ_NETWORK = "qinq_network"  # QinQ network interface (transit)


class DeviceRole(Enum):
    """Device role in bridge domain topology"""
    SOURCE = "source"          # Source device (traffic origin)
    DESTINATION = "destination"  # Destination device (traffic target)
    TRANSPORT = "transport"    # Transport device (spine/superspine)
    QINQ_HUB = "qinq_hub"      # QinQ hub device (central point)
    QINQ_SPOKE = "qinq_spoke"  # QinQ spoke device (endpoint)


class ValidationStatus(Enum):
    """Data validation status"""
    PENDING = "pending"        # Not yet validated
    VALID = "valid"            # Passed validation
    INVALID = "invalid"        # Failed validation
    WARNING = "warning"        # Passed with warnings


class BridgeDomainType(Enum):
    """Official DNAAS bridge domain type enumeration"""
    # Official DNAAS Types (1-5)
    DOUBLE_TAGGED = "double_tagged"              # Type 1: Edge imposition
    QINQ_SINGLE_BD = "qinq_single_bd"            # Type 2A: LEAF manipulation, single BD
    QINQ_MULTI_BD = "qinq_multi_bd"              # Type 2B: LEAF manipulation, multi BD
    HYBRID = "hybrid"                            # Type 3: Mixed imposition
    SINGLE_TAGGED = "single_tagged"              # Type 4A: Single VLAN
    SINGLE_TAGGED_RANGE = "single_tagged_range"  # Type 4B: VLAN Range
    SINGLE_TAGGED_LIST = "single_tagged_list"    # Type 4B: VLAN List
    PORT_MODE = "port_mode"                      # Type 5: Physical interface bridging
    
    # Special cases
    EMPTY_BRIDGE_DOMAIN = "empty_bridge_domain"  # Bridge domain with no interfaces (needs review)
    
    # Legacy/Deprecated (for backward compatibility)
    VLAN_RANGE = "vlan_range"                    # → Use SINGLE_TAGGED_RANGE
    VLAN_LIST = "vlan_list"                      # → Use SINGLE_TAGGED_LIST
    SINGLE_VLAN = "single_vlan"                  # → Use SINGLE_TAGGED or PORT_MODE
    QINQ = "qinq"                                # → Use specific QINQ types


class OuterTagImposition(Enum):
    """Outer VLAN tag imposition method for DNAAS"""
    EDGE = "edge"       # double-tag at edge device
    LEAF = "leaf"       # outer-tag push/pop at leaf


class ConsolidationDecision(Enum):
    """Consolidation decision types for bulletproof validation"""
    APPROVE = "approve"
    REJECT = "reject"
    REVIEW_REQUIRED = "review_required"
    APPROVE_EXACT = "approve_exact"
    APPROVE_HIGH_CONFIDENCE = "approve_high_confidence"
    APPROVE_PARTIAL = "approve_partial"


class ComplexityLevel(Enum):
    """Service complexity levels for topology analysis"""
    SIMPLE = "simple"          # 1-2 devices, basic configuration
    MODERATE = "moderate"      # 3-10 devices, moderate complexity
    COMPLEX = "complex"        # 11+ devices, high complexity


class BridgeDomainScope(Enum):
    """Bridge domain scope classification based on naming convention and deployment pattern"""
    LOCAL = "local"           # l_ prefix - leaf-only, VLAN ID locally significant
    GLOBAL = "global"         # g_ prefix - multi-device, VLAN ID globally significant  
    UNSPECIFIED = "unspecified"  # No prefix - legacy/test/special cases
    
    @classmethod
    def detect_from_name(cls, bridge_domain_name: str) -> 'BridgeDomainScope':
        """
        Detect bridge domain scope from naming convention (user intention)
        
        Args:
            bridge_domain_name: Bridge domain name (e.g., 'l_user_v123', 'g_user_v456')
            
        Returns:
            BridgeDomainScope: Named scope (user intention)
        """
        if not bridge_domain_name:
            return cls.UNSPECIFIED
            
        name = bridge_domain_name.strip().lower()
        
        if name.startswith('l_'):
            return cls.LOCAL
        elif name.startswith('g_'):
            return cls.GLOBAL
        else:
            return cls.UNSPECIFIED
    
    @classmethod
    def detect_from_deployment(cls, device_count: int, topology_type: str = None) -> 'BridgeDomainScope':
        """
        Detect actual bridge domain scope from deployment pattern (network reality)
        
        Args:
            device_count: Number of devices the bridge domain spans
            topology_type: Optional topology type for additional context
            
        Returns:
            BridgeDomainScope: Actual deployment scope
        """
        if device_count <= 1:
            return cls.LOCAL  # Single device = local deployment
        else:
            return cls.GLOBAL  # Multiple devices = global deployment


# Helper functions for enum operations
def get_enum_values(enum_class: type) -> List[str]:
    """Get all values from an enum class"""
    return [e.value for e in enum_class]


def get_enum_names(enum_class: type) -> List[str]:
    """Get all names from an enum class"""
    return [e.name for e in enum_class]


def validate_enum_value(enum_class: type, value: str) -> bool:
    """Validate if a value exists in an enum class"""
    return value in get_enum_values(enum_class)


def get_dnaas_type_display_name(bridge_domain_type: BridgeDomainType) -> str:
    """Get official DNAAS type display name for CLI/UI"""
    display_names = {
        BridgeDomainType.DOUBLE_TAGGED: "Type 1 (Static Double-Tag)",
        BridgeDomainType.QINQ_SINGLE_BD: "Type 2A (LEAF Full Range QinQ)",
        BridgeDomainType.QINQ_MULTI_BD: "Type 2B (LEAF Specific Range QinQ)",
        BridgeDomainType.HYBRID: "Type 3 (Mixed Pattern)",
        BridgeDomainType.SINGLE_TAGGED: "Type 4A (Single VLAN)",
        BridgeDomainType.SINGLE_TAGGED_RANGE: "Type 4B (VLAN Range)",
        BridgeDomainType.SINGLE_TAGGED_LIST: "Type 4B (VLAN List)",
        BridgeDomainType.PORT_MODE: "Type 5 (Physical Bridge)",
        
        # Special cases
        BridgeDomainType.EMPTY_BRIDGE_DOMAIN: "⚠️ Empty BD (Needs Review)",
        
        # Legacy types
        BridgeDomainType.VLAN_RANGE: "Legacy (VLAN Range)",
        BridgeDomainType.VLAN_LIST: "Legacy (VLAN List)",
        BridgeDomainType.SINGLE_VLAN: "Legacy (Single VLAN)",
        BridgeDomainType.QINQ: "Legacy (QinQ)",
    }
    return display_names.get(bridge_domain_type, str(bridge_domain_type))

def get_enum_by_value(enum_class: type, value: str):
    """Get enum instance by value"""
    for enum_instance in enum_class:
        if enum_instance.value == value:
            return enum_instance
    return None

