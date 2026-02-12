"""
Shared Integration Module for Clang-Tidy AI Agent and BLITZFIRE C++ Optimizer
===============================================================================

This module provides permanent integration between:
- clang_tidy_ai_agent: Code quality, safety, and compliance
- blitzfire_cpp_optimizer: Performance optimization and speed improvements

The integration ensures both agents work together in a unified pipeline.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages for the integrated workflow."""
    INITIAL_ANALYSIS = "initial_analysis"
    CLANG_TIDY_FIX = "clang_tidy_fix"
    PERFORMANCE_OPTIMIZE = "performance_optimize"
    FINAL_VALIDATION = "final_validation"
    COMPLETE = "complete"


@dataclass
class PipelineConfig:
    """Configuration for the integrated pipeline."""
    # File paths
    source_file: str
    output_dir: str = ".claude/agents/pipeline_output"
    
    # Clang-tidy settings
    clang_tidy_checks: str = "concurrency-*,cert-*,performance-*,readability-*,modernize-*"
    clang_tidy_fix: bool = True
    clang_tidy_format: bool = True
    
    # BLITZFIRE settings
    optimization_level: str = "advanced"  # quick_wins, algorithmic, advanced, extreme
    enable_simd: bool = True
    enable_parallel: bool = True
    enable_cache_opt: bool = True
    
    # Pipeline settings
    validate_after_each_stage: bool = True
    generate_report: bool = True
    backup_original: bool = True
    
    # Integration settings
    max_iterations: int = 3  # Max times to retry if validation fails
    strict_mode: bool = True  # Fail if any warnings remain


@dataclass
class PipelineResult:
    """Result of the integrated pipeline execution."""
    success: bool
    stage_completed: PipelineStage
    
    # Metrics
    warnings_fixed: int = 0
    performance_improvement: float = 0.0  # Percentage
    
    # Details
    clang_tidy_report: Dict[str, Any] = field(default_factory=dict)
    optimization_report: Dict[str, Any] = field(default_factory=dict)
    validation_report: Dict[str, Any] = field(default_factory=dict)
    
    # Files
    original_file: str = ""
    optimized_file: str = ""
    backup_file: str = ""
    
    # Errors
    errors: List[str] = field(default_factory=list)


class IntegratedPipeline:
    """
    Unified pipeline orchestrator for Clang-Tidy and BLITZFIRE optimization.
    
    Workflow:
    1. Initial Analysis: Baseline metrics and issue discovery
    2. Clang-Tidy Fix: Fix all code quality issues
    3. Performance Optimize: Apply BLITZFIRE optimizations
    4. Final Validation: Ensure no regressions
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.current_stage = PipelineStage.INITIAL_ANALYSIS
        self.iteration = 0
        
        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Import agents lazily to avoid circular dependencies
        self._clang_tidy_agent = None
        self._blitzfire_agent = None
    
    @property
    def clang_tidy_agent(self):
        """Lazy load clang-tidy agent."""
        if self._clang_tidy_agent is None:
            try:
                from clang_tidy_ai_agent.agent import ClangTidyFactoryOrchestrator
                from clang_tidy_ai_agent.models import ClangTidyDependencies
                deps = ClangTidyDependencies(
                    source_file=self.config.source_file,
                    clang_tidy_checks=self.config.clang_tidy_checks
                )
                self._clang_tidy_agent = ClangTidyFactoryOrchestrator(deps)
            except ImportError as e:
                logger.error(f"Failed to import clang_tidy_ai_agent: {e}")
                # Fallback to subprocess
                self._clang_tidy_agent = None
        return self._clang_tidy_agent
    
    @property
    def blitzfire_agent(self):
        """Lazy load BLITZFIRE optimizer agent."""
        if self._blitzfire_agent is None:
            try:
                from blitzfire_cpp_optimizer.agent import optimize_cpp_code
                from blitzfire_cpp_optimizer.dependencies import BlitzfireDependencies
                deps = BlitzfireDependencies(
                    optimization_level=self.config.optimization_level
                )
                self._blitzfire_agent = optimize_cpp_code
            except ImportError as e:
                logger.error(f"Failed to import blitzfire_cpp_optimizer: {e}")
                # Fallback to subprocess
                self._blitzfire_agent = None
        return self._blitzfire_agent
    
    async def run_pipeline(self) -> PipelineResult:
        """
        Execute the complete integrated pipeline.
        
        Returns:
            PipelineResult with complete execution details
        """
        result = PipelineResult(success=False, stage_completed=PipelineStage.INITIAL_ANALYSIS)
        
        try:
            # Stage 1: Initial Analysis
            logger.info("🔍 Stage 1: Initial Analysis")
            initial_metrics = await self._run_initial_analysis()
            result.clang_tidy_report['initial'] = initial_metrics
            
            # Backup original file
            if self.config.backup_original:
                result.backup_file = await self._backup_file()
                result.original_file = self.config.source_file
            
            # Stage 2: Clang-Tidy Fix
            logger.info("🔧 Stage 2: Clang-Tidy Code Quality Fixes")
            self.current_stage = PipelineStage.CLANG_TIDY_FIX
            
            clang_tidy_result = await self._run_clang_tidy_fixes()
            result.clang_tidy_report['fixes'] = clang_tidy_result
            result.warnings_fixed = clang_tidy_result.get('warnings_fixed', 0)
            
            if self.config.validate_after_each_stage:
                if not await self._validate_clang_tidy():
                    result.errors.append("Clang-tidy validation failed")
                    if self.config.strict_mode:
                        return result
            
            # Stage 3: BLITZFIRE Performance Optimization
            logger.info("🚀 Stage 3: BLITZFIRE Performance Optimization")
            self.current_stage = PipelineStage.PERFORMANCE_OPTIMIZE
            
            optimization_result = await self._run_blitzfire_optimization()
            result.optimization_report = optimization_result
            result.performance_improvement = optimization_result.get('speedup', 0.0)
            
            if self.config.validate_after_each_stage:
                if not await self._validate_optimization():
                    result.errors.append("Optimization validation failed")
                    if self.config.strict_mode:
                        return result
            
            # Stage 4: Final Validation
            logger.info("✅ Stage 4: Final Validation")
            self.current_stage = PipelineStage.FINAL_VALIDATION
            
            final_validation = await self._run_final_validation()
            result.validation_report = final_validation
            
            # Check success criteria
            if final_validation.get('zero_warnings', False) and \
               final_validation.get('build_success', False):
                result.success = True
                result.stage_completed = PipelineStage.COMPLETE
                result.optimized_file = self.config.source_file
                logger.info("✨ Pipeline completed successfully!")
            else:
                result.errors.append("Final validation failed")
                logger.error("Pipeline failed final validation")
            
            # Generate report
            if self.config.generate_report:
                await self._generate_report(result)
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            result.errors.append(str(e))
        
        return result
    
    async def _run_initial_analysis(self) -> Dict[str, Any]:
        """Run initial clang-tidy analysis to get baseline metrics."""
        if self.clang_tidy_agent:
            # Use agent
            return await self.clang_tidy_agent.discover_issues()
        else:
            # Fallback to subprocess
            cmd = [
                "clang-tidy",
                self.config.source_file,
                f"-checks={self.config.clang_tidy_checks}",
                "--export-fixes=-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "warnings_count": result.stdout.count("warning:"),
                "errors_count": result.stdout.count("error:"),
                "raw_output": result.stdout
            }
    
    async def _run_clang_tidy_fixes(self) -> Dict[str, Any]:
        """Apply clang-tidy fixes."""
        if self.clang_tidy_agent:
            # Use agent's fix workflow
            return await self.clang_tidy_agent.apply_fixes()
        else:
            # Fallback to subprocess
            cmd = [
                "python3",
                ".claude/agents/clang_tidy_ai_agent/cli.py",
                "fix",
                "--file", self.config.source_file,
                "--checks", self.config.clang_tidy_checks
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"success": result.returncode == 0, "output": result.stdout}
    
    async def _run_blitzfire_optimization(self) -> Dict[str, Any]:
        """Apply BLITZFIRE performance optimizations."""
        if self.blitzfire_agent:
            # Use agent
            return await self.blitzfire_agent(
                ctx=None,
                code=Path(self.config.source_file).read_text(),
                optimization_level=self.config.optimization_level,
                enable_simd=self.config.enable_simd,
                enable_parallel=self.config.enable_parallel
            )
        else:
            # Fallback to subprocess
            cmd = [
                "python3",
                ".claude/agents/blitzfire_cpp_optimizer/cli.py",
                "optimize",
                "--file", self.config.source_file,
                "--level", self.config.optimization_level
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {"success": result.returncode == 0, "output": result.stdout}
    
    async def _validate_clang_tidy(self) -> bool:
        """Validate no clang-tidy warnings remain."""
        analysis = await self._run_initial_analysis()
        return analysis.get('warnings_count', 0) == 0
    
    async def _validate_optimization(self) -> bool:
        """Validate optimization didn't introduce new warnings."""
        analysis = await self._run_initial_analysis()
        # Also check that optimization was applied
        with open(self.config.source_file, 'r') as f:
            code = f.read()
            # Check for optimization markers
            has_simd = "mm256" in code or "mm512" in code if self.config.enable_simd else True
            has_parallel = "#pragma omp" in code if self.config.enable_parallel else True
            
        return analysis.get('warnings_count', 0) == 0 and has_simd and has_parallel
    
    async def _run_final_validation(self) -> Dict[str, Any]:
        """Run comprehensive final validation."""
        validation = {
            "zero_warnings": False,
            "build_success": False,
            "tests_pass": False,
            "performance_validated": False
        }
        
        # Check warnings
        analysis = await self._run_initial_analysis()
        validation["zero_warnings"] = analysis.get('warnings_count', 0) == 0
        
        # Try to build
        build_cmd = [
            "/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake",
            "--build", "cmake-build-debug",
            "--target", "wire_ground_tests"
        ]
        build_result = subprocess.run(build_cmd, capture_output=True, text=True, cwd="/IdeaProjects/wire_ground")
        validation["build_success"] = build_result.returncode == 0
        
        return validation
    
    async def _backup_file(self) -> str:
        """Backup the original file."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.config.output_dir}/backup_{timestamp}_{Path(self.config.source_file).name}"
        
        with open(self.config.source_file, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        
        logger.info(f"Backed up to: {backup_path}")
        return backup_path
    
    async def _generate_report(self, result: PipelineResult):
        """Generate detailed pipeline execution report."""
        report_path = f"{self.config.output_dir}/pipeline_report.json"
        
        report = {
            "success": result.success,
            "stage_completed": result.stage_completed.value,
            "metrics": {
                "warnings_fixed": result.warnings_fixed,
                "performance_improvement": f"{result.performance_improvement}%"
            },
            "files": {
                "original": result.original_file,
                "optimized": result.optimized_file,
                "backup": result.backup_file
            },
            "details": {
                "clang_tidy": result.clang_tidy_report,
                "optimization": result.optimization_report,
                "validation": result.validation_report
            },
            "errors": result.errors
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")


# Convenience functions for direct usage

async def optimize_with_quality(
    source_file: str,
    optimization_level: str = "advanced",
    strict: bool = True
) -> PipelineResult:
    """
    Run the complete quality + optimization pipeline.
    
    Args:
        source_file: Path to C++ source file
        optimization_level: quick_wins, algorithmic, advanced, or extreme
        strict: Fail if any warnings remain
    
    Returns:
        PipelineResult with execution details
    """
    config = PipelineConfig(
        source_file=source_file,
        optimization_level=optimization_level,
        strict_mode=strict
    )
    
    pipeline = IntegratedPipeline(config)
    return await pipeline.run_pipeline()


def optimize_with_quality_sync(
    source_file: str,
    optimization_level: str = "advanced",
    strict: bool = True
) -> PipelineResult:
    """Synchronous wrapper for optimize_with_quality."""
    return asyncio.run(optimize_with_quality(source_file, optimization_level, strict))


# Make agents aware of each other
INTEGRATION_ENABLED = True
PIPELINE_VERSION = "1.0.0"

__all__ = [
    "PipelineConfig",
    "PipelineResult", 
    "PipelineStage",
    "IntegratedPipeline",
    "optimize_with_quality",
    "optimize_with_quality_sync",
    "INTEGRATION_ENABLED",
    "PIPELINE_VERSION"
]