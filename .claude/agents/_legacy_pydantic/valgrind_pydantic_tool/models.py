"""
Pydantic models for Valgrind analyzer tool.
Defines all configuration, input, output, and state models with validation.
"""

from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime


class ValgrindTool(str, Enum):
    """Supported Valgrind tools enumeration."""
    MEMCHECK = "memcheck"          # Memory errors/leaks
    CACHEGRIND = "cachegrind"      # Cache profiling
    CALLGRIND = "callgrind"        # Call-graph profiling
    HELGRIND = "helgrind"          # Thread races/locks
    DRD = "drd"                    # Thread errors (alternative)
    MASSIF = "massif"              # Heap profiling
    DHAT = "dhat"                  # Dynamic heap analysis
    LACKEY = "lackey"              # Basic example tool
    NULGRIND = "none"              # No analysis
    BBV = "exp-bbv"                # Experimental basic block vector


class IssueCategory(str, Enum):
    """Categories of issues that Valgrind can detect."""
    MEMORY_LEAK = "memory_leak"
    INVALID_READ = "invalid_read"
    INVALID_WRITE = "invalid_write"
    UNINITIALIZED_VALUE = "uninitialized_value"
    DATA_RACE = "data_race"
    LOCK_ORDER = "lock_order"
    DEADLOCK = "deadlock"
    CACHE_MISS = "cache_miss"
    HEAP_USAGE = "heap_usage"
    STACK_OVERFLOW = "stack_overflow"
    DOUBLE_FREE = "double_free"
    MISMATCHED_FREE = "mismatched_free"
    OVERLAP_ERROR = "overlap_error"
    SYSCALL_ERROR = "syscall_error"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValgrindIssue(BaseModel):
    """Represents a single issue detected by Valgrind."""
    category: IssueCategory
    severity: IssueSeverity = IssueSeverity.ERROR
    description: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    stack_trace: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    raw_output: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ValgrindConfig(BaseModel):
    """Configuration for Valgrind analysis with comprehensive flag support."""
    
    # Core configuration
    tool: ValgrindTool = ValgrindTool.MEMCHECK
    xml_output: bool = True
    timeout: int = 3600  # seconds
    
    # General Valgrind flags
    leak_check: Optional[str] = "full"  # no/summary/full/extended
    show_reachable: Optional[bool] = True
    show_possibly_lost: Optional[bool] = True
    track_origins: Optional[bool] = True
    track_fds: Optional[bool] = True
    num_callers: Optional[int] = 12
    error_limit: Optional[bool] = True
    gen_suppressions: Optional[str] = None  # no/yes/all
    suppressions: Optional[List[str]] = Field(default_factory=list)
    
    # Memcheck specific
    partial_loads_ok: Optional[bool] = True
    expensive_definedness_checks: Optional[bool] = False
    keep_stacktraces: Optional[str] = "alloc-and-free"
    freelist_vol: Optional[int] = 20000000
    freelist_big_blocks: Optional[int] = 1000000
    workaround_gcc296_bugs: Optional[bool] = False
    
    # Helgrind/DRD specific  
    history_level: Optional[str] = "full"  # none/approx/full
    check_stack_refs: Optional[bool] = True
    conflict_cache_size: Optional[int] = 1000000
    
    # Cachegrind/Callgrind specific
    cache_sim: Optional[bool] = True
    branch_sim: Optional[bool] = True
    dump_instr: Optional[str] = "no"  # no/yes
    collect_atstart: Optional[bool] = True
    collect_jumps: Optional[bool] = False
    separate_threads: Optional[bool] = False
    
    # Cache configuration
    I1: Optional[str] = None  # L1 instruction cache: size,assoc,line_size
    D1: Optional[str] = None  # L1 data cache
    LL: Optional[str] = None  # Last level cache
    
    # DRD specific
    free_is_write: Optional[bool] = False
    exclusive_threshold: Optional[int] = 10
    first_race_only: Optional[bool] = False
    segment_merging: Optional[bool] = True
    
    # Massif specific
    heap: Optional[bool] = True
    heap_admin: Optional[int] = 8
    stacks: Optional[bool] = False
    pages_as_heap: Optional[bool] = False
    depth: Optional[int] = 30
    alloc_fn: Optional[List[str]] = Field(default_factory=list)
    
    # Binary and arguments
    binary_path: Optional[str] = None
    binary_args: List[str] = Field(default_factory=list)
    
    # Output control
    log_file: Optional[str] = None
    xml_file: Optional[str] = None
    verbose: bool = False
    quiet: bool = False
    
    # AI integration
    ai_analyze: bool = False
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4"
    
    @validator('leak_check')
    def validate_leak_check(cls, v):
        if v and v not in ["no", "summary", "full", "extended"]:
            raise ValueError("Invalid leak_check value")
        return v
    
    @validator('history_level')
    def validate_history_level(cls, v):
        if v and v not in ["none", "approx", "full"]:
            raise ValueError("Invalid history_level value")
        return v
    
    @validator('gen_suppressions')
    def validate_gen_suppressions(cls, v):
        if v and v not in ["no", "yes", "all"]:
            raise ValueError("Invalid gen_suppressions value")
        return v


class ValgrindMetrics(BaseModel):
    """Metrics extracted from Valgrind analysis."""
    total_heap_usage: Optional[int] = 0
    leaked_bytes: Optional[int] = 0
    possibly_leaked_bytes: Optional[int] = 0
    still_reachable_bytes: Optional[int] = 0
    suppressed_bytes: Optional[int] = 0
    error_count: Optional[int] = 0
    warning_count: Optional[int] = 0
    execution_time: Optional[float] = 0.0
    cache_misses: Optional[int] = 0
    cache_miss_rate: Optional[float] = 0.0
    branch_mispredictions: Optional[int] = 0
    instructions_executed: Optional[int] = 0
    data_races: Optional[int] = 0
    lock_contentions: Optional[int] = 0
    
    def total_issues(self) -> int:
        """Calculate total number of issues."""
        return (self.error_count or 0) + (self.warning_count or 0)
    
    def is_memory_clean(self) -> bool:
        """Check if memory is completely clean."""
        return (
            (self.leaked_bytes or 0) == 0 and
            (self.possibly_leaked_bytes or 0) == 0 and
            (self.error_count or 0) == 0
        )


class ValgrindState(BaseModel):
    """State tracking for Valgrind analysis."""
    project_root: Path
    current_tool: Optional[ValgrindTool] = None
    analysis_start: Optional[datetime] = None
    analysis_end: Optional[datetime] = None
    issues: List[ValgrindIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    metrics: ValgrindMetrics = Field(default_factory=ValgrindMetrics)
    raw_outputs: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ValgrindResult(BaseModel):
    """Complete result of Valgrind analysis."""
    success: bool
    tool_used: ValgrindTool
    binary_path: str
    config: ValgrindConfig
    issues: List[ValgrindIssue]
    metrics: ValgrindMetrics
    suggestions: Optional[List[str]] = None
    raw_output: str
    xml_output: Optional[str] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
    
    def has_critical_issues(self) -> bool:
        """Check if analysis found critical issues."""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)
    
    def has_memory_leaks(self) -> bool:
        """Check if analysis found memory leaks."""
        return (
            any(issue.category == IssueCategory.MEMORY_LEAK for issue in self.issues) or
            (self.metrics.leaked_bytes or 0) > 0
        )
    
    def has_thread_issues(self) -> bool:
        """Check if analysis found thread safety issues."""
        thread_categories = {
            IssueCategory.DATA_RACE,
            IssueCategory.DEADLOCK,
            IssueCategory.LOCK_ORDER
        }
        return any(issue.category in thread_categories for issue in self.issues)
    
    def get_summary(self) -> str:
        """Get human-readable summary of results."""
        if self.success and not self.issues:
            return f"✅ Clean analysis with {self.tool_used}: No issues found"
        
        summary = f"⚠️  Analysis with {self.tool_used} found {len(self.issues)} issues:\n"
        
        # Categorize issues
        categories = {}
        for issue in self.issues:
            if issue.category not in categories:
                categories[issue.category] = 0
            categories[issue.category] += 1
        
        for category, count in categories.items():
            summary += f"  - {category.replace('_', ' ').title()}: {count}\n"
        
        # Add metrics if available
        if self.metrics.leaked_bytes and self.metrics.leaked_bytes > 0:
            summary += f"  - Memory leaked: {self.metrics.leaked_bytes} bytes\n"
        
        return summary.strip()


class ValgrindError(Exception):
    """Custom exception for Valgrind-related errors."""
    def __init__(self, message: str, exit_code: Optional[int] = None, stderr: Optional[str] = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class LearningDatabase(BaseModel):
    """Database for learning and improving analysis."""
    issue_patterns: Dict[IssueCategory, List[str]] = Field(default_factory=dict)
    fix_suggestions: Dict[IssueCategory, List[str]] = Field(default_factory=dict)
    common_suppressions: List[str] = Field(default_factory=list)
    performance_baselines: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_suggestion(self, category: IssueCategory, suggestion: str):
        """Add a fix suggestion for an issue category."""
        if category not in self.fix_suggestions:
            self.fix_suggestions[category] = []
        if suggestion not in self.fix_suggestions[category]:
            self.fix_suggestions[category].append(suggestion)
            self.last_updated = datetime.now()
    
    def get_suggestions(self, category: IssueCategory) -> List[str]:
        """Get fix suggestions for an issue category."""
        return self.fix_suggestions.get(category, [])