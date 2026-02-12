#!/usr/bin/env python3
"""MCP Server Session-Based Testing"""

import requests
import json
from datetime import datetime

class MCPSessionTester:
    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.session_id = None
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json"
        }

    def parse_sse_response(self, response_text):
        """Parse SSE response to extract JSON data"""
        for line in response_text.split('\n'):
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except:
                    pass
        return None

    def initialize_session(self):
        """Initialize MCP session and get session ID"""
        print("\n1️⃣ Initializing MCP Session...")

        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "capabilities": {"roots": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            },
            "id": 1
        }

        response = requests.post(
            self.base_url,
            headers=self.base_headers,
            json=payload,
            timeout=5
        )

        print(f"   Status: {response.status_code}")

        # Extract session ID from headers
        if "mcp-session-id" in response.headers:
            self.session_id = response.headers["mcp-session-id"]
            print(f"   ✅ Session ID: {self.session_id}")

            # Parse the response
            data = self.parse_sse_response(response.text)
            if data and "result" in data:
                result = data["result"]
                print(f"   Server: {result.get('serverInfo', {}).get('name', 'unknown')}")
                print(f"   Version: {result.get('serverInfo', {}).get('version', 'unknown')}")
                print(f"   Protocol: {result.get('protocolVersion', 'unknown')}")
            return True
        else:
            print("   ❌ No session ID received")
            return False

    def test_with_session(self, method, params, test_name):
        """Test a method using the established session"""
        if not self.session_id:
            print(f"\n❌ {test_name}: No session established")
            return False

        print(f"\n🔧 {test_name}...")

        # Add session ID to headers
        headers = self.base_headers.copy()
        headers["MCP-Session-Id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 2
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = self.parse_sse_response(response.text)
                if data:
                    if "result" in data:
                        print(f"   ✅ Success")
                        return data["result"]
                    elif "error" in data:
                        print(f"   ❌ Error: {data['error'].get('message', 'unknown')}")
                        return False
                print("   ⚠️ No parseable data in response")
            else:
                print(f"   ❌ HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

        return False

    def list_tools(self):
        """List available MCP tools"""
        result = self.test_with_session("tools/list", {}, "Listing Tools")

        if result and "tools" in result:
            tools = result["tools"]
            print(f"\n   📋 Found {len(tools)} tools:")
            for tool in tools[:10]:  # Show first 10
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")[:60]
                print(f"      • {name}: {desc}...")
            return True
        return False

    def test_rag_query(self):
        """Test RAG query tool"""
        params = {
            "name": "perform_rag_query",
            "arguments": {
                "query": "Python async programming",
                "match_count": 2
            }
        }

        result = self.test_with_session("tools/call", params, "Testing RAG Query")

        if result:
            print(f"   Result type: {type(result)}")
            if isinstance(result, list) and len(result) > 0:
                print(f"   ✅ Got {len(result)} results")
                return True
            elif isinstance(result, dict):
                print(f"   ✅ Got response: {str(result)[:100]}...")
                return True
        return False

    def test_list_projects(self):
        """Test listing projects"""
        params = {
            "name": "list_projects",
            "arguments": {}
        }

        result = self.test_with_session("tools/call", params, "Listing Projects")

        if result:
            if isinstance(result, list):
                print(f"   ✅ Found {len(result)} projects")
                for proj in result[:3]:  # Show first 3
                    if isinstance(proj, dict):
                        print(f"      • {proj.get('title', 'untitled')}")
                return True
            elif isinstance(result, dict) and "content" in result:
                print(f"   ✅ Response: {result['content'][:100]}...")
                return True
        return False

    def test_get_sources(self):
        """Test getting available sources"""
        params = {
            "name": "get_available_sources",
            "arguments": {}
        }

        result = self.test_with_session("tools/call", params, "Getting Available Sources")

        if result:
            print(f"   ✅ Sources retrieved")
            return True
        return False

def main():
    print("=" * 70)
    print(f"MCP Server Session-Based Test - {datetime.now()}")
    print("=" * 70)

    tester = MCPSessionTester()

    # Initialize session first
    if not tester.initialize_session():
        print("\n❌ Failed to initialize session. Cannot proceed with tests.")
        return

    # Run tests with the session
    results = []
    tests = [
        ("List Tools", tester.list_tools),
        ("RAG Query", tester.test_rag_query),
        ("List Projects", tester.test_list_projects),
        ("Get Sources", tester.test_get_sources),
    ]

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("-" * 70)

    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    total_passed = sum(1 for _, p in results if p)
    print(f"\n  Total: {total_passed}/{len(results)} tests passed")

    if total_passed == len(results):
        print("\n🎉 All tests passed! MCP server is fully functional.")
    elif total_passed > 0:
        print("\n⚠️ MCP server is partially functional.")
    else:
        print("\n❌ MCP server tests failed.")

    print("=" * 70)

if __name__ == "__main__":
    main()