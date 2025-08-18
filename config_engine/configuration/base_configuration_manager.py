#!/usr/bin/env python3
"""
Base Configuration Manager
Abstract base and data models for configuration generation/validation/diff
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.logging import get_logger
from core.exceptions import BusinessLogicError, ValidationError


@dataclass
class GeneratedConfig:
    success: bool
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConfigDiffResult:
    summary: str
    added_devices: int
    modified_devices: int
    removed_devices: int
    vlan_changes: int
    risk_level: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigValidationReport:
    valid: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BaseConfigurationManager(ABC):
    """Abstract base for configuration management"""
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("BaseConfigurationManager initialized")

    @abstractmethod
    def generate(self, builder_config: Dict[str, Any], user_id: int) -> GeneratedConfig:
        pass

    @abstractmethod
    def diff(self, current_config: Dict[str, Any], new_config: Dict[str, Any]) -> ConfigDiffResult:
        pass

    @abstractmethod
    def validate(self, new_config: Dict[str, Any], diff_details: Optional[Dict[str, Any]] = None) -> ConfigValidationReport:
        pass
