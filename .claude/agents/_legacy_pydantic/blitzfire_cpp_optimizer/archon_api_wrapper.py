#!/usr/bin/env python3
"""
Archon API Direct Access Wrapper
Replaces broken MCP tools with direct API calls
"""

import requests
import json
from typing import List, Dict, Any, Optional

class ArchonAPI:
    """Direct API wrapper to replace broken MCP tools"""

    def __init__(self, base_url: str = "http://archon-server:8181/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def health_check(self) -> Dict[str, Any]:
        """Check API server health"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # PROJECT MANAGEMENT (replaces archon:manage_project)
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        try:
            response = self.session.get(f"{self.base_url}/projects", timeout=10)
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "projects" in result:
                return result["projects"]
            else:
                return []
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []

    def create_project(self, title: str, description: str = "", github_repo: str = "") -> Optional[Dict[str, Any]]:
        """Create a new project"""
        try:
            data = {
                "title": title,
                "description": description
            }
            if github_repo:
                data["github_repo"] = github_repo

            response = self.session.post(f"{self.base_url}/projects", json=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            # Return the project data from the response
            if isinstance(result, dict) and "project" in result:
                return result["project"]
            else:
                return result
        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting project {project_id}: {e}")
            return None

    def update_project(self, project_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update project"""
        try:
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=updates, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating project {project_id}: {e}")
            return None

    # TASK MANAGEMENT (replaces archon:manage_task)
    def list_tasks(self, project_id: str = None, filter_by: str = None, filter_value: str = None) -> List[Dict[str, Any]]:
        """List tasks with optional filters"""
        try:
            params = {}
            if project_id:
                params["project_id"] = project_id
            if filter_by and filter_value:
                params[filter_by] = filter_value

            response = self.session.get(f"{self.base_url}/tasks", params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "tasks" in result:
                return result["tasks"]
            else:
                return []
        except Exception as e:
            print(f"Error listing tasks: {e}")
            return []

    def create_task(self, project_id: str, title: str, description: str = "",
                   status: str = "todo", assignee: str = "User",
                   task_order: int = 1, feature: str = "") -> Optional[Dict[str, Any]]:
        """Create a new task"""
        try:
            data = {
                "project_id": project_id,
                "title": title,
                "description": description,
                "status": status,
                "assignee": assignee,
                "task_order": task_order,
                "feature": feature
            }
            response = self.session.post(f"{self.base_url}/tasks", json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating task: {e}")
            return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            response = self.session.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting task {task_id}: {e}")
            return None

    def update_task(self, task_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update task"""
        try:
            response = self.session.put(f"{self.base_url}/tasks/{task_id}", json=updates, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error updating task {task_id}: {e}")
            return None

    def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        try:
            response = self.session.delete(f"{self.base_url}/tasks/{task_id}", timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False

    # RAG QUERIES (replaces archon:perform_rag_query)
    def perform_rag_query(self, query: str, match_count: int = 5) -> List[Dict[str, Any]]:
        """Perform RAG query"""
        try:
            data = {
                "query": query,
                "match_count": match_count
            }
            response = self.session.post(f"{self.base_url}/rag/query", json=data, timeout=15)
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "matches" in result:
                return result["matches"]
            else:
                return []
        except Exception as e:
            print(f"Error performing RAG query: {e}")
            return []

    # CODE SEARCH (replaces archon:search_code_examples)
    def search_code_examples(self, query: str, match_count: int = 3) -> List[Dict[str, Any]]:
        """Search for code examples"""
        try:
            # This might be a different endpoint or same as RAG
            data = {
                "query": f"code examples {query}",
                "match_count": match_count
            }
            response = self.session.post(f"{self.base_url}/rag/query", json=data, timeout=15)
            response.raise_for_status()
            result = response.json()

            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "matches" in result:
                return result["matches"]
            else:
                return []
        except Exception as e:
            print(f"Error searching code examples: {e}")
            return []

    # SOURCES (replaces archon:get_available_sources)
    def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get available sources"""
        try:
            response = self.session.get(f"{self.base_url}/sources", timeout=10)
            if response.status_code == 404:
                # Endpoint might not exist, return empty list
                return []
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting sources: {e}")
            return []

# Usage example functions that mimic the archon: tools
def archon_list_projects():
    """Drop-in replacement for archon:manage_project(action="list")"""
    api = ArchonAPI()
    return api.list_projects()

def archon_create_project(title: str, description: str = "", github_repo: str = ""):
    """Drop-in replacement for archon:manage_project(action="create", ...)"""
    api = ArchonAPI()
    return api.create_project(title, description, github_repo)

def archon_list_tasks(project_id: str = None, filter_by: str = None, filter_value: str = None):
    """Drop-in replacement for archon:manage_task(action="list", ...)"""
    api = ArchonAPI()
    return api.list_tasks(project_id, filter_by, filter_value)

def archon_create_task(project_id: str, title: str, **kwargs):
    """Drop-in replacement for archon:manage_task(action="create", ...)"""
    api = ArchonAPI()
    return api.create_task(project_id, title, **kwargs)

def archon_update_task(task_id: str, **updates):
    """Drop-in replacement for archon:manage_task(action="update", ...)"""
    api = ArchonAPI()
    return api.update_task(task_id, **updates)

def archon_get_task(task_id: str):
    """Drop-in replacement for archon:manage_task(action="get", ...)"""
    api = ArchonAPI()
    return api.get_task(task_id)

def archon_perform_rag_query(query: str, match_count: int = 5):
    """Drop-in replacement for archon:perform_rag_query"""
    api = ArchonAPI()
    return api.perform_rag_query(query, match_count)

def archon_search_code_examples(query: str, match_count: int = 3):
    """Drop-in replacement for archon:search_code_examples"""
    api = ArchonAPI()
    return api.search_code_examples(query, match_count)

def archon_get_available_sources():
    """Drop-in replacement for archon:get_available_sources"""
    api = ArchonAPI()
    return api.get_available_sources()

if __name__ == "__main__":
    # Test the API wrapper
    api = ArchonAPI()

    print("=== ARCHON API WRAPPER TEST ===")

    # Test health check
    health = api.health_check()
    print(f"Health: {health}")

    # Test projects
    projects = api.list_projects()
    print(f"Projects: {len(projects)} found")

    # Test tasks
    tasks = api.list_tasks()
    print(f"Tasks: {len(tasks)} found")

    # Test RAG query
    rag_results = api.perform_rag_query("Python testing", 2)
    print(f"RAG Results: {len(rag_results)} found")

    print("=== API Wrapper is working! ===")