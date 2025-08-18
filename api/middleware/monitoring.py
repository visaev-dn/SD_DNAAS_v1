#!/usr/bin/env python3
"""
Monitoring and Metrics Middleware
Provides comprehensive monitoring, metrics collection, and health checks
"""

from functools import wraps
from flask import request, jsonify, current_app, g
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import psutil
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores API metrics"""
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.lock = threading.RLock()
        
        # Request metrics
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.status_codes = defaultdict(int)
        
        # Endpoint metrics
        self.endpoint_metrics = defaultdict(lambda: {
            'total_requests': 0,
            'total_errors': 0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'last_request': None
        })
        
        # User metrics
        self.user_metrics = defaultdict(lambda: {
            'total_requests': 0,
            'total_errors': 0,
            'last_request': None
        })
        
        # System metrics
        self.system_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': []
        }
    
    def record_request(self, endpoint, method, user_id=None, response_time=None, status_code=None, error=None):
        """Record a request metric"""
        with self.lock:
            # Request counts
            self.request_counts[f"{method} {endpoint}"] += 1
            
            # Response times
            if response_time is not None:
                self.response_times[f"{method} {endpoint}"].append(response_time)
                # Keep only recent history
                if len(self.response_times[f"{method} {endpoint}"]) > self.max_history:
                    self.response_times[f"{method} {endpoint}"].pop(0)
            
            # Status codes
            if status_code:
                self.status_codes[status_code] += 1
            
            # Errors
            if error or (status_code and status_code >= 400):
                self.error_counts[f"{method} {endpoint}"] += 1
            
            # Endpoint metrics
            endpoint_key = f"{method} {endpoint}"
            if endpoint_key in self.endpoint_metrics:
                self.endpoint_metrics[endpoint_key]['total_requests'] += 1
                if response_time is not None:
                    metrics = self.endpoint_metrics[endpoint_key]
                    metrics['avg_response_time'] = (
                        (metrics['avg_response_time'] * (metrics['total_requests'] - 1) + response_time) / 
                        metrics['total_requests']
                    )
                    metrics['min_response_time'] = min(metrics['min_response_time'], response_time)
                    metrics['max_response_time'] = max(metrics['max_response_time'], response_time)
                metrics['last_request'] = datetime.utcnow()
                
                if error or (status_code and status_code >= 400):
                    metrics['total_errors'] += 1
            
            # User metrics
            if user_id:
                self.user_metrics[user_id]['total_requests'] += 1
                self.user_metrics[user_id]['last_request'] = datetime.utcnow()
                
                if error or (status_code and status_code >= 400):
                    self.user_metrics[user_id]['total_errors'] += 1
    
    def get_endpoint_metrics(self, endpoint=None, method=None):
        """Get metrics for specific endpoint or all endpoints"""
        with self.lock:
            if endpoint and method:
                key = f"{method} {endpoint}"
                return self.endpoint_metrics.get(key, {})
            elif endpoint:
                # Return metrics for all methods of an endpoint
                result = {}
                for key, metrics in self.endpoint_metrics.items():
                    if key.endswith(f" {endpoint}"):
                        result[key] = metrics
                return result
            else:
                return dict(self.endpoint_metrics)
    
    def get_user_metrics(self, user_id=None):
        """Get metrics for specific user or all users"""
        with self.lock:
            if user_id:
                return self.user_metrics.get(user_id, {})
            else:
                return dict(self.user_metrics)
    
    def get_system_metrics(self):
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_usage_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e)}
    
    def get_summary_stats(self):
        """Get summary statistics"""
        with self.lock:
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())
            
            # Calculate average response time across all endpoints
            all_response_times = []
            for times in self.response_times.values():
                all_response_times.extend(times)
            
            avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
            
            return {
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate_percent': (total_errors / total_requests * 100) if total_requests > 0 else 0,
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'unique_endpoints': len(self.endpoint_metrics),
                'unique_users': len(self.user_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def clear_metrics(self):
        """Clear all metrics"""
        with self.lock:
            self.request_counts.clear()
            self.response_times.clear()
            self.error_counts.clear()
            self.status_codes.clear()
            self.endpoint_metrics.clear()
            self.user_metrics.clear()
            logger.info("All metrics cleared")


# Global metrics collector
metrics_collector = MetricsCollector()


def monitor_request(f):
    """Decorator to monitor API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        user_id = None
        
        # Extract user ID if available
        if args and hasattr(args[0], 'id'):
            user_id = args[0].id
        
        try:
            # Execute the function
            response = f(*args, **kwargs)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract status code
            status_code = 200
            if isinstance(response, tuple):
                response_obj, status_code = response
            
            # Record metrics
            metrics_collector.record_request(
                endpoint=request.endpoint,
                method=request.method,
                user_id=user_id,
                response_time=response_time,
                status_code=status_code
            )
            
            return response
            
        except Exception as e:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record error metrics
            metrics_collector.record_request(
                endpoint=request.endpoint,
                method=request.method,
                user_id=user_id,
                response_time=response_time,
                status_code=500,
                error=str(e)
            )
            
            raise
    
    return decorated_function


def monitor_performance(threshold_ms=1000):
    """Decorator to monitor slow requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            response = f(*args, **kwargs)
            
            response_time = time.time() - start_time
            response_time_ms = response_time * 1000
            
            if response_time_ms > threshold_ms:
                logger.warning(f"Slow request detected", extra={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'response_time_ms': round(response_time_ms, 2),
                    'threshold_ms': threshold_ms,
                    'ip_address': request.remote_addr
                })
            
            return response
        
        return decorated_function
    return decorator


def health_check():
    """Basic health check endpoint"""
    try:
        # Check system resources
        system_metrics = metrics_collector.get_system_metrics()
        
        # Determine health status
        is_healthy = True
        issues = []
        
        if system_metrics.get('cpu_usage_percent', 0) > 90:
            is_healthy = False
            issues.append('High CPU usage')
        
        if system_metrics.get('memory_usage_percent', 0) > 90:
            is_healthy = False
            issues.append('High memory usage')
        
        if system_metrics.get('disk_usage_percent', 0) > 90:
            is_healthy = False
            issues.append('High disk usage')
        
        status_code = 200 if is_healthy else 503
        
        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'system_metrics': system_metrics,
            'issues': issues
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


def detailed_health_check():
    """Detailed health check with metrics"""
    try:
        summary_stats = metrics_collector.get_summary_stats()
        system_metrics = metrics_collector.get_system_metrics()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'summary_stats': summary_stats,
            'system_metrics': system_metrics,
            'endpoint_count': len(metrics_collector.get_endpoint_metrics()),
            'user_count': len(metrics_collector.get_user_metrics())
        })
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def get_metrics():
    """Get current metrics"""
    try:
        return jsonify({
            'summary': metrics_collector.get_summary_stats(),
            'endpoints': metrics_collector.get_endpoint_metrics(),
            'users': metrics_collector.get_user_metrics(),
            'system': metrics_collector.get_system_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return jsonify({'error': str(e)}), 500


def clear_metrics():
    """Clear all metrics"""
    try:
        metrics_collector.clear_metrics()
        return jsonify({'message': 'Metrics cleared successfully'})
        
    except Exception as e:
        logger.error(f"Failed to clear metrics: {e}")
        return jsonify({'error': str(e)}), 500


def configure_monitoring(app):
    """Configure monitoring for the Flask app"""
    
    # Add health check endpoints
    @app.route('/api/health', methods=['GET'])
    def basic_health_check():
        return health_check()
    
    @app.route('/api/health/detailed', methods=['GET'])
    def detailed_health():
        return detailed_health_check()
    
    # Add metrics endpoints
    @app.route('/api/metrics', methods=['GET'])
    def api_metrics():
        return get_metrics()
    
    @app.route('/api/metrics/clear', methods=['POST'])
    def clear_api_metrics():
        return clear_metrics()
    
    logger.info("Monitoring middleware configured")


# Convenience decorators
def monitor_endpoint(f):
    """Monitor specific endpoint performance"""
    return monitor_request(f)


def monitor_user_activity(f):
    """Monitor user activity patterns"""
    return monitor_request(f)


def performance_alert(threshold_ms=2000):
    """Alert on very slow requests"""
    return monitor_performance(threshold_ms)
