"""
Dependencies and context management for NEVER FAIL BUILD RESOLVER.
"""

import uuid
import logging
import json
import aiofiles
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional

from .settings import BuildResolverSettings, load_settings

logger = logging.getLogger(__name__)


@dataclass
class BuildResolverDependencies:
    """Dependencies for NEVER FAIL BUILD RESOLVER agent."""
    
    # Configuration
    settings: BuildResolverSettings
    
    # State Management
    current_state: str = "IDLE"
    resolution_mode: str = "smart"
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Project Context
    project_path: Optional[Path] = None
    build_path: Optional[Path] = None
    current_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Backup and Rollback
    backup_created: bool = False
    current_checkpoint_id: Optional[str] = None
    rollback_available: bool = False
    
    # Learning System
    resolution_history: List[Dict[str, Any]] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    current_problem_signature: Optional[str] = None
    
    # External Services
    mcp_client: Optional[Any] = None
    archon_project_id: Optional[str] = None
    
    # Runtime Context
    start_time: datetime = field(default_factory=datetime.now)
    execution_timeout: Optional[int] = None
    debug_mode: bool = False
    
    @classmethod
    async def create(cls, settings: Optional[BuildResolverSettings] = None, **overrides):
        """Create dependencies with initialized services."""
        if settings is None:
            settings = load_settings()
        
        # Initialize project paths
        project_path = settings.project_root
        build_path = project_path / settings.build_dir
        
        # Initialize MCP client if enabled
        mcp_client = None
        if settings.mcp_enabled and settings.mcp_server_url:
            try:
                mcp_client = await initialize_mcp_client(settings.mcp_server_url)
                logger.info("MCP client initialized successfully")
            except Exception as e:
                logger.warning(f"MCP client initialization failed: {e}")
        
        # Load learned patterns from persistent storage
        learned_patterns = await load_learned_patterns(settings.state_persistence_dir)
        
        # Load resolution history
        resolution_history = await load_resolution_history(settings.state_persistence_dir)
        
        instance = cls(
            settings=settings,
            project_path=project_path,
            build_path=build_path,
            mcp_client=mcp_client,
            archon_project_id=settings.archon_project_id,
            learned_patterns=learned_patterns,
            resolution_history=resolution_history,
            debug_mode=settings.debug_mode,
            **overrides
        )
        
        logger.info(f"BuildResolverDependencies created with session ID: {instance.session_id}")
        return instance
    
    async def cleanup(self):
        """Cleanup resources and save state."""
        try:
            # Save learned patterns
            await save_learned_patterns(
                self.learned_patterns, 
                self.settings.state_persistence_dir
            )
            
            # Save resolution history
            await save_resolution_history(
                self.resolution_history,
                self.settings.state_persistence_dir
            )
            
            # Cleanup MCP client
            if self.mcp_client:
                await self.mcp_client.close()
                
            logger.info(f"Dependencies cleanup completed for session: {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_resolution_timeout(self) -> int:
        """Get timeout for current resolution mode."""
        return self.settings.get_resolution_timeout(self.resolution_mode)
    
    def update_state(self, new_state: str) -> bool:
        """Update current state with validation."""
        valid_states = {"IDLE", "ANALYZING", "CATEGORIZING", "RESOLVING", "VALIDATING", "LEARNING"}
        if new_state not in valid_states:
            logger.error(f"Invalid state transition attempted: {self.current_state} -> {new_state}")
            return False
        
        logger.info(f"State transition: {self.current_state} -> {new_state}")
        self.current_state = new_state
        return True
    
    def add_error(self, error_data: Dict[str, Any]):
        """Add error to current error list."""
        error_data['timestamp'] = datetime.now().isoformat()
        error_data['session_id'] = self.session_id
        self.current_errors.append(error_data)
    
    def clear_errors(self):
        """Clear current error list."""
        self.current_errors.clear()
    
    def record_resolution_attempt(self, problem_type: str, solution: str, success: bool, duration: float):
        """Record a resolution attempt for learning."""
        resolution_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'problem_type': problem_type,
            'solution': solution,
            'success': success,
            'duration': duration,
            'resolution_mode': self.resolution_mode
        }
        
        self.resolution_history.append(resolution_record)
        
        # Limit history size
        if len(self.resolution_history) > self.settings.resolution_history_size:
            self.resolution_history = self.resolution_history[-self.settings.resolution_history_size:]
    
    def get_success_rate_for_problem_type(self, problem_type: str) -> float:
        """Get success rate for a specific problem type from history."""
        relevant_attempts = [
            attempt for attempt in self.resolution_history
            if attempt.get('problem_type') == problem_type
        ]
        
        if not relevant_attempts:
            return 0.0
        
        successful_attempts = [
            attempt for attempt in relevant_attempts
            if attempt.get('success', False)
        ]
        
        return len(successful_attempts) / len(relevant_attempts)


# Utility functions for persistence
async def load_learned_patterns(state_dir: Path) -> Dict[str, Any]:
    """Load learned patterns from persistent storage."""
    patterns_file = state_dir / "learned_patterns.json"
    try:
        if patterns_file.exists():
            async with aiofiles.open(patterns_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to load learned patterns: {e}")
    
    return {}


async def save_learned_patterns(patterns: Dict[str, Any], state_dir: Path):
    """Save learned patterns to persistent storage."""
    patterns_file = state_dir / "learned_patterns.json"
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(patterns_file, 'w') as f:
            await f.write(json.dumps(patterns, indent=2))
        logger.debug(f"Saved {len(patterns)} learned patterns")
    except Exception as e:
        logger.error(f"Failed to save learned patterns: {e}")


async def load_resolution_history(state_dir: Path) -> List[Dict[str, Any]]:
    """Load resolution history from persistent storage."""
    history_file = state_dir / "resolution_history.json"
    try:
        if history_file.exists():
            async with aiofiles.open(history_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
    except Exception as e:
        logger.warning(f"Failed to load resolution history: {e}")
    
    return []


async def save_resolution_history(history: List[Dict[str, Any]], state_dir: Path):
    """Save resolution history to persistent storage."""
    history_file = state_dir / "resolution_history.json"
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(history_file, 'w') as f:
            await f.write(json.dumps(history, indent=2))
        logger.debug(f"Saved resolution history with {len(history)} entries")
    except Exception as e:
        logger.error(f"Failed to save resolution history: {e}")


async def initialize_mcp_client(mcp_server_url: str) -> Optional[Any]:
    """Initialize MCP client connection."""
    # This would be implemented when MCP client library is available
    # For now, return None to indicate MCP is not available
    logger.warning("MCP client initialization not yet implemented")
    return None


# State machine validation
VALID_STATES = {
    "IDLE", "ANALYZING", "CATEGORIZING", 
    "RESOLVING", "VALIDATING", "LEARNING"
}

STATE_TRANSITIONS = {
    "IDLE": ["ANALYZING"],
    "ANALYZING": ["CATEGORIZING", "IDLE"],
    "CATEGORIZING": ["RESOLVING", "IDLE"],
    "RESOLVING": ["VALIDATING", "EMERGENCY", "IDLE"],
    "VALIDATING": ["LEARNING", "RESOLVING", "IDLE"],
    "LEARNING": ["IDLE"]
}


def validate_state_transition(current_state: str, new_state: str) -> bool:
    """Validate if state transition is allowed."""
    if current_state not in STATE_TRANSITIONS:
        return False
    return new_state in STATE_TRANSITIONS[current_state]