#!/usr/bin/env python3
"""
Deployments Routes
Manage deployments: listing, starting, status, deletion/restore operations
"""

from flask import request, jsonify, current_app
from datetime import datetime
import logging

from api.v1 import api_v1
from api.middleware.auth_middleware import token_required, user_ownership_required
from api.middleware.error_middleware import APIError, ValidationError, NotFoundError, ConflictError, InternalServerError
from models import db, Configuration, User, AuditLog
from deployment_manager import DeploymentManager
from config_engine.configuration_diff_engine import ConfigurationDiffEngine
from config_engine.rollback_manager import RollbackManager
from api.websocket import emit_deployment_progress, emit_deployment_complete, emit_deployment_error

logger = logging.getLogger(__name__)

# Initialize managers
deployment_manager = DeploymentManager()
diff_engine = ConfigurationDiffEngine(builder=None)  # Builder needs to be injected or passed
rollback_manager = RollbackManager()


@api_v1.route('/deployments/list', methods=['GET'])
@token_required
def list_deployments(current_user):
    """List deployments for the current user"""
    try:
        # Get deployments from the deployment manager
        deployments_result = deployment_manager.list_user_deployments(current_user.id)
        
        if deployments_result.success:
            return jsonify({
                'deployments': deployments_result.deployments,
                'total': len(deployments_result.deployments)
            })
        else:
            return jsonify({'error': 'Failed to list deployments', 'details': deployments_result.errors}), 500
            
    except Exception as e:
        logger.error(f"List deployments error: {e}")
        return jsonify({'error': 'Failed to list deployments'}), 500


@api_v1.route('/deployments/start', methods=['POST'])
@token_required
def start_deployment(current_user):
    """Start a new deployment"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Deployment data required'}), 400
        
        configuration_id = data.get('configuration_id')
        deployment_type = data.get('deployment_type', 'standard')
        dry_run = data.get('dry_run', False)
        
        if not configuration_id:
            return jsonify({'error': 'Configuration ID required'}), 400
        
        # Verify configuration exists and user owns it
        config = Configuration.query.get(configuration_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        if hasattr(config, 'user_id') and config.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Start deployment using the deployment manager
        deployment_result = deployment_manager.start_deployment(
            configuration_id=configuration_id,
            user_id=current_user.id,
            deployment_type=deployment_type,
            dry_run=dry_run
        )
        
        if deployment_result.success:
            # Emit deployment progress
            emit_deployment_progress(configuration_id, {
                'status': 'started',
                'message': f'Deployment started (type: {deployment_type})',
                'deployment_id': deployment_result.deployment_id
            })
            
            return jsonify({
                'message': 'Deployment started successfully',
                'deployment_id': deployment_result.deployment_id,
                'status': 'started',
                'type': deployment_type
            }), 201
        else:
            return jsonify({'error': 'Failed to start deployment', 'details': deployment_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Start deployment error: {e}")
        return jsonify({'error': 'Failed to start deployment'}), 500


@api_v1.route('/deployments/configurations', methods=['GET'])
@token_required
def get_user_configurations(current_user):
    """Get configurations available for deployment"""
    try:
        # Get user's configurations
        configs = Configuration.query.filter_by(user_id=current_user.id).all()
        
        deployment_configs = []
        for config in configs:
            deployment_configs.append({
                'id': config.id,
                'name': getattr(config, 'name', 'Unnamed Configuration'),
                'status': getattr(config, 'status', 'unknown'),
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'can_deploy': getattr(config, 'status', None) != 'deployed'
            })
        
        return jsonify({
            'configurations': deployment_configs,
            'total': len(deployment_configs)
        })
        
    except Exception as e:
        logger.error(f"Get user configurations error: {e}")
        return jsonify({'error': 'Failed to get configurations'}), 500


@api_v1.route('/deployments/test', methods=['GET'])
@token_required
def test_deployments(current_user):
    """Test deployment connectivity and readiness"""
    try:
        # Test deployment manager connectivity
        test_result = deployment_manager.test_connectivity()
        
        if test_result.success:
            return jsonify({
                'message': 'Deployment system is ready',
                'connectivity': 'OK',
                'services': test_result.service_status,
                'tested_at': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'message': 'Deployment system has issues',
                'connectivity': 'FAILED',
                'errors': test_result.errors,
                'tested_at': datetime.utcnow().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Test deployments error: {e}")
        return jsonify({'error': 'Failed to test deployment system'}), 500


@api_v1.route('/deployments/<deployment_id>/status', methods=['GET'])
@token_required
def get_deployment_status(current_user, deployment_id):
    """Get status of a specific deployment"""
    try:
        # Get deployment status from the deployment manager
        status_result = deployment_manager.get_deployment_status(deployment_id)
        
        if status_result.success:
            # Verify user has access to this deployment
            if status_result.deployment_data.get('user_id') != current_user.id:
                return jsonify({'error': 'Access denied'}), 403
            
            return jsonify({
                'deployment_id': deployment_id,
                'status': status_result.deployment_data,
                'current_phase': status_result.current_phase,
                'progress': status_result.progress,
                'estimated_completion': status_result.estimated_completion
            })
        else:
            return jsonify({'error': 'Failed to get deployment status', 'details': status_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Get deployment status error: {e}")
        return jsonify({'error': 'Failed to get deployment status'}), 500


@api_v1.route('/deployments/<int:config_id>/preview-deletion', methods=['GET'])
@token_required
@user_ownership_required
def preview_deletion_commands(current_user, config_id: int):
    """Preview commands needed to delete a configuration from devices"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get configuration content
        config_data = getattr(config, 'config_data', {}) or {}
        
        # Generate deletion preview using the diff engine
        deletion_preview = diff_engine.generate_deletion_commands(config_data)
        
        if deletion_preview.success:
            return jsonify({
                'configuration_id': config_id,
                'deletion_commands': deletion_preview.commands,
                'affected_devices': deletion_preview.affected_devices,
                'estimated_duration': deletion_preview.estimated_duration,
                'risk_level': deletion_preview.risk_level
            })
        else:
            return jsonify({'error': 'Failed to generate deletion preview', 'details': deletion_preview.errors}), 400
            
    except Exception as e:
        logger.error(f"Preview deletion error: {e}")
        return jsonify({'error': 'Failed to preview deletion'}), 500


@api_v1.route('/deployments/<int:config_id>/remove', methods=['POST'])
@token_required
@user_ownership_required
def remove_from_devices(current_user, config_id: int):
    """Remove configuration from devices"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)
        force = data.get('force', False)
        
        # Check if configuration is deployed
        if getattr(config, 'status', None) != 'deployed':
            return jsonify({'error': 'Configuration is not deployed'}), 400
        
        # Remove configuration using the deployment manager
        removal_result = deployment_manager.remove_configuration(
            config_id=config_id,
            dry_run=dry_run,
            force=force
        )
        
        if removal_result.success:
            # Update configuration status
            config.status = 'removed' if not dry_run else 'dry_run_removal'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'removed' if not dry_run else 'dry_run_removal',
                'message': f'Configuration removed from devices (dry_run: {dry_run})',
                'removal_id': removal_result.removal_id
            })
            
            return jsonify({
                'message': 'Configuration removed successfully' if not dry_run else 'Dry run removal completed',
                'removal_id': removal_result.removal_id,
                'dry_run': dry_run
            })
        else:
            return jsonify({'error': 'Removal failed', 'details': removal_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Remove from devices error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to remove configuration from devices'}), 500


@api_v1.route('/deployments/<int:config_id>/restore', methods=['POST'])
@token_required
@user_ownership_required
def restore_configuration(current_user, config_id: int):
    """Restore a previously removed configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        data = request.get_json() or {}
        restore_point = data.get('restore_point', 'last_deployed')
        dry_run = data.get('dry_run', False)
        
        # Check if configuration can be restored
        if getattr(config, 'status', None) not in ['removed', 'rolled_back']:
            return jsonify({'error': 'Configuration cannot be restored from current status'}), 400
        
        # Restore configuration using the rollback manager
        restore_result = rollback_manager.restore_configuration(
            config_id=config_id,
            restore_point=restore_point,
            dry_run=dry_run
        )
        
        if restore_result.success:
            # Update configuration status
            config.status = 'restored' if not dry_run else 'dry_run_restore'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'restored' if not dry_run else 'dry_run_restore',
                'message': f'Configuration restored to {restore_point} (dry_run: {dry_run})',
                'restore_id': restore_result.restore_id
            })
            
            return jsonify({
                'message': 'Configuration restored successfully' if not dry_run else 'Dry run restore completed',
                'restore_id': restore_result.restore_id,
                'restore_point': restore_point,
                'dry_run': dry_run
            })
        else:
            return jsonify({'error': 'Restore failed', 'details': restore_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Restore configuration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to restore configuration'}), 500


@api_v1.route('/deployments/<int:config_id>/pause', methods=['POST'])
@token_required
@user_ownership_required
def pause_deployment(current_user, config_id: int):
    """Pause an active deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Check if deployment can be paused
        if getattr(config, 'status', None) not in ['deploying', 'in_progress']:
            return jsonify({'error': 'Deployment cannot be paused from current status'}), 400
        
        # Pause deployment using the deployment manager
        pause_result = deployment_manager.pause_deployment(config_id)
        
        if pause_result.success:
            # Update configuration status
            config.status = 'paused'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'paused',
                'message': 'Deployment paused by user',
                'paused_at': datetime.utcnow().isoformat()
            })
            
            return jsonify({
                'message': 'Deployment paused successfully',
                'status': 'paused'
            })
        else:
            return jsonify({'error': 'Failed to pause deployment', 'details': pause_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Pause deployment error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to pause deployment'}), 500


@api_v1.route('/deployments/<int:config_id>/resume', methods=['POST'])
@token_required
@user_ownership_required
def resume_deployment(current_user, config_id: int):
    """Resume a paused deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Check if deployment can be resumed
        if getattr(config, 'status', None) != 'paused':
            return jsonify({'error': 'Deployment cannot be resumed from current status'}), 400
        
        # Resume deployment using the deployment manager
        resume_result = deployment_manager.resume_deployment(config_id)
        
        if resume_result.success:
            # Update configuration status
            config.status = 'deploying'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'resumed',
                'message': 'Deployment resumed by user',
                'resumed_at': datetime.utcnow().isoformat()
            })
            
            return jsonify({
                'message': 'Deployment resumed successfully',
                'status': 'deploying'
            })
        else:
            return jsonify({'error': 'Failed to resume deployment', 'details': resume_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Resume deployment error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to resume deployment'}), 500


@api_v1.route('/deployments/<int:config_id>/cancel', methods=['POST'])
@token_required
@user_ownership_required
def cancel_deployment(current_user, config_id: int):
    """Cancel an active deployment"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Check if deployment can be cancelled
        if getattr(config, 'status', None) not in ['deploying', 'in_progress', 'paused']:
            return jsonify({'error': 'Deployment cannot be cancelled from current status'}), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Cancelled by user')
        
        # Cancel deployment using the deployment manager
        cancel_result = deployment_manager.cancel_deployment(config_id, reason)
        
        if cancel_result.success:
            # Update configuration status
            config.status = 'cancelled'
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit deployment progress
            emit_deployment_progress(config_id, {
                'status': 'cancelled',
                'message': f'Deployment cancelled: {reason}',
                'cancelled_at': datetime.utcnow().isoformat()
            })
            
            return jsonify({
                'message': 'Deployment cancelled successfully',
                'status': 'cancelled',
                'reason': reason
            })
        else:
            return jsonify({'error': 'Failed to cancel deployment', 'details': cancel_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Cancel deployment error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel deployment'}), 500


@api_v1.route('/deployments/<int:config_id>/logs', methods=['GET'])
@token_required
@user_ownership_required
def get_deployment_logs(current_user, config_id: int):
    """Get deployment logs for a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get deployment logs from the deployment manager
        logs_result = deployment_manager.get_deployment_logs(config_id)
        
        if logs_result.success:
            return jsonify({
                'configuration_id': config_id,
                'logs': logs_result.logs,
                'total_entries': len(logs_result.logs),
                'last_updated': logs_result.last_updated
            })
        else:
            return jsonify({'error': 'Failed to get deployment logs', 'details': logs_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Get deployment logs error: {e}")
        return jsonify({'error': 'Failed to get deployment logs'}), 500


@api_v1.route('/deployments/<int:config_id>/metrics', methods=['GET'])
@token_required
@user_ownership_required
def get_deployment_metrics(current_user, config_id: int):
    """Get deployment metrics for a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get deployment metrics from the deployment manager
        metrics_result = deployment_manager.get_deployment_metrics(config_id)
        
        if metrics_result.success:
            return jsonify({
                'configuration_id': config_id,
                'metrics': metrics_result.metrics,
                'performance_data': metrics_result.performance_data,
                'resource_usage': metrics_result.resource_usage
            })
        else:
            return jsonify({'error': 'Failed to get deployment metrics', 'details': metrics_result.errors}), 400
            
    except Exception as e:
        logger.error(f"Get deployment metrics error: {e}")
        return jsonify({'error': 'Failed to get deployment metrics'}), 500
