# Optimized Dependencies for Clang-Tidy AI Agent

## Environment Variables

```bash
# Core Configuration
CLANG_TIDY_BINARY_PATH=/usr/bin/clang-tidy
PROJECT_ROOT=/IdeaProjects/wire_ground
CACHE_DIR=/tmp/clang_tidy_cache

# LLM Configuration
LLM_PROVIDER=anthropic
LLM_API_KEY=your_api_key_here
LLM_MODEL=claude-3-sonnet-20240229
LLM_MAX_RETRIES=3
LLM_TIMEOUT=30

# Performance Settings
MAX_CONCURRENT_ANALYSES=4
CACHE_TTL_SECONDS=3600
SUBPROCESS_TIMEOUT=30
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Feature Flags
ENABLE_CACHING=true
ENABLE_KNOWLEDGE_BASE=true
ENABLE_PROGRESS_TRACKING=true
ENABLE_PERFORMANCE_METRICS=true
ENABLE_MULTI_COMPILER_VALIDATION=true

# Database Configuration
SQLITE_DB_PATH=/tmp/clang_tidy_ai.db
KNOWLEDGE_BASE_PATH=/tmp/clang_tidy_knowledge.db

# Compiler Paths
GCC_PATH=/usr/bin/g++
CLANG_PATH=/usr/bin/clang++
CMAKE_PATH=/usr/bin/cmake

# Integration Settings
GIT_AUTO_COMMIT=false
CMAKE_BUILD_DIR=cmake-build-debug
AUDIT_LOG_PATH=/tmp/clang_tidy_audit.log
```

## Python Dependencies

### Core Requirements
```txt
# Pydantic AI Framework
pydantic-ai>=0.0.9
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Async and Concurrency
asyncio
aiofiles>=23.0.0
asyncio-throttle>=1.0.0
aiocache>=0.12.0

# HTTP and API
httpx>=0.24.0
tenacity>=8.2.0

# Database and Caching
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.19.0
cachetools>=5.3.0
diskcache>=5.6.0

# Utilities
python-dotenv>=1.0.0
structlog>=23.0.0
click>=8.1.0
rich>=13.0.0

# Performance Monitoring
prometheus-client>=0.16.0
psutil>=5.9.0

# Testing (dev dependencies)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
pytest-benchmark>=4.0.0
```

## Dependency Classes

### ClangTidyDependencies
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import aiosqlite
from structlog import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class OptimizedClangTidyDependencies:
    """Enhanced dependencies for the optimized agent."""
    
    # Core paths
    project_root: Path
    clang_tidy_binary: Path
    cache_dir: Path
    
    # Database connections
    db_connection: AsyncSession
    knowledge_base: aiosqlite.Connection
    
    # LLM configuration
    llm_provider: str
    llm_api_key: str
    llm_model: str
    
    # Performance settings
    max_concurrent: int = 4
    cache_ttl: int = 3600
    subprocess_timeout: int = 30
    
    # Circuit breaker settings
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Feature flags
    enable_caching: bool = True
    enable_knowledge_base: bool = True
    enable_progress_tracking: bool = True
    enable_metrics: bool = True
    
    # Runtime state
    logger: Any = None
    metrics_collector: Optional[Any] = None
    analysis_stats: Dict[str, int] = None
    
    def __post_init__(self):
        """Initialize runtime components."""
        self.logger = get_logger(__name__)
        self.analysis_stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "fixes_applied": 0,
            "errors_encountered": 0
        }
```

### Settings Configuration
```python
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from pathlib import Path

class OptimizedSettings(BaseSettings):
    """Application settings with validation."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Paths
    clang_tidy_binary_path: Path = Field(
        default=Path("/usr/bin/clang-tidy"),
        description="Path to clang-tidy binary"
    )
    project_root: Path = Field(
        default=Path("/IdeaProjects/wire_ground"),
        description="Project root directory"
    )
    cache_dir: Path = Field(
        default=Path("/tmp/clang_tidy_cache"),
        description="Cache directory"
    )
    
    # LLM Configuration
    llm_provider: str = Field(
        default="anthropic",
        description="LLM provider (anthropic/openai)"
    )
    llm_api_key: str = Field(
        ...,
        description="API key for LLM provider"
    )
    llm_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Model to use"
    )
    
    # Performance
    max_concurrent_analyses: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum concurrent analyses"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Cache TTL in seconds"
    )
    subprocess_timeout: int = Field(
        default=30,
        ge=5,
        description="Subprocess timeout in seconds"
    )
    
    # Features
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching"
    )
    enable_knowledge_base: bool = Field(
        default=True,
        description="Enable knowledge base"
    )
    enable_progress_tracking: bool = Field(
        default=True,
        description="Enable progress tracking"
    )
```

### Provider Configuration
```python
from typing import Union
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel

class OptimizedModelProvider:
    """Manages LLM model providers with fallback."""
    
    def __init__(self, settings: OptimizedSettings):
        self.settings = settings
        self.primary_model = self._create_model()
        self.fallback_model = None
    
    def _create_model(self) -> Union[OpenAIModel, AnthropicModel]:
        """Create the appropriate model based on provider."""
        if self.settings.llm_provider == "anthropic":
            return AnthropicModel(
                model=self.settings.llm_model,
                api_key=self.settings.llm_api_key
            )
        elif self.settings.llm_provider == "openai":
            return OpenAIModel(
                model=self.settings.llm_model,
                api_key=self.settings.llm_api_key
            )
        else:
            raise ValueError(f"Unknown provider: {self.settings.llm_provider}")
    
    def get_model(self):
        """Get the configured model with fallback support."""
        return self.primary_model
```

## Database Schema

### Cache Database
```sql
-- Analysis cache table
CREATE TABLE IF NOT EXISTS analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    analysis_result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    UNIQUE(file_path, file_hash)
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    success BOOLEAN NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Knowledge Base Database
```sql
-- Fixed patterns table
CREATE TABLE IF NOT EXISTS fix_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warning_type TEXT NOT NULL,
    fix_pattern TEXT NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applied fixes history
CREATE TABLE IF NOT EXISTS fix_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    warning_type TEXT NOT NULL,
    original_code TEXT NOT NULL,
    fixed_code TEXT NOT NULL,
    validation_result TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Integration Points

### CMake Integration
```cmake
# Add custom target for clang-tidy analysis
add_custom_target(
    clang_tidy_ai
    COMMAND python3 ${PROJECT_SOURCE_DIR}/.claude/agents/clang_tidy_ai_agent/cli.py
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
    COMMENT "Running AI-enhanced clang-tidy analysis"
)
```

### Git Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit
python3 .claude/agents/clang_tidy_ai_agent/cli.py --check-only
```