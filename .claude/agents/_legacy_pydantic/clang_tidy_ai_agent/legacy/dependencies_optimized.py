"""
Optimized dependencies for the Clang-Tidy AI Agent.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import aiosqlite
from sqlalchemy.ext.asyncio import AsyncSession
import structlog


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
    analysis_stats: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize runtime components."""
        if self.logger is None:
            self.logger = structlog.get_logger(__name__)
        
        if not self.analysis_stats:
            self.analysis_stats = {
                "total_analyses": 0,
                "cache_hits": 0,
                "fixes_applied": 0,
                "errors_encountered": 0,
                "api_calls": 0,
                "warnings_found": 0,
                "files_processed": 0
            }
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate paths
        if not self.clang_tidy_binary.exists():
            self.logger.warning(
                f"Clang-tidy binary not found at {self.clang_tidy_binary}"
            )
    
    async def initialize_databases(self):
        """Initialize database schemas."""
        # Initialize cache database schema
        if self.db_connection:
            await self._init_cache_schema()
        
        # Initialize knowledge base schema
        if self.knowledge_base:
            await self._init_knowledge_schema()
    
    async def _init_cache_schema(self):
        """Create cache database schema."""
        async with self.db_connection as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    analysis_result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    hit_count INTEGER DEFAULT 0,
                    UNIQUE(file_path, file_hash)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.commit()
    
    async def _init_knowledge_schema(self):
        """Create knowledge base schema."""
        await self.knowledge_base.execute("""
            CREATE TABLE IF NOT EXISTS fix_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warning_type TEXT NOT NULL,
                fix_pattern TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.knowledge_base.execute("""
            CREATE TABLE IF NOT EXISTS fix_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                warning_type TEXT NOT NULL,
                original_code TEXT NOT NULL,
                fixed_code TEXT NOT NULL,
                validation_result TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.knowledge_base.commit()
    
    def update_stats(self, stat_name: str, value: int = 1):
        """Update analysis statistics."""
        if stat_name in self.analysis_stats:
            self.analysis_stats[stat_name] += value
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary of analysis statistics."""
        stats = self.analysis_stats.copy()
        
        # Calculate derived metrics
        if stats["files_processed"] > 0:
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / stats["files_processed"]
            )
            stats["avg_warnings_per_file"] = (
                stats["warnings_found"] / stats["files_processed"]
            )
        else:
            stats["cache_hit_rate"] = 0.0
            stats["avg_warnings_per_file"] = 0.0
        
        if stats["total_analyses"] > 0:
            stats["error_rate"] = (
                stats["errors_encountered"] / stats["total_analyses"]
            )
        else:
            stats["error_rate"] = 0.0
        
        return stats
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.db_connection:
                await self.db_connection.close()
            
            if self.knowledge_base:
                await self.knowledge_base.close()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Factory functions for creating dependencies
async def create_dependencies(settings) -> OptimizedClangTidyDependencies:
    """Factory function to create initialized dependencies."""
    import aiosqlite
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Create async database engine
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{settings.sqlite_db_path}",
        echo=False
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Open knowledge base connection
    knowledge_base = await aiosqlite.connect(
        str(settings.knowledge_base_path)
    )
    
    deps = OptimizedClangTidyDependencies(
        project_root=settings.project_root,
        clang_tidy_binary=settings.clang_tidy_binary_path,
        cache_dir=settings.cache_dir,
        db_connection=async_session(),
        knowledge_base=knowledge_base,
        llm_provider=settings.llm_provider,
        llm_api_key=settings.llm_api_key,
        llm_model=settings.llm_model,
        max_concurrent=settings.max_concurrent_analyses,
        cache_ttl=settings.cache_ttl_seconds,
        subprocess_timeout=settings.subprocess_timeout,
        circuit_breaker_threshold=settings.circuit_breaker_threshold,
        circuit_breaker_timeout=settings.circuit_breaker_timeout,
        enable_caching=settings.enable_caching,
        enable_knowledge_base=settings.enable_knowledge_base,
        enable_progress_tracking=settings.enable_progress_tracking,
        enable_metrics=settings.enable_performance_metrics
    )
    
    # Initialize database schemas
    await deps.initialize_databases()
    
    return deps