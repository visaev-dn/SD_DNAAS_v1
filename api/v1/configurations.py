#!/usr/bin/env/python3
"""
Configurations Routes
Manage configurations: listing, details, metadata, builder input, validation, deployment, export, and smart deploy operations
"""

from flask import request, jsonify, current_app, send_file
from datetime import datetime
import logging
import json
import os
from pathlib import Path

from api.v1 import api_v1
from api.middleware.auth_middleware import token_required, user_ownership_required
from api.middleware.error_middleware import APIError, ValidationError, NotFoundError, ConflictError, InternalServerError
from models import db, Configuration, User, PersonalBridgeDomain, TopologyScan
from config_engine.configuration import ConfigurationManager
from config_engine.bridge_domain import UnifiedBridgeDomainBuilder, BridgeDomainConfig
from config_engine.enhanced_topology_scanner import EnhancedTopologyScanner
from config_engine.smart_deployment_manager import SmartDeploymentManager
from config_engine.configuration_diff_engine import ConfigurationDiffEngine
from config_engine.rollback_manager import RollbackManager
from api.websocket import emit_deployment_progress, emit_deployment_complete, emit_deployment_error

logger = logging.getLogger(__name__)

# Initialize managers
config_manager = ConfigurationManager()
unified_builder = UnifiedBridgeDomainBuilder()
smart_deployment_manager = SmartDeploymentManager()
diff_engine = ConfigurationDiffEngine(builder=unified_builder)
rollback_manager = RollbackManager()


@api_v1.route('/configurations', methods=['GET'])
@token_required
def get_configurations(current_user):
    """List configurations for the current user (basic fields)"""
    try:
        query = Configuration.query
        # Optional: filter by user
        user_only = request.args.get('mine', 'true').lower() == 'true'
        if user_only and hasattr(Configuration, 'user_id'):
            query = query.filter_by(user_id=current_user.id)
        
        configs = query.order_by(Configuration.created_at.desc()).all()
        
        items = []
        for c in configs:
            items.append({
                'id': c.id,
                'name': getattr(c, 'name', None),
                'status': getattr(c, 'status', None),
                'created_at': c.created_at.isoformat() if getattr(c, 'created_at', None) else None,
            })
        
        return jsonify({'configurations': items, 'total': len(items)})
    except Exception as e:
        logger.error(f"Get configurations error: {e}")
        return jsonify({'error': 'Failed to list configurations'}), 500


@api_v1.route('/configurations/<int:config_id>', methods=['GET'])
@token_required
@user_ownership_required
def get_configuration_details(current_user, config_id: int):
    """Get configuration details by ID"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = {
            'id': config.id,
            'name': getattr(config, 'name', None),
            'status': getattr(config, 'status', None),
            'content': getattr(config, 'config_data', None),
            'created_at': config.created_at.isoformat() if getattr(c, 'created_at', None) else None,
            'updated_at': config.updated_at.isoformat() if getattr(c, 'updated_at', None) else None,
        }
        return jsonify({'configuration': data})
    except Exception as e:
        logger.error(f"Get configuration details error: {e}")
        return jsonify({'error': 'Failed to get configuration details'}), 500


@api_v1.route('/configurations/<int:config_id>/metadata', methods=['GET'])
@token_required
@user_ownership_required
def get_configuration_metadata(current_user, config_id: int):
    """Get metadata for a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        metadata = getattr(config, 'metadata', {}) or {}
        return jsonify({'metadata': metadata})
    except Exception as e:
        logger.error(f"Get configuration metadata error: {e}")
        return jsonify({'error': 'Failed to get metadata'}), 500


@api_v1.route('/configurations/<int:config_id>/preview-deployment', methods=['GET'])
@token_required
@user_ownership_required
def preview_deployment_commands(current_user, config_id: int):
    """Preview deployment commands for a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get configuration content
        config_data = getattr(config, 'config_data', {}) or {}
        
        # Generate preview using the configuration manager
        preview_result = config_manager.generate_preview(config_data)
        
        return jsonify({
            'configuration_id': config_id,
            'preview': preview_result,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Preview deployment error: {e}")
        return jsonify({'error': 'Failed to preview deployment'}), 500


@api_v1.route('/configurations/<int:config_id>/builder-input', methods=['GET'])
@token_required
@user_ownership_required
def get_configuration_builder_input(current_user, config_id: int):
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        builder_input = getattr(config, 'builder_input', None)
        return jsonify({'builder_input': builder_input})
    except Exception as e:
        logger.error(f"Get builder input error: {e}")
        return jsonify({'error': 'Failed to get builder input'}), 500


@api_v1.route('/configurations/<int:config_id>/builder-input', methods=['PUT'])
@token_required
@user_ownership_required
def update_configuration_builder_input(current_user, config_id: int):
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json()
        if not data or 'builder_input' not in data:
            return jsonify({'error': 'Builder input data required'}), 400
        
        # Update builder input
        config.builder_input = data['builder_input']
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Builder input updated successfully'})
    except Exception as e:
        logger.error(f"Update builder input error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update builder input'}), 500


@api_v1.route('/configurations/<int:config_id>/regenerate-from-builder-input', methods=['POST'])
@token_required
@user_ownership_required
def regenerate_from_builder_input(current_user, config_id: int):
    """Regenerate configuration from builder input"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        builder_input = getattr(config, 'builder_input', None)
        if not builder_input:
            return jsonify({'error': 'No builder input available'}), 400
        
        # Regenerate using the configuration manager
        result = config_manager.generate(builder_input, current_user.id)
        
        if result.success:
            # Update configuration with new data
            config.config_data = result.config_data
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'message': 'Configuration regenerated successfully',
                'configuration_id': config_id
            })
        else:
            return jsonify({'error': 'Failed to regenerate configuration', 'details': result.errors}), 400
            
    except Exception as e:
        logger.error(f"Regenerate configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to regenerate configuration'}), 500


@api_v1.route('/configurations/<int:config_id>/validate', methods=['POST'])
@token_required
@user_ownership_required
def validate_configuration(current_user, config_id: int):
    """Validate a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        config_data = getattr(config, 'config_data', {}) or {}
        
        # Validate using the configuration manager
        validation_result = config_manager.validate(config_data)
        
        return jsonify({
            'configuration_id': config_id,
            'is_valid': validation_result.is_valid,
            'errors': validation_result.errors,
            'warnings': validation_result.warnings,
            'validated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Validate configuration error: {e}")
        return jsonify({'error': 'Failed to validate configuration'}), 500


@api_v1.route('/configurations/<int:config_id>/deploy', methods=['POST'])
@token_required
@user_ownership_required
def deploy_configuration(current_user, config_id: int):
    """Deploy a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)
        
        config_data = getattr(config, 'config_data', {}) or {}
        
        # Deploy using the configuration manager
        deployment_result = config_manager.deploy(config_data, dry_run=dry_run)
        
        if deployment_result.success:
            # Update configuration status
            config.status = 'deployed' if not dry_run else 'dry_run'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            if not dry_run:
                emit_deployment_progress(config_id, {
                    'status': 'completed',
                    'message': 'Configuration deployed successfully'
                })
            
            return jsonify({
                'message': 'Configuration deployed successfully' if not dry_run else 'Dry run completed',
                'deployment_id': deployment_result.deployment_id,
                'dry_run': dry_run
            })
        else:
            return jsonify({'error': 'Deployment failed', 'details': deployment_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Deploy configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to deploy configuration'}), 500


@api_v1.route('/configurations/<int:config_id>/export', methods=['POST'])
@token_required
@user_ownership_required
def export_configuration(current_user, config_id: int):
    """Export a configuration to file"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        export_format = data.get('format', 'json')
        filename = data.get('filename', f'config_{config_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        
        config_data = getattr(config, 'config_data', {}) or {}
        
        # Export using the configuration manager
        export_result = config_manager.export(config_data, export_format, filename)
        
        if export_result.success:
            # Return file for download
            file_path = Path(export_result.file_path)
            if file_path.exists():
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=export_result.filename,
                    mimetype='application/octet-stream'
                )
            else:
                return jsonify({'error': 'Export file not found'}), 500
        else:
            return jsonify({'error': 'Export failed', 'details': export_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Export configuration error: {e}")
        return jsonify({'error': 'Failed to export configuration'}), 500


@api_v1.route('/configurations/<int:config_id>/delete', methods=['DELETE'])
@token_required
@user_ownership_required
def delete_configuration(current_user, config_id: int):
    """Delete a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Check if configuration is deployed
        if getattr(config, 'status', None) == 'deployed':
            return jsonify({'error': 'Cannot delete deployed configuration'}), 400
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'message': 'Configuration deleted successfully'})
        
    except Exception as e:
        logger.error(f"Delete configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete configuration'}), 500


@api_v1.route('/configurations/import', methods=['POST'])
@token_required
def import_configuration(current_user):
    """Import a configuration from file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Import using the configuration manager
        import_result = config_manager.import_config(file, current_user.id)
        
        if import_result.success:
            # Create new configuration record
            new_config = Configuration(
                name=import_result.name,
                config_data=import_result.config_data,
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(new_config)
            db.session.commit()
            
            return jsonify({
                'message': 'Configuration imported successfully',
                'configuration_id': new_config.id
            })
        else:
            return jsonify({'error': 'Import failed', 'details': import_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Import configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to import configuration'}), 500


@api_v1.route('/configurations/<bridge_domain_name>/scan', methods=['POST'])
@token_required
def scan_bridge_domain_topology(current_user, bridge_domain_name: str):
    """Scan bridge domain topology"""
    try:
        data = request.get_json() or {}
        scan_depth = data.get('scan_depth', 'full')
        
        # Use the enhanced topology scanner
        scanner = EnhancedTopologyScanner()
        scan_result = scanner.scan_bridge_domain(bridge_domain_name, scan_depth)
        
        if scan_result.success:
            # Save scan result
            scan_record = TopologyScan(
                bridge_domain_name=bridge_domain_name,
                scan_data=scan_result.topology_data,
                scan_depth=scan_depth,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(scan_record)
            db.session.commit()
            
            return jsonify({
                'message': 'Topology scan completed successfully',
                'scan_id': scan_record.id,
                'topology_data': scan_result.topology_data
            })
        else:
            return jsonify({'error': 'Scan failed', 'details': scan_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Scan bridge domain topology error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to scan topology'}), 500


@api_v1.route('/configurations/<bridge_domain_name>/reverse-engineer', methods=['POST'])
@token_required
def reverse_engineer_configuration(current_user, bridge_domain_name: str):
    """Reverse engineer configuration from existing bridge domain"""
    try:
        data = request.get_json() or {}
        include_metadata = data.get('include_metadata', True)
        
        # Use the configuration manager for reverse engineering
        reverse_result = config_manager.reverse_engineer(bridge_domain_name, include_metadata)
        
        if reverse_result.success:
            # Create new configuration from reverse engineered data
            new_config = Configuration(
                name=f"Reverse Engineered: {bridge_domain_name}",
                config_data=reverse_result.config_data,
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(new_config)
            db.session.commit()
            
            return jsonify({
                'message': 'Configuration reverse engineered successfully',
                'configuration_id': new_config.id,
                'bridge_domain': bridge_domain_name
            })
        else:
            return jsonify({'error': 'Reverse engineering failed', 'details': reverse_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Reverse engineer configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to reverse engineer configuration'}), 500


@api_v1.route('/configurations/<bridge_domain_name>/scan-fixed', methods=['POST'])
@token_required
def scan_bridge_domain_topology_fixed(current_user, bridge_domain_name: str):
    """Scan bridge domain topology with fixed parameters"""
    try:
        data = request.get_json() or {}
        scan_depth = data.get('scan_depth', 'full')
        fixed_params = data.get('fixed_parameters', {})
        
        # Use the enhanced topology scanner with fixed parameters
        scanner = EnhancedTopologyScanner()
        scan_result = scanner.scan_bridge_domain_fixed(bridge_domain_name, scan_depth, fixed_params)
        
        if scan_result.success:
            # Save scan result
            scan_record = TopologyScan(
                bridge_domain_name=bridge_domain_name,
                scan_data=scan_result.topology_data,
                scan_depth=scan_depth,
                user_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(scan_record)
            db.session.commit()
            
            return jsonify({
                'message': 'Fixed topology scan completed successfully',
                'scan_id': scan_record.id,
                'topology_data': scan_result.topology_data
            })
        else:
            return jsonify({'error': 'Fixed scan failed', 'details': scan_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Fixed scan bridge domain topology error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to perform fixed topology scan'}), 500


@api_v1.route('/configurations/bridge-domain/<string:bridge_domain_id>', methods=['DELETE'])
@token_required
@user_ownership_required
def delete_imported_bridge_domain(current_user, bridge_domain_id: str):
    """Delete an imported bridge domain configuration"""
    try:
        # Find and delete the bridge domain configuration
        bd_config = PersonalBridgeDomain.query.filter_by(
            bridge_domain_id=bridge_domain_id,
            user_id=current_user.id
        ).first()
        
        if not bd_config:
            return jsonify({'error': 'Bridge domain configuration not found'}), 404
        
        db.session.delete(bd_config)
        db.session.commit()
        
        return jsonify({'message': 'Bridge domain configuration deleted successfully'})
        
    except Exception as e:
        logger.error(f"Delete imported bridge domain error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete bridge domain configuration'}), 500


@api_v1.route('/configurations/bridge-domain/<string:bridge_domain_id>', methods=['GET'])
@token_required
@user_ownership_required
def get_imported_bridge_domain_details(current_user, bridge_domain_id: str):
    """Get details of an imported bridge domain configuration"""
    try:
        bd_config = PersonalBridgeDomain.query.filter_by(
            bridge_domain_id=bridge_domain_id,
            user_id=current_user.id
        ).first()
        
        if not bd_config:
            return jsonify({'error': 'Bridge domain configuration not found'}), 404
        
        return jsonify({
            'bridge_domain_id': bd_config.bridge_domain_id,
            'name': bd_config.name,
            'topology_data': bd_config.topology_data,
            'created_at': bd_config.created_at.isoformat() if bd_config.created_at else None,
            'updated_at': bd_config.updated_at.isoformat() if bd_config.updated_at else None
        })
        
    except Exception as e:
        logger.error(f"Get imported bridge domain details error: {e}")
        return jsonify({'error': 'Failed to get bridge domain details'}), 500


@api_v1.route('/configurations/bridge-domain/<string:bridge_domain_id>/validate', methods=['POST'])
@token_required
@user_ownership_required
def validate_imported_bridge_domain(current_user, bridge_domain_id: str):
    """Validate an imported bridge domain configuration"""
    try:
        bd_config = PersonalBridgeDomain.query.filter_by(
            bridge_domain_id=bridge_domain_id,
            user_id=current_user.id
        ).first()
        
        if not bd_config:
            return jsonify({'error': 'Bridge domain configuration not found'}), 404
        
        # Validate using the configuration manager
        validation_result = config_manager.validate_bridge_domain(bd_config.topology_data)
        
        return jsonify({
            'bridge_domain_id': bridge_domain_id,
            'is_valid': validation_result.is_valid,
            'errors': validation_result.errors,
            'warnings': validation_result.warnings,
            'validated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Validate imported bridge domain error: {e}")
        return jsonify({'error': 'Failed to validate bridge domain configuration'}), 500


# Smart Deploy Operations

@api_v1.route('/configurations/<int:config_id>/smart-deploy/analyze', methods=['POST'])
@token_required
@user_ownership_required
def analyze_configuration_changes(current_user, config_id: int):
    """Analyze configuration changes for smart deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        analysis_depth = data.get('analysis_depth', 'comprehensive')
        
        # Use the smart deployment manager for analysis
        analysis_result = smart_deployment_manager.analyze_changes(
            config.config_data,
            analysis_depth=analysis_depth
        )
        
        if analysis_result.success:
            return jsonify({
                'configuration_id': config_id,
                'analysis': analysis_result.analysis_data,
                'risk_assessment': analysis_result.risk_assessment,
                'deployment_steps': analysis_result.deployment_steps,
                'estimated_duration': analysis_result.estimated_duration
            })
        else:
            return jsonify({'error': 'Analysis failed', 'details': analysis_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Smart deploy analyze error: {e}")
        return jsonify({'error': 'Failed to analyze configuration changes'}), 500


@api_v1.route('/configurations/<int:config_id>/smart-deploy/plan', methods=['POST'])
@token_required
@user_ownership_required
def generate_smart_deployment_plan(current_user, config_id: int):
    """Generate smart deployment plan"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        deployment_strategy = data.get('strategy', 'conservative')
        
        # Use the smart deployment manager to generate plan
        plan_result = smart_deployment_manager.generate_plan(
            config.config_data,
            strategy=deployment_strategy
        )
        
        if plan_result.success:
            return jsonify({
                'configuration_id': config_id,
                'deployment_plan': plan_result.plan_data,
                'phases': plan_result.phases,
                'rollback_points': plan_result.rollback_points,
                'estimated_duration': plan_result.estimated_duration
            })
        else:
            return jsonify({'error': 'Plan generation failed', 'details': plan_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Smart deploy plan error: {e}")
        return jsonify({'error': 'Failed to generate deployment plan'}), 500


@api_v1.route('/configurations/<int:config_id>/smart-deploy/execute', methods=['POST'])
@token_required
@user_ownership_required
def execute_smart_deployment(current_user, config_id: int):
    """Execute smart deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        deployment_id = data.get('deployment_id')
        
        if not deployment_id:
            return jsonify({'error': 'Deployment ID required'}), 400
        
        # Use the smart deployment manager to execute deployment
        execution_result = smart_deployment_manager.execute_deployment(
            deployment_id,
            config.config_data
        )
        
        if execution_result.success:
            # Update configuration status
            config.status = 'deploying'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'started',
                'message': 'Smart deployment started',
                'deployment_id': deployment_id
            })
            
            return jsonify({
                'message': 'Smart deployment started successfully',
                'deployment_id': deployment_id,
                'status': 'started'
            })
        else:
            return jsonify({'error': 'Deployment execution failed', 'details': execution_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Smart deploy execute error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to execute smart deployment'}), 500


@api_v1.route('/configurations/<int:config_id>/smart-deploy/rollback', methods=['POST'])
@token_required
@user_ownership_required
def rollback_smart_deployment(current_user, config_id: int):
    """Rollback smart deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        rollback_point = data.get('rollback_point', 'last_stable')
        
        # Use the rollback manager
        rollback_result = rollback_manager.rollback_deployment(
            config_id,
            rollback_point
        )
        
        if rollback_result.success:
            # Update configuration status
            config.status = 'rolled_back'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'rolled_back',
                'message': f'Deployment rolled back to {rollback_point}',
                'rollback_point': rollback_point
            })
            
            return jsonify({
                'message': 'Deployment rolled back successfully',
                'rollback_point': rollback_point,
                'status': 'rolled_back'
            })
        else:
            return jsonify({'error': 'Rollback failed', 'details': rollback_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Smart deploy rollback error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to rollback deployment'}), 500


@api_v1.route('/configurations/<int:config_id>/smart-deploy/status', methods=['GET'])
@token_required
@user_ownership_required
def smart_deploy_status(current_user, config_id: int):
    """Get smart deployment status"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get deployment status from smart deployment manager
        status_result = smart_deployment_manager.get_deployment_status(config_id)
        
        if status_result.success:
            return jsonify({
                'configuration_id': config_id,
                'deployment_status': status_result.status_data,
                'current_phase': status_result.current_phase,
                'progress': status_result.progress,
                'last_updated': status_result.last_updated
            })
        else:
            return jsonify({'error': 'Failed to get deployment status', 'details': status_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Smart deploy status error: {e}")
        return jsonify({'error': 'Failed to get deployment status'}), 500
