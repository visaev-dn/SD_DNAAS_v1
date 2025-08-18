#!/usr/bin/env python3
"""
Configuration Manager
Centralized configuration management for the Lab Automation Framework
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from ..exceptions.base_exceptions import ConfigurationError
from ..logging.logger_factory import get_logger


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    name: str = "lab_automation.db"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None


@dataclass
class APIConfig:
    """API server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "lab-automation-secret-key-2024"
    cors_enabled: bool = True
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100


@dataclass
class SSHConfig:
    """SSH connection configuration settings"""
    default_timeout: int = 30
    default_retry_attempts: int = 3
    connection_pool_size: int = 10
    max_concurrent_connections: int = 50
    key_based_auth_enabled: bool = True
    password_auth_enabled: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_logging: bool = True
    file_logging: bool = True


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    jwt_secret: str = "lab-automation-jwt-secret-2024"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    password_require_special_chars: bool = True
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


@dataclass
class AppConfig:
    """Main application configuration"""
    app_name: str = "Lab Automation Framework"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    ssh: SSHConfig = field(default_factory=SSHConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Custom configuration sections
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """
    Centralized configuration management for the Lab Automation Framework.
    
    This class handles loading configuration from multiple sources:
    - Environment variables
    - Configuration files (YAML/JSON)
    - Default values
    - Command line arguments
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger(__name__)
        self.config_path = config_path or self._find_config_file()
        self.config = AppConfig()
        self._loaded = False
        
        # Load configuration
        self.load_configuration()
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in common locations"""
        search_paths = [
            "config.yaml",
            "config.yml", 
            "config.json",
            "lab_automation.yaml",
            "lab_automation.yml",
            "lab_automation.json",
            "config/config.yaml",
            "config/config.yml",
            "config/config.json"
        ]
        
        for path in search_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def load_configuration(self) -> None:
        """Load configuration from all sources"""
        try:
            # Load from file if available
            if self.config_path:
                self._load_from_file()
            
            # Override with environment variables
            self._load_from_environment()
            
            # Validate configuration
            self._validate_configuration()
            
            self._loaded = True
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use default configuration
            self.logger.info("Using default configuration")
    
    def _load_from_file(self) -> None:
        """Load configuration from file"""
        if not self.config_path:
            return
        
        try:
            file_path = Path(self.config_path)
            if not file_path.exists():
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    self.logger.warning(f"Unsupported configuration file format: {file_path.suffix}")
                    return
            
            # Apply file configuration
            self._apply_file_config(file_config)
            self.logger.info(f"Configuration loaded from file: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration file {self.config_path}: {e}")
            raise ConfigurationError(f"Failed to load configuration file: {e}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        # Environment variable prefix
        prefix = "LAB_AUTOMATION_"
        
        # Map environment variables to configuration
        env_mappings = {
            f"{prefix}ENVIRONMENT": ("environment", str),
            f"{prefix}DEBUG": ("debug", bool),
            f"{prefix}DB_TYPE": ("database.type", str),
            f"{prefix}DB_HOST": ("database.host", str),
            f"{prefix}DB_PORT": ("database.port", int),
            f"{prefix}DB_NAME": ("database.name", str),
            f"{prefix}DB_USERNAME": ("database.username", str),
            f"{prefix}DB_PASSWORD": ("database.password", str),
            f"{prefix}API_HOST": ("api.host", str),
            f"{prefix}API_PORT": ("api.port", int),
            f"{prefix}API_SECRET_KEY": ("api.secret_key", str),
            f"{prefix}SSH_TIMEOUT": ("ssh.default_timeout", int),
            f"{prefix}SSH_RETRY_ATTEMPTS": ("ssh.default_retry_attempts", int),
            f"{prefix}LOG_LEVEL": ("logging.level", str),
            f"{prefix}LOG_DIR": ("logging.log_dir", str),
            f"{prefix}JWT_SECRET": ("security.jwt_secret", str),
            f"{prefix}JWT_EXPIRATION_HOURS": ("security.jwt_expiration_hours", int),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert value to appropriate type
                    if value_type == bool:
                        converted_value = value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        converted_value = int(value)
                    else:
                        converted_value = value
                    
                    # Set configuration value
                    self._set_nested_config_value(config_path, converted_value)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid environment variable {env_var}={value}: {e}")
    
    def _apply_file_config(self, file_config: Dict[str, Any]) -> None:
        """Apply configuration from file to config object"""
        if not file_config:
            return
        
        # Apply top-level configuration
        for key, value in file_config.items():
            if hasattr(self.config, key):
                if isinstance(value, dict) and hasattr(getattr(self.config, key), '__dict__'):
                    # Nested configuration object
                    self._update_nested_config(getattr(self.config, key), value)
                else:
                    # Simple value
                    setattr(self.config, key, value)
            else:
                # Custom configuration
                self.config.custom[key] = value
    
    def _update_nested_config(self, config_obj: Any, config_dict: Dict[str, Any]) -> None:
        """Update nested configuration object"""
        for key, value in config_dict.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def _set_nested_config_value(self, config_path: str, value: Any) -> None:
        """Set nested configuration value using dot notation"""
        parts = config_path.split('.')
        current = self.config
        
        # Navigate to parent object
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                self.logger.warning(f"Configuration path not found: {config_path}")
                return
        
        # Set value on final object
        if hasattr(current, parts[-1]):
            setattr(current, parts[-1], value)
        else:
            self.logger.warning(f"Configuration property not found: {parts[-1]}")
    
    def _validate_configuration(self) -> None:
        """Validate loaded configuration"""
        # Basic validation
        if self.config.database.port < 1 or self.config.database.port > 65535:
            raise ConfigurationError("Database port must be between 1 and 65535")
        
        if self.config.api.port < 1 or self.config.api.port > 65535:
            raise ConfigurationError("API port must be between 1 and 65535")
        
        if self.config.ssh.default_timeout < 1:
            raise ConfigurationError("SSH timeout must be positive")
        
        if self.config.ssh.default_retry_attempts < 0:
            raise ConfigurationError("SSH retry attempts must be non-negative")
        
        if self.config.security.password_min_length < 1:
            raise ConfigurationError("Password minimum length must be positive")
        
        self.logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested access)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self._get_nested_config_value(key)
        except (AttributeError, KeyError):
            return default
    
    def _get_nested_config_value(self, key: str) -> Any:
        """Get nested configuration value using dot notation"""
        parts = key.split('.')
        current = self.config
        
        for part in parts:
            if isinstance(current, dict):
                current = current[part]
            else:
                current = getattr(current, part)
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested access)
            value: Value to set
        """
        self._set_nested_config_value(key, value)
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.config.database.connection_string:
            return self.config.database.connection_string
        
        if self.config.database.type.lower() == "sqlite":
            return f"sqlite:///{self.config.database.name}"
        elif self.config.database.type.lower() == "postgresql":
            auth = ""
            if self.config.database.username and self.config.database.password:
                auth = f"{self.config.database.username}:{self.config.database.password}@"
            elif self.config.database.username:
                auth = f"{self.config.database.username}@"
            
            return f"postgresql://{auth}{self.config.database.host}:{self.config.database.port}/{self.config.database.name}"
        else:
            raise ConfigurationError(f"Unsupported database type: {self.config.database.type}")
    
    def save_configuration(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: Optional file path (uses current config_path if not specified)
        """
        save_path = file_path or self.config_path
        if not save_path:
            raise ConfigurationError("No configuration file path specified")
        
        try:
            # Convert configuration to dictionary
            config_dict = self._config_to_dict()
            
            # Save to file
            file_path = Path(save_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
            
            self.logger.info(f"Configuration saved to: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration object to dictionary"""
        config_dict = {}
        
        # Convert main configuration
        for field in self.config.__dataclass_fields__:
            value = getattr(self.config, field)
            if hasattr(value, '__dict__') and not isinstance(value, dict):
                # Nested configuration object
                config_dict[field] = self._object_to_dict(value)
            else:
                config_dict[field] = value
        
        return config_dict
    
    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary"""
        if hasattr(obj, '__dict__'):
            return {key: value for key, value in obj.__dict__.items()}
        return obj
    
    def reload(self) -> None:
        """Reload configuration from all sources"""
        self._loaded = False
        self.load_configuration()
    
    def is_loaded(self) -> bool:
        """Check if configuration is loaded"""
        return self._loaded
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self._config_to_dict()


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value by key"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set configuration value by key"""
    get_config_manager().set(key, value)
