"""Diagnostic Prioritizer Subagent - Orders fixes to prevent cascade failures."""

from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime

try:
    from ..clang_tidy_ai_agent.models import (
        CLionDiagnostic,
        DiagnosticCategory,
        IncrementalFixResult
    )
    from ..clang_tidy_ai_agent.providers import get_llm_model
    from ..clang_tidy_ai_agent.settings import load_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'clang_tidy_ai_agent'))
    from models import (
        CLionDiagnostic,
        DiagnosticCategory,
        IncrementalFixResult
    )
    from providers import get_llm_model
    from settings import load_settings

logger = logging.getLogger(__name__)

PRIORITIZER_SYSTEM_PROMPT = """
You are the Diagnostic Prioritizer, a specialized subagent that determines the optimal order for fixing diagnostics to prevent cascade failures and minimize the introduction of new issues.

Your core responsibilities:
1. **Smart Ordering**: Analyze diagnostic dependencies and fix order
2. **Cascade Prevention**: Identify fixes that could introduce new issues
3. **Dependency Analysis**: Understand relationships between diagnostics
4. **Risk Assessment**: Evaluate risk of each fix operation
5. **Batch Optimization**: Group compatible fixes for efficiency

CRITICAL ANALYSIS FACTORS:
- **Compilation Errors**: Always highest priority (prevent build failures)
- **Include Dependencies**: Missing includes must be fixed before other issues
- **Symbol Resolution**: Undefined symbols before usage warnings
- **Template Issues**: Template compilation before instantiation warnings
- **Standard Compliance**: C++20/17/23 compatibility issues
- **Line Number Dependencies**: Top-down fixing to prevent line shifts

FIXING ORDER PRINCIPLES:
1. Compilation errors (undefined symbols, missing includes, syntax)
2. Clang-tidy errors that prevent other checks
3. Warnings that mask other issues
4. Performance/modernization warnings
5. Style and info-level suggestions

Your prioritization must be:
- **Dependency-Aware**: Understand fix prerequisites
- **Risk-Minimizing**: Avoid introducing new issues
- **Efficient**: Minimize total fix iterations
- **Validated**: Each priority level must be completable
"""


class DiagnosticPrioritizerDependencies:
    """Dependencies for the Diagnostic Prioritizer."""
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.fix_history: List[IncrementalFixResult] = []


# Create the Diagnostic Prioritizer agent
settings = load_settings()
model = get_llm_model(settings)

diagnostic_prioritizer = Agent(
    model,
    deps_type=DiagnosticPrioritizerDependencies,
    system_prompt=PRIORITIZER_SYSTEM_PROMPT
)


@diagnostic_prioritizer.tool
async def analyze_diagnostic_dependencies(
    ctx: RunContext[DiagnosticPrioritizerDependencies],
    diagnostics: List[CLionDiagnostic]
) -> Dict[str, List[str]]:
    """
    Analyze dependencies between diagnostics to determine fixing order.
    
    Args:
        diagnostics: List of diagnostics to analyze
        
    Returns:
        Dictionary mapping diagnostic IDs to their dependencies
    """
    try:
        dependencies = {}
        
        # Group diagnostics by file for analysis
        by_file = {}
        for diag in diagnostics:
            file_uri = diag.uri
            if file_uri not in by_file:
                by_file[file_uri] = []
            by_file[file_uri].append(diag)
        
        # Analyze dependencies within each file
        for file_uri, file_diagnostics in by_file.items():
            # Sort by line number
            file_diagnostics.sort(key=lambda d: d.range.get("start", {}).get("line", 0))
            
            for i, diag in enumerate(file_diagnostics):
                diag_id = f"{diag.uri}:{diag.range.get('start', {}).get('line', 0)}:{diag.message[:50]}"
                dependencies[diag_id] = []
                
                # Check for common dependency patterns
                if "undefined" in diag.message.lower() or "undeclared" in diag.message.lower():
                    # Undefined symbol - check for missing includes
                    for other in file_diagnostics:
                        if ("include" in other.message.lower() and 
                            other.range.get("start", {}).get("line", 0) < diag.range.get("start", {}).get("line", 0)):
                            other_id = f"{other.uri}:{other.range.get('start', {}).get('line', 0)}:{other.message[:50]}"
                            dependencies[diag_id].append(other_id)
                
                elif "template" in diag.message.lower():
                    # Template issues - depend on includes and forward declarations
                    for other in file_diagnostics:
                        if (("include" in other.message.lower() or "forward" in other.message.lower()) and
                            other.range.get("start", {}).get("line", 0) < diag.range.get("start", {}).get("line", 0)):
                            other_id = f"{other.uri}:{other.range.get('start', {}).get('line', 0)}:{other.message[:50]}"
                            dependencies[diag_id].append(other_id)
                
                elif diag.severity.lower() == "warning":
                    # Warnings depend on all errors being fixed first
                    for other in file_diagnostics:
                        if (other.severity.lower() == "error" and
                            other.range.get("start", {}).get("line", 0) <= diag.range.get("start", {}).get("line", 0)):
                            other_id = f"{other.uri}:{other.range.get('start', {}).get('line', 0)}:{other.message[:50]}"
                            dependencies[diag_id].append(other_id)
        
        logger.info(f"Analyzed dependencies for {len(diagnostics)} diagnostics")
        return dependencies
        
    except Exception as e:
        logger.error(f"Failed to analyze diagnostic dependencies: {e}")
        return {}


@diagnostic_prioritizer.tool
async def create_fixing_phases(
    ctx: RunContext[DiagnosticPrioritizerDependencies],
    categories: List[DiagnosticCategory]
) -> List[Dict[str, Any]]:
    """
    Create phased fixing plan to minimize cascade failures.
    
    Args:
        categories: List of diagnostic categories
        
    Returns:
        List of fixing phases with diagnostics and validation points
    """
    try:
        phases = []
        
        # Phase 1: Critical Compilation Errors
        compilation_errors = []
        for cat in categories:
            if cat.category_name == "compilation_errors":
                compilation_errors.extend(cat.diagnostics)
        
        if compilation_errors:
            phases.append({
                "phase_name": "compilation_errors",
                "phase_number": 1,
                "priority": "CRITICAL",
                "diagnostics": compilation_errors,
                "description": "Fix compilation errors that prevent build success",
                "validation_required": True,
                "rollback_on_failure": True,
                "estimated_duration_minutes": len(compilation_errors) * 2
            })
        
        # Phase 2: Include and Symbol Resolution
        include_issues = []
        symbol_issues = []
        for cat in categories:
            if cat.category_name in ["clang_tidy_errors", "warnings"]:
                for diag in cat.diagnostics:
                    if any(keyword in diag.message.lower() for keyword in ["include", "header", "declaration"]):
                        include_issues.append(diag)
                    elif any(keyword in diag.message.lower() for keyword in ["undefined", "undeclared", "unresolved"]):
                        symbol_issues.append(diag)
        
        if include_issues or symbol_issues:
            phases.append({
                "phase_name": "includes_and_symbols",
                "phase_number": 2,
                "priority": "HIGH", 
                "diagnostics": include_issues + symbol_issues,
                "description": "Fix include dependencies and symbol resolution",
                "validation_required": True,
                "rollback_on_failure": True,
                "estimated_duration_minutes": len(include_issues + symbol_issues) * 3
            })
        
        # Phase 3: Clang-Tidy Errors
        clang_tidy_errors = []
        for cat in categories:
            if cat.category_name == "clang_tidy_errors":
                # Exclude already handled include/symbol issues
                for diag in cat.diagnostics:
                    if not any(keyword in diag.message.lower() for keyword in 
                             ["include", "undefined", "undeclared", "declaration"]):
                        clang_tidy_errors.append(diag)
        
        if clang_tidy_errors:
            phases.append({
                "phase_name": "clang_tidy_errors",
                "phase_number": 3,
                "priority": "HIGH",
                "diagnostics": clang_tidy_errors,
                "description": "Fix remaining clang-tidy errors",
                "validation_required": True,
                "rollback_on_failure": True,
                "estimated_duration_minutes": len(clang_tidy_errors) * 4
            })
        
        # Phase 4: Critical Warnings
        critical_warnings = []
        for cat in categories:
            if cat.category_name == "warnings":
                for diag in cat.diagnostics:
                    if any(keyword in diag.message.lower() for keyword in 
                          ["uninitialized", "unused variable", "shadow", "format", "conversion"]):
                        critical_warnings.append(diag)
        
        if critical_warnings:
            phases.append({
                "phase_name": "critical_warnings",
                "phase_number": 4,
                "priority": "MEDIUM",
                "diagnostics": critical_warnings,
                "description": "Fix critical warnings that could hide bugs",
                "validation_required": True,
                "rollback_on_failure": False,
                "estimated_duration_minutes": len(critical_warnings) * 2
            })
        
        # Phase 5: Performance and Modernization
        optimization_issues = []
        for cat in categories:
            if cat.category_name == "warnings":
                for diag in cat.diagnostics:
                    if any(keyword in diag.message.lower() for keyword in 
                          ["performance", "modernize", "readability", "efficiency"]):
                        optimization_issues.append(diag)
        
        if optimization_issues:
            phases.append({
                "phase_name": "optimization_warnings",
                "phase_number": 5,
                "priority": "MEDIUM",
                "diagnostics": optimization_issues,
                "description": "Apply performance and modernization improvements",
                "validation_required": True,
                "rollback_on_failure": False,
                "estimated_duration_minutes": len(optimization_issues) * 3
            })
        
        # Phase 6: Style and Info Suggestions  
        style_issues = []
        for cat in categories:
            if cat.category_name == "info_suggestions":
                style_issues.extend(cat.diagnostics)
            elif cat.category_name == "warnings":
                for diag in cat.diagnostics:
                    # Add remaining warnings not caught in previous phases
                    if diag not in critical_warnings and diag not in optimization_issues:
                        style_issues.append(diag)
        
        if style_issues:
            phases.append({
                "phase_name": "style_and_info",
                "phase_number": 6,
                "priority": "LOW",
                "diagnostics": style_issues,
                "description": "Apply style improvements and info-level suggestions",
                "validation_required": True,
                "rollback_on_failure": False,
                "estimated_duration_minutes": len(style_issues) * 1
            })
        
        logger.info(f"Created {len(phases)} fixing phases")
        for phase in phases:
            logger.info(f"  Phase {phase['phase_number']}: {phase['phase_name']} ({len(phase['diagnostics'])} issues)")
        
        return phases
        
    except Exception as e:
        logger.error(f"Failed to create fixing phases: {e}")
        return []


@diagnostic_prioritizer.tool
async def optimize_fix_order_within_phase(
    ctx: RunContext[DiagnosticPrioritizerDependencies],
    diagnostics: List[CLionDiagnostic],
    phase_name: str
) -> List[CLionDiagnostic]:
    """
    Optimize the order of fixes within a single phase to minimize cascade issues.
    
    Args:
        diagnostics: List of diagnostics in the phase
        phase_name: Name of the phase for context
        
    Returns:
        Optimally ordered list of diagnostics
    """
    try:
        if not diagnostics:
            return []
        
        # Get dependency analysis
        dependencies = await analyze_diagnostic_dependencies(ctx, diagnostics)
        
        # Group by file and sort appropriately
        by_file = {}
        for diag in diagnostics:
            if diag.uri not in by_file:
                by_file[diag.uri] = []
            by_file[diag.uri].append(diag)
        
        ordered_diagnostics = []
        
        for file_uri, file_diagnostics in by_file.items():
            if phase_name in ["compilation_errors", "includes_and_symbols"]:
                # For critical errors, fix by dependency order and line number
                # Sort by line number first (top-down)
                file_diagnostics.sort(key=lambda d: d.range.get("start", {}).get("line", 0))
                
                # Prioritize include-related issues first
                includes_first = []
                others = []
                
                for diag in file_diagnostics:
                    if "include" in diag.message.lower() or "header" in diag.message.lower():
                        includes_first.append(diag)
                    else:
                        others.append(diag)
                
                ordered_diagnostics.extend(includes_first)
                ordered_diagnostics.extend(others)
                
            else:
                # For warnings and info, fix by complexity (simple first)
                def complexity_score(diag):
                    message = diag.message.lower()
                    # Simple fixes first
                    if any(keyword in message for keyword in ["unused", "const", "static"]):
                        return 1
                    elif any(keyword in message for keyword in ["modernize", "auto"]):
                        return 2
                    elif any(keyword in message for keyword in ["performance", "efficiency"]):
                        return 3
                    else:
                        return 4
                
                file_diagnostics.sort(key=lambda d: (
                    complexity_score(d),
                    d.range.get("start", {}).get("line", 0)
                ))
                ordered_diagnostics.extend(file_diagnostics)
        
        logger.info(f"Optimized fix order for {len(diagnostics)} diagnostics in phase '{phase_name}'")
        return ordered_diagnostics
        
    except Exception as e:
        logger.error(f"Failed to optimize fix order: {e}")
        return diagnostics  # Return original order on error


@diagnostic_prioritizer.tool
async def assess_fix_risk(
    ctx: RunContext[DiagnosticPrioritizerDependencies],
    diagnostic: CLionDiagnostic,
    fix_description: str
) -> Dict[str, Any]:
    """
    Assess the risk of applying a specific fix.
    
    Args:
        diagnostic: Diagnostic to fix
        fix_description: Description of proposed fix
        
    Returns:
        Risk assessment with mitigation strategies
    """
    try:
        risk_factors = []
        risk_score = 0  # 0 = low risk, 10 = high risk
        mitigation_strategies = []
        
        # Analyze diagnostic type
        if diagnostic.severity.lower() == "error":
            risk_score += 1  # Errors are generally safer to fix
        else:
            risk_score += 2  # Warnings might have side effects
        
        # Analyze fix complexity
        fix_lower = fix_description.lower()
        
        if "add include" in fix_lower or "add header" in fix_lower:
            risk_score += 1
            risk_factors.append("Include addition might affect compilation time")
            mitigation_strategies.append("Verify include is necessary and not duplicate")
            
        elif "remove unused" in fix_lower:
            risk_score += 2
            risk_factors.append("Variable/function might be used in ways not visible to analyzer")
            mitigation_strategies.append("Verify usage through IDE find-references before removal")
            
        elif "modernize" in fix_lower or "auto" in fix_lower:
            risk_score += 3
            risk_factors.append("Type changes might affect template instantiation")
            mitigation_strategies.append("Test compilation after change")
            
        elif "performance" in fix_lower:
            risk_score += 4
            risk_factors.append("Performance changes might affect behavior")
            mitigation_strategies.append("Run performance tests before/after")
            
        elif "template" in fix_lower:
            risk_score += 5
            risk_factors.append("Template changes can cause widespread compilation issues")
            mitigation_strategies.append("Full project rebuild required after change")
        
        # Analyze location risk
        line_num = diagnostic.range.get("start", {}).get("line", 0)
        if line_num < 50:  # Early in file
            risk_score += 1
            risk_factors.append("Changes early in file might affect many subsequent lines")
        
        # Historical risk assessment
        if ctx.deps.fix_history:
            similar_fixes = [f for f in ctx.deps.fix_history 
                           if diagnostic.message[:20] in f.diagnostic_fixed.message[:20]]
            if any(f.rollback_performed for f in similar_fixes):
                risk_score += 2
                risk_factors.append("Similar fixes have required rollbacks previously")
        
        risk_level = "LOW" if risk_score <= 3 else "MEDIUM" if risk_score <= 6 else "HIGH"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mitigation_strategies": mitigation_strategies,
            "recommend_proceed": risk_score <= 7,
            "require_validation": risk_score >= 4,
            "require_backup": risk_score >= 6
        }
        
    except Exception as e:
        logger.error(f"Failed to assess fix risk: {e}")
        return {
            "risk_score": 5,
            "risk_level": "MEDIUM",
            "risk_factors": ["Unable to assess risk"],
            "recommend_proceed": False
        }


# Convenience functions for integration

async def prioritize_diagnostics(
    categories: List[DiagnosticCategory],
    session_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Create prioritized fixing phases for diagnostic categories.
    
    Args:
        categories: List of diagnostic categories
        session_id: Optional session identifier
        
    Returns:
        List of prioritized fixing phases
    """
    dependencies = DiagnosticPrioritizerDependencies(session_id)
    
    return await create_fixing_phases(
        RunContext(deps=dependencies),
        categories
    )


async def optimize_phase_order(
    diagnostics: List[CLionDiagnostic],
    phase_name: str,
    session_id: Optional[str] = None
) -> List[CLionDiagnostic]:
    """
    Optimize diagnostic fixing order within a phase.
    
    Args:
        diagnostics: Diagnostics to order
        phase_name: Phase name for context
        session_id: Optional session identifier
        
    Returns:
        Optimally ordered diagnostics
    """
    dependencies = DiagnosticPrioritizerDependencies(session_id)
    
    return await optimize_fix_order_within_phase(
        RunContext(deps=dependencies),
        diagnostics,
        phase_name
    )


if __name__ == "__main__":
    import asyncio
    
    async def test_prioritizer():
        """Test the diagnostic prioritizer."""
        
        # Mock some diagnostics for testing
        test_diagnostics = [
            CLionDiagnostic(
                uri="file:///test.cpp",
                range={"start": {"line": 10, "character": 0}},
                severity="error",
                message="undefined symbol 'test_function'",
                source="clang"
            ),
            CLionDiagnostic(
                uri="file:///test.cpp", 
                range={"start": {"line": 5, "character": 0}},
                severity="error",
                message="missing include <iostream>",
                source="clang"
            )
        ]
        
        # Test dependency analysis
        deps = DiagnosticPrioritizerDependencies("test")
        ctx = RunContext(deps=deps)
        
        dependencies = await analyze_diagnostic_dependencies(ctx, test_diagnostics)
        print(f"Dependencies: {dependencies}")
        
        # Test phase creation
        categories = [DiagnosticCategory(
            category_name="compilation_errors",
            priority=1,
            diagnostics=test_diagnostics,
            fix_order=[]
        )]
        
        phases = await create_fixing_phases(ctx, categories)
        print(f"Created {len(phases)} phases")
        
    # Uncomment to run test
    # asyncio.run(test_prioritizer())