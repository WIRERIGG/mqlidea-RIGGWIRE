"""Godbolt Compiler Explorer integration for assembly validation."""

import json
import requests
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .models import AssemblyComparison
from .settings import BlitzfireSettings


@dataclass
class GodboltCompiler:
    """Represents a Godbolt compiler configuration."""
    id: str
    name: str
    version: str
    language: str
    supported_architectures: List[str]


@dataclass
class AssemblyResult:
    """Raw assembly result from Godbolt."""
    asm: List[Dict[str, Any]]
    stdout: List[Dict[str, str]]
    stderr: List[Dict[str, str]]
    code: int
    okToCache: bool
    execTime: Optional[str] = None


class GodboltClient:
    """Client for interacting with Godbolt Compiler Explorer API."""

    def __init__(self, settings: BlitzfireSettings):
        """Initialize Godbolt client with settings."""
        self.base_url = settings.godbolt_base_url
        self.timeout = settings.godbolt_timeout
        self.cache_ttl = settings.godbolt_cache_ttl

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Blitzfire-Code-Agent/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        # Simple in-memory cache (would use Redis/etc in production)
        self._cache: Dict[str, Tuple[AssemblyResult, float]] = {}

    def _get_cache_key(self, code: str, compiler: str, options: str, architecture: str) -> str:
        """Generate cache key for assembly request."""
        combined = f"{code}{compiler}{options}{architecture}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached result is still valid."""
        return (time.time() - timestamp) < self.cache_ttl

    def get_available_compilers(self, language: str = "c++") -> List[GodboltCompiler]:
        """Get list of available compilers for the language."""
        try:
            url = f"{self.base_url}/api/compilers/{language}"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            compilers = []
            for comp_data in response.json():
                compilers.append(GodboltCompiler(
                    id=comp_data.get("id", ""),
                    name=comp_data.get("name", ""),
                    version=comp_data.get("version", ""),
                    language=language,
                    supported_architectures=comp_data.get("supportedArch", ["x86_64"])
                ))

            return compilers

        except requests.RequestException as e:
            print(f"Failed to get compilers: {e}")
            return []

    def compile_code(
        self,
        code: str,
        compiler: str = "clang_trunk",
        options: str = "-O3",
        architecture: str = "x86_64",
        use_cache: bool = True
    ) -> Optional[AssemblyResult]:
        """
        Compile code and get assembly output.

        Args:
            code: C++ source code to compile
            compiler: Compiler ID (e.g., 'clang_trunk', 'gcc_trunk')
            options: Compiler options (e.g., '-O3 -march=native')
            architecture: Target architecture
            use_cache: Whether to use caching

        Returns:
            AssemblyResult with compilation output, or None if failed
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(code, compiler, options, architecture)
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                if self._is_cache_valid(timestamp):
                    return result

        try:
            # Prepare compilation request
            url = f"{self.base_url}/api/compiler/{compiler}/compile"

            payload = {
                "source": code,
                "options": {
                    "userArguments": options,
                    "compilerOptions": {
                        "executorRequest": False
                    },
                    "filters": {
                        "binary": False,
                        "binaryObject": False,
                        "execute": False,
                        "intel": True,  # Use Intel syntax
                        "demangle": True,
                        "labels": True,
                        "libraryCode": False,
                        "directives": True,
                        "commentOnly": False,
                        "trim": True
                    },
                    "tools": [],
                    "libraries": []
                },
                "lang": "c++",
                "allowStoreCodeDebug": True
            }

            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result_data = response.json()

            # Parse response into AssemblyResult
            assembly_result = AssemblyResult(
                asm=result_data.get("asm", []),
                stdout=result_data.get("stdout", []),
                stderr=result_data.get("stderr", []),
                code=result_data.get("code", -1),
                okToCache=result_data.get("okToCache", False),
                execTime=result_data.get("execTime")
            )

            # Cache successful results
            if use_cache and assembly_result.okToCache:
                cache_key = self._get_cache_key(code, compiler, options, architecture)
                self._cache[cache_key] = (assembly_result, time.time())

            return assembly_result

        except requests.RequestException as e:
            print(f"Godbolt compilation failed: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Failed to parse Godbolt response: {e}")
            return None

    def compare_assembly(
        self,
        original_code: str,
        optimized_code: str,
        compiler: str = "clang_trunk",
        options: str = "-O3",
        architecture: str = "x86_64"
    ) -> Optional[AssemblyComparison]:
        """
        Compare assembly output between two code versions.

        Args:
            original_code: Baseline C++ code
            optimized_code: Optimized C++ code
            compiler: Compiler to use
            options: Compiler options
            architecture: Target architecture

        Returns:
            AssemblyComparison with analysis results
        """
        # Compile both versions
        original_asm = self.compile_code(original_code, compiler, options, architecture)
        optimized_asm = self.compile_code(optimized_code, compiler, options, architecture)

        if not original_asm or not optimized_asm:
            return None

        # Check for compilation errors
        if original_asm.code != 0 or optimized_asm.code != 0:
            print("Compilation errors detected")
            return None

        # Analyze assembly differences
        return self._analyze_assembly_differences(original_asm, optimized_asm)

    def _analyze_assembly_differences(
        self,
        original: AssemblyResult,
        optimized: AssemblyResult
    ) -> AssemblyComparison:
        """Analyze differences between two assembly results."""

        # Extract instruction counts
        original_instructions = len([line for line in original.asm if line.get("text", "").strip()])
        optimized_instructions = len([line for line in optimized.asm if line.get("text", "").strip()])

        # Look for optimization artifacts
        original_text = " ".join(line.get("text", "") for line in original.asm)
        optimized_text = " ".join(line.get("text", "") for line in optimized.asm)

        vectorization_detected = self._detect_vectorization(optimized_text, original_text)
        loop_unrolling_detected = self._detect_loop_unrolling(optimized_text, original_text)

        key_differences = []
        optimization_artifacts = []

        # Instruction count changes
        if optimized_instructions < original_instructions:
            reduction = original_instructions - optimized_instructions
            percentage = (reduction / original_instructions) * 100
            key_differences.append(f"Reduced instruction count by {reduction} ({percentage:.1f}%)")
            optimization_artifacts.append("Code size optimization")

        elif optimized_instructions > original_instructions:
            increase = optimized_instructions - original_instructions
            percentage = (increase / original_instructions) * 100
            key_differences.append(f"Increased instruction count by {increase} ({percentage:.1f}%) - likely from unrolling")

        # Vectorization detection
        if vectorization_detected:
            key_differences.append("SIMD vectorization detected")
            optimization_artifacts.append("Vector instructions (SSE/AVX)")

        # Loop unrolling detection
        if loop_unrolling_detected:
            key_differences.append("Loop unrolling applied")
            optimization_artifacts.append("Unrolled loop structure")

        # Function inlining detection
        if self._detect_inlining(optimized_text, original_text):
            key_differences.append("Function inlining detected")
            optimization_artifacts.append("Inlined function calls")

        # Memory access pattern improvements
        if self._detect_memory_optimization(optimized_text, original_text):
            key_differences.append("Optimized memory access patterns")
            optimization_artifacts.append("Memory access optimization")

        # Register usage improvements
        if self._detect_register_optimization(optimized_text, original_text):
            key_differences.append("Improved register utilization")
            optimization_artifacts.append("Register allocation optimization")

        return AssemblyComparison(
            original_instructions=original_instructions,
            optimized_instructions=optimized_instructions,
            vectorization_detected=vectorization_detected,
            loop_unrolling_detected=loop_unrolling_detected,
            key_differences=key_differences,
            optimization_artifacts=optimization_artifacts
        )

    def _detect_vectorization(self, optimized_text: str, original_text: str) -> bool:
        """Detect SIMD vectorization in assembly."""
        vector_instructions = [
            "movups", "movaps", "addps", "mulps", "subps", "divps",  # SSE
            "vmovups", "vmovaps", "vaddps", "vmulps", "vsubps", "vdivps",  # AVX
            "vfmadd", "vfmsub", "vfnmadd", "vfnmsub",  # FMA
            "vmovupd", "vmovapd", "vaddpd", "vmulpd",  # Double precision
            "vpcmpeq", "vpcmpgt", "vpand", "vpor", "vpxor",  # Integer SIMD
        ]

        optimized_vector_count = sum(1 for instr in vector_instructions if instr in optimized_text.lower())
        original_vector_count = sum(1 for instr in vector_instructions if instr in original_text.lower())

        return optimized_vector_count > original_vector_count

    def _detect_loop_unrolling(self, optimized_text: str, original_text: str) -> bool:
        """Detect loop unrolling in assembly."""
        # Look for repeated instruction patterns (simple heuristic)
        optimized_lines = optimized_text.split('\n')
        original_lines = original_text.split('\n')

        # Loop unrolling typically increases code size with repeated patterns
        return len(optimized_lines) > len(original_lines) * 1.2

    def _detect_inlining(self, optimized_text: str, original_text: str) -> bool:
        """Detect function inlining."""
        # Count call instructions
        optimized_calls = optimized_text.lower().count("call")
        original_calls = original_text.lower().count("call")

        return optimized_calls < original_calls

    def _detect_memory_optimization(self, optimized_text: str, original_text: str) -> bool:
        """Detect memory access optimizations."""
        # Look for reduced memory access instructions
        memory_instructions = ["mov", "load", "store", "push", "pop"]

        optimized_memory_count = sum(optimized_text.lower().count(instr) for instr in memory_instructions)
        original_memory_count = sum(original_text.lower().count(instr) for instr in memory_instructions)

        return optimized_memory_count < original_memory_count * 0.9

    def _detect_register_optimization(self, optimized_text: str, original_text: str) -> bool:
        """Detect register allocation improvements."""
        # Look for reduced stack operations (spills)
        stack_operations = ["push", "pop", "[rsp", "[rbp"]

        optimized_stack_count = sum(optimized_text.lower().count(op) for op in stack_operations)
        original_stack_count = sum(original_text.lower().count(op) for op in stack_operations)

        return optimized_stack_count < original_stack_count

    def get_assembly_diff(self, comparison: AssemblyComparison) -> str:
        """Generate a human-readable assembly diff summary."""
        diff_lines = [
            f"Assembly Comparison Summary:",
            f"Original: {comparison.original_instructions} instructions",
            f"Optimized: {comparison.optimized_instructions} instructions",
            ""
        ]

        if comparison.key_differences:
            diff_lines.append("Key Differences:")
            for diff in comparison.key_differences:
                diff_lines.append(f"  • {diff}")
            diff_lines.append("")

        if comparison.optimization_artifacts:
            diff_lines.append("Optimization Artifacts Detected:")
            for artifact in comparison.optimization_artifacts:
                diff_lines.append(f"  • {artifact}")
            diff_lines.append("")

        if comparison.vectorization_detected:
            diff_lines.append("🚀 SIMD vectorization successfully applied!")

        if comparison.loop_unrolling_detected:
            diff_lines.append("⚡ Loop unrolling optimization detected!")

        return "\n".join(diff_lines)


def create_godbolt_client(settings: BlitzfireSettings = None) -> GodboltClient:
    """Create a Godbolt client with default settings."""
    if settings is None:
        from .settings import settings as default_settings
        settings = default_settings

    return GodboltClient(settings)