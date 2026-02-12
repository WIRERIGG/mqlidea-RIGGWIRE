#!/usr/bin/env python3
"""Complete MCP Server Test Suite with Working Session Management"""

import requests
import json
from datetime import datetime
import time

class MCPClient:
    """MCP Client with proper session management"""

    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.session_id = None
        self.request_id = 1

    def _next_id(self):
        """Generate unique request ID"""
        self.request_id += 1
        return self.request_id

    def _parse_sse(self, text):
        """Parse SSE response to extract JSON data"""
        for line in text.split('\n'):
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except:
                    pass
        return None

    def _request(self, method, params=None):
        """Send MCP request with proper headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json"
        }

        if self.session_id:
            headers["MCP-Session-Id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id()
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=15
            )

            # Capture session ID from headers if present
            if "mcp-session-id" in response.headers and not self.session_id:
                self.session_id = response.headers["mcp-session-id"]

            # Parse response
            if response.status_code == 200:
                return self._parse_sse(response.text)
            else:
                return response.json() if response.text else None

        except Exception as e:
            return {"error": {"message": str(e)}}

    def initialize(self):
        """Initialize MCP session"""
        result = self._request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "experimental": {},
                "roots": {"listChanged": False}
            },
            "clientInfo": {
                "name": "mcp-test-client",
                "version": "1.0.0"
            }
        })

        if result and "result" in result:
            return result["result"]
        return None

    def list_tools(self):
        """List available tools"""
        result = self._request("tools/list")
        if result and "result" in result:
            return result["result"].get("tools", [])
        return []

    def call_tool(self, name, arguments):
        """Call a specific tool"""
        result = self._request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        if result and "result" in result:
            return result["result"]
        elif result and "error" in result:
            return {"error": result["error"]["message"]}
        return None


def test_mcp_server():
    """Comprehensive MCP server test"""
    print("=" * 70)
    print(f"Complete MCP Server Test - {datetime.now()}")
    print("=" * 70)

    client = MCPClient()

    # Test 1: Initialize
    print("\n📌 TEST 1: Initialize Session")
    print("-" * 40)
    init_result = client.initialize()
    if init_result:
        print(f"✅ Server: {init_result.get('serverInfo', {}).get('name')}")
        print(f"   Version: {init_result.get('serverInfo', {}).get('version')}")
        print(f"   Protocol: {init_result.get('protocolVersion')}")
        print(f"   Session ID: {client.session_id}")
    else:
        print("❌ Initialization failed")
        return

    # Test 2: List Tools
    print("\n📌 TEST 2: List Available Tools")
    print("-" * 40)
    tools = client.list_tools()
    if tools:
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools[:10]:  # Show first 10
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")[:60]
            print(f"   • {name}: {desc}...")
    else:
        print("❌ Failed to list tools")

    # Test 3: Test Individual Tools
    print("\n📌 TEST 3: Test Individual Tools")
    print("-" * 40)

    test_cases = [
        ("get_available_sources", {}),
        ("list_projects", {}),
        ("perform_rag_query", {
            "query": "Python async programming",
            "match_count": 2
        }),
        ("list_tasks", {
            "filter_by": "status",
            "filter_value": "todo"
        })
    ]

    results = []
    for tool_name, args in test_cases:
        print(f"\n🔧 Testing: {tool_name}")
        result = client.call_tool(tool_name, args)

        if result and "error" not in result:
            print(f"   ✅ Success")
            if isinstance(result, list):
                print(f"      Returned {len(result)} items")
            elif isinstance(result, dict):
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list):
                        print(f"      Content: {len(content)} items")
                    else:
                        print(f"      Content: {str(content)[:100]}...")
                else:
                    print(f"      Result: {str(result)[:100]}...")
            results.append(True)
        else:
            error_msg = result.get("error", "Unknown error") if result else "No response"
            print(f"   ❌ Failed: {error_msg}")
            results.append(False)

    # Test 4: Create and manage a test task
    print("\n📌 TEST 4: Task Management Flow")
    print("-" * 40)

    # First, try to get or create a test project
    print("\n1. Getting projects...")
    projects = client.call_tool("list_projects", {})

    project_id = None
    if projects and isinstance(projects, list) and len(projects) > 0:
        if isinstance(projects[0], dict):
            project_id = projects[0].get("id")
            print(f"   Using existing project: {projects[0].get('title')}")

    if not project_id:
        print("   Creating test project...")
        new_project = client.call_tool("create_project", {
            "title": "MCP Test Project",
            "description": "Test project for MCP validation"
        })
        if new_project and "id" in new_project:
            project_id = new_project["id"]
            print(f"   ✅ Created project ID: {project_id}")

    if project_id:
        # Create a test task
        print("\n2. Creating test task...")
        task = client.call_tool("create_task", {
            "project_id": project_id,
            "title": f"Test Task {int(time.time())}",
            "description": "Test task created by MCP test suite",
            "status": "todo"
        })

        if task and "id" in task:
            task_id = task["id"]
            print(f"   ✅ Created task ID: {task_id}")

            # Update task status
            print("\n3. Updating task status...")
            updated = client.call_tool("update_task", {
                "task_id": task_id,
                "status": "doing"
            })
            if updated:
                print(f"   ✅ Updated task to 'doing'")

            # Get task details
            print("\n4. Getting task details...")
            details = client.call_tool("get_task", {"task_id": task_id})
            if details:
                print(f"   ✅ Task status: {details.get('status')}")

            results.append(True)
        else:
            print("   ❌ Failed to create task")
            results.append(False)
    else:
        print("   ⚠️ Skipping task tests (no project)")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("-" * 40)

    total_tests = len(results)
    passed_tests = sum(results)

    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! MCP server is fully operational.")
    elif passed_tests > total_tests * 0.7:
        print("\n✅ MCP server is operational (most tests passed).")
    elif passed_tests > 0:
        print("\n⚠️ MCP server is partially operational.")
    else:
        print("\n❌ MCP server tests failed.")

    print("=" * 70)

    # Return test status
    return passed_tests == total_tests


if __name__ == "__main__":
    success = test_mcp_server()
    exit(0 if success else 1)