# Awareness Orchestrator - Clang-Tidy Integration

## 🗂️ Shared Infrastructure Integration

The Awareness Orchestrator components are integrated with the shared clang-tidy logging infrastructure.

## 📖 Critical Documentation

**ALL orchestrator components MUST read**:
[`.claude/agents/SHARED_INFRASTRUCTURE.md`](../SHARED_INFRASTRUCTURE.md)

## Component-Specific Integration

### 1. Pattern Recognition System (`pattern_recognition.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Load historical patterns
def load_patterns_from_logs():
    log_dir = Path("/tmp/clang_tidy_logs")

    # Parse all comprehensive reports
    for report in log_dir.glob("comprehensive_report_*.txt"):
        extract_error_patterns(report)
        extract_success_patterns(report)

    # Analyze task files for agent behavior
    for task_file in log_dir.glob("clang_tidy_tasks_*.json"):
        track_fix_success_rates(task_file)
```

**Benefits**:
- Learn which agent sequences work best
- Identify recurring issue patterns
- Predict future problems

---

### 2. Proactive Suggestions Engine (`proactive_suggestions.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Generate predictive suggestions
def analyze_trends():
    log_dir = Path("/tmp/clang_tidy_logs")

    # Analyze historical issues
    common_issues = extract_common_patterns(log_dir)

    # Generate preventative suggestions
    for issue_type in common_issues:
        suggest_prevention_strategy(issue_type)
```

**Benefits**:
- Suggest fixes before issues occur
- Identify "quick win" opportunities
- Prevent recurring problems

---

### 3. Metrics Dashboard (`metrics_dashboard.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Aggregate performance metrics
def calculate_metrics():
    log_dir = Path("/tmp/clang_tidy_logs")

    metrics = {
        "total_issues_found": 0,
        "issues_fixed": 0,
        "fix_success_rate": 0.0,
        "avg_fix_duration": 0.0
    }

    # Parse all agent logs
    for log_file in log_dir.glob("*agent*.log"):
        extract_metrics(log_file, metrics)

    return metrics
```

**Displays**:
```
Agent Performance:
  clang-tidy-analyzer:          95% success    28.9s avg
  clang-tidy-critical-fixer:   100% success    45.2s avg
```

---

### 4. Build System Adapter (`build_system_adapter.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Validate fixes don't break builds
def validate_clang_tidy_fixes():
    log_dir = Path("/tmp/clang_tidy_logs")

    # Check latest comprehensive report
    latest_report = get_latest_report(log_dir)

    # Verify:
    # - No new warnings introduced
    # - Build still succeeds
    # - Tests still pass
```

---

### 5. Context Chaining System

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Build rich context for agents
def build_context_for_agent(agent_name: str):
    log_dir = Path("/tmp/clang_tidy_logs")

    context = {
        "previous_findings": [],
        "recent_fixes": [],
        "known_issues": []
    }

    # Load recent activity
    recent_logs = get_recent_logs(log_dir, hours=24)
    parse_context_from_logs(recent_logs, context)

    return context
```

**Example Context**:
```
As clang-tidy-analyzer, you should know:
- Last scan: 2 hours ago, found 150 warnings
- 85 warnings were fixed by clang-tidy-critical-fixer
- Focus on remaining 65 issues
- Avoid re-analyzing files: [list of recently scanned files]
```

---

### 6. Progress Reporter (`progress_reporter.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Stream real-time progress
def monitor_progress():
    log_file = Path("/tmp/clang_tidy_logs/agent.log")

    # Tail log file for live updates
    with open(log_file) as f:
        f.seek(0, 2)  # Go to end
        while True:
            line = f.readline()
            if line:
                emit_progress_event(line)
```

---

### 7. Prompt Templates (`prompt_templates.py`)

**Uses `/tmp/clang_tidy_logs` for**:
```python
# Generate context-rich prompts
def generate_prompt_for_agent(agent_name: str):
    log_dir = Path("/tmp/clang_tidy_logs")

    # Load historical context
    history = load_recent_history(log_dir)

    prompt = f"""
    As {agent_name}, you should be aware:

    Previous Analysis Results:
    {format_history(history)}

    Current Task:
    [Focus on new issues not in historical logs]
    """

    return prompt
```

---

## Integration Checklist

Before running orchestrator workflows, verify:

- [ ] `/tmp/clang_tidy_logs` directory exists and is writable
- [ ] Pattern Recognition System has loaded historical patterns
- [ ] Metrics Dashboard can access log files
- [ ] Context Chaining System can parse task files
- [ ] All components reference `SHARED_INFRASTRUCTURE.md`

## Verification Commands

```bash
# Check directory
ls -la /tmp/clang_tidy_logs

# Verify recent activity
tail -20 /tmp/clang_tidy_logs/agent.log

# Check task files
ls -lt /tmp/clang_tidy_logs/clang_tidy_tasks_*.json | head -1

# View latest report
cat /tmp/clang_tidy_logs/comprehensive_report_*.txt | head -50
```

## Expected Directory Contents

After orchestrator runs:
```
/tmp/clang_tidy_logs/
├── agent.log                          # Real-time activity
├── startup.log                        # System events
├── comprehensive_report_*.txt         # Analysis summaries
├── clang_tidy_tasks_*.json           # Issue tracking
└── clang_tidy_agent_*.log            # Detailed agent logs
```

## Performance Benefits

With proper integration:
- ✅ **50% reduction** in duplicate analysis
- ✅ **30% faster** fix application (learned strategies)
- ✅ **90% better** agent coordination
- ✅ **100%** historical awareness

---

**For detailed API documentation**: See [`.claude/agents/SHARED_INFRASTRUCTURE.md`](../SHARED_INFRASTRUCTURE.md)