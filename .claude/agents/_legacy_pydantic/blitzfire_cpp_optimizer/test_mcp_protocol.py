#!/usr/bin/env python3
"""Test MCP Server with correct protocol"""

import requests
import json
from datetime import datetime
import time

class MCPProtocolTester:
    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.session_id = None

    def send_request(self, method, params=None, use_session=True):
        """Send a properly formatted MCP request"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json"
        }

        if use_session and self.session_id:
            headers["MCP-Session-Id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": int(time.time() * 1000)  # Unique ID
        }

        print(f"\n📤 Request: {method}")
        print(f"   Params: {json.dumps(params, indent=2) if params else '{}'}")

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")

            # Handle SSE response
            if "text/event-stream" in response.headers.get("content-type", ""):
                for line in response.text.split('\n'):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            return data
                        except:
                            pass

            # Handle JSON response
            if response.text:
                try:
                    return response.json()
                except:
                    print(f"   Raw response: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

        return None

    def test_initialize(self):
        """Test initialization"""
        print("\n" + "="*60)
        print("1. INITIALIZATION TEST")
        print("="*60)

        data = self.send_request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "experimental": {},
                    "roots": {"listChanged": False},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            use_session=False
        )

        if data and "result" in data:
            result = data["result"]
            self.session_id = result.get("sessionId")
            print(f"\n   ✅ Initialized successfully")
            print(f"   Server: {result.get('serverInfo', {}).get('name')}")
            print(f"   Version: {result.get('serverInfo', {}).get('version')}")
            print(f"   Session: {self.session_id}")
            return True

        print(f"\n   ❌ Initialization failed")
        return False

    def test_list_tools(self):
        """Test listing tools"""
        print("\n" + "="*60)
        print("2. LIST TOOLS TEST")
        print("="*60)

        data = self.send_request("tools/list")

        if data and "result" in data:
            tools = data["result"].get("tools", [])
            print(f"\n   ✅ Found {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"      • {tool.get('name')}: {tool.get('description', '')[:50]}...")
            return True

        if data and "error" in data:
            print(f"\n   ❌ Error: {data['error'].get('message')}")

        return False

    def test_call_tool(self):
        """Test calling a specific tool"""
        print("\n" + "="*60)
        print("3. CALL TOOL TEST")
        print("="*60)

        # Try different tool call formats
        test_calls = [
            # Format 1: Direct tool call
            {
                "method": "tools/call",
                "params": {
                    "name": "list_projects",
                    "arguments": {}
                }
            },
            # Format 2: With input wrapper
            {
                "method": "tools/call",
                "params": {
                    "name": "get_available_sources",
                    "input": {}
                }
            },
            # Format 3: Direct method call
            {
                "method": "list_projects",
                "params": {}
            }
        ]

        for i, test in enumerate(test_calls, 1):
            print(f"\n   Test {i}: {test['method']}")
            data = self.send_request(test["method"], test.get("params"))

            if data and "result" in data:
                print(f"      ✅ Success: {str(data['result'])[:100]}...")
                return True
            elif data and "error" in data:
                print(f"      ❌ Error: {data['error'].get('message')}")

        return False

    def test_rag_query(self):
        """Test RAG query with different formats"""
        print("\n" + "="*60)
        print("4. RAG QUERY TEST")
        print("="*60)

        # Try different parameter formats
        test_formats = [
            {
                "name": "perform_rag_query",
                "arguments": {
                    "query": "Python testing frameworks",
                    "match_count": 2
                }
            },
            {
                "name": "archon:perform_rag_query",
                "arguments": {
                    "query": "Python testing frameworks",
                    "match_count": 2
                }
            },
            {
                "tool": "perform_rag_query",
                "input": {
                    "query": "Python testing frameworks",
                    "match_count": 2
                }
            }
        ]

        for i, params in enumerate(test_formats, 1):
            print(f"\n   Format {i}:")
            data = self.send_request("tools/call", params)

            if data and "result" in data:
                print(f"      ✅ Success")
                return True
            elif data and "error" in data:
                print(f"      ❌ {data['error'].get('message')}")

        return False

def main():
    print("=" * 70)
    print(f"MCP Protocol Test Suite - {datetime.now()}")
    print("=" * 70)

    tester = MCPProtocolTester()

    # Run tests
    results = []
    tests = [
        ("Initialize", tester.test_initialize),
        ("List Tools", tester.test_list_tools),
        ("Call Tool", tester.test_call_tool),
        ("RAG Query", tester.test_rag_query)
    ]

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("-" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print("-" * 70)
    print(f"  Result: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 MCP server is fully operational!")
    elif passed_count > 0:
        print("\n⚠️ MCP server is partially operational")
    else:
        print("\n❌ MCP server communication failed")

    print("=" * 70)

if __name__ == "__main__":
    main()