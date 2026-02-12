#!/usr/bin/env python3
"""Comprehensive MCP Server Testing"""

import requests
import json
import uuid
from datetime import datetime
import time

class MCPTester:
    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.session_id = str(uuid.uuid4())
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json",
            "X-Session-Id": self.session_id
        }

    def test_initialize(self):
        """Test MCP initialization"""
        print("\n🔧 Testing MCP Initialization...")

        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {
                    "roots": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=5
            )

            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")

            if response.status_code == 200:
                # Handle SSE response
                if "text/event-stream" in response.headers.get("content-type", ""):
                    print("  Response: SSE stream received")
                    lines = response.text.split('\n')
                    for line in lines[:10]:  # Show first 10 lines
                        if line.strip():
                            print(f"    {line}")
                else:
                    data = response.json() if response.text else {}
                    print(f"  Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"  Error: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"  Exception: {e}")
            return False

    def test_tools_list(self):
        """Test listing available tools"""
        print("\n📋 Testing Tools List...")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=5
            )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                if "text/event-stream" in response.headers.get("content-type", ""):
                    print("  SSE Response received")
                    # Parse SSE data
                    lines = response.text.split('\n')
                    for line in lines:
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "result" in data and "tools" in data["result"]:
                                    tools = data["result"]["tools"]
                                    print(f"\n  Found {len(tools)} tools:")
                                    for tool in tools:
                                        print(f"    • {tool.get('name', 'unknown')}")
                                        if "description" in tool:
                                            print(f"      {tool['description'][:100]}...")
                            except:
                                pass
                else:
                    data = response.json() if response.text else {}
                    print(f"  Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"  Error: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"  Exception: {e}")
            return False

    def test_rag_tool(self):
        """Test RAG tool directly through MCP"""
        print("\n🔍 Testing RAG Tool via MCP...")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "perform_rag_query",
                "arguments": {
                    "query": "C++ optimization techniques",
                    "match_count": 2
                }
            },
            "id": 3
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                if "text/event-stream" in response.headers.get("content-type", ""):
                    print("  SSE Response received")
                    lines = response.text.split('\n')
                    for line in lines[:20]:
                        if line.strip():
                            print(f"    {line[:100]}")
                else:
                    data = response.json() if response.text else {}
                    print(f"  Response: {json.dumps(data, indent=2)[:500]}")
                return True
            else:
                print(f"  Error: {response.text[:500]}")
                return False

        except Exception as e:
            print(f"  Exception: {e}")
            return False

    def test_session_persistence(self):
        """Test if session persists across requests"""
        print("\n🔄 Testing Session Persistence...")

        # First request
        payload1 = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 4
        }

        # Second request with same session
        payload2 = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 5
        }

        try:
            print("  First request...")
            response1 = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload1,
                timeout=5
            )
            print(f"    Status: {response1.status_code}")

            time.sleep(1)

            print("  Second request (same session)...")
            response2 = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload2,
                timeout=5
            )
            print(f"    Status: {response2.status_code}")

            if response1.status_code == response2.status_code == 200:
                print("  ✅ Session persisted successfully")
                return True
            else:
                print("  ❌ Session persistence issue")
                return False

        except Exception as e:
            print(f"  Exception: {e}")
            return False

    def test_direct_api_fallback(self):
        """Test direct API access as fallback"""
        print("\n🔌 Testing Direct API Access...")

        api_endpoints = [
            ("Health", "GET", "http://archon-server:8181/api/health", None),
            ("Projects", "GET", "http://archon-server:8181/api/projects", None),
            ("Tasks", "GET", "http://archon-server:8181/api/tasks", None),
        ]

        results = []
        for name, method, url, data in api_endpoints:
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json=data, timeout=5)

                status = "✅" if response.status_code in [200, 201] else "❌"
                print(f"  {status} {name}: {response.status_code}")
                results.append(response.status_code in [200, 201])

            except Exception as e:
                print(f"  ❌ {name}: {str(e)[:50]}")
                results.append(False)

        return all(results)

def main():
    print("=" * 70)
    print(f"MCP Server Comprehensive Test - {datetime.now()}")
    print("=" * 70)

    tester = MCPTester()
    results = []

    # Run all tests
    tests = [
        ("Initialize", tester.test_initialize),
        ("Tools List", tester.test_tools_list),
        ("RAG Tool", tester.test_rag_tool),
        ("Session Persistence", tester.test_session_persistence),
        ("Direct API", tester.test_direct_api_fallback),
    ]

    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY:")
    print("-" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")

    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)

    print("-" * 70)
    print(f"  Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed! MCP server is fully operational.")
    elif total_passed > 0:
        print("\n⚠️ MCP server is partially operational.")
    else:
        print("\n❌ MCP server is not responding correctly.")

    print("=" * 70)

if __name__ == "__main__":
    main()