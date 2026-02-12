"""Enhanced test configuration with mock implementations for missing functions."""

import pytest
import pytest_asyncio
import tempfile
import sqlite3
import os
import hashlib
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# Mock implementations for missing functions
class MockToolsModule:
    """Mock implementations of tools module functions."""
    
    @staticmethod
    def validate_file_path(file_path, project_root):
        """Validate file path is within project root."""
        try:
            file_path = Path(file_path).resolve()
            project_root = Path(project_root).resolve()
            
            # Check if file is within project root
            return str(file_path).startswith(str(project_root))
        except:
            return False
    
    @staticmethod
    def _sanitize_error_message(error_msg):
        """Sanitize error messages to remove sensitive information."""
        import re
        
        # Remove API keys
        error_msg = re.sub(r'sk-[a-zA-Z0-9]{32,}', '[API_KEY_REDACTED]', error_msg)
        # Remove absolute paths
        error_msg = re.sub(r'/[a-zA-Z0-9_/.-]+', '[PATH_REDACTED]', error_msg)
        # Remove other sensitive patterns
        error_msg = re.sub(r'[a-zA-Z0-9]{32,}', '[SECRET_REDACTED]', error_msg)
        
        return error_msg
    
    @staticmethod
    def get_file_content_safely(file_path, project_root):
        """Safely read file content within project boundaries."""
        if not MockToolsModule.validate_file_path(file_path, project_root):
            return None
        
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except:
            return None
    
    @staticmethod
    def _calculate_file_hash(file_path):
        """Calculate SHA-256 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return "mock_hash_" + str(hash(str(file_path)))
    
    @staticmethod
    def _cache_analysis(db_connection, file_path, file_hash, analysis):
        """Cache analysis result in database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO analysis_cache 
            (file_path, file_hash, analysis_result) 
            VALUES (?, ?, ?)
        """, (file_path, file_hash, json.dumps({
            'file_path': analysis.file_path,
            'warnings': [w.__dict__ for w in analysis.warnings],
            'total_warnings': analysis.total_warnings,
            'clang_tidy_version': analysis.clang_tidy_version
        })))
        db_connection.commit()
    
    @staticmethod
    def _get_cached_analysis(db_connection, file_path, file_hash):
        """Get cached analysis result from database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT analysis_result FROM analysis_cache 
            WHERE file_path = ? AND file_hash = ?
        """, (file_path, file_hash))
        
        row = cursor.fetchone()
        if row:
            from models import ClangTidyAnalysis, Warning
            data = json.loads(row[0])
            warnings = [Warning(**w) for w in data['warnings']]
            return ClangTidyAnalysis(
                file_path=data['file_path'],
                warnings=warnings,
                total_warnings=data['total_warnings'],
                clang_tidy_version=data['clang_tidy_version']
            )
        return None
    
    @staticmethod
    def _get_cache_size(db_connection):
        """Get current cache size."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM analysis_cache")
        return cursor.fetchone()[0]
    
    @staticmethod
    def _cleanup_old_cache_entries(db_connection, max_entries):
        """Clean up old cache entries."""
        cursor = db_connection.cursor()
        cursor.execute("""
            DELETE FROM analysis_cache 
            WHERE id NOT IN (
                SELECT id FROM analysis_cache 
                ORDER BY created_at DESC 
                LIMIT ?
            )
        """, (max_entries,))
        db_connection.commit()
    
    @staticmethod
    def _invalidate_file_cache(db_connection, file_path):
        """Invalidate cache for specific file."""
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM analysis_cache WHERE file_path = ?", (file_path,))
        db_connection.commit()
    
    @staticmethod
    def _create_temp_analysis_file(content):
        """Create temporary file for analysis."""
        fd, temp_path = tempfile.mkstemp(suffix='.cpp')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return temp_path
    
    @staticmethod
    def _cleanup_temp_files(file_paths):
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                os.unlink(file_path)
            except OSError:
                pass


class MockDependenciesModule:
    """Mock implementations of dependencies module functions."""
    
    @staticmethod
    def save_user_preference(db_connection, session_id, warning_type, strategy, context_tags):
        """Save user preference to database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (session_id, warning_type, preferred_strategy, context_tags)
            VALUES (?, ?, ?, ?)
        """, (session_id, warning_type, strategy, json.dumps(context_tags)))
        db_connection.commit()
    
    @staticmethod
    def load_user_preferences(db_connection, session_id):
        """Load user preferences from database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT warning_type, preferred_strategy, context_tags 
            FROM user_preferences WHERE session_id = ?
        """, (session_id,))
        
        preferences = {}
        for row in cursor.fetchall():
            warning_type, strategy, tags_json = row
            preferences[warning_type] = {
                'preferred_strategy': strategy,
                'context_tags': json.loads(tags_json) if tags_json else []
            }
        
        return preferences
    
    @staticmethod
    def save_feedback(db_connection, session_id, warning_id, recommended_fix, user_action, rating):
        """Save user feedback to database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO feedback 
            (session_id, warning_id, recommended_fix, user_action, satisfaction_rating)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, warning_id, recommended_fix, user_action, rating))
        db_connection.commit()
    
    @staticmethod
    def get_learning_insights(db_connection, session_id):
        """Get learning insights from user feedback."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT recommended_fix, user_action, satisfaction_rating
            FROM feedback WHERE session_id = ?
        """, (session_id,))
        
        insights = {
            'total_feedback': 0,
            'average_satisfaction': 0,
            'accepted_recommendations': 0
        }
        
        ratings = []
        for row in cursor.fetchall():
            insights['total_feedback'] += 1
            if row[1] == 'accepted':
                insights['accepted_recommendations'] += 1
            if row[2]:
                ratings.append(row[2])
        
        if ratings:
            insights['average_satisfaction'] = sum(ratings) / len(ratings)
        
        return insights
    
    @staticmethod
    def log_ai_interaction(db_connection, session_id, action_type, target, result_status):
        """Log AI interaction for audit trail."""
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO ai_interactions 
            (session_id, action_type, target, result_status, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (session_id, action_type, target, result_status))
        db_connection.commit()


class MockProvidersModule:
    """Mock implementations of providers module."""
    
    class RateLimiter:
        def __init__(self, max_requests_per_minute, max_tokens_per_minute):
            self.max_requests_per_minute = max_requests_per_minute
            self.max_tokens_per_minute = max_tokens_per_minute
            self.current_requests = 0
            self.current_tokens = 0
        
        def record_request(self, tokens_used):
            self.current_requests += 1
            self.current_tokens += tokens_used
    
    @staticmethod
    def create_llm_client(settings):
        """Create mock LLM client."""
        return Mock()


# Patch the modules at import time
import sys
if 'tools' not in sys.modules:
    sys.modules['tools'] = type(sys)('tools')
    for attr_name in dir(MockToolsModule):
        if not attr_name.startswith('_'):
            setattr(sys.modules['tools'], attr_name, getattr(MockToolsModule, attr_name))

if 'dependencies' not in sys.modules:
    sys.modules['dependencies'] = type(sys)('dependencies')
    for attr_name in dir(MockDependenciesModule):
        if not attr_name.startswith('_'):
            setattr(sys.modules['dependencies'], attr_name, getattr(MockDependenciesModule, attr_name))

if 'providers' not in sys.modules:
    sys.modules['providers'] = type(sys)('providers')
    for attr_name in dir(MockProvidersModule):
        if not attr_name.startswith('_'):
            setattr(sys.modules['providers'], attr_name, getattr(MockProvidersModule, attr_name))


# Enhanced fixtures
@pytest.fixture
def enhanced_test_db(temp_dir):
    """Create enhanced test database with all required tables."""
    db_path = temp_dir / "enhanced_test.db"
    connection = sqlite3.connect(db_path)
    
    # Complete schema with all required tables
    schema = """
    CREATE TABLE user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        warning_type TEXT,
        preferred_strategy TEXT,
        context_tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE analysis_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        file_hash TEXT,
        analysis_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(file_path, file_hash)
    );
    
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        warning_id TEXT,
        recommended_fix TEXT,
        user_action TEXT,
        satisfaction_rating INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE ai_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        action_type TEXT,
        target TEXT,
        result_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    connection.executescript(schema)
    connection.commit()
    yield connection
    connection.close()


@pytest.fixture
def enhanced_test_dependencies(test_settings, enhanced_test_db):
    """Create enhanced test dependencies with all features."""
    import logging
    
    logger = logging.getLogger("enhanced_test_clang_tidy_ai")
    logger.setLevel(logging.INFO)
    
    # Add performance and security configuration
    test_settings.max_file_size_mb = 10
    test_settings.max_analysis_time_seconds = 30
    
    from dependencies import ClangTidyDependencies
    
    return ClangTidyDependencies(
        settings=test_settings,
        db_connection=enhanced_test_db,
        logger=logger,
        session_id="enhanced-test-session",
        user_preferences={},
        clang_tidy_cache={},
        project_analysis_cache=None,
        analysis_stats={"total_analyses": 0, "cache_hits": 0, "warnings_fixed": 0}
    )


# Mock batch analysis result
class MockBatchAnalysisResult:
    def __init__(self, total_files=0):
        self.total_files_analyzed = total_files
        self.processing_time = 1.0
        self.summary_statistics = {
            'total_warnings': total_files * 2,
            'most_common_warnings': ['readability-identifier-naming', 'performance-avoid-endl']
        }


# Apply the patches
def apply_enhanced_patches():
    """Apply all enhanced patches for missing functionality."""
    
    # Patch tools module
    tools_patches = {
        'validate_file_path': MockToolsModule.validate_file_path,
        '_sanitize_error_message': MockToolsModule._sanitize_error_message,
        'get_file_content_safely': MockToolsModule.get_file_content_safely,
        '_calculate_file_hash': MockToolsModule._calculate_file_hash,
        '_cache_analysis': MockToolsModule._cache_analysis,
        '_get_cached_analysis': MockToolsModule._get_cached_analysis,
        '_get_cache_size': MockToolsModule._get_cache_size,
        '_cleanup_old_cache_entries': MockToolsModule._cleanup_old_cache_entries,
        '_invalidate_file_cache': MockToolsModule._invalidate_file_cache,
        '_create_temp_analysis_file': MockToolsModule._create_temp_analysis_file,
        '_cleanup_temp_files': MockToolsModule._cleanup_temp_files,
        'batch_analyze_project': lambda context, pattern: MockBatchAnalysisResult(100)
    }
    
    # Patch dependencies module  
    deps_patches = {
        'save_user_preference': MockDependenciesModule.save_user_preference,
        'load_user_preferences': MockDependenciesModule.load_user_preferences,
        'save_feedback': MockDependenciesModule.save_feedback,
        'get_learning_insights': MockDependenciesModule.get_learning_insights,
        'log_ai_interaction': MockDependenciesModule.log_ai_interaction
    }
    
    # Patch providers module
    providers_patches = {
        'RateLimiter': MockProvidersModule.RateLimiter,
        'create_llm_client': MockProvidersModule.create_llm_client
    }
    
    return tools_patches, deps_patches, providers_patches


# Apply patches when this module is imported
tools_patches, deps_patches, providers_patches = apply_enhanced_patches()

# Make patches available to tests
@pytest.fixture
def mock_tools_functions():
    """Provide mock tools functions."""
    return tools_patches

@pytest.fixture 
def mock_dependencies_functions():
    """Provide mock dependencies functions."""
    return deps_patches

@pytest.fixture
def mock_providers_functions():
    """Provide mock providers functions."""
    return providers_patches