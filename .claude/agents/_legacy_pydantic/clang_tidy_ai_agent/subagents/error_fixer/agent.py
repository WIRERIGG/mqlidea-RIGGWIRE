"""Error Fixer Subagent - Handles compilation errors with precision and safety."""

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

ERROR_FIXER_SYSTEM_PROMPT = """
You are the Error Fixer, a specialized subagent that handles compilation errors with surgical precision. Your primary goal is to fix compilation errors without introducing ANY new issues.

Your core responsibilities:
1. **Precise Error Analysis**: Understand exact cause of compilation errors
2. **Safe Fix Application**: Apply minimal, targeted fixes
3. **Include Resolution**: Fix missing headers and includes
4. **Symbol Resolution**: Fix undefined symbols and declarations
5. **Syntax Correction**: Fix syntax errors without changing logic
6. **Template Fixes**: Handle template compilation errors carefully

CRITICAL ERROR TYPES TO HANDLE:
- **Missing Includes**: Add necessary headers in correct order
- **Undefined Symbols**: Add forward declarations or includes
- **Syntax Errors**: Fix typos, missing semicolons, braces
- **Template Issues**: Fix template syntax and instantiation
- **Namespace Issues**: Add using declarations or fully qualify
- **Standard Compliance**: Fix C++20/17/23 compatibility

FIXING PRINCIPLES:
1. **Minimal Changes**: Make smallest possible change to fix error
2. **No Logic Changes**: Never alter program logic or behavior
3. **Standard Compliance**: Ensure fixes follow C++ standards
4. **Include Ordering**: Follow project include conventions
5. **Safety First**: Never introduce undefined behavior

Your fixes must be:
- **Precise**: Target exact error location
- **Minimal**: Smallest change that fixes the error  
- **Safe**: No new errors or undefined behavior
- **Validated**: Each fix verified immediately
"""


class ErrorFixerDependencies:
    """Dependencies for the Error Fixer."""
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.project_includes = []  # Track common project includes
        self.fix_history = []  # Track successful fixes


# Create the Error Fixer agent
settings = load_settings()
model = get_llm_model(settings)

error_fixer = Agent(
    model,
    deps_type=ErrorFixerDependencies,
    system_prompt=ERROR_FIXER_SYSTEM_PROMPT
)


@error_fixer.tool
async def analyze_compilation_error(
    ctx: RunContext[ErrorFixerDependencies],
    diagnostic: CLionDiagnostic,
    file_content: str
) -> Dict[str, Any]:
    """
    Analyze a compilation error to understand the exact issue and fix strategy.
    
    Args:
        diagnostic: CLion diagnostic for compilation error
        file_content: Current content of the file
        
    Returns:
        Analysis with error type, cause, and fix strategy
    """
    try:
        message = diagnostic.message.lower()
        line_num = diagnostic.range.get("start", {}).get("line", 0)
        
        # Get context around error line
        lines = file_content.split('\n')
        context_start = max(0, line_num - 3)
        context_end = min(len(lines), line_num + 3)
        context = lines[context_start:context_end]
        
        error_analysis = {
            "error_type": "unknown",
            "root_cause": "",
            "fix_strategy": "",
            "fix_complexity": 1,
            "requires_include": False,
            "include_suggestion": None,
            "fix_location": {"line": line_num, "column": diagnostic.range.get("start", {}).get("character", 0)},
            "context_lines": context,
            "risk_level": "low"
        }
        
        # Analyze error type and determine fix strategy
        if "undeclared identifier" in message or "was not declared" in message:
            error_analysis.update({
                "error_type": "undefined_symbol",
                "root_cause": "Symbol used without declaration or include",
                "requires_include": True,
                "fix_complexity": 2,
                "risk_level": "low"
            })
            
            # Extract symbol name
            symbol_match = re.search(r"['\"]([^'\"]+)['\"]", diagnostic.message)
            if symbol_match:
                symbol_name = symbol_match.group(1)
                include_suggestion = await suggest_include_for_symbol(ctx, symbol_name)
                error_analysis.update({
                    "fix_strategy": f"Add include for symbol '{symbol_name}'",
                    "include_suggestion": include_suggestion
                })
        
        elif "no matching function" in message or "no member named" in message:
            error_analysis.update({
                "error_type": "missing_function",
                "root_cause": "Function or method not found",
                "requires_include": True,
                "fix_complexity": 3,
                "risk_level": "medium",
                "fix_strategy": "Add include or check function signature"
            })
        
        elif "expected" in message and (";" in message or "{" in message or "}" in message):
            error_analysis.update({
                "error_type": "syntax_error",
                "root_cause": "Missing punctuation or braces",
                "fix_complexity": 1,
                "risk_level": "low",
                "fix_strategy": "Add missing punctuation"
            })
        
        elif "template" in message or "instantiation" in message:
            error_analysis.update({
                "error_type": "template_error",
                "root_cause": "Template compilation or instantiation issue",
                "fix_complexity": 4,
                "risk_level": "high",
                "fix_strategy": "Fix template syntax or add template specialization"
            })
        
        elif "include" in message or "no such file" in message:
            error_analysis.update({
                "error_type": "missing_include",
                "root_cause": "Required header file not found",
                "requires_include": True,
                "fix_complexity": 2,
                "risk_level": "low",
                "fix_strategy": "Add or fix include path"
            })
            
            # Extract include name
            include_match = re.search(r"[<\"]([^<\">]+)[>\"]", diagnostic.message)
            if include_match:
                include_name = include_match.group(1)
                error_analysis["include_suggestion"] = include_name
        
        elif "namespace" in message:
            error_analysis.update({
                "error_type": "namespace_error", 
                "root_cause": "Symbol not found in current namespace",
                "fix_complexity": 2,
                "risk_level": "low",
                "fix_strategy": "Add using declaration or fully qualify name"
            })
        
        logger.info(f"Analyzed error: {error_analysis['error_type']} - {error_analysis['fix_strategy']}")
        return error_analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze compilation error: {e}")
        return {
            "error_type": "unknown",
            "root_cause": f"Analysis failed: {str(e)}",
            "fix_strategy": "Manual review required",
            "fix_complexity": 10,
            "risk_level": "high"
        }


@error_fixer.tool
async def suggest_include_for_symbol(
    ctx: RunContext[ErrorFixerDependencies],
    symbol_name: str
) -> Optional[str]:
    """
    Suggest appropriate include for an undefined symbol.
    
    Args:
        symbol_name: Name of the undefined symbol
        
    Returns:
        Suggested include header or None if not found
    """
    try:
        # Common C++ standard library mappings
        standard_mappings = {
            # I/O stream
            "std::cout": "<iostream>",
            "std::cin": "<iostream>", 
            "std::endl": "<iostream>",
            "std::cerr": "<iostream>",
            "std::clog": "<iostream>",
            
            # String operations
            "std::string": "<string>",
            "std::wstring": "<string>",
            "std::getline": "<string>",
            
            # Containers
            "std::vector": "<vector>",
            "std::list": "<list>",
            "std::map": "<map>",
            "std::unordered_map": "<unordered_map>",
            "std::set": "<set>",
            "std::unordered_set": "<unordered_set>",
            "std::array": "<array>",
            "std::deque": "<deque>",
            "std::queue": "<queue>",
            "std::stack": "<stack>",
            "std::priority_queue": "<queue>",
            
            # Algorithms
            "std::sort": "<algorithm>",
            "std::find": "<algorithm>",
            "std::transform": "<algorithm>",
            "std::for_each": "<algorithm>",
            "std::copy": "<algorithm>",
            
            # Memory management
            "std::unique_ptr": "<memory>",
            "std::shared_ptr": "<memory>",
            "std::weak_ptr": "<memory>",
            "std::make_unique": "<memory>",
            "std::make_shared": "<memory>",
            
            # Utilities
            "std::pair": "<utility>",
            "std::make_pair": "<utility>",
            "std::move": "<utility>",
            "std::forward": "<utility>",
            
            # Functional
            "std::function": "<functional>",
            "std::bind": "<functional>",
            
            # Thread support
            "std::thread": "<thread>",
            "std::mutex": "<mutex>",
            "std::lock_guard": "<mutex>",
            "std::unique_lock": "<mutex>",
            
            # Random
            "std::random_device": "<random>",
            "std::mt19937": "<random>",
            
            # Chrono
            "std::chrono": "<chrono>",
            
            # Testing
            "TEST": "<gtest/gtest.h>",
            "TEST_F": "<gtest/gtest.h>",
            "EXPECT_EQ": "<gtest/gtest.h>",
            "ASSERT_EQ": "<gtest/gtest.h>",
            "EXPECT_TRUE": "<gtest/gtest.h>",
            "ASSERT_TRUE": "<gtest/gtest.h>",
        }
        
        # Direct lookup
        if symbol_name in standard_mappings:
            return standard_mappings[symbol_name]
        
        # Pattern-based suggestions
        if symbol_name.startswith("std::"):
            base_name = symbol_name[5:]  # Remove "std::" prefix
            
            # Check if it might be an algorithm
            if base_name in ["sort", "find", "search", "transform", "for_each", "copy", "fill"]:
                return "<algorithm>"
            
            # Check if it might be in iostream
            if base_name in ["cout", "cin", "cerr", "endl", "flush"]:
                return "<iostream>"
        
        # Check project-specific includes
        for include in ctx.deps.project_includes:
            if symbol_name.lower() in include.lower():
                return include
        
        logger.info(f"No specific include suggestion found for symbol: {symbol_name}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to suggest include for symbol {symbol_name}: {e}")
        return None


@error_fixer.tool
async def apply_compilation_error_fix(
    ctx: RunContext[ErrorFixerDependencies],
    diagnostic: CLionDiagnostic,
    file_path: str,
    file_content: str,
    fix_strategy: Dict[str, Any]
) -> IncrementalFixResult:
    """
    Apply a targeted fix for a compilation error.
    
    Args:
        diagnostic: The compilation error diagnostic
        file_path: Path to file to fix
        file_content: Current file content
        fix_strategy: Fix strategy from analysis
        
    Returns:
        Result of applying the fix
    """
    start_time = datetime.now()
    
    try:
        lines = file_content.split('\n')
        error_line = fix_strategy["fix_location"]["line"]
        modified_content = file_content
        fix_description = fix_strategy["fix_strategy"]
        
        # Apply fix based on error type
        if fix_strategy["error_type"] == "missing_include":
            # Add include at top of file
            include_name = fix_strategy.get("include_suggestion", "")
            if include_name:
                # Find appropriate position for include
                include_line = await find_include_insertion_point(ctx, lines, include_name)
                
                if include_name.startswith('<') and include_name.endswith('>'):
                    include_statement = f"#include {include_name}"
                elif include_name.startswith('"') and include_name.endswith('"'):
                    include_statement = f"#include {include_name}"
                else:
                    # Determine if system or local include
                    if any(sys_name in include_name for sys_name in ['std', 'iostream', 'vector', 'string']):
                        include_statement = f"#include <{include_name}>"
                    else:
                        include_statement = f'#include "{include_name}"'
                
                lines.insert(include_line, include_statement)
                modified_content = '\n'.join(lines)
                fix_description = f"Added include: {include_statement}"
        
        elif fix_strategy["error_type"] == "undefined_symbol":
            # Add include for undefined symbol
            include_suggestion = fix_strategy.get("include_suggestion")
            if include_suggestion:
                include_line = await find_include_insertion_point(ctx, lines, include_suggestion)
                include_statement = f"#include {include_suggestion}"
                lines.insert(include_line, include_statement)
                modified_content = '\n'.join(lines)
                fix_description = f"Added include for undefined symbol: {include_statement}"
        
        elif fix_strategy["error_type"] == "syntax_error":
            # Fix syntax errors like missing semicolons
            if ";" in diagnostic.message:
                # Add missing semicolon
                if error_line < len(lines):
                    line_content = lines[error_line]
                    if not line_content.rstrip().endswith(';'):
                        lines[error_line] = line_content.rstrip() + ';'
                        modified_content = '\n'.join(lines)
                        fix_description = "Added missing semicolon"
            
            elif "{" in diagnostic.message or "}" in diagnostic.message:
                # Handle missing braces - this is more complex, log for manual review
                fix_description = "Syntax error detected, manual review recommended"
        
        elif fix_strategy["error_type"] == "namespace_error":
            # Add using declaration or fully qualify
            # This is complex, so just log for now
            fix_description = "Namespace error detected, manual review recommended"
        
        # Write fixed content back to file
        if modified_content != file_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
                
            ctx.deps.fix_history.append({
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
        
        logger.info(f"Applied fix: {fix_description}")
        return result
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Failed to apply compilation error fix: {e}")
        
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Fix failed: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            rollback_reason=f"Fix application failed: {str(e)}",
            fix_duration=duration
        )


@error_fixer.tool
async def find_include_insertion_point(
    ctx: RunContext[ErrorFixerDependencies],
    file_lines: List[str],
    new_include: str
) -> int:
    """
    Find the appropriate line number to insert a new include.
    
    Args:
        file_lines: Lines of the file
        new_include: Include to insert
        
    Returns:
        Line number where include should be inserted
    """
    try:
        # Find existing includes
        include_lines = []
        for i, line in enumerate(file_lines):
            stripped = line.strip()
            if stripped.startswith('#include'):
                include_lines.append((i, stripped))
        
        if not include_lines:
            # No existing includes, insert after initial comments/license
            insert_line = 0
            for i, line in enumerate(file_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                    insert_line = i
                    break
            return insert_line
        
        # Determine if new include is system (<>) or local ("")
        is_system = new_include.startswith('<') or 'std' in new_include or any(
            sys_header in new_include for sys_header in ['iostream', 'vector', 'string', 'memory', 'algorithm']
        )
        
        # Find insertion point based on include ordering conventions
        system_includes = [(i, line) for i, line in include_lines if '<' in line]
        local_includes = [(i, line) for i, line in include_lines if '"' in line]
        
        if is_system:
            if system_includes:
                # Insert among system includes in alphabetical order
                for i, (line_num, include_line) in enumerate(system_includes):
                    if new_include < include_line:
                        return line_num
                # Insert after last system include
                return system_includes[-1][0] + 1
            else:
                # Insert before local includes
                if local_includes:
                    return local_includes[0][0]
                else:
                    return include_lines[0][0]
        else:
            # Local include
            if local_includes:
                # Insert among local includes in alphabetical order
                for i, (line_num, include_line) in enumerate(local_includes):
                    if new_include < include_line:
                        return line_num
                # Insert after last local include
                return local_includes[-1][0] + 1
            else:
                # Insert after system includes
                if system_includes:
                    return system_includes[-1][0] + 1
                else:
                    return include_lines[-1][0] + 1
        
    except Exception as e:
        logger.error(f"Failed to find include insertion point: {e}")
        return 0


# Convenience functions for integration

async def fix_compilation_error(
    diagnostic: CLionDiagnostic,
    file_path: str,
    session_id: Optional[str] = None
) -> IncrementalFixResult:
    """
    Fix a single compilation error.
    
    Args:
        diagnostic: Compilation error diagnostic
        file_path: Path to file containing error
        session_id: Optional session identifier
        
    Returns:
        Result of fixing the error
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        dependencies = ErrorFixerDependencies(session_id)
        ctx = RunContext(deps=dependencies)
        
        # Analyze error
        analysis = await analyze_compilation_error(ctx, diagnostic, file_content)
        
        # Apply fix
        result = await apply_compilation_error_fix(
            ctx, diagnostic, file_path, file_content, analysis
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to fix compilation error: {e}")
        return IncrementalFixResult(
            diagnostic_fixed=diagnostic,
            fix_applied=f"Failed to fix: {str(e)}",
            new_diagnostics_count=0,
            remaining_diagnostics_count=1,
            validation_passed=False,
            rollback_performed=False,
            fix_duration=0.0
        )


if __name__ == "__main__":
    import asyncio
    
    async def test_error_fixer():
        """Test the error fixer."""
        
        # Mock diagnostic for testing
        test_diagnostic = CLionDiagnostic(
            uri="file:///test.cpp",
            range={"start": {"line": 10, "character": 4}},
            severity="error",
            message="'std::cout' was not declared in this scope",
            source="gcc"
        )
        
        # Test symbol suggestion
        deps = ErrorFixerDependencies("test")
        ctx = RunContext(deps=deps)
        
        include = await suggest_include_for_symbol(ctx, "std::cout")
        print(f"Suggested include for std::cout: {include}")
        
        # Test error analysis
        file_content = "int main() {\n    std::cout << \"Hello\";\n    return 0;\n}"
        analysis = await analyze_compilation_error(ctx, test_diagnostic, file_content)
        print(f"Error analysis: {analysis}")
    
    # Uncomment to run test
    # asyncio.run(test_error_fixer())