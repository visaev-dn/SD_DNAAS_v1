#!/usr/bin/env python3
"""
WebSocket Package
Real-time communication handlers for deployment progress and notifications
"""

from .websocket_handlers import (
    handle_connect,
    handle_disconnect,
    handle_subscription,
    handle_unsubscription,
    emit_deployment_progress,
    emit_deployment_complete,
    emit_deployment_error,
    emit_notification,
    broadcast_message,
    get_connected_clients
)

websocket_handlers = {
    'connect': handle_connect,
    'disconnect': handle_disconnect,
    'subscription': handle_subscription,
    'unsubscription': handle_unsubscription
}

__all__ = [
    'websocket_handlers',
    'handle_connect',
    'handle_disconnect', 
    'handle_subscription',
    'handle_unsubscription',
    'emit_deployment_progress',
    'emit_deployment_complete',
    'emit_deployment_error',
    'emit_notification',
    'broadcast_message',
    'get_connected_clients'
]
