# API Middleware Package
# Provides authentication, error handling, rate limiting, and logging middleware

from .auth_middleware import (
    token_required, permission_required, admin_required, user_ownership_required,
    create_audit_log
)

from .error_middleware import (
    APIError, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ConflictError, InternalServerError,
    handle_api_error, handle_validation_error, handle_generic_error,
    register_error_handlers, format_error_response, format_success_response
)

from .rate_limiting import (
    RateLimiter, rate_limit, rate_limit_by_user, rate_limit_by_ip,
    get_rate_limit_info, configure_rate_limits,
    auth_rate_limit, deployment_rate_limit, admin_rate_limit, user_rate_limit
)

from .logging_middleware import (
    RequestLogger, log_request, log_request_with_body, log_sensitive_operation,
    log_performance, log_user_activity, configure_request_logging,
    log_auth_operation, log_admin_operation, log_deployment_operation, log_configuration_change
)

__all__ = [
    # Auth middleware
    'token_required', 'permission_required', 'admin_required', 'user_ownership_required',
    'create_audit_log',
    
    # Error middleware
    'APIError', 'ValidationError', 'AuthenticationError', 'AuthorizationError',
    'NotFoundError', 'ConflictError', 'InternalServerError',
    'handle_api_error', 'handle_validation_error', 'handle_generic_error',
    'register_error_handlers', 'format_error_response', 'format_success_response',
    
    # Rate limiting middleware
    'RateLimiter', 'rate_limit', 'rate_limit_by_user', 'rate_limit_by_ip',
    'get_rate_limit_info', 'configure_rate_limits',
    'auth_rate_limit', 'deployment_rate_limit', 'admin_rate_limit', 'user_rate_limit',
    
    # Logging middleware
    'RequestLogger', 'log_request', 'log_request_with_body', 'log_sensitive_operation',
    'log_performance', 'log_user_activity', 'configure_request_logging',
    'log_auth_operation', 'log_admin_operation', 'log_deployment_operation', 'log_configuration_change'
]
