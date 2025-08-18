#!/usr/bin/env python3
"""
User Workflow Service Interface
Abstract base class defining the contract for user workflow operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """Represents a step in a user workflow"""
    step_id: str
    step_name: str
    step_type: str  # "input", "validation", "execution", "confirmation"
    required: bool = True
    depends_on: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowDefinition:
    """Definition of a complete user workflow"""
    workflow_id: str
    workflow_name: str
    description: str
    steps: List[WorkflowStep]
    version: str = "1.0"
    category: str = "general"


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    success: bool
    workflow_id: str
    step_results: Optional[Dict[str, Any]] = None
    final_result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class UserWorkflowService(ABC):
    """
    Abstract base class for user workflow services.
    
    This interface defines the contract that all user workflow services
    must implement, ensuring consistency across different implementations.
    """
    
    @abstractmethod
    def create_workflow(self, definition: WorkflowDefinition) -> bool:
        """
        Create a new user workflow.
        
        Args:
            definition: WorkflowDefinition containing workflow details
            
        Returns:
            True if workflow created successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def execute_workflow(self, workflow_id: str, user_inputs: Dict[str, Any]) -> WorkflowExecutionResult:
        """
        Execute a user workflow with provided inputs.
        
        Args:
            workflow_id: ID of the workflow to execute
            user_inputs: Dictionary of user inputs for the workflow
            
        Returns:
            WorkflowExecutionResult with execution status and results
        """
        pass
    
    @abstractmethod
    def get_available_workflows(self) -> List[WorkflowDefinition]:
        """
        Get list of available workflows.
        
        Returns:
            List of available WorkflowDefinition objects
        """
        pass
    
    @abstractmethod
    def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get definition of a specific workflow.
        
        Args:
            workflow_id: ID of the workflow to retrieve
            
        Returns:
            WorkflowDefinition if found, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_workflow_inputs(self, workflow_id: str, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate inputs for a workflow before execution.
        
        Args:
            workflow_id: ID of the workflow to validate inputs for
            inputs: Dictionary of inputs to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def get_workflow_execution_history(self, workflow_id: str) -> List[WorkflowExecutionResult]:
        """
        Get execution history for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            List of WorkflowExecutionResult objects
        """
        pass
    
    @abstractmethod
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing workflow definition.
        
        Args:
            workflow_id: ID of the workflow to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow definition.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflow usage and performance.
        
        Returns:
            Dictionary containing workflow statistics
        """
        pass
    
    @abstractmethod
    def export_workflow(self, workflow_id: str, format_type: str = "json") -> str:
        """
        Export workflow definition in specified format.
        
        Args:
            workflow_id: ID of the workflow to export
            format_type: Export format ("json", "yaml", "xml", etc.)
            
        Returns:
            String representation of exported workflow
        """
        pass
