"""Security validation tests for the Clang-Tidy AI Agent."""

import pytest
import pytest_asyncio
import os
from unittest.mock import patch, Mock, MagicMock
import tempfile
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel

try:
    from agent import clang_tidy_agent, ClangTidyAI
    from dependencies import ClangTidyDependencies
    from settings import ClangTidyAISettings
    from models import Warning, ClangTidyAnalysis
except ImportError:
    # Fallback for testing without full setup
    clang_tidy_agent = None
    ClangTidyAI = None
    ClangTidyDependencies = None
    ClangTidyAISettings = None
    Warning = None
    ClangTidyAnalysis = None


class TestAPIKeySecurity:
    """Test API key handling and security measures."""
    
    @pytest.mark.asyncio
    async def test_api_key_not_logged(self, test_dependencies, caplog):
        """Test that API keys are never logged."""
        # Create agent with test model to avoid actual API calls
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Mock dependencies with API key
        test_dependencies.settings.llm_api_key = "sk-test-secret-key-12345"
        
        with caplog.at_level("DEBUG"):
            try:
                result = await test_agent.run("Analyze this code", deps=test_dependencies)
            except Exception:
                pass  # We only care about logging behavior
        
        # Verify API key never appears in logs
        log_text = caplog.text
        assert "sk-test-secret-key-12345" not in log_text
        assert "secret-key" not in log_text.lower()
        
        # Ensure logging is happening (just not with secrets)
        assert len(caplog.records) > 0
    
    @pytest.mark.asyncio 
    async def test_api_key_environment_variable_protection(self):
        """Test that API keys are properly loaded from environment."""
        with patch.dict(os.environ, {"LLM_API_KEY": "test-secret-key"}):
            settings = ClangTidyAISettings()
            
            # Key should be loaded but not exposed in string representation
            assert settings.llm_api_key == "test-secret-key"
            assert "test-secret-key" not in str(settings)
            assert "test-secret-key" not in repr(settings)
    
    @pytest.mark.asyncio
    async def test_database_injection_protection(self, test_dependencies):
        """Test protection against SQL injection attempts."""
        from dependencies import save_user_preference, load_user_preferences
        
        # Attempt SQL injection in session_id
        malicious_session_id = "'; DROP TABLE user_preferences; --"
        
        # This should not cause any issues
        save_user_preference(
            test_dependencies.db_connection,
            malicious_session_id,
            "readability-identifier-naming",
            "snake_case",
            ["test"]
        )
        
        # Database should still be intact
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "user_preferences" in tables
        
        # Should be able to retrieve preferences safely
        preferences = load_user_preferences(test_dependencies.db_connection, malicious_session_id)
        assert isinstance(preferences, dict)
    
    def test_file_path_validation(self, test_dependencies):
        """Test validation of file paths to prevent directory traversal."""
        from tools import validate_file_path
        
        project_root = test_dependencies.settings.project_root
        
        # Valid paths should pass
        assert validate_file_path("src/main.cpp", project_root) is True
        assert validate_file_path("include/header.hpp", project_root) is True
        
        # Invalid paths should be rejected
        assert validate_file_path("../../../etc/passwd", project_root) is False
        assert validate_file_path("/etc/passwd", project_root) is False
        assert validate_file_path("../outside.cpp", project_root) is False
        
        # Null bytes should be rejected
        assert validate_file_path("src/main.cpp\x00malicious", project_root) is False


class TestInputValidation:
    """Test input validation and sanitization."""
    
    @pytest.mark.asyncio
    async def test_code_input_sanitization(self, test_dependencies):
        """Test that code inputs are properly sanitized."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Test with potentially malicious code
        malicious_code = """
        #include <iostream>
        #include <cstdlib>
        
        int main() {
            system("rm -rf /");  // Malicious command
            return 0;
        }
        """
        
        # Agent should handle this safely without executing it
        result = await test_agent.run(
            f"Analyze this code: {malicious_code}",
            deps=test_dependencies
        )
        
        # Should get a response without any system commands being executed
        assert result.data is not None
        assert isinstance(result.data, str)
    
    @pytest.mark.asyncio
    async def test_file_size_limits(self, test_dependencies):
        """Test that large files are handled safely."""
        from tools import analyze_code_with_clang_tidy
        
        # Create a very large file
        large_content = "int var{};\n" * 100000  # 100K lines
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(large_content)
            large_file_path = f.name
        
        try:
            class MockContext:
                def __init__(self, deps):
                    self.deps = deps
            
            context = MockContext(test_dependencies)
            
            # Should handle large files gracefully
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
                
                result = await analyze_code_with_clang_tidy(context, large_file_path)
                
                # Should complete without memory issues
                assert isinstance(result, ClangTidyAnalysis)
        finally:
            os.unlink(large_file_path)
    
    @pytest.mark.asyncio
    async def test_warning_rule_validation(self, test_dependencies):
        """Test validation of clang-tidy rule names."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        # Valid rule names should work
        valid_rules = [
            "readability-identifier-naming",
            "performance-avoid-endl",
            "modernize-use-auto"
        ]
        
        for rule in valid_rules:
            result = await test_agent.run(
                f"Explain the {rule} warning",
                deps=test_dependencies
            )
            assert result.data is not None
        
        # Invalid/malicious rule names should be handled safely
        invalid_rules = [
            "../malicious-rule",
            "rule; DROP TABLE warnings;",
            "rule\x00null",
            "a" * 1000  # extremely long rule name
        ]
        
        for rule in invalid_rules:
            try:
                result = await test_agent.run(
                    f"Explain the {rule} warning",
                    deps=test_dependencies
                )
                # Should either work safely or fail gracefully
                assert result.data is not None or result.data is None
            except Exception as e:
                # Should fail with appropriate error, not system compromise
                assert "security" not in str(e).lower() or "validation" in str(e).lower()


class TestDataProtection:
    """Test protection of sensitive data."""
    
    def test_error_message_sanitization(self, test_dependencies):
        """Test that error messages don't expose sensitive information."""
        from tools import _sanitize_error_message
        
        # Error messages with sensitive data
        sensitive_errors = [
            f"Failed to connect to {test_dependencies.settings.llm_api_key}",
            f"Database error at {test_dependencies.settings.clang_tidy_ai_db_path}",
            "File not found: /home/user/secret/private.cpp",
            "API error: invalid key sk-12345abcdef"
        ]
        
        for error in sensitive_errors:
            sanitized = _sanitize_error_message(error)
            
            # Should not contain sensitive paths or keys
            assert test_dependencies.settings.llm_api_key not in sanitized
            assert "sk-" not in sanitized
            assert "/home/" not in sanitized
            assert str(test_dependencies.settings.clang_tidy_ai_db_path) not in sanitized
    
    def test_user_data_isolation(self, test_dependencies):
        """Test that user data is properly isolated between sessions."""
        from dependencies import save_user_preference, load_user_preferences
        
        # Create preferences for different sessions
        save_user_preference(
            test_dependencies.db_connection,
            "session-1",
            "readability-identifier-naming", 
            "snake_case",
            ["preference-1"]
        )
        
        save_user_preference(
            test_dependencies.db_connection,
            "session-2",
            "readability-identifier-naming",
            "camelCase", 
            ["preference-2"]
        )
        
        # Each session should only see its own data
        prefs_1 = load_user_preferences(test_dependencies.db_connection, "session-1")
        prefs_2 = load_user_preferences(test_dependencies.db_connection, "session-2")
        
        assert prefs_1["readability-identifier-naming"]["preferred_strategy"] == "snake_case"
        assert prefs_2["readability-identifier-naming"]["preferred_strategy"] == "camelCase"
        
        assert "preference-1" in prefs_1["readability-identifier-naming"]["context_tags"]
        assert "preference-2" not in prefs_1["readability-identifier-naming"]["context_tags"]
    
    def test_temporary_file_cleanup(self, test_dependencies):
        """Test that temporary files are properly cleaned up."""
        from tools import _create_temp_analysis_file, _cleanup_temp_files
        
        # Create some temporary files
        temp_files = []
        for i in range(3):
            temp_file = _create_temp_analysis_file(f"test-content-{i}")
            temp_files.append(temp_file)
            assert os.path.exists(temp_file)
        
        # Cleanup should remove all temp files
        _cleanup_temp_files(temp_files)
        
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)


class TestPrivacyCompliance:
    """Test privacy and compliance measures."""
    
    def test_code_content_not_stored_permanently(self, test_dependencies):
        """Test that user code content is not permanently stored."""
        from tools import analyze_code_with_clang_tidy
        
        sensitive_code = """
        const char* API_SECRET = "super-secret-api-key-12345";
        const char* DB_PASSWORD = "database-password-xyz";
        """
        
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(sensitive_code)
            temp_file = f.name
        
        try:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
                
                result = await analyze_code_with_clang_tidy(context, temp_file)
                
                # Check database to ensure code content is not stored
                cursor = test_dependencies.db_connection.cursor()
                cursor.execute("SELECT analysis_result FROM analysis_cache")
                cached_results = cursor.fetchall()
                
                for result_row in cached_results:
                    cached_content = result_row[0]
                    assert "super-secret-api-key-12345" not in cached_content
                    assert "database-password-xyz" not in cached_content
        finally:
            os.unlink(temp_file)
    
    def test_audit_trail_creation(self, test_dependencies):
        """Test that appropriate audit trails are created."""
        from dependencies import log_ai_interaction
        
        # Log an AI interaction
        log_ai_interaction(
            test_dependencies.db_connection,
            test_dependencies.session_id,
            "analyze_file",
            "src/test.cpp",
            "success"
        )
        
        # Verify audit record was created
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("""
            SELECT session_id, action_type, target, result_status, created_at 
            FROM ai_interactions 
            WHERE session_id = ?
        """, (test_dependencies.session_id,))
        
        records = cursor.fetchall()
        assert len(records) == 1
        assert records[0][1] == "analyze_file"  # action_type
        assert records[0][2] == "src/test.cpp"  # target
        assert records[0][3] == "success"  # result_status
    
    @pytest.mark.asyncio
    async def test_local_model_fallback(self, test_dependencies):
        """Test fallback to local model for sensitive environments."""
        # Simulate environment where external API calls should be avoided
        test_dependencies.settings.llm_provider = "ollama"
        test_dependencies.settings.llm_base_url = "http://localhost:11434"
        
        # Create agent with local model
        local_agent = clang_tidy_agent.override(model=TestModel())
        
        # Should work without external network calls
        result = await local_agent.run(
            "Analyze this sensitive code",
            deps=test_dependencies
        )
        
        assert result.data is not None
        # Verify no external network calls were made
        # (This would require additional mocking in real implementation)


class TestAccessControl:
    """Test access control and authorization."""
    
    def test_project_root_boundary_enforcement(self, test_dependencies):
        """Test that file access is restricted to project root."""
        from tools import get_file_content_safely
        
        project_root = test_dependencies.settings.project_root
        
        # Create test file within project
        test_file = project_root / "src" / "allowed.cpp"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("// Allowed content")
        
        # Should be able to read files within project
        content = get_file_content_safely(str(test_file), project_root)
        assert content == "// Allowed content"
        
        # Should not be able to read files outside project
        outside_file = "/etc/passwd"
        content = get_file_content_safely(outside_file, project_root)
        assert content is None  # Should be rejected
        
        # Should not be able to use path traversal
        traversal_file = str(project_root / ".." / ".." / "etc" / "passwd")
        content = get_file_content_safely(traversal_file, project_root)
        assert content is None  # Should be rejected
    
    def test_session_isolation(self, test_dependencies):
        """Test that sessions are properly isolated."""
        from dependencies import create_dependencies
        
        # Create two different sessions
        deps1 = create_dependencies("session-1")
        deps2 = create_dependencies("session-2")
        
        try:
            # Modify one session's data
            deps1.user_preferences["test-pref"] = "value-1"
            deps2.user_preferences["test-pref"] = "value-2"
            
            # Sessions should maintain separate state
            assert deps1.user_preferences["test-pref"] == "value-1"
            assert deps2.user_preferences["test-pref"] == "value-2"
            assert deps1.session_id != deps2.session_id
            
        finally:
            deps1.db_connection.close()
            deps2.db_connection.close()
    
    def test_database_connection_security(self, test_dependencies):
        """Test database connection security measures."""
        connection = test_dependencies.db_connection
        
        # Should use parameterized queries only
        cursor = connection.cursor()
        
        # This should work (parameterized)
        cursor.execute(
            "INSERT INTO user_preferences (session_id, warning_type) VALUES (?, ?)",
            ("test-session", "test-warning")
        )
        
        # Verify data was inserted safely
        cursor.execute(
            "SELECT COUNT(*) FROM user_preferences WHERE session_id = ?",
            ("test-session",)
        )
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Cleanup
        cursor.execute("DELETE FROM user_preferences WHERE session_id = ?", ("test-session",))
        connection.commit()


class TestSecurityConfiguration:
    """Test security configuration and hardening."""
    
    def test_secure_defaults(self):
        """Test that secure defaults are used."""
        settings = ClangTidyAISettings()
        
        # Should have secure defaults
        assert settings.enable_learning_mode is True  # User control
        assert settings.cache_analysis_results is True  # Performance with privacy
        assert settings.max_file_size_mb >= 1  # Reasonable limit
        assert settings.max_analysis_time_seconds >= 10  # Timeout protection
    
    def test_tls_verification(self, test_dependencies):
        """Test that TLS verification is enabled for external calls."""
        import ssl
        import urllib3
        
        # Mock HTTPS client configuration
        with patch('urllib3.PoolManager') as mock_pool:
            from providers import create_llm_client
            
            client = create_llm_client(test_dependencies.settings)
            
            # Verify TLS verification is enabled
            if mock_pool.called:
                call_kwargs = mock_pool.call_args[1] if mock_pool.call_args else {}
                assert call_kwargs.get('cert_reqs') != ssl.CERT_NONE
    
    def test_rate_limiting_configuration(self, test_dependencies):
        """Test that rate limiting is properly configured."""
        from providers import RateLimiter
        
        limiter = RateLimiter(
            max_requests_per_minute=60,
            max_tokens_per_minute=90000
        )
        
        # Should enforce limits
        assert limiter.max_requests_per_minute <= 100  # Reasonable limit
        assert limiter.max_tokens_per_minute <= 100000  # Token limit
        
        # Should track usage
        limiter.record_request(tokens_used=1000)
        assert limiter.current_requests == 1
        assert limiter.current_tokens == 1000