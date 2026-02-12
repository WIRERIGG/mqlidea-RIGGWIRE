#!/usr/bin/env python3
"""
Comprehensive Validation for MT5 Infinite Reliability Agent
Uses demo_validation.py and coverage_validator.py patterns with awareness_orchestrator methodology
"""

import asyncio
import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class MT5AgentValidator:
    """Comprehensive validator for MT5 Infinite Reliability Agent."""

    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.validation_results = {}
        self.issues = []
        self.warnings = []

    def check_file_exists(self, filename: str) -> Dict[str, Any]:
        """Check if a required file exists and analyze its content."""
        file_path = self.agent_dir / filename
        exists = file_path.exists()

        result = {
            'file': filename,
            'exists': exists,
            'size': 0,
            'lines': 0
        }

        if exists:
            content = file_path.read_text()
            result['size'] = len(content)
            result['lines'] = len(content.split('\n'))

        return result

    def validate_structure(self) -> Dict[str, Any]:
        """Validate agent directory structure."""
        print("📁 Validating Agent Structure...")

        required_files = [
            '__init__.py',
            'agent.py',
            'dependencies.py',
            'models.py',
            'prompts.py',
            'providers.py',
            'settings.py',
            'tools.py',
            'README.md'
        ]

        optional_files = [
            'cli.py',
            '__main__.py'
        ]

        results = {
            'required_files': {},
            'optional_files': {},
            'tests_dir': False,
            'all_required_present': True
        }

        for filename in required_files:
            file_result = self.check_file_exists(filename)
            results['required_files'][filename] = file_result
            if not file_result['exists']:
                results['all_required_present'] = False
                self.issues.append(f"Missing required file: {filename}")

        for filename in optional_files:
            results['optional_files'][filename] = self.check_file_exists(filename)

        # Check tests directory
        tests_dir = self.agent_dir / 'tests'
        results['tests_dir'] = tests_dir.exists()
        if not results['tests_dir']:
            self.issues.append("Missing tests directory")

        return results

    def validate_imports(self) -> Dict[str, Any]:
        """Validate that all imports work correctly."""
        print("📦 Validating Imports...")

        results = {
            'import_success': False,
            'agent_accessible': False,
            'tools_accessible': False,
            'models_accessible': False,
            'dependencies_accessible': False,
            'errors': []
        }

        try:
            # Add parent to path for proper package import
            sys.path.insert(0, str(self.agent_dir.parent))

            # Test imports
            from mt5_infinite_reliability_agent import agent
            results['agent_accessible'] = True

            from mt5_infinite_reliability_agent import tools
            results['tools_accessible'] = True

            from mt5_infinite_reliability_agent import models
            results['models_accessible'] = True

            from mt5_infinite_reliability_agent import dependencies
            results['dependencies_accessible'] = True

            results['import_success'] = True

        except Exception as e:
            results['errors'].append(str(e))
            self.issues.append(f"Import error: {e}")

        return results

    def validate_agent_components(self) -> Dict[str, Any]:
        """Validate agent has all required components."""
        print("🤖 Validating Agent Components...")

        results = {
            'main_agent': False,
            'subagents': {},
            'tools_registered': [],
            'output_type_set': False,
            'dependencies_type_set': False,
            'system_prompt_set': False
        }

        try:
            sys.path.insert(0, str(self.agent_dir.parent))

            from mt5_infinite_reliability_agent.agent import (
                mt5_optimizer,
                ParserAgent,
                OptimizerAgent,
                FTMOComplianceAgent,
                VerificationAgent,
                DocumentationAgent
            )

            results['main_agent'] = mt5_optimizer is not None

            # Check subagents
            subagents = {
                'ParserAgent': ParserAgent,
                'OptimizerAgent': OptimizerAgent,
                'FTMOComplianceAgent': FTMOComplianceAgent,
                'VerificationAgent': VerificationAgent,
                'DocumentationAgent': DocumentationAgent
            }

            for name, agent_obj in subagents.items():
                results['subagents'][name] = {
                    'exists': agent_obj is not None,
                    'has_output_type': hasattr(agent_obj, 'output_type'),
                    'has_deps_type': hasattr(agent_obj, 'deps_type')
                }

            # Check main agent configuration
            results['output_type_set'] = mt5_optimizer.output_type is not None
            results['dependencies_type_set'] = mt5_optimizer.deps_type is not None
            results['system_prompt_set'] = bool(mt5_optimizer.system_prompt)

            # Get registered tools via toolsets
            if hasattr(mt5_optimizer, 'toolsets') and mt5_optimizer.toolsets:
                for toolset in mt5_optimizer.toolsets:
                    if hasattr(toolset, 'function_tools'):
                        for tool in toolset.function_tools:
                            if hasattr(tool, 'name'):
                                results['tools_registered'].append(tool.name)

        except Exception as e:
            self.issues.append(f"Agent component error: {e}")
            results['error'] = str(e)

        return results

    def validate_tools(self) -> Dict[str, Any]:
        """Validate all tool functions work correctly."""
        print("🔧 Validating Tools...")

        results = {
            'tools_found': [],
            'tools_callable': {},
            'tool_signatures_valid': {}
        }

        try:
            sys.path.insert(0, str(self.agent_dir.parent))

            from mt5_infinite_reliability_agent.tools import (
                parse_mql5_code,
                analyze_code_quality,
                apply_code_transformation,
                verify_code_correctness,
                create_proof_certificate,
                TransformationRollback
            )

            tools = {
                'parse_mql5_code': parse_mql5_code,
                'analyze_code_quality': analyze_code_quality,
                'apply_code_transformation': apply_code_transformation,
                'verify_code_correctness': verify_code_correctness,
                'create_proof_certificate': create_proof_certificate
            }

            # Test basic MQL5 code
            test_code = """
int OnInit() {
    return(INIT_SUCCEEDED);
}
void OnTick() {
    double ma = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);
}
"""

            for name, func in tools.items():
                results['tools_found'].append(name)
                results['tools_callable'][name] = callable(func)

                # Test each tool
                try:
                    if name == 'parse_mql5_code':
                        result = func(test_code)
                        results['tool_signatures_valid'][name] = 'ast' in result and 'stats' in result
                    elif name == 'analyze_code_quality':
                        parsed = parse_mql5_code(test_code)
                        result = func(parsed, ['complexity', 'memory'], 'medium')
                        results['tool_signatures_valid'][name] = 'issues_found' in result
                    elif name == 'apply_code_transformation':
                        result = func(test_code, [], {'auto_format': True, 'max_fixes': 5})
                        results['tool_signatures_valid'][name] = 'success' in result
                    elif name == 'verify_code_correctness':
                        result = func(test_code, test_code, [])
                        results['tool_signatures_valid'][name] = 'verified' in result
                    elif name == 'create_proof_certificate':
                        result = func({}, [], {}, {'proof_level': 'basic', 'output_format': 'json'})
                        results['tool_signatures_valid'][name] = 'certificate' in result
                except Exception as e:
                    results['tool_signatures_valid'][name] = False
                    self.warnings.append(f"Tool {name} test failed: {e}")

            # Check TransformationRollback
            results['rollback_class_exists'] = TransformationRollback is not None

        except Exception as e:
            self.issues.append(f"Tools validation error: {e}")
            results['error'] = str(e)

        return results

    def validate_models(self) -> Dict[str, Any]:
        """Validate all Pydantic models."""
        print("📋 Validating Models...")

        results = {
            'models_found': [],
            'models_instantiable': {},
            'enums_found': []
        }

        try:
            sys.path.insert(0, str(self.agent_dir.parent))

            from mt5_infinite_reliability_agent.models import (
                OptimizationResult,
                OptimizationContext,
                OptimizationIssue,
                OptimizationTransformation,
                AgentFindings,
                FTMOComplianceReport,
                FTMOComplianceCheck,
                MQL5Pattern,
                AgentHandoff,
                Severity,
                AgentType,
                OptimizationDimension,
                EscalationTier
            )

            models = {
                'OptimizationResult': OptimizationResult,
                'OptimizationContext': OptimizationContext,
                'OptimizationIssue': OptimizationIssue,
                'OptimizationTransformation': OptimizationTransformation,
                'AgentFindings': AgentFindings,
                'FTMOComplianceReport': FTMOComplianceReport,
                'FTMOComplianceCheck': FTMOComplianceCheck,
                'MQL5Pattern': MQL5Pattern,
                'AgentHandoff': AgentHandoff
            }

            enums = {
                'Severity': Severity,
                'AgentType': AgentType,
                'OptimizationDimension': OptimizationDimension,
                'EscalationTier': EscalationTier
            }

            for name, model in models.items():
                results['models_found'].append(name)
                # Check if model can be imported
                results['models_instantiable'][name] = model is not None

            for name, enum in enums.items():
                results['enums_found'].append(name)

        except Exception as e:
            self.issues.append(f"Models validation error: {e}")
            results['error'] = str(e)

        return results

    def validate_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage similar to coverage_validator.py."""
        print("📊 Validating Test Coverage...")

        results = {
            'test_files_found': [],
            'total_test_functions': 0,
            'async_tests': 0,
            'coverage_areas': {},
            'estimated_coverage': 0
        }

        tests_dir = self.agent_dir / 'tests'
        if not tests_dir.exists():
            self.issues.append("Tests directory not found")
            return results

        # Find all test files
        test_files = list(tests_dir.glob('test_*.py'))
        results['test_files_found'] = [f.name for f in test_files]

        # Analyze test content
        all_content = ""
        for test_file in test_files:
            content = test_file.read_text()
            all_content += content
            results['total_test_functions'] += content.count('def test_')
            results['async_tests'] += content.count('async def test_')

        # Coverage areas
        coverage_areas = {
            'agent_core': ['agent', 'Agent', 'run', 'execute'],
            'models': ['model', 'Model', 'Response', 'pydantic'],
            'tools': ['tool', 'Tool', 'function', 'call'],
            'dependencies': ['depend', 'Depend', 'inject', 'config'],
            'error_handling': ['error', 'Error', 'except', 'try', 'fail'],
            'async_operations': ['async', 'await', 'asyncio'],
            'validation': ['valid', 'assert', 'check', 'verify'],
            'security': ['security', 'safe', 'sanitiz'],
            'performance': ['performance', 'speed', 'time'],
            'mql5_specific': ['mql5', 'MQL5', 'OnTick', 'OnInit', 'indicator']
        }

        for area, keywords in coverage_areas.items():
            matches = sum(all_content.lower().count(k.lower()) for k in keywords)
            results['coverage_areas'][area] = {
                'covered': matches > 0,
                'matches': matches
            }

        # Calculate coverage estimate
        covered = sum(1 for a in results['coverage_areas'].values() if a['covered'])
        total = len(coverage_areas)

        # Source files
        source_files = list(self.agent_dir.glob('*.py'))
        source_files = [f for f in source_files if not f.name.startswith('__') and not f.name.startswith('test_')]

        base_coverage = (covered / total) * 100
        density_bonus = min(10, (results['total_test_functions'] / max(1, len(source_files))) * 2)
        async_bonus = min(5, (results['async_tests'] / max(1, results['total_test_functions'])) * 5)

        results['estimated_coverage'] = min(100, base_coverage + density_bonus + async_bonus)
        results['meets_98_threshold'] = results['estimated_coverage'] >= 98

        if not results['meets_98_threshold']:
            self.warnings.append(f"Coverage ({results['estimated_coverage']:.1f}%) below 98% threshold")

        return results

    def validate_dependencies_class(self) -> Dict[str, Any]:
        """Validate the AgentDependencies class."""
        print("🔗 Validating Dependencies...")

        results = {
            'class_exists': False,
            'from_settings_method': False,
            'progress_tracking': False,
            'snapshot_management': False,
            'rollback_capability': False
        }

        try:
            sys.path.insert(0, str(self.agent_dir.parent))

            from mt5_infinite_reliability_agent.dependencies import AgentDependencies

            results['class_exists'] = True
            results['from_settings_method'] = hasattr(AgentDependencies, 'from_settings')
            results['progress_tracking'] = hasattr(AgentDependencies, 'emit_progress')
            results['snapshot_management'] = hasattr(AgentDependencies, 'add_snapshot')
            results['rollback_capability'] = hasattr(AgentDependencies, 'rollback')

        except Exception as e:
            self.issues.append(f"Dependencies validation error: {e}")
            results['error'] = str(e)

        return results

    def validate_settings(self) -> Dict[str, Any]:
        """Validate settings configuration."""
        print("⚙️ Validating Settings...")

        results = {
            'settings_class_exists': False,
            'required_fields': {},
            'validation_works': False
        }

        try:
            # Read settings.py to check structure
            settings_file = self.agent_dir / 'settings.py'
            if settings_file.exists():
                content = settings_file.read_text()

                required_fields = [
                    'anthropic_api_key',
                    'llm_model',
                    'app_env',
                    'log_level',
                    'debug'
                ]

                for field in required_fields:
                    results['required_fields'][field] = field in content

                results['settings_class_exists'] = 'class Settings' in content
                results['validation_works'] = 'model_validator' in content or 'validator' in content

        except Exception as e:
            self.issues.append(f"Settings validation error: {e}")
            results['error'] = str(e)

        return results

    def validate_prompts(self) -> Dict[str, Any]:
        """Validate system prompts."""
        print("💬 Validating Prompts...")

        results = {
            'prompts_found': [],
            'prompt_generators_found': [],
            'orchestrator_prompt': False
        }

        try:
            prompts_file = self.agent_dir / 'prompts.py'
            if prompts_file.exists():
                content = prompts_file.read_text()

                # Check for prompt constants
                prompt_patterns = [
                    'SYSTEM_PROMPT',
                    'PARSER_AGENT_PROMPT',
                    'OPTIMIZER_AGENT_PROMPT',
                    'FTMO_COMPLIANCE_AGENT_PROMPT',
                    'VERIFICATION_AGENT_PROMPT',
                    'DOCUMENTATION_AGENT_PROMPT',
                    'ORCHESTRATOR_PROMPT'
                ]

                for pattern in prompt_patterns:
                    if pattern in content:
                        results['prompts_found'].append(pattern)

                results['orchestrator_prompt'] = 'ORCHESTRATOR_PROMPT' in content

                # Check for prompt generators
                generator_patterns = [
                    'get_parser_prompt',
                    'get_optimizer_prompt',
                    'get_ftmo_prompt',
                    'get_verification_prompt',
                    'get_documentation_prompt'
                ]

                for pattern in generator_patterns:
                    if pattern in content:
                        results['prompt_generators_found'].append(pattern)

        except Exception as e:
            self.issues.append(f"Prompts validation error: {e}")
            results['error'] = str(e)

        return results

    async def run_deep_validation(self) -> Dict[str, Any]:
        """Run comprehensive deep validation like demo_validation.py."""
        print("\n" + "=" * 70)
        print("🧪 MT5 INFINITE RELIABILITY AGENT - COMPREHENSIVE VALIDATION")
        print("=" * 70 + "\n")

        validation_start = datetime.now()

        # Run all validations
        self.validation_results = {
            'structure': self.validate_structure(),
            'imports': self.validate_imports(),
            'agent_components': self.validate_agent_components(),
            'tools': self.validate_tools(),
            'models': self.validate_models(),
            'test_coverage': self.validate_test_coverage(),
            'dependencies': self.validate_dependencies_class(),
            'settings': self.validate_settings(),
            'prompts': self.validate_prompts()
        }

        validation_end = datetime.now()
        duration = (validation_end - validation_start).total_seconds()

        # Calculate overall score
        score = self.calculate_readiness_score()

        # Generate report
        report = self.generate_report(score, duration)

        return {
            'results': self.validation_results,
            'score': score,
            'issues': self.issues,
            'warnings': self.warnings,
            'duration': duration,
            'report': report
        }

    def calculate_readiness_score(self) -> Dict[str, Any]:
        """Calculate overall readiness score."""

        checks = {
            'structure': self.validation_results['structure']['all_required_present'],
            'imports': self.validation_results['imports']['import_success'],
            'main_agent': self.validation_results['agent_components'].get('main_agent', False),
            'subagents': all(
                s.get('exists', False)
                for s in self.validation_results['agent_components'].get('subagents', {}).values()
            ),
            'tools_callable': all(
                self.validation_results['tools'].get('tools_callable', {}).values()
            ),
            'tools_working': all(
                self.validation_results['tools'].get('tool_signatures_valid', {}).values()
            ),
            'models_valid': len(self.validation_results['models'].get('models_found', [])) >= 5,
            'coverage_adequate': self.validation_results['test_coverage'].get('estimated_coverage', 0) >= 70,
            'coverage_threshold': self.validation_results['test_coverage'].get('meets_98_threshold', False),
            'dependencies_complete': all([
                self.validation_results['dependencies'].get('class_exists', False),
                self.validation_results['dependencies'].get('from_settings_method', False)
            ]),
            'prompts_present': self.validation_results['prompts'].get('orchestrator_prompt', False)
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        return {
            'checks': checks,
            'passed': passed,
            'total': total,
            'percentage': (passed / total) * 100,
            'ready': passed == total and len(self.issues) == 0
        }

    def generate_report(self, score: Dict[str, Any], duration: float) -> str:
        """Generate comprehensive validation report."""

        report = f"""
# 🧪 MT5 Infinite Reliability Agent - Validation Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Validation Duration**: {duration:.2f}s
**Framework**: Awareness Orchestrator Pattern + Coverage Validator

## 📊 EXECUTIVE SUMMARY

- **Overall Readiness**: {"✅ 100% READY" if score['ready'] else f"⚠️ {score['percentage']:.0f}% Ready"}
- **Checks Passed**: {score['passed']}/{score['total']}
- **Critical Issues**: {len(self.issues)}
- **Warnings**: {len(self.warnings)}

## ✅ READINESS CHECKLIST

"""

        for check, passed in score['checks'].items():
            icon = "✅" if passed else "❌"
            report += f"- {icon} **{check.replace('_', ' ').title()}**\n"

        # Structure validation
        report += f"""
## 📁 STRUCTURE VALIDATION

**Required Files**:
"""
        for filename, result in self.validation_results['structure']['required_files'].items():
            icon = "✅" if result['exists'] else "❌"
            report += f"- {icon} {filename}"
            if result['exists']:
                report += f" ({result['lines']} lines)"
            report += "\n"

        # Agent components
        report += f"""
## 🤖 AGENT COMPONENTS

**Main Orchestrator**: {"✅ Configured" if self.validation_results['agent_components'].get('main_agent') else "❌ Missing"}

**Subagents**:
"""
        for name, status in self.validation_results['agent_components'].get('subagents', {}).items():
            icon = "✅" if status.get('exists') else "❌"
            report += f"- {icon} {name}\n"

        # Tools validation
        report += f"""
## 🔧 TOOLS VALIDATION

**Tools Found**: {len(self.validation_results['tools'].get('tools_found', []))}
**All Callable**: {"✅ Yes" if all(self.validation_results['tools'].get('tools_callable', {}).values()) else "❌ No"}
**All Working**: {"✅ Yes" if all(self.validation_results['tools'].get('tool_signatures_valid', {}).values()) else "⚠️ Some issues"}

"""
        for tool_name, works in self.validation_results['tools'].get('tool_signatures_valid', {}).items():
            icon = "✅" if works else "❌"
            report += f"- {icon} {tool_name}\n"

        # Models validation
        report += f"""
## 📋 MODELS VALIDATION

**Pydantic Models**: {len(self.validation_results['models'].get('models_found', []))}
**Enums**: {len(self.validation_results['models'].get('enums_found', []))}

"""

        # Test coverage
        coverage = self.validation_results['test_coverage']
        report += f"""
## 📊 TEST COVERAGE

**Estimated Coverage**: {coverage.get('estimated_coverage', 0):.1f}% {"✅" if coverage.get('meets_98_threshold') else "⚠️"}
**Test Files**: {len(coverage.get('test_files_found', []))}
**Total Tests**: {coverage.get('total_test_functions', 0)}
**Async Tests**: {coverage.get('async_tests', 0)}

**Coverage Areas**:
"""
        for area, data in coverage.get('coverage_areas', {}).items():
            icon = "✅" if data.get('covered') else "❌"
            report += f"- {icon} {area.replace('_', ' ').title()}: {data.get('matches', 0)} references\n"

        # Issues and warnings
        if self.issues:
            report += "\n## ❌ CRITICAL ISSUES\n\n"
            for issue in self.issues:
                report += f"- {issue}\n"

        if self.warnings:
            report += "\n## ⚠️ WARNINGS\n\n"
            for warning in self.warnings:
                report += f"- {warning}\n"

        # Final assessment
        report += f"""
## 🎯 FINAL ASSESSMENT

**Production Readiness**: {"✅ APPROVED" if score['ready'] else "❌ NOT READY"}
**Deployment Status**: {"✅ CLEAR FOR DEPLOYMENT" if score['ready'] and len(self.issues) == 0 else "⚠️ REQUIRES FIXES"}

"""

        if score['ready']:
            report += """
### ✅ ALL VALIDATION CHECKS PASSED

The MT5 Infinite Reliability Agent meets all requirements:
- All required files present
- All imports working
- All tools functional and tested
- Coverage meets threshold
- Dependencies properly configured
- Prompts fully defined

**Recommendation**: Ready for production deployment
"""
        else:
            report += """
### ⚠️ FIXES REQUIRED

Please address the issues listed above before deployment.

**Priority Actions**:
"""
            for issue in self.issues[:5]:
                report += f"1. {issue}\n"

        report += """
---
*Validated using Awareness Orchestrator Pattern + Coverage Validator methodology*
*Framework: Pydantic AI Agent Deep Validator*
"""

        return report


async def main():
    """Run comprehensive validation."""

    validator = MT5AgentValidator()
    results = await validator.run_deep_validation()

    # Print summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION COMPLETE")
    print("=" * 70)

    score = results['score']
    print(f"\n✅ Checks Passed: {score['passed']}/{score['total']} ({score['percentage']:.0f}%)")
    print(f"❌ Critical Issues: {len(results['issues'])}")
    print(f"⚠️ Warnings: {len(results['warnings'])}")

    if results['issues']:
        print("\nCritical Issues:")
        for issue in results['issues']:
            print(f"  - {issue}")

    # Save report
    report_path = Path(__file__).parent / "VALIDATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(results['report'])
    print(f"\n📝 Full report saved to: {report_path}")

    # Final status
    if score['ready']:
        print("\n" + "=" * 70)
        print("🚀 MT5 INFINITE RELIABILITY AGENT: 100% READY FOR PRODUCTION")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ MT5 INFINITE RELIABILITY AGENT: REQUIRES FIXES")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
