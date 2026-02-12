"""Dependencies and context management for the Blitzfire Code Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING
import hashlib
import re
import requests
from pathlib import Path

# Optional docker import with graceful fallback
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

if TYPE_CHECKING:
    from docker import DockerClient

from .settings import BlitzfireSettings
from .models import Architecture, OptimizationMode, SafetyLevel


@dataclass
class BlitzfireDependencies:
    """Dependencies for Blitzfire agent execution."""

    # Configuration
    settings: BlitzfireSettings
    session_id: str

    # External service clients
    godbolt_session: requests.Session
    docker_client: Optional["DockerClient"] = None

    # Analysis context
    target_architecture: Architecture = Architecture.X86_64
    optimization_mode: OptimizationMode = OptimizationMode.GENERAL
    safety_level: SafetyLevel = SafetyLevel.HIGH

    # Caching
    analysis_cache: Dict[str, Any] = None
    benchmark_cache: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize caches if not provided."""
        if self.analysis_cache is None:
            self.analysis_cache = {}
        if self.benchmark_cache is None:
            self.benchmark_cache = {}

    @classmethod
    def create(cls, settings: BlitzfireSettings, session_id: str = "default") -> "BlitzfireDependencies":
        """Create dependencies with proper service initialization."""

        # Initialize Godbolt session
        godbolt_session = requests.Session()
        godbolt_session.timeout = settings.godbolt_timeout
        godbolt_session.headers.update({
            "User-Agent": "Blitzfire-Code-Agent/1.0",
            "Accept": "application/json"
        })

        # Initialize Docker client if enabled and available
        docker_client = None
        if settings.docker_enabled and DOCKER_AVAILABLE and docker is not None:
            try:
                docker_client = docker.from_env(timeout=settings.docker_timeout)
                # Test Docker connectivity
                docker_client.ping()
            except Exception:
                # Graceful fallback if Docker unavailable
                docker_client = None

        return cls(
            settings=settings,
            session_id=session_id,
            godbolt_session=godbolt_session,
            docker_client=docker_client,
        )

    def get_code_hash(self, code: str) -> str:
        """Generate hash of code for caching purposes."""
        return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]

    def is_docker_available(self) -> bool:
        """Check if Docker is available for benchmarking."""
        return self.docker_client is not None


class CodeAnalyzer:
    """Static code analysis utilities."""

    # Regex patterns for common performance issues
    PERFORMANCE_PATTERNS = {
        "string_concatenation_loop": re.compile(r'for\s*\([^}]+\)\s*{[^}]*\w+\s*\+=\s*["\'][^"\']*["\']'),
        "inefficient_vector_growth": re.compile(r'vector\w*\.push_back\s*\([^)]+\)'),
        "unnecessary_copying": re.compile(r'(\w+)\s*=\s*(\w+)\s*;.*\2(?![\w\[\]])'),
        "memory_allocation_loop": re.compile(r'for\s*\([^}]+\)\s*{[^}]*new\s+\w+'),
        "division_by_constant": re.compile(r'\w+\s*/\s*(\d+)'),
        "expensive_math_functions": re.compile(r'(sin|cos|tan|exp|log|sqrt|pow)\s*\('),
        "nested_loops": re.compile(r'for\s*\([^}]+\)\s*{[^}]*for\s*\([^}]+\)\s*{'),
        "inefficient_find": re.compile(r'\.find\s*\([^)]+\)\s*!=\s*\w+\.end\(\)'),
        "missing_const_ref": re.compile(r'(\w+)\s+(\w+)\s*\([^)]*(\w+)\s+(\w+)[^)]*\)'),
        "unnecessary_temporary": re.compile(r'(\w+)\s*\(\s*(\w+)\s*\+\s*(\w+)\s*\)')
    }

    @staticmethod
    def estimate_complexity(code: str) -> tuple[str, str, int]:
        """Estimate time/space complexity and loop nesting depth."""
        # Count nested loops for time complexity estimation
        loop_patterns = [
            re.compile(r'for\s*\([^}]+\)'),
            re.compile(r'while\s*\([^}]+\)'),
            re.compile(r'do\s*{[^}]*}\s*while')
        ]

        lines = code.split('\n')
        max_nesting = 0
        current_nesting = 0

        for line in lines:
            line = line.strip()
            # Count loop starts
            for pattern in loop_patterns:
                if pattern.search(line):
                    current_nesting += 1
                    max_nesting = max(max_nesting, current_nesting)

            # Count closing braces (approximate)
            if '}' in line:
                current_nesting = max(0, current_nesting - line.count('}'))

        # Estimate complexity based on nesting
        if max_nesting == 0:
            time_complexity = "O(1)"
        elif max_nesting == 1:
            time_complexity = "O(n)"
        elif max_nesting == 2:
            time_complexity = "O(n²)"
        elif max_nesting == 3:
            time_complexity = "O(n³)"
        else:
            time_complexity = f"O(n^{max_nesting})"

        # Simple space complexity estimation
        if re.search(r'vector|array|malloc|new', code):
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

        return time_complexity, space_complexity, max_nesting

    @staticmethod
    def find_hotspots(code: str) -> list[int]:
        """Find line numbers that are likely performance hotspots."""
        lines = code.split('\n')
        hotspots = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            # Check for performance-critical patterns
            if any(pattern.search(line) for pattern in CodeAnalyzer.PERFORMANCE_PATTERNS.values()):
                hotspots.append(i)

            # Additional hotspot indicators
            if any(keyword in line for keyword in ['malloc', 'calloc', 'new', 'delete']):
                hotspots.append(i)
            if re.search(r'std::(sort|find|copy|transform)', line):
                hotspots.append(i)

        return hotspots

    @staticmethod
    def detect_optimization_candidates(code: str) -> list[str]:
        """Detect specific optimization opportunities."""
        candidates = []

        # Check each pattern and suggest optimizations
        for pattern_name, pattern in CodeAnalyzer.PERFORMANCE_PATTERNS.items():
            if pattern.search(code):
                if pattern_name == "string_concatenation_loop":
                    candidates.append("Use stringstream for string concatenation in loops")
                elif pattern_name == "inefficient_vector_growth":
                    candidates.append("Reserve vector capacity before push_back operations")
                elif pattern_name == "nested_loops":
                    candidates.append("Consider loop interchange or blocking for cache efficiency")
                elif pattern_name == "division_by_constant":
                    candidates.append("Replace division by multiplication with reciprocal")
                elif pattern_name == "expensive_math_functions":
                    candidates.append("Consider lookup tables or approximations for math functions")

        # Additional candidates based on code analysis
        if re.search(r'#include\s+<algorithm>', code):
            candidates.append("Leverage STL algorithm optimizations and parallel execution")

        if re.search(r'float|double', code):
            candidates.append("Consider SIMD vectorization for floating-point operations")

        return candidates


class HFTAnalyzer:
    """Specialized analyzer for high-frequency trading code patterns."""

    HFT_RISK_PATTERNS = {
        "integer_overflow": re.compile(r'(\w+\s*[+\-*]\s*\w+)|(\+\+\w+)|(\w+\+\+)'),
        "unchecked_cast": re.compile(r'static_cast|reinterpret_cast|const_cast|\(\s*\w+\s*\)'),
        "non_atomic_shared": re.compile(r'(?<!atomic)\s+\w+\s*=\s*\w+.*(?=;)'),
        "mutex_in_hotpath": re.compile(r'mutex|lock_guard|unique_lock'),
        "exception_handling": re.compile(r'throw|try\s*{|catch\s*\('),
        "dynamic_allocation": re.compile(r'new\s+\w+|malloc|calloc|realloc'),
        "unbounded_loop": re.compile(r'while\s*\(\s*true\s*\)|for\s*\(\s*;\s*;\s*\)'),
        "floating_point_comparison": re.compile(r'==\s*[\d.]+f?|!=\s*[\d.]+f?')
    }

    @staticmethod
    def audit_hft_risks(code: str) -> Dict[str, list]:
        """Audit code for HFT-specific risks."""
        risks = {
            "overflow_risks": [],
            "race_conditions": [],
            "determinism_issues": [],
            "performance_risks": []
        }

        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check for overflow risks
            if HFTAnalyzer.HFT_RISK_PATTERNS["integer_overflow"].search(line_stripped):
                risks["overflow_risks"].append(f"Line {i}: Potential integer overflow")

            # Check for race conditions
            if HFTAnalyzer.HFT_RISK_PATTERNS["non_atomic_shared"].search(line_stripped):
                risks["race_conditions"].append(f"Line {i}: Non-atomic operation on shared data")

            # Check for determinism issues
            if HFTAnalyzer.HFT_RISK_PATTERNS["floating_point_comparison"].search(line_stripped):
                risks["determinism_issues"].append(f"Line {i}: Floating-point equality comparison")

            # Check for performance risks
            if HFTAnalyzer.HFT_RISK_PATTERNS["mutex_in_hotpath"].search(line_stripped):
                risks["performance_risks"].append(f"Line {i}: Blocking synchronization in hot path")

        return risks