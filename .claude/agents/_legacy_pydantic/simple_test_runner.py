#!/usr/bin/env python3
"""
Simple Test Runner for Pydantic AI Agents
Tests basic functionality without heavy dependencies
"""

import os
import sys
import asyncio
import traceback
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class SimpleTestRunner:
    """Simple test runner for basic agent validation."""

    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    async def test_agent_imports(self, agent_name: str, agent_dir: Path) -> Dict[str, Any]:
        """Test if agent modules can be imported."""
        self.log(f"Testing imports for {agent_name}")

        result = {
            'agent': agent_name,
            'import_tests': {},
            'structure_tests': {},
            'basic_functionality': {},
            'status': 'unknown'
        }

        # Test core module imports
        test_modules = ['agent', 'models', 'tools', 'dependencies']

        for module in test_modules:
            module_path = agent_dir / f"{module}.py"
            try:
                if module_path.exists():
                    # Try to import the module
                    sys.path.insert(0, str(agent_dir))
                    __import__(module)
                    result['import_tests'][module] = 'PASS'
                    self.passed_tests += 1
                else:
                    result['import_tests'][module] = 'MISSING'
                    self.failed_tests += 1
                self.total_tests += 1
            except Exception as e:
                result['import_tests'][module] = f'FAIL: {str(e)}'
                self.failed_tests += 1
                self.total_tests += 1
            finally:
                if str(agent_dir) in sys.path:
                    sys.path.remove(str(agent_dir))

        # Test directory structure
        expected_dirs = ['tests', '__pycache__']
        for dir_name in expected_dirs:
            dir_path = agent_dir / dir_name
            if dir_path.exists():
                result['structure_tests'][dir_name] = 'PRESENT'
            else:
                result['structure_tests'][dir_name] = 'MISSING'

        # Test our deep probe files exist
        deep_probe_file = agent_dir / 'tests' / 'test_deep_probe.py'
        if deep_probe_file.exists():
            result['structure_tests']['deep_probe_tests'] = 'PRESENT'
            # Count test functions in the file
            with open(deep_probe_file, 'r') as f:
                content = f.read()
                test_function_count = content.count('def test_')
                async_test_count = content.count('@pytest.mark.asyncio')
                result['basic_functionality']['test_functions'] = test_function_count
                result['basic_functionality']['async_tests'] = async_test_count
        else:
            result['structure_tests']['deep_probe_tests'] = 'MISSING'

        # Determine overall status
        import_failures = sum(1 for status in result['import_tests'].values() if 'FAIL' in status)
        if import_failures == 0:
            result['status'] = 'READY'
        elif import_failures <= 1:
            result['status'] = 'NEEDS_FIXES'
        else:
            result['status'] = 'BROKEN'

        return result

    async def test_agent_syntax(self, agent_name: str, agent_dir: Path) -> Dict[str, Any]:
        """Test Python syntax validity of agent files."""
        self.log(f"Testing syntax for {agent_name}")

        result = {
            'agent': agent_name,
            'syntax_tests': {},
            'line_counts': {},
            'complexity': {}
        }

        # Get all Python files
        python_files = list(agent_dir.glob('**/*.py'))

        for py_file in python_files:
            rel_path = py_file.relative_to(agent_dir)
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Test syntax by compiling
                compile(content, str(py_file), 'exec')
                result['syntax_tests'][str(rel_path)] = 'VALID'

                # Count lines and complexity indicators
                lines = content.split('\n')
                result['line_counts'][str(rel_path)] = len(lines)

                # Simple complexity metrics
                result['complexity'][str(rel_path)] = {
                    'functions': content.count('def '),
                    'classes': content.count('class '),
                    'async_functions': content.count('async def '),
                    'imports': content.count('import ') + content.count('from ')
                }

                self.passed_tests += 1
            except SyntaxError as e:
                result['syntax_tests'][str(rel_path)] = f'SYNTAX_ERROR: {e}'
                self.failed_tests += 1
            except Exception as e:
                result['syntax_tests'][str(rel_path)] = f'ERROR: {e}'
                self.failed_tests += 1

            self.total_tests += 1

        return result

    async def test_deep_probe_structure(self, agent_name: str, agent_dir: Path) -> Dict[str, Any]:
        """Test the structure and completeness of deep probe tests."""
        self.log(f"Analyzing deep probe tests for {agent_name}")

        result = {
            'agent': agent_name,
            'probe_categories': {},
            'test_coverage': {},
            'validation_features': {}
        }

        deep_probe_file = agent_dir / 'tests' / 'test_deep_probe.py'

        if not deep_probe_file.exists():
            result['status'] = 'NO_DEEP_PROBES'
            return result

        try:
            with open(deep_probe_file, 'r') as f:
                content = f.read()

            # Analyze probe categories
            probe_patterns = {
                'state_transitions': 'state_transition',
                'failure_injection': 'failure_injection',
                'performance_testing': 'performance',
                'security_probing': 'security',
                'property_testing': '@given',
                'memory_testing': 'memory',
                'concurrency_testing': 'concurrent',
                'isolation_testing': 'isolation'
            }

            for category, pattern in probe_patterns.items():
                if pattern in content:
                    result['probe_categories'][category] = 'IMPLEMENTED'
                    self.passed_tests += 1
                else:
                    result['probe_categories'][category] = 'MISSING'
                    self.failed_tests += 1
                self.total_tests += 1

            # Test coverage analysis
            result['test_coverage'] = {
                'total_test_functions': content.count('def test_'),
                'async_test_functions': content.count('async def test_'),
                'fixture_count': content.count('@pytest.fixture'),
                'hypothesis_tests': content.count('@given'),
                'parametrized_tests': content.count('@pytest.mark.parametrize')
            }

            # Validation features
            validation_features = {
                'probe_logger': 'ProbeLogger' in content,
                'error_recovery': 'error_recovery' in content,
                'fix_generation': 'generate_fix' in content,
                'security_testing': 'security' in content.lower(),
                'performance_metrics': 'performance' in content.lower()
            }

            result['validation_features'] = validation_features

            # Overall assessment
            implemented_probes = sum(1 for status in result['probe_categories'].values()
                                   if status == 'IMPLEMENTED')
            total_probes = len(probe_patterns)

            if implemented_probes >= total_probes * 0.8:
                result['status'] = 'COMPREHENSIVE'
            elif implemented_probes >= total_probes * 0.5:
                result['status'] = 'ADEQUATE'
            else:
                result['status'] = 'INSUFFICIENT'

        except Exception as e:
            result['status'] = f'ERROR: {e}'
            self.failed_tests += 1
            self.total_tests += 1

        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests for all agents."""
        self.log("Starting comprehensive agent validation")

        agents_dir = Path(__file__).parent
        agent_dirs = {
            'clang_tidy_ai_agent': agents_dir / 'clang_tidy_ai_agent',
            'blitzfire_code_agent': agents_dir / 'blitzfire_code_agent',
            'multi_agent_debugging_system': agents_dir / 'multi_agent_debugging_system'
        }

        results = {}

        for agent_name, agent_dir in agent_dirs.items():
            if agent_dir.exists():
                self.log(f"Testing {agent_name}")

                # Run all test categories
                import_result = await self.test_agent_imports(agent_name, agent_dir)
                syntax_result = await self.test_agent_syntax(agent_name, agent_dir)
                probe_result = await self.test_deep_probe_structure(agent_name, agent_dir)

                results[agent_name] = {
                    'imports': import_result,
                    'syntax': syntax_result,
                    'deep_probes': probe_result,
                    'overall_status': self._determine_agent_status(
                        import_result, syntax_result, probe_result
                    )
                }
            else:
                self.log(f"Agent directory not found: {agent_dir}", "ERROR")
                results[agent_name] = {'status': 'NOT_FOUND'}

        return results

    def _determine_agent_status(self, import_result: Dict, syntax_result: Dict,
                              probe_result: Dict) -> str:
        """Determine overall agent status."""

        if import_result['status'] == 'BROKEN':
            return 'CRITICAL_ISSUES'

        syntax_errors = sum(1 for status in syntax_result['syntax_tests'].values()
                           if 'ERROR' in status)

        if syntax_errors > 0:
            return 'SYNTAX_ISSUES'

        if probe_result.get('status') == 'COMPREHENSIVE':
            return 'PRODUCTION_READY'
        elif probe_result.get('status') == 'ADEQUATE':
            return 'NEEDS_ENHANCEMENT'
        else:
            return 'INSUFFICIENT_TESTING'

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate test report."""

        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        report = f"""
# Simple Agent Validation Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test Framework**: Simple Python Validation
**Total Tests**: {self.total_tests}
**Passed**: {self.passed_tests}
**Failed**: {self.failed_tests}
**Success Rate**: {success_rate:.1f}%

## Agent Status Summary

"""

        for agent_name, agent_result in results.items():
            if 'overall_status' in agent_result:
                status = agent_result['overall_status']
                status_icon = {
                    'PRODUCTION_READY': '✅',
                    'NEEDS_ENHANCEMENT': '⚠️',
                    'INSUFFICIENT_TESTING': '❌',
                    'SYNTAX_ISSUES': '🐛',
                    'CRITICAL_ISSUES': '💥'
                }.get(status, '❓')

                report += f"### {agent_name.replace('_', ' ').title()}\n"
                report += f"**Status**: {status_icon} {status}\n\n"

                # Import status
                import_result = agent_result['imports']
                import_passes = sum(1 for s in import_result['import_tests'].values() if s == 'PASS')
                import_total = len(import_result['import_tests'])
                report += f"- **Imports**: {import_passes}/{import_total} modules load successfully\n"

                # Syntax status
                syntax_result = agent_result['syntax']
                syntax_passes = sum(1 for s in syntax_result['syntax_tests'].values() if s == 'VALID')
                syntax_total = len(syntax_result['syntax_tests'])
                report += f"- **Syntax**: {syntax_passes}/{syntax_total} files valid\n"

                # Deep probe status
                probe_result = agent_result['deep_probes']
                if 'probe_categories' in probe_result:
                    probe_passes = sum(1 for s in probe_result['probe_categories'].values()
                                     if s == 'IMPLEMENTED')
                    probe_total = len(probe_result['probe_categories'])
                    report += f"- **Deep Probes**: {probe_passes}/{probe_total} categories implemented\n"

                # Test function counts
                if 'test_coverage' in probe_result:
                    coverage = probe_result['test_coverage']
                    report += f"- **Test Functions**: {coverage.get('total_test_functions', 0)}\n"
                    report += f"- **Async Tests**: {coverage.get('async_test_functions', 0)}\n"
                    report += f"- **Property Tests**: {coverage.get('hypothesis_tests', 0)}\n"

                report += "\n"

        # Detailed findings
        report += "## Detailed Analysis\n\n"

        for agent_name, agent_result in results.items():
            if 'imports' in agent_result:
                report += f"### {agent_name} Import Analysis\n"
                for module, status in agent_result['imports']['import_tests'].items():
                    status_icon = "✅" if status == "PASS" else "❌"
                    report += f"- {status_icon} {module}: {status}\n"
                report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        critical_agents = [name for name, result in results.items()
                          if result.get('overall_status') in ['CRITICAL_ISSUES', 'SYNTAX_ISSUES']]

        if critical_agents:
            report += f"🚨 **CRITICAL**: Fix import/syntax issues in: {', '.join(critical_agents)}\n\n"

        enhancement_agents = [name for name, result in results.items()
                            if result.get('overall_status') == 'NEEDS_ENHANCEMENT']

        if enhancement_agents:
            report += f"⚠️ **ENHANCE**: Improve test coverage in: {', '.join(enhancement_agents)}\n\n"

        ready_agents = [name for name, result in results.items()
                       if result.get('overall_status') == 'PRODUCTION_READY']

        if ready_agents:
            report += f"✅ **READY**: Production ready agents: {', '.join(ready_agents)}\n\n"

        # Overall assessment
        if len(ready_agents) == len(results):
            report += "🎉 **ALL AGENTS READY FOR PRODUCTION TESTING**\n"
        elif len(critical_agents) > 0:
            report += "🔴 **CRITICAL ISSUES MUST BE RESOLVED BEFORE TESTING**\n"
        else:
            report += "🟡 **SOME AGENTS NEED ENHANCEMENT BEFORE PRODUCTION**\n"

        return report


async def main():
    """Main test execution."""
    print("🧪 SIMPLE AGENT VALIDATION SYSTEM")
    print("=" * 50)

    runner = SimpleTestRunner()

    try:
        results = await runner.run_all_tests()

        # Generate report
        report = runner.generate_report(results)

        # Save report
        report_file = Path(__file__).parent / "simple_validation_report.md"
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\n📊 VALIDATION COMPLETE")
        print(f"📁 Report saved: {report_file}")
        print(f"📈 Success Rate: {runner.passed_tests}/{runner.total_tests} ({runner.passed_tests/runner.total_tests*100:.1f}%)")

        # Print summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(report.split("## Agent Status Summary")[1].split("## Detailed Analysis")[0])

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)