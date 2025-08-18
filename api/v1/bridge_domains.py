#!/usr/bin/env python3
"""
Bridge Domain Routes
Handles bridge domain discovery, listing, and visualization
"""

from flask import request, jsonify
import logging
from datetime import datetime

from api.v1 import api_v1
from models import db, TopologyScan, PersonalBridgeDomain
from auth import token_required, user_ownership_required
from config_engine.enhanced_topology_scanner import EnhancedTopologyScanner

logger = logging.getLogger(__name__)


@api_v1.route('/bridge-domains/discover', methods=['POST'])
@token_required
def discover_bridge_domains(current_user):
    """Discover bridge domains in the network"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        bridge_domain_name = data.get('bridge_domain_name')
        if not bridge_domain_name:
            return jsonify({'error': 'Bridge domain name is required'}), 400
        
        # Create topology scanner
        scanner = EnhancedTopologyScanner()
        
        # Run discovery
        discovery_result = scanner.discover_bridge_domain(bridge_domain_name)
        
        if not discovery_result:
            return jsonify({'error': 'Failed to discover bridge domain'}), 500
        
        # Save scan result
        scan = TopologyScan(
            user_id=current_user.id,
            scan_type='bridge_domain_discovery',
            target=bridge_domain_name,
            result=discovery_result,
            created_at=datetime.utcnow()
        )
        
        db.session.add(scan)
        db.session.commit()
        
        logger.info(f"Bridge domain discovery completed for {bridge_domain_name} by user {current_user.username}")
        
        return jsonify({
            'message': 'Bridge domain discovery completed',
            'scan_id': scan.id,
            'result': discovery_result
        }), 200
        
    except Exception as e:
        logger.error(f"Bridge domain discovery error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Discovery failed'}), 500


@api_v1.route('/bridge-domains/list', methods=['GET'])
@token_required
def list_bridge_domains(current_user):
    """List all bridge domains for the current user"""
    try:
        # Get user's personal bridge domains
        personal_domains = PersonalBridgeDomain.query.filter_by(user_id=current_user.id).all()
        
        # Get user's topology scans
        scans = TopologyScan.query.filter_by(
            user_id=current_user.id,
            scan_type='bridge_domain_discovery'
        ).order_by(TopologyScan.created_at.desc()).all()
        
        # Format response
        bridge_domains = []
        
        # Add personal bridge domains
        for domain in personal_domains:
            bridge_domains.append({
                'id': domain.id,
                'name': domain.bridge_domain_name,
                'vlan_id': domain.vlan_id,
                'type': 'personal',
                'created_at': domain.created_at.isoformat() if domain.created_at else None,
                'status': domain.status
            })
        
        # Add discovered bridge domains from scans
        for scan in scans:
            if scan.result and isinstance(scan.result, dict):
                # Extract bridge domain info from scan result
                scan_data = scan.result
                if 'bridge_domains' in scan_data:
                    for bd in scan_data['bridge_domains']:
                        bridge_domains.append({
                            'id': f"scan_{scan.id}_{bd.get('name', 'unknown')}",
                            'name': bd.get('name', 'Unknown'),
                            'vlan_id': bd.get('vlan_id'),
                            'type': 'discovered',
                            'created_at': scan.created_at.isoformat() if scan.created_at else None,
                            'status': 'active',
                            'scan_id': scan.id
                        })
        
        logger.info(f"Retrieved {len(bridge_domains)} bridge domains for user {current_user.username}")
        
        return jsonify({
            'bridge_domains': bridge_domains,
            'total_count': len(bridge_domains)
        }), 200
        
    except Exception as e:
        logger.error(f"List bridge domains error: {e}")
        return jsonify({'error': 'Failed to list bridge domains'}), 500


@api_v1.route('/bridge-domains/<bridge_domain_name>/details', methods=['GET'])
@token_required
def get_bridge_domain_details(current_user, bridge_domain_name):
    """Get detailed information about a specific bridge domain"""
    try:
        # First check personal bridge domains
        personal_domain = PersonalBridgeDomain.query.filter_by(
            user_id=current_user.id,
            bridge_domain_name=bridge_domain_name
        ).first()
        
        if personal_domain:
            return jsonify({
                'bridge_domain': {
                    'id': personal_domain.id,
                    'name': personal_domain.bridge_domain_name,
                    'vlan_id': personal_domain.vlan_id,
                    'type': 'personal',
                    'created_at': personal_domain.created_at.isoformat() if personal_domain.created_at else None,
                    'status': personal_domain.status,
                    'configuration': personal_domain.configuration
                }
            }), 200
        
        # Check topology scans
        scan = TopologyScan.query.filter_by(
            user_id=current_user.id,
            scan_type='bridge_domain_discovery',
            target=bridge_domain_name
        ).order_by(TopologyScan.created_at.desc()).first()
        
        if scan and scan.result:
            # Extract bridge domain details from scan result
            scan_data = scan.result
            if 'bridge_domains' in scan_data:
                for bd in scan_data['bridge_domains']:
                    if bd.get('name') == bridge_domain_name:
                        return jsonify({
                            'bridge_domain': {
                                'id': f"scan_{scan.id}_{bridge_domain_name}",
                                'name': bridge_domain_name,
                                'vlan_id': bd.get('vlan_id'),
                                'type': 'discovered',
                                'created_at': scan.created_at.isoformat() if scan.created_at else None,
                                'status': 'active',
                                'scan_id': scan.id,
                                'discovery_data': bd
                            }
                        }), 200
        
        return jsonify({'error': 'Bridge domain not found'}), 404
        
    except Exception as e:
        logger.error(f"Get bridge domain details error: {e}")
        return jsonify({'error': 'Failed to get bridge domain details'}), 500


@api_v1.route('/bridge-domains/<bridge_domain_name>/visualize', methods=['GET'])
@token_required
def visualize_bridge_domain(current_user, bridge_domain_name):
    """Generate visualization data for a bridge domain"""
    try:
        # Get bridge domain details first
        details_response = get_bridge_domain_details(current_user, bridge_domain_name)
        
        if details_response[1] != 200:
            return details_response
        
        details_data = details_response[0].json
        bridge_domain = details_data['bridge_domain']
        
        # Generate visualization data based on bridge domain type
        if bridge_domain['type'] == 'personal':
            # For personal bridge domains, use stored configuration
            config = bridge_domain.get('configuration', {})
            visualization_data = {
                'nodes': config.get('devices', []),
                'edges': config.get('connections', []),
                'vlan_id': bridge_domain['vlan_id'],
                'type': 'personal'
            }
        else:
            # For discovered bridge domains, use discovery data
            discovery_data = bridge_domain.get('discovery_data', {})
            visualization_data = {
                'nodes': discovery_data.get('devices', []),
                'edges': discovery_data.get('interfaces', []),
                'vlan_id': bridge_domain['vlan_id'],
                'type': 'discovered'
            }
        
        logger.info(f"Generated visualization for bridge domain {bridge_domain_name}")
        
        return jsonify({
            'bridge_domain_name': bridge_domain_name,
            'visualization': visualization_data
        }), 200
        
    except Exception as e:
        logger.error(f"Visualize bridge domain error: {e}")
        return jsonify({'error': 'Failed to generate visualization'}), 500


@api_v1.route('/bridge-domains/search', methods=['GET'])
@token_required
def search_bridge_domains(current_user):
    """Search bridge domains by name or VLAN ID"""
    try:
        query = request.args.get('q', '')
        vlan_id = request.args.get('vlan_id')
        
        if not query and not vlan_id:
            return jsonify({'error': 'Search query or VLAN ID is required'}), 400
        
        # Search personal bridge domains
        personal_query = PersonalBridgeDomain.query.filter_by(user_id=current_user.id)
        
        if query:
            personal_query = personal_query.filter(
                PersonalBridgeDomain.bridge_domain_name.contains(query)
            )
        
        if vlan_id:
            try:
                vlan_id_int = int(vlan_id)
                personal_query = personal_query.filter_by(vlan_id=vlan_id_int)
            except ValueError:
                return jsonify({'error': 'Invalid VLAN ID'}), 400
        
        personal_domains = personal_query.all()
        
        # Search topology scans
        scan_query = TopologyScan.query.filter_by(
            user_id=current_user.id,
            scan_type='bridge_domain_discovery'
        )
        
        if query:
            scan_query = scan_query.filter(TopologyScan.target.contains(query))
        
        scans = scan_query.all()
        
        # Format results
        results = []
        
        # Add personal bridge domains
        for domain in personal_domains:
            results.append({
                'id': domain.id,
                'name': domain.bridge_domain_name,
                'vlan_id': domain.vlan_id,
                'type': 'personal',
                'created_at': domain.created_at.isoformat() if domain.created_at else None,
                'status': domain.status
            })
        
        # Add discovered bridge domains from scans
        for scan in scans:
            if scan.result and isinstance(scan.result, dict):
                scan_data = scan.result
                if 'bridge_domains' in scan_data:
                    for bd in scan_data['bridge_domains']:
                        # Apply VLAN ID filter if specified
                        if vlan_id and bd.get('vlan_id') != int(vlan_id):
                            continue
                        
                        results.append({
                            'id': f"scan_{scan.id}_{bd.get('name', 'unknown')}",
                            'name': bd.get('name', 'Unknown'),
                            'vlan_id': bd.get('vlan_id'),
                            'type': 'discovered',
                            'created_at': scan.created_at.isoformat() if scan.created_at else None,
                            'status': 'active',
                            'scan_id': scan.id
                        })
        
        logger.info(f"Search completed for user {current_user.username}: {len(results)} results")
        
        return jsonify({
            'results': results,
            'total_count': len(results),
            'query': query,
            'vlan_id': vlan_id
        }), 200
        
    except Exception as e:
        logger.error(f"Search bridge domains error: {e}")
        return jsonify({'error': 'Search failed'}), 500
