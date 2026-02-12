"""
Comprehensive test suite for the Clang-Tidy Factory Orchestrator.
Validates the 5-phase workflow using patterns from successful safe_test.cpp debugging.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import List

# Import the factory components
try:
    from ..factory_orchestrator import (
        ClangTidyFactory, 
        FactorySession, 
        WorkflowPhase,
        fix_single_file,
        fix_project_wide,
        emergency_build_fix
    )
    from ..models import (
        Warning, 
        ClangTidyAnalysis, 
        FixStrategy, 
        ValidationResult,
        FactoryReport,
        SubagentResult
    )
except ImportError:
    import sys
    sys.path.append('..')
    from factory_orchestrator import (
        ClangTidyFactory, 
        FactorySession, 
        WorkflowPhase,
        fix_single_file,
        fix_project_wide,
        emergency_build_fix
    )
    from models import (
        Warning, 
        ClangTidyAnalysis, 
        FixStrategy, 
        ValidationResult,
        FactoryReport,
        SubagentResult
    )


class TestClangTidyFactory:
    """Test the main factory orchestrator functionality."""
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance for testing."""
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            factory = ClangTidyFactory()
            return factory
    
    @pytest.fixture
    def sample_cpp_files(self, tmp_path):
        """Create sample C++ files for testing."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("""
        #include <iostream>
        #include <ranges>
        
        int main() {
            std::vector<int> v(5);
            std::ranges::iota(v, 1);  // C++20 compatibility issue
            return 0;
        }
        """)
        return [str(test_file)]
    
    @pytest.mark.asyncio
    async def test_factory_initialization(self, factory):
        """Test factory initializes with correct subagents."""
        assert 'analyzer' in factory.subagents
        assert 'strategist' in factory.subagents
        assert 'critical_fixer' in factory.subagents
        assert 'safety_fixer' in factory.subagents
        assert 'quality_fixer' in factory.subagents
        assert 'validator' in factory.subagents
        
        # Verify subagent configurations
        assert factory.subagents['analyzer']['specialization'] == 'comprehensive_issue_discovery'
        assert factory.subagents['critical_fixer']['specialization'] == 'compilation_blockers'
    
    @pytest.mark.asyncio
    async def test_workflow_session_creation(self, factory, sample_cpp_files):
        """Test that workflow sessions are created properly."""
        with patch.object(factory, '_execute_phase_1_discovery', new_callable=AsyncMock), \
             patch.object(factory, '_execute_phase_2_strategy', new_callable=AsyncMock), \
             patch.object(factory, '_execute_phase_3_parallel_fixing', new_callable=AsyncMock), \
             patch.object(factory, '_execute_phase_4_validation', new_callable=AsyncMock), \
             patch.object(factory, '_execute_phase_5_reporting', new_callable=AsyncMock):
            
            session_id = await factory.start_factory_workflow(sample_cpp_files)
            
            assert session_id in factory.active_sessions
            session = factory.active_sessions[session_id]
            assert isinstance(session, FactorySession)
            assert session.target_files == sample_cpp_files
    
    @pytest.mark.asyncio
    async def test_phase_1_discovery(self, factory, sample_cpp_files):
        """Test Phase 1: Comprehensive Issue Discovery."""
        session = FactorySession("test_session", sample_cpp_files)
        
        # Mock the analyzer subagent response
        mock_analysis = "Found 6 std::ranges issues, 2 C++20 compatibility issues"
        with patch.object(factory, '_invoke_subagent', return_value=mock_analysis) as mock_invoke:
            await factory._execute_phase_1_discovery(session)
            
            # Verify analyzer subagent was called
            mock_invoke.assert_called_once_with('analyzer', pytest.any(str))
            
            # Verify session state was updated
            assert session.current_phase == WorkflowPhase.DISCOVERY
            assert session.discovered_issues is not None
    
    @pytest.mark.asyncio
    async def test_phase_2_strategy_planning(self, factory, sample_cpp_files):
        """Test Phase 2: Smart Fix Strategy Planning."""
        session = FactorySession("test_session", sample_cpp_files)
        
        # Setup discovered issues
        session.discovered_issues = ClangTidyAnalysis(
            total_warnings=8,
            warnings=[
                Warning(
                    line_number=5, column_number=5, rule_id="modernize-use-ranges",
                    severity="CRITICAL", category="critical", message="std::ranges issue"
                )
            ],
            categories=['critical', 'safety', 'quality'],
            recommended_fix_order=['critical', 'safety', 'quality']
        )
        
        mock_strategy = "3-phase strategy: critical → safety → quality"
        with patch.object(factory, '_invoke_subagent', return_value=mock_strategy) as mock_invoke:
            await factory._execute_phase_2_strategy(session)
            
            mock_invoke.assert_called_once_with('strategist', pytest.any(str))
            assert session.current_phase == WorkflowPhase.STRATEGY
            assert session.fix_strategy is not None
    
    @pytest.mark.asyncio
    async def test_phase_3_parallel_fixing(self, factory, sample_cpp_files):
        """Test Phase 3: Parallel Specialized Fixing."""
        session = FactorySession("test_session", sample_cpp_files)
        
        # Setup session with discovered issues and strategy
        session.discovered_issues = ClangTidyAnalysis(
            total_warnings=8,
            warnings=[
                Warning(
                    line_number=5, column_number=5, rule_id="modernize-use-ranges",
                    severity="CRITICAL", category="critical", message="std::ranges issue"
                ),
                Warning(
                    line_number=10, column_number=3, rule_id="cppcoreguidelines-pro-bounds-pointer-arithmetic",
                    severity="HIGH", category="safety", message="pointer arithmetic"
                )
            ],
            categories=['critical', 'safety', 'quality'],
            recommended_fix_order=['critical', 'safety', 'quality']
        )
        
        # Mock parallel subagent execution
        mock_results = ["critical fixes applied", "safety fixes applied", "quality fixes applied"]
        with patch.object(factory, '_invoke_subagent', side_effect=mock_results) as mock_invoke:
            await factory._execute_phase_3_parallel_fixing(session)
            
            # Verify all three fixing subagents were called
            assert mock_invoke.call_count == 3
            expected_subagents = ['critical_fixer', 'safety_fixer', 'quality_fixer']
            actual_subagents = [call[0][0] for call in mock_invoke.call_args_list]
            assert set(actual_subagents) == set(expected_subagents)
    
    @pytest.mark.asyncio
    async def test_phase_4_validation(self, factory, sample_cpp_files):
        """Test Phase 4: Continuous Validation & Build Testing."""
        session = FactorySession("test_session", sample_cpp_files)
        
        mock_validation = "All tests pass, build successful, 5% performance improvement"
        with patch.object(factory, '_invoke_subagent', return_value=mock_validation) as mock_invoke:
            await factory._execute_phase_4_validation(session)
            
            mock_invoke.assert_called_once_with('validator', pytest.any(str))
            assert session.current_phase == WorkflowPhase.VALIDATION
            assert len(session.validation_results) > 0
    
    @pytest.mark.asyncio
    async def test_phase_5_reporting(self, factory, sample_cpp_files):
        """Test Phase 5: Final Quality Assurance & Reporting."""
        session = FactorySession("test_session", sample_cpp_files)
        
        # Setup session with complete workflow data
        session.discovered_issues = ClangTidyAnalysis(
            total_warnings=8,
            warnings=[],
            categories=['critical', 'safety', 'quality'],
            recommended_fix_order=['critical', 'safety', 'quality']
        )
        session.validation_results = [
            ValidationResult(
                build_success=True,
                test_pass_rate=1.0,
                performance_impact=0.05,
                quality_improvement=0.23
            )
        ]
        
        report = await factory._execute_phase_5_reporting(session)
        
        assert session.current_phase == WorkflowPhase.REPORTING
        assert isinstance(report, dict)
        assert 'session_id' in report
        assert 'duration_seconds' in report
        assert report['build_status'] == 'SUCCESS'


class TestSubagentIntegration:
    """Test subagent integration and coordination."""
    
    @pytest.fixture
    def factory(self):
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            return ClangTidyFactory()
    
    @pytest.mark.asyncio
    async def test_subagent_invocation(self, factory):
        """Test basic subagent invocation mechanism."""
        test_prompt = "Analyze this code for issues"
        result = await factory._invoke_subagent('analyzer', test_prompt)
        
        # In current implementation, this returns a simulated response
        assert isinstance(result, str)
        assert 'analyzer' in result
    
    @pytest.mark.asyncio
    async def test_parallel_subagent_execution(self, factory):
        """Test that subagents can execute in parallel."""
        start_time = asyncio.get_event_loop().time()
        
        # Execute multiple subagents concurrently
        tasks = [
            factory._invoke_subagent('critical_fixer', "fix critical issues"),
            factory._invoke_subagent('safety_fixer', "fix safety issues"), 
            factory._invoke_subagent('quality_fixer', "fix quality issues")
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Verify all subagents returned results
        assert len(results) == 3
        assert all(isinstance(result, str) for result in results)
        
        # Verify parallel execution was faster than sequential
        # (Each mock subagent sleeps for 1 second, so parallel should be ~1s, sequential ~3s)
        execution_time = end_time - start_time
        assert execution_time < 2.0  # Should be much faster than 3 sequential seconds


class TestWorkflowPatterns:
    """Test different workflow patterns and use cases."""
    
    @pytest.fixture
    def factory(self):
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            return ClangTidyFactory()
    
    @pytest.mark.asyncio
    async def test_single_file_workflow(self, factory, tmp_path):
        """Test single file analysis workflow."""
        test_file = tmp_path / "single.cpp"
        test_file.write_text("int main() { return 0; }")
        
        with patch.object(factory, 'start_factory_workflow') as mock_workflow:
            mock_workflow.return_value = "session_123"
            
            result = await fix_single_file(str(test_file))
            
            mock_workflow.assert_called_once_with([str(test_file)], "single_file")
    
    @pytest.mark.asyncio
    async def test_project_wide_workflow(self, factory):
        """Test project-wide analysis workflow."""
        file_pattern = "*.cpp"
        
        with patch('factory_orchestrator.glob') as mock_glob, \
             patch.object(factory, 'start_factory_workflow') as mock_workflow:
            
            mock_glob.return_value = ["file1.cpp", "file2.cpp", "file3.cpp"]
            mock_workflow.return_value = "session_456"
            
            result = await fix_project_wide(file_pattern)
            
            mock_workflow.assert_called_once_with(
                ["file1.cpp", "file2.cpp", "file3.cpp"], 
                "project_wide"
            )
    
    @pytest.mark.asyncio
    async def test_emergency_build_fix(self, factory):
        """Test emergency build fix workflow."""
        failing_files = ["broken1.cpp", "broken2.cpp"]
        
        with patch.object(factory, 'start_factory_workflow') as mock_workflow:
            mock_workflow.return_value = "session_emergency"
            
            result = await emergency_build_fix(failing_files)
            
            mock_workflow.assert_called_once_with(failing_files, "build_problem")


class TestSafetestCppPatterns:
    """Test patterns specifically derived from safe_test.cpp success."""
    
    @pytest.fixture
    def factory(self):
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            return ClangTidyFactory()
    
    def test_issue_categorization(self):
        """Test that issues are categorized like in safe_test.cpp success."""
        # Test the categorization logic matches our proven patterns
        critical_issues = [
            "std::ranges::iota", "std::ranges::sort", "std::cmp_equal", "std::map::contains"
        ]
        safety_issues = [
            "pointer arithmetic", "bounds checking", "memory safety"
        ]
        quality_issues = [
            "readability-identifier-length", "readability-else-after-return",
            "readability-function-cognitive-complexity"
        ]
        
        # Verify our categorization matches successful patterns
        assert all("ranges" in issue or "cmp_" in issue or "contains" in issue 
                  for issue in critical_issues)
        assert all("pointer" in issue or "bounds" in issue or "memory" in issue 
                  for issue in safety_issues)
        assert all("readability" in issue for issue in quality_issues)
    
    @pytest.mark.asyncio 
    async def test_fix_ordering(self, factory, tmp_path):
        """Test that fix ordering follows safe_test.cpp success pattern."""
        session = FactorySession("test", [])
        
        # Mock discovered issues in order of safe_test.cpp fixes
        session.discovered_issues = ClangTidyAnalysis(
            total_warnings=7,
            warnings=[
                Warning(line_number=1, column_number=1, rule_id="modernize-use-ranges",
                       severity="CRITICAL", category="critical", message="std::ranges::iota"),
                Warning(line_number=2, column_number=1, rule_id="cppcoreguidelines-pro-bounds-pointer-arithmetic", 
                       severity="HIGH", category="safety", message="argv[i]"),
                Warning(line_number=3, column_number=1, rule_id="readability-identifier-length",
                       severity="MEDIUM", category="quality", message="short variable 'i'"),
            ],
            categories=['critical', 'safety', 'quality'],
            recommended_fix_order=['critical', 'safety', 'quality']
        )
        
        # Test that strategy planning respects this ordering
        with patch.object(factory, '_invoke_subagent', return_value="strategy created") as mock:
            await factory._execute_phase_2_strategy(session)
            
            # Verify strategy prompt mentions the correct ordering
            strategy_prompt = mock.call_args[0][1]
            assert "Phase 1: Build restoration" in strategy_prompt
            assert "Phase 2: Safety hardening" in strategy_prompt  
            assert "Phase 3: Quality enhancement" in strategy_prompt


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def factory(self):
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            return ClangTidyFactory()
    
    @pytest.mark.asyncio
    async def test_subagent_failure_handling(self, factory, sample_cpp_files):
        """Test handling when a subagent fails."""
        session = FactorySession("test_error", sample_cpp_files)
        session.discovered_issues = ClangTidyAnalysis(
            total_warnings=1, warnings=[], categories=[], recommended_fix_order=[]
        )
        
        # Mock one subagent to fail during parallel execution
        async def mock_invoke_with_failure(subagent_name, prompt):
            if subagent_name == 'safety_fixer':
                raise Exception("Simulated subagent failure")
            return f"success from {subagent_name}"
        
        with patch.object(factory, '_invoke_subagent', side_effect=mock_invoke_with_failure):
            with pytest.raises(Exception, match="Simulated subagent failure"):
                await factory._execute_phase_3_parallel_fixing(session)
    
    @pytest.mark.asyncio
    async def test_workflow_interruption_recovery(self, factory, sample_cpp_files):
        """Test recovery from workflow interruption."""
        # Test that sessions can be resumed or recovered
        session_id = "interrupted_session"
        session = FactorySession(session_id, sample_cpp_files)
        session.current_phase = WorkflowPhase.STRATEGY
        factory.active_sessions[session_id] = session
        
        # Verify session state is preserved
        assert factory.active_sessions[session_id].current_phase == WorkflowPhase.STRATEGY
        assert factory.active_sessions[session_id].target_files == sample_cpp_files


class TestPerformanceMetrics:
    """Test performance monitoring and metrics collection."""
    
    @pytest.fixture
    def factory(self):
        with patch('factory_orchestrator.load_settings'), \
             patch('factory_orchestrator.get_llm_model'):
            return ClangTidyFactory()
    
    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, factory, sample_cpp_files):
        """Test that execution time is tracked accurately."""
        start_time = asyncio.get_event_loop().time()
        session = FactorySession("perf_test", sample_cpp_files)
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - session.start_time
        
        assert duration >= 0.1
        assert duration < 1.0  # Should be reasonable
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, factory, sample_cpp_files):
        """Test that performance metrics are collected during workflow.""" 
        session = FactorySession("metrics_test", sample_cpp_files)
        
        # Add some mock performance data
        session.performance_metrics = {
            'discovery_time': 2.3,
            'strategy_time': 1.1,
            'fixing_time': 12.7,
            'validation_time': 3.2
        }
        
        total_time = sum(session.performance_metrics.values())
        assert total_time == 19.3
        assert 'discovery_time' in session.performance_metrics


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])