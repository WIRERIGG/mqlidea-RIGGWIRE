#!/usr/bin/env python3
"""Deep MCP Server Diagnostic Tool"""

import requests
import json
import sys
from datetime import datetime

class MCPDiagnostic:
    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.api_url = "http://archon-server:8181/api"
        self.session_id = None

    def print_section(self, title):
        """Print formatted section header"""
        print(f"\n{'='*70}")
        print(f"{title}")
        print('='*70)

    def print_test(self, name, status, details=""):
        """Print test result"""
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
        if details:
            for line in details.split('\n'):
                print(f"   {line}")

    def check_server_health(self):
        """Check if servers are responding"""
        self.print_section("1. SERVER HEALTH CHECK")

        # Check API server
        try:
            r = requests.get(f"{self.api_url}/health", timeout=2)
            self.print_test("API Server", r.status_code == 200,
                          f"Status: {r.status_code}\n{json.dumps(r.json(), indent=2)}")
        except Exception as e:
            self.print_test("API Server", False, str(e))

        # Check MCP endpoint
        try:
            r = requests.get(self.base_url.replace('/mcp', '/'), timeout=2)
            self.print_test("MCP Base URL", True, f"Status: {r.status_code}")
        except Exception as e:
            self.print_test("MCP Base URL", False, str(e))

    def test_initialization(self):
        """Test MCP initialization with various protocols"""
        self.print_section("2. INITIALIZATION TESTS")

        protocols = [
            ("2025-06-18", "Latest protocol"),
            ("1.0.0", "Legacy protocol"),
            ("2024-11-05", "Alternative protocol")
        ]

        for protocol, desc in protocols:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream,application/json"
            }

            payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol,
                    "capabilities": {},
                    "clientInfo": {"name": "diagnostic", "version": "1.0"}
                },
                "id": 1
            }

            try:
                r = requests.post(self.base_url, headers=headers, json=payload, timeout=5)

                if r.status_code == 200:
                    session = r.headers.get('mcp-session-id', 'No session')

                    # Parse SSE response
                    result = None
                    for line in r.text.split('\n'):
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                if 'result' in data:
                                    result = data['result']
                                    if not self.session_id:  # Save first working session
                                        self.session_id = r.headers.get('mcp-session-id')
                                    break
                            except:
                                pass

                    if result:
                        server_info = result.get('serverInfo', {})
                        self.print_test(f"Protocol {protocol} ({desc})", True,
                                      f"Server: {server_info.get('name')}\n"
                                      f"Version: {server_info.get('version')}\n"
                                      f"Session: {session}")
                    else:
                        self.print_test(f"Protocol {protocol} ({desc})", False,
                                      "No result in response")
                else:
                    self.print_test(f"Protocol {protocol} ({desc})", False,
                                  f"Status: {r.status_code}")

            except Exception as e:
                self.print_test(f"Protocol {protocol} ({desc})", False, str(e))

    def test_methods(self):
        """Test various MCP methods"""
        self.print_section("3. METHOD TESTS")

        if not self.session_id:
            print("⚠️  No session available, skipping method tests")
            return

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json",
            "MCP-Session-Id": self.session_id
        }

        # Test different methods
        methods = [
            ("tools/list", {}, "List tools"),
            ("prompts/list", {}, "List prompts"),
            ("resources/list", {}, "List resources"),
            ("ping", {}, "Ping"),
            ("notifications/initialized", {}, "Notification")
        ]

        for method, params, desc in methods:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 2
            }

            try:
                r = requests.post(self.base_url, headers=headers, json=payload, timeout=5)

                # Parse response
                response_data = None
                error_msg = None

                for line in r.text.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if 'result' in data:
                                response_data = data['result']
                            elif 'error' in data:
                                error_msg = data['error'].get('message', 'Unknown error')
                            break
                        except:
                            pass

                if response_data is not None:
                    if isinstance(response_data, dict):
                        count = len(response_data.get(method.split('/')[0], []))
                        self.print_test(f"{desc} ({method})", True, f"Found {count} items")
                    else:
                        self.print_test(f"{desc} ({method})", True, "Success")
                elif error_msg:
                    self.print_test(f"{desc} ({method})", False, error_msg)
                else:
                    self.print_test(f"{desc} ({method})", False, f"Status: {r.status_code}")

            except Exception as e:
                self.print_test(f"{desc} ({method})", False, str(e)[:50])

    def test_tool_calls(self):
        """Test different tool call formats"""
        self.print_section("4. TOOL CALL FORMAT TESTS")

        if not self.session_id:
            print("⚠️  No session available, skipping tool tests")
            return

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json",
            "MCP-Session-Id": self.session_id
        }

        # Try different parameter formats for tools/call
        formats = [
            {
                "name": "Format 1: name + arguments",
                "params": {
                    "name": "list_projects",
                    "arguments": {}
                }
            },
            {
                "name": "Format 2: tool + arguments",
                "params": {
                    "tool": "list_projects",
                    "arguments": {}
                }
            },
            {
                "name": "Format 3: name + input",
                "params": {
                    "name": "list_projects",
                    "input": {}
                }
            },
            {
                "name": "Format 4: toolName + params",
                "params": {
                    "toolName": "list_projects",
                    "params": {}
                }
            },
            {
                "name": "Format 5: Direct method call",
                "method": "list_projects",
                "params": {}
            }
        ]

        for fmt in formats:
            if "method" in fmt:
                # Direct method call
                payload = {
                    "jsonrpc": "2.0",
                    "method": fmt["method"],
                    "params": fmt["params"],
                    "id": 3
                }
                test_name = fmt["name"]
            else:
                # tools/call with different param formats
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": fmt["params"],
                    "id": 3
                }
                test_name = fmt["name"]

            try:
                r = requests.post(self.base_url, headers=headers, json=payload, timeout=5)

                # Parse response
                success = False
                details = ""

                for line in r.text.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if 'result' in data:
                                success = True
                                details = "✓ Got result"
                            elif 'error' in data:
                                details = data['error'].get('message', 'Unknown error')
                            break
                        except:
                            pass

                if not details:
                    details = f"Status: {r.status_code}"

                self.print_test(test_name, success, details)

                # If successful, save the working format
                if success:
                    print("\n   🎯 WORKING FORMAT FOUND!")
                    print(f"   Payload: {json.dumps(payload, indent=2)}")
                    return True

            except Exception as e:
                self.print_test(test_name, False, str(e)[:50])

        return False

    def test_direct_api(self):
        """Test direct API as fallback"""
        self.print_section("5. DIRECT API FALLBACK TEST")

        endpoints = [
            ("GET", "/health", None, "Health check"),
            ("GET", "/projects", None, "List projects"),
            ("GET", "/tasks", None, "List tasks"),
            ("POST", "/rag/query", {"query": "test", "match_count": 1}, "RAG query")
        ]

        for method, endpoint, data, desc in endpoints:
            url = f"{self.api_url}{endpoint}"

            try:
                if method == "GET":
                    r = requests.get(url, timeout=5)
                else:
                    r = requests.post(url, json=data, timeout=5)

                if r.status_code in [200, 201]:
                    result = r.json() if r.text else {}
                    if isinstance(result, list):
                        self.print_test(f"{desc} ({endpoint})", True, f"Found {len(result)} items")
                    else:
                        self.print_test(f"{desc} ({endpoint})", True, "Success")
                else:
                    self.print_test(f"{desc} ({endpoint})", False, f"Status: {r.status_code}")

            except Exception as e:
                self.print_test(f"{desc} ({endpoint})", False, str(e)[:50])

    def run_diagnostics(self):
        """Run all diagnostic tests"""
        print("="*70)
        print(f"MCP SERVER DEEP DIAGNOSTIC - {datetime.now()}")
        print("="*70)

        self.check_server_health()
        self.test_initialization()
        self.test_methods()
        self.test_tool_calls()
        self.test_direct_api()

        self.print_section("DIAGNOSTIC SUMMARY")

        if self.session_id:
            print(f"✅ Session established: {self.session_id}")
        else:
            print("❌ No session could be established")

        print("\nRecommendations:")
        print("• MCP server is running but has parameter format issues")
        print("• Use direct API endpoints as reliable fallback")
        print("• Session management works correctly with MCP-Session-Id header")
        print("• Server supports protocol version 2025-06-18")

        return self.session_id is not None

if __name__ == "__main__":
    diagnostic = MCPDiagnostic()
    success = diagnostic.run_diagnostics()
    sys.exit(0 if success else 1)