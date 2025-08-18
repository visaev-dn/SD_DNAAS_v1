#!/usr/bin/env python3
"""
WebSocket Handlers
Handles real-time communication for deployment progress and notifications
"""

from flask_socketio import emit, join_room, leave_room
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def handle_connect():
    """Handle WebSocket connection"""
    try:
        logger.info("WebSocket client connected")
        emit('connected', {
            'message': 'Connected to Lab Automation WebSocket',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"WebSocket connect error: {e}")


def handle_disconnect():
    """Handle WebSocket disconnection"""
    try:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket disconnect error: {e}")


def handle_subscription(data):
    """Handle subscription to deployment updates"""
    try:
        deployment_id = data.get('deployment_id')
        if not deployment_id:
            emit('error', {'message': 'Deployment ID is required'})
            return
        
        # Join the deployment room
        join_room(f'deployment_{deployment_id}')
        
        logger.info(f"Client subscribed to deployment {deployment_id}")
        
        emit('subscribed', {
            'message': f'Subscribed to deployment {deployment_id}',
            'deployment_id': deployment_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"WebSocket subscription error: {e}")
        emit('error', {'message': 'Subscription failed'})


def handle_unsubscription(data):
    """Handle unsubscription from deployment updates"""
    try:
        deployment_id = data.get('deployment_id')
        if not deployment_id:
            emit('error', {'message': 'Deployment ID is required'})
            return
        
        # Leave the deployment room
        leave_room(f'deployment_{deployment_id}')
        
        logger.info(f"Client unsubscribed from deployment {deployment_id}")
        
        emit('unsubscribed', {
            'message': f'Unsubscribed from deployment {deployment_id}',
            'deployment_id': deployment_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"WebSocket unsubscription error: {e}")
        emit('error', {'message': 'Unsubscription failed'})


def emit_deployment_progress(deployment_id, progress_data):
    """Emit deployment progress to subscribed clients"""
    try:
        room = f'deployment_{deployment_id}'
        
        # Add timestamp to progress data
        progress_data['timestamp'] = datetime.utcnow().isoformat()
        progress_data['deployment_id'] = deployment_id
        
        # Emit to all clients in the deployment room
        emit('deployment_progress', progress_data, room=room)
        
        logger.info(f"Emitted deployment progress for {deployment_id}: {progress_data.get('status', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to emit deployment progress: {e}")


def emit_deployment_complete(deployment_id, result_data):
    """Emit deployment completion notification"""
    try:
        room = f'deployment_{deployment_id}'
        
        # Add timestamp to result data
        result_data['timestamp'] = datetime.utcnow().isoformat()
        result_data['deployment_id'] = deployment_id
        
        # Emit to all clients in the deployment room
        emit('deployment_complete', result_data, room=room)
        
        logger.info(f"Emitted deployment completion for {deployment_id}")
        
    except Exception as e:
        logger.error(f"Failed to emit deployment completion: {e}")


def emit_deployment_error(deployment_id, error_data):
    """Emit deployment error notification"""
    try:
        room = f'deployment_{deployment_id}'
        
        # Add timestamp to error data
        error_data['timestamp'] = datetime.utcnow().isoformat()
        error_data['deployment_id'] = deployment_id
        
        # Emit to all clients in the deployment room
        emit('deployment_error', error_data, room=room)
        
        logger.info(f"Emitted deployment error for {deployment_id}: {error_data.get('error', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to emit deployment error: {e}")


def emit_notification(user_id, notification_data):
    """Emit notification to a specific user"""
    try:
        room = f'user_{user_id}'
        
        # Add timestamp to notification data
        notification_data['timestamp'] = datetime.utcnow().isoformat()
        notification_data['user_id'] = user_id
        
        # Emit to the user's room
        emit('notification', notification_data, room=room)
        
        logger.info(f"Emitted notification to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to emit notification: {e}")


def broadcast_message(message_data):
    """Broadcast message to all connected clients"""
    try:
        # Add timestamp to message data
        message_data['timestamp'] = datetime.utcnow().isoformat()
        
        # Emit to all clients
        emit('broadcast', message_data, broadcast=True)
        
        logger.info("Broadcasted message to all clients")
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")


def get_connected_clients():
    """Get count of connected WebSocket clients"""
    try:
        # This would need to be implemented based on the specific WebSocket library
        # For now, return a placeholder
        return {'connected_clients': 'Unknown'}
    except Exception as e:
        logger.error(f"Failed to get connected clients: {e}")
        return {'connected_clients': 'Error'}
