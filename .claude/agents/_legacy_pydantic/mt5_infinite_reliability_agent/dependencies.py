"""
Dependencies for MT5 Infinite Reliability Agent.

Provides context and state management for MQL5 optimization workflows.
Follows the awareness_orchestrator pattern for agent coordination.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any, Callable
from pathlib import Path
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    """Progress event for workflow tracking."""
    event_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDependencies:
    """
    Dependencies injected into agent runtime context.

    Provides access to:
    - File paths and analysis configuration
    - Optimization workflow state
    - Progress tracking and reporting
    - Agent coordination utilities
    """

    # Input/Output Paths
    source_code_path: Optional[Path] = None
    output_path: Optional[Path] = None
    target_directory: Path = field(
        default_factory=lambda: Path("/Users/shemarrigg/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE")
    )

    # Analysis Configuration
    verification_depth: Literal["basic", "standard", "comprehensive"] = "standard"
    analysis_mode: Literal["analyze", "optimize", "verify", "full"] = "full"
    dimensions: List[str] = field(
        default_factory=lambda: ["performance", "memory", "reliability", "ftmo_compliance"]
    )

    # Optimization Settings
    preserve_features: bool = True  # CRITICAL: Never alter trading logic
    auto_apply: bool = True
    enable_rollback: bool = True
    add_proof_annotations: bool = True

    # FTMO Compliance Settings
    ftmo_compliance_required: bool = True
    daily_loss_limit: float = 5.0
    max_drawdown_limit: float = 10.0

    # Proof Generation
    proof_level: Literal["basic", "detailed", "comprehensive"] = "detailed"

    # Session Context
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    orchestrator_id: Optional[str] = None  # For awareness_orchestrator integration

    # Escalation Configuration
    escalation_tier: Literal["fast", "smart", "thorough", "emergency"] = "fast"
    max_escalation_attempts: int = 3

    # Configuration Overrides
    max_code_size_kb: Optional[int] = None
    timeout_seconds: Optional[int] = None
    debug: bool = False

    # Internal State (not for user configuration)
    _snapshot_stack: List[str] = field(default_factory=list, init=False, repr=False)
    _transformation_count: int = field(default=0, init=False, repr=False)
    _progress_events: List[ProgressEvent] = field(default_factory=list, init=False, repr=False)
    _agent_findings: List[Dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    _escalation_history: List[str] = field(default_factory=list, init=False, repr=False)
    _progress_callback: Optional[Callable[[ProgressEvent], None]] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Validate paths and configuration."""
        if self.source_code_path:
            self.source_code_path = Path(self.source_code_path)
            if not self.source_code_path.exists():
                logger.warning(f"Source code path does not exist: {self.source_code_path}")

        if self.output_path:
            self.output_path = Path(self.output_path)
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure target directory exists
        self.target_directory = Path(self.target_directory)
        if not self.target_directory.exists():
            logger.warning(f"Target directory does not exist: {self.target_directory}")

    # ========================================================================
    # DIMENSION VALIDATION
    # ========================================================================

    def validate_dimensions(self) -> bool:
        """Validate analysis dimensions are supported."""
        valid_dimensions = {
            "performance", "memory", "reliability", "ftmo_compliance",
            "backtest_accuracy", "event_driven", "security", "robustness",
            "temporal", "concurrency", "probabilistic", "adaptive"
        }
        for dim in self.dimensions:
            if dim not in valid_dimensions:
                logger.error(f"Invalid dimension: {dim}")
                return False
        return True

    # ========================================================================
    # SNAPSHOT MANAGEMENT (Rollback Capability)
    # ========================================================================

    def add_snapshot(self, code_snapshot: str) -> None:
        """Add code snapshot for rollback capability."""
        if self.enable_rollback:
            self._snapshot_stack.append(code_snapshot)
            logger.debug(f"Snapshot added (stack size: {len(self._snapshot_stack)})")

    def rollback(self) -> Optional[str]:
        """Rollback to previous code state."""
        if self._snapshot_stack:
            snapshot = self._snapshot_stack.pop()
            logger.info("Rolled back to previous snapshot")
            self._escalation_history.append(f"rollback_{datetime.now().isoformat()}")
            return snapshot
        logger.warning("No snapshots available for rollback")
        return None

    def clear_snapshots(self) -> None:
        """Clear all snapshots (commit transformations)."""
        self._snapshot_stack.clear()
        logger.info("All snapshots cleared - transformations committed")

    # ========================================================================
    # TRANSFORMATION TRACKING
    # ========================================================================

    def increment_transformation_count(self) -> int:
        """Track number of transformations applied."""
        self._transformation_count += 1
        return self._transformation_count

    def get_transformation_count(self) -> int:
        """Get current transformation count."""
        return self._transformation_count

    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================

    def set_progress_callback(self, callback: Callable[[ProgressEvent], None]) -> None:
        """Set callback for progress events."""
        self._progress_callback = callback

    def emit_progress(self, event_type: str, message: str, metadata: Dict[str, Any] = None) -> None:
        """Emit a progress event."""
        event = ProgressEvent(
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
        self._progress_events.append(event)

        # Log the event
        logger.info(f"[{event_type}] {message}")

        # Call callback if set
        if self._progress_callback:
            try:
                self._progress_callback(event)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def get_progress_history(self) -> List[Dict[str, Any]]:
        """Get all progress events."""
        return [
            {
                "event_type": e.event_type,
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in self._progress_events
        ]

    # ========================================================================
    # AGENT FINDINGS MANAGEMENT
    # ========================================================================

    def record_agent_findings(self, agent_type: str, findings: Dict[str, Any]) -> None:
        """Record findings from a subagent."""
        self._agent_findings.append({
            "agent_type": agent_type,
            "timestamp": datetime.now().isoformat(),
            "findings": findings
        })
        logger.info(f"Recorded findings from {agent_type}")

    def get_all_findings(self) -> List[Dict[str, Any]]:
        """Get all agent findings."""
        return self._agent_findings

    def get_findings_by_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get findings from a specific agent type."""
        return [f for f in self._agent_findings if f["agent_type"] == agent_type]

    # ========================================================================
    # ESCALATION MANAGEMENT
    # ========================================================================

    def escalate(self, reason: str) -> bool:
        """Escalate to next tier if possible."""
        tier_order = ["fast", "smart", "thorough", "emergency"]
        current_idx = tier_order.index(self.escalation_tier)

        if current_idx < len(tier_order) - 1:
            old_tier = self.escalation_tier
            self.escalation_tier = tier_order[current_idx + 1]
            self._escalation_history.append(f"{old_tier}->{self.escalation_tier}:{reason}")
            self.emit_progress("escalation", f"Escalated from {old_tier} to {self.escalation_tier}: {reason}")
            return True
        else:
            logger.warning("Already at maximum escalation tier (emergency)")
            return False

    def get_escalation_history(self) -> List[str]:
        """Get escalation history."""
        return self._escalation_history

    # ========================================================================
    # FTMO COMPLIANCE HELPERS
    # ========================================================================

    def get_ftmo_limits(self) -> Dict[str, float]:
        """Get FTMO compliance limits."""
        return {
            "daily_loss_limit": self.daily_loss_limit,
            "max_drawdown_limit": self.max_drawdown_limit,
            "daily_loss_buffer": self.daily_loss_limit - 0.5,  # 0.5% safety margin
            "max_drawdown_buffer": self.max_drawdown_limit - 0.5
        }

    # ========================================================================
    # AWARENESS ORCHESTRATOR INTEGRATION
    # ========================================================================

    def sync_with_orchestrator(self, orchestrator_id: str, context: Dict[str, Any]) -> None:
        """Sync state with awareness_orchestrator."""
        self.orchestrator_id = orchestrator_id
        self.emit_progress("orchestrator_sync", f"Synced with orchestrator: {orchestrator_id}", context)
        logger.info(f"Synced with awareness_orchestrator: {orchestrator_id}")

    def prepare_handoff(self, target_agent: str) -> Dict[str, Any]:
        """Prepare context for handoff to another agent."""
        return {
            "source_agent": "mt5_infinite_reliability_agent",
            "target_agent": target_agent,
            "session_id": self.session_id,
            "orchestrator_id": self.orchestrator_id,
            "transformation_count": self._transformation_count,
            "escalation_tier": self.escalation_tier,
            "escalation_history": self._escalation_history,
            "progress_events": self.get_progress_history(),
            "findings_summary": {
                "total_findings": len(self._agent_findings),
                "by_agent": {
                    agent: len([f for f in self._agent_findings if f["agent_type"] == agent])
                    for agent in set(f["agent_type"] for f in self._agent_findings)
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def from_settings(cls, settings, **kwargs):
        """
        Create dependencies from settings with overrides.

        Args:
            settings: Settings instance
            **kwargs: Override values

        Returns:
            Configured AgentDependencies instance
        """
        # Handle 'mode' parameter (rename to 'analysis_mode')
        if 'mode' in kwargs:
            kwargs['analysis_mode'] = kwargs.pop('mode')

        return cls(
            verification_depth=kwargs.get("verification_depth", "standard"),
            analysis_mode=kwargs.get("analysis_mode", "full"),
            proof_level=kwargs.get("proof_level", settings.default_proof_level),
            max_code_size_kb=kwargs.get("max_code_size_kb", settings.max_code_size_kb),
            timeout_seconds=kwargs.get("timeout_seconds", settings.analysis_timeout_seconds),
            enable_rollback=kwargs.get("enable_rollback", settings.enable_atomic_rollback),
            debug=kwargs.get("debug", settings.debug),
            preserve_features=kwargs.get("preserve_features", True),
            ftmo_compliance_required=kwargs.get("ftmo_compliance_required", True),
            **{k: v for k, v in kwargs.items()
               if k not in [
                   "verification_depth", "analysis_mode", "proof_level",
                   "max_code_size_kb", "timeout_seconds", "enable_rollback",
                   "debug", "preserve_features", "ftmo_compliance_required"
               ]}
        )

    @classmethod
    def create_default(cls) -> "AgentDependencies":
        """Create dependencies with default configuration."""
        return cls()

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        return {
            "source_code_path": str(self.source_code_path) if self.source_code_path else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "target_directory": str(self.target_directory),
            "verification_depth": self.verification_depth,
            "analysis_mode": self.analysis_mode,
            "dimensions": self.dimensions,
            "preserve_features": self.preserve_features,
            "auto_apply": self.auto_apply,
            "enable_rollback": self.enable_rollback,
            "proof_level": self.proof_level,
            "ftmo_compliance_required": self.ftmo_compliance_required,
            "escalation_tier": self.escalation_tier,
            "session_id": self.session_id,
            "orchestrator_id": self.orchestrator_id,
            "transformation_count": self._transformation_count,
            "snapshot_stack_size": len(self._snapshot_stack),
            "progress_event_count": len(self._progress_events),
            "agent_findings_count": len(self._agent_findings),
            "escalation_history": self._escalation_history
        }

    def to_json(self) -> str:
        """Export configuration as JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def get_dependencies(
    source_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    **kwargs
) -> AgentDependencies:
    """
    Get configured agent dependencies.

    Args:
        source_path: Path to source MQL5 file
        output_path: Path for output
        **kwargs: Additional configuration

    Returns:
        Configured AgentDependencies instance
    """
    return AgentDependencies(
        source_code_path=source_path,
        output_path=output_path,
        **kwargs
    )
