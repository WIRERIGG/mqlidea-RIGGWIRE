#!/usr/bin/env python3
"""Test Archon MCP and API connectivity"""

import requests
import json
from datetime import datetime

def test_api_health():
    """Test API server health endpoint"""
    try:
        response = requests.get("http://archon-server:8181/api/health")
        if response.status_code == 200:
            print("✅ API Server: HEALTHY")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API Server: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Server: {e}")
        return False

def test_mcp_endpoint():
    """Test MCP server endpoint"""
    try:
        # MCP requires SSE headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream,application/json"
        }

        # Try a simple request
        response = requests.post(
            "http://archon-mcp:8051/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
            timeout=5
        )

        print(f"✅ MCP Server: Reachable (Status {response.status_code})")
        if response.status_code == 400:
            print("   Note: Requires session ID for full functionality")
        return True
    except Exception as e:
        print(f"❌ MCP Server: {e}")
        return False

def test_rag_query():
    """Test RAG query through API"""
    try:
        response = requests.post(
            "http://archon-server:8181/api/rag/query",
            json={
                "query": "C++ CMake build system",
                "match_count": 2
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ RAG Query: SUCCESS")
            data = response.json()
            if "matches" in data:
                print(f"   Found {len(data['matches'])} matches")
            return True
        else:
            print(f"❌ RAG Query: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ RAG Query: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print(f"Archon Service Connectivity Test - {datetime.now()}")
    print("=" * 60)

    results = []

    # Test each service
    print("\n1. Testing API Server...")
    results.append(test_api_health())

    print("\n2. Testing MCP Server...")
    results.append(test_mcp_endpoint())

    print("\n3. Testing RAG Functionality...")
    results.append(test_rag_query())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Services Tested: {len(results)}")
    print(f"  Successful: {sum(results)}")
    print(f"  Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✅ All services are operational!")
    else:
        print("\n⚠️ Some services are not fully accessible")
    print("=" * 60)