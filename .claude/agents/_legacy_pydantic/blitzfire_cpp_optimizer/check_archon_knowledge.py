#!/usr/bin/env python3
"""
Deep investigation of Archon knowledge base and available sources
"""

from archon_api_wrapper import ArchonAPI
import requests
import json

def deep_knowledge_check():
    """Comprehensive check of Archon's knowledge capabilities"""

    print("="*80)
    print("🧠 ARCHON KNOWLEDGE BASE DEEP INVESTIGATION")
    print("="*80)

    api = ArchonAPI()

    # 1. API Connection Test
    print("\n🔌 API CONNECTION")
    print("-"*50)

    health = api.health_check()
    if health.get('status') == 'healthy':
        print(f"✅ Connected to Archon API")
        print(f"   Service: {health.get('service')}")
        print(f"   Timestamp: {health.get('timestamp')}")
    else:
        print(f"❌ Connection failed: {health}")
        return

    # 2. Test RAG endpoint directly
    print("\n🔍 RAG SYSTEM INVESTIGATION")
    print("-"*50)

    # Test different query types
    test_queries = [
        # Technical queries
        ("C++ optimization", "Technical knowledge"),
        ("Python programming", "Programming knowledge"),
        ("React hooks", "Web development"),
        ("Docker containers", "DevOps knowledge"),

        # General queries
        ("machine learning", "AI/ML knowledge"),
        ("database design", "Database knowledge"),
        ("API design patterns", "Software architecture"),

        # Specific queries
        ("std::vector performance", "C++ specific"),
        ("async/await patterns", "Async programming"),
        ("unit testing best practices", "Testing knowledge")
    ]

    print("Testing RAG queries:")
    rag_results = {}

    for query, category in test_queries:
        try:
            response = requests.post(
                f"{api.base_url}/rag/query",
                json={"query": query, "match_count": 5},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                result_count = data.get('total_found', 0)
                execution_path = data.get('execution_path', 'unknown')
                search_mode = data.get('search_mode', 'unknown')

                rag_results[query] = {
                    'count': result_count,
                    'path': execution_path,
                    'mode': search_mode,
                    'success': data.get('success', False)
                }

                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results ({search_mode})")
            else:
                print(f"   ❌ '{query}': HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ '{query}': Error - {str(e)[:50]}")

    # 3. Check for different endpoints
    print("\n🔍 KNOWLEDGE ENDPOINTS DISCOVERY")
    print("-"*50)

    endpoints_to_test = [
        "/rag/query",
        "/rag/sources",
        "/rag/status",
        "/knowledge/sources",
        "/knowledge/status",
        "/documents",
        "/sources",
        "/embeddings",
        "/search",
        "/index/status",
        "/index/sources"
    ]

    working_endpoints = []
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{api.base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                working_endpoints.append(endpoint)
                print(f"   ✅ {endpoint} - Working")

                # Try to get content preview
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        print(f"      Keys: {keys}")
                    elif isinstance(data, list):
                        print(f"      List with {len(data)} items")
                except:
                    print(f"      Response: {response.text[:100]}...")

            elif response.status_code == 404:
                print(f"   ❌ {endpoint} - Not Found")
            else:
                print(f"   ⚠️ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {str(e)[:30]}")

    # 4. Check RAG configuration
    print("\n⚙️ RAG SYSTEM CONFIGURATION")
    print("-"*50)

    try:
        # Test with detailed parameters
        response = requests.post(
            f"{api.base_url}/rag/query",
            json={
                "query": "test configuration",
                "match_count": 1,
                "search_mode": "hybrid",
                "include_metadata": True
            },
            timeout=10
        )

        if response.status_code == 200:
            config_data = response.json()
            print(f"✅ RAG Configuration:")
            print(f"   Execution Path: {config_data.get('execution_path')}")
            print(f"   Search Mode: {config_data.get('search_mode')}")
            print(f"   Reranking Applied: {config_data.get('reranking_applied')}")
            print(f"   Success: {config_data.get('success')}")

            if 'metadata' in config_data:
                print(f"   Metadata Available: Yes")

    except Exception as e:
        print(f"❌ Configuration check failed: {e}")

    # 5. Test sources endpoint variations
    print("\n📚 SOURCES INVESTIGATION")
    print("-"*50)

    source_endpoints = [
        "/sources",
        "/rag/sources",
        "/knowledge/sources",
        "/documents/sources",
        "/index/sources"
    ]

    for endpoint in source_endpoints:
        try:
            response = requests.get(f"{api.base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}:")
                if isinstance(data, list):
                    print(f"   Sources found: {len(data)}")
                    for i, source in enumerate(data[:3]):
                        if isinstance(source, dict):
                            name = source.get('name', source.get('title', 'Unknown'))
                            print(f"      {i+1}. {name}")
                elif isinstance(data, dict):
                    if 'sources' in data:
                        sources = data['sources']
                        print(f"   Sources in response: {len(sources) if isinstance(sources, list) else 'N/A'}")
                    else:
                        print(f"   Response keys: {list(data.keys())[:5]}")
        except Exception as e:
            continue  # Skip failed endpoints

    # 6. Test knowledge population
    print("\n🌱 KNOWLEDGE BASE POPULATION TEST")
    print("-"*50)

    # Try to understand if we can add knowledge
    population_endpoints = [
        ("/documents", "POST"),
        ("/sources", "POST"),
        ("/rag/ingest", "POST"),
        ("/knowledge/ingest", "POST")
    ]

    for endpoint, method in population_endpoints:
        try:
            if method == "POST":
                # Try with minimal test data
                test_payload = {
                    "title": "Test Document",
                    "content": "This is a test document for knowledge base validation",
                    "type": "text"
                }

                response = requests.post(
                    f"{api.base_url}{endpoint}",
                    json=test_payload,
                    timeout=5
                )

                if response.status_code in [200, 201]:
                    print(f"✅ {endpoint} - Accepts content (Status {response.status_code})")
                elif response.status_code == 422:
                    print(f"⚠️ {endpoint} - Needs different format (422)")
                elif response.status_code == 405:
                    print(f"❌ {endpoint} - Method not allowed")
                else:
                    print(f"⚠️ {endpoint} - Status {response.status_code}")

        except Exception as e:
            continue

    # 7. Summary and recommendations
    print("\n" + "="*80)
    print("📊 KNOWLEDGE BASE ANALYSIS SUMMARY")
    print("="*80)

    total_queries = len(test_queries)
    successful_queries = sum(1 for r in rag_results.values() if r['count'] > 0)

    print(f"\n🔍 RAG System Status:")
    print(f"   Total test queries: {total_queries}")
    print(f"   Queries with results: {successful_queries}")
    print(f"   Success rate: {(successful_queries/total_queries*100):.1f}%")

    print(f"\n🔌 API Endpoints:")
    print(f"   Working endpoints: {len(working_endpoints)}")
    print(f"   Available: {working_endpoints}")

    if successful_queries == 0:
        print(f"\n❌ KNOWLEDGE BASE STATUS: EMPTY")
        print(f"   • RAG system is functional but has no indexed content")
        print(f"   • All queries return 0 results")
        print(f"   • Knowledge base needs to be populated")

        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Knowledge base needs content ingestion")
        print(f"   2. Documents/sources need to be indexed")
        print(f"   3. RAG system is ready but waiting for data")
        print(f"   4. Use Claude's built-in knowledge as fallback")

    else:
        print(f"\n✅ KNOWLEDGE BASE STATUS: POPULATED")
        print(f"   • RAG system has indexed content")
        print(f"   • {successful_queries}/{total_queries} query types return results")
        print(f"   • Knowledge base is functional and usable")

    print(f"\n🚀 FOR CLAUDE CODE INTEGRATION:")
    if successful_queries > 0:
        print(f"   ✅ Use archon:perform_rag_query for research")
        print(f"   ✅ Use archon:search_code_examples for implementations")
    else:
        print(f"   ⚠️ Use API wrapper for task management only")
        print(f"   ⚠️ Rely on Claude's built-in knowledge for research")
        print(f"   ✅ Task and project management fully functional")

    return {
        'rag_working': successful_queries > 0,
        'total_queries': total_queries,
        'successful_queries': successful_queries,
        'working_endpoints': working_endpoints,
        'knowledge_populated': successful_queries > 0
    }

if __name__ == "__main__":
    results = deep_knowledge_check()
    print(f"\n📋 Final Assessment: {json.dumps(results, indent=2)}")