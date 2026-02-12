# Archon MCP Hooks Documentation

## Overview

This directory contains hooks for integrating with the Archon MCP (Model Control Protocol) server. These hooks provide health monitoring, tool status checking, and session initialization capabilities.

## Available Hooks

### 1. `archon_status_hook.sh` - Comprehensive Status Monitor
**Purpose**: Provides detailed health and tool status information for the Archon MCP server.

**Features**:
- 🔍 Server discovery with retry logic
- 📊 Health endpoint status checking
- 📦 Tool availability monitoring
- 🔧 Server capability detection
- 📝 Useful command suggestions

**Usage**:
```bash
bash .claude/hooks/archon_status_hook.sh
```

**Output includes**:
- Connection status
- Health check results
- Available tools listing
- Server capabilities
- Troubleshooting guidance if connection fails

### 2. `session_start_hook.sh` - Quick Session Initializer
**Purpose**: Lightweight hook for session initialization with quick status display.

**Features**:
- 🚀 Fast connection establishment
- ✅ Quick health/tool status icons
- 🔗 Environment variable setup
- 📝 Quick command references

**Usage**:
```bash
bash .claude/hooks/session_start_hook.sh
```

**Best for**:
- Session start/reconnection
- Quick status checks
- Minimal output requirements

### 3. `simple_archon_connect.sh` - Basic Connection Hook
**Purpose**: Original simple connection script with basic retry logic.

**Features**:
- Basic connection testing
- Environment variable export
- Simple status output

## Status Indicators

The hooks use visual indicators for quick status assessment:

| Indicator | Meaning |
|-----------|---------|
| ✅ | Fully operational |
| ⚠️ | Partially configured/responding |
| ❌ | Not available/failed |
| ❓ | Unknown status |
| 🟢 | Service running |
| 🟡 | Service degraded |
| 🔴 | Service down |

## Environment Variables

All hooks set the following environment variables when successful:
- `MCP_SERVER_URL` - The MCP server endpoint URL
- `ARCHON_MCP_URL` - Alternative name for the same endpoint

## Troubleshooting

### Connection Failed
If the hooks report connection failure:

1. **Check container status**:
   ```bash
   docker ps | grep archon
   ```

2. **Verify network connectivity**:
   ```bash
   docker network ls
   curl -v http://archon-mcp:8051/health
   ```

3. **Check container logs**:
   ```bash
   docker logs archon-mcp
   ```

### Endpoints Not Configured
If you see "Endpoint not configured" messages:
- The server is running but specific endpoints may not be implemented
- This is normal if the MCP server is in basic mode
- The server can still receive and process requests

## Integration with Claude

These hooks can be configured in Claude's settings to run automatically:
- On session start
- On reconnection
- On manual trigger

## Quick Commands Reference

```bash
# Full status check
bash .claude/hooks/archon_status_hook.sh

# Quick session init
bash .claude/hooks/session_start_hook.sh

# Direct health check
curl -s http://archon-mcp:8051/health

# List available tools (JSON-RPC)
curl -s -X POST http://archon-mcp:8051/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'

# Check specific endpoint
curl -s http://archon-mcp:8051/mcp/tools
```

## Hook Configuration

To use these hooks automatically, add to your Claude settings:

```json
{
  "hooks": {
    "session_start": ".claude/hooks/session_start_hook.sh",
    "health_check": ".claude/hooks/archon_status_hook.sh"
  }
}
```

## Development

To create custom hooks:
1. Follow the existing script patterns
2. Use consistent color coding and output formatting
3. Include error handling and retry logic
4. Export required environment variables
5. Provide clear status indicators

## Notes

- All hooks use bash and require curl
- Timeout values are optimized for quick response (1-3 seconds)
- Retry logic prevents false negatives from transient network issues
- Color output enhances readability in terminal environments