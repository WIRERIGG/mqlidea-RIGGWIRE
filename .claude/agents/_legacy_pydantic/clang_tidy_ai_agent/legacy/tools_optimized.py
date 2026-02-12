"""Optimized Tools for the Clang-Tidy AI Agent with async and performance improvements."""

import subprocess
import hashlib
import json
import asyncio
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
from asyncio import Queue, Semaphore
from pydantic_ai import RunContext

try:
    from .dependencies_optimized import OptimizedClangTidyDependencies
    from ..core.models import (
        ClangTidyAnalysis, Warning, WarningExplanation, FixRecommendation, 
        PreferenceUpdate, ProjectAnalysis, CodeExamples, FixStrategy, AlternativeApproach
    )
except ImportError:
    from dependencies_optimized import OptimizedClangTidyDependencies
    from core.models import (
        ClangTidyAnalysis, Warning, WarningExplanation, FixRecommendation, 
        PreferenceUpdate, ProjectAnalysis, CodeExamples, FixStrategy, AlternativeApproach
    )
    
# Alias for backward compatibility
ClangTidyDependencies = OptimizedClangTidyDependencies

# Performance configuration
MAX_CONCURRENT_ANALYSES = 4
CACHE_TTL_SECONDS = 3600
SUBPROCESS_TIMEOUT = 30
MAX_RETRIES = 3
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)

# Semaphore for rate limiting
analysis_semaphore = Semaphore(MAX_CONCURRENT_ANALYSES)

# Circuit breaker state
circuit_breaker_state = {
    "failures": 0,
    "last_failure_time": 0,
    "is_open": False
}

class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        self.metrics = {}
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        return False
    
    @staticmethod
    def log_metric(operation: str, duration: float, success: bool = True):
        """Log performance metric."""
        status = "success" if success else "failure"
        print(f"[PERF] {operation}: {duration:.2f}s ({status})")

def circuit_breaker(func):
    """Circuit breaker decorator for resilient API calls."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if circuit is open
        if circuit_breaker_state["is_open"]:
            time_since_failure = time.time() - circuit_breaker_state["last_failure_time"]
            if time_since_failure < CIRCUIT_BREAKER_TIMEOUT:
                raise Exception("Circuit breaker is open - service temporarily unavailable")
            else:
                # Reset circuit breaker
                circuit_breaker_state["is_open"] = False
                circuit_breaker_state["failures"] = 0
        
        try:
            result = await func(*args, **kwargs)
            # Reset failure count on success
            circuit_breaker_state["failures"] = 0
            return result
        except Exception as e:
            circuit_breaker_state["failures"] += 1
            circuit_breaker_state["last_failure_time"] = time.time()
            
            if circuit_breaker_state["failures"] >= CIRCUIT_BREAKER_THRESHOLD:
                circuit_breaker_state["is_open"] = True
                print(f"[CIRCUIT BREAKER] Opened after {CIRCUIT_BREAKER_THRESHOLD} failures")
            
            raise e
    
    return wrapper

def cache_analysis_result(ttl_seconds: int = CACHE_TTL_SECONDS):
    """Decorator for caching analysis results with TTL."""
    cache = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = hashlib.md5(
                f"{args}{kwargs}".encode()
            ).hexdigest()
            
            # Check cache
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if time.time() - cached_time < ttl_seconds:
                    return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = (time.time(), result)
            
            return result
        
        return wrapper
    
    return decorator

async def run_clang_tidy_async(
    cmd: List[str], 
    cwd: Path, 
    timeout: int = SUBPROCESS_TIMEOUT
) -> tuple[str, str]:
    """Run clang-tidy asynchronously with timeout."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        return stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise TimeoutError(f"Clang-tidy timed out after {timeout} seconds")

@cache_analysis_result()
async def analyze_code_with_clang_tidy_optimized(
    ctx: RunContext[ClangTidyDependencies],
    file_path: str,
    check_filters: str = "readability-*,performance-*,modernize-*"
) -> ClangTidyAnalysis:
    """
    Optimized async version of clang-tidy analysis with caching and performance improvements.
    
    Args:
        file_path: Path to C++ file to analyze (relative to project root)
        check_filters: Comma-separated list of clang-tidy checks to run
        
    Returns:
        ClangTidyAnalysis with warnings, suggestions, and context information
    """
    deps = ctx.deps
    logger = deps.logger
    
    async with analysis_semaphore:  # Rate limiting
        async with PerformanceMonitor() as perf:
            try:
                # Resolve full path
                full_path = deps.settings.project_root / file_path
                if not full_path.exists():
                    logger.error(f"File not found: {full_path}")
                    return ClangTidyAnalysis(
                        file_path=file_path,
                        total_warnings=0,
                        warnings=[]
                    )
                
                # Check in-memory cache first (decorator handles this)
                
                # Check persistent cache
                if deps.settings.cache_analysis_results:
                    file_hash = await asyncio.get_event_loop().run_in_executor(
                        executor, _calculate_file_hash, full_path
                    )
                    cached_result = await _get_cached_analysis_async(
                        deps.db_connection, file_path, file_hash
                    )
                    if cached_result:
                        deps.analysis_stats["cache_hits"] += 1
                        logger.info(f"Using cached analysis for {file_path}")
                        PerformanceMonitor.log_metric("cache_hit", 0.01)
                        return cached_result
                
                # Prepare command
                cmd = [
                    str(deps.settings.clang_tidy_binary_path),
                    f"--checks={check_filters}",
                    "--format-style=file",
                    "--export-fixes=-",
                    str(full_path),
                    "--",
                    "-I/usr/include",
                    "-I/usr/include/c++/12"
                ]
                
                # Run clang-tidy asynchronously
                logger.info(f"Running async clang-tidy on {file_path}")
                start_time = time.time()
                
                stdout, stderr = await run_clang_tidy_async(
                    cmd, deps.settings.project_root
                )
                
                analysis_time = time.time() - start_time
                PerformanceMonitor.log_metric("clang_tidy_run", analysis_time)
                
                # Parse output in thread pool
                warnings = await asyncio.get_event_loop().run_in_executor(
                    executor, _parse_clang_tidy_output_optimized, stdout, stderr, file_path
                )
                
                analysis = ClangTidyAnalysis(
                    file_path=file_path,
                    warnings=warnings,
                    total_warnings=len(warnings),
                    clang_tidy_version=await _get_clang_tidy_version_async(
                        deps.settings.clang_tidy_binary_path
                    )
                )
                
                # Cache result asynchronously
                if deps.settings.cache_analysis_results:
                    asyncio.create_task(
                        _cache_analysis_async(
                            deps.db_connection, file_path, file_hash, analysis
                        )
                    )
                
                deps.analysis_stats["total_analyses"] += 1
                logger.info(f"Analysis complete: {len(warnings)} warnings in {analysis_time:.2f}s")
                
                return analysis
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                PerformanceMonitor.log_metric("analysis_error", 0, success=False)
                return ClangTidyAnalysis(
                    file_path=file_path,
                    total_warnings=0,
                    warnings=[]
                )

async def batch_analyze_files(
    ctx: RunContext[ClangTidyDependencies],
    file_paths: List[str],
    check_filters: str = "readability-*,performance-*,modernize-*"
) -> List[ClangTidyAnalysis]:
    """
    Analyze multiple files concurrently with optimized batch processing.
    
    Args:
        file_paths: List of file paths to analyze
        check_filters: Clang-tidy checks to run
        
    Returns:
        List of ClangTidyAnalysis results
    """
    tasks = []
    for file_path in file_paths:
        task = analyze_code_with_clang_tidy_optimized(ctx, file_path, check_filters)
        tasks.append(task)
    
    # Process files concurrently with rate limiting
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return valid results
    valid_results = []
    for result in results:
        if isinstance(result, ClangTidyAnalysis):
            valid_results.append(result)
        else:
            ctx.deps.logger.error(f"Batch analysis error: {result}")
    
    return valid_results

@circuit_breaker
async def explain_warning_with_ai(
    ctx: RunContext[ClangTidyDependencies],
    warning: Warning
) -> WarningExplanation:
    """
    Get AI-powered explanation for a clang-tidy warning with circuit breaker protection.
    
    Args:
        warning: The warning to explain
        
    Returns:
        WarningExplanation with detailed context and suggestions
    """
    deps = ctx.deps
    
    async with PerformanceMonitor() as perf:
        try:
            # Implementation would call LLM API here
            # For now, return a mock response
            explanation = WarningExplanation(
                warning_type=warning.type,
                plain_english_explanation="Mock explanation",
                why_it_matters="Mock importance",
                potential_impact="Mock impact",
                suggested_fix=FixRecommendation(
                    code_before="// before",
                    code_after="// after",
                    explanation="Mock fix explanation"
                ),
                related_best_practices=["Best practice 1", "Best practice 2"]
            )
            
            PerformanceMonitor.log_metric("ai_explanation", 0.5)
            return explanation
            
        except Exception as e:
            deps.logger.error(f"AI explanation failed: {e}")
            raise

# Helper functions (optimized versions)

def _calculate_file_hash(file_path: Path) -> str:
    """Calculate hash of file contents for caching."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

async def _get_cached_analysis_async(connection, file_path: str, file_hash: str) -> Optional[ClangTidyAnalysis]:
    """Async version of cache retrieval."""
    # Implementation would query database asynchronously
    return None

async def _cache_analysis_async(connection, file_path: str, file_hash: str, analysis: ClangTidyAnalysis):
    """Async version of cache storage."""
    # Implementation would store in database asynchronously
    pass

@lru_cache(maxsize=1)
async def _get_clang_tidy_version_async(binary_path: Path) -> str:
    """Get clang-tidy version with caching."""
    try:
        cmd = [str(binary_path), "--version"]
        stdout, _ = await run_clang_tidy_async(cmd, Path.cwd(), timeout=5)
        return stdout.split('\n')[0] if stdout else "unknown"
    except:
        return "unknown"

def _parse_clang_tidy_output_optimized(stdout: str, stderr: str, file_path: str) -> List[Warning]:
    """Optimized parser for clang-tidy output."""
    warnings = []
    
    # Parse both stdout and stderr for warnings
    output = stdout + "\n" + stderr
    
    for line in output.split('\n'):
        if 'warning:' in line and file_path in line:
            # Basic parsing - would be more sophisticated in production
            parts = line.split(':')
            if len(parts) >= 5:
                try:
                    warning = Warning(
                        type=parts[-1].strip().split('[')[-1].rstrip(']') if '[' in parts[-1] else "unknown",
                        message=':'.join(parts[3:-1]).strip() if len(parts) > 4 else line,
                        file=file_path,
                        line=int(parts[1]) if parts[1].isdigit() else 0,
                        column=int(parts[2]) if parts[2].isdigit() else 0,
                        severity="warning"
                    )
                    warnings.append(warning)
                except:
                    continue
    
    return warnings

# Export optimized functions
__all__ = [
    'analyze_code_with_clang_tidy_optimized',
    'batch_analyze_files',
    'explain_warning_with_ai',
    'PerformanceMonitor',
    'circuit_breaker',
    'cache_analysis_result'
]