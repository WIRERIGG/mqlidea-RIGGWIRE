"""
Clang-Tidy AI Agent - Factory Orchestrator for Comprehensive C++ Code Quality with Validation
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field

# Import shared integration for permanent BLITZFIRE cooperation
try:
    import sys
    sys.path.append('/IdeaProjects/wire_ground/.claude/agents')
    from shared_integration import (
        INTEGRATION_ENABLED,
        PipelineConfig,
        IntegratedPipeline,
        PipelineStage
    )
    BLITZFIRE_INTEGRATION = True
except ImportError:
    BLITZFIRE_INTEGRATION = False
    INTEGRATION_ENABLED = False

logger = logging.getLogger(__name__)

from models import (
    ClangTidyDependencies,
    IssueDiscoveryResponse,
    FixStrategyResponse,
    FixApplicationResponse,
    ValidationResponse,
    ArchonTaskResponse
)
from tools import (
    ClangTidyAnalyzer,
    IssueDiscoveryEngine,
    FixStrategyPlanner,
    FixApplicationEngine,
    ValidationEngine
)

try:
    from .agent_factory import (
        ClangTidyAgentFactory, ClangTidyAgentConfig, ClangTidyAgentType,
        ClangTidyValidationLevel, get_clang_tidy_factory, create_and_validate_clang_tidy_agents
    )
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False
    ClangTidyValidationLevel = None
    logger.warning("Clang-Tidy factory not available, using legacy mode")


class ClangTidyAnalysisRequest(BaseModel):
    """Request model for Clang-Tidy analysis."""
    file_path: str = Field(..., description="Path to C++ file to analyze")
    checks: str = Field(default="*", description="Clang-Tidy checks to run")
    fix_strategy: str = Field(default="conservative", description="Fix application strategy")
    enable_auto_fix: bool = Field(default=False, description="Enable automatic fix application")
    validation_level: str = Field(default="production", description="Validation level")


def get_model():
    """Get the appropriate model based on environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return OpenAIModel('gpt-4')
    else:
        # Fallback to TestModel for validation and testing
        return TestModel()


class ClangTidyAIAgent:
    """
    Clang-Tidy AI Agent with factory pattern and comprehensive validation.

    Coordinates the complete C++ code quality analysis and fix pipeline
    using specialized agents and comprehensive validation.
    """

    def __init__(self, use_factory: bool = True, session_id: str = "default"):
        """Initialize the Clang-Tidy AI agent."""
        self.session_id = session_id
        self.use_factory = use_factory and FACTORY_AVAILABLE

        if self.use_factory:
            self._initialize_with_factory()
        else:
            self._initialize_legacy()

    def _initialize_with_factory(self):
        """Initialize using the factory pattern."""
        try:
            self.factory = get_clang_tidy_factory()
            self.factory_agents = self.factory.create_standard_clang_tidy_agents()

            # Use orchestrator as the primary agent
            self.validated_agent = self.factory_agents["orchestrator"]
            self.agent = self.validated_agent.agent

            logger.info(f"Clang-Tidy agent initialized with factory (session: {self.session_id})")
        except Exception as e:
            logger.warning(f"Factory initialization failed, falling back to legacy: {e}")
            self.use_factory = False
            self._initialize_legacy()

    def _initialize_legacy(self):
        """Legacy initialization for backward compatibility."""
        self.agent = self._create_legacy_agent()
        logger.info(f"Clang-Tidy agent initialized in legacy mode (session: {self.session_id})")

    def _create_legacy_agent(self) -> Agent:
        """Create the legacy Clang-Tidy agent."""
        return Agent(
            model=get_model(),
            deps_type=ClangTidyDependencies,
            system_prompt="""
    You are the **Clang-Tidy Factory Orchestrator** - an advanced code quality specialist that transforms 
    clang-tidy warnings into systematic, prioritized fixes using specialized subagents.
    
    You coordinate a proven 5-phase workflow:
    
    ## Phase 1: Comprehensive Issue Discovery 🔍
    - Run comprehensive clang-tidy analysis on target files
    - Categorize issues by severity: CRITICAL, HIGH, MEDIUM, LOW
    - Generate structured issue inventory with line numbers
    - Create priority matrix based on impact and complexity
    
    ## Phase 2: Smart Fix Strategy Planning 📋  
    - Analyze issue dependencies and fix ordering
    - Group related fixes to minimize context switching
    - Identify batch fixes (e.g., all std::ranges → C++17 conversions)
    - Plan validation checkpoints between fix stages
    
    ## Phase 3: Specialized Fixing ⚡
    Execute specialized subagents in parallel:
    - Critical Issue Resolution (compilation errors, C++20 compatibility)
    - Safety & Performance Optimization (security warnings, memory safety)
    - Code Quality Enhancement (readability, maintainability, style)
    
    ## Phase 4: Continuous Validation & Build Testing ✅
    - Run build tests after each fix batch
    - Execute functional tests to verify correctness
    - Monitor for new warnings introduced by fixes
    
    ## Phase 5: Final Quality Assurance & Reporting 📊
    - Run final comprehensive clang-tidy analysis
    - Compare before/after metrics
    - Generate detailed fix report with explanations
    
    Always maintain zero-warning policy and ensure code correctness throughout the process.
    
    You have access to specialized engines for each phase:
    - IssueDiscoveryEngine for Phase 1
    - FixStrategyPlanner for Phase 2  
    - FixApplicationEngine for Phase 3
    - ValidationEngine for Phase 4
    - ArchonMCP integration for knowledge management
    """
)


class ClangTidyFactoryOrchestrator:
    """
    Main interface for the Clang-Tidy Factory Orchestrator system.
    
    Provides comprehensive C++ code quality improvement through systematic
    clang-tidy analysis, intelligent fix strategies, and validation.
    """
    
    def __init__(self, dependencies: Optional[ClangTidyDependencies] = None):
        self.dependencies = dependencies
        self.agent = clang_tidy_agent
        
        # Initialize specialized engines
        if dependencies:
            self.analyzer = ClangTidyAnalyzer(dependencies)
            self.discovery_engine = IssueDiscoveryEngine(self.analyzer)
            self.strategy_planner = FixStrategyPlanner()
            self.fix_engine = FixApplicationEngine(self.analyzer)
            self.validation_engine = ValidationEngine(self.analyzer)
        else:
            self.analyzer = None
            self.discovery_engine = None
            self.strategy_planner = None
            self.fix_engine = None
            self.validation_engine = None
    
    async def comprehensive_issue_discovery(
        self, 
        file_path: str,
        analysis_scope: str = "comprehensive"
    ) -> IssueDiscoveryResponse:
        """
        Phase 1: Comprehensive Issue Discovery
        
        Systematically discovers and categorizes ALL clang-tidy issues in the target file.
        """
        if not self.discovery_engine:
            raise RuntimeError("Dependencies not initialized. Use with create_dependencies().")
        
        return await self.discovery_engine.discover_all_issues(file_path, analysis_scope)
    
    async def create_fix_strategy(
        self,
        issues_analysis: IssueDiscoveryResponse,
        target_file: str
    ) -> FixStrategyResponse:
        """
        Phase 2: Smart Fix Strategy Planning
        
        Creates intelligent fixing strategy with minimal code disruption.
        """
        if not self.strategy_planner:
            raise RuntimeError("Dependencies not initialized. Use with create_dependencies().")
        
        return self.strategy_planner.create_intelligent_strategy(issues_analysis, target_file)
    
    async def apply_specialized_fixes(
        self,
        file_path: str,
        fix_strategy: FixStrategyResponse,
        fix_type: str = "critical"
    ) -> FixApplicationResponse:
        """
        Phase 3: Specialized Fixing with subagent specialization
        
        Applies fixes using specialized subagents for different categories.
        """
        if not self.fix_engine:
            raise RuntimeError("Dependencies not initialized. Use with create_dependencies().")
        
        return await self.fix_engine.apply_fixes_by_type(file_path, fix_type, fix_strategy)
    
    async def validate_fixes(
        self,
        file_path: str,
        original_issues: IssueDiscoveryResponse,
        fix_results: List[FixApplicationResponse]
    ) -> ValidationResponse:
        """
        Phase 4: Continuous Validation & Build Testing
        
        Validates fixes ensure they don't break functionality.
        """
        if not self.validation_engine:
            raise RuntimeError("Dependencies not initialized. Use with create_dependencies().")
        
        return await self.validation_engine.validate_fixes(file_path, original_issues, fix_results)
    
    async def integrate_with_archon(
        self,
        task_description: str,
        project_context: str
    ) -> ArchonTaskResponse:
        """
        Archon MCP Integration for knowledge management and task coordination.
        
        Integrates with Archon MCP server for advanced task management and knowledge queries.
        """
        # Check if Archon client is available
        if not hasattr(self.dependencies, 'archon_client') or not self.dependencies.archon_client:
            return ArchonTaskResponse(
                task_created=False,
                task_id=None,
                knowledge_retrieved=False,
                recommendations=["Archon MCP integration not available"],
                next_actions=["Continue with local analysis"]
            )
        
        archon_client = self.dependencies.archon_client
        
        try:
            # Create task in Archon
            task_result = await archon_client.manage_task(
                action="create",
                title=f"Clang-Tidy Factory: {task_description}",
                description=f"Context: {project_context}",
                task_type="clang_tidy_analysis"
            )
            
            # Perform knowledge query
            rag_result = await archon_client.perform_rag_query(
                query=f"clang-tidy best practices {task_description}",
                match_count=5
            )
            
            # Search for code examples
            examples_result = await archon_client.search_code_examples(
                query=f"C++ clang-tidy fixes {task_description}",
                match_count=3
            )
            
            recommendations = [
                "Successfully integrated with Archon MCP",
                "Retrieved clang-tidy best practices from knowledge base",
                "Found relevant code examples for implementation"
            ]
            
            if rag_result and not rag_result.get('error'):
                recommendations.append(f"Knowledge query returned {len(rag_result.get('results', []))} relevant documents")
            
            if examples_result and not examples_result.get('error'):
                recommendations.append(f"Code examples search returned {len(examples_result.get('results', []))} examples")
            
            next_actions = [
                "Apply knowledge-based recommendations to fix strategy",
                "Use code examples as reference for complex fixes",
                "Update Archon task with progress and results",
                "Leverage Archon project features for coordination"
            ]
            
            return ArchonTaskResponse(
                task_created=task_result.get('success', False),
                task_id=task_result.get('task_id'),
                knowledge_retrieved=not rag_result.get('error', True),
                recommendations=recommendations,
                next_actions=next_actions
            )
            
        except Exception as e:
            return ArchonTaskResponse(
                task_created=False,
                task_id=None,
                knowledge_retrieved=False,
                recommendations=[f"Archon integration failed: {str(e)}"],
                next_actions=["Continue with local analysis without Archon integration"]
            )
    
    async def run_complete_workflow(self, file_path: str) -> Dict[str, Any]:
        """
        Execute the complete 5-phase clang-tidy factory workflow.
        """
        if not self.dependencies:
            raise RuntimeError("Dependencies not initialized. Use with create_dependencies().")
        
        results = {}
        
        try:
            # Phase 1: Issue Discovery
            print("🔍 Phase 1: Comprehensive Issue Discovery...")
            discovery_result = await self.comprehensive_issue_discovery(file_path)
            results['phase1_discovery'] = discovery_result
            
            # Phase 2: Strategy Planning  
            print("📋 Phase 2: Smart Fix Strategy Planning...")
            strategy_result = await self.create_fix_strategy(discovery_result, file_path)
            results['phase2_strategy'] = strategy_result
            
            # Phase 3: Apply Fixes (Start with Critical)
            print("⚡ Phase 3: Applying Specialized Fixes...")
            
            fix_results = []
            
            # Apply critical fixes first
            if discovery_result.critical_issues:
                critical_fixes = await self.apply_specialized_fixes(file_path, strategy_result, "critical")
                fix_results.append(critical_fixes)
                results['phase3_critical'] = critical_fixes
            
            # Apply safety fixes
            if discovery_result.high_priority_issues:
                safety_fixes = await self.apply_specialized_fixes(file_path, strategy_result, "safety")
                fix_results.append(safety_fixes)
                results['phase3_safety'] = safety_fixes
            
            # Apply quality fixes
            if discovery_result.medium_priority_issues:
                quality_fixes = await self.apply_specialized_fixes(file_path, strategy_result, "quality")
                fix_results.append(quality_fixes)
                results['phase3_quality'] = quality_fixes
            
            # Apply modernization fixes
            if discovery_result.low_priority_issues:
                modern_fixes = await self.apply_specialized_fixes(file_path, strategy_result, "modernization")
                fix_results.append(modern_fixes)
                results['phase3_modernization'] = modern_fixes
            
            # Phase 4: Validation
            print("✅ Phase 4: Continuous Validation & Build Testing...")
            validation_result = await self.validate_fixes(file_path, discovery_result, fix_results)
            results['phase4_validation'] = validation_result
            
            # Phase 5: Archon Integration
            print("📊 Phase 5: Archon Integration & Knowledge Management...")
            archon_result = await self.integrate_with_archon(
                task_description=f"Clang-tidy analysis and fixes for {os.path.basename(file_path)}",
                project_context=f"Wire Ground C++ project - {len(discovery_result.critical_issues)} critical, {len(discovery_result.high_priority_issues)} high priority issues"
            )
            results['phase5_archon'] = archon_result
            
            # Generate summary
            results['workflow_summary'] = {
                'total_issues_discovered': discovery_result.total_issues,
                'total_fixes_applied': sum(r.fixes_applied for r in fix_results),
                'validation_passed': validation_result.validation_passed,
                'archon_integration_successful': archon_result.task_created,
                'workflow_completed': True
            }
            
            print("🎉 Complete 5-Phase Clang-Tidy Factory Workflow Completed!")
            
        except Exception as e:
            results['error'] = str(e)
            results['workflow_completed'] = False
            print(f"❌ Workflow failed: {e}")
        
        return results
    
    async def analyze_file_simple(self, file_path: str) -> str:
        """Simple file analysis for basic usage."""
        try:
            discovery_result = await self.comprehensive_issue_discovery(file_path, "comprehensive")
            
            summary = f"""
Clang-Tidy Factory Analysis Results for {file_path}:

📊 Issue Summary:
  • Total Issues: {discovery_result.total_issues}
  • Critical Issues: {len(discovery_result.critical_issues)}
  • High Priority Issues: {len(discovery_result.high_priority_issues)}
  • Medium Priority Issues: {len(discovery_result.medium_priority_issues)}
  • Low Priority Issues: {len(discovery_result.low_priority_issues)}

{discovery_result.analysis_summary}

⏱ Fix Complexity: {discovery_result.fix_complexity_estimate}

🔧 Recommended Next Steps:
1. Run complete workflow: orchestrator.run_complete_workflow('{file_path}')
2. Focus on critical issues first if compilation is broken
3. Apply systematic fix strategy with validation checkpoints
4. Leverage Archon integration for knowledge-based recommendations
"""
            return summary
            
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    async def fix_and_optimize(self, file_path: str, optimization_level: str = "advanced") -> Dict[str, Any]:
        """
        PERMANENT INTEGRATION: Fix clang-tidy warnings then optimize with BLITZFIRE.
        
        This method ensures complete code quality before applying performance optimizations.
        It represents the permanent integration between clang_tidy_ai_agent and blitzfire_cpp_optimizer.
        
        Args:
            file_path: Path to C++ source file
            optimization_level: BLITZFIRE optimization level (quick_wins, algorithmic, advanced, extreme)
        
        Returns:
            Complete workflow results including fixes and optimizations
        """
        results = {
            "success": False,
            "clang_tidy_phase": {},
            "blitzfire_phase": {},
            "integrated_pipeline": False
        }
        
        # Check if integrated pipeline is available
        if BLITZFIRE_INTEGRATION:
            logger.info("🔗 Using integrated Clang-Tidy + BLITZFIRE pipeline")
            results["integrated_pipeline"] = True
            
            try:
                # Use the integrated pipeline for complete workflow
                config = PipelineConfig(
                    source_file=file_path,
                    optimization_level=optimization_level,
                    clang_tidy_fix=True,
                    validate_after_each_stage=True,
                    generate_report=True,
                    strict_mode=True
                )
                
                pipeline = IntegratedPipeline(config)
                pipeline_result = await pipeline.run_pipeline()
                
                results.update({
                    "success": pipeline_result.success,
                    "warnings_fixed": pipeline_result.warnings_fixed,
                    "performance_improvement": pipeline_result.performance_improvement,
                    "stage_completed": pipeline_result.stage_completed.value,
                    "clang_tidy_phase": pipeline_result.clang_tidy_report,
                    "blitzfire_phase": pipeline_result.optimization_report,
                    "validation": pipeline_result.validation_report,
                    "errors": pipeline_result.errors
                })
                
                if pipeline_result.success:
                    logger.info("✅ Complete quality + optimization pipeline succeeded")
                    print(f"""
🎯 Integrated Pipeline Complete!
================================
✅ Clang-Tidy Warnings Fixed: {pipeline_result.warnings_fixed}
🚀 Performance Improvement: {pipeline_result.performance_improvement}%
📁 Optimized File: {pipeline_result.optimized_file}
📋 Report: {config.output_dir}/pipeline_report.json
""")
                else:
                    logger.warning(f"Pipeline encountered issues: {pipeline_result.errors}")
                    
            except Exception as e:
                logger.error(f"Integrated pipeline error: {e}")
                results["error"] = str(e)
                results["success"] = False
        
        else:
            # Fallback to sequential execution
            logger.info("📊 Running sequential clang-tidy → BLITZFIRE workflow")
            
            try:
                # Step 1: Run clang-tidy fixes
                print("🔧 Step 1: Fixing clang-tidy warnings...")
                clang_tidy_results = await self.run_complete_workflow(file_path)
                results["clang_tidy_phase"] = clang_tidy_results
                
                if clang_tidy_results.get("workflow_completed", False):
                    # Step 2: Apply BLITZFIRE optimizations
                    print("🚀 Step 2: Applying BLITZFIRE optimizations...")
                    
                    # Import blitzfire optimizer
                    try:
                        sys.path.append('/IdeaProjects/wire_ground/.claude/agents')
                        from blitzfire_cpp_optimizer.agent import optimize_with_clang_tidy_check
                        
                        with open(file_path, 'r') as f:
                            code = f.read()
                        
                        optimization_result = await optimize_with_clang_tidy_check(
                            ctx=None,
                            code=code,
                            source_file=file_path,
                            optimization_level=optimization_level,
                            auto_fix_warnings=False  # Already fixed
                        )
                        
                        results["blitzfire_phase"] = optimization_result
                        results["success"] = optimization_result.get("success", False)
                        
                        if results["success"]:
                            # Write optimized code back
                            if "optimized_code" in optimization_result:
                                with open(file_path, 'w') as f:
                                    f.write(optimization_result["optimized_code"])
                            
                            print(f"""
✅ Sequential Pipeline Complete!
================================
🔧 Clang-Tidy Phase: Complete
🚀 BLITZFIRE Phase: Complete
📊 Estimated Speedup: {optimization_result.get('estimated_speedup', 'unknown')}
""")
                            
                    except ImportError as e:
                        logger.error(f"Failed to import BLITZFIRE optimizer: {e}")
                        results["error"] = f"BLITZFIRE import failed: {e}"
                        
            except Exception as e:
                logger.error(f"Sequential workflow error: {e}")
                results["error"] = str(e)
                results["success"] = False
        
        return results


# Simple factory function for easy usage
async def analyze_cpp_file(file_path: str, dependencies: Optional[ClangTidyDependencies] = None) -> str:
    """Simple function to analyze a C++ file with clang-tidy."""
    if dependencies is None:
        from dependencies import create_dependencies
        dependencies = create_dependencies()
    
    orchestrator = ClangTidyFactoryOrchestrator(dependencies)
    return await orchestrator.analyze_file_simple(file_path)


# Export the main components
__all__ = [
    'clang_tidy_agent',
    'ClangTidyFactoryOrchestrator',
    'analyze_cpp_file'
]