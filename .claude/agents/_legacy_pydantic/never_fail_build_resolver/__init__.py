"""
NEVER FAIL BUILD RESOLVER - Pydantic AI Agent Package

A mission-critical AI agent that embodies the core principle: 
"NEVER give up and ALWAYS find a solution to ANY build problem."

This package provides comprehensive C++ build problem resolution with:
- Intelligent problem categorization and analysis
- Four-tier resolution strategy (fast, smart, thorough, emergency)
- State machine workflow orchestration
- Real-time learning from resolution patterns
- Seamless integration with wire_ground build infrastructure
"""

from .agent import (
    agent,
    resolve_build_problems,
    resolve_build_fast,
    resolve_build_smart,
    resolve_build_thorough,
    resolve_build_emergency,
    health_check
)

from .settings import load_settings, BuildResolverSettings
from .dependencies import BuildResolverDependencies
from .providers import get_llm_model, get_test_model

__version__ = "1.0.0"

__all__ = [
    # Main agent and resolution functions
    'agent',
    'resolve_build_problems',
    'resolve_build_fast',
    'resolve_build_smart', 
    'resolve_build_thorough',
    'resolve_build_emergency',
    'health_check',
    
    # Configuration and dependencies
    'load_settings',
    'BuildResolverSettings',
    'BuildResolverDependencies',
    
    # Model providers
    'get_llm_model',
    'get_test_model'
]