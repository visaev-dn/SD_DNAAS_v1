#!/usr/bin/env python3
"""
Phase 1 API Endpoints
Comprehensive REST API endpoints for Phase 1 data structures
"""

import logging
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def create_topology_endpoints(blueprint: Blueprint, db_manager=None):
    """Create topology-related API endpoints"""
    
    @blueprint.route('/topologies', methods=['GET'])
    def list_topologies():
        """List all Phase 1 topologies"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get query parameters
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            search = request.args.get('search', '')
            
            if search:
                topologies = db_manager.search_topologies(search, limit)
            else:
                # Get all topologies with pagination
                topologies = db_manager.get_all_topologies(limit=limit, offset=offset)
            
            return jsonify({
                'success': True,
                'topologies': topologies,
                'total': len(topologies),
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to list topologies: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/topologies/<int:topology_id>', methods=['GET'])
    def get_topology(topology_id: int):
        """Get specific Phase 1 topology by ID"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            topology = db_manager.get_topology_data(topology_id)
            if not topology:
                return jsonify({'error': 'Topology not found'}), 404
            
            return jsonify({
                'success': True,
                'topology': topology
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get topology {topology_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/topologies', methods=['POST'])
    def create_topology():
        """Create new Phase 1 topology"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Convert to TopologyData object
            from config_engine.phase1_data_structures import TopologyData
            topology_data = TopologyData.from_dict(data)
            
            # Save to database
            topology_id = db_manager.save_topology_data(topology_data)
            
            if topology_id:
                return jsonify({
                    'success': True,
                    'topology_id': topology_id,
                    'message': 'Topology created successfully'
                }), 201
            else:
                return jsonify({'error': 'Failed to create topology'}), 500
                
        except Exception as e:
            logger.error(f"❌ Failed to create topology: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/topologies/<int:topology_id>', methods=['PUT'])
    def update_topology(topology_id: int):
        """Update existing Phase 1 topology"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Get existing topology
            existing = db_manager.get_topology_data(topology_id)
            if not existing:
                return jsonify({'error': 'Topology not found'}), 404
            
            # Convert to TopologyData object
            from config_engine.phase1_data_structures import TopologyData
            topology_data = TopologyData.from_dict(data)
            
            # Delete old and create new (since TopologyData is immutable)
            db_manager.delete_topology_data(topology_id)
            new_id = db_manager.save_topology_data(topology_data)
            
            return jsonify({
                'success': True,
                'topology_id': new_id,
                'message': 'Topology updated successfully'
            })
                
        except Exception as e:
            logger.error(f"❌ Failed to update topology {topology_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/topologies/<int:topology_id>', methods=['DELETE'])
    def delete_topology(topology_id: int):
        """Delete Phase 1 topology"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            success = db_manager.delete_topology_data(topology_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Topology deleted successfully'
                })
            else:
                return jsonify({'error': 'Failed to delete topology'}), 500
                
        except Exception as e:
            logger.error(f"❌ Failed to delete topology {topology_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/topologies/search', methods=['GET'])
    def search_topologies():
        """Search Phase 1 topologies"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            search_term = request.args.get('q', '')
            limit = request.args.get('limit', 50, type=int)
            
            if not search_term:
                return jsonify({'error': 'Search term required'}), 400
            
            results = db_manager.search_topologies(search_term, limit)
            
            return jsonify({
                'success': True,
                'results': results,
                'total': len(results),
                'search_term': search_term
            })
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return jsonify({'error': str(e)}), 500


def create_device_endpoints(blueprint: Blueprint, db_manager=None):
    """Create device-related API endpoints"""
    
    @blueprint.route('/devices', methods=['GET'])
    def list_devices():
        """List all devices across all topologies"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get all topologies and extract devices
            topologies = db_manager.get_all_topologies(limit=1000)
            all_devices = []
            
            for topology in topologies:
                if hasattr(topology, 'devices'):
                    all_devices.extend(topology.devices)
            
            return jsonify({
                'success': True,
                'devices': all_devices,
                'total': len(all_devices)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to list devices: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/devices/<device_name>', methods=['GET'])
    def get_device(device_name: str):
        """Get device information by name"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Search for device across topologies
            topologies = db_manager.search_topologies(device_name, limit=100)
            device_info = None
            
            for topology in topologies:
                if hasattr(topology, 'devices'):
                    for device in topology.devices:
                        if device.name == device_name:
                            device_info = device
                            break
                    if device_info:
                        break
            
            if not device_info:
                return jsonify({'error': 'Device not found'}), 404
            
            return jsonify({
                'success': True,
                'device': device_info
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get device {device_name}: {e}")
            return jsonify({'error': str(e)}), 500


def create_interface_endpoints(blueprint: Blueprint, db_manager=None):
    """Create interface-related API endpoints"""
    
    @blueprint.route('/interfaces', methods=['GET'])
    def list_interfaces():
        """List all interfaces across all topologies"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get all topologies and extract interfaces
            topologies = db_manager.get_all_topologies(limit=1000)
            all_interfaces = []
            
            for topology in topologies:
                if hasattr(topology, 'interfaces'):
                    all_interfaces.extend(topology.interfaces)
            
            return jsonify({
                'success': True,
                'interfaces': all_interfaces,
                'total': len(all_interfaces)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to list interfaces: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/interfaces/<device_name>', methods=['GET'])
    def get_device_interfaces(device_name: str):
        """Get all interfaces for a specific device"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Search for device and get its interfaces
            topologies = db_manager.search_topologies(device_name, limit=100)
            device_interfaces = []
            
            for topology in topologies:
                if hasattr(topology, 'devices'):
                    for device in topology.devices:
                        if device.name == device_name:
                            # Get interfaces for this device
                            if hasattr(topology, 'interfaces'):
                                for interface in topology.interfaces:
                                    if interface.device_name == device_name:
                                        device_interfaces.append(interface)
                            break
            
            return jsonify({
                'success': True,
                'device': device_name,
                'interfaces': device_interfaces,
                'total': len(device_interfaces)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get interfaces for device {device_name}: {e}")
            return jsonify({'error': str(e)}), 500


def create_path_endpoints(blueprint: Blueprint, db_manager=None):
    """Create path-related API endpoints"""
    
    @blueprint.route('/paths', methods=['GET'])
    def list_paths():
        """List all paths across all topologies"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get all topologies and extract paths
            topologies = db_manager.get_all_topologies(limit=1000)
            all_paths = []
            
            for topology in topologies:
                if hasattr(topology, 'paths'):
                    all_paths.extend(topology.paths)
            
            return jsonify({
                'success': True,
                'paths': all_paths,
                'total': len(all_paths)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to list paths: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/paths/<path_name>', methods=['GET'])
    def get_path(path_name: str):
        """Get specific path by name"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Search for path across topologies
            topologies = db_manager.search_topologies(path_name, limit=100)
            path_info = None
            
            for topology in topologies:
                if hasattr(topology, 'paths'):
                    for path in topology.paths:
                        if path.path_name == path_name:
                            path_info = path
                            break
                    if path_info:
                        break
            
            if not path_info:
                return jsonify({'error': 'Path not found'}), 404
            
            return jsonify({
                'success': True,
                'path': path_info
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get path {path_name}: {e}")
            return jsonify({'error': str(e)}), 500


def create_bridge_domain_endpoints(blueprint: Blueprint, db_manager=None):
    """Create bridge domain configuration endpoints"""
    
    @blueprint.route('/bridge-domains', methods=['GET'])
    def list_bridge_domains():
        """List all bridge domain configurations"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get all topologies and extract bridge domain configs
            topologies = db_manager.get_all_topologies(limit=1000)
            bridge_domains = []
            
            for topology in topologies:
                if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
                    bridge_domains.append({
                        'topology_id': topology.id,
                        'bridge_domain_name': topology.bridge_domain_name,
                        'config': topology.bridge_domain_config
                    })
            
            return jsonify({
                'success': True,
                'bridge_domains': bridge_domains,
                'total': len(bridge_domains)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to list bridge domains: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/bridge-domains/<bridge_domain_name>', methods=['GET'])
    def get_bridge_domain(bridge_domain_name: str):
        """Get bridge domain configuration by name"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Search for bridge domain
            topologies = db_manager.search_topologies(bridge_domain_name, limit=100)
            bridge_domain_info = None
            
            for topology in topologies:
                if topology.bridge_domain_name == bridge_domain_name:
                    bridge_domain_info = {
                        'topology_id': topology.id,
                        'bridge_domain_name': topology.bridge_domain_name,
                        'config': topology.bridge_domain_config,
                        'topology': topology
                    }
                    break
            
            if not bridge_domain_info:
                return jsonify({'error': 'Bridge domain not found'}), 404
            
            return jsonify({
                'success': True,
                'bridge_domain': bridge_domain_info
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get bridge domain {bridge_domain_name}: {e}")
            return jsonify({'error': str(e)}), 500


def create_migration_endpoints(blueprint: Blueprint, db_manager=None):
    """Create migration-related API endpoints"""
    
    @blueprint.route('/migrate/test', methods=['GET'])
    def test_migration_endpoint():
        """Simple test endpoint"""
        return jsonify({
            'success': True,
            'message': 'Migration endpoint working',
            'timestamp': datetime.now().isoformat()
        })
    
    @blueprint.route('/migrate/status', methods=['GET'])
    def get_migration_status():
        """Get migration status and statistics"""
        try:
            # Try to get database manager from current app context
            from flask import current_app
            current_db_manager = None
            
            # First try the passed db_manager
            if db_manager:
                current_db_manager = db_manager
            else:
                # Try to get from app context
                try:
                    if hasattr(current_app, 'phase1_db_manager'):
                        current_db_manager = current_app.phase1_db_manager
                except:
                    pass
            
            if not current_db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Get database info for migration status
            db_info = current_db_manager.get_database_info()
            
            # Ensure all values are JSON serializable
            phase1_tables = db_info.get('phase1_tables', [])
            total_records = db_info.get('total_phase1_records', 0)
            database_size = db_info.get('database_size', 0)
            
            # Convert to basic types if needed
            if isinstance(phase1_tables, (list, tuple)):
                phase1_tables = list(phase1_tables)
            else:
                phase1_tables = []
            
            if not isinstance(total_records, (int, float)):
                total_records = 0
                
            if not isinstance(database_size, (int, float)):
                database_size = 0
            
            return jsonify({
                'success': True,
                'migration_status': {
                    'phase1_tables': phase1_tables,
                    'total_records': total_records,
                    'database_size': database_size,
                    'status': 'ready' if phase1_tables else 'not_initialized'
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get migration status: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/migrate/legacy', methods=['POST'])
    def migrate_legacy_data():
        """Migrate legacy configurations to Phase 1 format"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # This would require access to legacy database models
            # For now, return a placeholder response
            return jsonify({
                'success': True,
                'message': 'Migration endpoint ready - requires legacy database access',
                'status': 'pending_implementation'
            })
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return jsonify({'error': str(e)}), 500


def create_export_endpoints(blueprint: Blueprint, db_manager=None):
    """Create export/import API endpoints"""
    
    @blueprint.route('/export/<int:topology_id>', methods=['GET'])
    def export_topology(topology_id: int):
        """Export topology data in specified format"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            format_type = request.args.get('format', 'json')
            
            if format_type not in ['json', 'yaml']:
                return jsonify({'error': 'Unsupported format'}), 400
            
            # Get topology data
            topology = db_manager.get_topology_data(topology_id)
            if not topology:
                return jsonify({'error': 'Topology not found'}), 404
            
            # Export in specified format
            if format_type == 'json':
                from config_engine.phase1_database.serializers import Phase1DataSerializer
                serializer = Phase1DataSerializer()
                exported_data = serializer.serialize_topology(topology, 'json')
                return jsonify({
                    'success': True,
                    'format': 'json',
                    'data': exported_data,
                    'size': len(exported_data)
                })
            else:
                # YAML export
                from config_engine.phase1_database.serializers import Phase1DataSerializer
                serializer = Phase1DataSerializer()
                exported_data = serializer.serialize_topology(topology, 'yaml')
                return jsonify({
                    'success': True,
                    'format': 'yaml',
                    'data': exported_data,
                    'size': len(exported_data)
                })
                
        except Exception as e:
            logger.error(f"❌ Export failed for topology {topology_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/import', methods=['POST'])
    def import_topology():
        """Import topology data from file or data"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database manager not available'}), 500
            
            # Check if file was uploaded
            if 'file' in request.files:
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                # Read file content
                content = file.read().decode('utf-8')
                format_type = 'json' if file.filename.endswith('.json') else 'yaml'
                
            else:
                # Check for JSON data in request body
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                content = json.dumps(data)
                format_type = 'json'
            
            # Import using serializer
            from config_engine.phase1_database.serializers import Phase1DataSerializer
            serializer = Phase1DataSerializer()
            
            topology_data = serializer.deserialize_topology(content, format_type)
            if not topology_data:
                return jsonify({'error': 'Failed to deserialize data'}), 400
            
            # Save to database
            topology_id = db_manager.save_topology_data(topology_data)
            
            return jsonify({
                'success': True,
                'topology_id': topology_id,
                'message': 'Topology imported successfully'
            }), 201
                
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return jsonify({'error': str(e)}), 500
