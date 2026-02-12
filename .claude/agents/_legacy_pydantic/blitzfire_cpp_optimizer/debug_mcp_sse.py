#!/usr/bin/env python3
"""Debug MCP SSE Response Format"""

import requests
import json

def debug_sse_response():
    """Debug the SSE response format"""
    print("="*70)
    print("MCP SSE RESPONSE DEBUGGER")
    print("="*70)

    # Initialize session
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream,application/json"
    }

    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {}
        },
        "id": 1
    }

    print("\n1. INITIALIZE AND CAPTURE SESSION")
    print("-"*40)

    r = requests.post("http://archon-mcp:8051/mcp", headers=headers, json=init_payload)
    session_id = r.headers.get('mcp-session-id')

    print(f"Session ID: {session_id}")
    print(f"Response Headers: {dict(r.headers)}")
    print("\nRaw SSE Response (first 1000 chars):")
    print(r.text[:1000])

    # Parse initialization response to see tool hints
    for line in r.text.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'result' in data and 'instructions' in data['result']:
                    instructions = data['result']['instructions']
                    print("\n2. SERVER INSTRUCTIONS")
                    print("-"*40)
                    print(instructions[:2000])  # First 2000 chars of instructions

                    # Look for tool function examples
                    if 'list_projects()' in instructions:
                        print("\n✅ Found function signature examples in instructions!")
            except:
                pass

    # Now test with session
    print("\n3. TEST EMPTY PARAMS WITH SESSION")
    print("-"*40)

    headers['MCP-Session-Id'] = session_id

    # Try with empty params
    test_payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 2
    }

    r2 = requests.post("http://archon-mcp:8051/mcp", headers=headers, json=test_payload)
    print(f"Status: {r2.status_code}")
    print("Raw response:")
    print(r2.text[:500])

    # Try without params key at all
    print("\n4. TEST WITHOUT PARAMS KEY")
    print("-"*40)

    test_payload2 = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 3
    }

    r3 = requests.post("http://archon-mcp:8051/mcp", headers=headers, json=test_payload2)
    print(f"Status: {r3.status_code}")
    print("Raw response:")
    for line in r3.text.split('\n')[:10]:
        if line.strip():
            print(f"  {line}")

    # Check if it's expecting a different structure
    print("\n5. TEST NOTIFICATIONS FORMAT")
    print("-"*40)

    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
        # No ID for notifications
    }

    r4 = requests.post("http://archon-mcp:8051/mcp", headers=headers, json=notification)
    print(f"Status: {r4.status_code}")
    print("Response:")
    for line in r4.text.split('\n')[:10]:
        if line.strip():
            print(f"  {line}")

if __name__ == "__main__":
    debug_sse_response()