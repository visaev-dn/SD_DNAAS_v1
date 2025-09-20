#!/usr/bin/env python3
"""
Bridge Domain Signature for Bulletproof Consolidation
Comprehensive signature matching to prevent dangerous consolidations
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, BridgeDomainScope, ComplexityLevel, 
    TopologyType, ValidationStatus, ConsolidationDecision
)


@dataclass(frozen=True)
class BridgeDomainSignature:
    """
    Comprehensive bridge domain signature for safe consolidation matching.
    
    This signature captures all critical aspects of a bridge domain to ensure
    only truly identical services are consolidated together.
    """
    
    # === IDENTITY COMPONENTS ===
    username: str                           # visaev, mochiu, etc.
    vlan_id: Optional[int]                  # Primary VLAN ID
    
    # === SERVICE CLASSIFICATION ===
    bridge_domain_type: BridgeDomainType    # Type 1, 2A, 2B, 3, 4A, 4B, 5
    template_category: str                  # SINGLE_VLAN, QINQ, VLAN_RANGE, etc.
    
    # === QINQ SPECIFIC (Types 1, 2A, 2B, 3) ===
    outer_vlan: Optional[int]               # QinQ outer tag
    inner_vlan: Optional[int]               # QinQ inner tag  
    qinq_imposition: Optional[str]          # edge, leaf, hybrid
    
    # === NETWORK SCOPE ===
    scope: BridgeDomainScope                # LOCAL, GLOBAL, UNSPECIFIED
    scope_validation: bool                  # Does actual match intended?
    
    # === TOPOLOGY PATTERN ===
    topology_type: TopologyType             # P2P, P2MP, HUB_SPOKE
    device_count: int                       # Number of devices
    interface_count: int                    # Number of interfaces
    complexity_level: ComplexityLevel       # SIMPLE, MODERATE, COMPLEX
    
    # === VLAN CONFIGURATION ===
    vlan_manipulation: bool                 # Has push/pop operations
    vlan_range_start: Optional[int]         # For VLAN ranges
    vlan_range_end: Optional[int]           # For VLAN ranges
    vlan_list: Optional[List[int]]          # For VLAN lists
    
    # === SAFETY METADATA ===
    confidence_score: float                 # Detection confidence (0.0-1.0)
    validation_status: ValidationStatus     # VALIDATED, PARTIAL, FAILED
    
    def _is_qinq_type(self) -> bool:
        """Check if this is a QinQ service type"""
        return self.bridge_domain_type in [
            BridgeDomainType.DOUBLE_TAGGED,
            BridgeDomainType.QINQ_SINGLE_BD, 
            BridgeDomainType.QINQ_MULTI_BD,
            BridgeDomainType.HYBRID
        ]
    
    def to_safe_consolidation_key(self) -> str:
        """
        Generate comprehensive consolidation key for bulletproof matching.
        
        Format: user:{username}|vlan:{vlan_id}|type:{dnaas_type}|outer:{outer_vlan}|
                inner:{inner_vlan}|scope:{scope}|topo:{topology_type}|
                dev_range:{device_range}|manip:{has_manipulation}
        """
        # Device count range for flexibility
        if self.device_count <= 2:
            device_range = "small"
        elif self.device_count <= 10:
            device_range = "medium"
        else:
            device_range = "large"
        
        # Build comprehensive key
        key_parts = [
            f"user:{self.username}",
            f"vlan:{self.vlan_id or 'none'}",
            f"type:{self.bridge_domain_type.value}",
            f"outer:{self.outer_vlan or 'none'}",
            f"inner:{self.inner_vlan or 'none'}",
            f"scope:{self.scope.value}",
            f"topo:{self.topology_type.value}",
            f"dev_range:{device_range}",
            f"manip:{str(self.vlan_manipulation).lower()}"
        ]
        
        return "|".join(key_parts)
    
    def to_debug_dict(self) -> Dict[str, Any]:
        """Convert signature to dictionary for debug logging"""
        return {
            "identity": {
                "username": self.username,
                "vlan_id": self.vlan_id
            },
            "service_classification": {
                "bridge_domain_type": self.bridge_domain_type.value,
                "template_category": self.template_category
            },
            "qinq_config": {
                "outer_vlan": self.outer_vlan,
                "inner_vlan": self.inner_vlan,
                "qinq_imposition": self.qinq_imposition,
                "is_qinq": self._is_qinq_type()
            },
            "network_scope": {
                "scope": self.scope.value,
                "scope_validation": self.scope_validation
            },
            "topology_pattern": {
                "topology_type": self.topology_type.value,
                "device_count": self.device_count,
                "interface_count": self.interface_count,
                "complexity_level": self.complexity_level.value
            },
            "vlan_configuration": {
                "vlan_manipulation": self.vlan_manipulation,
                "vlan_range_start": self.vlan_range_start,
                "vlan_range_end": self.vlan_range_end,
                "vlan_list": self.vlan_list
            },
            "safety_metadata": {
                "confidence_score": self.confidence_score,
                "validation_status": self.validation_status.value,
                "consolidation_key": self.to_safe_consolidation_key()
            }
        }


@dataclass
class ConsolidationValidationResult:
    """Result of consolidation validation between two signatures"""
    
    passed: bool                            # Did validation pass?
    reason: str                             # Reason for pass/fail
    confidence: float                       # Confidence in result
    rule_name: str                          # Which validation rule
    details: Dict[str, Any]                 # Additional details


@dataclass 
class ConsolidationDecisionResult:
    """Complete consolidation decision with full reasoning"""
    
    decision: ConsolidationDecision         # Final decision
    consolidation_key: str                  # Group key
    bridge_domain_names: List[str]          # BDs in group
    confidence: float                       # Overall confidence
    
    # Validation results
    validation_results: List[ConsolidationValidationResult]
    safety_score: float                     # Overall safety (0.0-1.0)
    
    # Reasoning
    approval_reasons: List[str]             # Why approved
    rejection_reasons: List[str]            # Why rejected
    warnings: List[str]                     # Warnings/concerns
    
    # Debug information
    signatures: List[BridgeDomainSignature] # All signatures in group
    debug_info: Dict[str, Any]              # Detailed debug data
    
    def to_debug_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for debug logging"""
        return {
            "decision_summary": {
                "decision": self.decision.value,
                "consolidation_key": self.consolidation_key,
                "bridge_domain_count": len(self.bridge_domain_names),
                "confidence": self.confidence,
                "safety_score": self.safety_score
            },
            "bridge_domains": self.bridge_domain_names,
            "validation_results": [
                {
                    "rule": vr.rule_name,
                    "passed": vr.passed,
                    "reason": vr.reason,
                    "confidence": vr.confidence
                } for vr in self.validation_results
            ],
            "reasoning": {
                "approval_reasons": self.approval_reasons,
                "rejection_reasons": self.rejection_reasons,
                "warnings": self.warnings
            },
            "signatures": [sig.to_debug_dict() for sig in self.signatures],
            "debug_info": self.debug_info
        }


def validate_service_type_match(sig1: BridgeDomainSignature, sig2: BridgeDomainSignature) -> ConsolidationValidationResult:
    """Validate exact service type compatibility"""
    
    # Must have identical DNAAS types
    if sig1.bridge_domain_type != sig2.bridge_domain_type:
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Different DNAAS types: {sig1.bridge_domain_type.value} vs {sig2.bridge_domain_type.value}",
            confidence=1.0,
            rule_name="service_type_match",
            details={
                "sig1_type": sig1.bridge_domain_type.value,
                "sig2_type": sig2.bridge_domain_type.value,
                "mismatch_severity": "critical"
            }
        )
    
    # For QinQ types, validate QinQ configuration
    if sig1._is_qinq_type():
        if (sig1.outer_vlan != sig2.outer_vlan or 
            sig1.inner_vlan != sig2.inner_vlan or
            sig1.qinq_imposition != sig2.qinq_imposition):
            return ConsolidationValidationResult(
                passed=False,
                reason=f"Different QinQ configs: {sig1.outer_vlan}.{sig1.inner_vlan} vs {sig2.outer_vlan}.{sig2.inner_vlan}",
                confidence=1.0,
                rule_name="qinq_configuration_match",
                details={
                    "sig1_qinq": f"{sig1.outer_vlan}.{sig1.inner_vlan}",
                    "sig2_qinq": f"{sig2.outer_vlan}.{sig2.inner_vlan}",
                    "sig1_imposition": sig1.qinq_imposition,
                    "sig2_imposition": sig2.qinq_imposition
                }
            )
    
    # For VLAN range types, validate ranges
    if sig1.bridge_domain_type == BridgeDomainType.SINGLE_TAGGED_RANGE:
        if (sig1.vlan_range_start != sig2.vlan_range_start or
            sig1.vlan_range_end != sig2.vlan_range_end):
            return ConsolidationValidationResult(
                passed=False,
                reason=f"Different VLAN ranges: {sig1.vlan_range_start}-{sig1.vlan_range_end} vs {sig2.vlan_range_start}-{sig2.vlan_range_end}",
                confidence=1.0,
                rule_name="vlan_range_match",
                details={
                    "sig1_range": f"{sig1.vlan_range_start}-{sig1.vlan_range_end}",
                    "sig2_range": f"{sig2.vlan_range_start}-{sig2.vlan_range_end}"
                }
            )
    
    # For VLAN list types, validate lists
    if sig1.bridge_domain_type == BridgeDomainType.SINGLE_TAGGED_LIST:
        if sig1.vlan_list != sig2.vlan_list:
            return ConsolidationValidationResult(
                passed=False,
                reason=f"Different VLAN lists: {sig1.vlan_list} vs {sig2.vlan_list}",
                confidence=1.0,
                rule_name="vlan_list_match",
                details={
                    "sig1_list": sig1.vlan_list,
                    "sig2_list": sig2.vlan_list
                }
            )
    
    return ConsolidationValidationResult(
        passed=True,
        reason="Service types match perfectly",
        confidence=1.0,
        rule_name="service_type_match",
        details={
            "bridge_domain_type": sig1.bridge_domain_type.value,
            "template_category": sig1.template_category
        }
    )


def validate_scope_consistency(sig1: BridgeDomainSignature, sig2: BridgeDomainSignature) -> ConsolidationValidationResult:
    """Validate network scope compatibility"""
    
    # Must have same intended scope
    if sig1.scope != sig2.scope:
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Scope violation: {sig1.scope.value} vs {sig2.scope.value}",
            confidence=1.0,
            rule_name="scope_consistency",
            details={
                "sig1_scope": sig1.scope.value,
                "sig2_scope": sig2.scope.value,
                "violation_type": "scope_mismatch"
            }
        )
    
    # Must have same scope validation status
    if sig1.scope_validation != sig2.scope_validation:
        return ConsolidationValidationResult(
            passed=False,
            reason="Different scope validation states",
            confidence=0.8,
            rule_name="scope_validation",
            details={
                "sig1_validation": sig1.scope_validation,
                "sig2_validation": sig2.scope_validation
            }
        )
    
    return ConsolidationValidationResult(
        passed=True,
        reason="Scopes consistent",
        confidence=1.0,
        rule_name="scope_consistency",
        details={
            "scope": sig1.scope.value,
            "scope_validation": sig1.scope_validation
        }
    )


def validate_topology_compatibility(sig1: BridgeDomainSignature, sig2: BridgeDomainSignature) -> ConsolidationValidationResult:
    """Validate topology pattern compatibility"""
    
    # Must have same topology type
    if sig1.topology_type != sig2.topology_type:
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Different topology types: {sig1.topology_type.value} vs {sig2.topology_type.value}",
            confidence=1.0,
            rule_name="topology_compatibility",
            details={
                "sig1_topology": sig1.topology_type.value,
                "sig2_topology": sig2.topology_type.value,
                "mismatch_type": "topology_pattern"
            }
        )
    
    # Device count must be similar (within reasonable range)
    device_diff = abs(sig1.device_count - sig2.device_count)
    max_allowed_diff = max(2, min(sig1.device_count, sig2.device_count) * 0.2)  # 20% or 2 devices
    
    if device_diff > max_allowed_diff:
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Device count too different: {sig1.device_count} vs {sig2.device_count} devices",
            confidence=0.9,
            rule_name="device_count_compatibility",
            details={
                "sig1_devices": sig1.device_count,
                "sig2_devices": sig2.device_count,
                "difference": device_diff,
                "max_allowed": max_allowed_diff
            }
        )
    
    # Complexity levels should be similar
    complexity_order = {'simple': 1, 'moderate': 2, 'complex': 3}
    complexity_diff = abs(
        complexity_order[sig1.complexity_level.value] - 
        complexity_order[sig2.complexity_level.value]
    )
    
    if complexity_diff > 1:
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Complexity too different: {sig1.complexity_level.value} vs {sig2.complexity_level.value}",
            confidence=0.8,
            rule_name="complexity_compatibility",
            details={
                "sig1_complexity": sig1.complexity_level.value,
                "sig2_complexity": sig2.complexity_level.value,
                "difference": complexity_diff
            }
        )
    
    return ConsolidationValidationResult(
        passed=True,
        reason="Topology patterns compatible",
        confidence=1.0,
        rule_name="topology_compatibility",
        details={
            "topology_type": sig1.topology_type.value,
            "device_count_range": f"{min(sig1.device_count, sig2.device_count)}-{max(sig1.device_count, sig2.device_count)}",
            "complexity_level": sig1.complexity_level.value
        }
    )


def validate_configuration_consistency(sig1: BridgeDomainSignature, sig2: BridgeDomainSignature) -> ConsolidationValidationResult:
    """Validate VLAN configuration consistency"""
    
    # VLAN manipulation must match
    if sig1.vlan_manipulation != sig2.vlan_manipulation:
        return ConsolidationValidationResult(
            passed=False,
            reason="Different VLAN manipulation patterns",
            confidence=0.9,
            rule_name="configuration_consistency",
            details={
                "sig1_manipulation": sig1.vlan_manipulation,
                "sig2_manipulation": sig2.vlan_manipulation
            }
        )
    
    # Confidence scores should be reasonable
    confidence_diff = abs(sig1.confidence_score - sig2.confidence_score)
    if confidence_diff > 0.3:  # 30% difference
        return ConsolidationValidationResult(
            passed=False,
            reason=f"Confidence too different: {sig1.confidence_score:.2f} vs {sig2.confidence_score:.2f}",
            confidence=0.7,
            rule_name="confidence_consistency",
            details={
                "sig1_confidence": sig1.confidence_score,
                "sig2_confidence": sig2.confidence_score,
                "difference": confidence_diff
            }
        )
    
    return ConsolidationValidationResult(
        passed=True,
        reason="Configurations consistent",
        confidence=1.0,
        rule_name="configuration_consistency",
        details={
            "vlan_manipulation": sig1.vlan_manipulation,
            "confidence_range": f"{min(sig1.confidence_score, sig2.confidence_score):.2f}-{max(sig1.confidence_score, sig2.confidence_score):.2f}"
        }
    )
