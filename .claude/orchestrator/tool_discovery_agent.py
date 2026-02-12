"""
Tool Discovery Agent - Searches for and evaluates new AI and static analysis tools daily
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from pydantic_ai import Agent, RunContext, Tool
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import aiohttp
from bs4 import BeautifulSoup

load_dotenv()

logger = logging.getLogger(__name__)


class ToolDiscoverySettings(BaseSettings):
    """Settings for tool discovery agent"""

    # Search Configuration
    search_sources: List[str] = Field(
        default=["github", "hackernews", "devto", "awesomecpp"],
        description="Sources to search for new tools"
    )
    github_token: Optional[str] = Field(default=None, description="GitHub API token")
    search_interval_hours: int = Field(default=24, description="Hours between searches")

    # Evaluation Criteria
    min_stars: int = Field(default=100, description="Minimum GitHub stars")
    min_license_score: float = Field(default=0.7, description="License compatibility score")
    languages_of_interest: List[str] = Field(
        default=["C++", "Python", "Rust"],
        description="Programming languages to focus on"
    )

    # Integration
    auto_integrate_threshold: float = Field(default=0.85, description="Auto-integration score threshold")
    integration_test_timeout: int = Field(default=300, description="Integration test timeout in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DiscoveredTool(BaseModel):
    """Model for a discovered tool"""
    name: str
    description: str
    url: str
    category: str
    language: str
    stars: int = 0
    license: Optional[str] = None
    last_updated: Optional[datetime] = None
    compatibility_score: float = 0.0
    integration_difficulty: str = "unknown"
    recommended_for: List[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=datetime.now)


class ToolEvaluation(BaseModel):
    """Tool evaluation results"""
    tool_name: str
    technical_score: float
    community_score: float
    license_score: float
    integration_score: float
    overall_score: float
    recommendation: str
    integration_steps: List[str]
    potential_conflicts: List[str]


class ToolDependencies(BaseModel):
    """Dependencies for tool discovery agent"""
    settings: ToolDiscoverySettings
    cache_dir: Path
    integration_dir: Path
    session: Optional[aiohttp.ClientSession] = None


# Initialize the tool discovery agent
tool_discovery_agent = Agent(
    model="claude-3-5-sonnet-20240620",
    deps_type=ToolDependencies,
    system_prompt="""You are an expert tool discovery and evaluation agent for C++ and AI development tools.

Your responsibilities:
1. Search multiple sources for new development tools, static analyzers, and AI assistants
2. Evaluate tools based on technical merit, community adoption, and integration feasibility
3. Recommend tools for integration into the Wire Ground project
4. Generate integration plans for approved tools

Focus on:
- C++ static analysis tools (like clang-tidy, cppcheck, PVS-Studio)
- AI-powered code assistants and analyzers
- Performance profiling and optimization tools
- Security scanning tools
- Build system enhancements

Evaluation criteria:
- Technical quality and maturity
- Active maintenance and community support
- License compatibility (prefer MIT, Apache, BSD)
- Integration complexity
- Performance impact
- Security considerations
"""
)


@tool_discovery_agent.tool
async def search_github_trending(
    ctx: RunContext[ToolDependencies],
    language: str = "C++",
    since: str = "daily"
) -> List[Dict[str, Any]]:
    """Search GitHub trending repositories for new tools"""

    if not ctx.deps.settings.github_token:
        return []

    headers = {
        "Authorization": f"Bearer {ctx.deps.settings.github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Search for static analysis and development tools
    search_queries = [
        f"language:{language} static analysis stars:>100 pushed:>2024-01-01",
        f"language:{language} linter tool stars:>50",
        f"AI code analysis language:{language}",
        f"performance profiling {language}"
    ]

    discovered = []

    async with aiohttp.ClientSession() as session:
        for query in search_queries:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"

            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        for repo in data.get("items", [])[:10]:
                            discovered.append({
                                "name": repo["name"],
                                "description": repo["description"],
                                "url": repo["html_url"],
                                "stars": repo["stargazers_count"],
                                "language": repo["language"],
                                "license": repo.get("license", {}).get("name"),
                                "updated": repo["updated_at"]
                            })
            except Exception as e:
                logger.error(f"GitHub search error: {e}")

    return discovered


@tool_discovery_agent.tool
async def search_awesome_lists(
    ctx: RunContext[ToolDependencies]
) -> List[Dict[str, Any]]:
    """Search awesome-cpp and similar curated lists for tools"""

    awesome_lists = [
        "https://api.github.com/repos/fffaraz/awesome-cpp/contents/README.md",
        "https://api.github.com/repos/analysis-tools-dev/static-analysis/contents/README.md"
    ]

    discovered = []

    async with aiohttp.ClientSession() as session:
        for list_url in awesome_lists:
            try:
                async with session.get(list_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("content", "")

                        # Parse markdown content for tool references
                        # This is simplified - real implementation would parse more carefully
                        lines = content.split("\n")
                        for line in lines:
                            if "github.com" in line and any(keyword in line.lower() for keyword in ["static", "analysis", "lint", "check"]):
                                # Extract tool info from line
                                discovered.append({
                                    "source": "awesome_list",
                                    "reference": line[:200]  # First 200 chars
                                })
            except Exception as e:
                logger.error(f"Awesome list search error: {e}")

    return discovered


@tool_discovery_agent.tool
async def evaluate_tool(
    ctx: RunContext[ToolDependencies],
    tool: DiscoveredTool
) -> ToolEvaluation:
    """Evaluate a discovered tool for integration"""

    # Technical evaluation
    technical_score = 0.0

    # Check if tool is actively maintained
    if tool.last_updated:
        days_since_update = (datetime.now() - tool.last_updated).days
        if days_since_update < 30:
            technical_score += 0.3
        elif days_since_update < 90:
            technical_score += 0.2
        elif days_since_update < 180:
            technical_score += 0.1

    # Language compatibility
    if tool.language in ctx.deps.settings.languages_of_interest:
        technical_score += 0.3

    # Category relevance
    relevant_categories = ["static-analysis", "linter", "security", "performance"]
    if any(cat in tool.category.lower() for cat in relevant_categories):
        technical_score += 0.4

    # Community evaluation
    community_score = min(1.0, tool.stars / 1000)  # Normalize stars to 0-1

    # License evaluation
    license_score = 0.0
    good_licenses = ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause"]
    if tool.license in good_licenses:
        license_score = 1.0
    elif tool.license in ["GPL-3.0", "AGPL-3.0"]:
        license_score = 0.3

    # Integration complexity evaluation
    integration_score = 0.5  # Default medium complexity

    if "python" in tool.language.lower():
        integration_score = 0.8  # Easy to integrate Python tools
    elif "docker" in tool.description.lower():
        integration_score = 0.7  # Docker makes integration easier
    elif "plugin" in tool.description.lower():
        integration_score = 0.6

    # Calculate overall score
    overall_score = (
        technical_score * 0.3 +
        community_score * 0.2 +
        license_score * 0.2 +
        integration_score * 0.3
    )

    # Determine recommendation
    if overall_score >= ctx.deps.settings.auto_integrate_threshold:
        recommendation = "auto_integrate"
    elif overall_score >= 0.7:
        recommendation = "manual_review"
    elif overall_score >= 0.5:
        recommendation = "watch"
    else:
        recommendation = "skip"

    # Generate integration steps
    integration_steps = []

    if recommendation in ["auto_integrate", "manual_review"]:
        integration_steps = [
            f"1. Clone repository from {tool.url}",
            "2. Review documentation and requirements",
            "3. Create integration wrapper in tools/ directory",
            "4. Add to CMake build configuration",
            "5. Create test cases for tool integration",
            "6. Update CI/CD pipeline to include tool",
            "7. Document usage in project README"
        ]

    # Identify potential conflicts
    potential_conflicts = []

    if tool.license and "GPL" in tool.license:
        potential_conflicts.append("GPL license may conflict with proprietary code")

    if tool.stars < 100:
        potential_conflicts.append("Low community adoption may indicate instability")

    return ToolEvaluation(
        tool_name=tool.name,
        technical_score=technical_score,
        community_score=community_score,
        license_score=license_score,
        integration_score=integration_score,
        overall_score=overall_score,
        recommendation=recommendation,
        integration_steps=integration_steps,
        potential_conflicts=potential_conflicts
    )


@tool_discovery_agent.tool
async def generate_integration_code(
    ctx: RunContext[ToolDependencies],
    tool: DiscoveredTool,
    evaluation: ToolEvaluation
) -> str:
    """Generate integration code for approved tools"""

    if evaluation.recommendation not in ["auto_integrate", "manual_review"]:
        return "# Tool not approved for integration"

    integration_code = f'''#!/usr/bin/env python3
"""
Integration wrapper for {tool.name}
Generated: {datetime.now().isoformat()}
Tool URL: {tool.url}
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

class {tool.name.replace("-", "_").title()}Integration:
    """Integration class for {tool.name}"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tool_name = "{tool.name}"
        self.tool_path = self._find_tool()

    def _find_tool(self) -> Path:
        """Locate the tool executable"""
        # Check common locations
        locations = [
            Path("/usr/local/bin") / self.tool_name,
            Path("/usr/bin") / self.tool_name,
            self.project_root / "tools" / self.tool_name / "bin" / self.tool_name
        ]

        for loc in locations:
            if loc.exists():
                return loc

        # Try to find in PATH
        result = subprocess.run(["which", self.tool_name], capture_output=True, text=True)
        if result.returncode == 0:
            return Path(result.stdout.strip())

        raise FileNotFoundError(f"Tool {{self.tool_name}} not found")

    def run_analysis(self, target_files: List[Path]) -> Dict[str, Any]:
        """Run the tool on specified files"""
        results = {{
            "tool": self.tool_name,
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": len(target_files),
            "issues": []
        }}

        for file in target_files:
            if not file.exists():
                continue

            cmd = [str(self.tool_path), str(file)]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Parse tool output (this is tool-specific)
                if result.returncode != 0:
                    results["issues"].append({{
                        "file": str(file),
                        "output": result.stdout,
                        "errors": result.stderr
                    }})
            except subprocess.TimeoutExpired:
                results["issues"].append({{
                    "file": str(file),
                    "error": "Analysis timeout"
                }})
            except Exception as e:
                results["issues"].append({{
                    "file": str(file),
                    "error": str(e)
                }})

        return results

    def integrate_with_cmake(self) -> str:
        """Generate CMake integration"""
        return f"""
# {tool.name} integration
find_program({tool.name.upper()}_EXECUTABLE {tool.name})
if({tool.name.upper()}_EXECUTABLE)
    add_custom_target({tool.name}_check
        COMMAND ${{{tool.name.upper()}_EXECUTABLE}} ${{CMAKE_SOURCE_DIR}}/src/*.cpp
        WORKING_DIRECTORY ${{CMAKE_SOURCE_DIR}}
        COMMENT "Running {tool.name} analysis"
    )
endif()
"""

# Integration test
if __name__ == "__main__":
    integration = {tool.name.replace("-", "_").title()}Integration(Path.cwd())
    test_files = list(Path("src").glob("*.cpp"))[:5]
    results = integration.run_analysis(test_files)
    print(json.dumps(results, indent=2))
'''

    return integration_code


@tool_discovery_agent.tool
async def save_discovery_report(
    ctx: RunContext[ToolDependencies],
    discoveries: List[DiscoveredTool],
    evaluations: List[ToolEvaluation]
) -> str:
    """Save discovery and evaluation report"""

    report_dir = ctx.deps.cache_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"tool_discovery_{timestamp}.json"

    report = {
        "timestamp": datetime.now().isoformat(),
        "discovered_tools": [tool.dict() for tool in discoveries],
        "evaluations": [eval.dict() for eval in evaluations],
        "summary": {
            "total_discovered": len(discoveries),
            "auto_integrate": sum(1 for e in evaluations if e.recommendation == "auto_integrate"),
            "manual_review": sum(1 for e in evaluations if e.recommendation == "manual_review"),
            "watch": sum(1 for e in evaluations if e.recommendation == "watch"),
            "skip": sum(1 for e in evaluations if e.recommendation == "skip")
        }
    }

    with report_file.open("w") as f:
        json.dump(report, f, indent=2, default=str)

    # Also create a markdown summary
    summary_file = report_dir / f"tool_discovery_{timestamp}.md"

    summary_content = f"""# Tool Discovery Report
Generated: {datetime.now().isoformat()}

## Summary
- **Total Discovered**: {len(discoveries)}
- **Recommended for Auto-Integration**: {report['summary']['auto_integrate']}
- **Requires Manual Review**: {report['summary']['manual_review']}
- **Watching**: {report['summary']['watch']}
- **Skipped**: {report['summary']['skip']}

## Recommended Tools for Integration

"""

    for tool, eval in zip(discoveries, evaluations):
        if eval.recommendation in ["auto_integrate", "manual_review"]:
            summary_content += f"""### {tool.name}
- **URL**: {tool.url}
- **Description**: {tool.description}
- **Language**: {tool.language}
- **Stars**: {tool.stars}
- **License**: {tool.license}
- **Overall Score**: {eval.overall_score:.2f}
- **Recommendation**: {eval.recommendation}

**Integration Steps**:
"""
            for step in eval.integration_steps:
                summary_content += f"- {step}\n"

            if eval.potential_conflicts:
                summary_content += "\n**Potential Conflicts**:\n"
                for conflict in eval.potential_conflicts:
                    summary_content += f"- ⚠️ {conflict}\n"

            summary_content += "\n---\n\n"

    with summary_file.open("w") as f:
        f.write(summary_content)

    return str(report_file)


# Main discovery workflow
async def run_tool_discovery(settings: Optional[ToolDiscoverySettings] = None):
    """Run the complete tool discovery workflow"""

    if not settings:
        settings = ToolDiscoverySettings()

    deps = ToolDependencies(
        settings=settings,
        cache_dir=Path("tool_discovery_cache"),
        integration_dir=Path("integrations")
    )

    logger.info("Starting tool discovery workflow")

    # Search for new tools
    github_tools = await tool_discovery_agent.run(
        "Search GitHub for new C++ static analysis and AI tools",
        deps=deps
    )

    awesome_tools = await tool_discovery_agent.run(
        "Search awesome lists for recommended tools",
        deps=deps
    )

    # Convert to DiscoveredTool objects
    all_discoveries = []

    # Process discoveries and create DiscoveredTool objects
    # (Implementation would parse the agent responses)

    # Evaluate each tool
    evaluations = []
    for tool in all_discoveries:
        evaluation = await tool_discovery_agent.run(
            f"Evaluate {tool.name} for integration into Wire Ground project",
            deps=deps
        )
        evaluations.append(evaluation)

    # Generate integration code for approved tools
    for tool, eval in zip(all_discoveries, evaluations):
        if eval.recommendation == "auto_integrate":
            code = await tool_discovery_agent.run(
                f"Generate integration code for {tool.name}",
                deps=deps
            )

            # Save integration code
            integration_file = deps.integration_dir / f"{tool.name}_integration.py"
            integration_file.parent.mkdir(parents=True, exist_ok=True)
            integration_file.write_text(code)

    # Save report
    report_path = await tool_discovery_agent.run(
        "Save discovery and evaluation report",
        deps=deps
    )

    logger.info(f"Tool discovery complete. Report saved to {report_path}")

    return {
        "discovered": len(all_discoveries),
        "evaluations": evaluations,
        "report": report_path
    }


if __name__ == "__main__":
    asyncio.run(run_tool_discovery())