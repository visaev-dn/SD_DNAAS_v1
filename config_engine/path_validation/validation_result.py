"""
Validation result structures for path validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from .error_types import PathValidationError


@dataclass
class PathValidationError:
    """Detailed information about a path validation error."""
    error_type: PathValidationError
    segment_index: int
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of path validation."""
    is_valid: bool
    errors: List[PathValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    segment_details: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    validation_source: str = "path_validator"
    
    def add_error(self, error_type: PathValidationError, segment_index: int, 
                  message: str, context: Optional[Dict[str, Any]] = None):
        """Add a validation error."""
        error = PathValidationError(
            error_type=error_type,
            segment_index=segment_index,
            message=message,
            context=context or {}
        )
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
    
    def get_error_summary(self) -> str:
        """Get a human-readable summary of validation errors."""
        if not self.errors:
            return "No validation errors"
        
        summary = f"Validation failed with {len(self.errors)} error(s):\n"
        for error in self.errors:
            summary += f"  Segment {error.segment_index}: {error.message}\n"
        
        return summary
