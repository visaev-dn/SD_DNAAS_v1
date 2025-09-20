"""
Path validation module for ensuring topology path continuity.
"""

from .validator import validate_path_continuity, validate_path_connectivity, get_path_summary, ValidationResult
from .error_types import PathValidationError

__all__ = ['validate_path_continuity', 'validate_path_connectivity', 'get_path_summary', 'ValidationResult', 'PathValidationError']
