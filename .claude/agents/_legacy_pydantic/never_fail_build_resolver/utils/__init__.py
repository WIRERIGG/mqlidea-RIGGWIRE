"""Utility modules for the Never Fail Build Resolver Agent.

This package provides helper utilities, logging configuration, file operations,
and system integration utilities that support the main agent functionality.

Modules:
- logging_config: Advanced logging configuration and management
- file_operations: Safe file and directory operations with rollback
- system_utils: System information and resource monitoring utilities
- build_utils: Build system specific utilities and helpers
- error_patterns: Error pattern recognition and classification
"""

from .logging_config import setup_agent_logging, get_agent_logger
from .file_operations import SafeFileOperations, create_backup, restore_backup
from .system_utils import SystemUtils, check_system_requirements
from .build_utils import BuildSystemUtils, detect_build_system_type
from .error_patterns import ErrorPatternMatcher, classify_build_error

__all__ = [
    # Logging
    'setup_agent_logging',
    'get_agent_logger',
    
    # File Operations
    'SafeFileOperations',
    'create_backup',
    'restore_backup',
    
    # System Utilities
    'SystemUtils',
    'check_system_requirements',
    
    # Build Utilities
    'BuildSystemUtils',
    'detect_build_system_type',
    
    # Error Pattern Recognition
    'ErrorPatternMatcher',
    'classify_build_error'
]