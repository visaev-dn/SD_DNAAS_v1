#!/usr/bin/env python3
"""
Device Type Classifier Component

SINGLE RESPONSIBILITY: Classify device types (LEAF/SPINE/SUPERSPINE)

INPUT: Device names, device configurations
OUTPUT: Device type classifications
DEPENDENCIES: None (pure classification)
"""

import os
import sys
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import DeviceType

logger = logging.getLogger(__name__)

@dataclass
class DeviceClassification:
    """Device classification result"""
    device_name: str
    device_type: DeviceType
    confidence: float
    classification_method: str

class DeviceTypeClassifier:
    """
    Device Type Classifier Component
    
    SINGLE RESPONSIBILITY: Classify device types (LEAF/SPINE/SUPERSPINE)
    """
    
    def __init__(self):
        # Device name patterns for classification
        self.device_patterns = {
            DeviceType.LEAF: [
                r'DNAAS-LEAF-[A-F]\d+',
                r'.*LEAF.*',
                r'.*-L\d+.*'
            ],
            DeviceType.SPINE: [
                r'DNAAS-SPINE-[A-F]\d+',
                r'.*SPINE.*',
                r'.*-S\d+.*'
            ],
            DeviceType.SUPERSPINE: [
                r'DNAAS-SuperSpine.*',
                r'.*SUPERSPINE.*',
                r'.*SuperSpine.*'
            ]
        }
    
    def classify_device_type(self, device_name: str) -> DeviceClassification:
        """
        Determine device type from device name pattern
        
        Args:
            device_name: Name of the device to classify
            
        Returns:
            DeviceClassification with type, confidence, and method
        """
        logger.debug(f"🔍 Classifying device type for: {device_name}")
        
        # Check each device type pattern
        for device_type, patterns in self.device_patterns.items():
            for pattern in patterns:
                if re.match(pattern, device_name, re.IGNORECASE):
                    confidence = self._calculate_pattern_confidence(device_name, pattern)
                    
                    classification = DeviceClassification(
                        device_name=device_name,
                        device_type=device_type,
                        confidence=confidence,
                        classification_method=f"pattern_match_{pattern}"
                    )
                    
                    logger.debug(f"✅ Classified {device_name} as {device_type.value} (confidence: {confidence})")
                    return classification
        
        # No pattern matched - default to LEAF with low confidence
        logger.warning(f"⚠️ No pattern matched for {device_name}, defaulting to LEAF")
        
        return DeviceClassification(
            device_name=device_name,
            device_type=DeviceType.LEAF,
            confidence=0.3,
            classification_method="default_fallback"
        )
    
    def classify_all_devices(self, device_names: List[str]) -> Dict[str, DeviceClassification]:
        """
        Classify device types for all devices
        
        Args:
            device_names: List of device names to classify
            
        Returns:
            Dictionary mapping device names to classifications
        """
        logger.info(f"🔍 Classifying device types for {len(device_names)} devices...")
        
        classifications = {}
        
        for device_name in device_names:
            try:
                classification = self.classify_device_type(device_name)
                classifications[device_name] = classification
            except Exception as e:
                logger.error(f"Failed to classify device {device_name}: {e}")
                # Create default classification
                classifications[device_name] = DeviceClassification(
                    device_name=device_name,
                    device_type=DeviceType.LEAF,
                    confidence=0.1,
                    classification_method="error_fallback"
                )
        
        # Log classification summary
        type_counts = {}
        for classification in classifications.values():
            device_type = classification.device_type.value
            type_counts[device_type] = type_counts.get(device_type, 0) + 1
        
        logger.info(f"🔍 Device classification complete: {type_counts}")
        return classifications
    
    def validate_device_type(self, device_name: str, device_config: Dict) -> bool:
        """
        Validate device type against configuration data
        
        Args:
            device_name: Device name
            device_config: Device configuration data
            
        Returns:
            True if device type is consistent with configuration
        """
        classification = self.classify_device_type(device_name)
        
        # Add configuration-based validation logic here
        # For now, return True as we don't have specific config validation rules
        return True
    
    def _calculate_pattern_confidence(self, device_name: str, pattern: str) -> float:
        """Calculate confidence score for pattern match"""
        
        # Higher confidence for more specific patterns
        if 'DNAAS-' in pattern:
            return 0.95  # High confidence for official naming
        elif 'LEAF' in pattern or 'SPINE' in pattern:
            return 0.85  # Medium-high confidence for type keywords
        else:
            return 0.70  # Medium confidence for generic patterns
    
    def get_device_type_enum(self, device_name: str) -> DeviceType:
        """
        Get device type enum for a device (convenience method)
        
        Args:
            device_name: Device name
            
        Returns:
            DeviceType enum value
        """
        classification = self.classify_device_type(device_name)
        return classification.device_type
