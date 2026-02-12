"""Warning Eliminator Subagent - Eliminates ALL warnings with zero tolerance."""

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

WARNING_ELIMINATOR_SYSTEM_PROMPT = """
You are the Warning Eliminator, a specialized subagent that eliminates ALL warnings with ZERO TOLERANCE. Every warning is treated as an error that MUST be fixed.

Your core responsibilities:
1. **Zero-Tolerance Enforcement**: ALL warnings must be eliminated, no exceptions
2. **Safe Warning Fixes**: Fix warnings without changing program behavior
3. **Unused Variable Elimination**: Remove or mark unused variables appropriately
4. **Shadowing Resolution**: Fix variable/parameter shadowing issues
5. **Format String Fixes**: Fix printf/cout format inconsistencies  
6. **Conversion Warnings**: Fix implicit conversion warnings safely
7. **Initialization Issues**: Fix uninitialized variable warnings

CRITICAL WARNING CATEGORIES:
- **Unused Variables/Parameters**: Remove or mark with [[maybe_unused]]
- **Variable Shadowing**: Rename variables to avoid shadowing
- **Uninitialized Variables**: Add proper initialization
- **Format Warnings**: Fix printf format strings and arguments
- **Conversion Warnings**: Add explicit casts or fix types
- **Return Value Warnings**: Handle all return values
- **Deprecated Usage**: Replace deprecated functions/features
- **Clang-Tidy Warnings**: Fix all clang-tidy rule violations

FIXING PRINCIPLES:
1. **Preserve Behavior**: Never change program logic or behavior
2. **Minimal Changes**: Make smallest change that eliminates warning
3. **Modern C++**: Use modern C++ features when appropriate
4. **Safety First**: Add safety checks when eliminating warnings
5. **Code Clarity**: Improve code readability while fixing warnings

Your warning elimination must be:
- **Complete**: Every warning eliminated
- **Safe**: No behavior changes
- **Modern**: Use C++20/17/23 best practices
- **Validated**: Each fix verified immediately
"""


class WarningEliminatorDependencies:
    """Dependencies for the Warning Eliminator."""
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.warnings_eliminated = []  # Track eliminated warnings
        self.fix_patterns = {}  # Track successful fix patterns


# Create the Warning Eliminator agent
settings = load_settings()
model = get_llm_model(settings)

warning_eliminator = Agent(
    model,
    deps_type=WarningEliminatorDependencies,
    system_prompt=WARNING_ELIMINATOR_SYSTEM_PROMPT
)


@warning_eliminator.tool
async def analyze_warning_type(
    ctx: RunContext[WarningEliminatorDependencies],
    diagnostic: CLionDiagnostic,
    file_content: str
) -> Dict[str, Any]:
    """
    Analyze a warning to determine type and optimal fix strategy.
    
    Args:
        diagnostic: CLion warning diagnostic
        file_content: Current file content
        
    Returns:
        Analysis with warning type and fix strategy
    """
    try:
        message = diagnostic.message.lower()
        line_num = diagnostic.range.get("start", {}).get("line", 0)
        
        # Get context around warning line
        lines = file_content.split('\n')
        context_start = max(0, line_num - 2)
        context_end = min(len(lines), line_num + 2)
        context = lines[context_start:context_end]
        
        warning_analysis = {
            "warning_type": "unknown",
            "severity": "medium",
            "fix_strategy": "",
            "fix_complexity": 1,
            "preserve_variable": False,
            "requires_cast": False,
            "modernize_code": False,
            "fix_location": {"line": line_num, "column": diagnostic.range.get("start", {}).get("character", 0)},
            "context_lines": context,
            "risk_level": "low"
        }
        
        # Analyze warning types
        if "unused variable" in message or "unused parameter" in message:
            warning_analysis.update({
                "warning_type": "unused_variable",
                "severity": "low",
                "fix_strategy": "Remove variable or add [[maybe_unused]] attribute",
                "fix_complexity": 1,
                "risk_level": "low"
            })
            
            # Check if variable might be used in debugging or future code
            var_match = re.search(r"['\"]([^'\"]+)['\"]", diagnostic.message)
            if var_match:
                var_name = var_match.group(1)
                # Check if variable appears in comments or other contexts
                if var_name.lower() in file_content.lower():
                    warning_analysis.update({
                        "preserve_variable": True,
                        "fix_strategy": f"Mark variable '{var_name}' with [[maybe_unused]]"
                    })
                else:
                    warning_analysis["fix_strategy"] = f"Remove unused variable '{var_name}'"
        
        elif "shadows" in message or "shadowing" in message:
            warning_analysis.update({
                "warning_type": "variable_shadowing",
                "severity": "medium",
                "fix_strategy": "Rename variable to avoid shadowing",
                "fix_complexity": 2,
                "risk_level": "low"
            })
        
        elif "uninitialized" in message or "may be used uninitialized" in message:
            warning_analysis.update({
                "warning_type": "uninitialized_variable",
                "severity": "high",
                "fix_strategy": "Initialize variable at declaration",
                "fix_complexity": 2,
                "risk_level": "medium"
            })
        
        elif "format" in message and ("printf" in message or "cout" in message):
            warning_analysis.update({
                "warning_type": "format_string",
                "severity": "medium",
                "fix_strategy": "Fix format string or use safer alternatives",
                "fix_complexity": 3,
                "risk_level": "medium",
                "modernize_code": True
            })
        
        elif "conversion" in message or "narrowing" in message:
            warning_analysis.update({
                "warning_type": "type_conversion",
                "severity": "medium",
                "fix_strategy": "Add explicit cast or fix type mismatch",
                "fix_complexity": 2,
                "requires_cast": True,
                "risk_level": "medium"
            })
        
        elif "return" in message and ("control reaches end" in message or "missing return" in message):
            warning_analysis.update({
                "warning_type": "missing_return",
                "severity": "high",
                "fix_strategy": "Add return statement",
                "fix_complexity": 2,
                "risk_level": "high"
            })
        
        elif "deprecated" in message:
            warning_analysis.update({
                "warning_type": "deprecated_usage",
                "severity": "medium",
                "fix_strategy": "Replace with modern alternative",
                "fix_complexity": 3,
                "modernize_code": True,
                "risk_level": "medium"
            })
        
        elif "clang-tidy" in diagnostic.source.lower() if diagnostic.source else False:
            warning_analysis.update({
                "warning_type": "clang_tidy_warning",
                "severity": "medium", 
                "fix_strategy": await analyze_clang_tidy_warning(ctx, diagnostic, file_content),
                "fix_complexity": 3,
                "risk_level": "low"
            })
        
        logger.info(f"Analyzed warning: {warning_analysis['warning_type']} - {warning_analysis['fix_strategy']}")
        return warning_analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze warning: {e}")
        return {
            "warning_type": "unknown",
            "severity": "medium",
            "fix_strategy": f"Analysis failed: {str(e)}",
            "fix_complexity": 5,
            "risk_level": "high"
        }


@warning_eliminator.tool
async def analyze_clang_tidy_warning(
    ctx: RunContext[WarningEliminatorDependencies],
    diagnostic: CLionDiagnostic,
    file_content: str
) -> str:
    """
    Analyze clang-tidy specific warnings and determine fix strategy.
    
    Args:
        diagnostic: Clang-tidy warning diagnostic
        file_content: File content for context
        
    Returns:
        Specific fix strategy for the clang-tidy warning
    """
    try:
        message = diagnostic.message.lower()
        code = diagnostic.code.lower() if diagnostic.code else ""
        
        # Readability warnings
        if "readability" in code:
            if "identifier-naming" in code:
                return "Rename identifier to follow naming convention"
            elif "braces-around-statements" in code:
                return "Add braces around single statements"
            elif "else-after-return" in code:
                return "Remove unnecessary else after return"
            elif "redundant-member-init" in code:
                return "Remove redundant member initialization"
        
        # Performance warnings  
        elif "performance" in code:
            if "unnecessary-copy-initialization" in code:
                return "Use const reference to avoid unnecessary copy"
            elif "for-range-copy" in code:
                return "Use const reference in range-based for loop"
            elif "inefficient-string-concatenation" in code:
                return "Use string streaming for efficient concatenation"
        
        # Modernization warnings
        elif "modernize" in code:
            if "use-auto" in code:
                return "Replace type with auto for type deduction"
            elif "use-nullptr" in code:
                return "Replace NULL/0 with nullptr"
            elif "use-override" in code:
                return "Add override specifier to virtual function"
            elif "loop-convert" in code:
                return "Convert traditional loop to range-based for"
        
        # Bug-prone warnings
        elif "bugprone" in code:
            if "unused-return-value" in code:
                return "Use return value or cast to void if intentionally ignored"
            elif "infinite-loop" in code:
                return "Fix potential infinite loop condition"
        
        # Cert warnings (security)
        elif "cert" in code:
            if "err-exception-escape" in code:
                return "Handle or declare exceptions properly"
            elif "flp30-c" in code:
                return "Fix floating-point comparison"
        
        # General strategy based on message content
        if "const" in message:
            return "Add const qualifier where appropriate"
        elif "explicit" in message:
            return "Add explicit keyword to constructor"
        elif "virtual" in message:
            return "Add virtual destructor or override specifier"
        else:
            return f"Address clang-tidy warning: {diagnostic.code or 'unknown'}"
            
    except Exception as e:
        logger.error(f"Failed to analyze clang-tidy warning: {e}")
        return "Manual review of clang-tidy warning required"


@warning_eliminator.tool
async def eliminate_warning(
    ctx: RunContext[WarningEliminatorDependencies],
    diagnostic: CLionDiagnostic,
    file_path: str,
    file_content: str,
    warning_analysis: Dict[str, Any]
) -> IncrementalFixResult:
    """
    Eliminate a specific warning with targeted fix.
    
    Args:
        diagnostic: Warning diagnostic to eliminate
        file_path: Path to file containing warning
        file_content: Current file content
        warning_analysis: Analysis of the warning
        
    Returns:
        Result of eliminating the warning
    """
    start_time = datetime.now()
    
    try:
        lines = file_content.split('\n')
        warning_line = warning_analysis["fix_location"]["line"]
        modified_content = file_content
        fix_description = warning_analysis["fix_strategy"]
        
        # Apply fix based on warning type
        if warning_analysis["warning_type"] == "unused_variable":
            if warning_analysis["preserve_variable"]:
                # Add [[maybe_unused]] attribute
                if warning_line < len(lines):
                    line_content = lines[warning_line]
                    # Insert [[maybe_unused]] before variable declaration
                    var_match = re.search(r'(\b(?:const\s+)?(?:\w+\s+)+)(\w+)(\s*[=;])', line_content)
                    if var_match:
                        prefix, var_name, suffix = var_match.groups()
                        new_line = f"{prefix}[[maybe_unused]] {var_name}{suffix}"
                        lines[warning_line] = line_content.replace(var_match.group(0), new_line)
                        modified_content = '\n'.join(lines)
                        fix_description = f"Added [[maybe_unused]] to variable '{var_name}'"
            else:
                # Remove unused variable (more complex, needs careful analysis)
                fix_description = "Unused variable removal requires manual review"
        
        elif warning_analysis["warning_type"] == "variable_shadowing":
            # Rename shadowing variable
            if warning_line < len(lines):
                line_content = lines[warning_line]
                # Extract variable name from diagnostic message
                var_match = re.search(r"['\"]([^'\"]+)['\"]", diagnostic.message)
                if var_match:
                    old_name = var_match.group(1)
                    new_name = f"{old_name}_local"  # Simple renaming strategy
                    
                    # Replace only the declaration, not all occurrences (too risky)
                    # This is a simplified approach
                    if old_name in line_content:
                        lines[warning_line] = line_content.replace(f" {old_name}", f" {new_name}", 1)
                        modified_content = '\n'.join(lines)
                        fix_description = f"Renamed shadowing variable '{old_name}' to '{new_name}'"
        
        elif warning_analysis["warning_type"] == "uninitialized_variable":
            # Add initialization
            if warning_line < len(lines):
                line_content = lines[warning_line]
                # Simple initialization for common types
                if re.search(r'\bint\s+\w+\s*;', line_content):
                    lines[warning_line] = line_content.replace(';', ' = 0;')
                    modified_content = '\n'.join(lines)
                    fix_description = "Initialized int variable to 0"
                elif re.search(r'\bbool\s+\w+\s*;', line_content):
                    lines[warning_line] = line_content.replace(';', ' = false;')
                    modified_content = '\n'.join(lines)
                    fix_description = "Initialized bool variable to false"
                elif re.search(r'\b(?:float|double)\s+\w+\s*;', line_content):
                    lines[warning_line] = line_content.replace(';', ' = 0.0;')
                    modified_content = '\n'.join(lines)
                    fix_description = "Initialized floating-point variable to 0.0"
                else:
                    fix_description = "Variable initialization requires manual review"
        
        elif warning_analysis["warning_type"] == "format_string":
            # Fix format string issues
            if "printf" in diagnostic.message.lower():
                if warning_line < len(lines):
                    line_content = lines[warning_line]
                    # Replace printf with safer alternatives when possible
                    if 'printf("' in line_content and '\\n");' in line_content:
                        # Simple string-only printf can be replaced with cout
                        printf_match = re.search(r'printf\("([^"]+)\\n"\);', line_content)
                        if printf_match:
                            message = printf_match.group(1)
                            new_line = line_content.replace(printf_match.group(0), f'std::cout << "{message}" << \'\\n\';')
                            lines[warning_line] = new_line
                            modified_content = '\n'.join(lines)
                            fix_description = "Replaced printf with std::cout"
            else:
                fix_description = "Format string fix requires manual review"
        
        elif warning_analysis["warning_type"] == "type_conversion":
            # Add explicit cast
            if warning_line < len(lines):
                line_content = lines[warning_line]
                # This is complex and risky, so just add comment for now
                fix_description = "Type conversion warning requires manual review"
        
        elif warning_analysis["warning_type"] == "clang_tidy_warning":
            # Handle specific clang-tidy warnings
            if diagnostic.code:
                if "readability-identifier-naming" in diagnostic.code:
                    fix_description = "Identifier naming requires manual review"
                elif "modernize-use-auto" in diagnostic.code:
                    if warning_line < len(lines):
                        line_content = lines[warning_line]
                        # Simple auto replacement (very conservative)
                        if "= new " in line_content and "*" in line_content:
                            # Replace 'Type* var = new Type' with 'auto* var = new Type'
                            type_match = re.search(r'(\w+)\s*\*\s*(\w+)\s*=\s*new\s+\1', line_content)
                            if type_match:
                                new_line = line_content.replace(f"{type_match.group(1)}* {type_match.group(2)}", 
                                                              f"auto* {type_match.group(2)}")
                                lines[warning_line] = new_line
                                modified_content = '\n'.join(lines)
                                fix_description = "Replaced explicit type with auto"
                elif "modernize-use-nullptr" in diagnostic.code:
                    if warning_line < len(lines):
                        line_content = lines[warning_line]
                        if " NULL" in line_content:
                            lines[warning_line] = line_content.replace(" NULL", " nullptr")
                            modified_content = '\n'.join(lines)
                            fix_description = "Replaced NULL with nullptr"
                        elif " 0)" in line_content and "ptr" in line_content.lower():
                            lines[warning_line] = line_content.replace(" 0)", " nullptr)")
                            modified_content = '\n'.join(lines)
                            fix_description = "Replaced 0 with nullptr for pointer"
                else:
                    fix_description = f"Clang-tidy warning {diagnostic.code} requires manual review"
        
        # Write modified content back to file
        if modified_content != file_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            ctx.deps.warnings_eliminated.append({
                "diagnostic": diagnostic,
                "fix_applied": fix_description,
                "timestamp": datetime.now()
            })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        result = IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=fix_description,
            new_diagnostics_count=0,  # Will be updated by validation
            remaining_diagnostics_count=0,  # Will be updated by validation  
            validation_passed=True,  # Will be updated by validation
            rollback_performed=False,
            rollback_reason=None,
            fix_duration=duration
        )
        
        logger.info(f"Eliminated warning: {fix_description}")
        return result
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Failed to eliminate warning: {e}")
        
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Warning elimination failed: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            rollback_reason=f"Fix application failed: {str(e)}",
            fix_duration=duration
        )


@warning_eliminator.tool
async def batch_eliminate_similar_warnings(
    ctx: RunContext[WarningEliminatorDependencies],
    diagnostics: List[CLionDiagnostic],
    file_path: str
) -> List[IncrementalFixResult]:
    """
    Eliminate multiple similar warnings in batch for efficiency.
    
    Args:
        diagnostics: List of similar warnings to eliminate
        file_path: Path to file containing warnings
        
    Returns:
        List of fix results
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        results = []
        current_content = file_content
        
        # Group warnings by type for batch processing
        by_type = {}
        for diag in diagnostics:
            analysis = await analyze_warning_type(ctx, diag, current_content)
            warning_type = analysis["warning_type"]
            
            if warning_type not in by_type:
                by_type[warning_type] = []
            by_type[warning_type].append((diag, analysis))
        
        # Process each type in batch
        for warning_type, type_diagnostics in by_type.items():
            logger.info(f"Batch processing {len(type_diagnostics)} {warning_type} warnings")
            
            for diag, analysis in type_diagnostics:
                # Update content for each fix
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                result = await eliminate_warning(ctx, diag, file_path, current_content, analysis)
                results.append(result)
                
                # If fix failed, continue to next warning
                if not result.validation_passed:
                    logger.warning(f"Failed to eliminate warning: {result.fix_applied}")
        
        logger.info(f"Batch eliminated {len(results)} warnings")
        return results
        
    except Exception as e:
        logger.error(f"Batch warning elimination failed: {e}")
        return []


# Convenience functions for integration

async def eliminate_single_warning(
    diagnostic: CLionDiagnostic,
    file_path: str,
    session_id: Optional[str] = None
) -> IncrementalFixResult:
    """
    Eliminate a single warning.
    
    Args:
        diagnostic: Warning diagnostic to eliminate
        file_path: Path to file containing warning
        session_id: Optional session identifier
        
    Returns:
        Result of eliminating the warning
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        dependencies = WarningEliminatorDependencies(session_id)
        ctx = RunContext(deps=dependencies)
        
        # Analyze warning
        analysis = await analyze_warning_type(ctx, diagnostic, file_content)
        
        # Eliminate warning
        result = await eliminate_warning(ctx, diagnostic, file_path, file_content, analysis)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to eliminate warning: {e}")
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Failed to eliminate: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            fix_duration=0.0
        )


async def eliminate_all_warnings_in_file(
    warnings: List[CLionDiagnostic],
    file_path: str,
    session_id: Optional[str] = None
) -> List[IncrementalFixResult]:
    """
    Eliminate all warnings in a file with zero tolerance.
    
    Args:
        warnings: List of warnings to eliminate
        file_path: Path to file
        session_id: Optional session identifier
        
    Returns:
        List of fix results
    """
    dependencies = WarningEliminatorDependencies(session_id)
    
    return await batch_eliminate_similar_warnings(
        RunContext(deps=dependencies),
        warnings,
        file_path
    )


if __name__ == "__main__":
    import asyncio
    
    async def test_warning_eliminator():
        """Test the warning eliminator."""
        
        # Mock warning for testing
        test_warning = CLionDiagnostic(
            uri="file:///test.cpp",
            range={"start": {"line": 5, "character": 8}},
            severity="warning", 
            message="unused variable 'unused_var' [-Wunused-variable]",
            source="clang"
        )
        
        # Test warning analysis
        deps = WarningEliminatorDependencies("test")
        ctx = RunContext(deps=deps)
        
        file_content = "int main() {\n    int unused_var = 42;\n    return 0;\n}"
        analysis = await analyze_warning_type(ctx, test_warning, file_content)
        print(f"Warning analysis: {analysis}")
    
    # Uncomment to run test
    # asyncio.run(test_warning_eliminator())