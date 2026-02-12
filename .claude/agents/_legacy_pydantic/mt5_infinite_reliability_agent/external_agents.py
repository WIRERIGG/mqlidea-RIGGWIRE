"""
External Agent Adapters for MT5 Infinite Reliability Agent

Provides robust access to external agents with graceful fallbacks.
Ensures 100% availability even when external agents have issues.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# EXTERNAL AGENT STATUS TRACKING
# ============================================================================

class ExternalAgentRegistry:
    """Registry for tracking external agent availability."""

    def __init__(self):
        self.agents = {}
        self.last_check = None

    def register(self, name: str, status: str, capabilities: List[str]):
        """Register an external agent."""
        self.agents[name] = {
            "status": status,
            "capabilities": capabilities,
            "last_check": datetime.now().isoformat()
        }

    def get_status(self, name: str) -> Dict[str, Any]:
        """Get agent status."""
        return self.agents.get(name, {"status": "unknown"})

    def is_available(self, name: str) -> bool:
        """Check if agent is available."""
        return self.agents.get(name, {}).get("status") == "available"

    def list_available(self) -> List[str]:
        """List all available agents."""
        return [name for name, info in self.agents.items() if info["status"] == "available"]


# Global registry
agent_registry = ExternalAgentRegistry()


# ============================================================================
# MULTI-AGENT DEBUGGING SYSTEM ADAPTER
# ============================================================================

class MultiAgentDebuggerAdapter:
    """Adapter for Multi-Agent Debugging System with fallback."""

    def __init__(self):
        self.available = False
        self.error = None
        self._check_availability()

    def _check_availability(self):
        """Check if the agent is available."""
        try:
            from multi_agent_debugging_system.agent import analyze_cpp_code
            self.available = True
            self._analyze_func = analyze_cpp_code
            agent_registry.register(
                "multi_agent_debugging_system",
                "available",
                ["debugging", "code_analysis", "coordination"]
            )
        except Exception as e:
            self.available = False
            self.error = str(e)
            agent_registry.register(
                "multi_agent_debugging_system",
                "unavailable",
                []
            )
            logger.debug(f"Multi-Agent Debugger unavailable: {e}")

    async def analyze(self, code: str, question: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze code with Multi-Agent Debugger or fallback.

        Args:
            code: Code to analyze
            question: Question to ask
            analysis_type: Type of analysis

        Returns:
            Analysis results
        """
        start_time = time.time()

        if self.available:
            try:
                result = await self._analyze_func(code)
                return {
                    "success": True,
                    "source": "multi_agent_debugging_system",
                    "question": question,
                    "result": result,
                    "duration": time.time() - start_time,
                    "fallback": False
                }
            except Exception as e:
                logger.warning(f"Multi-Agent Debugger failed, using fallback: {e}")

        # Fallback: Provide basic debugging insights
        return self._fallback_analysis(code, question, start_time)

    def _fallback_analysis(self, code: str, question: str, start_time: float) -> Dict[str, Any]:
        """Provide fallback debugging analysis."""
        insights = []

        # Basic code analysis
        if "memory" in question.lower():
            if "ArrayResize" in code and "ArrayFree" not in code:
                insights.append("Potential memory issue: ArrayResize without ArrayFree")
            if "new " in code and "delete" not in code:
                insights.append("Potential memory leak: 'new' without 'delete'")

        if "error" in question.lower() or "issue" in question.lower():
            if "GetLastError" not in code:
                insights.append("Missing error checking: Consider using GetLastError()")
            if "INVALID_HANDLE" not in code and "iMA" in code:
                insights.append("Missing handle validation: Check for INVALID_HANDLE after indicator creation")

        if "performance" in question.lower():
            if code.count("iMA(") > 1 and "OnInit" not in code[:500]:
                insights.append("Performance: Create indicator handles in OnInit(), not repeatedly")

        if not insights:
            insights.append("Basic analysis complete. For detailed debugging, ensure multi_agent_debugging_system is available.")

        return {
            "success": True,
            "source": "fallback_analyzer",
            "question": question,
            "result": {
                "insights": insights,
                "note": "Using built-in fallback analysis"
            },
            "duration": time.time() - start_time,
            "fallback": True
        }


# ============================================================================
# NEVER-FAIL BUILD RESOLVER ADAPTER
# ============================================================================

class BuildResolverAdapter:
    """Adapter for Never-Fail Build Resolver with fallback."""

    def __init__(self):
        self.available = False
        self.error = None
        self._check_availability()

    def _check_availability(self):
        """Check if the agent is available."""
        try:
            from never_fail_build_resolver.agent import resolve_build_fast
            self.available = True
            self._resolve_funcs = {
                "fast": resolve_build_fast
            }
            try:
                from never_fail_build_resolver.agent import resolve_build_smart
                self._resolve_funcs["smart"] = resolve_build_smart
            except:
                pass
            try:
                from never_fail_build_resolver.agent import resolve_build_thorough
                self._resolve_funcs["thorough"] = resolve_build_thorough
            except:
                pass

            agent_registry.register(
                "never_fail_build_resolver",
                "available",
                ["build_resolution", "compilation", "cmake"]
            )
        except Exception as e:
            self.available = False
            self.error = str(e)
            agent_registry.register(
                "never_fail_build_resolver",
                "unavailable",
                []
            )
            logger.debug(f"Build Resolver unavailable: {e}")

    async def resolve(self, problem: str, error_context: str = "", tier: str = "smart") -> Dict[str, Any]:
        """
        Resolve build problems or provide fallback guidance.

        Args:
            problem: Problem description
            error_context: Error messages
            tier: Resolution tier

        Returns:
            Resolution results
        """
        start_time = time.time()

        if self.available and tier in self._resolve_funcs:
            try:
                result = await self._resolve_funcs[tier](error_context, ".")
                return {
                    "success": True,
                    "source": "never_fail_build_resolver",
                    "tier": tier,
                    "result": result,
                    "duration": time.time() - start_time,
                    "fallback": False
                }
            except Exception as e:
                logger.warning(f"Build Resolver failed, using fallback: {e}")

        # Fallback: Provide MQL5-specific build guidance
        return self._fallback_resolution(problem, error_context, start_time)

    def _fallback_resolution(self, problem: str, error_context: str, start_time: float) -> Dict[str, Any]:
        """Provide fallback build resolution for MQL5."""
        solutions = []
        context_lower = (problem + " " + error_context).lower()

        # MQL5 compilation errors
        if "undeclared identifier" in context_lower:
            solutions.append("Check variable declaration: Ensure all variables are declared before use")
            solutions.append("Verify include files: Add necessary #include directives")

        if "type mismatch" in context_lower:
            solutions.append("Check type compatibility: Ensure assignment types match")
            solutions.append("Use explicit type casting if needed: (double)value or (int)value")

        if "indicator" in context_lower or "handle" in context_lower:
            solutions.append("Verify indicator initialization in OnInit()")
            solutions.append("Check for INVALID_HANDLE after indicator creation")

        if "array" in context_lower:
            solutions.append("Ensure ArraySetAsSeries() is called for time-series access")
            solutions.append("Check array sizing with ArrayResize()")

        if "order" in context_lower or "trade" in context_lower:
            solutions.append("Verify MqlTradeRequest structure is properly filled")
            solutions.append("Check account permissions for trading")

        if not solutions:
            solutions = [
                "Verify syntax and semicolons",
                "Check include file paths",
                "Ensure all functions are properly closed with braces",
                "Compile with verbose errors in MetaEditor"
            ]

        return {
            "success": True,
            "source": "fallback_resolver",
            "tier": "fallback",
            "result": {
                "solutions": solutions,
                "note": "Using built-in MQL5 compilation guidance"
            },
            "duration": time.time() - start_time,
            "fallback": True
        }


# ============================================================================
# BLITZFIRE CODE AGENT ADAPTER
# ============================================================================

class BlitzfireOptimizerAdapter:
    """Adapter for Blitzfire Code Agent with fallback."""

    def __init__(self):
        self.available = False
        self.error = None
        self._check_availability()

    def _check_availability(self):
        """Check if the agent is available."""
        try:
            from blitzfire_code_agent.agent import quick_analyze
            self.available = True
            self._analyze_func = quick_analyze
            agent_registry.register(
                "blitzfire_code_agent",
                "available",
                ["performance", "optimization", "hft"]
            )
        except Exception as e:
            self.available = False
            self.error = str(e)
            agent_registry.register(
                "blitzfire_code_agent",
                "unavailable",
                []
            )
            logger.debug(f"Blitzfire Optimizer unavailable: {e}")

    async def optimize(self, code: str, question: str, focus: str = "performance") -> Dict[str, Any]:
        """
        Get optimization insights or provide fallback.

        Args:
            code: Code to optimize
            question: Optimization question
            focus: Focus area

        Returns:
            Optimization results
        """
        start_time = time.time()

        if self.available:
            try:
                result = await self._analyze_func(code, mode=focus)
                return {
                    "success": True,
                    "source": "blitzfire_code_agent",
                    "focus": focus,
                    "result": result.model_dump() if hasattr(result, 'model_dump') else result,
                    "duration": time.time() - start_time,
                    "fallback": False
                }
            except Exception as e:
                logger.warning(f"Blitzfire Optimizer failed, using fallback: {e}")

        # Fallback: Provide MQL5 optimization insights
        return self._fallback_optimization(code, question, focus, start_time)

    def _fallback_optimization(self, code: str, question: str, focus: str, start_time: float) -> Dict[str, Any]:
        """Provide fallback optimization for MQL5."""
        recommendations = []

        # Performance optimizations
        if focus in ["performance", "general", "latency"]:
            if "OnTick" in code and "iTime" not in code:
                recommendations.append({
                    "type": "critical",
                    "issue": "Heavy computation on every tick",
                    "fix": "Implement NewBarTrigger() pattern to run logic only on new bars"
                })

            if code.count("iMA(") > 2 or code.count("iRSI(") > 2:
                recommendations.append({
                    "type": "performance",
                    "issue": "Multiple indicator handle creations",
                    "fix": "Create all indicator handles in OnInit() and cache them"
                })

            if "CopyBuffer" in code and code.count("CopyBuffer") > 5:
                recommendations.append({
                    "type": "performance",
                    "issue": "Excessive CopyBuffer calls",
                    "fix": "Batch CopyBuffer calls and cache results"
                })

            if "string" in code.lower() and "OnTick" in code:
                recommendations.append({
                    "type": "performance",
                    "issue": "String operations in OnTick()",
                    "fix": "Minimize string operations in hot paths"
                })

        # Memory optimizations
        if focus in ["memory", "general"]:
            if "ArrayResize" in code:
                if code.count("ArrayResize") > code.count("ArrayFree"):
                    recommendations.append({
                        "type": "memory",
                        "issue": "Potential memory growth",
                        "fix": "Balance ArrayResize with ArrayFree or use fixed-size arrays"
                    })

        # Latency optimizations (HFT focus)
        if focus in ["latency", "hft"]:
            recommendations.append({
                "type": "latency",
                "issue": "HFT latency requirements",
                "fix": "Use tick-level processing, minimize API calls, cache everything"
            })

        if not recommendations:
            recommendations.append({
                "type": "info",
                "issue": "Basic analysis complete",
                "fix": "Code appears optimized. For deeper analysis, ensure blitzfire_code_agent is available."
            })

        return {
            "success": True,
            "source": "fallback_optimizer",
            "focus": focus,
            "result": {
                "recommendations": recommendations,
                "note": "Using built-in MQL5 optimization guidance"
            },
            "duration": time.time() - start_time,
            "fallback": True
        }


# ============================================================================
# UNIFIED EXTERNAL AGENT INTERFACE
# ============================================================================

class ExternalAgentInterface:
    """Unified interface for all external agents."""

    def __init__(self):
        self.debugger = MultiAgentDebuggerAdapter()
        self.build_resolver = BuildResolverAdapter()
        self.optimizer = BlitzfireOptimizerAdapter()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all external agents."""
        return {
            "multi_agent_debugging_system": {
                "available": self.debugger.available,
                "error": self.debugger.error
            },
            "never_fail_build_resolver": {
                "available": self.build_resolver.available,
                "error": self.build_resolver.error
            },
            "blitzfire_code_agent": {
                "available": self.optimizer.available,
                "error": self.optimizer.error
            },
            "all_available": all([
                self.debugger.available,
                self.build_resolver.available,
                self.optimizer.available
            ]),
            "fallback_available": True  # Fallbacks always available
        }

    async def consult_debugger(self, code: str, question: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Consult Multi-Agent Debugger."""
        return await self.debugger.analyze(code, question, analysis_type)

    async def consult_build_resolver(self, problem: str, error_context: str = "", tier: str = "smart") -> Dict[str, Any]:
        """Consult Build Resolver."""
        return await self.build_resolver.resolve(problem, error_context, tier)

    async def consult_optimizer(self, code: str, question: str, focus: str = "performance") -> Dict[str, Any]:
        """Consult Blitzfire Optimizer."""
        return await self.optimizer.optimize(code, question, focus)

    async def gather_all_opinions(self, code: str, topic: str, questions: List[str]) -> Dict[str, Any]:
        """Gather opinions from all available agents."""
        opinions = {
            "topic": topic,
            "agents_consulted": [],
            "opinions": {}
        }

        for question in questions[:3]:
            # Debugger
            debug_result = await self.debugger.analyze(code, f"{topic}: {question}")
            opinions["agents_consulted"].append("debugger" if not debug_result.get("fallback") else "debugger_fallback")
            opinions["opinions"]["debugger"] = debug_result

            # Optimizer
            opt_result = await self.optimizer.optimize(code, f"{topic}: {question}")
            opinions["agents_consulted"].append("optimizer" if not opt_result.get("fallback") else "optimizer_fallback")
            opinions["opinions"]["optimizer"] = opt_result

        return opinions


# Global interface instance
external_agents = ExternalAgentInterface()


# Convenience functions
async def consult_debugger(code: str, question: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
    """Consult Multi-Agent Debugger with fallback."""
    return await external_agents.consult_debugger(code, question, analysis_type)


async def consult_build_resolver(problem: str, error_context: str = "", tier: str = "smart") -> Dict[str, Any]:
    """Consult Build Resolver with fallback."""
    return await external_agents.consult_build_resolver(problem, error_context, tier)


async def consult_optimizer(code: str, question: str, focus: str = "performance") -> Dict[str, Any]:
    """Consult Blitzfire Optimizer with fallback."""
    return await external_agents.consult_optimizer(code, question, focus)


async def gather_opinions(code: str, topic: str, questions: List[str]) -> Dict[str, Any]:
    """Gather opinions from all agents with fallbacks."""
    return await external_agents.gather_all_opinions(code, topic, questions)


def get_agent_status() -> Dict[str, Any]:
    """Get status of all external agents."""
    return external_agents.get_status()


__all__ = [
    "ExternalAgentInterface",
    "external_agents",
    "consult_debugger",
    "consult_build_resolver",
    "consult_optimizer",
    "gather_opinions",
    "get_agent_status",
    "agent_registry"
]
