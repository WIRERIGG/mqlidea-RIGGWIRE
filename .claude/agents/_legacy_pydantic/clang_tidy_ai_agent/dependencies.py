"""
Dependencies management for Clang-Tidy AI Agent.
Handles database connections, settings, and Archon MCP integration.
"""

import os
import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx
import json

from models import ClangTidyDependencies


class ArchonMCPClient:
    """Client for Archon MCP server integration."""
    
    def __init__(self, base_url: str = "http://archon-mcp:8051"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def manage_task(
        self, 
        action: str, 
        task_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Manage tasks via Archon MCP."""
        try:
            payload = {"action": action, **kwargs}
            if task_id:
                payload["task_id"] = task_id
            
            response = await self.client.post(
                f"{self.base_url}/manage_task",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Archon MCP task management failed: {str(e)}"}
    
    async def perform_rag_query(
        self, 
        query: str, 
        match_count: int = 5
    ) -> Dict[str, Any]:
        """Perform knowledge queries via Archon MCP."""
        try:
            payload = {"query": query, "match_count": match_count}
            
            response = await self.client.post(
                f"{self.base_url}/perform_rag_query",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Archon MCP RAG query failed: {str(e)}"}
    
    async def search_code_examples(
        self, 
        query: str, 
        match_count: int = 3
    ) -> Dict[str, Any]:
        """Search code examples via Archon MCP."""
        try:
            payload = {"query": query, "match_count": match_count}
            
            response = await self.client.post(
                f"{self.base_url}/search_code_examples",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Archon MCP code search failed: {str(e)}"}
    
    async def get_project_features(self, project_id: str) -> Dict[str, Any]:
        """Get project features via Archon MCP."""
        try:
            payload = {"project_id": project_id}
            
            response = await self.client.post(
                f"{self.base_url}/get_project_features",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Archon MCP project features failed: {str(e)}"}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class ClangTidySettings:
    """Settings management for Clang-Tidy AI Agent."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), 
            ".env"
        )
        self.load_settings()
    
    def load_settings(self):
        """Load settings from environment and config file."""
        # Default settings
        self.project_root = "/IdeaProjects/wire_ground"
        self.clang_tidy_path = "clang-tidy"
        self.llm_provider = "openai"
        self.llm_model = "gpt-4"
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.temp_directory = "/tmp/clang_tidy_analysis"
        self.database_path = os.path.join(
            os.path.dirname(__file__),
            "clang_tidy_ai.db"
        )
        self.enable_archon = True
        self.archon_base_url = "http://archon-mcp:8051"
        
        # Load from .env file if exists
        env_file = Path(self.config_path)
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key == "PROJECT_ROOT":
                            self.project_root = value
                        elif key == "CLANG_TIDY_PATH":
                            self.clang_tidy_path = value
                        elif key == "LLM_PROVIDER":
                            self.llm_provider = value
                        elif key == "LLM_MODEL":
                            self.llm_model = value
                        elif key == "API_KEY":
                            self.api_key = value
                        elif key == "TEMP_DIRECTORY":
                            self.temp_directory = value
                        elif key == "DATABASE_PATH":
                            self.database_path = value
                        elif key == "ENABLE_ARCHON":
                            self.enable_archon = value.lower() == "true"
                        elif key == "ARCHON_BASE_URL":
                            self.archon_base_url = value


class DatabaseManager:
    """Database manager for Clang-Tidy AI Agent."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the SQLite database with required tables."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Create tables
        cursor = self.connection.cursor()
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                preferred_strategy TEXT NOT NULL,
                context_tags TEXT NOT NULL,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analysis cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                analysis_result TEXT NOT NULL,  -- JSON
                clang_tidy_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, file_hash)
            )
        """)
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                fix_strategy TEXT NOT NULL,
                user_satisfaction INTEGER NOT NULL CHECK (user_satisfaction BETWEEN 1 AND 5),
                feedback_text TEXT,
                context_info TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Task tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT  -- JSON
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_session_rule ON user_preferences(session_id, rule_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_file_hash ON analysis_cache(file_path, file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_tracking_status ON task_tracking(status)")
        
        self.connection.commit()
    
    def save_user_preference(
        self, 
        session_id: str,
        rule_id: str, 
        preferred_strategy: str,
        context_tags: List[str]
    ):
        """Save user preference for a clang-tidy rule."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (session_id, rule_id, preferred_strategy, context_tags, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, rule_id, preferred_strategy, json.dumps(context_tags)))
        self.connection.commit()
    
    def load_user_preferences(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Load user preferences for a session."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT rule_id, preferred_strategy, context_tags
            FROM user_preferences 
            WHERE session_id = ?
            ORDER BY updated_at DESC
        """, (session_id,))
        
        preferences = {}
        for row in cursor.fetchall():
            preferences[row['rule_id']] = {
                'preferred_strategy': row['preferred_strategy'],
                'context_tags': json.loads(row['context_tags'])
            }
        
        return preferences
    
    def cache_analysis_result(
        self, 
        file_path: str, 
        file_hash: str, 
        analysis_result: Dict[str, Any],
        clang_tidy_version: str = "unknown"
    ):
        """Cache analysis results."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO analysis_cache
            (file_path, file_hash, analysis_result, clang_tidy_version)
            VALUES (?, ?, ?, ?)
        """, (file_path, file_hash, json.dumps(analysis_result), clang_tidy_version))
        self.connection.commit()
    
    def get_cached_analysis(
        self, 
        file_path: str, 
        file_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached analysis results."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT analysis_result FROM analysis_cache
            WHERE file_path = ? AND file_hash = ?
        """, (file_path, file_hash))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row['analysis_result'])
        return None
    
    def save_feedback(
        self,
        session_id: str,
        fix_strategy: str,
        user_satisfaction: int,
        feedback_text: Optional[str] = None,
        context_info: Optional[Dict[str, Any]] = None
    ):
        """Save user feedback."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO feedback
            (session_id, fix_strategy, user_satisfaction, feedback_text, context_info)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id, 
            fix_strategy, 
            user_satisfaction, 
            feedback_text,
            json.dumps(context_info) if context_info else None
        ))
        self.connection.commit()
    
    def track_task(
        self,
        task_id: str,
        task_type: str,
        status: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track task progress."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO task_tracking
            (task_id, task_type, status, file_path, updated_at, metadata)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            task_id,
            task_type, 
            status,
            file_path,
            json.dumps(metadata) if metadata else None
        ))
        self.connection.commit()
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


def create_dependencies(
    session_id: Optional[str] = None,
    config_path: Optional[str] = None
) -> ClangTidyDependencies:
    """
    Create ClangTidyDependencies with all required components.
    
    This function initializes:
    - Settings management
    - Database connection
    - Archon MCP client (if enabled)
    """
    # Load settings
    settings = ClangTidySettings(config_path)
    
    # Initialize database
    db_manager = DatabaseManager(settings.database_path)
    
    # Initialize Archon MCP client if enabled
    archon_client = None
    if settings.enable_archon:
        archon_client = ArchonMCPClient(settings.archon_base_url)
    
    # Create dependencies object
    deps = ClangTidyDependencies(
        clang_tidy_path=settings.clang_tidy_path,
        temp_directory=settings.temp_directory,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        api_key=settings.api_key,
        db_connection=db_manager,
        settings=settings,
        archon_client=archon_client
    )
    
    return deps


async def cleanup_dependencies(deps: ClangTidyDependencies):
    """Clean up dependencies and close connections."""
    if hasattr(deps, 'db_connection') and deps.db_connection:
        deps.db_connection.close()
    
    if hasattr(deps, 'archon_client') and deps.archon_client:
        await deps.archon_client.close()


# Utility functions for testing
def create_test_dependencies(temp_db: Optional[str] = None) -> ClangTidyDependencies:
    """Create dependencies for testing purposes."""
    if temp_db is None:
        import tempfile
        temp_db = tempfile.mktemp(suffix='.db')
    
    db_manager = DatabaseManager(temp_db)
    
    settings = ClangTidySettings()
    settings.database_path = temp_db
    settings.api_key = "test-key"
    settings.enable_archon = False  # Disable for tests
    
    return ClangTidyDependencies(
        clang_tidy_path="clang-tidy",
        temp_directory="/tmp/test_clang_tidy",
        llm_provider="test",
        llm_model="test-model",
        api_key="test-key",
        db_connection=db_manager,
        settings=settings
    )


# Export main functions
__all__ = [
    'ClangTidySettings',
    'DatabaseManager', 
    'ArchonMCPClient',
    'create_dependencies',
    'cleanup_dependencies',
    'create_test_dependencies'
]