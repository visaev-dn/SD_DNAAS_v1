#!/usr/bin/env python3
"""
Configuration Package
Consolidated configuration management facade
"""

from .base_configuration_manager import (
    BaseConfigurationManager,
    GeneratedConfig,
    ConfigDiffResult,
    ConfigValidationReport,
)
from .configuration_manager import ConfigurationManager

__all__ = [
    'BaseConfigurationManager',
    'GeneratedConfig',
    'ConfigDiffResult',
    'ConfigValidationReport',
    'ConfigurationManager',
]
