"""Structured JSON logging with rotation and categorization.

Creates separate log files for different categories:
- app.log: General application events
- security.log: Security events (file validation, encryption)
- deploy.log: Deployment transactions
- error.log: All errors and exceptions
"""

import logging
import json
import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context if present
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data)


def setup_logging(log_dir: Optional[Path] = None, 
                  level: str = "INFO") -> None:
    """Setup application logging with rotation.
    
    Args:
        log_dir: Directory for log files (default: cwd/logs)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers and close them
    for handler in root_logger.handlers[:]:
        handler.close()  # Close file handles
        root_logger.removeHandler(handler)
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers with rotation (10MB per file, 5 backups)
    json_formatter = JsonFormatter()
    
    # App log (INFO and above)
    app_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log (ERROR and above only)
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Security log (custom filter for security events)
    security_handler = RotatingFileHandler(
        log_dir / "security.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(json_formatter)
    security_handler.addFilter(lambda record: 'security' in record.name.lower())
    root_logger.addHandler(security_handler)
    
    # Deploy log (custom filter for deploy events)
    deploy_handler = RotatingFileHandler(
        log_dir / "deploy.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    deploy_handler.setLevel(logging.INFO)
    deploy_handler.setFormatter(json_formatter)
    deploy_handler.addFilter(lambda record: 'deploy' in record.name.lower())
    root_logger.addHandler(deploy_handler)
    
    logging.info(f"Logging initialized: {log_dir} (level: {level})")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, 
                     message: str, **context: Any) -> None:
    """Log message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error)
        message: Log message
        **context: Additional context key-value pairs
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra={'context': context})


def setup_exception_logging() -> None:
    """Setup global exception handler to log uncaught exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow Ctrl+C to exit
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = get_logger("exception")
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
