"""Core module for Never Fail Build Resolver Agent.

This module provides the main components for intelligent build system resolution
including dependency management, model definitions, and the primary agent implementation.

The core modules include:
- settings: Configuration and settings management
- models: Pydantic models for structured data
- dependencies: Build system integration and dependency injection
- agent: Main PydanticAI agent implementation
- tools: Build diagnosis, resolution, and validation tools
"""

from .settings import BuildResolverSettings, load_settings
from .models import (
    BuildProblem,
    BuildError, 
    ResolutionStrategy,
    BuildAnalysis,
    ResolutionResult,
    SystemDiagnostics,
    BuildConfiguration,
    PreventionRule,
    BuildContext
)
from .dependencies import BuildResolverDependencies, create_dependencies
# Import from simple_agent instead of broken agent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from simple_agent import (
    BuildResolverAI,
    interactive_build_diagnosis, 
    emergency_build_resolution,
    NeverFailBuildResolver
)

# Provide the expected interface
build_resolver_agent = None  # Simple agent doesn't expose this
prevent_build_failures = None  # Will be implemented later
comprehensive_project_analysis = None  # Will be implemented later
from .tools import (
    diagnose_build_problems,
    apply_resolution_strategy,
    validate_resolution,
    prevent_future_problems,
    analyze_build_configuration,
    emergency_nuclear_reset
)

__all__ = [
    # Settings
    'BuildResolverSettings',
    'load_settings',
    
    # Models  
    'BuildProblem',
    'BuildError',
    'ResolutionStrategy', 
    'BuildAnalysis',
    'ResolutionResult',
    'SystemDiagnostics',
    'BuildConfiguration',
    'PreventionRule',
    'BuildContext',
    
    # Dependencies
    'BuildResolverDependencies',
    'create_dependencies',
    
    # Agent
    'build_resolver_agent',
    'BuildResolverAI',
    'interactive_build_diagnosis',
    'emergency_build_resolution',
    'prevent_build_failures', 
    'comprehensive_project_analysis',
    
    # Tools
    'diagnose_build_problems',
    'apply_resolution_strategy',
    'validate_resolution',
    'prevent_future_problems',
    'analyze_build_configuration',
    'emergency_nuclear_reset'
]