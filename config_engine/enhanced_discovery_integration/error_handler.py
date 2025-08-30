#!/usr/bin/env python3
"""
Enhanced Discovery Error Handler

Provides comprehensive error handling for enhanced discovery integration
with automatic error diagnosis and recovery suggestions.
"""

import logging
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


class EnhancedDiscoveryError(Exception):
    """Base class for enhanced discovery-related errors"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "ENHANCED_DISCOVERY_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()


class EnhancedDataConversionError(EnhancedDiscoveryError):
    """Error during data conversion from legacy to Enhanced Database"""
    
    def __init__(self, message: str, source_format: str = None, target_format: str = None, context: Dict = None):
        super().__init__(message, "DATA_CONVERSION_ERROR", context)
        self.source_format = source_format
        self.target_format = target_format


class EnhancedValidationError(EnhancedDiscoveryError):
    """Error during Enhanced Database data validation"""
    
    def __init__(self, message: str, field_name: str = None, validation_rule: str = None, context: Dict = None):
        super().__init__(message, "VALIDATION_ERROR", context)
        self.field_name = field_name
        self.validation_rule = validation_rule


class EnhancedDatabasePopulationError(EnhancedDiscoveryError):
    """Error during Enhanced Database population"""
    
    def __init__(self, message: str, operation: str = None, table_name: str = None, context: Dict = None):
        super().__init__(message, "DATABASE_POPULATION_ERROR", context)
        self.operation = operation
        self.table_name = table_name


class EnhancedMigrationError(EnhancedDiscoveryError):
    """Error during legacy data migration to Enhanced Database"""
    
    def __init__(self, message: str, migration_step: str = None, legacy_data_type: str = None, context: Dict = None):
        super().__init__(message, "MIGRATION_ERROR", context)
        self.migration_step = migration_step
        self.legacy_data_type = legacy_data_type


class EnhancedDatabaseMigrationError(EnhancedDiscoveryError):
    """Error during Enhanced Database migration operations"""
    
    def __init__(self, message: str, migration_type: str = None, source_system: str = None, context: Dict = None):
        super().__init__(message, "DATABASE_MIGRATION_ERROR", context)
        self.migration_type = migration_type
        self.source_system = source_system


@dataclass
class ErrorContext:
    """Structured error context information"""
    operation_id: str
    source_system: str
    target_system: str
    data_type: str
    record_count: int = 0
    processing_time: float = 0.0
    error_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryAction:
    """Recovery action suggestion"""
    action_type: str
    description: str
    priority: int  # 1=Critical, 2=High, 3=Medium, 4=Low
    commands: List[str] = field(default_factory=list)
    manual_steps: List[str] = field(default_factory=list)


class EnhancedDiscoveryErrorHandler:
    """Comprehensive error handling for enhanced discovery integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_log: List[EnhancedDiscoveryError] = []
        self.warning_log: List[Dict[str, Any]] = []
        self.recovery_actions: List[RecoveryAction] = []
        self.error_contexts: List[ErrorContext] = []
        
        # Initialize recovery action templates
        self._initialize_recovery_actions()
    
    def _initialize_recovery_actions(self):
        """Initialize common recovery action templates"""
        
        # Data conversion recovery actions
        self.recovery_actions.extend([
            RecoveryAction(
                action_type="data_validation",
                description="Validate source data format and structure",
                priority=1,
                manual_steps=[
                    "Check source file format (XML, YAML, JSON)",
                    "Verify required fields are present",
                    "Check data type consistency"
                ]
            ),
            RecoveryAction(
                action_type="schema_compatibility",
                description="Check Enhanced Database schema compatibility",
                priority=1,
                manual_steps=[
                    "Review Phase 1 data structure requirements",
                    "Check field mappings between legacy and enhanced formats",
                    "Validate enum values and constraints"
                ]
            ),
            RecoveryAction(
                action_type="data_cleansing",
                description="Clean and normalize source data",
                priority=2,
                manual_steps=[
                    "Remove invalid characters",
                    "Normalize field values",
                    "Handle missing or null values"
                ]
            )
        ])
        
        # Database population recovery actions
        self.recovery_actions.extend([
            RecoveryAction(
                action_type="database_connectivity",
                description="Check Enhanced Database connectivity",
                priority=1,
                commands=[
                    "python3 -c 'from config_engine.phase1_database import create_phase1_database_manager; db = create_phase1_database_manager(); print(\"✅ Connected\")'"
                ],
                manual_steps=[
                    "Verify database file exists and is accessible",
                    "Check database permissions",
                    "Validate database schema"
                ]
            ),
            RecoveryAction(
                action_type="data_integrity",
                description="Validate data integrity constraints",
                priority=2,
                manual_steps=[
                    "Check foreign key relationships",
                    "Validate unique constraints",
                    "Review transaction logs"
                ]
            ),
            RecoveryAction(
                action_type="rollback_operation",
                description="Rollback failed database operations",
                priority=1,
                manual_steps=[
                    "Identify failed transaction",
                    "Restore from backup if available",
                    "Clear partial data entries"
                ]
            )
        ])
        
        # Migration recovery actions
        self.recovery_actions.extend([
            RecoveryAction(
                action_type="legacy_data_validation",
                description="Validate legacy data before migration",
                priority=1,
                manual_steps=[
                    "Check legacy data format",
                    "Verify data completeness",
                    "Validate data relationships"
                ]
            ),
            RecoveryAction(
                action_type="migration_mapping",
                description="Review migration mapping rules",
                priority=2,
                manual_steps=[
                    "Check field mapping configuration",
                    "Verify data type conversions",
                    "Review transformation rules"
                ]
            ),
            RecoveryAction(
                action_type="rollback_migration",
                description="Rollback failed migration",
                priority=1,
                manual_steps=[
                    "Stop migration process",
                    "Clear migrated data",
                    "Restore original legacy data"
                ]
            )
        ])
    
    def handle_conversion_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle data conversion errors with recovery suggestions"""
        
        error_context = ErrorContext(
            operation_id=context.get('operation_id', 'unknown'),
            source_system=context.get('source_system', 'legacy'),
            target_system='enhanced_database',
            data_type=context.get('data_type', 'unknown'),
            record_count=context.get('record_count', 0),
            processing_time=context.get('processing_time', 0.0),
            error_context=context
        )
        
        # Log the error
        self.logger.error(f"Data conversion error: {error}")
        self.logger.error(f"Context: {context}")
        
        # Create enhanced error
        if isinstance(error, EnhancedDataConversionError):
            enhanced_error = error
        else:
            enhanced_error = EnhancedDataConversionError(
                message=str(error),
                source_format=context.get('source_format'),
                target_format='enhanced_database',
                context=context
            )
        
        self.error_log.append(enhanced_error)
        self.error_contexts.append(error_context)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions('data_conversion', context)
        
        return {
            'error_type': 'data_conversion_error',
            'error_message': str(error),
            'error_code': enhanced_error.error_code,
            'context': context,
            'recovery_suggestions': recovery_suggestions,
            'timestamp': enhanced_error.timestamp.isoformat()
        }
    
    def handle_validation_error(self, error: Exception, data: Any) -> Dict[str, Any]:
        """Handle validation errors with data correction suggestions"""
        
        error_context = ErrorContext(
            operation_id='validation',
            source_system='data_conversion',
            target_system='enhanced_database',
            data_type=str(type(data)),
            record_count=1,
            error_context={'data_sample': str(data)[:200]}
        )
        
        # Log the error
        self.logger.error(f"Validation error: {error}")
        self.logger.error(f"Data sample: {str(data)[:200]}")
        
        # Create enhanced error
        if isinstance(error, EnhancedValidationError):
            enhanced_error = error
        else:
            enhanced_error = EnhancedValidationError(
                message=str(error),
                context={'data_sample': str(data)[:200]}
            )
        
        self.error_log.append(enhanced_error)
        self.error_contexts.append(error_context)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions('validation', {'data_type': str(type(data))})
        
        return {
            'error_type': 'validation_error',
            'error_message': str(error),
            'error_code': enhanced_error.error_code,
            'recovery_suggestions': recovery_suggestions,
            'timestamp': enhanced_error.timestamp.isoformat()
        }
    
    def handle_database_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Handle database population errors with rollback options"""
        
        error_context = ErrorContext(
            operation_id=operation,
            source_system='enhanced_discovery',
            target_system='enhanced_database',
            data_type='database_operation',
            error_context={'operation': operation}
        )
        
        # Log the error
        self.logger.error(f"Database operation error: {error}")
        self.logger.error(f"Operation: {operation}")
        
        # Create enhanced error
        if isinstance(error, EnhancedDatabasePopulationError):
            enhanced_error = error
        else:
            enhanced_error = EnhancedDatabasePopulationError(
                message=str(error),
                operation=operation
            )
        
        self.error_log.append(enhanced_error)
        self.error_contexts.append(error_context)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions('database_operation', {'operation': operation})
        
        return {
            'error_type': 'database_operation_error',
            'error_message': str(error),
            'error_code': enhanced_error.error_code,
            'operation': operation,
            'recovery_suggestions': recovery_suggestions,
            'timestamp': enhanced_error.timestamp.isoformat()
        }
    
    def _generate_recovery_suggestions(self, error_type: str, context: Dict) -> List[RecoveryAction]:
        """Generate recovery action suggestions based on error type and context"""
        
        suggestions = []
        
        if error_type == 'data_conversion':
            suggestions.extend([
                action for action in self.recovery_actions 
                if action.action_type in ['data_validation', 'schema_compatibility', 'data_cleansing']
            ])
        elif error_type == 'validation':
            suggestions.extend([
                action for action in self.recovery_actions 
                if action.action_type in ['data_validation', 'schema_compatibility']
            ])
        elif error_type == 'database_operation':
            suggestions.extend([
                action for action in self.recovery_actions 
                if action.action_type in ['database_connectivity', 'data_integrity', 'rollback_operation']
            ])
        elif error_type == 'migration':
            suggestions.extend([
                action for action in self.recovery_actions 
                if action.action_type in ['legacy_data_validation', 'migration_mapping', 'rollback_migration']
            ])
        
        # Sort by priority (lower number = higher priority)
        suggestions.sort(key=lambda x: x.priority)
        
        return suggestions
    
    def generate_troubleshooting_report(self) -> str:
        """Generate comprehensive troubleshooting report"""
        
        report = []
        report.append("🔍 Enhanced Discovery Troubleshooting Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Error Summary
        if self.error_log:
            report.append("❌ Errors Found:")
            for error in self.error_log:
                report.append(f"  • {error.error_code}: {error.message}")
                report.append(f"    Timestamp: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                if error.context:
                    report.append(f"    Context: {error.context}")
                report.append("")
        else:
            report.append("✅ No errors found")
            report.append("")
        
        # Warning Summary
        if self.warning_log:
            report.append("⚠️ Warnings:")
            for warning in self.warning_log:
                report.append(f"  • {warning.get('message', 'Unknown warning')}")
            report.append("")
        
        # Recovery Actions
        if self.recovery_actions:
            report.append("🛠️ Available Recovery Actions:")
            for action in sorted(self.recovery_actions, key=lambda x: x.priority):
                priority_text = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}[action.priority]
                report.append(f"  • [{priority_text}] {action.description}")
                if action.manual_steps:
                    report.append("    Manual Steps:")
                    for step in action.manual_steps:
                        report.append(f"      - {step}")
                if action.commands:
                    report.append("    Commands:")
                    for cmd in action.commands:
                        report.append(f"      $ {cmd}")
                report.append("")
        
        # Context Information
        if self.error_contexts:
            report.append("📊 Operation Context:")
            for ctx in self.error_contexts:
                report.append(f"  • Operation: {ctx.operation_id}")
                report.append(f"    Source: {ctx.source_system} → Target: {ctx.target_system}")
                report.append(f"    Data Type: {ctx.data_type}")
                report.append(f"    Records: {ctx.record_count}")
                report.append(f"    Processing Time: {ctx.processing_time:.2f}s")
                report.append("")
        
        return "\n".join(report)
    
    def clear_error_log(self):
        """Clear all error logs"""
        self.error_log.clear()
        self.warning_log.clear()
        self.error_contexts.clear()
        self.logger.info("Error logs cleared")
    
    def handle_compatibility_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Handle compatibility-related errors"""
        
        error_context = {
            'operation': operation,
            'error_type': 'compatibility_error',
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the error
        self.logger.error(f"Compatibility error in {operation}: {error}")
        
        # Create recovery suggestions
        recovery_suggestions = self._get_recovery_suggestions('compatibility')
        
        return {
            'error_handled': True,
            'error_type': 'compatibility_error',
            'error_context': error_context,
            'recovery_suggestions': recovery_suggestions,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        
        error_types = {}
        for error in self.error_log:
            error_type = error.__class__.__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'total_warnings': len(self.warning_log),
            'error_types': error_types,
            'last_error_time': self.error_log[-1].timestamp.isoformat() if self.error_log else None,
            'error_contexts_count': len(self.error_contexts)
        }
