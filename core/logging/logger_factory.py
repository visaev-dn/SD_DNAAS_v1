#!/usr/bin/env python3
"""
Logger Factory
Centralized logging configuration for the Lab Automation Framework
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class LoggerFactory:
    """
    Factory class for creating and configuring loggers.
    
    This provides consistent logging configuration across all components
    of the Lab Automation Framework.
    """
    
    # Default configuration
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Log file configuration
    LOG_DIR = Path("logs")
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    
    # Log levels for different components
    COMPONENT_LOG_LEVELS = {
        'services': logging.INFO,
        'core': logging.INFO,
        'config_engine': logging.INFO,
        'api': logging.INFO,
        'database': logging.WARNING,
        'ssh': logging.INFO,
        'discovery': logging.INFO,
        'topology': logging.INFO,
        'bridge_domain': logging.INFO,
    }
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def initialize(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the logging system.
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        if cls._initialized:
            return
        
        # Create logs directory if it doesn't exist
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        # Apply custom configuration if provided
        if config:
            cls._apply_config(config)
        
        # Configure root logger
        cls._configure_root_logger()
        
        # Configure component-specific loggers
        cls._configure_component_loggers()
        
        cls._initialized = True
    
    @classmethod
    def _apply_config(cls, config: Dict[str, Any]) -> None:
        """Apply custom configuration"""
        if 'log_level' in config:
            cls.DEFAULT_LOG_LEVEL = getattr(logging, config['log_level'].upper())
        
        if 'log_format' in config:
            cls.DEFAULT_LOG_FORMAT = config['log_format']
        
        if 'log_dir' in config:
            cls.LOG_DIR = Path(config['log_dir'])
        
        if 'component_levels' in config:
            cls.COMPONENT_LOG_LEVELS.update(config['component_levels'])
    
    @classmethod
    def _configure_root_logger(cls) -> None:
        """Configure the root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(cls.DEFAULT_LOG_LEVEL)
        console_formatter = logging.Formatter(
            cls.DEFAULT_LOG_FORMAT,
            datefmt=cls.DEFAULT_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        all_logs_handler = cls._create_rotating_file_handler(
            cls.LOG_DIR / "lab_automation.log",
            logging.DEBUG
        )
        root_logger.addHandler(all_logs_handler)
    
    @classmethod
    def _configure_component_loggers(cls) -> None:
        """Configure component-specific loggers"""
        for component, level in cls.COMPONENT_LOG_LEVELS.items():
            logger = logging.getLogger(component)
            logger.setLevel(level)
            
            # Create component-specific log file
            log_file = cls.LOG_DIR / f"{component}.log"
            handler = cls._create_rotating_file_handler(log_file, level)
            logger.addHandler(handler)
    
    @classmethod
    def _create_rotating_file_handler(cls, log_file: Path, level: int) -> logging.Handler:
        """Create a rotating file handler"""
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=cls.MAX_LOG_SIZE,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            cls.DEFAULT_LOG_FORMAT,
            datefmt=cls.DEFAULT_DATE_FORMAT
        )
        handler.setFormatter(formatter)
        
        return handler
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for the specified name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        # Ensure logging is initialized
        if not cls._initialized:
            cls.initialize()
        
        # Return cached logger if available
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def set_log_level(cls, logger_name: str, level: str) -> None:
        """
        Set log level for a specific logger.
        
        Args:
            logger_name: Name of the logger
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if not cls._initialized:
            cls.initialize()
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
    
    @classmethod
    def add_custom_handler(cls, logger_name: str, handler: logging.Handler) -> None:
        """
        Add a custom handler to a specific logger.
        
        Args:
            logger_name: Name of the logger
            handler: Custom logging handler
        """
        if not cls._initialized:
            cls.initialize()
        
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
    
    @classmethod
    def get_log_file_path(cls, component: str) -> Path:
        """
        Get the log file path for a specific component.
        
        Args:
            component: Component name
            
        Returns:
            Path to the component's log file
        """
        return cls.LOG_DIR / f"{component}.log"
    
    @classmethod
    def cleanup_old_logs(cls, days_to_keep: int = 30) -> None:
        """
        Clean up old log files.
        
        Args:
            days_to_keep: Number of days to keep log files
        """
        if not cls.LOG_DIR.exists():
            return
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_file in cls.LOG_DIR.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    print(f"Removed old log file: {log_file}")
            except Exception as e:
                print(f"Failed to remove old log file {log_file}: {e}")


# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return LoggerFactory.get_logger(name)


# Convenience function for initializing logging
def initialize_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize the logging system.
    
    Args:
        config: Optional configuration dictionary
    """
    LoggerFactory.initialize(config)
