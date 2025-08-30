#!/usr/bin/env python3
"""
Phase 1 Integration - Legacy Adapter
Provides backward compatibility adapters for existing CLI functions
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

from .cli_wrapper import Phase1CLIWrapper, Phase1MenuSystemWrapper


class LegacyFunctionAdapter:
    """
    Adapter that provides backward compatibility for existing CLI functions.
    
    This adapter allows existing code to work unchanged while benefiting
    from Phase 1 validation and insights.
    """
    
    def __init__(self):
        """Initialize the legacy function adapter"""
        self.logger = logging.getLogger('LegacyFunctionAdapter')
        self.cli_wrapper = Phase1CLIWrapper()
        self.menu_wrapper = Phase1MenuSystemWrapper()
    
    def adapt_bridge_domain_builder(self, original_function: Callable) -> Callable:
        """
        Adapt the original bridge domain builder function.
        
        Args:
            original_function: Original bridge domain builder function
            
        Returns:
            Wrapped function with Phase 1 integration
        """
        @wraps(original_function)
        def wrapped_function(*args, **kwargs):
            try:
                # Extract parameters (assuming standard signature)
                if len(args) >= 6:
                    service_name = args[0]
                    vlan_id = args[1]
                    source_device = args[2]
                    source_interface = args[3]
                    dest_device = args[4]
                    dest_interface = args[5]
                    
                    # Use Phase 1 wrapped version
                    return self.cli_wrapper.wrapped_bridge_domain_builder(
                        service_name, vlan_id, source_device, source_interface,
                        dest_device, dest_interface
                    )
                else:
                    # Fall back to original function if signature doesn't match
                    self.logger.warning("⚠️ Falling back to original function due to signature mismatch")
                    return original_function(*args, **kwargs)
                    
            except Exception as e:
                self.logger.error(f"❌ Adapter failed, falling back to original: {e}")
                return original_function(*args, **kwargs)
        
        return wrapped_function
    
    def adapt_unified_builder(self, original_function: Callable) -> Callable:
        """
        Adapt the original unified bridge domain builder function.
        
        Args:
            original_function: Original unified builder function
            
        Returns:
            Wrapped function with Phase 1 integration
        """
        @wraps(original_function)
        def wrapped_function(*args, **kwargs):
            try:
                # Extract parameters (assuming standard signature)
                if len(args) >= 5:
                    service_name = args[0]
                    vlan_id = args[1]
                    source_device = args[2]
                    source_interface = args[3]
                    destinations = args[4]
                    
                    # Use Phase 1 wrapped version
                    return self.cli_wrapper.wrapped_unified_bridge_domain_builder(
                        service_name, vlan_id, source_device, source_interface, destinations
                    )
                else:
                    # Fall back to original function if signature doesn't match
                    self.logger.warning("⚠️ Falling back to original function due to signature mismatch")
                    return original_function(*args, **kwargs)
                    
            except Exception as e:
                self.logger.error(f"❌ Adapter failed, falling back to original: {e}")
                return original_function(*args, **kwargs)
        
        return wrapped_function
    
    def adapt_enhanced_menu_system(self, original_class):
        """
        Adapt the original enhanced menu system class.
        
        Args:
            original_class: Original EnhancedMenuSystem class
            
        Returns:
            Wrapped class with Phase 1 integration
        """
        class WrappedEnhancedMenuSystem(original_class):
            def __init__(self):
                super().__init__()
                self.phase1_wrapper = Phase1MenuSystemWrapper()
                self.logger = logging.getLogger('WrappedEnhancedMenuSystem')
            
            def run_enhanced_bridge_domain_builder(self) -> bool:
                """Override with Phase 1 integration"""
                try:
                    return self.phase1_wrapper.run_enhanced_bridge_domain_builder()
                except Exception as e:
                    self.logger.error(f"❌ Phase 1 wrapper failed, falling back to original: {e}")
                    return super().run_enhanced_bridge_domain_builder()
        
        return WrappedEnhancedMenuSystem


def phase1_enhanced(original_function: Callable) -> Callable:
    """
    Decorator to add Phase 1 enhancement to any function.
    
    This decorator can be applied to existing functions to add
    Phase 1 validation and insights without changing the function signature.
    
    Args:
        original_function: Function to enhance
        
    Returns:
        Enhanced function with Phase 1 integration
    """
    adapter = LegacyFunctionAdapter()
    
    @wraps(original_function)
    def enhanced_function(*args, **kwargs):
        logger = logging.getLogger('Phase1Enhanced')
        
        try:
            # Try to determine function type and apply appropriate wrapper
            function_name = original_function.__name__
            
            if 'bridge_domain_builder' in function_name.lower():
                if 'unified' in function_name.lower():
                    return adapter.adapt_unified_builder(original_function)(*args, **kwargs)
                else:
                    return adapter.adapt_bridge_domain_builder(original_function)(*args, **kwargs)
            else:
                # For other functions, just add logging and call original
                logger.info(f"🔧 Phase 1 enhanced: {function_name}")
                return original_function(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"❌ Phase 1 enhancement failed for {function_name}: {e}")
            return original_function(*args, **kwargs)
    
    return enhanced_function


class BackwardCompatibilityManager:
    """
    Manages backward compatibility for the entire system.
    
    This manager ensures that existing code continues to work
    while gradually introducing Phase 1 benefits.
    """
    
    def __init__(self):
        """Initialize the backward compatibility manager"""
        self.logger = logging.getLogger('BackwardCompatibilityManager')
        self.adapter = LegacyFunctionAdapter()
        self.enabled = True
    
    def enable_phase1_integration(self) -> None:
        """Enable Phase 1 integration system-wide"""
        self.enabled = True
        self.logger.info("✅ Phase 1 integration enabled system-wide")
    
    def disable_phase1_integration(self) -> None:
        """Disable Phase 1 integration (fall back to legacy)"""
        self.enabled = False
        self.logger.info("⚠️ Phase 1 integration disabled - using legacy functions")
    
    def is_phase1_enabled(self) -> bool:
        """Check if Phase 1 integration is enabled"""
        return self.enabled
    
    def wrap_existing_functions(self, module_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrap existing functions in a module with Phase 1 integration.
        
        Args:
            module_dict: Dictionary of module functions/classes
            
        Returns:
            Dictionary with wrapped functions
        """
        if not self.enabled:
            return module_dict
        
        wrapped_dict = module_dict.copy()
        
        for name, obj in module_dict.items():
            if callable(obj) and 'bridge_domain' in name.lower():
                try:
                    if 'unified' in name.lower():
                        wrapped_dict[name] = self.adapter.adapt_unified_builder(obj)
                    else:
                        wrapped_dict[name] = self.adapter.adapt_bridge_domain_builder(obj)
                    
                    self.logger.info(f"✅ Wrapped function: {name}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to wrap {name}: {e}")
                    wrapped_dict[name] = obj
        
        return wrapped_dict
    
    def get_compatibility_report(self) -> Dict[str, Any]:
        """Get compatibility status report"""
        return {
            'phase1_enabled': self.enabled,
            'adapter_available': self.adapter is not None,
            'cli_wrapper_available': hasattr(self.adapter, 'cli_wrapper'),
            'menu_wrapper_available': hasattr(self.adapter, 'menu_wrapper'),
            'status': 'active' if self.enabled else 'disabled'
        }


# Global compatibility manager instance
compatibility_manager = BackwardCompatibilityManager()

