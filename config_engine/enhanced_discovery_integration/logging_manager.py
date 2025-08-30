#!/usr/bin/env python3
"""
Enhanced Discovery Logging Manager

Provides comprehensive logging and monitoring for enhanced discovery integration
with structured logging, performance metrics, and operation tracking.
"""

import logging
import logging.handlers
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
import uuid


@dataclass
class OperationLog:
    """Structured operation log entry"""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = "running"  # running, completed, failed, cancelled
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    record_count: int = 0
    source_system: str = "legacy"
    target_system: str = "enhanced_database"


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_type: str
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    total_records_processed: int = 0
    average_records_per_operation: float = 0.0


class EnhancedDiscoveryLoggingManager:
    """Enhanced logging for enhanced discovery integration"""
    
    def __init__(self, log_level: str = 'INFO', log_dir: str = 'logs'):
        self.log_level = log_level
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Operation tracking
        self.operation_log: List[OperationLog] = []
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.current_operations: Dict[str, OperationLog] = {}
        
        # Performance tracking
        self.start_time = time.time()
        self.total_operations = 0
        self.total_records_processed = 0
        
        self.logger.info("🚀 Enhanced Discovery Logging Manager initialized")
    
    def setup_logging(self):
        """Set up comprehensive logging configuration"""
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create handlers
        # File handler for detailed logs
        detailed_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'enhanced_discovery_detailed.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        detailed_handler.setLevel(logging.DEBUG)
        detailed_handler.setFormatter(detailed_formatter)
        
        # File handler for operation logs
        operation_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'enhanced_discovery_operations.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        operation_handler.setLevel(logging.INFO)
        operation_handler.setFormatter(detailed_formatter)
        
        # File handler for performance logs
        performance_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'enhanced_discovery_performance.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(simple_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level.upper()))
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our handlers
        root_logger.addHandler(detailed_handler)
        root_logger.addHandler(operation_handler)
        root_logger.addHandler(performance_handler)
        root_logger.addHandler(console_handler)
        
        # Set specific logger levels
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Create specific loggers for different components
        self.operation_logger = logging.getLogger('enhanced_discovery.operations')
        self.performance_logger = logging.getLogger('enhanced_discovery.performance')
        self.data_logger = logging.getLogger('enhanced_discovery.data')
        
        self.logger.info("📝 Enhanced Discovery logging configured successfully")
    
    def start_operation(self, operation_id: Optional[str] = None, operation_type: str = "operation", details: Dict[str, Any] = None) -> str:
        """Start tracking a new operation. If operation_id is None, generate one."""
        
        op_id = operation_id or str(uuid.uuid4())
        operation = OperationLog(
            operation_id=op_id,
            operation_type=operation_type,
            start_time=datetime.now(),
            details=details or {},
            source_system=details.get('source_system', 'legacy') if details else 'legacy',
            target_system=details.get('target_system', 'enhanced_database') if details else 'enhanced_database'
        )
        
        self.current_operations[op_id] = operation
        self.operation_log.append(operation)
        self.total_operations += 1
        
        self.operation_logger.info(f"🚀 Operation started: {operation_type} (ID: {op_id})")
        self.operation_logger.debug(f"Operation details: {details}")
        
        return op_id
    
    def update_operation(self, operation_id: str, updates: Dict[str, Any]):
        """Update operation details during execution"""
        
        if operation_id in self.current_operations:
            operation = self.current_operations[operation_id]
            
            for key, value in updates.items():
                if hasattr(operation, key):
                    setattr(operation, key, value)
            
            self.operation_logger.debug(f"Operation {operation_id} updated: {updates}")
    
    def complete_operation(self, operation_id: str, status: str = "completed", 
                          error_message: str = None, record_count: int = 0):
        """Mark operation as completed"""
        
        if operation_id in self.current_operations:
            operation = self.current_operations[operation_id]
            operation.end_time = datetime.now()
            operation.duration = (operation.end_time - operation.start_time).total_seconds()
            operation.status = status
            operation.error_message = error_message
            operation.record_count = record_count
            
            # Update performance metrics
            self._update_performance_metrics(operation)
            
            # Log completion
            if status == "completed":
                self.operation_logger.info(
                    f"✅ Operation completed: {operation.operation_type} "
                    f"(ID: {operation_id}, Duration: {operation.duration:.2f}s, "
                    f"Records: {record_count})"
                )
            elif status == "failed":
                self.operation_logger.error(
                    f"❌ Operation failed: {operation.operation_type} "
                    f"(ID: {operation_id}, Duration: {operation.duration:.2f}s, "
                    f"Error: {error_message})"
                )
            
            # Remove from current operations
            del self.current_operations[operation_id]
            
            # Update total records
            self.total_records_processed += record_count
    
    def log_discovery_operation(self, operation: str, details: Dict):
        """Log enhanced discovery operation with structured details"""
        
        self.logger.info(f"🔍 Enhanced Discovery Operation: {operation}")
        self.logger.debug(f"Operation details: {json.dumps(details, indent=2, default=str)}")
        
        # Log to operation-specific logger
        self.operation_logger.info(f"Discovery operation: {operation}")
        self.operation_logger.debug(f"Details: {details}")
    
    def log_data_conversion(self, source: str, target: str, success: bool, details: Dict):
        """Log data conversion operations to Enhanced Database"""
        
        status_icon = "✅" if success else "❌"
        status_text = "SUCCESS" if success else "FAILED"
        
        self.data_logger.info(
            f"{status_icon} Data conversion: {source} → {target} [{status_text}]"
        )
        self.data_logger.debug(f"Conversion details: {json.dumps(details, indent=2, default=str)}")
        
        # Log to main logger
        self.logger.info(f"Data conversion: {source} → {target} [{status_text}]")
    
    def log_database_operation(self, operation: str, table: str, record_count: int, duration: float):
        """Log Enhanced Database operations with performance metrics"""
        
        self.logger.info(
            f"🗄️ Database operation: {operation} on {table} "
            f"({record_count} records, {duration:.2f}s)"
        )
        
        # Log to performance logger
        self.performance_logger.info(
            f"Database operation: {operation} | Table: {table} | "
            f"Records: {record_count} | Duration: {duration:.2f}s"
        )
        
        # Log to operation logger
        self.operation_logger.info(
            f"Database operation completed: {operation} on {table}"
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log specific performance metrics"""
        
        self.performance_logger.info(f"Performance metric: {metric_name} = {value}{unit}")
        
        # Also log to main logger for visibility
        self.logger.info(f"📊 Performance: {metric_name} = {value}{unit}")
    
    def _update_performance_metrics(self, operation: OperationLog):
        """Update performance metrics for an operation"""
        
        operation_type = operation.operation_type
        
        if operation_type not in self.performance_metrics:
            self.performance_metrics[operation_type] = PerformanceMetrics(
                operation_type=operation_type
            )
        
        metrics = self.performance_metrics[operation_type]
        metrics.total_operations += 1
        
        if operation.status == "completed":
            metrics.successful_operations += 1
        elif operation.status == "failed":
            metrics.failed_operations += 1
        
        if operation.duration is not None:
            metrics.total_duration += operation.duration
            metrics.average_duration = metrics.total_duration / metrics.total_operations
            metrics.min_duration = min(metrics.min_duration, operation.duration)
            metrics.max_duration = max(metrics.max_duration, operation.duration)
        
        if operation.record_count > 0:
            metrics.total_records_processed += operation.record_count
            metrics.average_records_per_operation = (
                metrics.total_records_processed / metrics.total_operations
            )
    
    def generate_operation_summary(self) -> Dict[str, Any]:
        """Generate comprehensive operation summary"""
        
        # Calculate overall statistics
        total_duration = sum(
            op.duration for op in self.operation_log if op.duration is not None
        )
        
        completed_operations = [op for op in self.operation_log if op.status == "completed"]
        failed_operations = [op for op in self.operation_log if op.status == "failed"]
        
        summary = {
            'total_operations': len(self.operation_log),
            'completed_operations': len(completed_operations),
            'failed_operations': len(failed_operations),
            'running_operations': len(self.current_operations),
            'total_duration': total_duration,
            'average_duration': total_duration / len(self.operation_log) if self.operation_log else 0,
            'total_records_processed': self.total_records_processed,
            'uptime': time.time() - self.start_time,
            'performance_metrics': {
                op_type: asdict(metrics) 
                for op_type, metrics in self.performance_metrics.items()
            },
            'recent_operations': [
                {
                    'operation_id': op.operation_id,
                    'operation_type': op.operation_type,
                    'status': op.status,
                    'duration': op.duration,
                    'record_count': op.record_count,
                    'start_time': op.start_time.isoformat(),
                    'end_time': op.end_time.isoformat() if op.end_time else None
                }
                for op in self.operation_log[-10:]  # Last 10 operations
            ]
        }
        
        return summary
    
    def export_operation_logs(self, output_file: str = None) -> str:
        """Export operation logs to JSON file"""
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.log_dir / f'enhanced_discovery_operations_{timestamp}.json'
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'summary': self.generate_operation_summary(),
            'operations': [
                {
                    'operation_id': op.operation_id,
                    'operation_type': op.operation_type,
                    'start_time': op.start_time.isoformat(),
                    'end_time': op.end_time.isoformat() if op.end_time else None,
                    'duration': op.duration,
                    'status': op.status,
                    'details': op.details,
                    'error_message': op.error_message,
                    'record_count': op.record_count,
                    'source_system': op.source_system,
                    'target_system': op.target_system
                }
                for op in self.operation_log
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"📤 Operation logs exported to: {output_file}")
        return str(output_file)
    
    def clear_operation_logs(self):
        """Clear all operation logs"""
        
        self.operation_log.clear()
        self.current_operations.clear()
        self.performance_metrics.clear()
        self.total_operations = 0
        self.total_records_processed = 0
        self.start_time = time.time()
        
        self.logger.info("🗑️ Operation logs cleared")
    
    def get_current_operations(self) -> List[Dict[str, Any]]:
        """Get list of currently running operations"""
        
        return [
            {
                'operation_id': op.operation_id,
                'operation_type': op.operation_type,
                'start_time': op.start_time.isoformat(),
                'duration': (datetime.now() - op.start_time).total_seconds(),
                'details': op.details
            }
            for op in self.current_operations.values()
        ]
    
    def get_operation_by_id(self, operation_id: str) -> Optional[OperationLog]:
        """Get operation details by ID"""
        
        # Check current operations first
        if operation_id in self.current_operations:
            return self.current_operations[operation_id]
        
        # Check completed operations
        for operation in self.operation_log:
            if operation.operation_id == operation_id:
                return operation
        
        return None
