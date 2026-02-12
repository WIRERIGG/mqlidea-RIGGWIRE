"""
MT5 Infinite Reliability Agent

An advanced MQL5 code optimizer using a multi-agent architecture for comprehensive
optimization of Expert Advisors, indicators, and scripts for MetaTrader 5.

Architecture:
- Main Orchestrator: Coordinates specialized subagents
- Parser Agent: AST analysis and code structure mapping
- Optimizer Agent: Performance and efficiency improvements
- FTMO Compliance Agent: Risk management validation
- Verification Agent: Mathematical proofs and correctness
- Documentation Agent: MQL5 reference research

Target: /Users/shemarrigg/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE

Integration:
- Syncs with awareness_orchestrator for state tracking
- Escalates to multi_agent_debugging_system for deep analysis
- Follows never-fail-build-resolver escalation patterns
"""

from .agent import (
    agent,
    mt5_optimizer,
    ParserAgent,
    OptimizerAgent,
    FTMOComplianceAgent,
    VerificationAgent,
    DocumentationAgent,
    optimize_mql5_code,
    optimize_mql5_file,
    analyze_mql5_code,
    analyze_mql5_file,
    create_agent_with_deps,
)
from .dependencies import AgentDependencies, ProgressEvent, get_dependencies
from .settings import settings, load_settings
from .models import (
    OptimizationDimension,
    Severity,
    AgentType,
    EscalationTier,
    MQL5Pattern,
    OptimizationIssue,
    OptimizationTransformation,
    FTMOComplianceCheck,
    FTMOComplianceReport,
    AgentFindings,
    OptimizationContext,
    OptimizationResult,
    CacheableIndicatorData,
    NewBarTrigger,
    PerformanceMetrics,
    MQL5DocumentationRef,
    OptimizationProof,
    AgentHandoff,
)
from .tools import (
    parse_mql5_code,
    analyze_code_quality,
    apply_code_transformation,
    verify_code_correctness,
    create_proof_certificate,
    register_tools,
)
from .prompts import (
    SYSTEM_PROMPT,
    PARSER_AGENT_PROMPT,
    OPTIMIZER_AGENT_PROMPT,
    FTMO_COMPLIANCE_AGENT_PROMPT,
    VERIFICATION_AGENT_PROMPT,
    DOCUMENTATION_AGENT_PROMPT,
    ORCHESTRATOR_PROMPT,
    NEW_BAR_TRIGGER_TEMPLATE,
    CACHED_INDICATOR_TEMPLATE,
    FTMO_COMPLIANCE_TEMPLATE,
    ERROR_HANDLING_TEMPLATE,
)

__version__ = "2.0.0"
__all__ = [
    # Main agents
    "agent",
    "mt5_optimizer",

    # Subagents
    "ParserAgent",
    "OptimizerAgent",
    "FTMOComplianceAgent",
    "VerificationAgent",
    "DocumentationAgent",

    # Convenience functions
    "optimize_mql5_code",
    "optimize_mql5_file",
    "analyze_mql5_code",
    "analyze_mql5_file",
    "create_agent_with_deps",

    # Dependencies
    "AgentDependencies",
    "ProgressEvent",
    "get_dependencies",

    # Settings
    "settings",
    "load_settings",

    # Models
    "OptimizationDimension",
    "Severity",
    "AgentType",
    "EscalationTier",
    "MQL5Pattern",
    "OptimizationIssue",
    "OptimizationTransformation",
    "FTMOComplianceCheck",
    "FTMOComplianceReport",
    "AgentFindings",
    "OptimizationContext",
    "OptimizationResult",
    "CacheableIndicatorData",
    "NewBarTrigger",
    "PerformanceMetrics",
    "MQL5DocumentationRef",
    "OptimizationProof",
    "AgentHandoff",

    # Tools (standalone functions)
    "parse_mql5_code",
    "analyze_code_quality",
    "apply_code_transformation",
    "verify_code_correctness",
    "create_proof_certificate",
    "register_tools",

    # Prompts
    "SYSTEM_PROMPT",
    "PARSER_AGENT_PROMPT",
    "OPTIMIZER_AGENT_PROMPT",
    "FTMO_COMPLIANCE_AGENT_PROMPT",
    "VERIFICATION_AGENT_PROMPT",
    "DOCUMENTATION_AGENT_PROMPT",
    "ORCHESTRATOR_PROMPT",

    # MQL5 Code Templates
    "NEW_BAR_TRIGGER_TEMPLATE",
    "CACHED_INDICATOR_TEMPLATE",
    "FTMO_COMPLIANCE_TEMPLATE",
    "ERROR_HANDLING_TEMPLATE",
]
