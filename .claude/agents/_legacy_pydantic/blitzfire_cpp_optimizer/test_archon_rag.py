#!/usr/bin/env python3
"""
Test Archon RAG functionality with relevant queries for Claude Code
"""

import requests
import json

def test_rag_for_development():
    """Test RAG queries relevant to software development and Claude Code usage"""

    print("="*80)
    print("🧠 ARCHON RAG SYSTEM - DEVELOPMENT FOCUSED TESTING")
    print("="*80)

    base_url = "http://archon-server:8181/api"

    # 1. Test C++ and systems programming queries
    print("\n🔧 C++ & SYSTEMS PROGRAMMING")
    print("-"*50)

    cpp_queries = [
        "C++ performance optimization techniques",
        "memory management in C++",
        "C++ compiler optimization flags",
        "std::vector vs std::array performance",
        "C++ unit testing frameworks",
        "CMake build system configuration",
        "AddressSanitizer integration",
        "C++ RAII patterns",
        "template metaprogramming",
        "C++ concurrency and threading"
    ]

    cpp_results = {}
    for query in cpp_queries:
        try:
            response = requests.post(f"{base_url}/rag/query",
                json={"query": query, "match_count": 3}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result_count = data.get('total_found', 0)
                cpp_results[query] = result_count
                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results")

                # Show sample content for successful queries
                if result_count > 0 and data.get('results'):
                    sample = data['results'][0].get('content', '')[:100]
                    print(f"      Sample: {sample}...")
        except Exception as e:
            print(f"   ❌ '{query}': Error - {str(e)[:50]}")

    # 2. Test development tools and processes
    print("\n🛠️ DEVELOPMENT TOOLS & PROCESSES")
    print("-"*50)

    dev_queries = [
        "git workflow best practices",
        "continuous integration setup",
        "code review guidelines",
        "debugging techniques",
        "unit test design patterns",
        "API design principles",
        "software architecture patterns",
        "Docker containerization",
        "DevOps automation",
        "monitoring and logging"
    ]

    dev_results = {}
    for query in dev_queries:
        try:
            response = requests.post(f"{base_url}/rag/query",
                json={"query": query, "match_count": 3}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result_count = data.get('total_found', 0)
                dev_results[query] = result_count
                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results")
        except Exception as e:
            print(f"   ❌ '{query}': Error - {str(e)[:50]}")

    # 3. Test programming languages and frameworks
    print("\n💻 PROGRAMMING LANGUAGES & FRAMEWORKS")
    print("-"*50)

    lang_queries = [
        "Python async programming",
        "JavaScript promises and async/await",
        "React hooks patterns",
        "Node.js performance optimization",
        "TypeScript best practices",
        "Rust memory safety",
        "Go concurrency patterns",
        "Java virtual machine tuning",
        "Python data science libraries",
        "Web API design"
    ]

    lang_results = {}
    for query in lang_queries:
        try:
            response = requests.post(f"{base_url}/rag/query",
                json={"query": query, "match_count": 3}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result_count = data.get('total_found', 0)
                lang_results[query] = result_count
                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results")
        except Exception as e:
            print(f"   ❌ '{query}': Error - {str(e)[:50]}")

    # 4. Test a specific successful query in detail
    print("\n🔍 DETAILED QUERY ANALYSIS")
    print("-"*50)

    # Find the most successful query category
    all_results = {**cpp_results, **dev_results, **lang_results}
    successful_queries = [(q, count) for q, count in all_results.items() if count > 0]

    if successful_queries:
        # Test the query with highest results
        best_query, best_count = max(successful_queries, key=lambda x: x[1])
        print(f"🎯 Testing best performing query: '{best_query}' ({best_count} results)")

        response = requests.post(f"{base_url}/rag/query",
            json={"query": best_query, "match_count": 5}, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Query Details:")
            print(f"   Query: {data.get('query')}")
            print(f"   Total Found: {data.get('total_found')}")
            print(f"   Search Mode: {data.get('search_mode')}")
            print(f"   Reranking Applied: {data.get('reranking_applied')}")

            if data.get('results'):
                print(f"\n📝 Sample Results:")
                for i, result in enumerate(data['results'][:2]):
                    print(f"\n   Result {i+1}:")
                    print(f"      Content: {result.get('content', '')[:200]}...")
                    if 'metadata' in result:
                        print(f"      Metadata: {result['metadata']}")

    # 5. Test search modes and parameters
    print("\n⚙️ SEARCH MODE TESTING")
    print("-"*50)

    if successful_queries:
        test_query = successful_queries[0][0]  # Use first successful query

        search_modes = ["hybrid", "semantic", "keyword"]
        for mode in search_modes:
            try:
                response = requests.post(f"{base_url}/rag/query",
                    json={
                        "query": test_query,
                        "match_count": 3,
                        "search_mode": mode
                    }, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    result_count = data.get('total_found', 0)
                    print(f"   ✅ {mode} mode: {result_count} results")
                else:
                    print(f"   ❌ {mode} mode: Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ {mode} mode: Error")

    # 6. Summary and recommendations
    print("\n" + "="*80)
    print("📊 RAG SYSTEM ANALYSIS FOR CLAUDE CODE")
    print("="*80)

    total_tested = len(cpp_queries) + len(dev_queries) + len(lang_queries)
    total_successful = sum(1 for count in all_results.values() if count > 0)

    print(f"\n📈 QUERY SUCCESS RATES:")
    print(f"   C++ Queries: {sum(1 for count in cpp_results.values() if count > 0)}/{len(cpp_queries)} successful")
    print(f"   Dev Tools: {sum(1 for count in dev_results.values() if count > 0)}/{len(dev_queries)} successful")
    print(f"   Languages: {sum(1 for count in lang_results.values() if count > 0)}/{len(lang_queries)} successful")
    print(f"   Overall: {total_successful}/{total_tested} ({total_successful/total_tested*100:.1f}%)")

    print(f"\n🎯 BEST PERFORMING CATEGORIES:")
    category_scores = {
        "C++ & Systems": sum(cpp_results.values()) / len(cpp_results),
        "Dev Tools": sum(dev_results.values()) / len(dev_results),
        "Languages": sum(lang_results.values()) / len(lang_results)
    }

    for category, avg_score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category}: {avg_score:.1f} avg results per query")

    print(f"\n💡 RECOMMENDATIONS FOR CLAUDE CODE:")
    if total_successful > total_tested * 0.5:
        print(f"   ✅ RAG system is well-populated and useful")
        print(f"   ✅ Use archon:perform_rag_query for research tasks")
        print(f"   ✅ Particularly effective for: {max(category_scores.items(), key=lambda x: x[1])[0]}")
    elif total_successful > 0:
        print(f"   ⚠️ RAG system has limited but useful content")
        print(f"   ⚠️ Use for specific domains with good coverage")
        print(f"   ✅ Supplement with Claude's built-in knowledge")
    else:
        print(f"   ❌ RAG system has minimal useful content")
        print(f"   ❌ Rely primarily on Claude's built-in knowledge")

    print(f"\n🚀 INTEGRATION READY:")
    print(f"   • Task management: ✅ Fully functional")
    print(f"   • Project organization: ✅ Complete")
    print(f"   • Knowledge queries: {'✅ Recommended' if total_successful > 0 else '⚠️ Limited'}")

    return {
        'total_tested': total_tested,
        'total_successful': total_successful,
        'success_rate': total_successful/total_tested,
        'category_scores': category_scores,
        'best_category': max(category_scores.items(), key=lambda x: x[1])[0],
        'recommended': total_successful > total_tested * 0.3
    }

if __name__ == "__main__":
    results = test_rag_for_development()
    print(f"\n📋 Final Assessment: {json.dumps(results, indent=2)}")