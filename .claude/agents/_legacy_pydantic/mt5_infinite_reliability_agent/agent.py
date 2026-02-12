"""
MT5 Infinite Reliability Agent - Pydantic AI Agent Implementation

Advanced MQL5 code optimizer coordinating specialized subagents for comprehensive
optimization of Expert Advisors, indicators, and scripts for MetaTrader 5.

Architecture follows the awareness_orchestrator pattern with multi-agent coordination
and the never-fail-build-resolver escalation strategy.

Target: /Users/shemarrigg/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from pydantic_ai import Agent, RunContext

from .providers import get_llm_model


def get_result_data(result):
    """Safely extract data from agent run result (compatible with different pydantic_ai versions)."""
    # Try different attribute names used across pydantic_ai versions
    if hasattr(result, 'data'):
        return result.data  # Fixed: was causing infinite recursion
    elif hasattr(result, 'output'):
        return result.output
    elif hasattr(result, 'response'):
        return result.response
    elif hasattr(result, 'content'):
        return result.content
    else:
        # If it's a simple type, return as-is
        return str(result)
from .dependencies import AgentDependencies
from .settings import settings
from .models import (
    AgentFindings,
    OptimizationResult,
    OptimizationContext,
    OptimizationIssue,
    OptimizationTransformation,
    FTMOComplianceReport,
    FTMOComplianceCheck,
    Severity,
    AgentType,
    OptimizationDimension,
    EscalationTier,
    AgentHandoff,
)
from .prompts import (
    SYSTEM_PROMPT,
    PARSER_AGENT_PROMPT,
    OPTIMIZER_AGENT_PROMPT,
    FTMO_COMPLIANCE_AGENT_PROMPT,
    VERIFICATION_AGENT_PROMPT,
    DOCUMENTATION_AGENT_PROMPT,
    ORCHESTRATOR_PROMPT,
    get_parser_prompt,
    get_optimizer_prompt,
    get_ftmo_prompt,
    get_verification_prompt,
    get_documentation_prompt,
)
from .tools import register_tools
from .mql5_docs import (
    mql5_docs,
    get_mql5_documentation,
    get_ftmo_compliance_guide,
    get_optimization_template,
    analyze_code_documentation_needs
)
from .external_agents import (
    external_agents,
    get_agent_status,
    consult_debugger as _consult_debugger,
    consult_build_resolver as _consult_build_resolver,
    consult_optimizer as _consult_optimizer,
    gather_opinions as _gather_opinions
)

logger = logging.getLogger(__name__)


# ============================================================================
# SPECIALIZED SUBAGENTS (Following awareness_orchestrator pattern)
# ============================================================================

# Parser Agent - AST Analysis
ParserAgent = Agent(
    model=get_llm_model(),
    system_prompt=PARSER_AGENT_PROMPT,
    deps_type=AgentDependencies,
    output_type=AgentFindings,
    retries=2
)


@ParserAgent.tool
async def parse_mql5_structure(
    ctx: RunContext[AgentDependencies],
    code: str
) -> dict:
    """
    Parse MQL5 source code into structured AST representation.

    Args:
        code: MQL5 source code to parse

    Returns:
        Dictionary with AST, statistics, patterns, and code hash
    """
    from .tools import parse_mql5_code
    result = parse_mql5_code(code)
    logger.info(f"Parsed MQL5: {result['stats']['function_count']} functions, {result['stats']['line_count']} lines")
    return {"success": True, "data": result}


# Optimizer Agent - Performance Optimization
OptimizerAgent = Agent(
    model=get_llm_model(),
    system_prompt=OPTIMIZER_AGENT_PROMPT,
    deps_type=AgentDependencies,
    output_type=AgentFindings,
    retries=2
)


@OptimizerAgent.tool
async def identify_optimization_opportunities(
    ctx: RunContext[AgentDependencies],
    parsed_code: dict,
    dimensions: List[str] = None
) -> dict:
    """
    Identify optimization opportunities in parsed MQL5 code.

    Args:
        parsed_code: Output from parser agent (can be raw result or wrapped in success/data)
        dimensions: Optimization dimensions to evaluate

    Returns:
        List of optimization issues with fix suggestions
    """
    from .tools import analyze_code_quality, parse_mql5_code

    dims = dimensions or ["performance", "memory", "reliability", "ftmo_compliance"]

    # Handle different data formats the LLM might pass
    actual_parsed = parsed_code

    # If wrapped in success/data structure, extract the data
    if isinstance(parsed_code, dict):
        if "data" in parsed_code and isinstance(parsed_code["data"], dict):
            actual_parsed = parsed_code["data"]
        elif "success" in parsed_code and "data" in parsed_code:
            actual_parsed = parsed_code["data"]

    # Validate we have the required 'patterns' key
    if not isinstance(actual_parsed, dict) or "patterns" not in actual_parsed:
        logger.warning("parsed_code missing 'patterns' key, attempting to re-parse if code available")
        # Check if there's raw code we can parse
        if isinstance(parsed_code, str):
            actual_parsed = parse_mql5_code(parsed_code)
        elif isinstance(parsed_code, dict) and "code" in parsed_code:
            actual_parsed = parse_mql5_code(parsed_code["code"])
        else:
            # Create minimal structure to avoid KeyError
            actual_parsed = {
                "patterns": {"loops": 0, "conditions": 0, "indicators": 0, "array_access": 0, "trade_operations": 0, "error_handling": 0},
                "anti_patterns": [],
                "ast": {"event_handlers": [], "functions": [], "inputs": [], "variables": []},
                "stats": {"function_count": 0, "input_count": 0, "variable_count": 0, "line_count": 0, "cyclomatic_complexity": 1}
            }
            logger.warning("Using minimal parsed structure - analysis may be incomplete")

    result = analyze_code_quality(actual_parsed, dims, "medium")
    logger.info(f"Found {result['issues_found']} optimization opportunities")
    return {"success": True, "data": result}


# FTMO Compliance Agent
FTMOComplianceAgent = Agent(
    model=get_llm_model(),
    system_prompt=FTMO_COMPLIANCE_AGENT_PROMPT,
    deps_type=AgentDependencies,
    output_type=FTMOComplianceReport,
    retries=2
)


@FTMOComplianceAgent.tool
async def validate_ftmo_compliance(
    ctx: RunContext[AgentDependencies],
    code: str
) -> dict:
    """
    Validate FTMO compliance in MQL5 code.

    Args:
        code: MQL5 source code to validate

    Returns:
        FTMO compliance report with checks and recommendations
    """
    checks = []

    # Check for drawdown monitoring
    has_drawdown = "drawdown" in code.lower() or "GetCurrentDrawdown" in code
    checks.append(FTMOComplianceCheck(
        rule_name="Drawdown Monitoring",
        passed=has_drawdown,
        description="Code includes drawdown calculation",
        recommendation="Implement GetCurrentDrawdown() method" if not has_drawdown else None
    ))

    # Check for daily loss limit
    has_daily_loss = "daily" in code.lower() and "loss" in code.lower()
    checks.append(FTMOComplianceCheck(
        rule_name="Daily Loss Tracking",
        passed=has_daily_loss,
        description="Code tracks daily loss",
        threshold=5.0,
        recommendation="Add GetDailyLossPercent() method" if not has_daily_loss else None
    ))

    # Check for emergency stop
    has_emergency = "IsTradingAllowed" in code or "StopTrading" in code
    checks.append(FTMOComplianceCheck(
        rule_name="Emergency Stop",
        passed=has_emergency,
        description="Code has trading halt mechanism",
        recommendation="Implement IsTradingAllowed() check" if not has_emergency else None
    ))

    overall = all(c.passed for c in checks)
    recommendations = [c.recommendation for c in checks if c.recommendation]

    return {
        "success": True,
        "data": {
            "overall_compliant": overall,
            "checks": [{"rule": c.rule_name, "passed": c.passed, "desc": c.description} for c in checks],
            "recommendations": recommendations
        }
    }


# Verification Agent - Mathematical Proofs
VerificationAgent = Agent(
    model=get_llm_model(),
    system_prompt=VERIFICATION_AGENT_PROMPT,
    deps_type=AgentDependencies,
    output_type=AgentFindings,
    retries=2
)


@VerificationAgent.tool
async def verify_transformation(
    ctx: RunContext[AgentDependencies],
    original_code: str,
    transformed_code: str,
    transformations: List[dict]
) -> dict:
    """
    Verify that code transformations preserve correctness.

    Args:
        original_code: Original code before transformations
        transformed_code: Code after transformations
        transformations: List of applied transformations

    Returns:
        Verification results with status and confidence score
    """
    from .tools import verify_code_correctness
    result = verify_code_correctness(original_code, transformed_code, transformations)
    logger.info(f"Verification: {'PASSED' if result['verified'] else 'FAILED'}")
    return {"success": True, "data": result}


# Documentation Agent - MQL5 Reference Research
DocumentationAgent = Agent(
    model=get_llm_model(),
    system_prompt=DOCUMENTATION_AGENT_PROMPT,
    deps_type=AgentDependencies,
    output_type=AgentFindings,
    retries=2
)


@DocumentationAgent.tool
async def search_mql5_documentation(
    ctx: RunContext[AgentDependencies],
    query: str,
    focus_areas: List[str] = None
) -> dict:
    """
    Search MQL5 documentation for optimization guidance.

    Args:
        query: Search query for documentation
        focus_areas: Specific documentation sections to search

    Returns:
        Documentation references and best practices
    """
    # Simulated documentation lookup (in production, would use web search)
    references = []

    if "indicator" in query.lower():
        references.append({
            "section": "Technical Indicators",
            "page": 2847,
            "url": "https://www.mql5.com/en/docs/indicators",
            "excerpt": "Indicator handles should be created in OnInit() and released in OnDeinit()",
            "relevance": "Performance optimization for indicator access"
        })

    if "array" in query.lower() or "buffer" in query.lower():
        references.append({
            "section": "Array Functions",
            "page": 1203,
            "url": "https://www.mql5.com/en/docs/array",
            "excerpt": "ArraySetAsSeries() should be called before accessing time series data",
            "relevance": "Proper array handling for time series"
        })

    if "event" in query.lower() or "tick" in query.lower():
        references.append({
            "section": "Event Handling",
            "page": 456,
            "url": "https://www.mql5.com/en/docs/event_handlers",
            "excerpt": "OnTick() is called on every tick - minimize computation",
            "relevance": "Event-driven optimization patterns"
        })

    return {
        "success": True,
        "data": {
            "query": query,
            "references": references,
            "total_found": len(references)
        }
    }


# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

mt5_optimizer = Agent(
    model=get_llm_model(),
    system_prompt=ORCHESTRATOR_PROMPT,
    deps_type=AgentDependencies,
    output_type=OptimizationResult,
    retries=2
)

# Register all tools with main orchestrator
register_tools(mt5_optimizer, AgentDependencies)


@mt5_optimizer.tool
async def run_parser_agent(
    ctx: RunContext[AgentDependencies],
    code: str,
    context: str = ""
) -> AgentFindings:
    """
    Execute Parser Agent for code structure analysis.

    Args:
        code: MQL5 source code to parse
        context: Additional analysis context

    Returns:
        Parser agent findings with code structure
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Parser Agent")

    prompt = get_parser_prompt(ctx.deps.source_code_path or "unknown", context)
    prompt += f"\n\nCode to parse:\n```mql5\n{code[:5000]}...\n```"

    result = await ParserAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Parser Agent completed in {duration:.2f}s")

    return get_result_data(result)


@mt5_optimizer.tool
async def run_optimizer_agent(
    ctx: RunContext[AgentDependencies],
    parser_findings: str = "",
    documentation_refs: str = ""
) -> AgentFindings:
    """
    Execute Optimizer Agent for performance improvements.

    Args:
        parser_findings: Findings from Parser Agent
        documentation_refs: MQL5 documentation references

    Returns:
        Optimizer agent findings with transformations
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Optimizer Agent")

    prompt = get_optimizer_prompt(parser_findings, documentation_refs)
    result = await OptimizerAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Optimizer Agent completed in {duration:.2f}s")

    return get_result_data(result)


@mt5_optimizer.tool
async def run_ftmo_compliance_agent(
    ctx: RunContext[AgentDependencies],
    code: str
) -> FTMOComplianceReport:
    """
    Execute FTMO Compliance Agent for risk validation.

    Args:
        code: MQL5 source code to validate

    Returns:
        FTMO compliance report
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting FTMO Compliance Agent")

    prompt = get_ftmo_prompt(code_structure="", current_implementation=code[:3000])
    result = await FTMOComplianceAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"FTMO Compliance Agent completed in {duration:.2f}s")

    return get_result_data(result)


@mt5_optimizer.tool
async def run_verification_agent(
    ctx: RunContext[AgentDependencies],
    original_code: str,
    transformed_code: str,
    transformations: str
) -> AgentFindings:
    """
    Execute Verification Agent for transformation validation.

    Args:
        original_code: Code before optimization
        transformed_code: Code after optimization
        transformations: List of transformations applied

    Returns:
        Verification agent findings with proofs
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Verification Agent")

    prompt = get_verification_prompt(original_code, transformed_code, transformations)
    result = await VerificationAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Verification Agent completed in {duration:.2f}s")

    return get_result_data(result)


@mt5_optimizer.tool
async def run_documentation_agent(
    ctx: RunContext[AgentDependencies],
    query: str,
    focus_areas: List[str] = None
) -> AgentFindings:
    """
    Execute Documentation Agent for MQL5 reference research.

    Args:
        query: Research query
        focus_areas: Specific areas to research

    Returns:
        Documentation agent findings with references
    """
    start_time = time.time()
    ctx.deps.emit_progress("agent_start", "Starting Documentation Agent")

    prompt = get_documentation_prompt(query, focus_areas)
    result = await DocumentationAgent.run(prompt, deps=ctx.deps)

    duration = time.time() - start_time
    ctx.deps.emit_progress("agent_complete", f"Documentation Agent completed in {duration:.2f}s")

    return get_result_data(result)


@mt5_optimizer.tool
async def escalate_to_agent(
    ctx: RunContext[AgentDependencies],
    target_agent: str,
    reason: str,
    context_data: dict
) -> dict:
    """
    Escalate to another agent for specialized handling.

    Args:
        target_agent: Name of target agent (awareness_orchestrator, multi_agent_debugging_system)
        reason: Reason for escalation
        context_data: Context to pass to target agent

    Returns:
        Escalation result
    """
    handoff = AgentHandoff(
        from_agent=AgentType.OPTIMIZER,
        to_agent=AgentType.VERIFICATION,  # Will be mapped based on target_agent
        reason=reason,
        context_data=context_data,
        priority="immediate"
    )

    ctx.deps.emit_progress("escalation", f"Escalating to {target_agent}: {reason}")

    # Log escalation for external processing
    logger.info(f"ESCALATE: {target_agent} - {reason}")
    logger.info(f"Context: {context_data}")

    return {
        "escalated": True,
        "target_agent": target_agent,
        "reason": reason,
        "handoff_id": f"handoff_{datetime.now().isoformat()}"
    }


# ============================================================================
# MQL5 DOCUMENTATION TOOLS - Always Available
# ============================================================================

@mt5_optimizer.tool
async def lookup_mql5_documentation(
    ctx: RunContext[AgentDependencies],
    query: str,
    category: str = None
) -> dict:
    """
    Search built-in MQL5 documentation reference.

    ALWAYS AVAILABLE: Does not require external agents.

    Use this for:
    - Looking up MQL5 function syntax and usage
    - Finding event handler documentation
    - Getting indicator function references
    - Trading function specifications

    Args:
        query: Search term (e.g., "OnInit", "iMA", "OrderSend")
        category: Optional filter: "event_handlers", "indicator_functions",
                  "trading_functions", "ftmo_compliance", "optimization_patterns"

    Returns:
        Documentation entries matching the query
    """
    ctx.deps.emit_progress("documentation", f"Looking up MQL5 docs: {query}")
    result = get_mql5_documentation(query, category)
    return {"success": True, "data": result}


@mt5_optimizer.tool
async def get_ftmo_rules(
    ctx: RunContext[AgentDependencies]
) -> dict:
    """
    Get complete FTMO compliance rules and requirements.

    ALWAYS AVAILABLE: Does not require external agents.

    Returns:
        Complete FTMO compliance guide including:
        - Daily loss limits (5%)
        - Maximum drawdown limits (10%)
        - Trading restrictions
        - Required protections
    """
    ctx.deps.emit_progress("documentation", "Fetching FTMO compliance rules")
    result = get_ftmo_compliance_guide()
    return {"success": True, "data": result}


@mt5_optimizer.tool
async def get_optimization_code_template(
    ctx: RunContext[AgentDependencies],
    template_type: str
) -> dict:
    """
    Get optimized MQL5 code templates.

    ALWAYS AVAILABLE: Does not require external agents.

    Args:
        template_type: One of:
            - "new_bar_trigger": Efficient new bar detection
            - "indicator_caching": Handle caching pattern
            - "drawdown_monitor": FTMO-compliant drawdown check

    Returns:
        Ready-to-use optimized code template
    """
    ctx.deps.emit_progress("documentation", f"Getting template: {template_type}")
    result = get_optimization_template(template_type)
    return {"success": True, "data": result}


@mt5_optimizer.tool
async def analyze_documentation_needs(
    ctx: RunContext[AgentDependencies],
    code: str
) -> dict:
    """
    Analyze code and identify what documentation would be helpful.

    ALWAYS AVAILABLE: Does not require external agents.

    Args:
        code: MQL5 code to analyze

    Returns:
        Analysis of code features and relevant documentation references
    """
    ctx.deps.emit_progress("documentation", "Analyzing code for documentation needs")
    result = analyze_code_documentation_needs(code)
    return {"success": True, "data": result}


@mt5_optimizer.tool
async def get_external_agent_status(
    ctx: RunContext[AgentDependencies]
) -> dict:
    """
    Check availability status of all external agents.

    ALWAYS AVAILABLE: Reports which agents are live vs using fallbacks.

    Returns:
        Status of each external agent and fallback availability
    """
    ctx.deps.emit_progress("status", "Checking external agent availability")
    result = get_agent_status()
    return {"success": True, "data": result}


# ============================================================================
# EXTERNAL AGENT INTEGRATION - Delegate to Specialized Agents (WITH FALLBACKS)
# ============================================================================

@mt5_optimizer.tool
async def consult_multi_agent_debugger(
    ctx: RunContext[AgentDependencies],
    code: str,
    question: str,
    analysis_type: str = "comprehensive"
) -> dict:
    """
    Consult Multi-Agent Debugging System for coordinated code analysis.

    Use this when you need:
    - Deep debugging insights from multiple specialized tools
    - Coordinated analysis of complex issues
    - Cross-validation of findings from different perspectives

    ALWAYS AVAILABLE: Uses fallback if external agent unavailable.

    Args:
        code: Code to analyze
        question: Specific question to ask the debugger
        analysis_type: "quick", "comprehensive", or "deep"

    Returns:
        Debugging insights and recommendations (with fallback support)
    """
    start_time = time.time()
    ctx.deps.emit_progress("external_agent", "Consulting Multi-Agent Debugger for insights")

    try:
        # Use robust adapter with fallback
        result = await _consult_debugger(code, question, analysis_type)

        ctx.deps.emit_progress(
            "external_agent_complete",
            f"Debugger responded in {result.get('duration', 0):.2f}s (fallback: {result.get('fallback', False)})"
        )

        return {
            "success": True,
            "source": result.get("source", "unknown"),
            "question": question,
            "result": result.get("result", {}),
            "duration": time.time() - start_time,
            "fallback": result.get("fallback", False)
        }
    except Exception as e:
        logger.error(f"Debugger consultation error: {e}")
        return {
            "success": False,
            "source": "error",
            "question": question,
            "error": str(e),
            "duration": time.time() - start_time,
            "fallback": True
        }


@mt5_optimizer.tool
async def consult_build_resolver(
    ctx: RunContext[AgentDependencies],
    problem_description: str,
    error_context: str = "",
    resolution_tier: str = "smart"
) -> dict:
    """
    Consult Never-Fail Build Resolver for build and compilation issues.

    Use this when you need:
    - Help resolving compilation errors in MQL5 code
    - Build configuration recommendations
    - Dependency resolution strategies
    - CMake/build system guidance

    ALWAYS AVAILABLE: Uses fallback if external agent unavailable.

    Args:
        problem_description: Description of the build problem
        error_context: Any error messages or logs
        resolution_tier: "fast", "smart", "thorough", or "emergency"

    Returns:
        Build resolution strategies and recommendations (with fallback support)
    """
    start_time = time.time()
    ctx.deps.emit_progress("external_agent", f"Consulting Build Resolver ({resolution_tier}) for solutions")

    try:
        # Use robust adapter with fallback
        result = await _consult_build_resolver(problem_description, error_context, resolution_tier)

        ctx.deps.emit_progress(
            "external_agent_complete",
            f"Build Resolver responded in {result.get('duration', 0):.2f}s (fallback: {result.get('fallback', False)})"
        )

        return {
            "success": True,
            "source": result.get("source", "unknown"),
            "tier": resolution_tier,
            "problem": problem_description,
            "result": result.get("result", {}),
            "duration": time.time() - start_time,
            "fallback": result.get("fallback", False)
        }
    except Exception as e:
        logger.error(f"Build Resolver consultation error: {e}")
        return {
            "success": False,
            "source": "error",
            "tier": resolution_tier,
            "problem": problem_description,
            "error": str(e),
            "duration": time.time() - start_time,
            "fallback": True
        }


@mt5_optimizer.tool
async def consult_blitzfire_optimizer(
    ctx: RunContext[AgentDependencies],
    code: str,
    optimization_question: str,
    focus_area: str = "performance"
) -> dict:
    """
    Consult Blitzfire Code Agent for high-performance optimization insights.

    Use this when you need:
    - Performance optimization recommendations
    - Algorithm efficiency analysis
    - Memory usage optimization
    - Latency reduction strategies (critical for HFT)

    ALWAYS AVAILABLE: Uses fallback if external agent unavailable.

    Args:
        code: Code to optimize
        optimization_question: Specific optimization question
        focus_area: "performance", "memory", "latency", or "general"

    Returns:
        Performance optimization insights and recommendations (with fallback support)
    """
    start_time = time.time()
    ctx.deps.emit_progress("external_agent", f"Consulting Blitzfire Optimizer for {focus_area} insights")

    try:
        # Use robust adapter with fallback
        result = await _consult_optimizer(code, optimization_question, focus_area)

        ctx.deps.emit_progress(
            "external_agent_complete",
            f"Blitzfire Optimizer responded in {result.get('duration', 0):.2f}s (fallback: {result.get('fallback', False)})"
        )

        return {
            "success": True,
            "source": result.get("source", "unknown"),
            "focus_area": focus_area,
            "question": optimization_question,
            "result": result.get("result", {}),
            "duration": time.time() - start_time,
            "fallback": result.get("fallback", False)
        }
    except Exception as e:
        logger.error(f"Blitzfire Optimizer consultation error: {e}")
        return {
            "success": False,
            "source": "error",
            "focus_area": focus_area,
            "question": optimization_question,
            "error": str(e),
            "duration": time.time() - start_time,
            "fallback": True
        }


@mt5_optimizer.tool
async def delegate_specialized_task(
    ctx: RunContext[AgentDependencies],
    task_type: str,
    task_description: str,
    code_context: str = "",
    questions: List[str] = None
) -> dict:
    """
    Delegate a specialized task to the most appropriate external agent.

    This is the primary delegation tool - it automatically routes tasks
    to the best agent based on the task type.

    Args:
        task_type: Type of task - "debugging", "build", "performance", "analysis"
        task_description: Detailed description of what needs to be done
        code_context: Relevant code for context
        questions: Specific questions to ask the agent

    Returns:
        Combined insights from the delegated agent(s)
    """
    start_time = time.time()
    ctx.deps.emit_progress("delegation", f"Delegating {task_type} task to specialized agent")

    results = {
        "task_type": task_type,
        "task_description": task_description,
        "delegated_to": [],
        "responses": {},
        "success": True
    }

    questions = questions or [task_description]

    # Route to appropriate agent(s)
    if task_type == "debugging":
        for question in questions:
            response = await consult_multi_agent_debugger(ctx, code_context, question)
            results["responses"]["multi_agent_debugger"] = response
            results["delegated_to"].append("multi_agent_debugging_system")

    elif task_type == "build":
        response = await consult_build_resolver(ctx, task_description, code_context)
        results["responses"]["build_resolver"] = response
        results["delegated_to"].append("never_fail_build_resolver")

    elif task_type == "performance":
        for question in questions:
            response = await consult_blitzfire_optimizer(ctx, code_context, question)
            results["responses"]["blitzfire_optimizer"] = response
            results["delegated_to"].append("blitzfire_code_agent")

    elif task_type == "analysis":
        # For comprehensive analysis, consult multiple agents
        debug_response = await consult_multi_agent_debugger(ctx, code_context, task_description, "comprehensive")
        results["responses"]["debugger"] = debug_response
        results["delegated_to"].append("multi_agent_debugging_system")

        perf_response = await consult_blitzfire_optimizer(ctx, code_context, "What are the main performance bottlenecks?")
        results["responses"]["performance"] = perf_response
        results["delegated_to"].append("blitzfire_code_agent")

    else:
        results["success"] = False
        results["error"] = f"Unknown task type: {task_type}. Use: debugging, build, performance, analysis"

    duration = time.time() - start_time
    results["duration"] = duration
    ctx.deps.emit_progress("delegation_complete", f"Task delegation completed in {duration:.2f}s")

    return results


@mt5_optimizer.tool
async def gather_expert_opinions(
    ctx: RunContext[AgentDependencies],
    code: str,
    topic: str,
    questions: List[str]
) -> dict:
    """
    Gather opinions from multiple specialized agents on a specific topic.

    Use this for planning and decision-making when you need:
    - Multiple perspectives on an optimization strategy
    - Validation of your approach from different experts
    - Comprehensive input before making changes

    ALWAYS AVAILABLE: Uses fallbacks if external agents unavailable.

    Args:
        code: The code being analyzed
        topic: The main topic/concern (e.g., "memory optimization", "error handling")
        questions: List of specific questions to ask each agent

    Returns:
        Consolidated expert opinions from all consulted agents (with fallback support)
    """
    start_time = time.time()
    ctx.deps.emit_progress("gathering_opinions", f"Gathering expert opinions on: {topic}")

    try:
        # Use robust adapter with fallback
        result = await _gather_opinions(code, topic, questions)

        ctx.deps.emit_progress(
            "opinions_gathered",
            f"Expert opinions gathered in {result.get('duration', 0):.2f}s"
        )

        return {
            "success": True,
            "topic": topic,
            "agents_consulted": result.get("agents_consulted", []),
            "opinions": result.get("opinions", {}),
            "duration": time.time() - start_time,
            "fallback_used": any(
                o.get("fallback", False)
                for opinions in result.get("opinions", {}).values()
                for o in (opinions if isinstance(opinions, list) else [opinions])
            )
        }
    except Exception as e:
        logger.error(f"Expert opinions gathering error: {e}")
        return {
            "success": False,
            "topic": topic,
            "error": str(e),
            "duration": time.time() - start_time,
            "fallback_used": True
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Keep original agent reference for backward compatibility
agent = mt5_optimizer

logger.info("MT5 Infinite Reliability Agent initialized with subagent orchestration")


async def optimize_mql5_code(
    code: str,
    mode: str = "full",
    ftmo_compliance: bool = True,
    **dependency_overrides
) -> OptimizationResult:
    """
    Optimize MQL5 code using the full subagent workflow.

    Args:
        code: MQL5 source code to optimize
        mode: "analyze", "optimize", "verify", or "full"
        ftmo_compliance: Whether to validate FTMO compliance
        **dependency_overrides: Override default dependencies

    Returns:
        Complete optimization result with all agent findings
    """
    deps = AgentDependencies.from_settings(
        settings,
        analysis_mode=mode,
        **dependency_overrides
    )

    deps.add_snapshot(code)

    try:
        prompt = f"""
        Orchestrate comprehensive MQL5 optimization:

        Mode: {mode}
        FTMO Compliance Required: {ftmo_compliance}

        Execute agents in optimal sequence:
        1. Run documentation_agent to gather MQL5 best practices
        2. Run parser_agent for code structure analysis
        3. Run optimizer_agent for performance improvements
        4. Run ftmo_compliance_agent for risk validation (if required)
        5. Run verification_agent to prove transformation correctness

        Code to optimize:
        ```mql5
        {code[:10000]}
        ```

        Provide comprehensive optimization result with all findings synthesized.
        """

        result = await mt5_optimizer.run(prompt, deps=deps)
        return get_result_data(result)

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        original_code = deps.rollback()
        if original_code:
            logger.info("Rolled back to original code")
        raise


async def optimize_mql5_file(
    file_path: str,
    output_path: Optional[str] = None,
    **kwargs
) -> OptimizationResult:
    """
    Optimize MQL5 file using the full subagent workflow.

    Args:
        file_path: Path to MQL5 source file
        output_path: Optional path to write optimized code
        **kwargs: Additional configuration options

    Returns:
        Complete optimization result
    """
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    code = source_path.read_text(encoding="utf-8")

    deps = AgentDependencies.from_settings(
        settings,
        source_code_path=source_path,
        output_path=Path(output_path) if output_path else None,
        **kwargs
    )

    deps.add_snapshot(code)

    try:
        result = await optimize_mql5_code(code, **kwargs)

        if output_path and result.optimized_code:
            output_file = Path(output_path)
            output_file.write_text(result.optimized_code, encoding="utf-8")
            logger.info(f"Optimized code written to: {output_path}")

        return result

    except Exception as e:
        logger.error(f"File optimization failed: {e}")
        original_code = deps.rollback()
        if original_code:
            logger.info("Rolled back to original code")
        raise


def create_agent_with_deps(**dependency_overrides) -> tuple:
    """
    Create agent instance with custom dependencies.

    Args:
        **dependency_overrides: Custom dependency values

    Returns:
        Tuple of (orchestrator_agent, dependencies)
    """
    deps = AgentDependencies.from_settings(settings, **dependency_overrides)
    return mt5_optimizer, deps


# Legacy compatibility
async def analyze_mql5_code(code: str, mode: str = "full", **kwargs) -> dict:
    """Legacy function - redirects to optimize_mql5_code."""
    result = await optimize_mql5_code(code, mode=mode, **kwargs)
    return {
        "success": result.success,
        "findings": [f.__dict__ for f in result.get_all_issues()],
        "transformations": [t.__dict__ for t in result.transformations],
        "optimized_code": result.optimized_code
    }


async def analyze_mql5_file(file_path: str, output_path: Optional[str] = None, **kwargs) -> dict:
    """Legacy function - redirects to optimize_mql5_file."""
    result = await optimize_mql5_file(file_path, output_path, **kwargs)
    return {
        "success": result.success,
        "findings": [f.__dict__ for f in result.get_all_issues()],
        "optimized_code": result.optimized_code
    }


__all__ = [
    # Main orchestrator
    "mt5_optimizer",
    "agent",

    # Internal subagents
    "ParserAgent",
    "OptimizerAgent",
    "FTMOComplianceAgent",
    "VerificationAgent",
    "DocumentationAgent",

    # Main functions
    "optimize_mql5_code",
    "optimize_mql5_file",
    "analyze_mql5_code",
    "analyze_mql5_file",
    "create_agent_with_deps",

    # MQL5 Documentation tools (ALWAYS AVAILABLE)
    "lookup_mql5_documentation",
    "get_ftmo_rules",
    "get_optimization_code_template",
    "analyze_documentation_needs",
    "get_external_agent_status",

    # External agent delegation tools (WITH FALLBACKS)
    "consult_multi_agent_debugger",
    "consult_build_resolver",
    "consult_blitzfire_optimizer",
    "delegate_specialized_task",
    "gather_expert_opinions",

    # Documentation service
    "mql5_docs",
    "external_agents",
]
