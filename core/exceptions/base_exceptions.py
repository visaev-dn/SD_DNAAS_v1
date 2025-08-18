#!/usr/bin/env python3
"""
Base Exception Classes
Foundation exception classes for the Lab Automation Framework
"""

from typing import Optional, Dict, Any, List


class LabAutomationError(Exception):
    """
    Base exception class for all Lab Automation Framework errors.
    
    This provides a common base for all custom exceptions in the system,
    allowing for consistent error handling and logging.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, 
                 original_exception: Optional[Exception] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
            original_exception: Optional original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = self._get_timestamp()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for error tracking"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }
    
    def __str__(self) -> str:
        """String representation of the exception"""
        base = f"{self.__class__.__name__}: {self.message}"
        if self.error_code:
            base += f" (Code: {self.error_code})"
        if self.details:
            base += f" - Details: {self.details}"
        return base


class ConfigurationError(LabAutomationError):
    """Raised when there's a configuration-related error"""
    pass


class ValidationError(LabAutomationError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field_errors: Optional[List[str]] = None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_errors: List of field-specific validation errors
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including field errors"""
        base_dict = super().to_dict()
        base_dict['field_errors'] = self.field_errors
        return base_dict


class ServiceError(LabAutomationError):
    """Base exception for service-related errors"""
    pass


class InfrastructureError(LabAutomationError):
    """Base exception for infrastructure-related errors (database, network, etc.)"""
    pass


class BusinessLogicError(LabAutomationError):
    """Base exception for business logic errors"""
    pass


class AuthenticationError(LabAutomationError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(LabAutomationError):
    """Raised when authorization fails (insufficient permissions)"""
    pass


class ResourceNotFoundError(LabAutomationError):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        """
        Initialize resource not found error.
        
        Args:
            resource_type: Type of resource (e.g., 'device', 'service', 'user')
            resource_id: ID of the resource that was not found
            **kwargs: Additional arguments for base class
        """
        message = f"{resource_type.capitalize()} with ID '{resource_id}' not found"
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConnectionError(InfrastructureError):
    """Raised when connection to external service/device fails"""
    
    def __init__(self, service_name: str, connection_details: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize connection error.
        
        Args:
            service_name: Name of the service/device that failed to connect
            connection_details: Optional connection details for debugging
            **kwargs: Additional arguments for base class
        """
        message = f"Failed to connect to {service_name}"
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.connection_details = connection_details or {}


class TimeoutError(InfrastructureError):
    """Raised when an operation times out"""
    
    def __init__(self, operation: str, timeout_seconds: float, **kwargs):
        """
        Initialize timeout error.
        
        Args:
            operation: Description of the operation that timed out
            timeout_seconds: Timeout value in seconds
            **kwargs: Additional arguments for base class
        """
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, **kwargs)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class DataIntegrityError(InfrastructureError):
    """Raised when data integrity is compromised"""
    pass


class ExternalServiceError(InfrastructureError):
    """Raised when an external service returns an error"""
    
    def __init__(self, service_name: str, service_response: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize external service error.
        
        Args:
            service_name: Name of the external service
            service_response: Optional response from the external service
            **kwargs: Additional arguments for base class
        """
        message = f"External service '{service_name}' returned an error"
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.service_response = service_response or {}
