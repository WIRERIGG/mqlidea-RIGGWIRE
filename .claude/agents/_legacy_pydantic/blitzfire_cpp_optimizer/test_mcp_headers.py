#!/usr/bin/env python3
"""Test MCP session management via headers"""

import requests
import json
from datetime import datetime

def test_mcp_headers():
    """Test MCP server header-based session management"""
    base_url = "http://archon-mcp:8051/mcp"

    print("=" * 70)
    print("MCP Header-Based Session Test")
    print("=" * 70)

    # Step 1: Initialize and capture session from headers
    print("\n1. INITIALIZATION")
    print("-" * 40)

    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "experimental": {},
                "roots": {"listChanged": False}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream,application/json"
    }

    response = requests.post(base_url, headers=headers, json=init_payload, timeout=5)

    print(f"Status: {response.status_code}")
    print("\nResponse Headers:")
    for key, value in response.headers.items():
        if key.lower().startswith('mcp') or key.lower() == 'set-cookie' or 'session' in key.lower():
            print(f"  {key}: {value}")

    # Check for session ID in various places
    session_id = None

    # Check header
    if "mcp-session-id" in response.headers:
        session_id = response.headers["mcp-session-id"]
        print(f"\n✅ Found session ID in headers: {session_id}")
    elif "MCP-Session-Id" in response.headers:
        session_id = response.headers["MCP-Session-Id"]
        print(f"\n✅ Found session ID in headers: {session_id}")

    # Parse response for session info
    if "text/event-stream" in response.headers.get("content-type", ""):
        for line in response.text.split('\n'):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "result" in data and "sessionId" in data["result"]:
                        session_id = data["result"]["sessionId"]
                        print(f"\n✅ Found session ID in response: {session_id}")
                except:
                    pass

    if not session_id:
        print("\n❌ No session ID found")
        print("\nRaw response preview:")
        print(response.text[:500])
        return

    # Step 2: Use session to list tools
    print("\n\n2. LIST TOOLS WITH SESSION")
    print("-" * 40)

    list_payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }

    # Try different header formats
    header_formats = [
        {"MCP-Session-Id": session_id},
        {"mcp-session-id": session_id},
        {"X-Session-Id": session_id},
        {"Session-Id": session_id},
        {"Cookie": f"session_id={session_id}"}
    ]

    for i, session_headers in enumerate(header_formats, 1):
        test_headers = headers.copy()
        test_headers.update(session_headers)

        print(f"\nAttempt {i}: Using {list(session_headers.keys())[0]}")

        response = requests.post(base_url, headers=test_headers, json=list_payload, timeout=5)

        if response.status_code == 200:
            print(f"  ✅ Success! (Status {response.status_code})")

            # Parse response
            if "text/event-stream" in response.headers.get("content-type", ""):
                for line in response.text.split('\n'):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "result" in data and "tools" in data["result"]:
                                tools = data["result"]["tools"]
                                print(f"  Found {len(tools)} tools")
                                for tool in tools[:3]:
                                    print(f"    • {tool.get('name')}")
                                return True
                        except:
                            pass
            break
        else:
            print(f"  ❌ Failed (Status {response.status_code})")
            if response.text:
                try:
                    error = response.json()
                    print(f"     {error.get('error', {}).get('message', 'Unknown error')}")
                except:
                    pass

    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_mcp_headers()