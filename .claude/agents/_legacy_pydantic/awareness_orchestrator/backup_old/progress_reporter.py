"""
Progress Reporting System
Real-time streaming progress updates for orchestration workflows
"""

import time
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProgressEventType(str, Enum):
    """Types of progress events."""
    TASK_START = "task_start"
    PROGRESS_UPDATE = "progress_update"
    MILESTONE = "milestone"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ProgressEvent:
    """Progress event data."""
    type: ProgressEventType
    timestamp: datetime
    task_id: str
    message: str
    progress: float = 0.0  # 0.0 to 1.0
    stage: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressReporter:
    """
    Real-time progress reporting system.

    Features:
    - Event-based progress tracking
    - Multiple listener support (console, file, network)
    - Milestone tracking
    - Stage-based progress
    - Duration tracking
    - Metadata attachment
    """

    def __init__(self):
        self.listeners: List[Callable[[ProgressEvent], None]] = []
        self.current_task: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.milestones: List[Dict[str, Any]] = []
        self.stages: List[str] = []
        self.current_stage_index: int = 0

    def add_listener(self, listener: Callable[[ProgressEvent], None]):
        """
        Add progress listener callback.

        Args:
            listener: Callback function that receives ProgressEvent
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable[[ProgressEvent], None]):
        """Remove progress listener callback."""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def start_task(
        self,
        task_id: str,
        description: str,
        stages: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Start new task reporting.

        Args:
            task_id: Unique task identifier
            description: Human-readable task description
            stages: Optional list of stage names
            metadata: Additional task metadata
        """
        self.current_task = task_id
        self.start_time = datetime.now()
        self.milestones = []
        self.stages = stages or []
        self.current_stage_index = 0

        event = ProgressEvent(
            type=ProgressEventType.TASK_START,
            timestamp=self.start_time,
            task_id=task_id,
            message=description,
            metadata=metadata or {}
        )

        self._emit(event)

    def update_progress(
        self,
        progress: float,
        message: str,
        stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update task progress.

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
            stage: Optional stage name
            metadata: Additional metadata
        """
        if not self.current_task:
            return

        # Auto-advance stage if using staged progress
        if self.stages and stage and stage in self.stages:
            self.current_stage_index = self.stages.index(stage)

        event = ProgressEvent(
            type=ProgressEventType.PROGRESS_UPDATE,
            timestamp=datetime.now(),
            task_id=self.current_task,
            message=message,
            progress=max(0.0, min(1.0, progress)),  # Clamp to [0, 1]
            stage=stage,
            metadata=metadata or {}
        )

        self._emit(event)

    def milestone(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Record milestone achievement.

        Args:
            name: Milestone name
            data: Optional milestone data
        """
        if not self.current_task:
            return

        milestone = {
            "name": name,
            "timestamp": datetime.now(),
            "data": data or {}
        }

        self.milestones.append(milestone)

        event = ProgressEvent(
            type=ProgressEventType.MILESTONE,
            timestamp=milestone["timestamp"],
            task_id=self.current_task,
            message=f"Milestone: {name}",
            metadata={"milestone": milestone}
        )

        self._emit(event)

    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Report warning."""
        if not self.current_task:
            return

        event = ProgressEvent(
            type=ProgressEventType.WARNING,
            timestamp=datetime.now(),
            task_id=self.current_task,
            message=message,
            metadata=metadata or {}
        )

        self._emit(event)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Report informational message."""
        if not self.current_task:
            return

        event = ProgressEvent(
            type=ProgressEventType.INFO,
            timestamp=datetime.now(),
            task_id=self.current_task,
            message=message,
            metadata=metadata or {}
        )

        self._emit(event)

    def complete_task(
        self,
        success: bool,
        message: Optional[str] = None,
        result: Optional[Any] = None
    ):
        """
        Complete task reporting.

        Args:
            success: Whether task completed successfully
            message: Optional completion message
            result: Optional result data
        """
        if not self.current_task:
            return

        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        event_type = ProgressEventType.TASK_COMPLETE if success else ProgressEventType.TASK_FAILED
        default_message = "Task completed successfully" if success else "Task failed"

        event = ProgressEvent(
            type=event_type,
            timestamp=datetime.now(),
            task_id=self.current_task,
            message=message or default_message,
            progress=1.0,
            metadata={
                "duration": duration,
                "milestones_count": len(self.milestones),
                "success": success,
                "result": result
            }
        )

        self._emit(event)

        # Reset state
        self.current_task = None
        self.start_time = None
        self.milestones = []
        self.stages = []
        self.current_stage_index = 0

    def get_elapsed_time(self) -> float:
        """Get elapsed time since task start in seconds."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

    def _emit(self, event: ProgressEvent):
        """Emit event to all listeners."""
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Progress listener error: {e}")

    # Built-in Listeners

    @staticmethod
    def console_listener(event: ProgressEvent):
        """
        Default console progress listener with color and formatting.

        Displays progress updates with emoji indicators and colored output.
        """
        event_type = event.type

        if event_type == ProgressEventType.TASK_START:
            print(f"\n🚀 Starting: {event.message}")
            print(f"   Task ID: {event.task_id}")
            if "stages" in event.metadata:
                print(f"   Stages: {', '.join(event.metadata['stages'])}")

        elif event_type == ProgressEventType.PROGRESS_UPDATE:
            progress_pct = event.progress * 100
            stage_info = f"[{event.stage}] " if event.stage else ""
            print(f"📊 {stage_info}{progress_pct:.0f}% - {event.message}")

            # Show additional metadata if present
            if "findings" in event.metadata:
                print(f"   └─ Findings: {event.metadata['findings']}")
            if "warnings" in event.metadata:
                print(f"   └─ Warnings: {event.metadata['warnings']}")

        elif event_type == ProgressEventType.MILESTONE:
            milestone = event.metadata.get("milestone", {})
            print(f"✅ Milestone: {milestone.get('name', 'Unknown')}")
            if milestone_data := milestone.get("data"):
                for key, value in milestone_data.items():
                    print(f"   └─ {key}: {value}")

        elif event_type == ProgressEventType.TASK_COMPLETE:
            duration = event.metadata.get("duration", 0)
            print(f"\n✅ COMPLETE - Duration: {duration:.1f}s")
            print(f"   Milestones: {event.metadata.get('milestones_count', 0)}")

        elif event_type == ProgressEventType.TASK_FAILED:
            duration = event.metadata.get("duration", 0)
            print(f"\n❌ FAILED - Duration: {duration:.1f}s")
            print(f"   Reason: {event.message}")

        elif event_type == ProgressEventType.WARNING:
            print(f"⚠️  Warning: {event.message}")

        elif event_type == ProgressEventType.INFO:
            print(f"ℹ️  {event.message}")

    @staticmethod
    def file_listener(filepath: str) -> Callable[[ProgressEvent], None]:
        """
        Create file-based progress listener.

        Args:
            filepath: Path to log file

        Returns:
            Listener function that writes to file
        """
        def listener(event: ProgressEvent):
            with open(filepath, 'a') as f:
                timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {event.type.value} - {event.message}\n")

                if event.progress > 0:
                    f.write(f"  Progress: {event.progress * 100:.1f}%\n")

                if event.metadata:
                    f.write(f"  Metadata: {event.metadata}\n")

                f.write("\n")

        return listener

    @staticmethod
    def json_listener(filepath: str) -> Callable[[ProgressEvent], None]:
        """
        Create JSON-based progress listener.

        Args:
            filepath: Path to JSON log file

        Returns:
            Listener function that writes JSON events
        """
        import json

        def listener(event: ProgressEvent):
            event_data = {
                "type": event.type.value,
                "timestamp": event.timestamp.isoformat(),
                "task_id": event.task_id,
                "message": event.message,
                "progress": event.progress,
                "stage": event.stage,
                "metadata": event.metadata
            }

            with open(filepath, 'a') as f:
                json.dump(event_data, f)
                f.write('\n')

        return listener


def main():
    """Test progress reporter."""
    print("=" * 80)
    print("Progress Reporter - Test")
    print("=" * 80)

    # Create reporter
    reporter = ProgressReporter()

    # Add console listener
    reporter.add_listener(ProgressReporter.console_listener)

    # Start task with stages
    reporter.start_task(
        task_id="test-task-001",
        description="Test orchestration workflow",
        stages=["initialization", "analysis", "fixing", "validation"],
        metadata={"target": "safe_test.cpp"}
    )

    # Simulate progress updates
    time.sleep(0.5)

    reporter.update_progress(
        progress=0.1,
        message="Initializing agents...",
        stage="initialization"
    )

    time.sleep(0.5)

    reporter.update_progress(
        progress=0.3,
        message="Running multi-agent debugging system...",
        stage="analysis",
        metadata={"agent": "multi-agent-debugging-system"}
    )

    time.sleep(0.5)

    reporter.milestone(
        name="Analysis Complete",
        data={"findings": 47, "critical": 3}
    )

    reporter.update_progress(
        progress=0.5,
        message="Analyzing with clang-tidy...",
        stage="analysis",
        metadata={"findings": 125}
    )

    time.sleep(0.5)

    reporter.milestone(
        name="Static Analysis Complete",
        data={"total_findings": 172}
    )

    reporter.update_progress(
        progress=0.7,
        message="Applying critical fixes...",
        stage="fixing",
        metadata={"fixes_applied": 3}
    )

    time.sleep(0.5)

    reporter.warning("Build warning detected, will retry with different approach")

    time.sleep(0.5)

    reporter.update_progress(
        progress=0.9,
        message="Running validation tests...",
        stage="validation"
    )

    time.sleep(0.5)

    reporter.milestone(
        name="Tests Passed",
        data={"passed": 99, "failed": 0}
    )

    # Complete task
    reporter.complete_task(
        success=True,
        message="All validations passed",
        result={"status": "success", "issues_fixed": 3}
    )

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()