"""Main Never Fail Build Resolver Agent implementation using Pydantic AI."""

from pydantic_ai import Agent, RunContext
import asyncio
import time
from typing import Optional, List, Dict, Any

try:
    from .dependencies import BuildResolverDependencies, create_dependencies
    from .providers import get_llm_model
    from .settings import load_settings
    from .prompts import SYSTEM_PROMPT
    from .tools import (
        diagnose_build_problems,
        apply_resolution_strategy,
        validate_resolution,
        prevent_future_problems,
        analyze_build_configuration,
        emergency_nuclear_reset
    )
    from .models import (
        BuildAnalysis,
        ResolutionStrategy,
        ResolutionResult,
        ValidationResult,
        PreventionRule,
        BuildConfiguration,
        ResolutionTier,
        ResolutionStep,
        BuildErrorSeverity,
        BuildErrorCategory,
        ResolutionStatus
    )
except ImportError:
    # Fallback for direct execution from parent directory
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from core.dependencies import BuildResolverDependencies, create_dependencies
    from core.providers import get_llm_model
    from core.settings import load_settings
    from core.prompts import SYSTEM_PROMPT
    from core.tools import (
        diagnose_build_problems,
        apply_resolution_strategy,
        validate_resolution,
        prevent_future_problems,
        analyze_build_configuration,
        emergency_nuclear_reset
    )
    from core.models import (
        BuildAnalysis,
        ResolutionStrategy,
        ResolutionResult,
        ValidationResult,
        PreventionRule,
        BuildConfiguration,
        ResolutionTier,
        ResolutionStep,
        BuildErrorSeverity,
        BuildErrorCategory,
        ResolutionStatus
    )

# Load settings and create model
settings = load_settings()
model = get_llm_model(settings)

# Create the main agent
build_resolver_agent = Agent(
    model,
    deps_type=BuildResolverDependencies,
    system_prompt=SYSTEM_PROMPT
)

# ============================================================================
# Agent Tool Registration
# ============================================================================

@build_resolver_agent.tool
async def diagnose_build_failure(
    ctx: RunContext[BuildResolverDependencies],
    build_command: str,
    working_directory: str = None,
    timeout_seconds: int = 300
) -> BuildAnalysis:
    """Diagnose build failures and analyze root causes comprehensively."""
    return await diagnose_build_problems(ctx, build_command, working_directory, timeout_seconds)

@build_resolver_agent.tool
async def create_resolution_strategy(
    ctx: RunContext[BuildResolverDependencies],
    analysis: BuildAnalysis,
    tier: str = "intelligent",
    time_limit_seconds: int = 300
) -> ResolutionStrategy:
    """Create a detailed resolution strategy based on build analysis."""
    
    deps = ctx.deps
    logger = deps.logger
    
    # Convert tier string to enum
    tier_map = {
        "prevention": ResolutionTier.PREVENTION,
        "intelligent": ResolutionTier.INTELLIGENT, 
        "comprehensive": ResolutionTier.COMPREHENSIVE,
        "nuclear": ResolutionTier.NUCLEAR
    }
    
    resolution_tier = tier_map.get(tier.lower(), ResolutionTier.INTELLIGENT)
    
    # Get best strategy from learning database
    problem_pattern = f"{analysis.root_cause_analysis}:{len(analysis.build_problem.build_errors)}"
    best_strategy_id = deps.learning_database.get_best_strategy(problem_pattern)
    
    # Create strategy based on tier and problem analysis
    strategy_id = f"strategy_{resolution_tier.value}_{int(time.time())}"
    
    # Define resolution steps based on tier and problem categories
    steps = []
    step_id = 1
    
    error_categories = set(error.category for error in analysis.build_problem.build_errors)
    
    if resolution_tier == ResolutionTier.PREVENTION:
        steps = _create_prevention_steps(error_categories)
    elif resolution_tier == ResolutionTier.INTELLIGENT:
        steps = _create_intelligent_resolution_steps(error_categories, analysis)
    elif resolution_tier == ResolutionTier.COMPREHENSIVE:
        steps = _create_comprehensive_resolution_steps(error_categories, analysis)
    elif resolution_tier == ResolutionTier.NUCLEAR:
        steps = _create_nuclear_resolution_steps()
    
    # Assign step IDs
    for i, step in enumerate(steps, 1):
        step.step_id = i
    
    # Calculate estimated time
    total_time = sum(step.estimated_duration_seconds for step in steps)
    
    # Assess confidence based on historical success rate
    confidence_score = 0.8  # Default confidence
    if best_strategy_id:
        confidence_score = 0.9  # Higher confidence if we have historical data
    
    strategy = ResolutionStrategy(
        strategy_id=strategy_id,
        strategy_name=f"{resolution_tier.value.title()} Build Resolution",
        tier=resolution_tier,
        confidence_score=confidence_score,
        estimated_success_rate=0.85,  # Will be updated from historical data
        description=f"Systematic {resolution_tier.value} resolution for build failures",
        target_problems=list(error_categories),
        resolution_steps=steps,
        estimated_total_time_seconds=min(total_time, time_limit_seconds),
        risk_assessment=_assess_strategy_risk(resolution_tier),
        backup_required=resolution_tier in [ResolutionTier.COMPREHENSIVE, ResolutionTier.NUCLEAR],
        success_criteria=[
            "Build command executes successfully",
            "All tests pass",
            "No regression in functionality"
        ]
    )
    
    logger.info(f"Created {resolution_tier.value} resolution strategy with {len(steps)} steps")
    
    return strategy

@build_resolver_agent.tool
async def execute_resolution(
    ctx: RunContext[BuildResolverDependencies],
    strategy: ResolutionStrategy,
    enable_backup: bool = True
) -> ResolutionResult:
    """Execute a resolution strategy and return detailed results."""
    return await apply_resolution_strategy(ctx, strategy, enable_backup)

@build_resolver_agent.tool
async def validate_build_fix(
    ctx: RunContext[BuildResolverDependencies],
    original_build_command: str,
    working_directory: str = None
) -> ValidationResult:
    """Validate that build problems have been resolved."""
    return await validate_resolution(ctx, original_build_command, working_directory)

@build_resolver_agent.tool
async def create_prevention_rules(
    ctx: RunContext[BuildResolverDependencies],
    analysis: BuildAnalysis,
    successful_strategy_id: str
) -> List[PreventionRule]:
    """Create prevention rules to avoid future build failures."""
    return await prevent_future_problems(ctx, analysis, successful_strategy_id)

@build_resolver_agent.tool
async def analyze_project_configuration(
    ctx: RunContext[BuildResolverDependencies],
    project_directory: str = None
) -> BuildConfiguration:
    """Analyze current build system configuration for potential issues."""
    return await analyze_build_configuration(ctx, project_directory)

@build_resolver_agent.tool
async def emergency_reset(
    ctx: RunContext[BuildResolverDependencies],
    confirmed: bool = False
) -> ResolutionResult:
    """Emergency nuclear option: Complete build system reset (USE WITH EXTREME CAUTION)."""
    if not confirmed:
        raise ValueError("Emergency reset requires confirmed=True parameter to proceed")
    
    return await emergency_nuclear_reset(ctx, confirmation_required=False)

# ============================================================================
# Resolution Step Generators
# ============================================================================

def _create_prevention_steps(error_categories: set) -> List[ResolutionStep]:
    """Create prevention-focused resolution steps."""
    steps = []
    
    if BuildErrorCategory.DEPENDENCY in error_categories:
        steps.append(ResolutionStep(
            step_id=0,
            description="Check dependency versions and compatibility",
            command="./scripts/check_dependencies.sh",
            expected_outcome="All dependencies are compatible and available",
            validation_method="Verify no dependency conflicts reported",
            estimated_duration_seconds=30,
            risk_level="low"
        ))
    
    if BuildErrorCategory.CONFIGURATION in error_categories:
        steps.append(ResolutionStep(
            step_id=0,
            description="Validate build configuration",
            command="./scripts/validate_build_config.sh",
            expected_outcome="Build configuration is valid",
            validation_method="Check configuration validation output",
            estimated_duration_seconds=20,
            risk_level="low"
        ))
    
    return steps

def _create_intelligent_resolution_steps(error_categories: set, analysis: BuildAnalysis) -> List[ResolutionStep]:
    """Create intelligent resolution steps based on error analysis."""
    steps = []
    
    # Always start with build safety check
    steps.append(ResolutionStep(
        step_id=0,
        description="Run build safety check",
        command="./scripts/build_safety_check.sh",
        expected_outcome="Build environment is safe and ready",
        validation_method="Check safety check output for issues",
        estimated_duration_seconds=45,
        risk_level="low"
    ))
    
    if BuildErrorCategory.DEPENDENCY in error_categories:
        steps.append(ResolutionStep(
            step_id=0,
            description="Resolve dependency conflicts",
            command="./scripts/fix_build.sh smart",
            expected_outcome="Dependency conflicts resolved",
            validation_method="Run dependency check",
            rollback_command="git checkout -- .",
            estimated_duration_seconds=120,
            risk_level="medium"
        ))
    
    if BuildErrorCategory.CONFIGURATION in error_categories:
        steps.append(ResolutionStep(
            step_id=0,
            description="Reconfigure build system",
            command="cmake --fresh -S . -B cmake-build-debug -DCMAKE_BUILD_TYPE=Debug",
            expected_outcome="CMake configuration successful",
            validation_method="Check for CMakeCache.txt creation",
            rollback_command="rm -rf cmake-build-debug",
            estimated_duration_seconds=60,
            risk_level="medium"
        ))
    
    if BuildErrorCategory.COMPILATION in error_categories:
        steps.append(ResolutionStep(
            step_id=0,
            description="Fix compilation errors with AI assistance",
            command="./scripts/ai_clang_tidy.sh project",
            expected_outcome="Compilation errors resolved",
            validation_method="Attempt compilation of affected files",
            estimated_duration_seconds=180,
            risk_level="medium"
        ))
    
    # Final build attempt
    steps.append(ResolutionStep(
        step_id=0,
        description="Attempt full build",
        command=analysis.build_problem.build_command,
        expected_outcome="Build succeeds without errors",
        validation_method="Check build exit code and output",
        estimated_duration_seconds=300,
        risk_level="low"
    ))
    
    return steps

def _create_comprehensive_resolution_steps(error_categories: set, analysis: BuildAnalysis) -> List[ResolutionStep]:
    """Create comprehensive resolution steps for complex problems."""
    steps = []
    
    # Comprehensive backup
    steps.append(ResolutionStep(
        step_id=0,
        description="Create comprehensive backup",
        command="./scripts/create_build_backup.sh",
        expected_outcome="Complete project backup created",
        validation_method="Verify backup directory exists",
        estimated_duration_seconds=60,
        risk_level="low"
    ))
    
    # Clean slate approach
    steps.append(ResolutionStep(
        step_id=0,
        description="Clean all build artifacts",
        command="rm -rf cmake-build-* build/ CMakeCache.txt CMakeFiles/",
        expected_outcome="All build artifacts removed",
        validation_method="Check build directories are gone",
        rollback_command="./scripts/restore_build_backup.sh",
        estimated_duration_seconds=30,
        risk_level="medium"
    ))
    
    # Comprehensive dependency resolution
    steps.append(ResolutionStep(
        step_id=0,
        description="Comprehensive dependency resolution",
        command="./scripts/fix_build.sh thorough",
        expected_outcome="All dependencies resolved and verified",
        validation_method="Run full dependency validation",
        estimated_duration_seconds=300,
        risk_level="medium"
    ))
    
    # Full reconfiguration
    steps.append(ResolutionStep(
        step_id=0,
        description="Full CMake reconfiguration with all options",
        command="cmake -S . -B cmake-build-debug -DCMAKE_BUILD_TYPE=Debug -DENABLE_POWER_MODE=ON -DENABLE_SANITIZERS=ON",
        expected_outcome="Complete CMake configuration success",
        validation_method="Verify all required targets configured",
        estimated_duration_seconds=120,
        risk_level="medium"
    ))
    
    # Incremental build with validation
    steps.append(ResolutionStep(
        step_id=0,
        description="Incremental build with comprehensive validation",
        command="cmake --build cmake-build-debug --target all -j4",
        expected_outcome="Full project builds successfully",
        validation_method="Run test suite to verify functionality",
        estimated_duration_seconds=600,
        risk_level="medium"
    ))
    
    return steps

def _create_nuclear_resolution_steps() -> List[ResolutionStep]:
    """Create nuclear option resolution steps (last resort)."""
    steps = []
    
    steps.append(ResolutionStep(
        step_id=0,
        description="NUCLEAR: Complete environment reset",
        command="./scripts/nuclear_build_reset.sh",
        expected_outcome="Complete build environment reconstructed",
        validation_method="Verify all tools and dependencies reinstalled",
        estimated_duration_seconds=1800,
        risk_level="high"
    ))
    
    return steps

def _assess_strategy_risk(tier: ResolutionTier) -> str:
    """Assess risk level for resolution strategy."""
    risk_map = {
        ResolutionTier.PREVENTION: "Very Low - Only checks and validates",
        ResolutionTier.INTELLIGENT: "Low - Targeted fixes with rollback options",
        ResolutionTier.COMPREHENSIVE: "Medium - Extensive changes but reversible",
        ResolutionTier.NUCLEAR: "High - Complete environment reset"
    }
    
    return risk_map.get(tier, "Unknown")

# ============================================================================
# Convenience Interface Classes
# ============================================================================

class BuildResolverAI:
    """Main interface for the Never Fail Build Resolver AI Agent."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self._dependencies = None
    
    def __enter__(self):
        self._dependencies = create_dependencies(self.session_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._dependencies:
            self._dependencies.db_connection.close()
    
    async def __aenter__(self):
        self._dependencies = create_dependencies(self.session_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._dependencies:
            self._dependencies.db_connection.close()
    
    async def diagnose_and_fix_build(
        self,
        build_command: str,
        working_directory: str = None,
        resolution_tier: str = "intelligent",
        enable_validation: bool = True
    ) -> Dict[str, Any]:
        """Complete build diagnosis and resolution workflow."""
        if not self._dependencies:
            raise RuntimeError("BuildResolverAI must be used as a context manager")
        
        results = {
            "success": False,
            "analysis": None,
            "strategy": None,
            "resolution": None,
            "validation": None,
            "prevention_rules": [],
            "total_time_seconds": 0
        }
        
        start_time = time.time()
        
        try:
            self._dependencies.logger.info("Starting complete build resolution workflow")
            
            # Step 1: Diagnose build problems
            self._dependencies.logger.info("Step 1: Diagnosing build problems")
            analysis = await build_resolver_agent.run(
                f"Please diagnose the build failure for command: '{build_command}'",
                deps=self._dependencies
            )
            results["analysis"] = analysis.data if hasattr(analysis, 'data') else str(analysis)
            
            # Step 2: Create resolution strategy
            self._dependencies.logger.info(f"Step 2: Creating {resolution_tier} resolution strategy")
            strategy_prompt = f"Based on the build analysis, create a {resolution_tier} resolution strategy with a 5-minute time limit."
            strategy_result = await build_resolver_agent.run(strategy_prompt, deps=self._dependencies)
            results["strategy"] = strategy_result.data if hasattr(strategy_result, 'data') else str(strategy_result)
            
            # Step 3: Execute resolution
            self._dependencies.logger.info("Step 3: Executing resolution strategy")
            resolution_prompt = "Execute the resolution strategy we just created, with backup enabled."
            resolution_result = await build_resolver_agent.run(resolution_prompt, deps=self._dependencies)
            results["resolution"] = resolution_result.data if hasattr(resolution_result, 'data') else str(resolution_result)
            
            # Step 4: Validate resolution (if enabled)
            if enable_validation:
                self._dependencies.logger.info("Step 4: Validating resolution")
                validation_prompt = f"Validate that the build fix worked by testing the original command: '{build_command}'"
                validation_result = await build_resolver_agent.run(validation_prompt, deps=self._dependencies)
                results["validation"] = validation_result.data if hasattr(validation_result, 'data') else str(validation_result)
            
            # Step 5: Create prevention rules
            self._dependencies.logger.info("Step 5: Creating prevention rules")
            prevention_prompt = "Create prevention rules based on the successful resolution to prevent future similar failures."
            prevention_result = await build_resolver_agent.run(prevention_prompt, deps=self._dependencies)
            results["prevention_rules"] = prevention_result.data if hasattr(prevention_result, 'data') else str(prevention_result)
            
            results["success"] = True
            self._dependencies.logger.info("Complete build resolution workflow completed successfully")
            
        except Exception as e:
            self._dependencies.logger.error(f"Build resolution workflow failed: {e}")
            results["error"] = str(e)
        
        finally:
            results["total_time_seconds"] = time.time() - start_time
        
        return results
    
    async def emergency_build_resolution(self, build_command: str) -> Dict[str, Any]:
        """Emergency build resolution using all available tiers."""
        if not self._dependencies:
            raise RuntimeError("BuildResolverAI must be used as a context manager")
        
        self._dependencies.logger.warning("Starting emergency build resolution")
        
        # Try each tier in sequence until success
        tiers = ["intelligent", "comprehensive", "nuclear"]
        
        for tier in tiers:
            self._dependencies.logger.info(f"Attempting emergency resolution with {tier} tier")
            
            try:
                result = await self.diagnose_and_fix_build(
                    build_command=build_command,
                    resolution_tier=tier,
                    enable_validation=True
                )
                
                if result["success"]:
                    self._dependencies.logger.info(f"Emergency resolution succeeded with {tier} tier")
                    return result
                
            except Exception as e:
                self._dependencies.logger.error(f"Emergency {tier} resolution failed: {e}")
                if tier == "nuclear":
                    raise  # Nuclear option failed, give up
                continue
        
        raise RuntimeError("All emergency resolution tiers failed")
    
    async def analyze_project_health(self, project_directory: str = None) -> Dict[str, Any]:
        """Analyze overall project build health and configuration."""
        if not self._dependencies:
            raise RuntimeError("BuildResolverAI must be used as a context manager")
        
        query = f"Please analyze the build configuration and project health"
        if project_directory:
            query += f" for project in directory: {project_directory}"
        
        result = await build_resolver_agent.run(query, deps=self._dependencies)
        return {"analysis": result.data if hasattr(result, 'data') else str(result)}
    
    async def chat_about_build_issues(self, message: str) -> str:
        """Have a conversational interaction about build issues."""
        if not self._dependencies:
            raise RuntimeError("BuildResolverAI must be used as a context manager")
        
        result = await build_resolver_agent.run(message, deps=self._dependencies)
        return result.data if hasattr(result, 'data') else str(result)

# ============================================================================
# Standalone Interface Functions
# ============================================================================

async def interactive_build_diagnosis(
    build_command: str,
    working_directory: str = None,
    session_id: str = None
) -> str:
    """Interactive build diagnosis with conversational interface."""
    dependencies = create_dependencies(session_id)
    
    try:
        result = await build_resolver_agent.run(
            f"Please perform a comprehensive diagnosis of this build failure: '{build_command}'. Provide detailed analysis with root cause identification and recommended resolution approach.",
            deps=dependencies
        )
        return result.data if hasattr(result, 'data') else str(result)
    finally:
        dependencies.db_connection.close()

async def emergency_build_resolution(
    build_command: str,
    working_directory: str = None,
    session_id: str = None
) -> str:
    """Emergency build resolution with automatic tier escalation."""
    dependencies = create_dependencies(session_id)
    
    try:
        result = await build_resolver_agent.run(
            f"EMERGENCY: This is a critical build failure that needs immediate resolution: '{build_command}'. Use whatever tier necessary to fix this, including nuclear options if required. Provide step-by-step resolution with clear progress updates.",
            deps=dependencies
        )
        return result.data if hasattr(result, 'data') else str(result)
    finally:
        dependencies.db_connection.close()

async def prevent_build_failures(
    project_directory: str = None,
    session_id: str = None
) -> str:
    """Proactive build failure prevention analysis."""
    dependencies = create_dependencies(session_id)
    
    try:
        query = "Please analyze the current build system configuration and create proactive prevention measures to avoid build failures."
        if project_directory:
            query += f" Focus on the project in directory: {project_directory}"
        
        result = await build_resolver_agent.run(query, deps=dependencies)
        return result.data if hasattr(result, 'data') else str(result)
    finally:
        dependencies.db_connection.close()

async def comprehensive_project_analysis(
    project_directory: str = None,
    session_id: str = None
) -> str:
    """Comprehensive project-wide build system analysis."""
    dependencies = create_dependencies(session_id)
    
    try:
        query = "Please perform a comprehensive analysis of the entire project build system, including configuration, dependencies, potential issues, and optimization recommendations."
        if project_directory:
            query += f" Analyze the project in directory: {project_directory}"
        
        result = await build_resolver_agent.run(query, deps=dependencies)
        return result.data if hasattr(result, 'data') else str(result)
    finally:
        dependencies.db_connection.close()

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def example_usage():
        """Example of how to use the Never Fail Build Resolver AI Agent."""
        
        print("=== Build Diagnosis Example ===")
        result = await interactive_build_diagnosis(
            "cmake --build cmake-build-debug --target wire_ground_tests"
        )
        print(result)
        
        print("\n=== Emergency Resolution Example ===")
        emergency_result = await emergency_build_resolution(
            "cmake --build cmake-build-debug --target all"
        )
        print(emergency_result)
        
        print("\n=== Prevention Analysis Example ===")
        prevention_result = await prevent_build_failures()
        print(prevention_result)
        
        print("\n=== Complete Workflow Example ===")
        async with BuildResolverAI(session_id="example") as resolver:
            complete_result = await resolver.diagnose_and_fix_build(
                build_command="cmake --build cmake-build-debug --target all",
                resolution_tier="intelligent",
                enable_validation=True
            )
            print(f"Complete workflow result: {complete_result}")
            
            chat_result = await resolver.chat_about_build_issues(
                "What are the most common build failures in C++ projects and how can I prevent them?"
            )
            print(f"Chat result: {chat_result}")
    
    # Uncomment to run example
    # asyncio.run(example_usage())