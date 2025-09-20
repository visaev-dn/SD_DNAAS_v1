"""
Path validation error types.
"""

from enum import Enum


class PathValidationError(Enum):
    """Types of path validation errors."""
    EMPTY_PATH = "Path has no segments"
    DISCONTINUOUS_CHAIN = "Path segments don't form continuous chain"
    DEVICE_MISMATCH = "Segment device names don't match"
    INVALID_INTERFACE = "Interface connectivity is invalid"
    SINGLE_SEGMENT_PATH = "Path has only one segment (no intermediate devices)"
