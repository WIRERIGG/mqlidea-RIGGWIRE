"""Advanced logging configuration for the Never Fail Build Resolver Agent."""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import os


class BuildResolverFormatter(logging.Formatter):
    """Custom formatter for build resolver logs with color support."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_colors: bool = True, include_session: bool = True):
        self.use_colors = use_colors and sys.stderr.isatty()
        self.include_session = include_session
        
        if include_session:
            fmt = '[{asctime}] [{session_id}] {levelname:8} | {name:25} | {message}'
        else:
            fmt = '[{asctime}] {levelname:8} | {name:25} | {message}'
            
        super().__init__(fmt, style='{', datefmt='%Y-%m-%d %H:%M:%S')
    
    def format(self, record):
        # Add session_id if not present
        if self.include_session and not hasattr(record, 'session_id'):
            record.session_id = getattr(logging.getLogger().manager, 'session_id', 'global')
        
        # Format the record
        formatted = super().format(record)
        
        # Add colors if enabled
        if self.use_colors:
            level_color = self.COLORS.get(record.levelname, '')
            reset_color = self.COLORS['RESET']
            formatted = f"{level_color}{formatted}{reset_color}"
        
        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add session_id if available
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_agent_logging(
    session_id: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_file_logging: bool = True,
    enable_json_logging: bool = False,
    max_log_files: int = 10,
    max_file_size_mb: int = 50
) -> logging.Logger:
    """Setup comprehensive logging for the build resolver agent.
    
    Args:
        session_id: Unique session identifier
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: project_root/logs)
        enable_file_logging: Whether to enable file logging
        enable_json_logging: Whether to enable structured JSON logging
        max_log_files: Maximum number of log files to retain
        max_file_size_mb: Maximum size of each log file in MB
    
    Returns:
        Configured logger instance
    """
    
    # Get or create logger
    logger_name = f"build_resolver_{session_id}"
    logger = logging.getLogger(logger_name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set log level
    log_level_obj = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(log_level_obj)
    
    # Store session_id on logger manager for formatter access
    if not hasattr(logger.manager, 'session_id'):
        logger.manager.session_id = session_id
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level_obj)
    console_formatter = BuildResolverFormatter(use_colors=True, include_session=True)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if enable_file_logging:
        # Setup log directory
        if log_dir is None:
            log_dir = Path.cwd() / "logs"
        
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Regular file handler with rotation
        log_file = log_dir / f"build_resolver_{session_id}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=max_log_files
        )
        file_handler.setLevel(logging.DEBUG)  # File logs capture everything
        file_formatter = BuildResolverFormatter(use_colors=False, include_session=True)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        if enable_json_logging:
            # JSON file handler for structured logging
            json_log_file = log_dir / f"build_resolver_{session_id}.json"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=max_log_files
            )
            json_handler.setLevel(logging.INFO)
            json_formatter = JSONFormatter()
            json_handler.setFormatter(json_formatter)
            logger.addHandler(json_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Build Resolver logging initialized for session {session_id}")
    logger.info(f"Log level: {log_level}, File logging: {enable_file_logging}, JSON logging: {enable_json_logging}")
    
    return logger


def get_agent_logger(session_id: str, module_name: str = None) -> logging.Logger:
    """Get a logger instance for a specific module within the agent session.
    
    Args:
        session_id: Session identifier
        module_name: Name of the module requesting the logger
    
    Returns:
        Logger instance
    """
    if module_name:
        logger_name = f"build_resolver_{session_id}.{module_name}"
    else:
        logger_name = f"build_resolver_{session_id}"
    
    return logging.getLogger(logger_name)


class LogContext:
    """Context manager for adding structured context to log messages."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


class PerformanceLogger:
    """Performance logging utility for timing operations."""
    
    def __init__(self, logger: logging.Logger, operation_name: str, 
                 log_level: int = logging.INFO, include_memory: bool = False):
        self.logger = logger
        self.operation_name = operation_name
        self.log_level = log_level
        self.include_memory = include_memory
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        
        if self.include_memory:
            try:
                import psutil
                process = psutil.Process()
                self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            except ImportError:
                self.include_memory = False
        
        self.logger.log(self.log_level, f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        end_time = time.perf_counter()
        duration = end_time - self.start_time
        
        extra_info = {"operation": self.operation_name, "duration_seconds": duration}
        
        if self.include_memory and self.start_memory is not None:
            try:
                import psutil
                process = psutil.Process()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = end_memory - self.start_memory
                extra_info.update({
                    "memory_start_mb": self.start_memory,
                    "memory_end_mb": end_memory,
                    "memory_delta_mb": memory_delta
                })
            except ImportError:
                pass
        
        if exc_type is None:
            self.logger.log(
                self.log_level,
                f"Completed {self.operation_name} in {duration:.3f}s",
                extra=extra_info
            )
        else:
            self.logger.error(
                f"Failed {self.operation_name} after {duration:.3f}s: {exc_val}",
                extra=extra_info,
                exc_info=(exc_type, exc_val, exc_tb)
            )


def log_system_info(logger: logging.Logger):
    """Log system information for debugging purposes."""
    try:
        import platform
        import psutil
        
        logger.info("System Information:")
        logger.info(f"  Platform: {platform.platform()}")
        logger.info(f"  Python: {platform.python_version()}")
        logger.info(f"  Architecture: {platform.architecture()[0]}")
        logger.info(f"  CPU cores: {psutil.cpu_count()}")
        
        memory = psutil.virtual_memory()
        logger.info(f"  Memory: {memory.total / 1024**3:.1f}GB total, {memory.available / 1024**3:.1f}GB available")
        
        disk = psutil.disk_usage('/')
        logger.info(f"  Disk: {disk.total / 1024**3:.1f}GB total, {disk.free / 1024**3:.1f}GB free")
        
    except Exception as e:
        logger.warning(f"Failed to log system information: {e}")


def configure_third_party_loggers(level: int = logging.WARNING):
    """Configure third-party library loggers to reduce noise."""
    
    # Common noisy loggers
    noisy_loggers = [
        'urllib3',
        'requests',
        'httpx',
        'httpcore',
        'openai',
        'anthropic',
        'pydantic_ai',
        'asyncio',
        'aiohttp'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(level)


# Example usage
if __name__ == "__main__":
    # Setup logging
    session_id = "test_session"
    logger = setup_agent_logging(
        session_id=session_id,
        log_level="DEBUG",
        enable_file_logging=True,
        enable_json_logging=True
    )
    
    # Log system information
    log_system_info(logger)
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test performance logging
    with PerformanceLogger(logger, "test_operation", include_memory=True):
        import time
        time.sleep(0.1)
    
    # Test context logging
    with LogContext(logger, build_id="test_build_123", tier="intelligent"):
        logger.info("Message with context")
    
    # Test module-specific logger
    module_logger = get_agent_logger(session_id, "test_module")
    module_logger.info("Message from test module")