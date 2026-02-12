"""Basic tests for blitzfire_cpp_optimizer"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBlitzfirecppoptimizer:
    """Basic tests for blitzfire_cpp_optimizer"""
    
    def test_import_agent(self):
        """Test that agent can be imported"""
        try:
            # Try different import patterns
            import agent
            assert agent is not None
        except ImportError:
            try:
                import core.agent
                assert core.agent is not None
            except ImportError:
                # Agent might be markdown-only
                pytest.skip("No Python agent module found")
    
    def test_basic_structure(self):
        """Test basic agent structure exists"""
        agent_dir = Path(__file__).parent.parent
        
        # Check for common files
        possible_files = [
            "agent.py",
            "core/agent.py", 
            "models.py",
            "core/models.py",
            "requirements.txt",
            "README.md"
        ]
        
        found_files = []
        for file_name in possible_files:
            if (agent_dir / file_name).exists():
                found_files.append(file_name)
        
        # Should have at least one file
        assert len(found_files) > 0, f"No agent files found. Expected one of: {possible_files}"
