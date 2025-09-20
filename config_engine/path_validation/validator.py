"""
Path validation logic for ensuring topology path continuity.
"""

from typing import List, Optional
from .error_types import PathValidationError
from .validation_result import ValidationResult, PathValidationError as ValidationError
from config_engine.phase1_data_structures.path_info import PathSegment


def validate_path_continuity(path_segments: List[PathSegment]) -> ValidationResult:
    """
    Validate that path segments form a continuous chain from source to destination.
    
    Args:
        path_segments: List of path segments to validate
        
    Returns:
        ValidationResult: Validation result with success/failure and error details
    """
    result = ValidationResult(is_valid=True)
    
    # Handle edge cases
    if not path_segments:
        result.add_error(
            PathValidationError.EMPTY_PATH,
            0,
            "Path has no segments"
        )
        return result
    
    if len(path_segments) == 1:
        # Single segment is valid but might be worth noting
        result.add_warning("Path has only one segment (direct connection)")
        return result
    
    # Validate continuous chain
    for i in range(len(path_segments) - 1):
        current_segment = path_segments[i]
        next_segment = path_segments[i + 1]
        
        # Check if current segment's destination matches next segment's source
        if current_segment.dest_device != next_segment.source_device:
            result.add_error(
                PathValidationError.DEVICE_MISMATCH,
                i,
                f"Segment {i} ends at '{current_segment.dest_device}' but segment {i+1} starts at '{next_segment.source_device}'",
                {
                    'current_segment': i,
                    'next_segment': i + 1,
                    'current_dest': current_segment.dest_device,
                    'next_source': next_segment.source_device
                }
            )
    
    # Additional validation: check if first segment starts with a valid source
    if path_segments and not path_segments[0].source_device:
        result.add_error(
            PathValidationError.INVALID_INTERFACE,
            0,
            "First segment has no source device"
        )
    
    # Additional validation: check if last segment ends with a valid destination
    if path_segments and not path_segments[-1].dest_device:
        result.add_error(
            PathValidationError.INVALID_INTERFACE,
            len(path_segments) - 1,
            "Last segment has no destination device"
        )
    
    return result


def validate_path_connectivity(path_segments: List[PathSegment]) -> ValidationResult:
    """
    Additional validation: check if the path actually connects from start to end.
    
    Args:
        path_segments: List of path segments to validate
        
    Returns:
        ValidationResult: Validation result for connectivity
    """
    result = ValidationResult(is_valid=True)
    
    if len(path_segments) < 2:
        return result  # Single segment or empty path handled by main validation
    
    # Check if we can trace from first source to last destination
    first_source = path_segments[0].source_device
    last_dest = path_segments[-1].dest_device
    
    if not first_source or not last_dest:
        result.add_error(
            PathValidationError.INVALID_INTERFACE,
            0,
            "Missing source or destination device information"
        )
        return result
    
    # Simple connectivity check: ensure path is continuous
    current_device = first_source
    for i, segment in enumerate(path_segments):
        if segment.source_device != current_device:
            result.add_error(
                PathValidationError.DISCONTINUOUS_CHAIN,
                i,
                f"Path discontinuity at segment {i}: expected source '{current_device}', got '{segment.source_device}'"
            )
            break
        
        current_device = segment.dest_device
    
    return result


def get_path_summary(path_segments: List[PathSegment]) -> str:
    """
    Get a human-readable summary of the path.
    
    Args:
        path_segments: List of path segments
        
    Returns:
        str: Path summary
    """
    if not path_segments:
        return "Empty path"
    
    if len(path_segments) == 1:
        segment = path_segments[0]
        return f"Direct connection: {segment.source_device} → {segment.dest_device}"
    
    # Multi-segment path
    path_str = f"{path_segments[0].source_device}"
    for segment in path_segments:
        path_str += f" → {segment.dest_device}"
    
    return path_str
