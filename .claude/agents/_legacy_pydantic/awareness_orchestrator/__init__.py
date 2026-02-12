"""
Awareness Orchestrator - Monolithic PydanticAI Agent System

A comprehensive orchestration system with 3 specialized agents:
- Analysis Agent: Structural analysis, code quality, refactoring opportunities
- Architecture Agent: Design patterns, modularization, migration planning
- Validation Agent: Testing strategies, regression prevention, quality assurance

This system provides context-rich, intelligent code analysis with learning capabilities.
"""

from .agent import (
    awareness_orchestrator,
    AnalysisAgent,
    ArchitectureAgent,
    ValidationAgent,
    OrchestrationResult,
    AgentFindings,
)
from .settings import load_settings
from .dependencies import OrchestrationDeps

__version__ = "1.0.0"

__all__ = [
    "awareness_orchestrator",
    "AnalysisAgent",
    "ArchitectureAgent",
    "ValidationAgent",
    "OrchestrationResult",
    "AgentFindings",
    "load_settings",
    "OrchestrationDeps",
]
