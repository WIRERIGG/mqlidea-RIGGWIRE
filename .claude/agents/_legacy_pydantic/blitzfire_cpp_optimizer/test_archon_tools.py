#!/usr/bin/env python3
"""Test Archon MCP tools with correct format based on documentation"""

import requests
import json
from datetime import datetime

class ArchonMCPTester:
    def __init__(self):
        self.base_url = "http://archon-mcp:8051/mcp"
        self.session_id = None

    def initialize(self):
        """Initialize MCP session"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json"
        }

        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "experimental": {},
                    "roots": {"listChanged": False}
                },
                "clientInfo": {
                    "name": "archon-test",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }

        r = requests.post(self.base_url, headers=headers, json=payload, timeout=5)
        self.session_id = r.headers.get('mcp-session-id')

        # Parse response
        for line in r.text.split('\n'):
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    if 'result' in data:
                        print(f"✅ Initialized: Session {self.session_id}")
                        return True
                except:
                    pass
        return False

    def call_tool(self, tool_name, args, description=""):
        """Call an Archon tool using the expected format"""
        if not self.session_id:
            print("❌ No session available")
            return None

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json",
            "MCP-Session-Id": self.session_id
        }

        # Try different formats based on Archon documentation
        formats = [
            # Format 1: Based on documentation examples - manage_task format
            {
                "method": "tools/call",
                "params": {
                    "name": f"archon:{tool_name}",
                    "arguments": args
                }
            },
            # Format 2: Direct tool name
            {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            },
            # Format 3: With input instead of arguments
            {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "input": args
                }
            }
        ]

        for i, fmt in enumerate(formats, 1):
            payload = {
                "jsonrpc": "2.0",
                **fmt,
                "id": 100 + i
            }

            print(f"\n  Attempt {i}: {fmt['params'].get('name', tool_name)}")
            print(f"    Payload: {json.dumps(payload, indent=4)}")

            r = requests.post(self.base_url, headers=headers, json=payload, timeout=10)

            # Parse response
            for line in r.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'result' in data:
                            print(f"    ✅ SUCCESS! Got result")
                            return data['result']
                        elif 'error' in data:
                            print(f"    ❌ Error: {data['error'].get('message')}")
                    except Exception as e:
                        print(f"    Parse error: {e}")

        return None

def test_archon_tools():
    """Test Archon MCP tools based on documentation"""
    print("="*70)
    print(f"ARCHON MCP TOOLS TEST - {datetime.now()}")
    print("="*70)
    print("\nTesting tool formats from Archon documentation...")

    tester = ArchonMCPTester()

    # Initialize session
    if not tester.initialize():
        print("❌ Failed to initialize session")
        return

    # Test tools from documentation
    print("\n" + "="*70)
    print("TESTING ARCHON TOOLS")
    print("="*70)

    tests = [
        # From documentation: manage_task examples
        {
            "name": "manage_task",
            "args": {
                "action": "list",
                "filter_by": "status",
                "filter_value": "todo"
            },
            "description": "List TODO tasks"
        },
        {
            "name": "list_tasks",
            "args": {
                "filter_by": "status",
                "filter_value": "todo"
            },
            "description": "Alternative: list_tasks"
        },
        # From documentation: manage_project
        {
            "name": "manage_project",
            "args": {
                "action": "list"
            },
            "description": "List projects"
        },
        {
            "name": "list_projects",
            "args": {},
            "description": "Alternative: list_projects"
        },
        # From documentation: perform_rag_query
        {
            "name": "perform_rag_query",
            "args": {
                "query": "Python testing frameworks",
                "match_count": 2
            },
            "description": "RAG query"
        },
        # From documentation: search_code_examples
        {
            "name": "search_code_examples",
            "args": {
                "query": "React hooks",
                "match_count": 2
            },
            "description": "Search code examples"
        },
        # From documentation: get_available_sources
        {
            "name": "get_available_sources",
            "args": {},
            "description": "Get available sources"
        }
    ]

    successful = 0
    for test in tests:
        print(f"\n{'='*50}")
        print(f"TEST: {test['description']}")
        print(f"Tool: {test['name']}")
        print(f"Args: {test['args']}")
        print("-"*50)

        result = tester.call_tool(test['name'], test['args'], test['description'])

        if result:
            successful += 1
            print(f"\n✅ WORKING FORMAT FOUND for {test['name']}!")
            if isinstance(result, list):
                print(f"   Result: List with {len(result)} items")
            elif isinstance(result, dict):
                print(f"   Result: {str(result)[:200]}...")
            else:
                print(f"   Result: {str(result)[:200]}...")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Successful tools: {successful}/{len(tests)}")

    if successful > 0:
        print("\n✅ Some Archon tools are working!")
    else:
        print("\n❌ No Archon tools worked with tested formats")

if __name__ == "__main__":
    test_archon_tools()