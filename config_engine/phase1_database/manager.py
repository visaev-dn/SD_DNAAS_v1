#!/usr/bin/env python3
"""
Phase 1 Database Manager - Optimized Version
Enhanced manager with support for consolidated configuration, path groups, 
VLAN centralization, and confidence metrics.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker, Session

# Import Phase 1 models and data structures
from .models import (
    Base, Phase1TopologyData, Phase1DeviceInfo, Phase1InterfaceInfo,
    Phase1PathInfo, Phase1PathSegment, Phase1BridgeDomainConfig, 
    Phase1Destination, Phase1Configuration, Phase1PathGroup, Phase1VlanConfig, Phase1ConfidenceMetrics
)
from config_engine.phase1_data_structures import TopologyData

logger = logging.getLogger(__name__)


class Phase1DatabaseManager:
    """
    Phase 1 Database Manager for handling Phase 1 data structures.
    
    This manager provides:
    1. Storage and retrieval of Phase 1 topology data
    2. Support for optimized data structure (consolidated configs, path groups, VLAN centralization)
    3. Backward compatibility with existing configurations
    4. Advanced querying capabilities
    """
    
    def __init__(self, db_path: str = 'instance/lab_automation.db'):
        """Initialize Phase 1 database manager"""
        self.db_path = db_path
        self.logger = logger
        
        # Initialize SQLAlchemy engine
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create Phase 1 tables if they don't exist
        self._create_phase1_tables()
        
        self.logger.info(f"🚀 Phase 1 Database Manager initialized for {db_path}")
    
    def _create_phase1_tables(self) -> None:
        """Create Phase 1 database tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("✅ Phase 1 database tables created/verified")
        except Exception as e:
            self.logger.error(f"❌ Failed to create Phase 1 tables: {e}")
            raise
    
    def save_topology_data(self, topology_data: TopologyData, 
                          legacy_config_id: Optional[int] = None) -> Optional[int]:
        """
        Save Phase 1 topology data to database with optimized structure.
        
        Args:
            topology_data: Phase 1 TopologyData object
            legacy_config_id: Optional legacy configuration ID for linking
            
        Returns:
            Topology data ID if successful, None otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Check if topology already exists (upsert logic)
            existing_topology = session.query(Phase1TopologyData).filter(
                Phase1TopologyData.bridge_domain_name == topology_data.bridge_domain_name
            ).first()
            
            if existing_topology:
                # Update existing topology
                existing_topology.topology_type = topology_data.topology_type.value
                existing_topology.vlan_id = topology_data.vlan_id
                existing_topology.discovered_at = topology_data.discovered_at
                existing_topology.scan_method = getattr(topology_data, 'scan_method', 'unknown')
                existing_topology.confidence_score = topology_data.confidence_score
                existing_topology.validation_status = topology_data.validation_status.value
                existing_topology.device_count = len(topology_data.devices)
                existing_topology.interface_count = len(topology_data.interfaces)
                existing_topology.path_count = len(topology_data.paths)
                existing_topology.updated_at = datetime.utcnow()
                existing_topology.change_count += 1
                
                phase1_topology = existing_topology
                topology_id = existing_topology.id
                
                # Update bridge domain config (relationship handling)
                if hasattr(topology_data, 'bridge_domain_config') and topology_data.bridge_domain_config:
                    self._update_bridge_domain_config(session, topology_id, topology_data.bridge_domain_config)
                
                self.logger.info(f"📝 Updated existing topology: {topology_data.bridge_domain_name} (ID: {topology_id})")
            else:
                # Create new Phase 1 topology data
                phase1_topology = Phase1TopologyData(topology_data, legacy_config_id)
                session.add(phase1_topology)
                session.flush()  # Get the ID
                topology_id = phase1_topology.id
                
                self.logger.info(f"✨ Created new topology: {topology_data.bridge_domain_name} (ID: {topology_id})")
            
            topology_id = phase1_topology.id
            
            # Create device information
            for device_info in topology_data.devices:
                phase1_device = Phase1DeviceInfo(device_info, topology_id)
                session.add(phase1_device)
                session.flush()
                
                # Create interface information for this device
                device_interfaces = [i for i in topology_data.interfaces if i.device_name == device_info.name]
                for interface_info in device_interfaces:
                    phase1_interface = Phase1InterfaceInfo(interface_info, topology_id, phase1_device.id)
                    session.add(phase1_interface)
            
            # Create bridge domain configuration with consolidated destinations
            if hasattr(topology_data, 'bridge_domain_config') and topology_data.bridge_domain_config:
                config = topology_data.bridge_domain_config
                phase1_config = Phase1BridgeDomainConfig(config, topology_id)
                
                # Add destinations to the consolidated JSON field
                if hasattr(config, 'destinations') and config.destinations:
                    for dest in config.destinations:
                        if isinstance(dest, dict):
                            device = dest.get('device', '')
                            port = dest.get('port', '')
                            vlan_id = dest.get('vlan_id')
                        else:
                            device = getattr(dest, 'device', '')
                            port = getattr(dest, 'port', '')
                            vlan_id = getattr(dest, 'vlan_id', None)
                        
                        phase1_config.add_destination(device, port, vlan_id)
                
                session.add(phase1_config)
                session.flush()
                
                # Create VLAN configuration
                if config.vlan_id:
                    vlan_config = Phase1VlanConfig(phase1_config.id, config.vlan_id, 'single')
                    session.add(vlan_config)
                
                # Create path groups from paths
                self._create_path_groups(session, phase1_config.id, topology_data.paths)
                
                # Create confidence metrics
                confidence_metrics = Phase1ConfidenceMetrics(phase1_config.id)
                self._calculate_confidence_scores(confidence_metrics, topology_data)
                session.add(confidence_metrics)
            
            # Create path information
            for path_info in topology_data.paths:
                phase1_path = Phase1PathInfo(path_info, topology_id)
                session.add(phase1_path)
                session.flush()
                
                # Create path segments
                for segment in path_info.segments:
                    phase1_segment = Phase1PathSegment(segment, phase1_path.id)
                    session.add(phase1_segment)
            
            session.commit()
            
            self.logger.info(f"✅ Phase 1 topology data saved successfully with ID: {topology_id}")
            return topology_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save Phase 1 topology data: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def _create_path_groups(self, session: Session, config_id: int, paths: List) -> None:
        """Create path groups by consolidating paths between same source-destination pairs"""
        try:
            # Group paths by source-destination device pairs
            path_groups = {}
            
            for path in paths:
                key = (path.source_device, path.dest_device)
                if key not in path_groups:
                    path_groups[key] = []
                path_groups[key].append(path)
            
            # Create path group records
            for (source, dest), path_list in path_groups.items():
                path_group = Phase1PathGroup(config_id, source, dest)
                path_group.path_count = len(path_list)
                
                # Set primary path (first one) and backup paths
                if path_list:
                    # Note: We'll need to link this to actual path IDs later
                    # For now, just store the count
                    path_group.load_balancing_type = 'active-active' if len(path_list) > 1 else 'none'
                    path_group.redundancy_level = 'n+1' if len(path_list) > 1 else 'none'
                
                session.add(path_group)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create path groups: {e}")
            raise
    
    def _calculate_confidence_scores(self, confidence_metrics: Phase1ConfidenceMetrics, topology_data: TopologyData) -> None:
        """Calculate weighted confidence scores for different components"""
        try:
            # Device confidence
            if topology_data.devices:
                device_scores = [d.confidence_score for d in topology_data.devices]
                confidence_metrics.device_confidence = sum(device_scores) / len(device_scores)
                confidence_metrics.add_confidence_factor('devices', confidence_metrics.device_confidence, 
                                                      f"Average of {len(device_scores)} devices")
            
            # Interface confidence
            if topology_data.interfaces:
                interface_scores = [i.confidence_score for i in topology_data.interfaces]
                confidence_metrics.interface_confidence = sum(interface_scores) / len(interface_scores)
                confidence_metrics.add_confidence_factor('interfaces', confidence_metrics.interface_confidence,
                                                      f"Average of {len(interface_scores)} interfaces")
            
            # Path confidence
            if topology_data.paths:
                path_scores = [p.confidence_score for p in topology_data.paths]
                confidence_metrics.path_confidence = sum(path_scores) / len(path_scores)
                confidence_metrics.add_confidence_factor('paths', confidence_metrics.path_confidence,
                                                      f"Average of {len(path_scores)} paths")
            
            # VLAN confidence (if available)
            if topology_data.vlan_id:
                confidence_metrics.vlan_confidence = 1.0  # VLAN ID is known
                confidence_metrics.add_confidence_factor('vlan', 1.0, "VLAN ID confirmed")
            else:
                confidence_metrics.vlan_confidence = 0.0
                confidence_metrics.add_confidence_factor('vlan', 0.0, "VLAN ID missing")
            
            # Calculate overall confidence
            confidence_metrics.calculate_overall_confidence()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate confidence scores: {e}")
            raise
    
    def get_topology_data(self, topology_id: int) -> Optional[TopologyData]:
        """
        Retrieve Phase 1 topology data by ID.
        
        Args:
            topology_id: ID of the topology data
            
        Returns:
            TopologyData object if found, None otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Query topology data
            phase1_topology = session.query(Phase1TopologyData).filter(
                Phase1TopologyData.id == topology_id
            ).first()
            
            if not phase1_topology:
                self.logger.warning(f"⚠️ Topology data not found for ID: {topology_id}")
                return None
            
            # Convert back to Phase 1 TopologyData object
            topology_data = phase1_topology.to_phase1_topology()
            
            self.logger.info(f"✅ Phase 1 topology data retrieved for ID: {topology_id}")
            return topology_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve Phase 1 topology data: {e}")
            return None
        finally:
            session.close()

    def _update_bridge_domain_config(self, session, topology_id: int, bridge_domain_config):
        """Update bridge domain configuration for existing topology"""
        try:
            # Get existing bridge domain config
            existing_config = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.topology_id == topology_id
            ).first()
            
            if existing_config:
                # Update existing config
                existing_config.service_name = bridge_domain_config.service_name
                existing_config.bridge_domain_type = bridge_domain_config.bridge_domain_type.value
                existing_config.source_device = bridge_domain_config.source_device
                existing_config.source_interface = bridge_domain_config.source_interface
                existing_config.vlan_id = bridge_domain_config.vlan_id
                existing_config.outer_vlan = bridge_domain_config.outer_vlan
                existing_config.inner_vlan = bridge_domain_config.inner_vlan
                existing_config.bridge_domain_scope = bridge_domain_config.bridge_domain_scope.value
                existing_config.outer_tag_imposition = bridge_domain_config.outer_tag_imposition.value
                existing_config.confidence_score = bridge_domain_config.confidence_score
                existing_config.validation_status = bridge_domain_config.validation_status.value
                existing_config.updated_at = datetime.utcnow()
                
                # Update destinations JSON field
                destinations_json = [
                    {'device': dest['device'], 'port': dest['port']} 
                    for dest in bridge_domain_config.destinations
                ]
                existing_config.destinations = json.dumps(destinations_json)
                
                self.logger.debug(f"Updated bridge domain config for topology {topology_id}")
            else:
                # Create new config if none exists
                phase1_config = Phase1BridgeDomainConfig(bridge_domain_config, topology_id)
                session.add(phase1_config)
                self.logger.debug(f"Created new bridge domain config for topology {topology_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update bridge domain config for topology {topology_id}: {e}")
    
    def get_all_topologies(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[TopologyData]:
        """
        Retrieve all Phase 1 topology data with optional pagination.
        
        Args:
            limit: Maximum number of topologies to return
            offset: Number of topologies to skip
            
        Returns:
            List of TopologyData objects
        """
        try:
            session = self.SessionLocal()
            
            # Build query
            query = session.query(Phase1TopologyData)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            # Execute query
            phase1_topologies = query.all()
            
            # Convert to Phase 1 TopologyData objects
            topology_data_list = []
            for phase1_topology in phase1_topologies:
                try:
                    topology_data = phase1_topology.to_phase1_topology()
                    topology_data_list.append(topology_data)
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to convert topology {phase1_topology.id}: {e}")
                    continue
            
            self.logger.info(f"✅ Retrieved {len(topology_data_list)} Phase 1 topologies")
            return topology_data_list
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve Phase 1 topologies: {e}")
            return []
        finally:
            session.close()
    
    def get_topology_by_bridge_domain(self, bridge_domain_name: str) -> Optional[TopologyData]:
        """
        Retrieve Phase 1 topology data by bridge domain name.
        
        Args:
            bridge_domain_name: Name of the bridge domain
            
        Returns:
            TopologyData object if found, None otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Query topology data by bridge domain name
            phase1_topology = session.query(Phase1TopologyData).filter(
                Phase1TopologyData.bridge_domain_name == bridge_domain_name
            ).first()
            
            if not phase1_topology:
                self.logger.warning(f"⚠️ Topology data not found for bridge domain: {bridge_domain_name}")
                return None
            
            # Convert back to Phase 1 TopologyData object
            topology_data = phase1_topology.to_phase1_topology()
            
            self.logger.info(f"✅ Phase 1 topology data retrieved for bridge domain: {bridge_domain_name}")
            return topology_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve Phase 1 topology data: {e}")
            return None
        finally:
            session.close()

    def get_devices_by_topology_id(self, topology_id: int) -> List[Phase1DeviceInfo]:
        """
        Retrieve all devices for a specific topology.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1DeviceInfo objects
        """
        try:
            session = self.SessionLocal()
            devices = session.query(Phase1DeviceInfo).filter(
                Phase1DeviceInfo.topology_id == topology_id
            ).all()
            return devices
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve devices for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    def get_interfaces_by_topology_id(self, topology_id: int) -> List[Phase1InterfaceInfo]:
        """
        Retrieve all interfaces for a specific topology.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1InterfaceInfo objects
        """
        try:
            session = self.SessionLocal()
            interfaces = session.query(Phase1InterfaceInfo).filter(
                Phase1InterfaceInfo.topology_id == topology_id
            ).all()
            return interfaces
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve interfaces for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    def get_bridge_domain_configs_by_topology_id(self, topology_id: int) -> List[Phase1BridgeDomainConfig]:
        """
        Retrieve all bridge domain configurations for a specific topology.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1BridgeDomainConfig objects
        """
        try:
            session = self.SessionLocal()
            configs = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.topology_id == topology_id
            ).all()
            return configs
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve bridge domain configs for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    def get_destinations_by_topology_id(self, topology_id: int) -> List[Phase1Destination]:
        """
        Retrieve all destinations for a specific topology.
        NOTE: This method is deprecated. Use get_bridge_domain_configs_by_topology_id() 
        and access the destinations JSON field instead.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1Destination objects (legacy)
        """
        try:
            session = self.SessionLocal()
            # Get destinations through bridge domain configs
            configs = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.topology_id == topology_id
            ).all()
            
            destinations = []
            for config in configs:
                dests = session.query(Phase1Destination).filter(
                    Phase1Destination.bridge_domain_config_id == config.id
                ).all()
                destinations.extend(dests)
            
            return destinations
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve destinations for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    def get_paths_by_topology_id(self, topology_id: int) -> List[Phase1PathInfo]:
        """
        Retrieve all paths for a specific topology.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1PathInfo objects
        """
        try:
            session = self.SessionLocal()
            paths = session.query(Phase1PathInfo).filter(
                Phase1PathInfo.topology_id == topology_id
            ).all()
            return paths
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve paths for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    def get_path_segments_by_topology_id(self, topology_id: int) -> List[Phase1PathSegment]:
        """
        Retrieve all path segments for a specific topology.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            List of Phase1PathSegment objects
        """
        try:
            session = self.SessionLocal()
            # Get path segments through paths
            paths = session.query(Phase1PathInfo).filter(
                Phase1PathInfo.topology_id == topology_id
            ).all()
            
            segments = []
            for path in paths:
                segs = session.query(Phase1PathSegment).filter(
                    Phase1PathSegment.path_id == path.id
                ).all()
                segments.extend(segs)
            
            return segments
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve path segments for topology {topology_id}: {e}")
            return []
        finally:
            session.close()

    # NEW METHODS FOR OPTIMIZED STRUCTURE

    def get_path_groups_by_config_id(self, config_id: int) -> List[Phase1PathGroup]:
        """
        Retrieve all path groups for a specific bridge domain configuration.
        
        Args:
            config_id: ID of the bridge domain configuration
            
        Returns:
            List of Phase1PathGroup objects
        """
        try:
            session = self.SessionLocal()
            path_groups = session.query(Phase1PathGroup).filter(
                Phase1PathGroup.config_id == config_id
            ).all()
            return path_groups
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve path groups for config {config_id}: {e}")
            return []
        finally:
            session.close()

    def get_vlan_config_by_config_id(self, config_id: int) -> List[Phase1VlanConfig]:
        """
        Retrieve VLAN configuration for a specific bridge domain configuration.
        
        Args:
            config_id: ID of the bridge domain configuration
            
        Returns:
            List of Phase1VlanConfig objects
        """
        try:
            session = self.SessionLocal()
            vlan_configs = session.query(Phase1VlanConfig).filter(
                Phase1VlanConfig.config_id == config_id
            ).all()
            return vlan_configs
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve VLAN configs for config {config_id}: {e}")
            return []
        finally:
            session.close()

    def get_confidence_metrics_by_config_id(self, config_id: int) -> Optional[Phase1ConfidenceMetrics]:
        """
        Retrieve confidence metrics for a specific bridge domain configuration.
        
        Args:
            config_id: ID of the bridge domain configuration
            
        Returns:
            Phase1ConfidenceMetrics object if found, None otherwise
        """
        try:
            session = self.SessionLocal()
            confidence_metrics = session.query(Phase1ConfidenceMetrics).filter(
                Phase1ConfidenceMetrics.config_id == config_id
            ).first()
            return confidence_metrics
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve confidence metrics for config {config_id}: {e}")
            return None
        finally:
            session.close()

    def update_confidence_scores(self, config_id: int) -> bool:
        """
        Update confidence scores for a specific bridge domain configuration.
        
        Args:
            config_id: ID of the bridge domain configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Get the configuration and related data
            config = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.id == config_id
            ).first()
            
            if not config:
                self.logger.error(f"❌ Bridge domain config not found for ID: {config_id}")
                return False
            
            # Get or create confidence metrics
            confidence_metrics = session.query(Phase1ConfidenceMetrics).filter(
                Phase1ConfidenceMetrics.config_id == config_id
            ).first()
            
            if not confidence_metrics:
                confidence_metrics = Phase1ConfidenceMetrics(config_id)
                session.add(confidence_metrics)
            
            # Calculate new confidence scores
            self._recalculate_confidence_scores(session, config_id, confidence_metrics)
            
            session.commit()
            self.logger.info(f"✅ Confidence scores updated for config {config_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update confidence scores: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def _recalculate_confidence_scores(self, session: Session, config_id: int, confidence_metrics: Phase1ConfidenceMetrics) -> None:
        """Recalculate confidence scores based on current data"""
        try:
            # Get related data
            devices = session.query(Phase1DeviceInfo).join(Phase1TopologyData).filter(
                Phase1TopologyData.id == Phase1BridgeDomainConfig.topology_id,
                Phase1BridgeDomainConfig.id == config_id
            ).all()
            
            interfaces = session.query(Phase1InterfaceInfo).join(Phase1TopologyData).filter(
                Phase1TopologyData.id == Phase1BridgeDomainConfig.topology_id,
                Phase1BridgeDomainConfig.id == config_id
            ).all()
            
            paths = session.query(Phase1PathInfo).join(Phase1TopologyData).filter(
                Phase1TopologyData.id == Phase1BridgeDomainConfig.topology_id,
                Phase1BridgeDomainConfig.id == config_id
            ).all()
            
            # Calculate component confidence scores
            if devices:
                device_scores = [d.confidence_score for d in devices]
                confidence_metrics.device_confidence = sum(device_scores) / len(device_scores)
            
            if interfaces:
                interface_scores = [i.confidence_score for i in interfaces]
                confidence_metrics.interface_confidence = sum(interface_scores) / len(interface_scores)
            
            if paths:
                path_scores = [p.confidence_score for p in paths]
                confidence_metrics.path_confidence = sum(path_scores) / len(path_scores)
            
            # VLAN confidence (if available)
            config = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.id == config_id
            ).first()
            confidence_metrics.vlan_confidence = 1.0 if config and config.vlan_id else 0.0
            
            # Calculate overall confidence
            confidence_metrics.calculate_overall_confidence()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to recalculate confidence scores: {e}")
            raise

    def consolidate_paths_into_groups(self, topology_id: int) -> bool:
        """
        Consolidate individual paths into logical path groups.
        
        Args:
            topology_id: ID of the topology
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Get all paths for the topology
            paths = session.query(Phase1PathInfo).filter(
                Phase1PathInfo.topology_id == topology_id
            ).all()
            
            # Get bridge domain config
            config = session.query(Phase1BridgeDomainConfig).filter(
                Phase1BridgeDomainConfig.topology_id == topology_id
            ).first()
            
            if not config:
                self.logger.error(f"❌ Bridge domain config not found for topology {topology_id}")
                return False
            
            # Group paths by source-destination pairs
            path_groups = {}
            for path in paths:
                key = (path.source_device, path.dest_device)
                if key not in path_groups:
                    path_groups[key] = []
                path_groups[key].append(path)
            
            # Create or update path groups
            for (source, dest), path_list in path_groups.items():
                # Check if path group already exists
                existing_group = session.query(Phase1PathGroup).filter(
                    Phase1PathGroup.config_id == config.id,
                    Phase1PathGroup.source_device == source,
                    Phase1PathGroup.destination_device == dest
                ).first()
                
                if existing_group:
                    # Update existing group
                    existing_group.path_count = len(path_list)
                    existing_group.load_balancing_type = 'active-active' if len(path_list) > 1 else 'none'
                    existing_group.redundancy_level = 'n+1' if len(path_list) > 1 else 'none'
                else:
                    # Create new group
                    path_group = Phase1PathGroup(config.id, source, dest)
                    path_group.path_count = len(path_list)
                    path_group.load_balancing_type = 'active-active' if len(path_list) > 1 else 'none'
                    path_group.redundancy_level = 'n+1' if len(path_list) > 1 else 'none'
                    session.add(path_group)
            
            session.commit()
            self.logger.info(f"✅ Paths consolidated into groups for topology {topology_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to consolidate paths: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def link_to_legacy_config(self, topology_id: int, legacy_config_id: int) -> bool:
        """
        Link Phase 1 topology data to legacy configuration.
        
        Args:
            topology_id: Phase 1 topology data ID
            legacy_config_id: Legacy configuration ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.SessionLocal()
            
            # Update topology data
            topology = session.query(Phase1TopologyData).filter(
                Phase1TopologyData.id == topology_id
            ).first()
            
            if not topology:
                self.logger.error(f"❌ Topology data not found for ID: {topology_id}")
                return False
            
            topology.legacy_config_id = legacy_config_id
            
            # Create Phase 1 configuration link
            phase1_config = Phase1Configuration(legacy_config_id, topology_id)
            session.add(phase1_config)
            
            session.commit()
            
            self.logger.info(f"✅ Phase 1 topology {topology_id} linked to legacy config {legacy_config_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to link to legacy config: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_phase1_configurations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of Phase 1 configurations.
        
        Args:
            limit: Maximum number of configurations to return
            
        Returns:
            List of Phase 1 configuration dictionaries
        """
        try:
            session = self.SessionLocal()
            
            # Query Phase 1 configurations with related data
            phase1_configs = session.query(Phase1Configuration).limit(limit).all()
            
            result = []
            for config in phase1_configs:
                config_dict = {
                    'id': config.id,
                    'legacy_config_id': config.legacy_config_id,
                    'topology_id': config.topology_id,
                    'created_at': config.created_at.isoformat() if config.created_at else None
                }
                result.append(config_dict)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get Phase 1 configurations: {e}")
            return []
        finally:
            session.close()
    
    def get_topology_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about Phase 1 topology data.
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            session = self.SessionLocal()
            
            # Basic counts
            total_topologies = session.query(Phase1TopologyData).count()
            total_devices = session.query(Phase1DeviceInfo).count()
            total_interfaces = session.query(Phase1InterfaceInfo).count()
            total_paths = session.query(Phase1PathInfo).count()
            
            # Topology type distribution
            topology_types = session.query(
                Phase1TopologyData.topology_type,
                session.func.count(Phase1TopologyData.id)
            ).group_by(Phase1TopologyData.topology_type).all()
            
            # Validation status distribution
            validation_statuses = session.query(
                Phase1TopologyData.validation_status,
                session.func.count(Phase1TopologyData.id)
            ).group_by(Phase1TopologyData.validation_status).all()
            
            # Device type distribution
            device_types = session.query(
                Phase1DeviceInfo.device_type,
                session.func.count(Phase1DeviceInfo.id)
            ).group_by(Phase1DeviceInfo.device_type).all()
            
            # Interface type distribution
            interface_types = session.query(
                Phase1InterfaceInfo.interface_type,
                session.func.count(Phase1InterfaceInfo.id)
            ).group_by(Phase1InterfaceInfo.interface_type).all()
            
            # Confidence score ranges
            confidence_ranges = {
                'high': session.query(Phase1TopologyData).filter(Phase1TopologyData.confidence_score >= 0.8).count(),
                'medium': session.query(Phase1TopologyData).filter(
                    Phase1TopologyData.confidence_score >= 0.5,
                    Phase1TopologyData.confidence_score < 0.8
                ).count(),
                'low': session.query(Phase1TopologyData).filter(Phase1TopologyData.confidence_score < 0.5).count()
            }
            
            stats = {
                'total_topologies': total_topologies,
                'total_devices': total_devices,
                'total_interfaces': total_interfaces,
                'total_paths': total_paths,
                'topology_types': dict(topology_types),
                'validation_statuses': dict(validation_statuses),
                'device_types': dict(device_types),
                'interface_types': dict(interface_types),
                'confidence_ranges': confidence_ranges,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get topology statistics: {e}")
            return {}
        finally:
            session.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and health status.
        
        Returns:
            Dictionary containing database information
        """
        try:
            session = self.SessionLocal()
            
            # Table sizes
            table_sizes = {}
            tables = ['phase1_topology_data', 'phase1_device_info', 'phase1_interface_info', 
                     'phase1_bridge_domain_config', 'phase1_path_info', 'phase1_path_segments',
                     'phase1_path_groups', 'phase1_vlan_configs', 'phase1_confidence_metrics']
            
            for table in tables:
                try:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_sizes[table] = count
                except Exception:
                    table_sizes[table] = 0
            
            # Database file size
            db_path = Path(self.db_path)
            file_size = db_path.stat().st_size if db_path.exists() else 0
            
            # Last update
            last_update = session.query(Phase1TopologyData.updated_at).order_by(
                Phase1TopologyData.updated_at.desc()
            ).first()
            
            info = {
                'database_path': str(self.db_path),
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'table_sizes': table_sizes,
                'last_update': last_update[0].isoformat() if last_update and last_update[0] else None,
                'total_records': sum(table_sizes.values()),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get database info: {e}")
            return {}
        finally:
            session.close()

    def search_topologies(self, search_term: str, limit: int = 50) -> List:
        """Search topologies by bridge domain name with fuzzy matching"""
        try:
            with self.SessionLocal() as session:
                search_term_lower = search_term.lower()
                
                # Multiple search strategies for better matching
                queries = []
                
                # 1. Exact match (highest priority)
                exact_query = session.query(Phase1TopologyData).filter(
                    Phase1TopologyData.bridge_domain_name == search_term
                )
                
                # 2. Case-insensitive exact match
                case_insensitive_query = session.query(Phase1TopologyData).filter(
                    Phase1TopologyData.bridge_domain_name.ilike(search_term)
                )
                
                # 3. Contains match (case-insensitive) with eager loading
                from sqlalchemy.orm import joinedload
                contains_query = session.query(Phase1TopologyData).options(
                    joinedload(Phase1TopologyData.devices)
                ).filter(
                    Phase1TopologyData.bridge_domain_name.ilike(f'%{search_term}%')
                )
                
                # 4. Starts with match
                starts_with_query = session.query(Phase1TopologyData).filter(
                    Phase1TopologyData.bridge_domain_name.ilike(f'{search_term}%')
                )
                
                # 5. Word boundary match (for partial words)
                word_parts = search_term_lower.split('_')
                if len(word_parts) > 1:
                    # Search for each part
                    for part in word_parts:
                        if len(part) >= 3:  # Only search meaningful parts
                            part_query = session.query(Phase1TopologyData).filter(
                                Phase1TopologyData.bridge_domain_name.ilike(f'%{part}%')
                            )
                            queries.append(part_query)
                
                # Combine all queries and remove duplicates by ID
                seen_ids = set()
                all_results = []
                
                # Add exact matches first (highest priority)
                for topology in exact_query.all():
                    if topology.id not in seen_ids:
                        all_results.append(topology)
                        seen_ids.add(topology.id)
                
                # Add case-insensitive exact matches
                for topology in case_insensitive_query.all():
                    if topology.id not in seen_ids:
                        all_results.append(topology)
                        seen_ids.add(topology.id)
                
                # Add starts-with matches
                for topology in starts_with_query.all():
                    if topology.id not in seen_ids:
                        all_results.append(topology)
                        seen_ids.add(topology.id)
                
                # Add contains matches
                for topology in contains_query.all():
                    if topology.id not in seen_ids:
                        all_results.append(topology)
                        seen_ids.add(topology.id)
                
                # Add partial word matches
                for query in queries:
                    for topology in query.all():
                        if topology.id not in seen_ids:
                            all_results.append(topology)
                            seen_ids.add(topology.id)
                
                # Results are already sorted by relevance due to order of addition
                if limit and len(all_results) > limit:
                    all_results = all_results[:limit]
                
                # Convert to simple objects that don't require session
                class SearchResult:
                    def __init__(self, topology):
                        self.id = topology.id
                        self.bridge_domain_name = topology.bridge_domain_name
                        self.topology_type = topology.topology_type
                        self.devices = []  # Simplified for search results
                        self.created_at = topology.created_at
                
                results = [SearchResult(topology) for topology in all_results]
                return results
                
        except Exception as e:
            self.logger.error(f"❌ Failed to search topologies for '{search_term}': {e}")
            return []
