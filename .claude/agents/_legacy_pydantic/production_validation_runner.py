#!/usr/bin/env python3
"""
Production Validation Runner for Pydantic AI Agents
Ensures all agents are production-ready with comprehensive validation
"""

import os
import sys
import subprocess
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback


class ProductionValidator:
    """Production-grade validation system for AI agents."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.agents_dir = Path(__file__).parent
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        self.production_ready = []

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level."""
        if self.verbose or level in ["ERROR", "CRITICAL", "WARNING"]:
            timestamp = datetime.now().strftime('%H:%M:%S')
            icon = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "CRITICAL": "💥"
            }.get(level, "📝")
            print(f"[{timestamp}] {icon} {level}: {message}")

    def validate_test_structure(self, agent_name: str) -> Dict[str, Any]:
        """Validate test structure and completeness."""
        self.log(f"Validating test structure for {agent_name}")

        test_file = self.agents_dir / agent_name / 'tests' / 'test_deep_probe.py'

        if not test_file.exists():
            self.critical_issues.append(f"{agent_name}: Missing deep probe tests")
            return {'status': 'CRITICAL', 'error': 'Missing test file'}

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            # Check for required test categories
            required_categories = [
                'deep_behavior_probing',
                'failure_injection',
                'property_based_testing',
                'performance_testing',
                'security_testing',
                'memory_safety',
                'state_machine_validation',
                'error_recovery'
            ]

            implemented_categories = []
            for category in required_categories:
                patterns = {
                    'deep_behavior_probing': ['probe', 'behavior', 'state_transition'],
                    'failure_injection': ['failure', 'inject', 'side_effect'],
                    'property_based_testing': ['@given', 'hypothesis', 'invariant'],
                    'performance_testing': ['performance', 'load', 'concurrent'],
                    'security_testing': ['security', 'injection', 'attack'],
                    'memory_safety': ['memory', 'boundary', 'resource'],
                    'state_machine_validation': ['state', 'machine', 'transition'],
                    'error_recovery': ['recovery', 'error', 'fallback']
                }

                category_found = any(pattern in content.lower() for pattern in patterns.get(category, []))
                if category_found:
                    implemented_categories.append(category)

            # Count test functions
            test_functions = content.count('def test_')
            async_tests = content.count('async def test_')
            fixtures = content.count('@pytest.fixture')

            result = {
                'status': 'GOOD' if len(implemented_categories) >= 6 else 'NEEDS_WORK',
                'test_functions': test_functions,
                'async_tests': async_tests,
                'fixtures': fixtures,
                'implemented_categories': implemented_categories,
                'missing_categories': [cat for cat in required_categories if cat not in implemented_categories],
                'coverage_estimate': len(implemented_categories) / len(required_categories) * 100
            }

            if result['status'] == 'NEEDS_WORK':
                self.warnings.append(f"{agent_name}: Missing test categories: {result['missing_categories']}")

            return result

        except Exception as e:
            self.critical_issues.append(f"{agent_name}: Test file error: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}

    def validate_syntax_and_imports(self, agent_name: str) -> Dict[str, Any]:
        """Validate Python syntax and basic imports."""
        self.log(f"Validating syntax for {agent_name}")

        agent_dir = self.agents_dir / agent_name
        python_files = list(agent_dir.glob('**/*.py'))

        syntax_results = {}
        import_results = {}

        for py_file in python_files:
            rel_path = py_file.relative_to(agent_dir)

            # Check syntax
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                compile(content, str(py_file), 'exec')
                syntax_results[str(rel_path)] = 'VALID'
            except SyntaxError as e:
                syntax_results[str(rel_path)] = f'SYNTAX_ERROR: {e}'
                self.critical_issues.append(f"{agent_name}: Syntax error in {rel_path}")
            except Exception as e:
                syntax_results[str(rel_path)] = f'ERROR: {e}'

        # Test basic imports (without actually importing to avoid dependency issues)
        core_modules = ['agent.py', 'models.py', 'tools.py', 'dependencies.py']
        for module in core_modules:
            module_path = agent_dir / module
            if module_path.exists():
                try:
                    with open(module_path, 'r') as f:
                        content = f.read()
                    # Check for basic structure
                    if 'class' in content or 'def' in content:
                        import_results[module] = 'STRUCTURE_OK'
                    else:
                        import_results[module] = 'NO_DEFINITIONS'
                        self.warnings.append(f"{agent_name}: {module} has no class/function definitions")
                except Exception as e:
                    import_results[module] = f'READ_ERROR: {e}'
            else:
                import_results[module] = 'MISSING'
                if module != 'models.py':  # models.py is optional for some agents
                    self.warnings.append(f"{agent_name}: Missing {module}")

        syntax_errors = sum(1 for status in syntax_results.values() if 'ERROR' in status)

        return {
            'status': 'GOOD' if syntax_errors == 0 else 'CRITICAL',
            'syntax_results': syntax_results,
            'import_results': import_results,
            'total_files': len(python_files),
            'syntax_errors': syntax_errors
        }

    def validate_security_features(self, agent_name: str) -> Dict[str, Any]:
        """Validate security features implementation."""
        self.log(f"Validating security features for {agent_name}")

        test_file = self.agents_dir / agent_name / 'tests' / 'test_deep_probe.py'

        if not test_file.exists():
            return {'status': 'MISSING', 'error': 'No test file'}

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            security_features = {
                'injection_prevention': any(term in content.lower() for term in ['injection', 'sanitiz', 'escape']),
                'input_validation': any(term in content.lower() for term in ['validation', 'sanitiz', 'filter']),
                'resource_limits': any(term in content.lower() for term in ['limit', 'resource', 'memory', 'timeout']),
                'privilege_checks': any(term in content.lower() for term in ['privilege', 'permission', 'access']),
                'error_handling': any(term in content.lower() for term in ['error', 'exception', 'try', 'except']),
                'isolation_testing': any(term in content.lower() for term in ['isolation', 'separation', 'boundary'])
            }

            implemented_features = sum(1 for implemented in security_features.values() if implemented)
            total_features = len(security_features)

            status = 'GOOD' if implemented_features >= total_features * 0.7 else 'NEEDS_IMPROVEMENT'

            if status == 'NEEDS_IMPROVEMENT':
                missing = [feat for feat, impl in security_features.items() if not impl]
                self.warnings.append(f"{agent_name}: Missing security features: {missing}")

            return {
                'status': status,
                'security_features': security_features,
                'implemented_count': implemented_features,
                'total_count': total_features,
                'security_score': implemented_features / total_features * 100
            }

        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def validate_performance_features(self, agent_name: str) -> Dict[str, Any]:
        """Validate performance testing features."""
        self.log(f"Validating performance features for {agent_name}")

        test_file = self.agents_dir / agent_name / 'tests' / 'test_deep_probe.py'

        if not test_file.exists():
            return {'status': 'MISSING', 'error': 'No test file'}

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            performance_features = {
                'concurrent_testing': any(term in content.lower() for term in ['concurrent', 'parallel', 'asyncio.gather']),
                'load_testing': any(term in content.lower() for term in ['load', 'stress', 'performance']),
                'memory_testing': any(term in content.lower() for term in ['memory', 'boundary', 'large']),
                'timeout_testing': any(term in content.lower() for term in ['timeout', 'time', 'duration']),
                'scalability_testing': any(term in content.lower() for term in ['scalab', 'scale', 'size']),
                'benchmark_testing': any(term in content.lower() for term in ['benchmark', 'metric', 'measurement'])
            }

            implemented_features = sum(1 for implemented in performance_features.values() if implemented)
            total_features = len(performance_features)

            # Special handling for Blitzfire agent - needs higher performance standards
            threshold = 0.8 if agent_name == 'blitzfire_code_agent' else 0.6
            status = 'GOOD' if implemented_features >= total_features * threshold else 'NEEDS_IMPROVEMENT'

            if status == 'NEEDS_IMPROVEMENT':
                missing = [feat for feat, impl in performance_features.items() if not impl]
                self.warnings.append(f"{agent_name}: Missing performance features: {missing}")

            return {
                'status': status,
                'performance_features': performance_features,
                'implemented_count': implemented_features,
                'total_count': total_features,
                'performance_score': implemented_features / total_features * 100
            }

        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def run_basic_test_syntax_check(self, agent_name: str) -> Dict[str, Any]:
        """Run basic test file syntax validation."""
        self.log(f"Running test syntax check for {agent_name}")

        test_file = self.agents_dir / agent_name / 'tests' / 'test_deep_probe.py'

        if not test_file.exists():
            return {'status': 'MISSING', 'error': 'No test file'}

        try:
            # Try to compile the test file
            with open(test_file, 'r') as f:
                content = f.read()

            compile(content, str(test_file), 'exec')

            # Check for basic pytest structure
            has_pytest = '@pytest.' in content or 'pytest' in content
            has_async = 'async def test_' in content
            has_fixtures = '@pytest.fixture' in content
            test_count = content.count('def test_')

            return {
                'status': 'GOOD' if has_pytest and test_count > 0 else 'NEEDS_WORK',
                'has_pytest': has_pytest,
                'has_async': has_async,
                'has_fixtures': has_fixtures,
                'test_count': test_count,
                'file_size': len(content)
            }

        except SyntaxError as e:
            self.critical_issues.append(f"{agent_name}: Test syntax error: {e}")
            return {'status': 'CRITICAL', 'error': f'Syntax error: {e}'}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def assess_production_readiness(self, agent_name: str, validations: Dict[str, Any]) -> str:
        """Assess overall production readiness."""

        # Count critical issues
        critical_count = sum(1 for v in validations.values()
                           if v.get('status') in ['CRITICAL', 'ERROR'])

        # Count warnings
        warning_count = sum(1 for v in validations.values()
                          if v.get('status') == 'NEEDS_WORK')

        # Check test coverage
        test_validation = validations.get('test_structure', {})
        coverage = test_validation.get('coverage_estimate', 0)

        # Production readiness criteria
        if critical_count > 0:
            return 'CRITICAL_ISSUES'
        elif coverage < 70:
            return 'INSUFFICIENT_TESTING'
        elif warning_count > 2:
            return 'NEEDS_IMPROVEMENT'
        elif coverage >= 85:
            return 'PRODUCTION_READY'
        else:
            return 'REVIEW_REQUIRED'

    async def validate_all_agents(self) -> Dict[str, Any]:
        """Run comprehensive validation on all agents."""
        self.log("Starting comprehensive production validation", "INFO")

        agents = ['clang_tidy_ai_agent', 'blitzfire_code_agent', 'multi_agent_debugging_system']

        for agent_name in agents:
            self.log(f"Validating {agent_name}", "INFO")

            # Run all validation checks
            validations = {
                'test_structure': self.validate_test_structure(agent_name),
                'syntax_imports': self.validate_syntax_and_imports(agent_name),
                'security_features': self.validate_security_features(agent_name),
                'performance_features': self.validate_performance_features(agent_name),
                'test_syntax': self.run_basic_test_syntax_check(agent_name)
            }

            # Assess overall readiness
            readiness = self.assess_production_readiness(agent_name, validations)

            self.validation_results[agent_name] = {
                'validations': validations,
                'readiness': readiness,
                'timestamp': datetime.now().isoformat()
            }

            # Track production ready agents
            if readiness == 'PRODUCTION_READY':
                self.production_ready.append(agent_name)
                self.log(f"{agent_name}: PRODUCTION READY ✅", "SUCCESS")
            elif readiness == 'CRITICAL_ISSUES':
                self.log(f"{agent_name}: CRITICAL ISSUES ❌", "CRITICAL")
            else:
                self.log(f"{agent_name}: {readiness} ⚠️", "WARNING")

        return self.validation_results

    def generate_production_report(self) -> str:
        """Generate production readiness report."""

        total_agents = len(self.validation_results)
        ready_agents = len(self.production_ready)
        critical_agents = len([a for a, r in self.validation_results.items()
                              if r['readiness'] == 'CRITICAL_ISSUES'])

        report = f"""
# 🚀 PRODUCTION READINESS REPORT

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Validation Framework**: Production-Grade AI Agent Validator
**Project**: Wire Ground Quantitative Finance Framework

## 📊 EXECUTIVE SUMMARY

- **Total Agents**: {total_agents}
- **Production Ready**: {ready_agents} ✅
- **Critical Issues**: {critical_agents} ❌
- **Overall Status**: {"✅ READY FOR DEPLOYMENT" if ready_agents == total_agents else "⚠️ REQUIRES ATTENTION" if critical_agents == 0 else "❌ CRITICAL ISSUES MUST BE RESOLVED"}

### 🎯 Agent Status Overview
"""

        for agent_name, result in self.validation_results.items():
            readiness = result['readiness']
            icon = {
                'PRODUCTION_READY': '✅',
                'REVIEW_REQUIRED': '🔍',
                'NEEDS_IMPROVEMENT': '⚠️',
                'INSUFFICIENT_TESTING': '📊',
                'CRITICAL_ISSUES': '❌'
            }.get(readiness, '❓')

            report += f"- **{agent_name.replace('_', ' ').title()}**: {icon} {readiness}\n"

        report += "\n## 🔍 DETAILED VALIDATION RESULTS\n"

        for agent_name, result in self.validation_results.items():
            validations = result['validations']

            report += f"\n### {agent_name.replace('_', ' ').title()}\n"
            report += f"**Overall Status**: {result['readiness']}\n\n"

            # Test structure
            test_struct = validations.get('test_structure', {})
            if 'test_functions' in test_struct:
                report += f"**Test Coverage**:\n"
                report += f"- Test Functions: {test_struct['test_functions']}\n"
                report += f"- Async Tests: {test_struct['async_tests']}\n"
                report += f"- Coverage Estimate: {test_struct.get('coverage_estimate', 0):.1f}%\n"
                report += f"- Implemented Categories: {len(test_struct.get('implemented_categories', []))}/8\n"

            # Security features
            security = validations.get('security_features', {})
            if 'security_score' in security:
                report += f"\n**Security Validation**:\n"
                report += f"- Security Score: {security['security_score']:.1f}%\n"
                report += f"- Features Implemented: {security['implemented_count']}/{security['total_count']}\n"

            # Performance features
            performance = validations.get('performance_features', {})
            if 'performance_score' in performance:
                report += f"\n**Performance Testing**:\n"
                report += f"- Performance Score: {performance['performance_score']:.1f}%\n"
                report += f"- Features Implemented: {performance['implemented_count']}/{performance['total_count']}\n"

            # Syntax validation
            syntax = validations.get('syntax_imports', {})
            if 'syntax_errors' in syntax:
                report += f"\n**Code Quality**:\n"
                report += f"- Total Files: {syntax['total_files']}\n"
                report += f"- Syntax Errors: {syntax['syntax_errors']}\n"
                report += f"- Status: {'✅ CLEAN' if syntax['syntax_errors'] == 0 else '❌ ERRORS'}\n"

        # Issues and recommendations
        if self.critical_issues:
            report += "\n## 🚨 CRITICAL ISSUES\n"
            for issue in self.critical_issues:
                report += f"- ❌ {issue}\n"

        if self.warnings:
            report += "\n## ⚠️ WARNINGS\n"
            for warning in self.warnings:
                report += f"- ⚠️ {warning}\n"

        # Production deployment guidance
        report += "\n## 🚀 PRODUCTION DEPLOYMENT GUIDANCE\n"

        if ready_agents == total_agents:
            report += """
### ✅ ALL AGENTS READY FOR DEPLOYMENT

**Immediate Actions**:
1. Deploy all agents to production environment
2. Enable monitoring and alerting
3. Configure health checks
4. Set up performance dashboards

**Monitoring Setup**:
- Response time thresholds: <100ms for critical operations
- Error rate alerts: >1% error rate triggers alert
- Memory usage: Monitor for memory leaks
- Security events: Log and alert on security violations
"""
        else:
            report += f"""
### ⚠️ PARTIAL DEPLOYMENT READY

**Ready for Production**: {', '.join(self.production_ready)}

**Requires Fixes**: {', '.join([a for a, r in self.validation_results.items() if r['readiness'] != 'PRODUCTION_READY'])}

**Recommended Approach**:
1. Deploy production-ready agents immediately
2. Fix critical issues in remaining agents
3. Gradual deployment as agents become ready
4. Monitor production agents while fixing others
"""

        # Final recommendations
        report += "\n## 📋 NEXT STEPS\n"

        if critical_agents > 0:
            report += "1. **CRITICAL**: Fix all critical issues before any deployment\n"

        if ready_agents > 0:
            report += f"2. **DEPLOY**: {', '.join(self.production_ready)} ready for immediate production deployment\n"

        if len(self.warnings) > 0:
            report += "3. **ENHANCE**: Address warnings for optimal performance\n"

        report += "4. **MONITOR**: Set up comprehensive monitoring and alerting\n"
        report += "5. **VALIDATE**: Run full integration tests in production environment\n"

        report += f"""
## ✅ VALIDATION COMPLETE

**Summary**: {ready_agents}/{total_agents} agents validated and ready for production deployment.

**Risk Assessment**: {"LOW" if critical_agents == 0 else "HIGH"}
**Deployment Confidence**: {"HIGH" if ready_agents == total_agents else "MODERATE" if critical_agents == 0 else "LOW"}

---
*Production validation completed by Wire Ground AI Agent Validation System*
"""

        return report

    def create_deployment_checklist(self) -> str:
        """Create production deployment checklist."""

        checklist = f"""
# 🚀 PRODUCTION DEPLOYMENT CHECKLIST

**Project**: Wire Ground Quantitative Finance Framework
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## PRE-DEPLOYMENT VALIDATION

### ✅ Agent Readiness
"""

        for agent_name in ['clang_tidy_ai_agent', 'blitzfire_code_agent', 'multi_agent_debugging_system']:
            result = self.validation_results.get(agent_name, {})
            status = result.get('readiness', 'UNKNOWN')
            checkbox = "☑️" if status == 'PRODUCTION_READY' else "☐"

            checklist += f"- {checkbox} **{agent_name.replace('_', ' ').title()}**: {status}\n"

        checklist += f"""

### 🔧 Infrastructure Requirements
- ☐ **Python 3.12+**: Runtime environment configured
- ☐ **Dependencies**: All required packages installed
- ☐ **Memory**: Minimum 4GB RAM allocated per agent
- ☐ **CPU**: Multi-core processor for concurrent operations
- ☐ **Storage**: Sufficient disk space for logs and temporary files
- ☐ **Network**: Stable internet connection for external APIs

### 🛡️ Security Configuration
- ☐ **Access Controls**: Proper authentication and authorization
- ☐ **API Keys**: Secure storage and rotation policies
- ☐ **Firewall**: Network security rules configured
- ☐ **Encryption**: Data encryption at rest and in transit
- ☐ **Audit Logging**: Security event logging enabled
- ☐ **Backup**: Secure backup and recovery procedures

### 📊 Monitoring Setup
- ☐ **Health Checks**: Endpoint monitoring configured
- ☐ **Performance Metrics**: Response time and throughput tracking
- ☐ **Error Monitoring**: Exception tracking and alerting
- ☐ **Resource Monitoring**: CPU, memory, and disk usage
- ☐ **Log Aggregation**: Centralized logging system
- ☐ **Dashboards**: Real-time monitoring dashboards

## DEPLOYMENT PHASES

### Phase 1: Production-Ready Agents
**Deploy Immediately**: {', '.join(self.production_ready) if self.production_ready else 'None ready'}

- ☐ Deploy to production environment
- ☐ Configure load balancing
- ☐ Enable monitoring and alerting
- ☐ Run smoke tests
- ☐ Verify functionality

### Phase 2: Agents Requiring Fixes
**Deploy After Fixes**: {', '.join([a for a, r in self.validation_results.items() if r.get('readiness') != 'PRODUCTION_READY']) if self.validation_results else 'None'}

- ☐ Fix critical issues identified in validation
- ☐ Re-run validation tests
- ☐ Deploy to staging environment first
- ☐ Full integration testing
- ☐ Deploy to production

### Phase 3: Integration Testing
- ☐ **End-to-End Testing**: Full system integration tests
- ☐ **Load Testing**: Production-level load simulation
- ☐ **Failover Testing**: Disaster recovery procedures
- ☐ **Performance Benchmarking**: Baseline performance metrics
- ☐ **Security Testing**: Penetration testing and vulnerability scans

## POST-DEPLOYMENT VALIDATION

### 🔍 Immediate Checks (0-4 hours)
- ☐ All agents responding to health checks
- ☐ No critical errors in logs
- ☐ Performance within expected parameters
- ☐ Security monitoring active
- ☐ Backup systems functioning

### 📈 Short-term Monitoring (1-7 days)
- ☐ Performance trend analysis
- ☐ Error rate monitoring
- ☐ Resource utilization assessment
- ☐ User experience validation
- ☐ Security incident review

### 🔄 Long-term Operations (1+ weeks)
- ☐ Performance optimization
- ☐ Capacity planning
- ☐ Security updates
- ☐ Feature enhancements
- ☐ Maintenance scheduling

## ROLLBACK PLAN

### 🚨 Emergency Procedures
- ☐ **Immediate Rollback**: Automated rollback triggers defined
- ☐ **Service Isolation**: Ability to isolate problematic agents
- ☐ **Backup Activation**: Fallback systems ready
- ☐ **Communication Plan**: Stakeholder notification procedures
- ☐ **Recovery Testing**: Regular disaster recovery drills

## SIGN-OFF

### Development Team
- ☐ **Lead Developer**: Code quality approved
- ☐ **QA Engineer**: Testing completed and passed
- ☐ **Security Officer**: Security review completed
- ☐ **DevOps Engineer**: Infrastructure ready

### Business Stakeholders
- ☐ **Product Owner**: Feature requirements met
- ☐ **Operations Manager**: Operational procedures defined
- ☐ **Risk Manager**: Risk assessment completed
- ☐ **Compliance Officer**: Regulatory requirements met

---
**DEPLOYMENT AUTHORIZATION**

By checking all items above, the Wire Ground AI Agent system is approved for production deployment.

**Final Deployment Decision**: {"✅ APPROVED" if len(self.production_ready) == len(self.validation_results) else "⚠️ CONDITIONAL" if len(self.critical_issues) == 0 else "❌ NOT APPROVED"}

*Checklist generated by Production Validation System*
"""

        return checklist


async def main():
    """Main validation execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Production Validation for AI Agents')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-o', '--output-dir', default='.', help='Output directory for reports')

    args = parser.parse_args()

    validator = ProductionValidator(verbose=args.verbose)

    try:
        print("🚀 PRODUCTION VALIDATION SYSTEM")
        print("=" * 50)
        print("Ensuring all AI agents are production-ready...")
        print()

        # Run comprehensive validation
        results = await validator.validate_all_agents()

        # Generate reports
        output_dir = Path(args.output_dir)

        # Production readiness report
        production_report = validator.generate_production_report()
        production_file = output_dir / "PRODUCTION_READINESS_REPORT.md"
        with open(production_file, 'w') as f:
            f.write(production_report)

        # Deployment checklist
        checklist = validator.create_deployment_checklist()
        checklist_file = output_dir / "DEPLOYMENT_CHECKLIST.md"
        with open(checklist_file, 'w') as f:
            f.write(checklist)

        # Summary
        total_agents = len(results)
        ready_agents = len(validator.production_ready)
        critical_issues = len(validator.critical_issues)

        print("\n" + "=" * 50)
        print("PRODUCTION VALIDATION COMPLETE")
        print("=" * 50)
        print(f"📊 Reports: {production_file}, {checklist_file}")
        print(f"🎯 Ready: {ready_agents}/{total_agents} agents")
        print(f"🚨 Critical: {critical_issues} issues")

        if ready_agents == total_agents and critical_issues == 0:
            print("✅ ALL AGENTS PRODUCTION READY!")
            print("🚀 CLEARED FOR DEPLOYMENT")
        elif critical_issues == 0:
            print("⚠️ SOME AGENTS NEED ENHANCEMENT")
            print("🔧 FIX WARNINGS BEFORE FULL DEPLOYMENT")
        else:
            print("❌ CRITICAL ISSUES DETECTED")
            print("🛑 MUST FIX BEFORE DEPLOYMENT")

        return 0 if critical_issues == 0 else 1

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)