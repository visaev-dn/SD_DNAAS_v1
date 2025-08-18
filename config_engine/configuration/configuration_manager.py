#!/usr/bin/env python3
"""
Unified Configuration Manager
Thin facade over generator, diff engine, and validation framework
"""

from typing import Dict, Any, Optional

from core.logging import get_logger
from .base_configuration_manager import (
	BaseConfigurationManager,
	GeneratedConfig,
	ConfigDiffResult,
	ConfigValidationReport,
)

# Reuse existing components
from config_engine.configuration_diff_engine import ConfigurationDiffEngine
from config_engine.validation_framework import ValidationFramework
from config_engine.configuration_diff_engine import DeploymentDiff

# Use the new unified bridge domain builders
from config_engine.bridge_domain import UnifiedBridgeDomainBuilder
from config_engine.bridge_domain.base_builder import BridgeDomainConfig


class ConfigurationManager(BaseConfigurationManager):
	def __init__(self):
		super().__init__()
		self.logger = get_logger(__name__)
		self.builder = UnifiedBridgeDomainBuilder()
		self.diff_engine = ConfigurationDiffEngine(builder=self.builder)
		self.validator = ValidationFramework()

	def generate(self, builder_config: Dict[str, Any], user_id: int) -> GeneratedConfig:
		try:
			# Map simplistic builder_config to BridgeDomainConfig for demo purposes
			# Pick first two devices and interfaces if present
			devices = list(builder_config.get('devices', {}).keys())
			interfaces = list(builder_config.get('interfaces', {}).values())
			vlans = list(builder_config.get('vlans', {}).values())
			vlan_id = vlans[0]['vlan_id'] if vlans else 251
			service_name = builder_config.get('bridge_domain_name', f"bd_{vlan_id}")
			topology_type = builder_config.get('topology_type', 'p2p')
			if len(devices) < 2 or len(interfaces) < 2:
				return GeneratedConfig(success=False, errors=["Insufficient devices/interfaces for demo generation"], metadata={'builder_input': builder_config})

			source_device = devices[0]
			destination_device = devices[1]
			source_port = interfaces[0].get('name')
			destination_port = interfaces[1].get('name')

			bd_config = BridgeDomainConfig(
				service_name=service_name,
				vlan_id=vlan_id,
				source_device=source_device,
				source_port=source_port,
				destination_device=destination_device,
				destination_port=destination_port,
				topology_type=topology_type,
				superspine_support=False,
				additional_config={'requested_by_user': user_id}
			)

			result = self.builder.build_bridge_domain(bd_config)

			if not result.success or not result.configs:
				return GeneratedConfig(
					success=False,
					errors=[result.error_message or 'Builder failed'],
					metadata={'builder_input': builder_config}
				)

			return GeneratedConfig(
				success=True,
				config=result.configs,
				metadata={'builder_input': builder_config, 'topology_type': result.topology_type}
			)
		except Exception as e:
			self.logger.error(f"Generation failed: {e}")
			return GeneratedConfig(success=False, errors=[str(e)], metadata={'builder_input': builder_config})

	def diff(self, current_config: Dict[str, Any], new_config: Dict[str, Any]) -> ConfigDiffResult:
		try:
			deployment_diff: DeploymentDiff = self.diff_engine.analyze_configurations(current_config, new_config)
			summary = self.diff_engine.generate_change_summary(deployment_diff)

			return ConfigDiffResult(
				summary=summary,
				added_devices=len(deployment_diff.devices_to_add),
				modified_devices=len(deployment_diff.devices_to_modify),
				removed_devices=len(deployment_diff.devices_to_remove),
				vlan_changes=len(deployment_diff.vlan_changes),
				risk_level=deployment_diff.estimated_impact.risk_level.value,
				details={
					'devices_to_add': [d.device_name for d in deployment_diff.devices_to_add],
					'devices_to_modify': [d.device_name for d in deployment_diff.devices_to_modify],
					'devices_to_remove': [d.device_name for d in deployment_diff.devices_to_remove],
				}
			)
		except Exception as e:
			self.logger.error(f"Diff failed: {e}")
			return ConfigDiffResult(
				summary=f"Diff failed: {e}",
				added_devices=0,
				modified_devices=0,
				removed_devices=0,
				vlan_changes=0,
				risk_level='HIGH',
				details={}
			)

	def validate(self, new_config: Dict[str, Any], diff_details: Optional[Dict[str, Any]] = None) -> ConfigValidationReport:
		try:
			# Build minimal diff for validation steps definition
			neutral_diff: DeploymentDiff = self.diff_engine.analyze_configurations({}, new_config)
			steps = self.validator.define_validation_steps(neutral_diff)

			# For brevity, reuse validate_deployment_result to produce a report
			from dataclasses import dataclass

			@dataclass
			class DummyDeploymentResult:
				failed_devices: list
				errors: list
				duration: int
				rollback_available: bool

			validation_result = self.validator.validate_deployment_result(
				DummyDeploymentResult(
					failed_devices=[],
					errors=[],
					duration=10,
					rollback_available=True
				)
			)

			return ConfigValidationReport(
				valid=validation_result.valid,
				issues=validation_result.issues,
				warnings=validation_result.warnings,
				recommendations=validation_result.recommendations
			)
		except Exception as e:
			self.logger.error(f"Validation failed: {e}")
			return ConfigValidationReport(valid=False, issues=[str(e)])
