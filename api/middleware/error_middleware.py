#!/usr/bin/env python3
"""
Error Handling Middleware
Centralized error handling and response formatting
"""

from flask import jsonify, current_app
import logging
import traceback

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(APIError):
    """Raised when input validation fails"""
    def __init__(self, message, payload=None):
        super().__init__(message, 400, payload)


class AuthenticationError(APIError):
    """Raised when authentication fails"""
    def __init__(self, message, payload=None):
        super().__init__(message, 401, payload)


class AuthorizationError(APIError):
    """Raised when authorization fails"""
    def __init__(self, message, payload=None):
        super().__init__(message, 403, payload)


class NotFoundError(APIError):
    """Raised when a resource is not found"""
    def __init__(self, message, payload=None):
        super().__init__(message, 404, payload)


class ConflictError(APIError):
    """Raised when there's a conflict (e.g., duplicate resource)"""
    def __init__(self, message, payload=None):
        super().__init__(message, 409, payload)


class InternalServerError(APIError):
    """Raised when an internal server error occurs"""
    def __init__(self, message, payload=None):
        super().__init__(message, 500, payload)


def handle_api_error(error):
    """Handle API errors and return consistent JSON responses"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_validation_error(error):
    """Handle validation errors"""
    response = jsonify({
        'error': 'Validation Error',
        'message': str(error),
        'status_code': 400
    })
    response.status_code = 400
    return response


def handle_generic_error(error):
    """Handle generic errors and return consistent JSON responses"""
    # Log the error
    logger.error(f"Unhandled error: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # In production, don't expose internal error details
    if current_app.config.get('DEBUG', False):
        response = jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'traceback': traceback.format_exc(),
            'status_code': 500
        })
    else:
        response = jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        })
    
    response.status_code = 500
    return response


def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_exception(error):
        return handle_api_error(error)
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid request data',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'HTTP method not supported for this endpoint',
            'status_code': 405
        }), 405
    
    @app.errorhandler(409)
    def handle_conflict(error):
        return jsonify({
            'error': 'Conflict',
            'message': 'Resource conflict detected',
            'status_code': 409
        }), 409
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'Request data cannot be processed',
            'status_code': 422
        }), 422
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        return handle_generic_error(error)
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        return handle_generic_error(error)


def format_error_response(message, status_code=400, details=None):
    """Format a consistent error response"""
    response = {
        'error': True,
        'message': message,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
    
    return response


def format_success_response(data=None, message="Success"):
    """Format a consistent success response"""
    response = {
        'error': False,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return response
