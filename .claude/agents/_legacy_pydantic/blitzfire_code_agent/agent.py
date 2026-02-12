"""Main Blitzfire Code Agent implementation with factory pattern and validation."""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic import BaseModel, Field

from .models import (
    BlitzfireResponse, AnalysisResult, OptimizationStrategy,
    AssemblyComparison, BenchmarkResult, Architecture, OptimizationMode,
    ConversationContext, HFTAuditResult
)
from .dependencies import BlitzfireDependencies, CodeAnalyzer, HFTAnalyzer
from .providers import get_llm_model
from .prompts import get_system_prompt, format_personality_message
from .tools import (
    analyze_code, generate_optimizations, validate_assembly,
    benchmark_performance, hft_audit, interactive_chat, mock_reasoning_response
)
try:
    from .agent_factory import (
        BlitzfireAgentFactory, BlitzfireAgentConfig, BlitzfireAgentType,
        BlitzfireValidationLevel, get_blitzfire_factory, create_and_validate_blitzfire_agents
    )
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False
    BlitzfireValidationLevel = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlitzfireAnalysisRequest(BaseModel):
    """Request model for Blitzfire optimization analysis."""
    code_content: str = Field(..., description="C++ source code to analyze")
    architecture: str = Field(default="x86_64", description="Target architecture")
    optimization_mode: str = Field(default="general", description="Optimization domain")
    include_benchmarks: bool = Field(default=True, description="Whether to run benchmarks")
    include_assembly: bool = Field(default=True, description="Whether to validate with assembly")
    validation_level: Optional[str] = Field(
        default="production",
        description="Validation strictness level"
    )


class BlitzfireCodeAgent:
    """
    Blitzfire Code Agent - AI-powered C++ optimization expert with factory pattern and validation.

    A sophisticated agent that combines static code analysis, multi-tier optimization
    strategies, assembly validation, and empirical benchmarking with comprehensive
    validation and monitoring capabilities.
    """

    def __init__(self, model: Optional[Model] = None, session_id: str = "default", use_factory: bool = True):
        """Initialize the Blitzfire agent."""
        self.model = model or get_llm_model()
        self.session_id = session_id
        self.use_factory = use_factory and FACTORY_AVAILABLE

        if self.use_factory:
            # Use factory pattern with validation
            self.factory = get_blitzfire_factory()
            self._initialize_with_factory()
        else:
            # Legacy initialization for backward compatibility
            self._initialize_legacy()

    def _initialize_with_factory(self):
        """Initialize using the factory pattern."""
        try:
            # Create standard Blitzfire agents
            self.factory_agents = self.factory.create_standard_blitzfire_agents()

            # Use the optimizer as the primary agent
            self.validated_agent = self.factory_agents["optimizer"]
            self.agent = self.validated_agent.agent

            logger.info(f"Blitzfire agent initialized with factory (session: {self.session_id})")
        except Exception as e:
            logger.warning(f"Factory initialization failed, falling back to legacy: {e}")
            self.use_factory = False
            self._initialize_legacy()

    def _initialize_legacy(self):
        """Legacy initialization for backward compatibility."""
        # Create the Pydantic AI agent with proper system prompt
        self.agent = Agent(
            self.model,
            deps_type=BlitzfireDependencies,
            system_prompt=get_system_prompt()
        )

        # Register tools with the agent
        self._register_tools()

        logger.info(f"Blitzfire agent initialized in legacy mode (session: {self.session_id})")

    def _register_tools(self):
        """Register all tools with the Pydantic AI agent."""

        @self.agent.tool
        async def analyze_cpp_code(
            ctx: RunContext[BlitzfireDependencies],
            code_content: str,
            architecture: str = "x86_64",
            optimization_mode: str = "general",
            focus_areas: List[str] = None
        ) -> AnalysisResult:
            """Analyze C++ code for performance optimization opportunities."""
            return analyze_code(code_content, architecture, optimization_mode, focus_areas)

        @self.agent.tool
        async def create_optimization_strategy(
            ctx: RunContext[BlitzfireDependencies],
            analysis_results: Dict[str, Any],
            performance_target: float = 2.0,
            safety_level: str = "high",
            include_advanced: bool = True
        ) -> OptimizationStrategy:
            """Generate multi-tier optimization strategies."""
            # Convert dict back to AnalysisResult for processing
            # This is a simplified conversion - production would use proper serialization
            analysis = AnalysisResult(**analysis_results)
            return generate_optimizations(analysis, performance_target, safety_level, include_advanced)

        @self.agent.tool
        async def validate_with_assembly(
            ctx: RunContext[BlitzfireDependencies],
            original_code: str,
            optimized_code: str,
            compiler: str = "clang_trunk",
            optimization_level: str = "-O3"
        ) -> Optional[AssemblyComparison]:
            """Compare assembly output between original and optimized code."""
            if not ctx.deps.godbolt_session:
                return None
            return validate_assembly(original_code, optimized_code, compiler, optimization_level)

        @self.agent.tool
        async def run_performance_benchmarks(
            ctx: RunContext[BlitzfireDependencies],
            test_functions: List[str],
            test_sizes: List[int] = None,
            iterations: int = 1000
        ) -> List[BenchmarkResult]:
            """Execute empirical performance benchmarking."""
            if not ctx.deps.is_docker_available():
                return []  # Graceful fallback
            return benchmark_performance(test_functions, test_sizes, iterations)

        @self.agent.tool
        async def perform_hft_audit(
            ctx: RunContext[BlitzfireDependencies],
            code_content: str,
            audit_level: str = "comprehensive"
        ) -> Dict[str, Any]:
            """Perform HFT-specific code quality audit."""
            return hft_audit(code_content, audit_level)

        @self.agent.tool
        async def chat_about_optimization(
            ctx: RunContext[BlitzfireDependencies],
            user_message: str,
            educational_mode: bool = True
        ) -> str:
            """Handle conversational optimization guidance."""
            # Use previous analysis from context if available
            context = {"session_id": ctx.deps.session_id}
            return interactive_chat(user_message, context, educational_mode)

    async def analyze_and_optimize(
        self,
        code_content: str = None,
        architecture: str = "x86_64",
        optimization_mode: str = "general",
        include_benchmarks: bool = True,
        include_assembly: bool = True,
        request: Optional[BlitzfireAnalysisRequest] = None
    ) -> BlitzfireResponse:
        """
        Complete analysis and optimization of C++ code with optional validation.

        Args:
            code_content: C++ source code to analyze (legacy parameter)
            architecture: Target architecture (legacy parameter)
            optimization_mode: Optimization domain (legacy parameter)
            include_benchmarks: Whether to run benchmarks (legacy parameter)
            include_assembly: Whether to validate with assembly (legacy parameter)
            request: Validated analysis request (preferred parameter)

        Returns:
            Complete BlitzfireResponse with analysis, strategy, validation results
        """
        start_time = time.time()

        # Handle both legacy and new request formats
        if request is None:
            request = BlitzfireAnalysisRequest(
                code_content=code_content,
                architecture=architecture,
                optimization_mode=optimization_mode,
                include_benchmarks=include_benchmarks,
                include_assembly=include_assembly
            )

        if self.use_factory:
            return await self._analyze_with_validation(request, start_time)
        else:
            return await self._analyze_legacy(request, start_time)

    async def _analyze_with_validation(
        self,
        request: BlitzfireAnalysisRequest,
        start_time: float
    ) -> BlitzfireResponse:
        """Analyze with factory pattern and comprehensive validation."""
        try:
            # Create dependencies
            deps = self._create_dependencies()

            # Execute with validation
            execution_record = await self.validated_agent.run_with_validation(
                prompt=self._create_optimization_prompt(request),
                deps=deps,
                input_schema=BlitzfireAnalysisRequest
            )

            if not execution_record["success"]:
                return self._create_error_response(
                    f"Analysis failed: {execution_record.get('error', 'Unknown error')}",
                    start_time, request
                )

            # Process the result
            result_data = execution_record.get("result", "{}")
            validation_results = execution_record.get("validation_results", {})

            # Run the actual analysis using existing tools
            return await self._run_blitzfire_analysis(request, start_time, validation_results)

        except Exception as e:
            logger.error(f"Blitzfire analysis failed: {str(e)}")
            return self._create_error_response(str(e), start_time, request)

    async def _analyze_legacy(
        self,
        request: BlitzfireAnalysisRequest,
        start_time: float
    ) -> BlitzfireResponse:
        """Legacy analysis method for backward compatibility."""
        return await self._run_blitzfire_analysis(request, start_time, {})

    async def _run_blitzfire_analysis(
        self,
        request: BlitzfireAnalysisRequest,
        start_time: float,
        validation_results: Dict[str, Any]
    ) -> BlitzfireResponse:
        """Run the actual Blitzfire analysis pipeline."""
        # Create dependencies
        deps = self._create_dependencies()

        # Step 1: Analyze the code
        analysis = analyze_code(
            code_content=request.code_content,
            architecture=request.architecture,
            optimization_mode=request.optimization_mode
        )

        # Step 2: Generate optimization strategy
        strategy = generate_optimizations(
            analysis_results=analysis,
            performance_target=2.0,
            safety_level="high",
            include_advanced=True
        )

        # Step 3: Assembly validation (if requested)
        assembly_comparison = None
        if request.include_assembly and len(strategy.tiers) > 0:
            # Use first tier's optimized code for comparison
            first_tier = strategy.tiers[0]
            assembly_comparison = validate_assembly(
                original_code=first_tier.code_before,
                optimized_code=first_tier.code_after
            )

        # Step 4: Benchmarking (if requested and available)
        benchmark_results = []
        if request.include_benchmarks and deps.is_docker_available():
            # Extract function names from optimization tiers
            test_functions = [f"benchmark_tier_{i+1}" for i in range(len(strategy.tiers))]
            benchmark_results = benchmark_performance(test_functions)

        # Step 5: Generate personality message and educational content
        personality_message = format_personality_message(
            "optimization_found",
            count=len(analysis.issues),
            speedup=strategy.total_estimated_speedup
        )

        educational_insights = [
            f"Your code has {analysis.complexity.time_complexity} complexity - understanding Big-O helps predict performance with larger inputs!",
            f"Found {len(analysis.complexity.hotspots)} performance hotspots - these are the lines that matter most for optimization.",
            "Cache-friendly code can be 10-100x faster than cache-unfriendly patterns!"
        ]

        if assembly_comparison and assembly_comparison.vectorization_detected:
            educational_insights.append("The compiler detected vectorization opportunities - SIMD can give 4-8x speedups!")

        # Calculate Blitzfire score (1-10 based on optimization potential)
        base_score = min(10, max(1, int(strategy.total_estimated_speedup)))
        if benchmark_results:
            # Boost score if benchmarks exceed estimates
            avg_measured_speedup = sum(r.speedup_ratio or 1.0 for r in benchmark_results if r.speedup_ratio) / len(benchmark_results)
            if avg_measured_speedup > strategy.total_estimated_speedup:
                base_score = min(10, base_score + 1)

        blitzfire_score = base_score

        processing_time = time.time() - start_time

        recommended_next_steps = [
            "Start with Tier 1 optimizations - they're safe and give quick wins!",
            "Profile your code with tools like perf or VTune to validate hotspots",
            "Implement optimizations incrementally and test each step"
        ]

        additional_resources = [
            "Compiler Explorer (godbolt.org) - visualize your optimizations",
            "Intel Optimization Manual - deep dive into CPU performance",
            "Agner Fog's optimization guides - comprehensive C++ performance resources"
        ]

        # Enhanced response with validation metadata
        response_metadata = {
            "session_id": self.session_id,
            "architecture": request.architecture,
            "optimization_mode": request.optimization_mode,
            "factory_mode": self.use_factory,
            "execution_time": time.time() - start_time
        }

        if validation_results:
            response_metadata["validation_results"] = validation_results

        return BlitzfireResponse(
            analysis=analysis,
            strategy=strategy,
            assembly_comparison=assembly_comparison,
            benchmark_results=benchmark_results,
            personality_message=personality_message,
            educational_insights=educational_insights,
            recommended_next_steps=recommended_next_steps,
            additional_resources=additional_resources,
            blitzfire_score=blitzfire_score,
            processing_time_seconds=processing_time,
            metadata=response_metadata
        )

    def _create_dependencies(self) -> BlitzfireDependencies:
        """Create BlitzfireDependencies for analysis."""
        from .settings import settings
        return BlitzfireDependencies.create(settings, self.session_id)

    def _create_optimization_prompt(self, request: BlitzfireAnalysisRequest) -> str:
        """Create optimization prompt for agent execution."""
        return f"""
        Analyze this C++ code for optimization opportunities:

        Code:
        ```cpp
        {request.code_content}
        ```

        Target Architecture: {request.architecture}
        Optimization Mode: {request.optimization_mode}

        Provide comprehensive static analysis focusing on:
        1. Performance bottlenecks
        2. Memory usage patterns
        3. Algorithmic complexity
        4. Architecture-specific optimizations
        """

    def _create_error_response(
        self,
        error_message: str,
        start_time: float,
        request: BlitzfireAnalysisRequest
    ) -> BlitzfireResponse:
        """Create error response with validation metadata."""
        return BlitzfireResponse(
            analysis={},
            strategy={},
            assembly_comparison=None,
            benchmark_results=[],
            personality_message="Sorry, I encountered an error during analysis.",
            educational_insights=[],
            recommended_next_steps=["Please check your code and try again"],
            additional_resources=[],
            blitzfire_score=0,
            processing_time_seconds=time.time() - start_time,
            metadata={
                "session_id": self.session_id,
                "error": error_message,
                "success": False,
                "architecture": request.architecture,
                "optimization_mode": request.optimization_mode,
                "factory_mode": self.use_factory
            }
        )

    async def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status and statistics."""
        if not self.use_factory:
            return {"factory_mode": False, "validation": "legacy"}

        try:
            # Get factory statistics
            stats = self.factory.get_statistics()

            # Get agent health check
            health_results = await self.factory.validate_all_agents()

            return {
                "factory_mode": True,
                "validation_enabled": True,
                "factory_statistics": stats,
                "agent_health": {
                    name: {
                        "valid": result.is_valid,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                    for name, result in health_results.items()
                },
                "session_id": self.session_id
            }
        except Exception as e:
            return {
                "factory_mode": True,
                "validation_error": str(e),
                "session_id": self.session_id
            }

    async def chat(self, message: str, context: Optional[ConversationContext] = None) -> str:
        """
        Interactive chat interface for optimization guidance.

        Args:
            message: User message or question
            context: Conversation context with history

        Returns:
            Agent response with optimization guidance
        """
        # Create dependencies
        from .settings import settings
        deps = BlitzfireDependencies.create(settings, self.session_id)

        try:
            # Use the agent's chat functionality
            result = await self.agent.run(message, deps=deps)
            return result.data
        except Exception as e:
            # Fallback to static response system
            return interactive_chat(message, {}, educational_mode=True)

    async def analyze_for_hft(self, code_content: str) -> Dict[str, Any]:
        """
        Specialized analysis for high-frequency trading code.

        Args:
            code_content: C++ source code to audit

        Returns:
            HFT-specific audit results with safety recommendations
        """
        # Perform standard analysis first
        standard_analysis = analyze_code(
            code_content=code_content,
            optimization_mode="hft"
        )

        # Add HFT-specific auditing
        hft_results = hft_audit(code_content)

        return {
            "standard_analysis": standard_analysis,
            "hft_audit": hft_results,
            "combined_recommendations": self._generate_hft_recommendations(standard_analysis, hft_results)
        }

    def _generate_hft_recommendations(
        self,
        analysis: AnalysisResult,
        hft_audit_results: Dict[str, Any]
    ) -> List[str]:
        """Generate HFT-specific recommendations."""
        recommendations = []

        if hft_audit_results["total_issues"] > 0:
            recommendations.append("🏦 Critical: Address safety issues before optimizing for performance")

        if len(hft_audit_results["overflow_risks"]) > 0:
            recommendations.append("Use SafeInt library or bounds checking for financial calculations")

        if len(hft_audit_results["race_conditions"]) > 0:
            recommendations.append("Implement lock-free data structures with proper memory ordering")

        if analysis.complexity.time_complexity in ["O(n²)", "O(n³)"]:
            recommendations.append("Consider deterministic algorithms with bounded execution time")

        recommendations.extend([
            "Add comprehensive logging for audit trail compliance",
            "Use deterministic floating-point arithmetic",
            "Implement circuit breakers for error handling",
            "Consider formal verification for critical algorithms"
        ])

        return recommendations


# Convenience function for quick analysis
async def quick_analyze(code_content: str, mode: str = "general") -> BlitzfireResponse:
    """Quick analysis function for testing and simple usage."""
    agent = BlitzfireCodeAgent()
    return await agent.analyze_and_optimize(
        code_content=code_content,
        optimization_mode=mode,
        include_benchmarks=False,  # Skip for quick analysis
        include_assembly=False
    )