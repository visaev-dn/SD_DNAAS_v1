# API Middleware Package
# Provides authentication, error handling, rate limiting, logging, caching, and monitoring middleware

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

from .caching import (
    CacheEntry, LRUCache, api_cache, generate_cache_key, cache_response,
    cache_by_user, cache_by_parameters, invalidate_cache,
    cache_stats, clear_cache, configure_caching,
    cache_dashboard_data, cache_configuration_data, cache_topology_data,
    invalidate_user_cache
)

from .monitoring import (
    MetricsCollector, metrics_collector, monitor_request, monitor_performance,
    health_check, detailed_health_check, get_metrics, clear_metrics,
    configure_monitoring, monitor_endpoint, monitor_user_activity, performance_alert
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
    'log_auth_operation', 'log_admin_operation', 'log_deployment_operation', 'log_configuration_change',
    
    # Caching middleware
    'CacheEntry', 'LRUCache', 'api_cache', 'generate_cache_key', 'cache_response',
    'cache_by_user', 'cache_by_parameters', 'invalidate_cache',
    'cache_stats', 'clear_cache', 'configure_caching',
    'cache_dashboard_data', 'cache_configuration_data', 'cache_topology_data',
    'invalidate_user_cache',
    
    # Monitoring middleware
    'MetricsCollector', 'metrics_collector', 'monitor_request', 'monitor_performance',
    'health_check', 'detailed_health_check', 'get_metrics', 'clear_metrics',
    'configure_monitoring', 'monitor_endpoint', 'monitor_user_activity', 'performance_alert'
]
