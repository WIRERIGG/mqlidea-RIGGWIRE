#!/usr/bin/env python3
"""Minimal MCP test to find working format"""

import requests
import json

url = "http://archon-mcp:8051/mcp"

# Test different initialization formats
tests = [
    {
        "name": "Standard MCP init",
        "payload": {
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
    },
    {
        "name": "Minimal init",
        "payload": {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {}
            },
            "id": 1
        }
    },
    {
        "name": "With clientInfo only",
        "payload": {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "test",
                    "version": "1.0"
                }
            },
            "id": 1
        }
    },
    {
        "name": "Empty params",
        "payload": {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
    }
]

print("MCP INITIALIZATION FORMAT TEST")
print("="*60)

headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream,application/json"
}

for test in tests:
    print(f"\nTest: {test['name']}")
    print("-"*40)

    try:
        r = requests.post(url, headers=headers, json=test['payload'], timeout=5)

        print(f"Status: {r.status_code}")
        print(f"Session ID: {r.headers.get('mcp-session-id', 'None')}")

        # Parse response
        success = False
        error_msg = None

        for line in r.text.split('\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        success = True
                        server_info = data['result'].get('serverInfo', {})
                        print(f"✅ SUCCESS!")
                        print(f"   Server: {server_info.get('name')}")
                        print(f"   Version: {server_info.get('version')}")
                        print(f"   Protocol: {data['result'].get('protocolVersion')}")
                    elif 'error' in data:
                        error_msg = data['error'].get('message', 'Unknown error')
                    break
                except Exception as e:
                    print(f"Parse error: {e}")

        if not success and error_msg:
            print(f"❌ Error: {error_msg}")

        if success:
            # Test tools/list with this session
            session_id = r.headers.get('mcp-session-id')
            if session_id:
                print(f"\nTesting tools/list with session {session_id[:8]}...")

                headers2 = headers.copy()
                headers2['MCP-Session-Id'] = session_id

                # Try different params formats
                params_formats = [
                    {},
                    None,
                    {"dummy": "value"}
                ]

                for i, params in enumerate(params_formats, 1):
                    if params is None:
                        payload2 = {
                            "jsonrpc": "2.0",
                            "method": "tools/list",
                            "id": 100 + i
                        }
                    else:
                        payload2 = {
                            "jsonrpc": "2.0",
                            "method": "tools/list",
                            "params": params,
                            "id": 100 + i
                        }

                    r2 = requests.post(url, headers=headers2, json=payload2, timeout=5)

                    result_found = False
                    for line in r2.text.split('\n'):
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if 'result' in data:
                                    result_found = True
                                    tools = data['result'].get('tools', [])
                                    print(f"  Attempt {i} (params={params}): ✅ Found {len(tools)} tools")
                                    if tools:
                                        print("    Tools found! Working format discovered!")
                                        print(f"    Payload: {json.dumps(payload2, indent=2)}")
                                    break
                                elif 'error' in data:
                                    print(f"  Attempt {i} (params={params}): ❌ {data['error'].get('message')}")
                                    break
                            except:
                                pass

    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "="*60)