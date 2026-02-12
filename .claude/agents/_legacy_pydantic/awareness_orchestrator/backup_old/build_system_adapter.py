"""
Build System Adapter - Advanced CMake and GoogleTest Integration
Provides comprehensive build system integration with CLion compatibility.
"""

import asyncio
import re
import os
import glob
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from shutil import which


@dataclass
class BuildResult:
    """Result from build execution."""
    success: bool
    duration: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    target: str = ""
    parallel_jobs: int = 0


@dataclass
class TestResult:
    """Result from test execution."""
    success: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration: float = 0.0
    failed_test_names: List[str] = field(default_factory=list)
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass
class CommandResult:
    """Result from command execution."""
    returncode: int
    stdout: str
    stderr: str
    duration: float
    command: List[str]


class BuildSystemAdapter:
    """
    Advanced build system integration with CLion compatibility.

    Features:
    - Automatic CMake detection (CLion or system)
    - Parallel compilation with CPU count detection
    - Comprehensive warning/error parsing
    - GoogleTest result parsing with detailed output
    - Test filtering support
    - Real-time output streaming capability
    """

    def __init__(
        self,
        project_root: Path,
        build_dir: Path,
        cmake_path: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.build_dir = Path(build_dir)
        self.cmake_path = cmake_path or self._find_cmake()
        self.cpu_count = os.cpu_count() or 4

    def _find_cmake(self) -> str:
        """
        Find CMake binary with CLion priority.

        Priority order:
        1. CLion's CMake (most compatible)
        2. System cmake in PATH
        3. Standard locations
        4. Fallback to "cmake"
        """
        candidates = [
            # CLion's CMake (glob pattern)
            str(Path.home() / ".jbdevcontainer/JetBrains/RemoteDev/dist/*/bin/cmake/linux/x64/bin/cmake"),
            # System cmake
            "cmake",
            "/usr/bin/cmake",
            "/usr/local/bin/cmake"
        ]

        for candidate in candidates:
            if "*" in candidate:
                # Handle glob patterns (CLion path)
                matches = glob.glob(candidate)
                if matches:
                    # Use the first match (usually the latest version)
                    return matches[0]
            else:
                # Check if binary exists in PATH
                if which(candidate):
                    return candidate
                # Check absolute path
                elif Path(candidate).exists():
                    return candidate

        # Fallback
        return "cmake"

    async def build_target(
        self,
        target: str = "wire_ground_tests",
        parallel: bool = True,
        verbose: bool = False
    ) -> BuildResult:
        """
        Build specific target with parallel compilation.

        Args:
            target: CMake target to build
            parallel: Enable parallel compilation
            verbose: Enable verbose build output

        Returns:
            BuildResult with comprehensive build information
        """
        start_time = datetime.now()

        # Build command
        cmd = [
            self.cmake_path,
            "--build",
            str(self.build_dir),
            "--target",
            target
        ]

        # Add verbose flag if requested
        if verbose:
            cmd.append("--verbose")

        # Add parallel compilation
        if parallel:
            cmd.extend(["--", "-j", str(self.cpu_count)])

        # Execute build
        result = await self._run_command(cmd)

        duration = (datetime.now() - start_time).total_seconds()

        # Parse output
        combined_output = result.stdout + result.stderr
        warnings = self._parse_warnings(combined_output)
        errors = self._parse_errors(combined_output)

        # Determine success
        success = (
            result.returncode == 0 and
            f"Built target {target}" in combined_output
        )

        return BuildResult(
            success=success,
            duration=duration,
            warnings=warnings,
            errors=errors,
            stdout=result.stdout,
            stderr=result.stderr,
            target=target,
            parallel_jobs=self.cpu_count if parallel else 1
        )

    async def run_tests(
        self,
        test_binary: str = "wire_ground_tests",
        test_filter: Optional[str] = None,
        verbose: bool = True,
        color: bool = True
    ) -> TestResult:
        """
        Run GoogleTest suite with optional filtering.

        Args:
            test_binary: Name of test executable
            test_filter: GoogleTest filter pattern (e.g., "SafetyTestSuite.*")
            verbose: Enable verbose test output
            color: Enable colored output

        Returns:
            TestResult with detailed test information
        """
        start_time = datetime.now()

        # Find test binary
        test_path = self.build_dir / "tests" / test_binary
        if not test_path.exists():
            test_path = self.build_dir / test_binary

        if not test_path.exists():
            return TestResult(
                success=False,
                duration=0.0,
                stderr=f"Test binary not found: {test_binary}"
            )

        # Build command
        cmd = [str(test_path)]

        if test_filter:
            cmd.append(f"--gtest_filter={test_filter}")

        if color:
            cmd.append("--gtest_color=yes")

        if verbose:
            cmd.append("--gtest_print_time=1")

        # Execute tests
        result = await self._run_command(cmd)

        duration = (datetime.now() - start_time).total_seconds()

        # Parse GoogleTest output
        total, passed, failed, skipped, failed_names, details = self._parse_gtest_output(
            result.stdout
        )

        return TestResult(
            success=result.returncode == 0,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            duration=duration,
            failed_test_names=failed_names,
            test_details=details,
            stdout=result.stdout,
            stderr=result.stderr
        )

    async def run_specific_test(
        self,
        test_binary: str,
        test_name: str
    ) -> TestResult:
        """
        Run a specific test by exact name.

        Args:
            test_binary: Name of test executable
            test_name: Exact test name (e.g., "SafetyTestSuite.MemorySafety")

        Returns:
            TestResult for the specific test
        """
        return await self.run_tests(
            test_binary=test_binary,
            test_filter=test_name,
            verbose=True
        )

    async def list_tests(
        self,
        test_binary: str = "wire_ground_tests"
    ) -> List[str]:
        """
        List all available tests in a test binary.

        Args:
            test_binary: Name of test executable

        Returns:
            List of test names
        """
        test_path = self.build_dir / "tests" / test_binary
        if not test_path.exists():
            test_path = self.build_dir / test_binary

        if not test_path.exists():
            return []

        cmd = [str(test_path), "--gtest_list_tests"]
        result = await self._run_command(cmd)

        if result.returncode != 0:
            return []

        # Parse test list
        tests = []
        current_suite = ""

        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.endswith('.'):
                # Test suite name
                current_suite = line
            elif line.startswith('  '):
                # Test name
                test_name = line.strip()
                tests.append(f"{current_suite}{test_name}")

        return tests

    def _parse_warnings(self, output: str) -> List[str]:
        """
        Parse compiler warnings with improved detection.

        Detects:
        - GCC/Clang warnings
        - CMake warnings
        - Linker warnings
        """
        warnings = []
        lines = output.split('\n')

        for line in lines:
            line_stripped = line.strip()

            # GCC/Clang warning patterns
            if re.search(r'warning:|⚠️', line, re.IGNORECASE):
                warnings.append(line_stripped)

            # CMake warnings
            elif re.search(r'CMake Warning', line):
                warnings.append(line_stripped)

            # Linker warnings
            elif re.search(r'ld: warning:', line):
                warnings.append(line_stripped)

            # Deprecation warnings
            elif 'deprecated' in line.lower() and 'warning' in line.lower():
                warnings.append(line_stripped)

        return warnings

    def _parse_errors(self, output: str) -> List[str]:
        """
        Parse compiler errors with improved detection.

        Detects:
        - Compilation errors
        - Linker errors
        - CMake errors
        """
        errors = []
        lines = output.split('\n')

        for line in lines:
            line_stripped = line.strip()

            # Skip lines that are warnings
            if 'warning' in line.lower():
                continue

            # Compilation errors
            if re.search(r'error:|❌|fatal error:', line, re.IGNORECASE):
                errors.append(line_stripped)

            # CMake errors
            elif re.search(r'CMake Error', line):
                errors.append(line_stripped)

            # Linker errors
            elif re.search(r'undefined reference|cannot find', line):
                errors.append(line_stripped)

            # Collect error
            elif re.search(r'collect2: error:', line):
                errors.append(line_stripped)

        return errors

    def _parse_gtest_output(
        self,
        output: str
    ) -> Tuple[int, int, int, int, List[str], List[Dict[str, Any]]]:
        """
        Parse GoogleTest output for comprehensive test results.

        Returns:
            (total, passed, failed, skipped, failed_names, details)
        """
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        failed_names = []
        details = []

        lines = output.split('\n')
        current_test = None
        test_output = []

        for line in lines:
            # [==========] Running 99 tests from 1 test suite.
            if match := re.search(r'\[==========\] Running (\d+) tests', line):
                total = int(match.group(1))

            # [  PASSED  ] 99 tests.
            elif match := re.search(r'\[  PASSED  \]\s+(\d+) tests', line):
                passed = int(match.group(1))

            # [  FAILED  ] 3 tests
            elif match := re.search(r'\[  FAILED  \]\s+(\d+) tests', line):
                failed = int(match.group(1))

            # [ RUN      ] TestSuite.TestName
            elif match := re.search(r'\[ RUN      \]\s+(\S+)', line):
                if current_test:
                    # Save previous test details
                    details.append({
                        "name": current_test,
                        "status": "running",
                        "output": '\n'.join(test_output)
                    })
                current_test = match.group(1)
                test_output = []

            # [       OK ] TestSuite.TestName (0 ms)
            elif match := re.search(r'\[       OK \]\s+(\S+)\s+\((\d+) ms\)', line):
                test_name = match.group(1)
                duration_ms = int(match.group(2))
                details.append({
                    "name": test_name,
                    "status": "passed",
                    "duration_ms": duration_ms,
                    "output": '\n'.join(test_output)
                })
                current_test = None
                test_output = []

            # [  FAILED  ] TestSuite.TestName (0 ms)
            elif match := re.search(r'\[  FAILED  \]\s+(\S+)\s+\((\d+) ms\)', line):
                test_name = match.group(1)
                duration_ms = int(match.group(2))
                failed_names.append(test_name)
                details.append({
                    "name": test_name,
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "output": '\n'.join(test_output)
                })
                current_test = None
                test_output = []

            # [ DISABLED ] TestSuite.TestName
            elif match := re.search(r'\[ DISABLED \]\s+(\S+)', line):
                test_name = match.group(1)
                skipped += 1
                details.append({
                    "name": test_name,
                    "status": "skipped",
                    "output": ""
                })

            # Collect test output
            elif current_test:
                test_output.append(line)

        # If total not found, calculate from passed + failed
        if total == 0:
            total = passed + failed + skipped

        return total, passed, failed, skipped, failed_names, details

    async def _run_command(self, cmd: List[str]) -> CommandResult:
        """Execute command and capture output."""
        start_time = datetime.now()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )

            stdout, stderr = await process.communicate()
            duration = (datetime.now() - start_time).total_seconds()

            return CommandResult(
                returncode=process.returncode or 0,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                duration=duration,
                command=cmd
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                command=cmd
            )

    def get_build_info(self) -> Dict[str, Any]:
        """Get build system information."""
        return {
            "project_root": str(self.project_root),
            "build_dir": str(self.build_dir),
            "cmake_path": self.cmake_path,
            "cpu_count": self.cpu_count,
            "cmake_version": self._get_cmake_version(),
            "build_dir_exists": self.build_dir.exists()
        }

    def _get_cmake_version(self) -> str:
        """Get CMake version."""
        try:
            import subprocess
            result = subprocess.run(
                [self.cmake_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                first_line = result.stdout.split('\n')[0]
                if match := re.search(r'cmake version ([\d.]+)', first_line):
                    return match.group(1)
        except:
            pass
        return "unknown"


async def main():
    """Test build system adapter."""
    print("=" * 80)
    print("Build System Adapter - Test")
    print("=" * 80)

    # Initialize adapter
    project_root = Path("/IdeaProjects/wire_ground")
    build_dir = project_root / "cmake-build-debug"

    adapter = BuildSystemAdapter(project_root, build_dir)

    # Show build info
    info = adapter.get_build_info()
    print(f"\n📋 Build System Info:")
    print(f"   Project: {info['project_root']}")
    print(f"   Build Dir: {info['build_dir']}")
    print(f"   CMake: {info['cmake_path']}")
    print(f"   CMake Version: {info['cmake_version']}")
    print(f"   CPU Cores: {info['cpu_count']}")
    print(f"   Build Dir Exists: {info['build_dir_exists']}")

    # List available tests
    print(f"\n📝 Listing Available Tests...")
    tests = await adapter.list_tests()
    if tests:
        print(f"   Found {len(tests)} tests:")
        for test in tests[:10]:  # Show first 10
            print(f"   - {test}")
        if len(tests) > 10:
            print(f"   ... and {len(tests) - 10} more")
    else:
        print(f"   No tests found or test binary doesn't exist")

    # Build target
    print(f"\n🔨 Building wire_ground_tests...")
    build_result = await adapter.build_target(
        target="wire_ground_tests",
        parallel=True,
        verbose=False
    )

    print(f"   Status: {'✅ SUCCESS' if build_result.success else '❌ FAILED'}")
    print(f"   Duration: {build_result.duration:.1f}s")
    print(f"   Parallel Jobs: {build_result.parallel_jobs}")
    print(f"   Warnings: {len(build_result.warnings)}")
    print(f"   Errors: {len(build_result.errors)}")

    if build_result.errors:
        print(f"\n❌ Build Errors:")
        for error in build_result.errors[:5]:
            print(f"   - {error}")

    # Run tests if build succeeded
    if build_result.success:
        print(f"\n🧪 Running Tests...")
        test_result = await adapter.run_tests(
            test_filter="SafetyTestSuite.*",
            verbose=True
        )

        print(f"   Status: {'✅ SUCCESS' if test_result.success else '❌ FAILED'}")
        print(f"   Duration: {test_result.duration:.1f}s")
        print(f"   Total Tests: {test_result.total_tests}")
        print(f"   Passed: {test_result.passed_tests}")
        print(f"   Failed: {test_result.failed_tests}")
        print(f"   Skipped: {test_result.skipped_tests}")

        if test_result.failed_test_names:
            print(f"\n❌ Failed Tests:")
            for test_name in test_result.failed_test_names[:5]:
                print(f"   - {test_name}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())