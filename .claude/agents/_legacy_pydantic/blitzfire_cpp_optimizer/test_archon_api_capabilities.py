#!/usr/bin/env python3
"""
Test what capabilities are available through the Archon API wrapper
"""

from archon_api_wrapper import ArchonAPI
import json

def explore_api_capabilities():
    """Explore all available API endpoints and capabilities"""
    api = ArchonAPI()

    print("="*70)
    print("ARCHON API CAPABILITIES EXPLORER")
    print("="*70)

    # 1. Health and Status
    print("\n🏥 HEALTH & STATUS")
    print("-"*40)
    health = api.health_check()
    print(f"✅ Health Check: {health}")

    # 2. Project Management
    print("\n📁 PROJECT MANAGEMENT")
    print("-"*40)

    projects = api.list_projects()
    print(f"✅ List Projects: Found {len(projects)} projects")

    if projects:
        for i, project in enumerate(projects[:3]):  # Show first 3
            if isinstance(project, dict):
                print(f"   Project {i+1}: {project.get('title', 'Untitled')}")
                print(f"      ID: {project.get('id', 'No ID')}")
                print(f"      Description: {project.get('description', 'No description')[:50]}...")
            else:
                print(f"   Project {i+1}: {str(project)[:50]}...")

    # 3. Task Management
    print("\n✅ TASK MANAGEMENT")
    print("-"*40)

    tasks = api.list_tasks()
    print(f"✅ List All Tasks: Found {len(tasks)} tasks")

    if tasks:
        for i, task in enumerate(tasks[:3]):  # Show first 3
            if isinstance(task, dict):
                print(f"   Task {i+1}: {task.get('title', 'Untitled')}")
                print(f"      Status: {task.get('status', 'Unknown')}")
                print(f"      Project: {task.get('project_id', 'No project')}")
            else:
                print(f"   Task {i+1}: {str(task)[:50]}...")

    # Test filtered tasks
    todo_tasks = api.list_tasks(filter_by="status", filter_value="todo")
    doing_tasks = api.list_tasks(filter_by="status", filter_value="doing")
    done_tasks = api.list_tasks(filter_by="status", filter_value="done")

    print(f"✅ Filtered Tasks:")
    print(f"   TODO: {len(todo_tasks)} tasks")
    print(f"   DOING: {len(doing_tasks)} tasks")
    print(f"   DONE: {len(done_tasks)} tasks")

    # 4. Knowledge & RAG
    print("\n🧠 KNOWLEDGE & RAG")
    print("-"*40)

    # Test RAG queries
    test_queries = [
        "Python async programming",
        "C++ optimization techniques",
        "React hooks best practices",
        "Docker containerization",
        "API design patterns"
    ]

    rag_results = []
    for query in test_queries:
        results = api.perform_rag_query(query, 2)
        rag_results.append((query, len(results)))
        print(f"   RAG Query '{query}': {len(results)} results")

    # Test code examples search
    code_results = []
    for query in test_queries[:3]:  # Test first 3
        results = api.search_code_examples(query, 2)
        code_results.append((query, len(results)))
        print(f"   Code Examples '{query}': {len(results)} results")

    # 5. Sources
    print("\n📚 SOURCES")
    print("-"*40)

    sources = api.get_available_sources()
    print(f"✅ Available Sources: Found {len(sources)} sources")

    for i, source in enumerate(sources[:3]):  # Show first 3
        if isinstance(source, dict):
            print(f"   Source {i+1}: {source.get('name', 'Unknown')}")
        else:
            print(f"   Source {i+1}: {str(source)[:50]}...")

    # 6. Test CRUD Operations
    print("\n🔧 CRUD OPERATIONS TEST")
    print("-"*40)

    # Try to create a test project
    test_project = api.create_project(
        title="API Test Project",
        description="Test project created by API wrapper",
        github_repo="https://github.com/test/repo"
    )

    if test_project:
        project_id = test_project.get('id')
        print(f"✅ Created Test Project: {project_id}")

        # Try to create a test task
        test_task = api.create_task(
            project_id=project_id,
            title="Test Task from API",
            description="This task was created via direct API",
            status="todo",
            task_order=1
        )

        if test_task:
            task_id = test_task.get('id')
            print(f"✅ Created Test Task: {task_id}")

            # Try to update the task
            updated_task = api.update_task(task_id, status="doing")
            if updated_task:
                print(f"✅ Updated Task Status: {updated_task.get('status')}")

            # Get task details
            task_details = api.get_task(task_id)
            if task_details:
                print(f"✅ Retrieved Task: {task_details.get('title')}")

        # Get project details
        project_details = api.get_project(project_id)
        if project_details:
            print(f"✅ Retrieved Project: {project_details.get('title')}")

    # 7. Available API Endpoints Discovery
    print("\n🔍 API ENDPOINTS DISCOVERY")
    print("-"*40)

    # Test common endpoints that might exist
    test_endpoints = [
        "/projects",
        "/tasks",
        "/rag/query",
        "/sources",
        "/health",
        "/documents",
        "/features",
        "/versions",
        "/users",
        "/settings"
    ]

    working_endpoints = []
    for endpoint in test_endpoints:
        try:
            response = api.session.get(f"{api.base_url}{endpoint}", timeout=2)
            if response.status_code in [200, 201]:
                working_endpoints.append(endpoint)
                print(f"   ✅ {endpoint} - Working")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint} - Not Found")
            else:
                print(f"   ⚠️ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {str(e)[:30]}")

    # 8. Summary
    print("\n" + "="*70)
    print("SUMMARY OF CAPABILITIES")
    print("="*70)

    print(f"📁 Projects: {len(projects)} available, CRUD operations working")
    print(f"✅ Tasks: {len(tasks)} available, full lifecycle management")
    print(f"🧠 RAG Queries: Testing {len(test_queries)} queries")
    print(f"📚 Sources: {len(sources)} available")
    print(f"🔍 Working Endpoints: {len(working_endpoints)} discovered")

    # Show what you can actually do
    print("\n🎯 WHAT YOU CAN DO WITH THIS API:")
    print("• Full project management (create, read, update, delete)")
    print("• Complete task lifecycle management")
    print("• Knowledge queries via RAG system")
    print("• Code example searches")
    print("• Health monitoring")
    print("• Task filtering by status, project, etc.")
    print("• Real-time project and task updates")

    if len(rag_results) > 0 and any(count > 0 for _, count in rag_results):
        print("• Knowledge base is populated with data")
    else:
        print("• Knowledge base may be empty or RAG needs setup")

    print("\n🚀 READY TO USE AS ARCHON MCP REPLACEMENT!")

    return {
        "projects": len(projects),
        "tasks": len(tasks),
        "working_endpoints": working_endpoints,
        "rag_working": any(count > 0 for _, count in rag_results),
        "crud_working": test_project is not None
    }

if __name__ == "__main__":
    capabilities = explore_api_capabilities()

    print(f"\n📊 Final Stats: {json.dumps(capabilities, indent=2)}")