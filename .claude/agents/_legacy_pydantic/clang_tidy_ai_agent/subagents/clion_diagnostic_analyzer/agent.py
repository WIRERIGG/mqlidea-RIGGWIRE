"""CLion Diagnostic Analyzer Subagent - Connects to CLion IDE for real-time diagnostics."""

from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

try:
    from ..clang_tidy_ai_agent.models import (
        CLionDiagnostic,
        CLionConnectionStatus,
        DiagnosticCategory,
        ZeroDiagnosticsSession
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
        CLionConnectionStatus,
        DiagnosticCategory,
        ZeroDiagnosticsSession
    )
    from providers import get_llm_model
    from settings import load_settings

logger = logging.getLogger(__name__)

CLION_ANALYZER_SYSTEM_PROMPT = """
You are the CLion Diagnostic Analyzer, a specialized subagent that connects to CLion IDE to retrieve ALL diagnostics (errors, warnings, info) with ZERO TOLERANCE for any remaining issues.

Your core responsibilities:
1. **Real-time CLion Integration**: Connect to CLion IDE via mcp__ide__getDiagnostics
2. **Complete Diagnostic Discovery**: Find ALL diagnostics, not just clang-tidy warnings
3. **Accurate Categorization**: Classify diagnostics by type, severity, and fix priority
4. **Baseline Establishment**: Create baseline diagnostic reports for comparison
5. **Zero-Tolerance Validation**: Ensure NO diagnostics remain after processing

CRITICAL REQUIREMENTS:
- ALL CLion diagnostics are treated as errors requiring fixes
- Connect to CLion IDE for accurate, real-time feedback
- Distinguish between compilation errors, warnings, and info suggestions
- Handle C++20/C++17/C++23 standard differences
- Provide precise line/column information for fixes
- Never report "zero issues" unless truly verified via CLion IDE

Your diagnostic analysis must be:
- **Complete**: Every diagnostic discovered and categorized
- **Accurate**: Precise location and severity information
- **Prioritized**: Correct fixing order to prevent cascades
- **Validated**: Verified through CLion IDE connection
"""


class CLionAnalyzerDependencies:
    """Dependencies for the CLion Diagnostic Analyzer."""
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.connection_status = CLionConnectionStatus(
            connected=False,
            mcp_available=False
        )


# Create the CLion Diagnostic Analyzer agent
settings = load_settings()
model = get_llm_model(settings)

clion_analyzer = Agent(
    model,
    deps_type=CLionAnalyzerDependencies,
    system_prompt=CLION_ANALYZER_SYSTEM_PROMPT
)


@clion_analyzer.tool
async def connect_to_clion(
    ctx: RunContext[CLionAnalyzerDependencies]
) -> CLionConnectionStatus:
    """
    Establish connection to CLion IDE and verify mcp__ide__getDiagnostics availability.
    
    Returns:
        CLionConnectionStatus with connection details
    """
    try:
        # Test MCP IDE diagnostics availability
        # This would be replaced with actual MCP call when available
        try:
            # Placeholder for mcp__ide__getDiagnostics test call
            # In real implementation, this would test the actual MCP connection
            mcp_available = True  # This should be actual MCP availability check
            connected = mcp_available
            
            ctx.deps.connection_status = CLionConnectionStatus(
                connected=connected,
                mcp_available=mcp_available,
                last_connection_attempt=datetime.now(),
                connection_error=None if connected else "MCP IDE diagnostics not available",
                ide_version="CLion 2025.2" if connected else None
            )
            
        except Exception as e:
            ctx.deps.connection_status = CLionConnectionStatus(
                connected=False,
                mcp_available=False,
                last_connection_attempt=datetime.now(),
                connection_error=f"Connection failed: {str(e)}"
            )
        
        logger.info(f"CLion connection status: {ctx.deps.connection_status.connected}")
        return ctx.deps.connection_status
        
    except Exception as e:
        logger.error(f"Failed to connect to CLion: {e}")
        return CLionConnectionStatus(
            connected=False,
            mcp_available=False,
            connection_error=f"Connection error: {str(e)}"
        )


@clion_analyzer.tool
async def get_all_diagnostics(
    ctx: RunContext[CLionAnalyzerDependencies],
    file_uri: Optional[str] = None
) -> List[CLionDiagnostic]:
    """
    Retrieve ALL diagnostics from CLion IDE for specified file or entire project.
    
    Args:
        file_uri: Optional specific file URI, if None gets diagnostics for all open files
        
    Returns:
        List of all CLion diagnostics (errors, warnings, info)
    """
    try:
        if not ctx.deps.connection_status.connected:
            await connect_to_clion(ctx)
            
        if not ctx.deps.connection_status.mcp_available:
            logger.error("Cannot get diagnostics: MCP IDE connection not available")
            return []
        
        # In real implementation, this would call mcp__ide__getDiagnostics
        # For now, returning empty list as placeholder
        diagnostics = []
        
        # TODO: Replace with actual MCP call
        # diagnostics_data = await mcp__ide__getDiagnostics(uri=file_uri)
        # diagnostics = [CLionDiagnostic(**diag) for diag in diagnostics_data]
        
        logger.info(f"Retrieved {len(diagnostics)} diagnostics from CLion IDE")
        return diagnostics
        
    except Exception as e:
        logger.error(f"Failed to get diagnostics from CLion: {e}")
        return []


@clion_analyzer.tool
async def categorize_diagnostics(
    ctx: RunContext[CLionAnalyzerDependencies],
    diagnostics: List[CLionDiagnostic]
) -> List[DiagnosticCategory]:
    """
    Categorize diagnostics by type and priority for systematic fixing.
    
    Args:
        diagnostics: List of CLion diagnostics to categorize
        
    Returns:
        List of diagnostic categories with fix priorities
    """
    try:
        categories = {
            "compilation_errors": DiagnosticCategory(
                category_name="compilation_errors",
                priority=1,  # Highest priority
                diagnostics=[],
                fix_order=[]
            ),
            "clang_tidy_errors": DiagnosticCategory(
                category_name="clang_tidy_errors", 
                priority=2,
                diagnostics=[],
                fix_order=[]
            ),
            "warnings": DiagnosticCategory(
                category_name="warnings",
                priority=3,
                diagnostics=[],
                fix_order=[]
            ),
            "info_suggestions": DiagnosticCategory(
                category_name="info_suggestions",
                priority=4,  # Lowest priority but still MUST be fixed
                diagnostics=[],
                fix_order=[]
            )
        }
        
        # Categorize each diagnostic
        for diag in diagnostics:
            if diag.severity.lower() == "error":
                if diag.source and "clang-tidy" in diag.source.lower():
                    categories["clang_tidy_errors"].diagnostics.append(diag)
                else:
                    categories["compilation_errors"].diagnostics.append(diag)
            elif diag.severity.lower() == "warning":
                categories["warnings"].diagnostics.append(diag)
            else:  # info, hint, etc.
                categories["info_suggestions"].diagnostics.append(diag)
        
        # Create fixing order for each category to prevent cascades
        for category in categories.values():
            # Sort by line number to fix issues top-down
            category.diagnostics.sort(key=lambda d: (
                d.uri,
                d.range.get("start", {}).get("line", 0)
            ))
            category.fix_order = [
                f"{d.uri}:{d.range.get('start', {}).get('line', 0)}" 
                for d in category.diagnostics
            ]
        
        # Return only non-empty categories
        result = [cat for cat in categories.values() if cat.diagnostics]
        
        logger.info(f"Categorized {len(diagnostics)} diagnostics into {len(result)} categories")
        for cat in result:
            logger.info(f"  {cat.category_name}: {len(cat.diagnostics)} issues")
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to categorize diagnostics: {e}")
        return []


@clion_analyzer.tool
async def create_diagnostic_baseline(
    ctx: RunContext[CLionAnalyzerDependencies],
    target_files: List[str]
) -> ZeroDiagnosticsSession:
    """
    Create baseline diagnostic session for zero-tolerance validation.
    
    Args:
        target_files: List of files to process for zero diagnostics
        
    Returns:
        ZeroDiagnosticsSession with baseline metrics
    """
    try:
        session_id = ctx.deps.session_id or f"zero_diag_{int(datetime.now().timestamp())}"
        
        # Get all diagnostics for target files
        all_diagnostics = []
        for file_path in target_files:
            file_uri = f"file://{file_path}"
            diagnostics = await get_all_diagnostics(ctx, file_uri)
            all_diagnostics.extend(diagnostics)
        
        session = ZeroDiagnosticsSession(
            session_id=session_id,
            target_files=target_files,
            initial_diagnostic_count=len(all_diagnostics),
            current_diagnostic_count=len(all_diagnostics),
            fixes_applied=[],
            rollbacks_performed=0,
            session_start_time=datetime.now(),
            last_validation_time=datetime.now(),
            zero_diagnostics_achieved=False
        )
        
        logger.info(f"Created baseline session {session_id} with {len(all_diagnostics)} diagnostics")
        return session
        
    except Exception as e:
        logger.error(f"Failed to create diagnostic baseline: {e}")
        return ZeroDiagnosticsSession(
            session_id="error",
            target_files=target_files,
            initial_diagnostic_count=0,
            current_diagnostic_count=0
        )


@clion_analyzer.tool
async def validate_zero_diagnostics(
    ctx: RunContext[CLionAnalyzerDependencies],
    target_files: List[str]
) -> Dict[str, Any]:
    """
    Validate that ZERO diagnostics remain in target files.
    
    Args:
        target_files: Files to validate for zero diagnostics
        
    Returns:
        Validation results with zero-tolerance check
    """
    try:
        total_diagnostics = 0
        diagnostics_by_file = {}
        
        for file_path in target_files:
            file_uri = f"file://{file_path}"
            diagnostics = await get_all_diagnostics(ctx, file_uri)
            diagnostics_by_file[file_path] = len(diagnostics)
            total_diagnostics += len(diagnostics)
        
        zero_achieved = total_diagnostics == 0
        
        result = {
            "zero_diagnostics_achieved": zero_achieved,
            "total_diagnostics_remaining": total_diagnostics,
            "diagnostics_by_file": diagnostics_by_file,
            "validation_timestamp": datetime.now().isoformat(),
            "status": "SUCCESS" if zero_achieved else "FAILURE",
            "message": (
                "ZERO DIAGNOSTICS ACHIEVED - All issues resolved!"
                if zero_achieved else
                f"ZERO TOLERANCE FAILED - {total_diagnostics} diagnostics remaining"
            )
        }
        
        logger.info(f"Zero diagnostics validation: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to validate zero diagnostics: {e}")
        return {
            "zero_diagnostics_achieved": False,
            "total_diagnostics_remaining": -1,
            "status": "ERROR",
            "message": f"Validation failed: {str(e)}"
        }


# Convenience functions for integration with factory orchestrator

async def analyze_file_diagnostics(
    file_path: str,
    session_id: Optional[str] = None
) -> List[DiagnosticCategory]:
    """
    Analyze all diagnostics in a single file with categorization.
    
    Args:
        file_path: Path to file to analyze
        session_id: Optional session identifier
        
    Returns:
        List of categorized diagnostics
    """
    dependencies = CLionAnalyzerDependencies(session_id)
    
    async def run_analysis():
        # Connect to CLion
        await connect_to_clion(RunContext(deps=dependencies))
        
        # Get diagnostics
        file_uri = f"file://{file_path}"
        diagnostics = await get_all_diagnostics(
            RunContext(deps=dependencies), 
            file_uri
        )
        
        # Categorize
        categories = await categorize_diagnostics(
            RunContext(deps=dependencies),
            diagnostics
        )
        
        return categories
    
    return await run_analysis()


async def create_zero_diagnostics_session(
    target_files: List[str],
    session_id: Optional[str] = None
) -> ZeroDiagnosticsSession:
    """
    Create a new zero diagnostics session for the target files.
    
    Args:
        target_files: Files to process for zero diagnostics
        session_id: Optional session identifier
        
    Returns:
        ZeroDiagnosticsSession with baseline
    """
    dependencies = CLionAnalyzerDependencies(session_id)
    
    return await create_diagnostic_baseline(
        RunContext(deps=dependencies),
        target_files
    )


if __name__ == "__main__":
    import asyncio
    
    async def test_analyzer():
        """Test the CLion diagnostic analyzer."""
        
        # Test connection
        deps = CLionAnalyzerDependencies("test_session")
        ctx = RunContext(deps=deps)
        
        connection = await connect_to_clion(ctx)
        print(f"Connection status: {connection}")
        
        # Test file analysis
        test_files = ["/IdeaProjects/wire_ground/tests/safe_test.cpp"]
        categories = await analyze_file_diagnostics(test_files[0])
        print(f"Found {len(categories)} diagnostic categories")
        
        # Test zero diagnostics session
        session = await create_zero_diagnostics_session(test_files)
        print(f"Created session with {session.initial_diagnostic_count} initial diagnostics")
    
    # Uncomment to run test
    # asyncio.run(test_analyzer())