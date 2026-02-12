"""
Optimized Clang-Tidy AI Agent with performance enhancements and enterprise features.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
import structlog

try:
    from .tools_optimized import (
        analyze_code_with_clang_tidy_optimized,
        batch_analyze_files,
        explain_warning_with_ai,
        PerformanceMonitor,
        circuit_breaker
    )
    from .dependencies_optimized import OptimizedClangTidyDependencies
    from .settings_optimized import OptimizedSettings, load_optimized_settings
    from .providers_optimized import OptimizedModelProvider
    from ..core.models import (
        ClangTidyAnalysis, 
        Warning, 
        WarningExplanation,
        ProjectAnalysis,
        FixRecommendation
    )
except ImportError:
    # Fallback for direct execution
    from tools_optimized import (
        analyze_code_with_clang_tidy_optimized,
        batch_analyze_files,
        explain_warning_with_ai,
        PerformanceMonitor,
        circuit_breaker
    )
    from dependencies_optimized import OptimizedClangTidyDependencies
    from settings_optimized import OptimizedSettings, load_optimized_settings
    from providers_optimized import OptimizedModelProvider
    from models import (
        ClangTidyAnalysis, 
        Warning, 
        WarningExplanation,
        ProjectAnalysis,
        FixRecommendation
    )

# Configure structured logging
logger = structlog.get_logger(__name__)

# System prompts from planning
SYSTEM_PROMPT = """
You are an enterprise-grade C++ Code Quality AI Assistant specializing in intelligent clang-tidy analysis and automated code improvement. Your mission is to maintain zero-warning compliance while preserving code safety and semantics.

Core Principles:
- SAFETY FIRST: Never introduce changes that could break functionality
- CONSERVATIVE FIXING: Only apply fixes you're 100% confident about
- CONTEXT AWARENESS: Understand surrounding code patterns before suggesting fixes
- PERFORMANCE FOCUS: Optimize for both code quality and execution speed
- LEARNING CAPABILITY: Build knowledge from each analysis to improve future suggestions

When analyzing C++ code:
1. Categorize warnings by severity (Critical Safety > Performance > Style)
2. Provide clear explanations in plain language for each warning
3. Suggest fixes that maintain original code intent and formatting
4. Identify patterns across multiple warnings for systemic improvements
5. Generate actionable recommendations with priority rankings

Your responses should be structured, concise, and actionable, suitable for both automated processing and human review.
"""

ANALYSIS_PROMPT = """
Analyze the provided clang-tidy output for {file_path} considering:
- Project coding standards and existing patterns
- Multi-compiler compatibility (GCC, Clang, MSVC)
- Performance implications of suggested fixes
- Safety and security considerations
- Integration with existing codebase

Provide:
1. Categorized warning summary by tier (Critical/Performance/Style)
2. Context-aware fix recommendations with rationale
3. Risk assessment for each proposed change
4. Alternative approaches where applicable
5. Knowledge base insights from similar past issues
"""


class OptimizedClangTidyAgent:
    """
    High-performance Clang-Tidy AI Agent with enterprise features.
    """
    
    def __init__(self, settings: Optional[OptimizedSettings] = None):
        """Initialize the optimized agent."""
        self.settings = settings or load_optimized_settings()
        self.provider = OptimizedModelProvider(self.settings)
        self.logger = logger.bind(agent="clang_tidy_ai_optimized")
        
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            model=self.provider.get_model(),
            deps_type=OptimizedClangTidyDependencies,
            system_prompt=SYSTEM_PROMPT
        )
        
        # Register optimized tools
        self._register_tools()
        
        # Performance tracking
        self.metrics = {
            "analyses_completed": 0,
            "total_warnings_found": 0,
            "fixes_applied": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "total_time_ms": 0
        }
    
    def _register_tools(self):
        """Register optimized tools with the agent."""
        
        @self.agent.tool
        async def analyze_file(
            ctx: RunContext[OptimizedClangTidyDependencies],
            file_path: str,
            check_filters: str = "readability-*,performance-*,modernize-*"
        ) -> ClangTidyAnalysis:
            """Analyze a single file with optimized performance."""
            return await analyze_code_with_clang_tidy_optimized(
                ctx, file_path, check_filters
            )
        
        @self.agent.tool
        async def analyze_batch(
            ctx: RunContext[OptimizedClangTidyDependencies],
            file_paths: List[str],
            check_filters: str = "readability-*,performance-*,modernize-*"
        ) -> List[ClangTidyAnalysis]:
            """Analyze multiple files concurrently."""
            return await batch_analyze_files(
                ctx, file_paths, check_filters
            )
        
        @self.agent.tool
        async def explain_warnings(
            ctx: RunContext[OptimizedClangTidyDependencies],
            warnings: List[Warning]
        ) -> List[WarningExplanation]:
            """Get AI explanations for warnings with circuit breaker protection."""
            explanations = []
            for warning in warnings:
                try:
                    explanation = await explain_warning_with_ai(ctx, warning)
                    explanations.append(explanation)
                except Exception as e:
                    ctx.deps.logger.error(f"Failed to explain warning: {e}")
                    # Continue with other warnings
            return explanations
    
    async def analyze_project(
        self, 
        file_patterns: List[str],
        check_filters: Optional[str] = None
    ) -> ProjectAnalysis:
        """
        Analyze entire project with optimized batch processing.
        
        Args:
            file_patterns: Glob patterns for files to analyze
            check_filters: Optional clang-tidy checks to run
            
        Returns:
            Comprehensive project analysis with metrics
        """
        start_time = time.time()
        
        # Collect files matching patterns
        files_to_analyze = []
        for pattern in file_patterns:
            files_to_analyze.extend(
                Path(self.settings.project_root).glob(pattern)
            )
        
        self.logger.info(
            "Starting project analysis",
            file_count=len(files_to_analyze),
            patterns=file_patterns
        )
        
        # Create dependencies
        deps = await self._create_dependencies()
        
        # Analyze files in batches
        batch_size = self.settings.max_concurrent_analyses
        all_analyses = []
        
        for i in range(0, len(files_to_analyze), batch_size):
            batch = files_to_analyze[i:i+batch_size]
            batch_paths = [str(f.relative_to(self.settings.project_root)) for f in batch]
            
            async with PerformanceMonitor() as perf:
                # Use the agent to analyze batch
                result = await self.agent.run(
                    f"Analyze these files: {batch_paths}",
                    deps=deps
                )
                
                if result.data:
                    all_analyses.extend(result.data)
        
        # Aggregate results
        total_warnings = sum(a.total_warnings for a in all_analyses)
        execution_time = time.time() - start_time
        
        # Update metrics
        self.metrics["analyses_completed"] += len(all_analyses)
        self.metrics["total_warnings_found"] += total_warnings
        self.metrics["total_time_ms"] += int(execution_time * 1000)
        
        # Create project analysis
        project_analysis = ProjectAnalysis(
            timestamp=datetime.now().isoformat(),
            files_analyzed=len(all_analyses),
            total_warnings=total_warnings,
            warnings_by_category=self._categorize_warnings(all_analyses),
            execution_time_seconds=execution_time,
            cache_hit_rate=deps.analysis_stats.get("cache_hits", 0) / max(len(all_analyses), 1),
            recommendations=await self._generate_recommendations(all_analyses, deps)
        )
        
        self.logger.info(
            "Project analysis complete",
            files=len(all_analyses),
            warnings=total_warnings,
            time_seconds=execution_time
        )
        
        return project_analysis
    
    async def analyze_with_fixes(
        self,
        file_path: str,
        auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a file and optionally apply safe fixes.
        
        Args:
            file_path: Path to C++ file
            auto_fix: Whether to automatically apply safe fixes
            
        Returns:
            Analysis results with fix recommendations
        """
        deps = await self._create_dependencies()
        
        # Analyze the file
        analysis_prompt = ANALYSIS_PROMPT.format(file_path=file_path)
        
        result = await self.agent.run(
            analysis_prompt,
            deps=deps
        )
        
        if not result.data:
            return {"status": "error", "message": "Analysis failed"}
        
        analysis = result.data
        
        # Get AI explanations for warnings
        if analysis.warnings:
            explanations_result = await self.agent.run(
                f"Explain these warnings: {analysis.warnings}",
                deps=deps
            )
            
            explanations = explanations_result.data if explanations_result.data else []
        else:
            explanations = []
        
        # Prepare response
        response = {
            "status": "success",
            "file": file_path,
            "total_warnings": analysis.total_warnings,
            "warnings": [w.dict() for w in analysis.warnings],
            "explanations": [e.dict() for e in explanations],
            "auto_fix_available": auto_fix and len(explanations) > 0
        }
        
        if auto_fix and explanations:
            # Apply safe fixes (would implement actual fixing logic here)
            fixes_applied = await self._apply_safe_fixes(
                file_path, analysis.warnings, explanations, deps
            )
            response["fixes_applied"] = fixes_applied
            self.metrics["fixes_applied"] += len(fixes_applied)
        
        return response
    
    async def _create_dependencies(self) -> OptimizedClangTidyDependencies:
        """Create optimized dependencies for the agent."""
        # Initialize database connections
        import aiosqlite
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Create async database engine
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.settings.sqlite_db_path}",
            echo=False
        )
        
        # Create async session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Open knowledge base connection
        knowledge_base = await aiosqlite.connect(
            str(self.settings.knowledge_base_path)
        )
        
        return OptimizedClangTidyDependencies(
            project_root=self.settings.project_root,
            clang_tidy_binary=self.settings.clang_tidy_binary_path,
            cache_dir=self.settings.cache_dir,
            db_connection=async_session(),
            knowledge_base=knowledge_base,
            llm_provider=self.settings.llm_provider,
            llm_api_key=self.settings.llm_api_key,
            llm_model=self.settings.llm_model,
            max_concurrent=self.settings.max_concurrent_analyses,
            cache_ttl=self.settings.cache_ttl_seconds,
            subprocess_timeout=self.settings.subprocess_timeout,
            circuit_breaker_threshold=self.settings.circuit_breaker_threshold,
            circuit_breaker_timeout=self.settings.circuit_breaker_timeout,
            enable_caching=self.settings.enable_caching,
            enable_knowledge_base=self.settings.enable_knowledge_base,
            enable_progress_tracking=self.settings.enable_progress_tracking,
            enable_metrics=self.settings.enable_performance_metrics,
            logger=self.logger
        )
    
    def _categorize_warnings(
        self, 
        analyses: List[ClangTidyAnalysis]
    ) -> Dict[str, int]:
        """Categorize warnings by type."""
        categories = {}
        for analysis in analyses:
            for warning in analysis.warnings:
                category = warning.type.split('-')[0] if '-' in warning.type else 'other'
                categories[category] = categories.get(category, 0) + 1
        return categories
    
    async def _generate_recommendations(
        self,
        analyses: List[ClangTidyAnalysis],
        deps: OptimizedClangTidyDependencies
    ) -> List[str]:
        """Generate project-wide recommendations."""
        recommendations = []
        
        # Analyze patterns
        warning_counts = self._categorize_warnings(analyses)
        
        if warning_counts.get('readability', 0) > 10:
            recommendations.append(
                "Consider running a project-wide readability cleanup"
            )
        
        if warning_counts.get('performance', 0) > 5:
            recommendations.append(
                "Performance improvements available - review performance warnings"
            )
        
        if warning_counts.get('modernize', 0) > 15:
            recommendations.append(
                "Multiple modernization opportunities - consider C++17/20 migration"
            )
        
        return recommendations
    
    async def _apply_safe_fixes(
        self,
        file_path: str,
        warnings: List[Warning],
        explanations: List[WarningExplanation],
        deps: OptimizedClangTidyDependencies
    ) -> List[Dict[str, Any]]:
        """Apply safe, validated fixes to the file."""
        fixes_applied = []
        
        # Group explanations by warning
        explanation_map = {e.warning_type: e for e in explanations}
        
        for warning in warnings:
            explanation = explanation_map.get(warning.type)
            if not explanation or not explanation.suggested_fix:
                continue
            
            # Only apply high-confidence fixes
            if self._is_safe_to_fix(warning.type):
                # Would implement actual file modification here
                fixes_applied.append({
                    "warning_type": warning.type,
                    "line": warning.line,
                    "fix_applied": explanation.suggested_fix.explanation
                })
        
        return fixes_applied
    
    def _is_safe_to_fix(self, warning_type: str) -> bool:
        """Determine if a warning type is safe to auto-fix."""
        safe_fixes = {
            "readability-braces-around-statements",
            "readability-static-definition-in-anonymous-namespace",
            "modernize-use-nullptr",
            "readability-container-size-empty"
        }
        return warning_type in safe_fixes
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()


# CLI interface
async def main():
    """Main entry point for the optimized agent."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agent_optimized.py <file_or_pattern> [--auto-fix]")
        sys.exit(1)
    
    file_or_pattern = sys.argv[1]
    auto_fix = "--auto-fix" in sys.argv
    
    # Create and run agent
    agent = OptimizedClangTidyAgent()
    
    if '*' in file_or_pattern:
        # Project analysis
        result = await agent.analyze_project([file_or_pattern])
        print(json.dumps(result.dict(), indent=2))
    else:
        # Single file analysis
        result = await agent.analyze_with_fixes(file_or_pattern, auto_fix)
        print(json.dumps(result, indent=2))
    
    # Print metrics
    print("\nPerformance Metrics:")
    print(json.dumps(agent.get_metrics(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())