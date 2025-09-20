#!/usr/bin/env python3
"""
Phase 1 Path Information Data Structure
Defines standardized path representation for topology data
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from .enums import TopologyType, ValidationStatus


@dataclass(frozen=True)
class PathSegment:
    """
    Immutable path segment structure for topology data.
    
    This class represents a single hop in a network path with
    source and destination device/interface information.
    """
    
    # Basic segment information (required fields)
    source_device: str
    dest_device: str
    source_interface: str
    dest_interface: str
    segment_type: str  # leaf_to_spine, spine_to_spine, spine_to_leaf
    
    # Optional fields with defaults
    connection_type: str = "direct"  # direct, bundle, lag
    bundle_id: Optional[int] = None
    confidence_score: float = field(default=1.0, metadata={'min': 0.0, 'max': 1.0})
    
    # Performance metrics
    bandwidth: Optional[float] = None  # Bandwidth in Mbps
    latency: Optional[float] = None    # Latency in milliseconds
    
    # Metadata with defaults
    discovered_at: datetime = field(default_factory=datetime.now)
    segment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate path segment after initialization"""
        self._validate_path_segment()
    
    def _validate_path_segment(self):
        """Validate path segment integrity"""
        if not self.source_device:
            raise ValueError("Source device cannot be empty")
        
        if not self.dest_device:
            raise ValueError("Destination device cannot be empty")
        
        if not self.source_interface:
            raise ValueError("Source interface cannot be empty")
        
        if not self.dest_interface:
            raise ValueError("Destination interface cannot be empty")
        
        if not self.segment_type:
            raise ValueError("Segment type cannot be empty")
        
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if self.bundle_id is not None and (self.bundle_id < 1 or self.bundle_id > 64):
            raise ValueError("Bundle ID must be between 1 and 64")
    
    @property
    def is_leaf_to_spine(self) -> bool:
        """Check if segment is leaf to spine"""
        return self.segment_type == "leaf_to_spine"
    
    @property
    def is_spine_to_spine(self) -> bool:
        """Check if segment is spine to spine"""
        return self.segment_type == "spine_to_spine"
    
    @property
    def is_spine_to_leaf(self) -> bool:
        """Check if segment is spine to leaf"""
        return self.segment_type == "spine_to_leaf"
    
    @property
    def is_bundled(self) -> bool:
        """Check if segment uses bundle interfaces"""
        return self.bundle_id is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert path segment to dictionary for serialization"""
        return {
            'segment_id': self.segment_id,
            'source_device': self.source_device,
            'dest_device': self.dest_device,
            'source_interface': self.source_interface,
            'dest_interface': self.dest_interface,
            'segment_type': self.segment_type,
            'connection_type': self.connection_type,
            'bundle_id': self.bundle_id,
            'bandwidth': self.bandwidth,
            'latency': self.latency,
            'discovered_at': self.discovered_at.isoformat(),
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathSegment':
        """Create PathSegment from dictionary"""
        # Convert datetime strings back to datetime objects
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        return cls(**data)


@dataclass(frozen=True)
class PathInfo:
    """
    Immutable path information structure for topology data.
    
    This class represents a complete network path between devices
    with all its segments and metadata.
    """
    
    # Path identification (required fields)
    path_name: str
    path_type: TopologyType
    source_device: str
    dest_device: str
    segments: List[PathSegment]
    
    # Optional fields with defaults
    is_active: bool = True
    is_redundant: bool = False
    confidence_score: float = field(default=1.0, metadata={'min': 0.0, 'max': 1.0})
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Metadata with defaults
    discovered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    path_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate path information after initialization"""
        self._validate_path_info()
    
    def _validate_path_info(self):
        """Validate path information integrity"""
        if not self.path_name:
            raise ValueError("Path name cannot be empty")
        
        if not isinstance(self.path_type, TopologyType):
            raise ValueError("Path type must be a valid TopologyType enum")
        
        if not self.source_device:
            raise ValueError("Source device cannot be empty")
        
        if not self.dest_device:
            raise ValueError("Destination device cannot be empty")
        
        if not self.segments:
            raise ValueError("Path must have at least one segment")
        
        if self.confidence_score is not None and (self.confidence_score < 0.0 or self.confidence_score > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Validate path continuity
        self._validate_path_continuity()
    
    def _validate_path_continuity(self):
        """Validate that path segments form a continuous path"""
        if len(self.segments) == 0:
            return
        
        # First segment should start with source device
        first_segment = self.segments[0]
        if first_segment.source_device != self.source_device:
            raise ValueError(f"First segment must start with source device {self.source_device}")
        
        # Last segment should end with dest device
        last_segment = self.segments[-1]
        if last_segment.dest_device != self.dest_device:
            raise ValueError(f"Last segment must end with destination device {self.dest_device}")
        
        # Adjacent segments should connect
        for i in range(len(self.segments) - 1):
            current_segment = self.segments[i]
            next_segment = self.segments[i + 1]
            
            if current_segment.dest_device != next_segment.source_device:
                raise ValueError(
                    f"Path discontinuity: segment {i} ends at {current_segment.dest_device}, "
                    f"segment {i+1} starts at {next_segment.source_device}"
                )
    
    @property
    def is_p2p(self) -> bool:
        """Check if path is point-to-point"""
        return self.path_type == TopologyType.P2P
    
    @property
    def is_p2mp(self) -> bool:
        """Check if path is point-to-multipoint"""
        return self.path_type == TopologyType.P2MP
    
    @property
    def path_length(self) -> int:
        """Get path length in segments"""
        return len(self.segments)
    
    @property
    def is_direct(self) -> bool:
        """Check if path is direct (single segment)"""
        return len(self.segments) == 1
    
    @property
    def is_multi_segment(self) -> bool:
        """Check if path is multi-segment"""
        return len(self.segments) > 1
    
    @property
    def intermediate_devices(self) -> List[str]:
        """Get list of intermediate devices (excluding source and destination)"""
        if len(self.segments) <= 1:
            return []
        
        intermediate = []
        for i in range(1, len(self.segments)):
            intermediate.append(self.segments[i].source_device)
        
        return intermediate
    
    @property
    def all_devices(self) -> List[str]:
        """Get all devices in the path (including source and destination)"""
        devices = [self.source_device]
        for segment in self.segments:
            if segment.dest_device not in devices:
                devices.append(segment.dest_device)
        return devices
    
    @property
    def all_interfaces(self) -> List[str]:
        """Get all interfaces in the path"""
        interfaces = []
        for segment in self.segments:
            if segment.source_interface not in interfaces:
                interfaces.append(segment.source_interface)
            if segment.dest_interface not in interfaces:
                interfaces.append(segment.dest_interface)
        return interfaces
    
    @property
    def bundle_interfaces(self) -> List[str]:
        """Get all bundle interfaces in the path"""
        bundle_interfaces = []
        for segment in self.segments:
            if segment.is_bundled:
                if segment.source_interface not in bundle_interfaces:
                    bundle_interfaces.append(segment.source_interface)
                if segment.dest_interface not in bundle_interfaces:
                    bundle_interfaces.append(segment.dest_interface)
        return bundle_interfaces
    
    def get_segment_by_device(self, device_name: str) -> Optional[PathSegment]:
        """Get path segment that involves a specific device"""
        for segment in self.segments:
            if segment.source_device == device_name or segment.dest_device == device_name:
                return segment
        return None
    
    def get_segments_by_type(self, segment_type: str) -> List[PathSegment]:
        """Get all segments of a specific type"""
        return [segment for segment in self.segments if segment.segment_type == segment_type]
    
    def has_device(self, device_name: str) -> bool:
        """Check if path includes a specific device"""
        return device_name in self.all_devices
    
    def has_interface(self, interface_name: str) -> bool:
        """Check if path includes a specific interface"""
        return interface_name in self.all_interfaces
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert path info to dictionary for serialization"""
        return {
            'path_id': self.path_id,
            'path_name': self.path_name,
            'path_type': self.path_type.value,
            'source_device': self.source_device,
            'dest_device': self.dest_device,
            'segments': [segment.to_dict() for segment in self.segments],
            'is_active': self.is_active,
            'is_redundant': self.is_redundant,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status.value,
            'discovered_at': self.discovered_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'source_data': self.source_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathInfo':
        """Create PathInfo from dictionary"""
        # Convert datetime strings back to datetime objects
        if 'discovered_at' in data and isinstance(data['discovered_at'], str):
            data['discovered_at'] = datetime.fromisoformat(data['discovered_at'])
        
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        # Convert segments
        if 'segments' in data:
            data['segments'] = [PathSegment.from_dict(seg) for seg in data['segments']]
        
        return cls(**data)
