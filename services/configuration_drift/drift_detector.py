#!/usr/bin/env python3
"""
Configuration Drift Detector

Detects when database and device reality are out of sync by analyzing
deployment results, commit-check outputs, and validation failures.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from .data_models import DriftEvent, DriftType, ConfigurationDriftException

logger = logging.getLogger(__name__)


class ConfigurationDriftDetector:
    """Detects database-reality sync issues from various sources"""
    
    def __init__(self):
        self.drift_patterns = self._load_drift_patterns()
        
    def detect_drift_from_commit_check(self, device_name: str, commit_check_output: str, 
                                      expected_configs: List[Dict]) -> Optional[DriftEvent]:
        """Detect drift from commit-check 'already configured' responses"""
        
        try:
            # Analyze commit-check output for drift indicators
            if 'no configuration changes were made' in commit_check_output.lower():
                
                # Extract interface information from expected configs
                interface_name = None
                if expected_configs:
                    # Look for interface in first command
                    first_config = expected_configs[0]
                    if isinstance(first_config, dict) and 'interface' in first_config:
                        interface_name = first_config['interface']
                    elif isinstance(first_config, str) and 'interfaces ' in first_config:
                        # Extract interface from command string
                        parts = first_config.split()
                        if len(parts) >= 2:
                            interface_name = parts[1]
                
                drift_event = DriftEvent(
                    drift_type=DriftType.INTERFACE_ALREADY_CONFIGURED,
                    device_name=device_name,
                    interface_name=interface_name,
                    expected_config={'commands': expected_configs},
                    detection_source="commit_check",
                    severity="medium",
                    resolution_options=["discover_and_sync", "skip", "override", "abort"]
                )
                
                logger.info(f"Drift detected from commit-check on {device_name}: {interface_name}")
                return drift_event
            
            # Check for other drift patterns
            if 'configuration already exists' in commit_check_output.lower():
                return DriftEvent(
                    drift_type=DriftType.BRIDGE_DOMAIN_ALREADY_EXISTS,
                    device_name=device_name,
                    detection_source="commit_check",
                    severity="medium"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting drift from commit-check: {e}")
            return None
    
    def detect_drift_from_deployment_result(self, deployment_result) -> List[DriftEvent]:
        """Detect drift from deployment execution results"""
        
        drift_events = []
        
        try:
            # Check execution results for drift indicators
            for device_name, exec_result in deployment_result.execution_results.items():
                
                if not exec_result.success:
                    # Check for "already configured" in error messages
                    if 'no configuration changes' in exec_result.error_message.lower():
                        drift_event = DriftEvent(
                            drift_type=DriftType.INTERFACE_ALREADY_CONFIGURED,
                            device_name=device_name,
                            detection_source="deployment_result",
                            severity="high",
                            actual_config={'error': exec_result.error_message}
                        )
                        drift_events.append(drift_event)
                
                # Check commit-check results for drift
                if hasattr(exec_result, 'commit_check_passed') and exec_result.commit_check_passed:
                    if exec_result.error_message and 'already configured' in exec_result.error_message.lower():
                        drift_event = DriftEvent(
                            drift_type=DriftType.INTERFACE_ALREADY_CONFIGURED,
                            device_name=device_name,
                            detection_source="commit_check_result",
                            severity="medium"
                        )
                        drift_events.append(drift_event)
            
            if drift_events:
                logger.info(f"Detected {len(drift_events)} drift events from deployment result")
            
            return drift_events
            
        except Exception as e:
            logger.error(f"Error detecting drift from deployment result: {e}")
            return []
    
    def detect_drift_from_validation_failure(self, device_name: str, interface_name: str, 
                                           validation_output: str) -> Optional[DriftEvent]:
        """Detect drift from post-deployment validation failures"""
        
        try:
            # Check if validation failed because interface doesn't exist as expected
            if 'not found' in validation_output.lower():
                return DriftEvent(
                    drift_type=DriftType.CONFIGURATION_MISMATCH,
                    device_name=device_name,
                    interface_name=interface_name,
                    detection_source="validation_failure",
                    severity="high",
                    actual_config={'validation_output': validation_output}
                )
            
            # Check for unexpected VLAN configurations
            if 'vlan-id' in validation_output.lower():
                return DriftEvent(
                    drift_type=DriftType.VLAN_CONFLICT,
                    device_name=device_name,
                    interface_name=interface_name,
                    detection_source="validation_mismatch",
                    severity="medium"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting drift from validation failure: {e}")
            return None
    
    def analyze_drift_patterns(self, drift_events: List[DriftEvent]) -> Dict:
        """Analyze drift patterns for operational insights"""
        
        try:
            analysis = {
                'total_events': len(drift_events),
                'by_type': {},
                'by_device': {},
                'by_source': {},
                'severity_distribution': {},
                'recommendations': []
            }
            
            # Analyze by type
            for event in drift_events:
                drift_type = event.drift_type.value
                analysis['by_type'][drift_type] = analysis['by_type'].get(drift_type, 0) + 1
                
                # Analyze by device
                device = event.device_name
                analysis['by_device'][device] = analysis['by_device'].get(device, 0) + 1
                
                # Analyze by source
                source = event.detection_source
                analysis['by_source'][source] = analysis['by_source'].get(source, 0) + 1
                
                # Analyze by severity
                severity = event.severity
                analysis['severity_distribution'][severity] = analysis['severity_distribution'].get(severity, 0) + 1
            
            # Generate recommendations
            if analysis['by_type'].get('interface_already_configured', 0) > 5:
                analysis['recommendations'].append("High number of already-configured interfaces - consider full device discovery")
            
            if len(analysis['by_device']) > 10:
                analysis['recommendations'].append("Drift detected across many devices - consider systematic sync")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing drift patterns: {e}")
            return {'error': str(e)}
    
    def _load_drift_patterns(self) -> Dict:
        """Load patterns for detecting different types of drift"""
        
        return {
            'already_configured_patterns': [
                'no configuration changes were made',
                'configuration already exists',
                'interface already configured',
                'vlan already assigned'
            ],
            'conflict_patterns': [
                'vlan conflict',
                'interface in use',
                'configuration conflict',
                'already assigned'
            ],
            'error_patterns': [
                'configuration error',
                'invalid configuration',
                'configuration failed',
                'syntax error'
            ]
        }


# Convenience functions
def detect_drift_from_commit_check(device_name: str, commit_check_output: str, 
                                  expected_configs: List[Dict]) -> Optional[DriftEvent]:
    """Convenience function to detect drift from commit-check"""
    detector = ConfigurationDriftDetector()
    return detector.detect_drift_from_commit_check(device_name, commit_check_output, expected_configs)


def detect_drift_from_deployment(deployment_result) -> List[DriftEvent]:
    """Convenience function to detect drift from deployment result"""
    detector = ConfigurationDriftDetector()
    return detector.detect_drift_from_deployment_result(deployment_result)


def analyze_drift_patterns(drift_events: List[DriftEvent]) -> Dict:
    """Convenience function to analyze drift patterns"""
    detector = ConfigurationDriftDetector()
    return detector.analyze_drift_patterns(drift_events)
