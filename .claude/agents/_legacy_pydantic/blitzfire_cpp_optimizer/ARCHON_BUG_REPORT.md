# Archon MCP Server Bug Report

## Issue Summary
The Archon MCP server has critical bugs preventing all tool calls from working.

## Environment
- **Archon MCP Server**: v1.12.2
- **MCP Protocol**: 2025-06-18
- **Container**: archon-mcp (Docker)
- **API Server**: Working correctly at http://archon-server:8181

## Symptoms
1. **All `tools/call` requests fail** with "Invalid request parameters"
2. **All `tools/list` requests fail** with "Invalid request parameters"
3. **Session state management broken** ("Received request before initialization was complete")

## Root Cause Analysis

### 1. Pydantic Schema Validation Bug
The server logs show validation errors:
```
CallToolRequest.params.name
  Field required [type=missing, input_value={'name': 'list_projects', 'arguments': {}}, input_type=dict]
```

The MCP server expects `CallToolRequest.params.name` but standard MCP format sends `{"name": "tool_name", "arguments": {...}}` which should be valid.

### 2. Request Routing Failure
Server attempts to validate every request against ALL request types simultaneously:
- PingRequest.method
- InitializeRequest.method
- CompleteRequest.method
- CallToolRequest.method
- etc.

This indicates the request dispatcher is broken and not routing to the correct validator.

### 3. State Management Bug
Even after successful initialization, server reports:
```
Failed to validate request: Received request before initialization was complete
```

## Reproduction Steps

1. Initialize MCP session (works correctly)
2. Call any tool with standard MCP format:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "list_projects",
       "arguments": {}
     },
     "id": 1
   }
   ```
3. **Result**: Always returns "Invalid request parameters"

## Expected Behavior
Tool calls should work according to MCP 2.0 specification.

## Actual Behavior
All tool calls fail with validation errors.

## Workaround
Direct API calls work correctly:
- `GET http://archon-server:8181/api/projects` ✅
- `GET http://archon-server:8181/api/tasks` ✅
- `POST http://archon-server:8181/api/rag/query` ✅

## Fix Required
1. **Fix Pydantic schemas** for MCP request validation
2. **Fix request routing** to dispatch to correct validator
3. **Fix session state management** initialization tracking
4. **Add proper MCP protocol compliance testing**

## Priority
**HIGH** - This breaks the entire MCP interface making Archon unusable via MCP protocol.

## Files to Check
- `src/mcp_server/` - MCP request validation
- Pydantic models for `CallToolRequest`, `ListToolsRequest`
- Session management and initialization state tracking