# 🗂️ CRITICAL: Shared Infrastructure Notice

**ALL SUBAGENTS IN THIS DIRECTORY MUST READ THIS**

## Shared Logging & Coordination

All clang-tidy subagents use the shared infrastructure at:
```
/tmp/clang_tidy_logs
```

## 📖 Required Reading

**BEFORE OPERATION**: Read [`.claude/agents/SHARED_INFRASTRUCTURE.md`](../../SHARED_INFRASTRUCTURE.md)

This document contains:
- ✅ Complete logging directory structure
- ✅ Task coordination mechanisms
- ✅ Historical analysis patterns
- ✅ Integration code examples
- ✅ Thread safety guidelines
- ✅ Error handling best practices

## Quick Reference

### For Analysis Agents (clang-tidy-analyzer)
- Check for recent analysis before scanning
- Write findings to `clang_tidy_tasks_*.json`
- Update `agent.log` with progress
- Create `comprehensive_report_*.txt`

### For Fixer Agents (critical, safety, quality)
- Load tasks from latest `clang_tidy_tasks_*.json`
- Update task status after fixes
- Log success/failure to `agent.log`
- Record fix duration

### For Strategist & Validator
- Build strategies from historical task files
- Validate against before/after logs
- Track success rates across runs

### For zero-warnings-enforcer
- Monitor logs for new warnings
- Verify zero-warning compliance
- Track regression prevention

## Non-Compliance Consequences

Agents that don't use this infrastructure:
- ❌ Will duplicate work
- ❌ May have task conflicts
- ❌ Cannot learn from history
- ❌ Will operate inefficiently

## Questions?

Update [`SHARED_INFRASTRUCTURE.md`](../../SHARED_INFRASTRUCTURE.md) or contact the Awareness Orchestrator team.