#!/usr/bin/env python3
"""
Phase 1 Database Models - Optimized Version
Enhanced models with consolidated configuration, proper interface classification, 
path groups, VLAN centralization, and confidence metrics.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Phase1TopologyData(Base):
    """
    Phase 1 Topology Data model for database storage.
    """
    
    __tablename__ = 'phase1_topology_data'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Bridge domain information
    bridge_domain_name = Column(String(255), nullable=False, unique=True)
    topology_type = Column(String(50), nullable=False)  # p2p, p2mp
    
    # VLAN configuration
    vlan_id = Column(Integer, nullable=True)
    
    # Discovery information
    discovered_at = Column(DateTime, nullable=False)
    scan_method = Column(String(100), nullable=False)  # cli_input, legacy_mapping, device_scan
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy integration
    legacy_config_id = Column(Integer, nullable=True)
    legacy_bridge_domain_id = Column(Integer, nullable=True)
    
    # Performance optimization fields
    device_count = Column(Integer, default=0)
    interface_count = Column(Integer, default=0)
    path_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    change_count = Column(Integer, default=0)
    
    # Service signature fields for deduplication
    service_signature = Column(String(500), nullable=True, unique=True, index=True)
    discovery_session_id = Column(String(100), nullable=True, index=True)
    discovery_count = Column(Integer, default=1)
    first_discovered_at = Column(DateTime, nullable=True)
    signature_confidence = Column(Float, default=0.0)
    signature_classification = Column(String(100), nullable=True)
    
    # Review and quality control fields
    review_required = Column(Boolean, default=False, index=True)
    review_reason = Column(String(500), nullable=True)
    data_sources = Column(JSON, nullable=True)  # Track contributing discovery runs
    
    # Relationships
    devices = relationship('Phase1DeviceInfo', back_populates='topology', cascade='all, delete-orphan')
    interfaces = relationship('Phase1InterfaceInfo', back_populates='topology', cascade='all, delete-orphan')
    bridge_domain_configs = relationship('Phase1BridgeDomainConfig', back_populates='topology', cascade='all, delete-orphan')
    paths = relationship('Phase1PathInfo', back_populates='topology', cascade='all, delete-orphan')
    
    def __init__(self, topology_data, legacy_config_id: int = None):
        """Initialize from Phase 1 TopologyData"""
        self.bridge_domain_name = topology_data.bridge_domain_name
        self.topology_type = topology_data.topology_type.value
        self.vlan_id = topology_data.vlan_id
        self.discovered_at = topology_data.discovered_at
        self.scan_method = getattr(topology_data, 'scan_method', 'unknown')
        self.confidence_score = topology_data.confidence_score
        self.validation_status = topology_data.validation_status.value
        self.legacy_config_id = legacy_config_id
        self.legacy_bridge_domain_id = getattr(topology_data, 'legacy_bridge_domain_id', None)
        
        # Calculate summary fields
        self.device_count = len(topology_data.devices)
        self.interface_count = len(topology_data.interfaces)
        self.path_count = len(topology_data.paths)
    
    def to_phase1_topology(self):
        """Convert back to Phase 1 TopologyData object"""
        from config_engine.phase1_data_structures import TopologyData, TopologyType, ValidationStatus
        
        # Reconstruct devices, interfaces, and paths
        devices = [device.to_phase1_device() for device in self.devices]
        interfaces = [interface.to_phase1_interface() for interface in self.interfaces]
        
        # Reconstruct paths with error handling for validation issues
        paths = []
        for path in self.paths:
            try:
                reconstructed_path = path.to_phase1_path()
                paths.append(reconstructed_path)
            except Exception as e:
                # Log the path reconstruction error but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Failed to reconstruct path {path.path_name}: {e}")
                # Skip this path rather than failing the entire topology
                continue
        
        # If no valid paths were reconstructed, create a minimal fallback path
        if not paths and devices:
            try:
                from config_engine.phase1_data_structures.path_info import PathInfo, PathSegment, TopologyType
                from config_engine.phase1_data_structures.enums import TopologyType as TopologyTypeEnum
                
                # Create a minimal path using the first device
                first_device = devices[0].name if devices else 'unknown_device'
                minimal_segment = PathSegment(
                    source_device=first_device,
                    dest_device=first_device,
                    source_interface='internal_switching',
                    dest_interface='internal_switching',
                    segment_type='minimal_fallback'
                )
                
                minimal_path = PathInfo(
                    path_name=f"{self.bridge_domain_name}_minimal_fallback",
                    path_type=TopologyTypeEnum.P2P,
                    source_device=first_device,
                    dest_device=first_device,
                    segments=[minimal_segment]
                )
                
                paths = [minimal_path]
                logger.warning(f"⚠️ Created minimal fallback path for {self.bridge_domain_name}")
                
            except Exception as fallback_error:
                logger.error(f"❌ Failed to create fallback path: {fallback_error}")
                # If even fallback fails, we'll let the TopologyData constructor handle it
        
        # Get bridge domain config if available
        bridge_domain_config = None
        if hasattr(self, 'bridge_domain_configs') and self.bridge_domain_configs:
            # Convert the first config to BridgeDomainConfig
            # Use absolute import to avoid conflicts with other BridgeDomainConfig classes
            import config_engine.phase1_data_structures.bridge_domain_config as bd_config_module
            import config_engine.phase1_data_structures.enums as enums_module
            config = self.bridge_domain_configs[0]
            
            # Convert destinations to the expected format (device, port)
            formatted_destinations = []
            if hasattr(config, 'destinations') and config.destinations:
                try:
                    # Parse JSON destinations if it's a string
                    destinations_data = config.destinations
                    if isinstance(destinations_data, str):
                        destinations_data = json.loads(destinations_data)
                    
                    for dest in destinations_data:
                        if isinstance(dest, dict):
                            # Convert 'interface' to 'port' to match expected format
                            formatted_dest = {
                                'device': dest.get('device', 'unknown'),
                                'port': dest.get('interface', dest.get('port', 'unknown'))
                            }
                            formatted_destinations.append(formatted_dest)
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, use fallback
                    pass
            
            # Ensure at least one destination exists (validation requirement)
            if not formatted_destinations:
                # Use the first device from the devices list if available
                first_device = devices[0].name if devices else 'unknown'
                formatted_destinations = [{'device': first_device, 'port': 'unknown'}]
            
            try:
                # Handle potential enum conversion issues
                bridge_domain_type = enums_module.BridgeDomainType(config.bridge_domain_type) if config.bridge_domain_type else enums_module.BridgeDomainType.SINGLE_VLAN
                
                # Handle outer tag imposition conversion
                outer_tag_imposition = None
                if config.outer_tag_imposition:
                    try:
                        outer_tag_imposition = enums_module.OuterTagImposition(config.outer_tag_imposition)
                    except ValueError:
                        # Use default if conversion fails
                        outer_tag_imposition = enums_module.OuterTagImposition.EDGE
                
                # Handle bridge domain scope conversion
                bridge_domain_scope = None
                if hasattr(config, 'bridge_domain_scope') and config.bridge_domain_scope:
                    try:
                        bridge_domain_scope = enums_module.BridgeDomainScope(config.bridge_domain_scope)
                    except ValueError:
                        # Auto-detect if conversion fails
                        bridge_domain_scope = enums_module.BridgeDomainScope.detect_from_name(config.service_name or '')
                else:
                    # Auto-detect if not present
                    bridge_domain_scope = enums_module.BridgeDomainScope.detect_from_name(config.service_name or '')

                bridge_domain_config = bd_config_module.BridgeDomainConfig(
                    service_name=config.service_name or 'unknown',
                    bridge_domain_type=bridge_domain_type,
                    source_device=config.source_device or 'unknown',
                    source_interface=config.source_interface or 'unknown',
                    destinations=formatted_destinations,
                    vlan_id=config.vlan_id,
                    bridge_domain_scope=bridge_domain_scope,
                    outer_tag_imposition=outer_tag_imposition,
                    created_at=config.created_at,
                    confidence_score=config.confidence_score or 0.0,
                    validation_status=enums_module.ValidationStatus(config.validation_status) if config.validation_status else enums_module.ValidationStatus.PENDING
                )
            except Exception as e:
                # If BridgeDomainConfig creation fails, create a minimal one
                bridge_domain_config = bd_config_module.BridgeDomainConfig(
                    service_name=config.service_name or 'unknown',
                    bridge_domain_type=enums_module.BridgeDomainType.SINGLE_VLAN,
                    source_device=config.source_device or 'unknown',
                    source_interface=config.source_interface or 'unknown',
                    destinations=formatted_destinations,
                    vlan_id=config.vlan_id,
                    bridge_domain_scope=enums_module.BridgeDomainScope.detect_from_name(config.service_name or '')
                )
        
        # If no bridge domain config was created, create a minimal one
        if bridge_domain_config is None:
            import config_engine.phase1_data_structures.bridge_domain_config as bd_config_module
            import config_engine.phase1_data_structures.enums as enums_module
            
            # Create a minimal bridge domain config with default values
            first_device = devices[0].name if devices else 'unknown'
            bridge_domain_config = bd_config_module.BridgeDomainConfig(
                service_name=self.bridge_domain_name or 'unknown',
                bridge_domain_type=enums_module.BridgeDomainType.SINGLE_VLAN,
                source_device=first_device,
                source_interface='unknown',
                destinations=[{'device': first_device, 'port': 'unknown'}],
                vlan_id=self.vlan_id or 1,
                bridge_domain_scope=enums_module.BridgeDomainScope.detect_from_name(self.bridge_domain_name or '')
            )
        
        # Use a default scan method if not available
        scan_method = getattr(self, 'scan_method', 'unknown')
        

        
        return TopologyData(
            bridge_domain_name=self.bridge_domain_name,
            topology_type=TopologyType(self.topology_type),
            vlan_id=self.vlan_id,
            devices=devices,
            interfaces=interfaces,
            paths=paths,
            bridge_domain_config=bridge_domain_config,
            discovered_at=self.discovered_at,
            scan_method=scan_method,
            confidence_score=self.confidence_score,
            validation_status=ValidationStatus(self.validation_status)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'bridge_domain_name': self.bridge_domain_name,
            'topology_type': self.topology_type,
            'vlan_id': self.vlan_id,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'scan_method': self.scan_method,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'legacy_config_id': self.legacy_config_id,
            'legacy_bridge_domain_id': self.legacy_bridge_domain_id,
            'device_count': self.device_count,
            'interface_count': self.interface_count,
            'path_count': self.path_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'change_count': self.change_count
        }


class Phase1DeviceInfo(Base):
    """
    Phase 1 Device Information model for database storage.
    """
    
    __tablename__ = 'phase1_device_info'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    topology_id = Column(Integer, ForeignKey('phase1_topology_data.id'), nullable=False)
    
    # Device information
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)  # leaf, spine, superspine
    device_role = Column(String(50), nullable=False)  # source, destination, transport
    
    # Enhanced device role fields
    is_primary_source = Column(Boolean, default=False)  # NEW: Only one primary source per BD
    redundancy_group_id = Column(Integer, nullable=True)  # NEW: Group related devices
    
    # Device details
    device_id = Column(String(255), nullable=True)
    row = Column(String(10), nullable=True)
    rack = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default='pending')
    
    # Relationships
    topology = relationship('Phase1TopologyData', back_populates='devices')
    interfaces = relationship('Phase1InterfaceInfo', back_populates='device', cascade='all, delete-orphan')
    
    def __init__(self, device_info, topology_id: int):
        """Initialize from Phase 1 DeviceInfo"""
        self.topology_id = topology_id
        self.name = device_info.name
        self.device_type = device_info.device_type.value
        self.device_role = device_info.device_role.value
        self.device_id = getattr(device_info, 'device_id', None)
        self.row = getattr(device_info, 'row', None)
        self.rack = getattr(device_info, 'rack', None)
        self.model = getattr(device_info, 'model', None)
        self.serial_number = getattr(device_info, 'serial_number', None)
        self.discovered_at = device_info.discovered_at
        self.confidence_score = device_info.confidence_score
        self.validation_status = device_info.validation_status.value
        
        # Enhanced role logic
        self.is_primary_source = (device_info.device_role.value == 'source' and 
                                 device_info.device_type.value == 'leaf')
        self.redundancy_group_id = getattr(device_info, 'redundancy_group_id', None)
    
    def to_phase1_device(self):
        """Convert back to Phase 1 DeviceInfo object"""
        from config_engine.phase1_data_structures import DeviceInfo, DeviceType, DeviceRole, ValidationStatus
        
        return DeviceInfo(
            name=self.name,
            device_type=DeviceType(self.device_type),
            device_role=DeviceRole(self.device_role),
            device_id=self.device_id,
            row=self.row,
            rack=self.rack,
            position=getattr(self, 'position', None),
            total_interfaces=getattr(self, 'total_interfaces', 0),
            available_interfaces=getattr(self, 'available_interfaces', 0),
            configured_interfaces=getattr(self, 'configured_interfaces', 0),
            discovered_at=self.discovered_at,
            confidence_score=self.confidence_score,
            validation_status=ValidationStatus(self.validation_status)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'device_role': self.device_role,
            'is_primary_source': self.is_primary_source,
            'redundancy_group_id': self.redundancy_group_id,
            'device_id': self.device_id,
            'row': self.row,
            'rack': self.rack,
            'model': self.model,
            'serial_number': self.serial_number,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status
        }


class Phase1InterfaceInfo(Base):
    """
    Phase 1 Interface Information model for database storage.
    """
    
    __tablename__ = 'phase1_interface_info'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    topology_id = Column(Integer, ForeignKey('phase1_topology_data.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('phase1_device_info.id'), nullable=False)
    
    # Interface information
    name = Column(String(255), nullable=False)
    interface_type = Column(String(50), nullable=False)  # physical, bundle, subinterface, port-channel
    
    # Enhanced interface classification
    parent_interface = Column(String(255), nullable=True)  # NEW: For subinterfaces (e.g., "bundle-60000")
    subinterface_id = Column(String(50), nullable=True)   # NEW: For subinterfaces (e.g., "251")
    
    interface_role = Column(String(50), nullable=False)  # access, transport, management
    
    # Configuration
    vlan_id = Column(Integer, nullable=True)
    l2_service_enabled = Column(Boolean, default=False)
    outer_tag_imposition = Column(String(50), nullable=True)  # edge, core, none
    
    # Timestamps
    discovered_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default='pending')
    
    # Relationships
    topology = relationship('Phase1TopologyData', back_populates='interfaces')
    device = relationship('Phase1DeviceInfo', back_populates='interfaces')
    
    def __init__(self, interface_info, topology_id: int, device_id: int):
        """Initialize from Phase 1 InterfaceInfo"""
        self.topology_id = topology_id
        self.device_id = device_id
        self.name = interface_info.name
        self.interface_type = interface_info.interface_type.value
        self.interface_role = interface_info.interface_role.value
        self.vlan_id = interface_info.vlan_id
        self.l2_service_enabled = interface_info.l2_service_enabled
        self.outer_tag_imposition = getattr(interface_info, 'outer_tag_imposition', None)
        if self.outer_tag_imposition:
            self.outer_tag_imposition = self.outer_tag_imposition.value
        self.discovered_at = interface_info.discovered_at
        self.confidence_score = interface_info.confidence_score
        self.validation_status = interface_info.validation_status.value
        
        # Enhanced interface classification
        if '.' in interface_info.name:
            # This is a subinterface (e.g., "bundle-60000.251")
            parts = interface_info.name.split('.')
            self.parent_interface = parts[0]
            self.subinterface_id = parts[1]
            self.interface_type = 'subinterface'  # Override the original type
        elif interface_info.name.startswith('bundle-') or interface_info.name.startswith('port-channel'):
            self.interface_type = 'bundle'
    
    def to_phase1_interface(self):
        """Convert back to Phase 1 InterfaceInfo object"""
        from config_engine.phase1_data_structures import InterfaceInfo, InterfaceType, InterfaceRole, ValidationStatus
        
        # Convert subinterface_id to integer if it's a string
        subinterface_id = getattr(self, 'subinterface_id', None)
        if subinterface_id is not None and isinstance(subinterface_id, str):
            try:
                subinterface_id = int(subinterface_id)
            except ValueError:
                subinterface_id = None
        
        return InterfaceInfo(
            name=self.name,
            interface_type=InterfaceType(self.interface_type),
            interface_role=InterfaceRole(self.interface_role),
            device_name=self.device.name if self.device else 'unknown',
            vlan_id=self.vlan_id,
            bundle_id=getattr(self, 'bundle_id', None),
            subinterface_id=subinterface_id,
            l2_service_enabled=self.l2_service_enabled,
            discovered_at=self.discovered_at,
            confidence_score=self.confidence_score,
            validation_status=ValidationStatus(self.validation_status)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'interface_type': self.interface_type,
            'interface_role': self.interface_role,
            'parent_interface': self.parent_interface,
            'subinterface_id': self.subinterface_id,
            'device_name': self.device.name if self.device else 'unknown',
            'vlan_id': self.vlan_id,
            'l2_service_enabled': self.l2_service_enabled,
            'outer_tag_imposition': self.outer_tag_imposition,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status
        }


class Phase1BridgeDomainConfig(Base):
    """
    Phase 1 Bridge Domain Configuration model for database storage.
    OPTIMIZED: Now includes destinations as JSON field for consolidation.
    """
    
    __tablename__ = 'phase1_bridge_domain_config'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    topology_id = Column(Integer, ForeignKey('phase1_topology_data.id'), nullable=False)
    
    # Configuration information
    service_name = Column(String(255), nullable=False)
    bridge_domain_type = Column(String(50), nullable=False)  # single_vlan, multi_vlan, etc.
    source_device = Column(String(255), nullable=False)
    source_interface = Column(String(255), nullable=False)
    
    # OPTIMIZED: Consolidated destinations as JSON
    destinations = Column(JSON, nullable=False)  # NEW: Array of destination objects
    
    # Configuration details
    vlan_id = Column(Integer, nullable=True)
    outer_vlan = Column(Integer, nullable=True)  # For QinQ configurations
    inner_vlan = Column(Integer, nullable=True)  # For QinQ configurations
    outer_tag_imposition = Column(String(50), nullable=True)  # edge, core, none
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default='pending')
    
    # Consolidation metadata
    bridge_domain_scope = Column(String(20), nullable=True)  # LOCAL, GLOBAL, UNSPECIFIED
    is_consolidated = Column(Boolean, default=False)
    consolidation_key = Column(String(255), nullable=True)  # username_vlan key for grouping
    original_names = Column(JSON, nullable=True)  # List of original BD names before consolidation
    consolidation_reason = Column(String(500), nullable=True)  # Why this was consolidated
    
    # Relationships
    topology = relationship('Phase1TopologyData', back_populates='bridge_domain_configs')
    vlan_configs = relationship('Phase1VlanConfig', back_populates='bridge_domain_config', cascade='all, delete-orphan')
    path_groups = relationship('Phase1PathGroup', back_populates='bridge_domain_config', cascade='all, delete-orphan')
    confidence_metrics = relationship('Phase1ConfidenceMetrics', back_populates='bridge_domain_config', cascade='all, delete-orphan')
    
    def __init__(self, config, topology_id: int):
        """Initialize from Phase 1 BridgeDomainConfig"""
        self.topology_id = topology_id
        self.service_name = config.service_name
        self.bridge_domain_type = config.bridge_domain_type.value
        self.source_device = config.source_device
        self.source_interface = config.source_interface
        self.vlan_id = config.vlan_id
        self.outer_tag_imposition = getattr(config, 'outer_tag_imposition', None)
        if self.outer_tag_imposition:
            self.outer_tag_imposition = self.outer_tag_imposition.value
        self.created_at = datetime.utcnow()
        self.confidence_score = getattr(config, 'confidence_score', 0.0)
        self.validation_status = getattr(config, 'validation_status', 'pending')
        if self.validation_status:
            self.validation_status = self.validation_status.value
        
        # Initialize empty destinations (will be populated later)
        self.destinations = []
    
    def add_destination(self, device: str, interface: str, vlan_id: int = None):
        """Add a destination to the destinations JSON array"""
        if not self.destinations:
            self.destinations = []
        
        destination = {
            'device': device,
            'interface': interface,
            'vlan_id': vlan_id,
            'created_at': datetime.utcnow().isoformat()
        }
        self.destinations.append(destination)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'service_name': self.service_name,
            'bridge_domain_type': self.bridge_domain_type,
            'source_device': self.source_device,
            'source_interface': self.source_interface,
            'destinations': self.destinations,
            'vlan_id': self.vlan_id,
            'outer_tag_imposition': self.outer_tag_imposition,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status
        }


class Phase1VlanConfig(Base):
    """
    Phase 1 VLAN Configuration model for database storage.
    NEW: Centralized VLAN configuration to eliminate repetition.
    """
    
    __tablename__ = 'phase1_vlan_configs'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    config_id = Column(Integer, ForeignKey('phase1_bridge_domain_config.id'), nullable=False)
    
    # VLAN configuration
    vlan_id = Column(Integer, nullable=False)
    vlan_type = Column(String(50), nullable=False)  # 'single', 'range', 'list', 'qinq'
    
    # QinQ configuration
    outer_vlan = Column(Integer, nullable=True)
    inner_vlan = Column(Integer, nullable=True)
    bridge_domain_scope = Column(String(20), nullable=True)  # local, global, unspecified
    
    # VLAN range configuration
    vlan_range_start = Column(Integer, nullable=True)
    vlan_range_end = Column(Integer, nullable=True)
    
    # VLAN list configuration
    vlan_list = Column(JSON, nullable=True)  # Array of VLAN IDs
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bridge_domain_config = relationship('Phase1BridgeDomainConfig', back_populates='vlan_configs')
    
    def __init__(self, config_id: int, vlan_id: int, vlan_type: str = 'single'):
        """Initialize VLAN configuration"""
        self.config_id = config_id
        self.vlan_id = vlan_id
        self.vlan_type = vlan_type
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vlan_id': self.vlan_id,
            'vlan_type': self.vlan_type,
            'outer_vlan': self.outer_vlan,
            'inner_vlan': self.inner_vlan,
            'vlan_range_start': self.vlan_range_start,
            'vlan_range_end': self.vlan_range_end,
            'vlan_list': self.vlan_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Phase1PathGroup(Base):
    """
    Phase 1 Path Group model for database storage.
    NEW: Consolidates multiple paths between same source-destination pairs.
    """
    
    __tablename__ = 'phase1_path_groups'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    config_id = Column(Integer, ForeignKey('phase1_bridge_domain_config.id'), nullable=False)
    
    # Path group information
    source_device = Column(String(255), nullable=False)
    destination_device = Column(String(255), nullable=False)
    path_count = Column(Integer, default=1)
    
    # Path references
    primary_path_id = Column(Integer, nullable=True)  # Reference to best path
    backup_paths = Column(JSON, nullable=True)  # Array of backup path IDs
    
    # Load balancing and redundancy
    load_balancing_type = Column(String(50), default='active-active')  # active-active, active-backup, round-robin
    redundancy_level = Column(String(50), default='none')  # none, n+1, 2n
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bridge_domain_config = relationship('Phase1BridgeDomainConfig', back_populates='path_groups')
    
    def __init__(self, config_id: int, source_device: str, destination_device: str):
        """Initialize path group"""
        self.config_id = config_id
        self.source_device = source_device
        self.destination_device = destination_device
        self.created_at = datetime.utcnow()
        self.backup_paths = []
    
    def add_backup_path(self, path_id: int):
        """Add a backup path to the group"""
        if not self.backup_paths:
            self.backup_paths = []
        self.backup_paths.append(path_id)
        self.path_count = len(self.backup_paths) + (1 if self.primary_path_id else 0)
    
    def set_primary_path(self, path_id: int):
        """Set the primary path for this group"""
        self.primary_path_id = path_id
        self.path_count = len(self.backup_paths) + 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'source_device': self.source_device,
            'destination_device': self.destination_device,
            'path_count': self.path_count,
            'primary_path_id': self.primary_path_id,
            'backup_paths': self.backup_paths,
            'load_balancing_type': self.load_balancing_type,
            'redundancy_level': self.redundancy_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Phase1ConfidenceMetrics(Base):
    """
    Phase 1 Confidence Metrics model for database storage.
    NEW: Detailed confidence scoring with weighted calculations.
    """
    
    __tablename__ = 'phase1_confidence_metrics'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    config_id = Column(Integer, ForeignKey('phase1_bridge_domain_config.id'), nullable=False)
    
    # Confidence scores by component
    device_confidence = Column(Float, default=0.0)
    interface_confidence = Column(Float, default=0.0)
    path_confidence = Column(Float, default=0.0)
    vlan_confidence = Column(Float, default=0.0)
    
    # Overall confidence
    overall_confidence = Column(Float, default=0.0)
    
    # Confidence factors (JSON array of contributing factors)
    confidence_factors = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bridge_domain_config = relationship('Phase1BridgeDomainConfig', back_populates='confidence_metrics')
    
    def __init__(self, config_id: int):
        """Initialize confidence metrics"""
        self.config_id = config_id
        self.created_at = datetime.utcnow()
        self.confidence_factors = []
    
    def calculate_overall_confidence(self):
        """Calculate weighted overall confidence score"""
        # Weighted average: devices (30%), interfaces (30%), paths (25%), VLAN (15%)
        weights = {
            'device': 0.30,
            'interface': 0.30,
            'path': 0.25,
            'vlan': 0.15
        }
        
        self.overall_confidence = (
            (self.device_confidence * weights['device']) +
            (self.interface_confidence * weights['interface']) +
            (self.path_confidence * weights['path']) +
            (self.vlan_confidence * weights['vlan'])
        )
        
        return self.overall_confidence
    
    def add_confidence_factor(self, factor_type: str, score: float, reason: str):
        """Add a confidence factor"""
        if not self.confidence_factors:
            self.confidence_factors = []
        
        factor = {
            'type': factor_type,
            'score': score,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.confidence_factors.append(factor)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'device_confidence': self.device_confidence,
            'interface_confidence': self.interface_confidence,
            'path_confidence': self.path_confidence,
            'vlan_confidence': self.vlan_confidence,
            'overall_confidence': self.overall_confidence,
            'confidence_factors': self.confidence_factors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Phase1PathInfo(Base):
    """
    Phase 1 Path Information model for database storage.
    """
    
    __tablename__ = 'phase1_path_info'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    topology_id = Column(Integer, ForeignKey('phase1_topology_data.id'), nullable=False)
    
    # Path information
    path_name = Column(String(255), nullable=False)
    path_type = Column(String(50), nullable=False)  # p2p, p2mp
    source_device = Column(String(255), nullable=False)
    dest_device = Column(String(255), nullable=False)
    
    # Path details
    # Timestamps
    discovered_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    validation_status = Column(String(50), default='pending')
    
    # Relationships
    topology = relationship('Phase1TopologyData', back_populates='paths')
    segments = relationship('Phase1PathSegment', back_populates='path', cascade='all, delete-orphan')
    
    def __init__(self, path_info, topology_id: int):
        """Initialize from Phase 1 PathInfo"""
        self.topology_id = topology_id
        self.path_name = path_info.path_name
        self.path_type = path_info.path_type.value
        self.source_device = path_info.source_device
        self.dest_device = path_info.dest_device
        self.discovered_at = path_info.discovered_at
        self.confidence_score = path_info.confidence_score
        self.validation_status = path_info.validation_status.value
    
    def to_phase1_path(self):
        """Convert back to Phase 1 PathInfo object"""
        from config_engine.phase1_data_structures import PathInfo, TopologyType, ValidationStatus
        
        # Reconstruct segments
        segments = [segment.to_phase1_segment() for segment in self.segments]
        
        return PathInfo(
            path_name=self.path_name,
            path_type=TopologyType(self.path_type),
            source_device=self.source_device,
            dest_device=self.dest_device,
            segments=segments,
            discovered_at=self.discovered_at,
            confidence_score=self.confidence_score,
            validation_status=ValidationStatus(self.validation_status)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'path_name': self.path_name,
            'path_type': self.path_type,
            'source_device': self.source_device,
            'dest_device': self.dest_device,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status,
            'segment_count': len(self.segments)
        }


class Phase1PathSegment(Base):
    """
    Phase 1 Path Segment model for database storage.
    """
    
    __tablename__ = 'phase1_path_segments'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    path_id = Column(Integer, ForeignKey('phase1_path_info.id'), nullable=False)
    
    # Segment information
    source_device = Column(String(255), nullable=False)
    dest_device = Column(String(255), nullable=False)
    source_interface = Column(String(255), nullable=False)
    dest_interface = Column(String(255), nullable=False)
    segment_type = Column(String(100), nullable=False)
    
    # Connection details
    connection_type = Column(String(50), default='direct')
    
    # Performance metrics
    bandwidth = Column(Float, nullable=True)
    latency = Column(Float, nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    path = relationship('Phase1PathInfo', back_populates='segments')
    
    def __init__(self, segment, path_id: int):
        """Initialize from Phase 1 PathSegment"""
        self.path_id = path_id
        self.source_device = segment.source_device
        self.dest_device = segment.dest_device
        self.source_interface = segment.source_interface
        self.dest_interface = segment.dest_interface
        self.segment_type = segment.segment_type
        self.connection_type = segment.connection_type
        self.bandwidth = getattr(segment, 'bandwidth', None)
        self.latency = getattr(segment, 'latency', None)
        self.discovered_at = segment.discovered_at
        self.confidence_score = segment.confidence_score
    
    def to_phase1_segment(self):
        """Convert back to Phase 1 PathSegment object"""
        from config_engine.phase1_data_structures import PathSegment
        
        return PathSegment(
            source_device=self.source_device,
            dest_device=self.dest_device,
            source_interface=self.source_interface,
            dest_interface=self.dest_interface,
            segment_type=self.segment_type,
            connection_type=self.connection_type,
            discovered_at=self.discovered_at,
            confidence_score=self.confidence_score
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'source_device': self.source_device,
            'dest_device': self.dest_device,
            'source_interface': self.source_interface,
            'dest_interface': self.dest_interface,
            'segment_type': self.segment_type,
            'connection_type': self.connection_type,
            'bandwidth': self.bandwidth,
            'latency': self.latency,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confidence_score': self.confidence_score
        }


# Legacy compatibility - keep these for now but they're deprecated
class Phase1Destination(Base):
    """
    DEPRECATED: Phase 1 Destination model.
    Replaced by destinations JSON field in Phase1BridgeDomainConfig.
    Keeping for backward compatibility during migration.
    """
    
    __tablename__ = 'phase1_destinations'
    
    id = Column(Integer, primary_key=True)
    bridge_domain_config_id = Column(Integer, ForeignKey('phase1_bridge_domain_config.id'), nullable=False)
    device = Column(String(255), nullable=False)
    port = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __init__(self, device: str, port: str, bridge_domain_config_id: int):
        self.device = device
        self.port = port
        self.bridge_domain_config_id = bridge_domain_config_id
        self.created_at = datetime.utcnow()


class Phase1Configuration(Base):
    """
    DEPRECATED: Phase 1 Configuration model.
    Keeping for backward compatibility during migration.
    """
    
    __tablename__ = 'phase1_configurations'
    
    id = Column(Integer, primary_key=True)
    legacy_config_id = Column(Integer, nullable=False)
    topology_id = Column(Integer, ForeignKey('phase1_topology_data.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __init__(self, legacy_config_id: int, topology_id: int):
        self.legacy_config_id = legacy_config_id
        self.topology_id = topology_id
        self.created_at = datetime.utcnow()
