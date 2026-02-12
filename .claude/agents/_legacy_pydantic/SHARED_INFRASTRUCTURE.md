# Shared Infrastructure & Tools
## Available to All Agents and Subagents

**Last Updated**: 2025-09-30
**Status**: ✅ Production Ready

---

## 🗂️ Clang-Tidy Logging Infrastructure

### Directory: `/tmp/clang_tidy_logs`

**Purpose**: Centralized logging and data persistence for all clang-tidy analysis, fixing, and monitoring operations.

**Status**: ✅ **ACTIVE** - All agents should utilize this directory for coordination and learning.

---

## 📊 What's Stored in `/tmp/clang_tidy_logs`

### 1. **Comprehensive Analysis Reports**
```
comprehensive_report_<timestamp>.txt
```
**Contains**:
- Executive summary of all codebase issues
- Categorized warnings by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Recommended action plans
- Statistics and metrics

**Usage**:
- Check before starting new analysis to avoid duplicate work
- Reference for understanding codebase quality state
- Historical comparison for trend analysis

---

### 2. **Real-Time Agent Logs**
```
agent.log
clang_tidy_agent_<timestamp>.log
```
**Contains**:
- Timestamped event logs: `[2025-09-30 00:46:35] [INFO] ...`
- Analysis progress for each C++ file
- Error messages, warnings, and success notifications
- Performance metrics (files analyzed, issues found/fixed)
- Thread-safe concurrent operation logs

**Usage**:
```bash
# Monitor live progress
tail -f /tmp/clang_tidy_logs/agent.log

# Search for specific events
grep "ERROR" /tmp/clang_tidy_logs/agent.log
grep "SUCCESS" /tmp/clang_tidy_logs/agent.log
```

---

### 3. **Task Tracking Files**
```
clang_tidy_tasks_<timestamp>.json
```
**Contains**:
- JSON-structured list of ALL detected clang-tidy issues
- Priority rankings (0=critical bugprone/cert, 6=low priority)
- Fix status tracking (pending, attempted, successful, failed)
- File metadata (paths, line numbers, column numbers, check names)
- Issue dependencies and relationships

**Example Structure**:
```json
{
  "tasks": [
    {
      "id": "task_001",
      "file": "src/core.cpp",
      "line": 42,
      "column": 10,
      "check": "modernize-use-nullptr",
      "priority": 4,
      "status": "pending",
      "message": "Use nullptr instead of 0",
      "estimated_effort": "trivial"
    }
  ],
  "summary": {
    "total_issues": 150,
    "critical": 5,
    "high": 20,
    "medium": 75,
    "low": 50
  }
}
```

**Usage**:
- Load tasks for batch processing
- Track fix progress across sessions
- Coordinate work between multiple agents
- Avoid duplicate fix attempts

---

### 4. **Startup & System Logs**
```
startup.log
```
**Contains**:
- System initialization events
- Dependency checks (clang-tidy, python3 availability)
- Process management (PID tracking, start/stop events)
- Configuration validation

**Usage**:
- Verify system readiness before operations
- Debug initialization issues
- Track system uptime and restarts

---

### 5. **Temporary Analysis Outputs**
```
clang_tidy_output_<filename>_<pid>.txt
clang_tidy_comprehensive_<timestamp>.log
```
**Contains**:
- Raw clang-tidy command output
- Compilation errors and warnings
- Per-file analysis results
- Intermediate processing data

**Usage**:
- Parse for detailed warning information
- Debug analysis failures
- Extract context for AI processing

---

## 🤖 Agent Integration Patterns

### Pattern 1: Pre-Analysis Check (Recommended)
```python
from pathlib import Path
import json
from datetime import datetime, timedelta

def check_recent_analysis(target_file: str) -> dict:
    """Check if file was recently analyzed."""
    log_dir = Path("/tmp/clang_tidy_logs")

    # Check for recent task files (within last hour)
    cutoff_time = datetime.now() - timedelta(hours=1)

    for task_file in log_dir.glob("clang_tidy_tasks_*.json"):
        if task_file.stat().st_mtime > cutoff_time.timestamp():
            with open(task_file) as f:
                data = json.load(f)
                # Check if our target file has recorded issues
                for task in data.get("tasks", []):
                    if task["file"] == target_file:
                        return {
                            "recently_analyzed": True,
                            "issues_found": len([t for t in data["tasks"] if t["file"] == target_file]),
                            "task_file": str(task_file)
                        }

    return {"recently_analyzed": False}
```

---

### Pattern 2: Historical Pattern Analysis
```python
def analyze_historical_patterns() -> dict:
    """Extract patterns from historical logs."""
    log_dir = Path("/tmp/clang_tidy_logs")
    patterns = {
        "common_issues": {},
        "frequent_files": {},
        "fix_success_rate": {}
    }

    # Analyze all comprehensive reports
    for report in log_dir.glob("comprehensive_report_*.txt"):
        with open(report) as f:
            content = f.read()
            # Extract patterns (example)
            if "modernize-use-nullptr" in content:
                patterns["common_issues"]["nullptr"] = patterns["common_issues"].get("nullptr", 0) + 1

    return patterns
```

---

### Pattern 3: Live Progress Monitoring
```python
import subprocess

def monitor_agent_progress():
    """Stream live agent progress."""
    log_file = Path("/tmp/clang_tidy_logs/agent.log")

    if log_file.exists():
        # Tail the log file
        process = subprocess.Popen(
            ["tail", "-f", str(log_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in iter(process.stdout.readline, ''):
            if "[ERROR]" in line:
                print(f"🔴 {line.strip()}")
            elif "[SUCCESS]" in line:
                print(f"✅ {line.strip()}")
            elif "[INFO]" in line:
                print(f"ℹ️  {line.strip()}")
```

---

### Pattern 4: Task Coordination
```python
def claim_next_task(agent_id: str) -> dict:
    """Claim the next highest-priority unclaimed task."""
    log_dir = Path("/tmp/clang_tidy_logs")

    # Find most recent task file
    task_files = sorted(log_dir.glob("clang_tidy_tasks_*.json"),
                       key=lambda p: p.stat().st_mtime,
                       reverse=True)

    if not task_files:
        return {"error": "No task files found"}

    with open(task_files[0]) as f:
        data = json.load(f)

    # Find highest priority pending task
    for task in sorted(data.get("tasks", []), key=lambda t: t["priority"]):
        if task["status"] == "pending":
            # Claim it
            task["status"] = "in_progress"
            task["assigned_to"] = agent_id
            task["claimed_at"] = datetime.now().isoformat()

            # Save updated tasks
            with open(task_files[0], 'w') as f:
                json.dump(data, f, indent=2)

            return task

    return {"error": "No pending tasks available"}
```

---

## 🔗 Integration with Awareness Orchestrator

### Agents That SHOULD Use This Infrastructure

#### ✅ **Primary Consumers**
1. **clang-tidy-analyzer** - Read historical reports, write new analysis
2. **clang-tidy-critical-fixer** - Read task lists, track fix attempts
3. **clang-tidy-safety-fixer** - Coordinate with other fixers via logs
4. **clang-tidy-quality-fixer** - Access priority queues from task files
5. **clang-tidy-validator** - Verify fixes via before/after logs
6. **zero-warnings-enforcer** - Monitor for new warnings in logs

#### 🔄 **Secondary Consumers**
7. **Pattern Recognition System** - Extract historical patterns
8. **Proactive Suggestions Engine** - Predict issues from trends
9. **Metrics Dashboard** - Aggregate statistics from logs
10. **Build System Adapter** - Validate fixes via log correlation
11. **Context Chaining System** - Build agent context from history

---

## 📋 Agent-Specific Usage Guidelines

### For `clang-tidy-analyzer`
**MUST DO**:
- ✅ Check `/tmp/clang_tidy_logs/comprehensive_report_*.txt` before full codebase scan
- ✅ Write new findings to timestamped task files
- ✅ Update `agent.log` with progress for each file analyzed
- ✅ Record analysis duration and issue counts

**AVOID**:
- ❌ Re-analyzing files with recent (< 1 hour) analysis logs
- ❌ Creating duplicate task entries for same issues
- ❌ Ignoring existing priority classifications

---

### For `clang-tidy-critical-fixer`, `clang-tidy-safety-fixer`, `clang-tidy-quality-fixer`
**MUST DO**:
- ✅ Load tasks from most recent `clang_tidy_tasks_*.json`
- ✅ Update task status after each fix attempt
- ✅ Log success/failure with detailed error messages
- ✅ Record fix duration for performance tracking

**AVOID**:
- ❌ Attempting fixes without checking task status (avoid race conditions)
- ❌ Failing silently without logging errors
- ❌ Overwriting task files (use atomic updates)

---

### For `clang-tidy-validator`
**MUST DO**:
- ✅ Compare before/after states using log timestamps
- ✅ Verify no new issues introduced (compare task counts)
- ✅ Update task status to "verified" or "failed_validation"
- ✅ Log validation metrics (build success, test pass rate)

---

### For Awareness Orchestrator Components
**MUST DO**:
- ✅ **Pattern Recognition**: Parse all log files for pattern extraction
- ✅ **Proactive Suggestions**: Use historical data for predictions
- ✅ **Metrics Dashboard**: Aggregate stats from all timestamped logs
- ✅ **Build System Adapter**: Correlate build results with fix attempts
- ✅ **Context Chaining**: Build rich context from recent activity

---

## 🛠️ Utility Functions (Copy to Your Agent)

### Read Latest Task File
```python
def get_latest_task_file() -> Path:
    """Get the most recent task file."""
    log_dir = Path("/tmp/clang_tidy_logs")
    task_files = list(log_dir.glob("clang_tidy_tasks_*.json"))
    if not task_files:
        raise FileNotFoundError("No task files found in /tmp/clang_tidy_logs")
    return max(task_files, key=lambda p: p.stat().st_mtime)
```

### Append to Agent Log
```python
def log_agent_event(level: str, message: str):
    """Thread-safe logging to agent.log."""
    import threading
    from datetime import datetime

    log_file = Path("/tmp/clang_tidy_logs/agent.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"

    lock = threading.Lock()
    with lock:
        with open(log_file, "a") as f:
            f.write(log_entry)
```

### Load Task Statistics
```python
def get_task_statistics() -> dict:
    """Get current task statistics."""
    task_file = get_latest_task_file()
    with open(task_file) as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    return {
        "total": len(tasks),
        "pending": len([t for t in tasks if t["status"] == "pending"]),
        "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
        "completed": len([t for t in tasks if t["status"] == "completed"]),
        "failed": len([t for t in tasks if t["status"] == "failed"])
    }
```

---

## 🚨 Critical Guidelines

### Thread Safety
- **Always use file locks** when updating shared task files
- **Use atomic writes** (write to temp file, then rename)
- **Verify file exists** before reading to handle race conditions

### Error Handling
- **Log all errors** to `agent.log` before raising exceptions
- **Include context** (file path, line number, operation attempted)
- **Gracefully degrade** if logs unavailable (don't block operation)

### Performance
- **Cache task file paths** instead of globbing repeatedly
- **Stream large log files** instead of reading entirely into memory
- **Use tail commands** for real-time monitoring instead of polling

### Cleanup
- **Do NOT delete** log files (let system manage /tmp)
- **Rotate logs** only when directory exceeds 100MB
- **Keep comprehensive reports** for at least 7 days

---

## 📞 Support & Troubleshooting

### Directory Missing?
```bash
# Create directory if missing
mkdir -p /tmp/clang_tidy_logs
chmod 755 /tmp/clang_tidy_logs
```

### Verify Directory Access
```bash
# Check permissions
ls -la /tmp/clang_tidy_logs

# Test write access
echo "test" > /tmp/clang_tidy_logs/test.log
rm /tmp/clang_tidy_logs/test.log
```

### Monitor System Activity
```bash
# Watch live updates
watch -n 2 'ls -lth /tmp/clang_tidy_logs | head -10'

# Count current issues
tail -100 /tmp/clang_tidy_logs/agent.log | grep -c "warning:"
```

---

## 🎯 Success Metrics

Agents using this infrastructure should achieve:
- ✅ **Zero duplicate work** (< 5% re-analysis of recently scanned files)
- ✅ **Coordination efficiency** (< 1% task claim conflicts)
- ✅ **Learning acceleration** (50%+ faster fixes on recurring issues)
- ✅ **Historical awareness** (100% of agents check logs before operating)

---

**For Questions or Issues**: Update this document or contact the Awareness Orchestrator team.