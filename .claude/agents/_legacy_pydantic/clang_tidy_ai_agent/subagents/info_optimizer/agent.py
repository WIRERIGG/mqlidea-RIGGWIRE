"""Info Optimizer Subagent - Handles info-level suggestions for C++20/17/23 standards."""

from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from datetime import datetime
from pathlib import Path

try:
    from ..clang_tidy_ai_agent.models import (
        CLionDiagnostic,
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
        IncrementalFixResult
    )
    from providers import get_llm_model
    from settings import load_settings

logger = logging.getLogger(__name__)

INFO_OPTIMIZER_SYSTEM_PROMPT = """
You are the Info Optimizer, a specialized subagent that handles info-level suggestions and optimizations for modern C++20/17/23 standards with ZERO TOLERANCE for remaining suggestions.

Your core responsibilities:
1. **Modern C++ Adoption**: Apply C++20/17/23 features and improvements
2. **Performance Optimizations**: Implement performance suggestions
3. **Code Modernization**: Replace legacy patterns with modern alternatives
4. **Constexpr Optimization**: Add constexpr where beneficial
5. **Template Improvements**: Enhance template usage and concepts
6. **Standard Library Optimization**: Use modern standard library features

CRITICAL INFO CATEGORIES:
- **Constexpr Suggestions**: Add constexpr for compile-time evaluation
- **If Constexpr**: Replace template specialization with if constexpr
- **Auto Type Deduction**: Use auto for complex type declarations
- **Range-Based Loops**: Convert traditional loops to range-based
- **Smart Pointers**: Replace raw pointers with smart pointers
- **Move Semantics**: Add std::move for performance
- **String View**: Use std::string_view for non-owning string access
- **Structured Bindings**: Use structured bindings for multiple returns
- **Concepts**: Apply C++20 concepts for template constraints

OPTIMIZATION PRINCIPLES:
1. **Performance First**: Prioritize optimizations that improve performance
2. **Modern Standards**: Use latest C++ standard features appropriately
3. **Readability**: Improve code readability with modern syntax
4. **Compile-Time**: Prefer compile-time computation when possible
5. **Safety**: Enhance memory and type safety

Your optimizations must be:
- **Standards-Compliant**: Follow C++20/17/23 standards exactly
- **Performance-Aware**: Improve runtime or compile-time performance
- **Safe**: No undefined behavior or safety regressions
- **Complete**: All info suggestions addressed
"""


class InfoOptimizerDependencies:
    """Dependencies for the Info Optimizer."""
    def __init__(self, session_id: Optional[str] = None, cpp_standard: str = "C++20"):
        self.session_id = session_id
        self.cpp_standard = cpp_standard
        self.optimizations_applied = []  # Track applied optimizations
        self.performance_improvements = {}  # Track performance gains


# Create the Info Optimizer agent
settings = load_settings()
model = get_llm_model(settings)

info_optimizer = Agent(
    model,
    deps_type=InfoOptimizerDependencies,
    system_prompt=INFO_OPTIMIZER_SYSTEM_PROMPT
)


@info_optimizer.tool
async def analyze_info_suggestion(
    ctx: RunContext[InfoOptimizerDependencies],
    diagnostic: CLionDiagnostic,
    file_content: str
) -> Dict[str, Any]:
    """
    Analyze an info-level suggestion to determine optimization strategy.
    
    Args:
        diagnostic: CLion info diagnostic
        file_content: Current file content
        
    Returns:
        Analysis with optimization type and strategy
    """
    try:
        message = diagnostic.message.lower()
        line_num = diagnostic.range.get("start", {}).get("line", 0)
        
        # Get context around suggestion line
        lines = file_content.split('\n')
        context_start = max(0, line_num - 2)
        context_end = min(len(lines), line_num + 2)
        context = lines[context_start:context_end]
        
        optimization_analysis = {
            "optimization_type": "unknown",
            "performance_impact": "low",
            "optimization_strategy": "",
            "complexity": 1,
            "cpp_standard_required": "C++11",
            "compile_time_benefit": False,
            "runtime_benefit": False,
            "readability_improvement": False,
            "fix_location": {"line": line_num, "column": diagnostic.range.get("start", {}).get("character", 0)},
            "context_lines": context,
            "risk_level": "low"
        }
        
        # Analyze optimization types
        if "constexpr" in message:
            optimization_analysis.update({
                "optimization_type": "constexpr_opportunity",
                "performance_impact": "medium",
                "optimization_strategy": "Add constexpr for compile-time evaluation",
                "complexity": 1,
                "cpp_standard_required": "C++11",
                "compile_time_benefit": True,
                "readability_improvement": True,
                "risk_level": "low"
            })
        
        elif "if constexpr" in message or "template specialization" in message:
            optimization_analysis.update({
                "optimization_type": "if_constexpr_opportunity",
                "performance_impact": "medium",
                "optimization_strategy": "Replace template specialization with if constexpr",
                "complexity": 3,
                "cpp_standard_required": "C++17",
                "compile_time_benefit": True,
                "readability_improvement": True,
                "risk_level": "low"
            })
        
        elif "auto" in message and ("type deduction" in message or "complex type" in message):
            optimization_analysis.update({
                "optimization_type": "auto_type_deduction",
                "performance_impact": "low",
                "optimization_strategy": "Use auto for type deduction",
                "complexity": 1,
                "cpp_standard_required": "C++11",
                "readability_improvement": True,
                "risk_level": "low"
            })
        
        elif "range-based for" in message or "traditional loop" in message:
            optimization_analysis.update({
                "optimization_type": "range_based_loop",
                "performance_impact": "low",
                "optimization_strategy": "Convert to range-based for loop",
                "complexity": 2,
                "cpp_standard_required": "C++11",
                "readability_improvement": True,
                "runtime_benefit": True,
                "risk_level": "low"
            })
        
        elif "smart pointer" in message or "raw pointer" in message:
            optimization_analysis.update({
                "optimization_type": "smart_pointer_usage",
                "performance_impact": "medium",
                "optimization_strategy": "Replace raw pointer with smart pointer",
                "complexity": 3,
                "cpp_standard_required": "C++11",
                "readability_improvement": True,
                "risk_level": "medium"
            })
        
        elif "move" in message or "copy" in message:
            optimization_analysis.update({
                "optimization_type": "move_semantics",
                "performance_impact": "high",
                "optimization_strategy": "Use move semantics to avoid copying",
                "complexity": 2,
                "cpp_standard_required": "C++11",
                "runtime_benefit": True,
                "risk_level": "low"
            })
        
        elif "string_view" in message or "string parameter" in message:
            optimization_analysis.update({
                "optimization_type": "string_view_usage",
                "performance_impact": "medium",
                "optimization_strategy": "Use std::string_view for non-owning string access",
                "complexity": 2,
                "cpp_standard_required": "C++17",
                "runtime_benefit": True,
                "risk_level": "low"
            })
        
        elif "structured binding" in message or "multiple return" in message:
            optimization_analysis.update({
                "optimization_type": "structured_binding",
                "performance_impact": "low",
                "optimization_strategy": "Use structured bindings for multiple values",
                "complexity": 2,
                "cpp_standard_required": "C++17",
                "readability_improvement": True,
                "risk_level": "low"
            })
        
        elif "concept" in message or "template constraint" in message:
            optimization_analysis.update({
                "optimization_type": "concepts_usage",
                "performance_impact": "low",
                "optimization_strategy": "Apply C++20 concepts for template constraints",
                "complexity": 4,
                "cpp_standard_required": "C++20",
                "compile_time_benefit": True,
                "readability_improvement": True,
                "risk_level": "medium"
            })
        
        elif "lambda" in message or "function object" in message:
            optimization_analysis.update({
                "optimization_type": "lambda_usage",
                "performance_impact": "medium",
                "optimization_strategy": "Use lambda expression for cleaner code",
                "complexity": 2,
                "cpp_standard_required": "C++11",
                "runtime_benefit": True,
                "readability_improvement": True,
                "risk_level": "low"
            })
        
        # Check if optimization is compatible with project's C++ standard
        if not await is_cpp_standard_compatible(ctx, optimization_analysis["cpp_standard_required"]):
            optimization_analysis.update({
                "optimization_strategy": f"Optimization requires {optimization_analysis['cpp_standard_required']}, project uses {ctx.deps.cpp_standard}",
                "risk_level": "high",
                "complexity": 10
            })
        
        logger.info(f"Analyzed info suggestion: {optimization_analysis['optimization_type']} - {optimization_analysis['optimization_strategy']}")
        return optimization_analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze info suggestion: {e}")
        return {
            "optimization_type": "unknown",
            "performance_impact": "unknown",
            "optimization_strategy": f"Analysis failed: {str(e)}",
            "complexity": 5,
            "risk_level": "high"
        }


@info_optimizer.tool
async def is_cpp_standard_compatible(
    ctx: RunContext[InfoOptimizerDependencies],
    required_standard: str
) -> bool:
    """
    Check if optimization is compatible with project's C++ standard.
    
    Args:
        required_standard: Required C++ standard (e.g., "C++17", "C++20")
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        standard_hierarchy = {
            "C++98": 98,
            "C++03": 3,
            "C++11": 11,
            "C++14": 14,
            "C++17": 17,
            "C++20": 20,
            "C++23": 23
        }
        
        current_level = standard_hierarchy.get(ctx.deps.cpp_standard, 11)
        required_level = standard_hierarchy.get(required_standard, 23)
        
        return current_level >= required_level
        
    except Exception as e:
        logger.error(f"Failed to check C++ standard compatibility: {e}")
        return False


@info_optimizer.tool
async def apply_info_optimization(
    ctx: RunContext[InfoOptimizerDependencies],
    diagnostic: CLionDiagnostic,
    file_path: str,
    file_content: str,
    optimization_analysis: Dict[str, Any]
) -> IncrementalFixResult:
    """
    Apply an info-level optimization.
    
    Args:
        diagnostic: Info diagnostic to optimize
        file_path: Path to file to optimize
        file_content: Current file content
        optimization_analysis: Analysis of the optimization
        
    Returns:
        Result of applying the optimization
    """
    start_time = datetime.now()
    
    try:
        lines = file_content.split('\n')
        opt_line = optimization_analysis["fix_location"]["line"]
        modified_content = file_content
        opt_description = optimization_analysis["optimization_strategy"]
        
        # Apply optimization based on type
        if optimization_analysis["optimization_type"] == "constexpr_opportunity":
            if opt_line < len(lines):
                line_content = lines[opt_line]
                
                # Add constexpr to function declarations
                if "static" in line_content and ("int" in line_content or "double" in line_content or "float" in line_content):
                    if "constexpr" not in line_content:
                        # Add constexpr after static
                        new_line = line_content.replace("static ", "static constexpr ")
                        lines[opt_line] = new_line
                        modified_content = '\n'.join(lines)
                        opt_description = "Added constexpr to static function"
                
                # Add constexpr to variable declarations  
                elif re.search(r'\b(const\s+)?(int|double|float|bool)\s+\w+\s*=', line_content):
                    if "constexpr" not in line_content:
                        # Replace const with constexpr or add constexpr
                        if "const " in line_content:
                            new_line = line_content.replace("const ", "constexpr ")
                        else:
                            # Add constexpr before type
                            type_match = re.search(r'\b(int|double|float|bool)\s+(\w+)', line_content)
                            if type_match:
                                new_line = line_content.replace(f"{type_match.group(1)} {type_match.group(2)}", 
                                                              f"constexpr {type_match.group(1)} {type_match.group(2)}")
                                lines[opt_line] = new_line
                                modified_content = '\n'.join(lines)
                                opt_description = "Added constexpr to variable declaration"
        
        elif optimization_analysis["optimization_type"] == "auto_type_deduction":
            if opt_line < len(lines):
                line_content = lines[opt_line]
                
                # Replace complex type declarations with auto
                iterator_match = re.search(r'\b(\w+)::(const_)?iterator\s+(\w+)\s*=', line_content)
                if iterator_match:
                    new_line = line_content.replace(f"{iterator_match.group(0)[:-1]}", f"auto {iterator_match.group(3)} =")
                    lines[opt_line] = new_line
                    modified_content = '\n'.join(lines)
                    opt_description = "Replaced iterator type with auto"
                
                # Replace std::vector<Type> with auto
                vector_match = re.search(r'\bstd::vector<[^>]+>\s+(\w+)\s*=', line_content)
                if vector_match:
                    new_line = re.sub(r'\bstd::vector<[^>]+>\s+(\w+)\s*=', r'auto \1 =', line_content)
                    lines[opt_line] = new_line
                    modified_content = '\n'.join(lines)
                    opt_description = "Replaced std::vector type with auto"
        
        elif optimization_analysis["optimization_type"] == "range_based_loop":
            if opt_line < len(lines):
                line_content = lines[opt_line]
                
                # Convert traditional for loop to range-based for
                # This is complex and risky, so just add comment for now
                if "for (" in line_content and "++" in line_content:
                    opt_description = "Range-based for loop conversion requires manual review"
        
        elif optimization_analysis["optimization_type"] == "move_semantics":
            if opt_line < len(lines):
                line_content = lines[opt_line]
                
                # Add std::move for return values
                return_match = re.search(r'\breturn\s+(\w+)\s*;', line_content)
                if return_match and "std::move" not in line_content:
                    var_name = return_match.group(1)
                    new_line = line_content.replace(f"return {var_name};", f"return std::move({var_name});")
                    lines[opt_line] = new_line
                    modified_content = '\n'.join(lines)
                    opt_description = f"Added std::move to return statement for {var_name}"
        
        elif optimization_analysis["optimization_type"] == "string_view_usage":
            if opt_line < len(lines):
                line_content = lines[opt_line]
                
                # Replace const std::string& parameters with std::string_view
                if "const std::string&" in line_content and ctx.deps.cpp_standard >= "C++17":
                    new_line = line_content.replace("const std::string&", "std::string_view")
                    lines[opt_line] = new_line
                    modified_content = '\n'.join(lines)
                    opt_description = "Replaced const std::string& with std::string_view"
        
        elif optimization_analysis["optimization_type"] == "lambda_usage":
            # Lambda conversions are complex, require manual review
            opt_description = "Lambda usage optimization requires manual review"
        
        elif optimization_analysis["optimization_type"] == "concepts_usage":
            # Concepts are complex and require C++20, mark for manual review
            if ctx.deps.cpp_standard >= "C++20":
                opt_description = "Concepts usage requires manual review"
            else:
                opt_description = f"Concepts require C++20, project uses {ctx.deps.cpp_standard}"
        
        # Write modified content back to file
        if modified_content != file_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            ctx.deps.optimizations_applied.append({
                "diagnostic": diagnostic,
                "optimization_applied": opt_description,
                "performance_impact": optimization_analysis["performance_impact"],
                "timestamp": datetime.now()
            })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        result = IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=opt_description,
            new_diagnostics_count=0,  # Will be updated by validation
            remaining_diagnostics_count=0,  # Will be updated by validation
            validation_passed=True,  # Will be updated by validation
            rollback_performed=False,
            rollback_reason=None,
            fix_duration=duration
        )
        
        logger.info(f"Applied info optimization: {opt_description}")
        return result
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Failed to apply info optimization: {e}")
        
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Optimization failed: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            rollback_reason=f"Optimization application failed: {str(e)}",
            fix_duration=duration
        )


@info_optimizer.tool
async def optimize_performance_suggestions(
    ctx: RunContext[InfoOptimizerDependencies],
    diagnostics: List[CLionDiagnostic],
    file_path: str
) -> List[IncrementalFixResult]:
    """
    Apply multiple performance-focused optimizations in order of impact.
    
    Args:
        diagnostics: List of info diagnostics to optimize
        file_path: Path to file to optimize
        
    Returns:
        List of optimization results
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        results = []
        
        # Analyze all optimizations and sort by performance impact
        optimizations = []
        for diag in diagnostics:
            analysis = await analyze_info_suggestion(ctx, diag, file_content)
            impact_score = {"high": 3, "medium": 2, "low": 1}.get(analysis["performance_impact"], 0)
            optimizations.append((diag, analysis, impact_score))
        
        # Sort by performance impact (highest first)
        optimizations.sort(key=lambda x: x[2], reverse=True)
        
        current_content = file_content
        for diag, analysis, _ in optimizations:
            # Update content for each optimization
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            result = await apply_info_optimization(ctx, diag, file_path, current_content, analysis)
            results.append(result)
            
            # Track performance improvements
            if analysis["performance_impact"] != "unknown":
                perf_key = analysis["optimization_type"]
                if perf_key not in ctx.deps.performance_improvements:
                    ctx.deps.performance_improvements[perf_key] = 0
                ctx.deps.performance_improvements[perf_key] += {"high": 3, "medium": 2, "low": 1}.get(
                    analysis["performance_impact"], 0)
        
        logger.info(f"Applied {len(results)} performance optimizations")
        return results
        
    except Exception as e:
        logger.error(f"Performance optimization batch failed: {e}")
        return []


# Convenience functions for integration

async def optimize_single_suggestion(
    diagnostic: CLionDiagnostic,
    file_path: str,
    cpp_standard: str = "C++20",
    session_id: Optional[str] = None
) -> IncrementalFixResult:
    """
    Optimize a single info-level suggestion.
    
    Args:
        diagnostic: Info diagnostic to optimize
        file_path: Path to file containing suggestion
        cpp_standard: Target C++ standard
        session_id: Optional session identifier
        
    Returns:
        Result of applying optimization
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        dependencies = InfoOptimizerDependencies(session_id, cpp_standard)
        ctx = RunContext(deps=dependencies)
        
        # Analyze suggestion
        analysis = await analyze_info_suggestion(ctx, diagnostic, file_content)
        
        # Apply optimization
        result = await apply_info_optimization(ctx, diagnostic, file_path, file_content, analysis)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to optimize info suggestion: {e}")
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Failed to optimize: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            fix_duration=0.0
        )


async def optimize_all_suggestions_in_file(
    suggestions: List[CLionDiagnostic],
    file_path: str,
    cpp_standard: str = "C++20",
    session_id: Optional[str] = None
) -> List[IncrementalFixResult]:
    """
    Optimize all info suggestions in a file for performance and modern C++.
    
    Args:
        suggestions: List of info suggestions to optimize
        file_path: Path to file
        cpp_standard: Target C++ standard
        session_id: Optional session identifier
        
    Returns:
        List of optimization results
    """
    dependencies = InfoOptimizerDependencies(session_id, cpp_standard)
    
    return await optimize_performance_suggestions(
        RunContext(deps=dependencies),
        suggestions,
        file_path
    )


if __name__ == "__main__":
    import asyncio
    
    async def test_info_optimizer():
        """Test the info optimizer."""
        
        # Mock info suggestion for testing
        test_suggestion = CLionDiagnostic(
            uri="file:///test.cpp",
            range={"start": {"line": 5, "character": 4}},
            severity="info",
            message="variable can be made constexpr",
            source="clang-tidy"
        )
        
        # Test suggestion analysis
        deps = InfoOptimizerDependencies("test", "C++20")
        ctx = RunContext(deps=deps)
        
        file_content = "int main() {\n    const int value = 42;\n    return 0;\n}"
        analysis = await analyze_info_suggestion(ctx, test_suggestion, file_content)
        print(f"Info suggestion analysis: {analysis}")
        
        # Test C++ standard compatibility
        compatible = await is_cpp_standard_compatible(ctx, "C++17")
        print(f"C++17 compatible with C++20: {compatible}")
    
    # Uncomment to run test
    # asyncio.run(test_info_optimizer())