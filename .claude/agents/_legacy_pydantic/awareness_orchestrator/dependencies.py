"""
Dependencies for Awareness Orchestrator.

Provides access to all orchestrator components and utilities.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sys

# Add backup_old to path for imports
backup_path = Path(__file__).parent / "backup_old"
if str(backup_path) not in sys.path:
    sys.path.insert(0, str(backup_path))

# Import orchestrator components from backup_old (use alias to avoid conflict with models.BuildResult)
from build_system_adapter import BuildSystemAdapter
from build_system_adapter import BuildResult as AdapterBuildResult
from pattern_recognition import PatternRecognitionSystem
from proactive_suggestions import ProactiveSuggestionsEngine
from metrics_dashboard import MetricsDashboard
from progress_reporter import ProgressReporter, ProgressEvent
from prompt_templates import PromptTemplate

from .models import (
    OrchestrationContext,
    OrchestrationResult,
    AgentFindings,
    Finding,
    Severity,
    AgentType
)


@dataclass
class OrchestrationDeps:
    """
    Dependencies container for Awareness Orchestrator.

    Provides access to all orchestrator components:
    - Build system integration
    - Pattern recognition and learning
    - Proactive suggestion engine
    - Metrics tracking and dashboard
    - Progress reporting
    - Prompt template generation
    """

    # Project paths
    project_root: Path
    build_dir: Path

    # Core components (lazy-initialized)
    _build_adapter: Optional[BuildSystemAdapter] = None
    _pattern_recognition: Optional[PatternRecognitionSystem] = None
    _suggestions_engine: Optional[ProactiveSuggestionsEngine] = None
    _metrics_dashboard: Optional[MetricsDashboard] = None
    _progress_reporter: Optional[ProgressReporter] = None
    _prompt_templates: Optional[PromptTemplate] = None

    @property
    def build_adapter(self) -> BuildSystemAdapter:
        """Get or create build system adapter."""
        if self._build_adapter is None:
            self._build_adapter = BuildSystemAdapter(
                project_root=self.project_root,
                build_dir=self.build_dir
            )
        return self._build_adapter

    @property
    def pattern_recognition(self) -> PatternRecognitionSystem:
        """Get or create pattern recognition system."""
        if self._pattern_recognition is None:
            patterns_dir = Path(__file__).parent / "patterns"
            patterns_dir.mkdir(exist_ok=True)
            self._pattern_recognition = PatternRecognitionSystem(
                storage_path=patterns_dir
            )
        return self._pattern_recognition

    @property
    def suggestions_engine(self) -> ProactiveSuggestionsEngine:
        """Get or create proactive suggestions engine."""
        if self._suggestions_engine is None:
            self._suggestions_engine = ProactiveSuggestionsEngine(
                pattern_system=self.pattern_recognition
            )
        return self._suggestions_engine

    @property
    def metrics_dashboard(self) -> MetricsDashboard:
        """Get or create metrics dashboard."""
        if self._metrics_dashboard is None:
            self._metrics_dashboard = MetricsDashboard(
                pattern_db=self.pattern_recognition
            )
        return self._metrics_dashboard

    @property
    def progress_reporter(self) -> ProgressReporter:
        """Get or create progress reporter."""
        if self._progress_reporter is None:
            self._progress_reporter = ProgressReporter()
        return self._progress_reporter

    @property
    def prompt_templates(self) -> PromptTemplate:
        """Get or create prompt template generator."""
        if self._prompt_templates is None:
            self._prompt_templates = PromptTemplate()
        return self._prompt_templates

    async def build_and_test(self, target: str = "wire_ground_tests") -> AdapterBuildResult:
        """Build and test the project."""
        return await self.build_adapter.build_target(target)

    async def run_tests(self, filter_pattern: Optional[str] = None):
        """Run project tests with optional filter."""
        return await self.build_adapter.run_tests(test_filter=filter_pattern)

    def get_suggestions(self, file_path: str) -> list:
        """Get proactive suggestions for a file."""
        return self.suggestions_engine.analyze_file(Path(file_path))

    def record_orchestration(self, result: OrchestrationResult):
        """Record orchestration result for learning."""
        self.pattern_recognition.record_run(
            success=result.success,
            duration=result.total_duration,
            findings=result.agent_findings,
            errors=result.errors
        )

    def get_recommended_agents(self, context: OrchestrationContext) -> list[str]:
        """Get recommended agent sequence based on patterns."""
        return self.pattern_recognition.recommend_agent_sequence(
            file_path=context.file_path,
            task_description=context.task_description
        )

    def emit_progress(self, event_type: str, message: str, metadata: dict = None):
        """Emit progress event."""
        self.progress_reporter.emit(
            ProgressEvent(
                event_type=event_type,
                message=message,
                metadata=metadata or {}
            )
        )

    def generate_dashboard(self) -> str:
        """Generate metrics dashboard."""
        return self.metrics_dashboard.generate_dashboard()

    @classmethod
    def create_default(cls) -> "OrchestrationDeps":
        """Create dependencies with auto-detected project paths."""
        # Auto-detect current project root
        current_dir = Path.cwd()
        # Look for common project markers (CMakeLists.txt, .git, etc.)
        project_root = current_dir
        while project_root != project_root.parent:
            if (project_root / "CMakeLists.txt").exists() or (project_root / ".git").exists():
                break
            project_root = project_root.parent

        return cls(
            project_root=project_root,
            build_dir=project_root / "cmake-build-debug"
        )


def get_dependencies(
    project_root: Optional[Path] = None,
    build_dir: Optional[Path] = None
) -> OrchestrationDeps:
    """
    Get orchestration dependencies.

    Args:
        project_root: Project root directory (default: /IdeaProjects/wire_ground)
        build_dir: Build directory (default: project_root/cmake-build-debug)

    Returns:
        Configured OrchestrationDeps instance
    """
    if project_root is None:
        project_root = Path("/IdeaProjects/wire_ground")

    if build_dir is None:
        build_dir = project_root / "cmake-build-debug"

    return OrchestrationDeps(
        project_root=project_root,
        build_dir=build_dir
    )
