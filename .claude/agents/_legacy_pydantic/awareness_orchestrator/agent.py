"""
Awareness Orchestrator - PydanticAI Agent Implementation.

Coordinates ALL specialized agents in the agents directory for comprehensive analysis:
- Analysis Agent: Code quality and structural analysis
- Architecture Agent: Design patterns and modularization strategies
- Validation Agent: Testing and quality assurance

EXTERNAL AGENT INTEGRATIONS:
- BlitzfireCodeAgent: High-performance code analysis
- BlitzfireCppOptimizer: C++ performance optimization
- ClangTidyAIAgent: Static analysis with AI-powered fixes
- MT5InfiniteReliabilityAgent: MQL5 code optimization
- MultiAgentDebugger: Coordinated multi-tool debugging
- NeverFailBuildResolver: Build problem resolution
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from pydantic_ai import Agent, RunContext

from .models import (
    AgentFindings,
    OrchestrationResult,
    OrchestrationContext,
    Finding,
    Severity,
    AgentType
)
from .dependencies import OrchestrationDeps
from .providers import get_llm_model
from .prompts import (
    ANALYSIS_AGENT_PROMPT,
    ARCHITECTURE_AGENT_PROMPT,
    VALIDATION_AGENT_PROMPT,
    ORCHESTRATOR_PROMPT,
    MQL5_ORCHESTRATOR_PROMPT,
    get_analysis_prompt,
    get_architecture_prompt,
    get_validation_prompt,
    get_mql5_orchestrator_prompt,
    detect_code_type
)

logger = logging.getLogger(__name__)


# ============================================================================
# INTERNAL SUBAGENTS (Core Orchestrator Agents)
# ============================================================================

# Analysis Agent
AnalysisAgent = Agent(
    model=get_llm_model(),
    system_prompt=ANALYSIS_AGENT_PROMPT,
    deps_type=OrchestrationDeps,
    output_type=AgentFindings
)


@AnalysisAgent.tool
async def scan_file(ctx: RunContext[OrchestrationDeps], file_path: str) -> dict:
    """
    Scan file for code quality issues, warnings, and structural problems.

    Args:
        file_path: Path to file to analyze

    Returns:
        Dictionary with suggestions, warnings, and issues found
    """
    suggestions = ctx.deps.get_suggestions(file_path)

    return {
        "file_path": file_path,
        "total_issues": len(suggestions),
        "suggestions": [s.to_dict() for s in suggestions[:20]],
        "message": f"Found {len(suggestions)} potential improvements"
    }


@AnalysisAgent.tool
async def build_project(ctx: RunContext[OrchestrationDeps], target: str = "wire_ground_tests") -> dict:
    """
    Build the project and analyze build output.

    Args:
        target: Build target name

    Returns:
        Build result with warnings and errors
    """
    ctx.deps.emit_progress("build", f"Building target: {target}")
    result = await ctx.deps.build_and_test(target)

    return {
        "success": result.success,
        "duration": result.duration,
        "warnings_count": len(result.warnings),
        "errors_count": len(result.errors),
        "warnings": result.warnings[:10],
        "errors": result.errors[:10]
    }


# Architecture Agent
ArchitectureAgent = Agent(
    model=get_llm_model(),
    system_prompt=ARCHITECTURE_AGENT_PROMPT,
    deps_type=OrchestrationDeps,
    output_type=AgentFindings
)


@ArchitectureAgent.tool
async def get_recommended_agents(ctx: RunContext[OrchestrationDeps], task: str) -> list[str]:
    """
    Get recommended agent sequence based on learned patterns.

    Args:
        task: Task description

    Returns:
        List of recommended agent names in execution order
    """
    context = OrchestrationContext(
        file_path="",
        task_description=task
    )
    return ctx.deps.get_recommended_agents(context)


# Validation Agent
ValidationAgent = Agent(
    model=get_llm_model(),
    system_prompt=VALIDATION_AGENT_PROMPT,
    deps_type=OrchestrationDeps,
    output_type=AgentFindings
)


@ValidationAgent.tool
async def run_tests(ctx: RunContext[OrchestrationDeps], filter_pattern: Optional[str] = None) -> dict:
    """
    Run test suite with optional filtering.

    Args:
        filter_pattern: GoogleTest filter pattern (e.g., "SafetyTestSuite.*")

    Returns:
        Test execution results
    """
    ctx.deps.emit_progress("test", f"Running tests{f' with filter: {filter_pattern}' if filter_pattern else ''}")
    result = await ctx.deps.run_tests(filter_pattern)

    return {
        "success": result.success,
        "total": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "duration": result.duration,
        "failed_tests": result.failed_tests[:10]
    }


# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

awareness_orchestrator = Agent(
    model=get_llm_model(),
    system_prompt=ORCHESTRATOR_PROMPT,
    deps_type=OrchestrationDeps,
    output_type=OrchestrationResult
)


# ============================================================================
# INTERNAL AGENT TOOLS
# ============================================================================

@awareness_orchestrator.tool
async def run_analysis_agent(
    ctx: RunContext[OrchestrationDeps],
    file_path: str,
    context: str = ""
) -> AgentFindings:
    """
    Execute Analysis Agent for code quality assessment.

    Args:
        file_path: File to analyze
        context: Additional context for analysis

    Returns:
        Analysis agent findings
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Analysis Agent")

    prompt = get_analysis_prompt(file_path, context)
    result = await AnalysisAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Analysis Agent completed in {duration:.2f}s")

    return result.data


@awareness_orchestrator.tool
async def run_architecture_agent(
    ctx: RunContext[OrchestrationDeps],
    analysis_findings: str = ""
) -> AgentFindings:
    """
    Execute Architecture Agent for design and modularization analysis.

    Args:
        analysis_findings: Findings from Analysis Agent

    Returns:
        Architecture agent findings
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Architecture Agent")

    prompt = get_architecture_prompt(analysis_findings)
    result = await ArchitectureAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Architecture Agent completed in {duration:.2f}s")

    return result.data


@awareness_orchestrator.tool
async def run_validation_agent(
    ctx: RunContext[OrchestrationDeps],
    analysis_findings: str = "",
    architecture_plan: str = ""
) -> AgentFindings:
    """
    Execute Validation Agent for testing strategy and QA.

    Args:
        analysis_findings: Findings from Analysis Agent
        architecture_plan: Plan from Architecture Agent

    Returns:
        Validation agent findings
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Validation Agent")

    prompt = get_validation_prompt(analysis_findings, architecture_plan)
    result = await ValidationAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Validation Agent completed in {duration:.2f}s")

    return result.data


@awareness_orchestrator.tool
async def record_results(ctx: RunContext[OrchestrationDeps], result: OrchestrationResult):
    """
    Record orchestration results for pattern learning.

    Args:
        result: Complete orchestration result

    Returns:
        Confirmation message
    """
    ctx.deps.record_orchestration(result)
    return {"status": "recorded", "success": result.success}


@awareness_orchestrator.tool
async def show_dashboard(ctx: RunContext[OrchestrationDeps]) -> str:
    """
    Generate and display metrics dashboard.

    Returns:
        Formatted dashboard string
    """
    return ctx.deps.generate_dashboard()


# ============================================================================
# EXTERNAL AGENT INTEGRATION TOOLS
# ============================================================================

@awareness_orchestrator.tool
async def run_blitzfire_code_agent(
    ctx: RunContext[OrchestrationDeps],
    code_content: str,
    mode: str = "general"
) -> Dict[str, Any]:
    """
    Execute BlitzfireCodeAgent for high-performance code analysis.

    Args:
        code_content: Code to analyze
        mode: Analysis mode ("general", "performance", "security")

    Returns:
        Blitzfire analysis results
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Blitzfire Code Agent")

    try:
        from blitzfire_code_agent.agent import quick_analyze
        result = await quick_analyze(code_content, mode)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"Blitzfire Code Agent completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "blitzfire_code_agent",
            "mode": mode,
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result),
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"Blitzfire Code Agent not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"Blitzfire Code Agent error: {e}")
        return {"success": False, "error": str(e)}


@awareness_orchestrator.tool
async def run_blitzfire_cpp_optimizer(
    ctx: RunContext[OrchestrationDeps],
    code: str,
    optimization_type: str = "full"
) -> Dict[str, Any]:
    """
    Execute BlitzfireCppOptimizer for C++ performance optimization.

    Args:
        code: C++ code to optimize
        optimization_type: Type of optimization ("simd", "cache", "algorithm", "full")

    Returns:
        Optimization recommendations and analysis
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Blitzfire C++ Optimizer")

    try:
        from blitzfire_cpp_optimizer.agent import analyze_cpp_performance
        result = await analyze_cpp_performance(code)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"Blitzfire C++ Optimizer completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "blitzfire_cpp_optimizer",
            "optimization_type": optimization_type,
            "result": result if isinstance(result, dict) else str(result),
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"Blitzfire C++ Optimizer not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"Blitzfire C++ Optimizer error: {e}")
        return {"success": False, "error": str(e)}


@awareness_orchestrator.tool
async def run_clang_tidy_ai_agent(
    ctx: RunContext[OrchestrationDeps],
    file_path: str
) -> Dict[str, Any]:
    """
    Execute ClangTidyAIAgent for static analysis with AI-powered fixes.

    Args:
        file_path: Path to C++ file to analyze

    Returns:
        Clang-tidy findings and fix recommendations
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Clang-Tidy AI Agent")

    try:
        from clang_tidy_ai_agent.agent import analyze_cpp_file
        result = await analyze_cpp_file(file_path)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"Clang-Tidy AI Agent completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "clang_tidy_ai_agent",
            "file_path": file_path,
            "result": result,
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"Clang-Tidy AI Agent not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"Clang-Tidy AI Agent error: {e}")
        return {"success": False, "error": str(e)}


@awareness_orchestrator.tool
async def run_mt5_optimizer_agent(
    ctx: RunContext[OrchestrationDeps],
    code: str,
    mode: str = "full",
    ftmo_compliance: bool = True
) -> Dict[str, Any]:
    """
    Execute MT5 Infinite Reliability Agent for MQL5 code optimization.

    Args:
        code: MQL5 code to optimize
        mode: Optimization mode ("analyze", "optimize", "verify", "full")
        ftmo_compliance: Whether to validate FTMO compliance

    Returns:
        MQL5 optimization results with FTMO compliance report
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting MT5 Infinite Reliability Agent")

    try:
        from mt5_infinite_reliability_agent.agent import optimize_mql5_code
        result = await optimize_mql5_code(code, mode=mode, ftmo_compliance=ftmo_compliance)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"MT5 Agent completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "mt5_infinite_reliability_agent",
            "mode": mode,
            "ftmo_compliance": ftmo_compliance,
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result),
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"MT5 Agent not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"MT5 Agent error: {e}")
        return {"success": False, "error": str(e)}


@awareness_orchestrator.tool
async def run_multi_agent_debugger(
    ctx: RunContext[OrchestrationDeps],
    code: str,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Execute MultiAgentDebugger for coordinated multi-tool debugging.

    Args:
        code: Code to debug and analyze
        analysis_type: Type of analysis ("quick", "comprehensive", "deep")

    Returns:
        Coordinated debugging results from multiple tools
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Multi-Agent Debugger")

    try:
        from multi_agent_debugging_system.agent import analyze_cpp_code
        result = await analyze_cpp_code(code)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"Multi-Agent Debugger completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "multi_agent_debugging_system",
            "analysis_type": analysis_type,
            "result": result if isinstance(result, dict) else str(result),
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"Multi-Agent Debugger not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"Multi-Agent Debugger error: {e}")
        return {"success": False, "error": str(e)}


@awareness_orchestrator.tool
async def run_never_fail_build_resolver(
    ctx: RunContext[OrchestrationDeps],
    error_log: str,
    project_path: str,
    resolution_tier: str = "smart"
) -> Dict[str, Any]:
    """
    Execute NeverFailBuildResolver for build problem resolution.

    Args:
        error_log: Build error log content
        project_path: Path to project root
        resolution_tier: Resolution tier ("fast", "smart", "thorough", "emergency")

    Returns:
        Build resolution results with fixes applied
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", f"Starting Never-Fail Build Resolver ({resolution_tier})")

    try:
        if resolution_tier == "fast":
            from never_fail_build_resolver.agent import resolve_build_fast
            result = await resolve_build_fast(error_log, project_path)
        elif resolution_tier == "smart":
            from never_fail_build_resolver.agent import resolve_build_smart
            result = await resolve_build_smart(error_log, project_path)
        elif resolution_tier == "thorough":
            from never_fail_build_resolver.agent import resolve_build_thorough
            result = await resolve_build_thorough(error_log, project_path)
        elif resolution_tier == "emergency":
            from never_fail_build_resolver.agent import resolve_build_emergency
            result = await resolve_build_emergency(error_log, project_path)
        else:
            from never_fail_build_resolver.agent import resolve_build_smart
            result = await resolve_build_smart(error_log, project_path)

        duration = time.time() - start_time
        ctx.deps.emit_progress("agent_complete", f"Build Resolver completed in {duration:.2f}s")

        return {
            "success": True,
            "agent": "never_fail_build_resolver",
            "resolution_tier": resolution_tier,
            "result": result,
            "duration": duration
        }
    except ImportError as e:
        logger.warning(f"Never-Fail Build Resolver not available: {e}")
        return {"success": False, "error": f"Agent not available: {e}"}
    except Exception as e:
        logger.error(f"Build Resolver error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@awareness_orchestrator.tool
async def list_available_agents(ctx: RunContext[OrchestrationDeps]) -> Dict[str, Any]:
    """
    List all available agents and their status.

    Returns:
        Dictionary with available agents and their capabilities
    """
    agents = {
        "internal": {
            "analysis_agent": {
                "status": "available",
                "description": "Code quality and structural analysis",
                "tools": ["scan_file", "build_project"]
            },
            "architecture_agent": {
                "status": "available",
                "description": "Design patterns and modularization strategies",
                "tools": ["get_recommended_agents"]
            },
            "validation_agent": {
                "status": "available",
                "description": "Testing and quality assurance",
                "tools": ["run_tests"]
            }
        },
        "external": {}
    }

    # Check external agent availability
    external_agents = [
        ("blitzfire_code_agent", "blitzfire_code_agent.agent", "High-performance code analysis"),
        ("blitzfire_cpp_optimizer", "blitzfire_cpp_optimizer.agent", "C++ performance optimization"),
        ("clang_tidy_ai_agent", "clang_tidy_ai_agent.agent", "Static analysis with AI fixes"),
        ("mt5_infinite_reliability_agent", "mt5_infinite_reliability_agent.agent", "MQL5 code optimization"),
        ("multi_agent_debugging_system", "multi_agent_debugging_system.agent", "Coordinated multi-tool debugging"),
        ("never_fail_build_resolver", "never_fail_build_resolver.agent", "Build problem resolution")
    ]

    for name, module, description in external_agents:
        try:
            __import__(module)
            agents["external"][name] = {
                "status": "available",
                "description": description
            }
        except ImportError:
            agents["external"][name] = {
                "status": "not_available",
                "description": description
            }

    return agents


@awareness_orchestrator.tool
async def run_agent_chain(
    ctx: RunContext[OrchestrationDeps],
    agent_sequence: List[str],
    initial_input: str,
    file_path: str = ""
) -> Dict[str, Any]:
    """
    Execute a chain of agents in sequence, passing results between them.

    Args:
        agent_sequence: List of agent names to execute in order
        initial_input: Initial input to pass to first agent
        file_path: Optional file path for file-based agents

    Returns:
        Combined results from all agents in the chain
    """
    start_time = time.time()
    ctx.deps.emit_progress("chain_start", f"Starting agent chain: {' -> '.join(agent_sequence)}")

    results = {
        "chain": agent_sequence,
        "agent_results": {},
        "success": True,
        "errors": []
    }

    current_input = initial_input

    agent_runners = {
        "analysis_agent": lambda: run_analysis_agent(ctx, file_path, current_input),
        "architecture_agent": lambda: run_architecture_agent(ctx, current_input),
        "validation_agent": lambda: run_validation_agent(ctx, current_input, ""),
        "blitzfire_code_agent": lambda: run_blitzfire_code_agent(ctx, current_input),
        "blitzfire_cpp_optimizer": lambda: run_blitzfire_cpp_optimizer(ctx, current_input),
        "clang_tidy_ai_agent": lambda: run_clang_tidy_ai_agent(ctx, file_path),
        "mt5_optimizer_agent": lambda: run_mt5_optimizer_agent(ctx, current_input),
        "multi_agent_debugger": lambda: run_multi_agent_debugger(ctx, current_input),
        "never_fail_build_resolver": lambda: run_never_fail_build_resolver(ctx, current_input, file_path)
    }

    for agent_name in agent_sequence:
        if agent_name in agent_runners:
            try:
                agent_result = await agent_runners[agent_name]()
                results["agent_results"][agent_name] = agent_result

                # Pass result to next agent
                if isinstance(agent_result, dict):
                    current_input = str(agent_result.get("result", agent_result))
                else:
                    current_input = str(agent_result)

            except Exception as e:
                results["errors"].append(f"{agent_name}: {str(e)}")
                results["success"] = False
                logger.error(f"Agent chain error at {agent_name}: {e}")
        else:
            results["errors"].append(f"Unknown agent: {agent_name}")

    duration = time.time() - start_time
    results["duration"] = duration
    ctx.deps.emit_progress("chain_complete", f"Agent chain completed in {duration:.2f}s")

    return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def analyze_file(
    file_path: str,
    context: str = "",
    deps: Optional[OrchestrationDeps] = None
) -> AgentFindings:
    """
    Directly run Analysis Agent on a file.

    Args:
        file_path: File to analyze
        context: Additional context
        deps: Dependencies (uses default if not provided)

    Returns:
        Analysis findings
    """
    if deps is None:
        deps = OrchestrationDeps.create_default()

    prompt = get_analysis_prompt(file_path, context)
    result = await AnalysisAgent.run(prompt, deps=deps)
    return result.data


async def orchestrate(
    file_path: str,
    task_description: str,
    deps: Optional[OrchestrationDeps] = None
) -> OrchestrationResult:
    """
    Run complete orchestration workflow.

    Args:
        file_path: File to analyze
        task_description: Description of the orchestration task
        deps: Dependencies (uses default if not provided)

    Returns:
        Complete orchestration result
    """
    if deps is None:
        deps = OrchestrationDeps.create_default()

    start_time = time.time()
    deps.emit_progress("orchestration_start", f"Starting orchestration for: {file_path}")

    prompt = f"""
    Orchestrate a comprehensive analysis of the following:

    File: {file_path}
    Task: {task_description}

    You have access to the following agents:

    INTERNAL AGENTS:
    - run_analysis_agent: Code quality assessment
    - run_architecture_agent: Design recommendations
    - run_validation_agent: Testing strategies

    EXTERNAL AGENTS (call as needed):
    - run_blitzfire_code_agent: High-performance code analysis
    - run_blitzfire_cpp_optimizer: C++ performance optimization
    - run_clang_tidy_ai_agent: Static analysis with AI fixes
    - run_mt5_optimizer_agent: MQL5 code optimization
    - run_multi_agent_debugger: Coordinated multi-tool debugging
    - run_never_fail_build_resolver: Build problem resolution

    UTILITY:
    - list_available_agents: Check which agents are available
    - run_agent_chain: Execute multiple agents in sequence
    - record_results: Save results for learning
    - show_dashboard: Display metrics

    Execute agents in optimal sequence based on the task.
    Provide a comprehensive orchestration result with all findings synthesized.
    """

    result = await awareness_orchestrator.run(prompt, deps=deps)

    total_duration = time.time() - start_time
    deps.emit_progress("orchestration_complete", f"Orchestration completed in {total_duration:.2f}s")

    return result.data


async def orchestrate_with_agents(
    file_path: str,
    task_description: str,
    agent_list: List[str],
    deps: Optional[OrchestrationDeps] = None
) -> Dict[str, Any]:
    """
    Run orchestration with a specific list of agents.

    Args:
        file_path: File to analyze
        task_description: Description of the task
        agent_list: List of agents to use
        deps: Dependencies

    Returns:
        Combined results from specified agents
    """
    if deps is None:
        deps = OrchestrationDeps.create_default()

    # Read file content if it's a file path
    file_content = ""
    if Path(file_path).exists():
        file_content = Path(file_path).read_text()

    # Create a mock context for the chain runner
    class MockContext:
        def __init__(self, d):
            self.deps = d

    mock_ctx = MockContext(deps)

    # Run the agent chain
    result = await run_agent_chain(mock_ctx, agent_list, file_content, file_path)

    return result


async def orchestrate_mql5(
    code: str,
    file_path: str = "",
    ftmo_compliance: bool = True,
    include_architecture: bool = True,
    include_validation: bool = True,
    deps: Optional[OrchestrationDeps] = None
) -> Dict[str, Any]:
    """
    Specialized orchestration for MQL5/EA/Indicator code.

    Uses MT5 Infinite Reliability Agent as PRIMARY agent for deep context,
    then brings in supporting agents for additional insights.

    Args:
        code: MQL5 source code
        file_path: Path to the MQL5 file (for context)
        ftmo_compliance: Whether to validate FTMO compliance
        include_architecture: Include Architecture Agent analysis
        include_validation: Include Validation Agent analysis
        deps: Dependencies

    Returns:
        Comprehensive MQL5 analysis with all agent findings
    """
    if deps is None:
        deps = OrchestrationDeps.create_default()

    start_time = time.time()
    deps.emit_progress("mql5_orchestration_start", f"Starting MQL5 orchestration for: {file_path}")

    results = {
        "code_type": "MQL5",
        "file_path": file_path,
        "agents_used": [],
        "mt5_analysis": None,
        "architecture_analysis": None,
        "validation_analysis": None,
        "ftmo_compliance": None,
        "recommendations": [],
        "success": True,
        "errors": []
    }

    # Create mock context
    class MockContext:
        def __init__(self, d):
            self.deps = d

    mock_ctx = MockContext(deps)

    # STEP 1: MT5 Infinite Reliability Agent (PRIMARY - Deep Context & Planning)
    deps.emit_progress("agent_start", "Starting MT5 Infinite Reliability Agent (Primary)")
    try:
        mt5_result = await run_mt5_optimizer_agent(
            mock_ctx,
            code=code,
            mode="full",
            ftmo_compliance=ftmo_compliance
        )
        results["mt5_analysis"] = mt5_result
        results["agents_used"].append("mt5_infinite_reliability_agent")

        if mt5_result.get("success"):
            # Extract FTMO compliance status
            if "result" in mt5_result:
                result_data = mt5_result["result"]
                if isinstance(result_data, dict):
                    results["ftmo_compliance"] = result_data.get("ftmo_compliance_report")

            deps.emit_progress("agent_complete", "MT5 Agent analysis complete")
        else:
            results["errors"].append(f"MT5 Agent error: {mt5_result.get('error')}")

    except Exception as e:
        logger.error(f"MT5 Agent failed: {e}")
        results["errors"].append(f"MT5 Agent failed: {e}")
        results["success"] = False

    # STEP 2: Architecture Agent (Design Patterns & Modularization)
    if include_architecture and results["mt5_analysis"]:
        deps.emit_progress("agent_start", "Starting Architecture Agent for design insights")
        try:
            # Pass MT5 findings to Architecture Agent
            mt5_findings_str = str(results["mt5_analysis"].get("result", ""))
            arch_result = await run_architecture_agent(mock_ctx, mt5_findings_str)
            results["architecture_analysis"] = arch_result
            results["agents_used"].append("architecture_agent")
            deps.emit_progress("agent_complete", "Architecture Agent complete")
        except Exception as e:
            logger.warning(f"Architecture Agent failed: {e}")
            results["errors"].append(f"Architecture Agent failed: {e}")

    # STEP 3: Validation Agent (Testing Strategy)
    if include_validation and results["mt5_analysis"]:
        deps.emit_progress("agent_start", "Starting Validation Agent for testing strategy")
        try:
            mt5_findings_str = str(results["mt5_analysis"].get("result", ""))
            arch_plan_str = str(results.get("architecture_analysis", ""))
            val_result = await run_validation_agent(mock_ctx, mt5_findings_str, arch_plan_str)
            results["validation_analysis"] = val_result
            results["agents_used"].append("validation_agent")
            deps.emit_progress("agent_complete", "Validation Agent complete")
        except Exception as e:
            logger.warning(f"Validation Agent failed: {e}")
            results["errors"].append(f"Validation Agent failed: {e}")

    # STEP 4: Synthesize Recommendations
    recommendations = []

    # From MT5 Analysis
    if results["mt5_analysis"] and results["mt5_analysis"].get("success"):
        mt5_data = results["mt5_analysis"].get("result", {})
        if isinstance(mt5_data, dict):
            # Extract issues/recommendations from MT5 analysis
            if "issues" in mt5_data:
                for issue in mt5_data.get("issues", [])[:10]:
                    recommendations.append({
                        "source": "mt5_agent",
                        "priority": issue.get("severity", "medium"),
                        "recommendation": issue.get("message", str(issue))
                    })

    # From Architecture Analysis
    if results["architecture_analysis"]:
        if hasattr(results["architecture_analysis"], "findings"):
            for finding in results["architecture_analysis"].findings[:5]:
                recommendations.append({
                    "source": "architecture_agent",
                    "priority": finding.severity if hasattr(finding, 'severity') else "medium",
                    "recommendation": finding.message if hasattr(finding, 'message') else str(finding)
                })

    # From Validation Analysis
    if results["validation_analysis"]:
        if hasattr(results["validation_analysis"], "findings"):
            for finding in results["validation_analysis"].findings[:5]:
                recommendations.append({
                    "source": "validation_agent",
                    "priority": finding.severity if hasattr(finding, 'severity') else "medium",
                    "recommendation": finding.message if hasattr(finding, 'message') else str(finding)
                })

    results["recommendations"] = recommendations

    # Calculate duration
    duration = time.time() - start_time
    results["duration"] = duration
    results["agents_executed"] = len(results["agents_used"])

    deps.emit_progress("mql5_orchestration_complete", f"MQL5 orchestration completed in {duration:.2f}s")

    return results


async def orchestrate_mql5_file(
    file_path: str,
    ftmo_compliance: bool = True,
    deps: Optional[OrchestrationDeps] = None
) -> Dict[str, Any]:
    """
    Orchestrate MQL5 analysis from a file path.

    Args:
        file_path: Path to .mq5 or .mqh file
        ftmo_compliance: Whether to validate FTMO compliance
        deps: Dependencies

    Returns:
        Comprehensive MQL5 analysis
    """
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    code = path.read_text(encoding="utf-8")
    return await orchestrate_mql5(
        code=code,
        file_path=file_path,
        ftmo_compliance=ftmo_compliance,
        deps=deps
    )


def is_mql5_code(code: str, file_path: str = "") -> bool:
    """
    Detect if code is MQL5/EA/Indicator.

    Args:
        code: Source code content
        file_path: Optional file path for extension checking

    Returns:
        True if code appears to be MQL5
    """
    # Check file extension
    if file_path:
        ext = Path(file_path).suffix.lower()
        if ext in ['.mq5', '.mqh', '.mq4', '.mqh']:
            return True

    # Check for MQL5 patterns
    mql5_patterns = [
        'OnInit()',
        'OnTick()',
        'OnDeinit(',
        'OnCalculate(',
        'iMA(',
        'iRSI(',
        'OrderSend(',
        'PositionOpen(',
        '#property indicator',
        '#property copyright',
        'INIT_SUCCEEDED',
        'input int',
        'input double',
        'input string',
        '_Symbol',
        '_Period',
        'PRICE_CLOSE',
        'MODE_SMA'
    ]

    matches = sum(1 for pattern in mql5_patterns if pattern in code)
    return matches >= 3  # At least 3 MQL5 patterns found


async def smart_orchestrate(
    code: str,
    file_path: str = "",
    task_description: str = "",
    deps: Optional[OrchestrationDeps] = None
) -> Dict[str, Any]:
    """
    Smart orchestration that auto-detects code type and routes to appropriate workflow.

    For MQL5/EA/Indicator: Uses MT5 agent as primary
    For C++: Uses standard Analysis → Architecture → Validation workflow

    Args:
        code: Source code content
        file_path: Optional file path
        task_description: Description of the task
        deps: Dependencies

    Returns:
        Orchestration results tailored to code type
    """
    if deps is None:
        deps = OrchestrationDeps.create_default()

    # Auto-detect code type
    if is_mql5_code(code, file_path):
        deps.emit_progress("detection", "Detected MQL5/EA/Indicator code - routing to MT5 agent")
        return await orchestrate_mql5(
            code=code,
            file_path=file_path,
            ftmo_compliance=True,
            include_architecture=True,
            include_validation=True,
            deps=deps
        )
    else:
        deps.emit_progress("detection", "Detected C++ code - using standard orchestration")
        return await orchestrate(file_path, task_description, deps)


# Keep backward compatibility
agent = awareness_orchestrator


__all__ = [
    # Main orchestrator
    "awareness_orchestrator",
    "agent",

    # Internal agents
    "AnalysisAgent",
    "ArchitectureAgent",
    "ValidationAgent",

    # Standard orchestration
    "analyze_file",
    "orchestrate",
    "orchestrate_with_agents",

    # MQL5-SPECIFIC ORCHESTRATION (MT5 Agent Primary)
    "orchestrate_mql5",
    "orchestrate_mql5_file",
    "smart_orchestrate",
    "is_mql5_code",

    # Models
    "AgentFindings",
    "OrchestrationResult",

    # Tools (for external access)
    "run_analysis_agent",
    "run_architecture_agent",
    "run_validation_agent",
    "run_blitzfire_code_agent",
    "run_blitzfire_cpp_optimizer",
    "run_clang_tidy_ai_agent",
    "run_mt5_optimizer_agent",
    "run_multi_agent_debugger",
    "run_never_fail_build_resolver",
    "list_available_agents",
    "run_agent_chain",
]
