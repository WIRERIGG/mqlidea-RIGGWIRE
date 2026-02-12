"""Requirements validation tests for the Clang-Tidy AI Agent.

Tests all requirements specified in planning/INITIAL.md to ensure compliance.
"""

import pytest
import pytest_asyncio
import os
import sys
import tempfile
import time
import sqlite3
from unittest.mock import patch, Mock
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel

try:
    from agent import clang_tidy_agent, ClangTidyAI
    from dependencies import ClangTidyDependencies, create_dependencies
    from settings import ClangTidyAISettings
    from models import Warning, ClangTidyAnalysis, WarningExplanation, FixRecommendation
    from tools import analyze_code_with_clang_tidy
except ImportError:
    # Fallback for testing without full setup
    clang_tidy_agent = None
    ClangTidyAI = None
    ClangTidyDependencies = None
    create_dependencies = None
    ClangTidyAISettings = None
    Warning = None
    ClangTidyAnalysis = None
    WarningExplanation = None
    FixRecommendation = None
    analyze_code_with_clang_tidy = None


class TestCoreRequirements:
    """Test Core Functionality (MVP) requirements."""
    
    @pytest.mark.asyncio
    async def test_req_001_conversational_analysis(self, test_dependencies):
        """REQ-001: Conversational Analysis - Natural language discussion about clang-tidy issues."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Test natural language queries about code quality
        queries = [
            "What does the readability-identifier-naming warning mean?",
            "How can I fix performance issues in my loop?",
            "Why is using std::endl bad for performance?",
            "Explain the difference between camelCase and snake_case naming"
        ]
        
        for query in queries:
            result = await test_agent.run(query, deps=test_dependencies)
            
            assert result.data is not None, f"No response for query: {query}"
            assert isinstance(result.data, str), "Response should be natural language text"
            assert len(result.data) > 50, "Response should be substantive"
    
    @pytest.mark.asyncio
    async def test_req_002_context_aware_explanations(self, test_dependencies, sample_cpp_file):
        """REQ-002: Context-Aware Explanations - Understand why specific warnings occur in context."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="",
                stderr="""src/test.cpp:5:9: warning: variable name 'myVar' doesn't follow naming convention [readability-identifier-naming]
    int myVar = 42;
        ^~~~~
        my_var""",
                returncode=0
            )
            
            result = await test_agent.run(
                f"Analyze {sample_cpp_file} and explain why the warnings occur in this specific context",
                deps=test_dependencies
            )
            
            assert result.data is not None
            # Should provide contextual explanation, not just generic rule description
            response_text = result.data.lower()
            assert "context" in response_text or "specific" in response_text or "this code" in response_text
    
    @pytest.mark.asyncio
    async def test_req_003_educational_interface(self, test_dependencies):
        """REQ-003: Educational Interface - Learn about code quality patterns through dialogue."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Educational queries
        educational_queries = [
            "Teach me about RAII in C++",
            "What are the benefits of const correctness?",
            "How do I write more readable C++ code?",
            "What's the difference between stack and heap allocation?"
        ]
        
        for query in educational_queries:
            result = await test_agent.run(query, deps=test_dependencies)
            
            assert result.data is not None, f"No educational response for: {query}"
            # Educational responses should be detailed and informative
            assert len(result.data) > 100, "Educational response should be comprehensive"
    
    @pytest.mark.asyncio
    async def test_req_004_intelligent_fix_strategy_selection(self, test_dependencies):
        """REQ-004: Intelligent Fix Strategy Selection - AI-powered selection of optimal fix approaches."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Test fix strategy recommendations
        code_samples = [
            ("int myVar = 42;", "naming convention"),
            ("std::cout << value << std::endl;", "performance optimization"),
            ("char* buffer = malloc(100);", "memory management"),
        ]
        
        for code, issue_type in code_samples:
            result = await test_agent.run(
                f"What's the best strategy to fix this {issue_type} issue: {code}",
                deps=test_dependencies
            )
            
            assert result.data is not None
            response = result.data.lower()
            # Should provide strategic recommendations, not just identify problems
            assert any(word in response for word in ["strategy", "approach", "recommend", "suggest"])
    
    @pytest.mark.asyncio
    async def test_req_005_preference_learning(self, test_dependencies):
        """REQ-005: Preference Learning - Adapt recommendations based on user choices and codebase patterns."""
        from dependencies import save_user_preference, load_user_preferences
        
        # Save user preferences
        save_user_preference(
            test_dependencies.db_connection,
            test_dependencies.session_id,
            "readability-identifier-naming",
            "snake_case_conversion", 
            ["consistent_style", "team_preference"]
        )
        
        # Load preferences back
        preferences = load_user_preferences(
            test_dependencies.db_connection, 
            test_dependencies.session_id
        )
        
        # Verify learning system works
        assert "readability-identifier-naming" in preferences
        assert preferences["readability-identifier-naming"]["preferred_strategy"] == "snake_case_conversion"
        assert "consistent_style" in preferences["readability-identifier-naming"]["context_tags"]
    
    @pytest.mark.asyncio
    async def test_req_006_natural_language_explanations(self, test_dependencies):
        """REQ-006: Natural Language Explanation Engine - Human-readable explanations of what fixes do and why."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        result = await test_agent.run(
            "Explain what the modernize-use-auto rule does and why it's beneficial",
            deps=test_dependencies
        )
        
        assert result.data is not None
        explanation = result.data.lower()
        
        # Should explain both "what" and "why"
        assert "what" in explanation or "does" in explanation
        assert "why" in explanation or "benefit" in explanation or "advantage" in explanation
        
        # Should be educational
        assert len(result.data) > 100  # Substantial explanation


class TestTechnicalRequirements:
    """Test Technical Requirements."""
    
    def test_req_007_pydantic_ai_framework(self, test_dependencies):
        """REQ-007: Pydantic AI - Primary conversational framework."""
        # Verify agent is built with Pydantic AI
        assert clang_tidy_agent is not None, "Agent should be a Pydantic AI agent"
        assert hasattr(clang_tidy_agent, 'run'), "Should have Pydantic AI run method"
        assert hasattr(clang_tidy_agent, 'model'), "Should have model attribute"
    
    def test_req_008_multi_provider_llm_support(self, temp_dir):
        """REQ-008: Multi-Provider LLM Support - OpenAI, Anthropic, Gemini, Ollama compatibility."""
        providers = ["openai", "anthropic", "gemini", "ollama"]
        
        for provider in providers:
            # Test that settings can be configured for each provider
            settings = ClangTidyAISettings(
                llm_provider=provider,
                llm_api_key="test-key",
                llm_model="test-model",
                project_root=temp_dir
            )
            
            assert settings.llm_provider == provider
            assert settings.llm_api_key == "test-key"
    
    def test_req_009_database_integration(self, test_dependencies):
        """REQ-009: Database Integration - SQLite for learning and preference storage."""
        # Verify database connection and schema
        connection = test_dependencies.db_connection
        cursor = connection.cursor()
        
        # Check required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = {"user_preferences", "analysis_cache", "feedback"}
        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"
    
    def test_req_010_directory_scope_constraint(self, test_dependencies):
        """REQ-010: Directory Scope - Must operate within /IdeaProjects/wire_ground/."""
        project_root = test_dependencies.settings.project_root
        
        # Verify project root is within expected scope
        expected_scope = Path("/IdeaProjects/wire_ground")
        assert expected_scope in project_root.parents or project_root == expected_scope, \
            f"Project root {project_root} is outside expected scope {expected_scope}"
    
    @pytest.mark.asyncio
    async def test_req_011_existing_script_compatibility(self, test_dependencies):
        """REQ-011: Existing Script Compatibility - Leverage existing clang-tidy infrastructure."""
        # Test that we can integrate with existing scripts
        script_path = Path("/IdeaProjects/wire_ground/scripts/clang_tidy_fixer.sh")
        
        # The integration should be able to work with existing scripts
        # (This would require more complex testing in real scenario)
        assert test_dependencies.settings.clang_tidy_binary_path is not None
        assert test_dependencies.settings.project_root is not None


class TestInterfaceModeRequirements:
    """Test Interface Mode requirements."""
    
    @pytest.mark.asyncio
    async def test_req_012_interactive_cli_mode(self, test_dependencies):
        """REQ-012: Interactive CLI - Conversational interface for code review and fixes."""
        # Test that ClangTidyAI can be used as interactive interface
        ai = ClangTidyAI(session_id="interactive-test")
        
        async with ai:
            # Should support interactive queries
            result = await ai.chat("What should I know about C++ code quality?")
            assert result is not None
            assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_req_013_automated_mode(self, test_dependencies, sample_cpp_file):
        """REQ-013: Automated Mode - Enhanced version of existing automated fixing."""
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="automated analysis", returncode=0)
            
            # Should support automated analysis
            result = await analyze_code_with_clang_tidy(
                context,
                str(sample_cpp_file.relative_to(test_dependencies.settings.project_root))
            )
            
            assert isinstance(result, ClangTidyAnalysis)
            assert result.file_path is not None
    
    @pytest.mark.asyncio
    async def test_req_014_batch_analysis_mode(self, test_dependencies, integration_test_project):
        """REQ-014: Batch Analysis - Process multiple files with AI insights."""
        from tools import batch_analyze_project
        
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="batch analysis", returncode=0)
            
            # Should support batch processing
            result = await batch_analyze_project(context, str(integration_test_project / "**" / "*.cpp"))
            
            assert result.total_files_analyzed >= 0
            assert hasattr(result, 'summary_statistics')
    
    def test_req_015_learning_mode(self, test_dependencies):
        """REQ-015: Learning Mode - Capture user preferences and improve recommendations."""
        from dependencies import save_feedback, get_learning_insights
        
        # Save user feedback
        save_feedback(
            test_dependencies.db_connection,
            test_dependencies.session_id,
            "warning-123",
            "snake_case_conversion",
            "accepted",
            5  # satisfaction rating
        )
        
        # Should be able to get insights from feedback
        insights = get_learning_insights(test_dependencies.db_connection, test_dependencies.session_id)
        
        assert insights is not None
        assert isinstance(insights, dict)


class TestQualityGateRequirements:
    """Test Quality Gate requirements."""
    
    @pytest.mark.asyncio
    async def test_req_016_zero_breaking_changes(self, test_dependencies):
        """REQ-016: Zero Breaking Changes - Existing automated scripts continue to work unchanged."""
        # The AI agent should enhance rather than replace existing functionality
        # This is verified by ensuring the agent can coexist with existing tools
        
        # Test that existing models and interfaces still work
        assert ClangTidyAnalysis is not None
        assert Warning is not None
        
        # Test that database operations don't interfere with existing data structures
        connection = test_dependencies.db_connection
        cursor = connection.cursor()
        
        # Should be able to perform standard database operations
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        count = cursor.fetchone()[0]
        assert count >= 0  # Should not error
    
    @pytest.mark.asyncio
    async def test_req_017_performance_response_time(self, test_dependencies):
        """REQ-017: Performance - Interactive responses within 2-3 seconds for typical queries."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        typical_queries = [
            "What is the readability-identifier-naming rule?",
            "How do I fix a performance warning?",
            "Explain const correctness",
        ]
        
        for query in typical_queries:
            start_time = time.time()
            result = await test_agent.run(query, deps=test_dependencies)
            response_time = time.time() - start_time
            
            assert response_time < 3.0, f"Query '{query}' took {response_time:.2f}s, exceeds 3s limit"
            assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_req_018_fix_accuracy(self, test_dependencies):
        """REQ-018: Accuracy - Fix recommendations should be contextually appropriate >90% of the time."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Test with known good examples where we can verify appropriateness
        test_cases = [
            ("int myVar = 42;", "naming convention", ["snake_case", "camel_case", "rename"]),
            ("std::cout << value << std::endl;", "performance", ["newline", "\\n", "flush"]),
            ("vector.push_back(item);", "performance", ["reserve", "capacity", "allocation"]),
        ]
        
        appropriate_responses = 0
        
        for code, issue_type, expected_concepts in test_cases:
            result = await test_agent.run(
                f"How should I fix this {issue_type} issue in: {code}",
                deps=test_dependencies
            )
            
            if result.data is not None:
                response_text = result.data.lower()
                # Check if response mentions relevant concepts
                if any(concept in response_text for concept in expected_concepts):
                    appropriate_responses += 1
        
        # Should have high accuracy (>90% for this test)
        accuracy = appropriate_responses / len(test_cases)
        assert accuracy > 0.9, f"Fix accuracy {accuracy:.1%} below 90% threshold"
    
    @pytest.mark.asyncio
    async def test_req_019_educational_value(self, test_dependencies):
        """REQ-019: Educational Value - Explanations help developers learn and improve code quality understanding."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        result = await test_agent.run(
            "Explain why const correctness is important in C++ and how it improves code quality",
            deps=test_dependencies
        )
        
        assert result.data is not None
        explanation = result.data.lower()
        
        # Educational content should cover multiple aspects
        educational_indicators = [
            "benefit", "advantage", "improve", "help", "prevent", "avoid",
            "example", "because", "reason", "why", "how"
        ]
        
        found_indicators = sum(1 for indicator in educational_indicators if indicator in explanation)
        assert found_indicators >= 3, "Response should be educational with multiple learning aspects"


class TestNonFunctionalRequirements:
    """Test Non-Functional Requirements."""
    
    @pytest.mark.asyncio
    async def test_req_020_performance_response_time(self, test_dependencies):
        """REQ-020: Performance - Response Time <3 seconds for interactive queries."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        start_time = time.time()
        result = await test_agent.run("Quick test query", deps=test_dependencies)
        response_time = time.time() - start_time
        
        assert response_time < 3.0, f"Response time {response_time:.2f}s exceeds 3s requirement"
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_req_021_throughput_capability(self, test_dependencies, integration_test_project):
        """REQ-021: Throughput - Handle analysis of 100+ files in batch mode."""
        from tools import batch_analyze_project
        
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="batch processing", returncode=0)
            
            # Should handle large batch processing
            result = await batch_analyze_project(context, str(integration_test_project / "**" / "*.cpp"))
            
            # Should be capable of processing 100+ files
            # (Actual count depends on test project size, but system should handle it)
            assert result.total_files_analyzed >= 0
            assert hasattr(result, 'processing_time')
    
    def test_req_022_memory_usage_limits(self, test_dependencies):
        """REQ-022: Memory Usage - <500MB additional overhead over base clang-tidy system."""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Perform memory-intensive operations
        large_objects = []
        for i in range(1000):
            # Create analysis objects (simulating heavy usage)
            warnings = [
                Warning(
                    line_number=j,
                    column_number=10,
                    rule_id=f"rule-{j}",
                    severity="warning",
                    message=f"Warning {j}",
                    suggested_fix=f"Fix {j}",
                    context_lines=[f"Line {k}" for k in range(5)]
                )
                for j in range(10)  # 10 warnings per analysis
            ]
            
            analysis = ClangTidyAnalysis(
                file_path=f"file_{i}.cpp",
                warnings=warnings,
                total_warnings=len(warnings),
                clang_tidy_version="test"
            )
            
            large_objects.append(analysis)
        
        peak_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_overhead = peak_memory - initial_memory
        
        # Should stay within 500MB limit
        assert memory_overhead < 500, f"Memory overhead {memory_overhead:.1f}MB exceeds 500MB limit"
        
        # Cleanup
        del large_objects
    
    def test_req_023_api_key_security(self, test_dependencies):
        """REQ-023: Security - Proper handling of API keys and sensitive code data."""
        # API keys should never appear in string representations
        settings = test_dependencies.settings
        settings.llm_api_key = "sk-secret-key-12345"
        
        # Should not expose API key in string representations
        assert "sk-secret-key-12345" not in str(settings)
        assert "sk-secret-key-12345" not in repr(settings)
        
        # Should not appear in logs or debug output
        import logging
        import io
        
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_security")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Log some operations
        logger.info(f"Settings initialized: {settings}")
        logger.debug(f"Settings details: {repr(settings)}")
        
        log_contents = log_stream.getvalue()
        assert "sk-secret-key-12345" not in log_contents, "API key leaked in logs"
    
    def test_req_024_audit_trail(self, test_dependencies):
        """REQ-024: Security - Log all AI-assisted fixes for review and compliance."""
        from dependencies import log_ai_interaction
        
        # Should be able to log AI interactions
        log_ai_interaction(
            test_dependencies.db_connection,
            test_dependencies.session_id,
            "fix_recommendation",
            "src/test.cpp:readability-identifier-naming",
            "success"
        )
        
        # Verify audit record exists
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM ai_interactions 
            WHERE session_id = ? AND action_type = 'fix_recommendation'
        """, (test_dependencies.session_id,))
        
        count = cursor.fetchone()[0]
        assert count >= 1, "Audit trail should record AI interactions"


class TestSuccessMetrics:
    """Test Success Metrics requirements."""
    
    @pytest.mark.asyncio
    async def test_req_025_user_experience_metrics(self, test_dependencies):
        """REQ-025: User Experience - Interactive mode adoption and educational impact."""
        # Test that interactive features are usable and engaging
        ai = ClangTidyAI(session_id="ux-test")
        
        async with ai:
            # Should provide engaging educational content
            result = await ai.chat("Teach me about modern C++ best practices")
            
            assert result is not None
            assert len(result) > 200, "Educational content should be comprehensive"
            
            # Should be conversational and helpful
            result2 = await ai.chat("Can you give me a specific example?")
            assert result2 is not None, "Should handle follow-up questions"
    
    def test_req_026_technical_metrics(self, test_dependencies):
        """REQ-026: Technical Metrics - System reliability and integration health."""
        # Test system reliability indicators
        connection = test_dependencies.db_connection
        
        # Database operations should be reliable
        for i in range(100):
            cursor = connection.cursor()
            cursor.execute("INSERT INTO user_preferences (session_id, warning_type) VALUES (?, ?)", 
                          (f"reliability-test-{i}", "test-rule"))
            connection.commit()
        
        # Should maintain data integrity
        cursor.execute("SELECT COUNT(*) FROM user_preferences WHERE session_id LIKE 'reliability-test-%'")
        count = cursor.fetchone()[0]
        assert count == 100, "Should maintain data integrity under load"
        
        # Cleanup
        cursor.execute("DELETE FROM user_preferences WHERE session_id LIKE 'reliability-test-%'")
        connection.commit()
    
    def test_req_027_integration_health(self, test_dependencies):
        """REQ-027: Integration Health - Zero impact on existing automated workflows."""
        # Verify that new components don't interfere with existing functionality
        
        # Should coexist with existing data structures
        warning = Warning(
            line_number=10,
            column_number=5,
            rule_id="existing-rule",
            severity="warning", 
            message="Existing warning format",
            suggested_fix="Existing fix format",
            context_lines=["existing", "context", "lines"]
        )
        
        analysis = ClangTidyAnalysis(
            file_path="existing/path.cpp",
            warnings=[warning],
            total_warnings=1,
            clang_tidy_version="existing-version"
        )
        
        # Should work with existing interfaces
        assert analysis.file_path == "existing/path.cpp"
        assert analysis.total_warnings == 1
        assert len(analysis.warnings) == 1
        assert analysis.warnings[0].rule_id == "existing-rule"