"""
GitHub Integration Module - Automated issue creation and PR management
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

from pydantic_ai import Agent, RunContext, Tool
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from github import Github, PullRequest, Issue
from github.GithubException import GithubException

load_dotenv()

logger = logging.getLogger(__name__)


class GitHubSettings(BaseSettings):
    """GitHub integration settings"""

    # Authentication
    github_token: str = Field(..., description="GitHub personal access token")
    github_repo: str = Field(..., description="Repository name (owner/repo)")

    # Issue Settings
    auto_create_issues: bool = Field(default=True, description="Automatically create issues")
    issue_labels: List[str] = Field(
        default=["automated", "ai-generated"],
        description="Default labels for created issues"
    )
    assign_to: List[str] = Field(default_factory=list, description="Auto-assign issues to these users")

    # PR Settings
    auto_review_prs: bool = Field(default=True, description="Automatically review PRs")
    require_tests: bool = Field(default=True, description="Require tests for PRs")
    auto_merge_threshold: float = Field(default=0.95, description="Auto-merge confidence threshold")

    # Webhook Settings
    webhook_secret: Optional[str] = Field(default=None, description="GitHub webhook secret")
    webhook_port: int = Field(default=8080, description="Port for webhook listener")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class IssueType(str, Enum):
    """Types of GitHub issues"""
    BUG = "bug"
    FEATURE = "enhancement"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    REFACTOR = "refactoring"


class PRStatus(str, Enum):
    """Pull request status"""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class GitHubIssue(BaseModel):
    """Model for GitHub issue"""
    title: str
    body: str
    issue_type: IssueType
    priority: str = "medium"
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    milestone: Optional[str] = None
    related_files: List[str] = Field(default_factory=list)
    detected_by: str = "ai_agent"


class PRReview(BaseModel):
    """Model for pull request review"""
    pr_number: int
    review_status: PRStatus
    comments: List[str]
    suggestions: List[Dict[str, str]]
    confidence_score: float
    test_coverage: float
    performance_impact: Optional[str] = None
    security_concerns: List[str] = Field(default_factory=list)


class GitHubDependencies(BaseModel):
    """Dependencies for GitHub integration"""
    settings: GitHubSettings
    github_client: Optional[Github] = None
    repo: Optional[Any] = None


# Initialize GitHub integration agent
github_agent = Agent(
    model="claude-3-5-sonnet-20240620",
    deps_type=GitHubDependencies,
    system_prompt="""You are a GitHub integration specialist for the Wire Ground C++ project.

Your responsibilities:
1. Analyze code and testing results to create appropriate GitHub issues
2. Review pull requests for code quality, test coverage, and security
3. Generate helpful PR comments and suggestions
4. Manage issue labels and milestones appropriately
5. Coordinate with CI/CD systems for automated workflows

When creating issues:
- Use clear, actionable titles
- Provide detailed descriptions with context
- Include code snippets when relevant
- Suggest potential solutions
- Set appropriate labels and priorities

When reviewing PRs:
- Check for code quality and style compliance
- Verify test coverage
- Identify security concerns
- Suggest performance improvements
- Ensure documentation is updated
"""
)


@github_agent.tool
async def create_issue(
    ctx: RunContext[GitHubDependencies],
    issue: GitHubIssue
) -> Dict[str, Any]:
    """Create a GitHub issue"""

    if not ctx.deps.github_client:
        ctx.deps.github_client = Github(ctx.deps.settings.github_token)

    if not ctx.deps.repo:
        ctx.deps.repo = ctx.deps.github_client.get_repo(ctx.deps.settings.github_repo)

    try:
        # Prepare issue body with additional context
        enhanced_body = f"""{issue.body}

---
**Additional Context:**
- Detected by: {issue.detected_by}
- Priority: {issue.priority}
- Type: {issue.issue_type.value}
"""

        if issue.related_files:
            enhanced_body += f"\n**Related Files:**\n"
            for file in issue.related_files:
                enhanced_body += f"- `{file}`\n"

        # Create the issue
        created_issue = ctx.deps.repo.create_issue(
            title=issue.title,
            body=enhanced_body,
            labels=issue.labels + ctx.deps.settings.issue_labels,
            assignees=issue.assignees or ctx.deps.settings.assign_to
        )

        # Set milestone if specified
        if issue.milestone:
            milestones = ctx.deps.repo.get_milestones()
            for milestone in milestones:
                if milestone.title == issue.milestone:
                    created_issue.edit(milestone=milestone)
                    break

        logger.info(f"Created issue #{created_issue.number}: {issue.title}")

        return {
            "success": True,
            "issue_number": created_issue.number,
            "issue_url": created_issue.html_url,
            "title": issue.title
        }

    except GithubException as e:
        logger.error(f"Failed to create issue: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@github_agent.tool
async def review_pr(
    ctx: RunContext[GitHubDependencies],
    pr_number: int
) -> PRReview:
    """Review a pull request"""

    if not ctx.deps.github_client:
        ctx.deps.github_client = Github(ctx.deps.settings.github_token)

    if not ctx.deps.repo:
        ctx.deps.repo = ctx.deps.github_client.get_repo(ctx.deps.settings.github_repo)

    try:
        pr = ctx.deps.repo.get_pull(pr_number)

        # Analyze PR changes
        files_changed = pr.get_files()
        commits = pr.get_commits()

        comments = []
        suggestions = []
        security_concerns = []

        # Check each file
        total_additions = 0
        total_deletions = 0
        has_tests = False
        has_docs = False

        for file in files_changed:
            total_additions += file.additions
            total_deletions += file.deletions

            # Check for test files
            if "test" in file.filename.lower():
                has_tests = True

            # Check for documentation
            if file.filename.endswith((".md", ".rst", ".txt")):
                has_docs = True

            # Security checks
            if file.patch:
                # Check for hardcoded secrets
                if any(keyword in file.patch.lower() for keyword in ["password", "secret", "api_key", "token"]):
                    security_concerns.append(f"Potential hardcoded secret in {file.filename}")

                # Check for unsafe functions (C++)
                unsafe_functions = ["strcpy", "sprintf", "gets", "scanf"]
                for func in unsafe_functions:
                    if func in file.patch:
                        suggestions.append({
                            "file": file.filename,
                            "suggestion": f"Replace unsafe function {func} with safer alternative"
                        })

        # Calculate confidence score
        confidence_score = 0.5  # Base score

        if has_tests:
            confidence_score += 0.2
        else:
            comments.append("⚠️ No test files detected. Please add tests for your changes.")

        if has_docs:
            confidence_score += 0.1
        else:
            comments.append("📝 Consider updating documentation for these changes.")

        if not security_concerns:
            confidence_score += 0.2
        else:
            confidence_score -= 0.1
            for concern in security_concerns:
                comments.append(f"🔒 Security: {concern}")

        # Determine review status
        if confidence_score >= ctx.deps.settings.auto_merge_threshold:
            review_status = PRStatus.APPROVED
            comments.append("✅ This PR looks good and meets all quality criteria.")
        elif confidence_score >= 0.7:
            review_status = PRStatus.PENDING
            comments.append("⏳ This PR needs minor improvements before approval.")
        elif confidence_score >= 0.5:
            review_status = PRStatus.CHANGES_REQUESTED
            comments.append("🔄 Please address the feedback before this PR can be approved.")
        else:
            review_status = PRStatus.REJECTED
            comments.append("❌ This PR has significant issues that need to be resolved.")

        # Calculate test coverage estimate (simplified)
        test_coverage = 0.8 if has_tests else 0.2

        # Performance impact assessment
        performance_impact = None
        if total_additions > 500:
            performance_impact = "high"
            comments.append("⚡ Large PR - consider breaking into smaller changes for easier review.")
        elif total_additions > 100:
            performance_impact = "medium"

        return PRReview(
            pr_number=pr_number,
            review_status=review_status,
            comments=comments,
            suggestions=suggestions,
            confidence_score=confidence_score,
            test_coverage=test_coverage,
            performance_impact=performance_impact,
            security_concerns=security_concerns
        )

    except GithubException as e:
        logger.error(f"Failed to review PR: {e}")
        return PRReview(
            pr_number=pr_number,
            review_status=PRStatus.PENDING,
            comments=[f"Error reviewing PR: {e}"],
            suggestions=[],
            confidence_score=0.0,
            test_coverage=0.0
        )


@github_agent.tool
async def post_pr_review(
    ctx: RunContext[GitHubDependencies],
    review: PRReview
) -> bool:
    """Post review comments to a pull request"""

    if not ctx.deps.github_client:
        ctx.deps.github_client = Github(ctx.deps.settings.github_token)

    if not ctx.deps.repo:
        ctx.deps.repo = ctx.deps.github_client.get_repo(ctx.deps.settings.github_repo)

    try:
        pr = ctx.deps.repo.get_pull(review.pr_number)

        # Prepare review body
        review_body = f"""## AI Review Results

**Status:** {review.review_status.value}
**Confidence Score:** {review.confidence_score:.2f}
**Test Coverage Estimate:** {review.test_coverage:.1%}
"""

        if review.performance_impact:
            review_body += f"**Performance Impact:** {review.performance_impact}\n"

        if review.comments:
            review_body += "\n### Comments\n"
            for comment in review.comments:
                review_body += f"- {comment}\n"

        if review.suggestions:
            review_body += "\n### Suggestions\n"
            for suggestion in review.suggestions:
                review_body += f"- **{suggestion['file']}**: {suggestion['suggestion']}\n"

        if review.security_concerns:
            review_body += "\n### ⚠️ Security Concerns\n"
            for concern in review.security_concerns:
                review_body += f"- {concern}\n"

        # Post the review
        if review.review_status == PRStatus.APPROVED:
            pr.create_review(body=review_body, event="APPROVE")
        elif review.review_status == PRStatus.CHANGES_REQUESTED:
            pr.create_review(body=review_body, event="REQUEST_CHANGES")
        else:
            pr.create_review(body=review_body, event="COMMENT")

        logger.info(f"Posted review for PR #{review.pr_number}")
        return True

    except GithubException as e:
        logger.error(f"Failed to post PR review: {e}")
        return False


@github_agent.tool
async def create_issue_from_analysis(
    ctx: RunContext[GitHubDependencies],
    analysis_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Create issues based on code analysis results"""

    created_issues = []

    # Parse analysis results to identify issues
    if "errors" in analysis_results:
        for error in analysis_results["errors"]:
            issue = GitHubIssue(
                title=f"Fix: {error.get('message', 'Error detected')}",
                body=f"""An error was detected during automated code analysis.

**Error Details:**
- File: `{error.get('file', 'unknown')}`
- Line: {error.get('line', 'unknown')}
- Message: {error.get('message', 'No message')}

**Suggested Fix:**
{error.get('suggestion', 'Please review and fix the issue.')}
""",
                issue_type=IssueType.BUG,
                priority="high",
                labels=["bug", "automated-detection"],
                related_files=[error.get('file', '')]
            )

            result = await create_issue(ctx, issue)
            created_issues.append(result)

    # Create issues for performance problems
    if "performance_issues" in analysis_results:
        for perf_issue in analysis_results["performance_issues"]:
            issue = GitHubIssue(
                title=f"Performance: {perf_issue.get('description', 'Optimization needed')}",
                body=f"""A performance issue was identified.

**Details:**
- Location: `{perf_issue.get('location', 'unknown')}`
- Impact: {perf_issue.get('impact', 'unknown')}
- Current Performance: {perf_issue.get('current', 'N/A')}
- Expected Performance: {perf_issue.get('expected', 'N/A')}

**Recommendation:**
{perf_issue.get('recommendation', 'Optimize this code section.')}
""",
                issue_type=IssueType.PERFORMANCE,
                priority="medium",
                labels=["performance", "optimization"],
                related_files=perf_issue.get('files', [])
            )

            result = await create_issue(ctx, issue)
            created_issues.append(result)

    # Create issues for security vulnerabilities
    if "security_issues" in analysis_results:
        for sec_issue in analysis_results["security_issues"]:
            issue = GitHubIssue(
                title=f"Security: {sec_issue.get('vulnerability', 'Vulnerability detected')}",
                body=f"""A security vulnerability was detected.

⚠️ **SECURITY ISSUE** ⚠️

**Vulnerability Details:**
- Type: {sec_issue.get('type', 'unknown')}
- Severity: {sec_issue.get('severity', 'unknown')}
- Location: `{sec_issue.get('location', 'unknown')}`

**Impact:**
{sec_issue.get('impact', 'Potential security risk.')}

**Remediation:**
{sec_issue.get('remediation', 'Please fix this security issue immediately.')}
""",
                issue_type=IssueType.SECURITY,
                priority="critical",
                labels=["security", "vulnerability", "critical"],
                related_files=sec_issue.get('files', [])
            )

            result = await create_issue(ctx, issue)
            created_issues.append(result)

    return created_issues


@github_agent.tool
async def setup_webhook_handler(
    ctx: RunContext[GitHubDependencies]
) -> Dict[str, Any]:
    """Set up webhook handler for GitHub events"""

    # This would typically set up a webhook listener
    # For demonstration, we'll return the configuration

    webhook_config = {
        "url": f"https://your-domain.com/github-webhook",
        "port": ctx.deps.settings.webhook_port,
        "events": [
            "push",
            "pull_request",
            "issues",
            "issue_comment",
            "pull_request_review",
            "workflow_run"
        ],
        "secret": ctx.deps.settings.webhook_secret,
        "handlers": {
            "push": "handle_push_event",
            "pull_request": "handle_pr_event",
            "issues": "handle_issue_event",
            "workflow_run": "handle_workflow_event"
        }
    }

    return webhook_config


class GitHubIntegration:
    """Main GitHub integration class"""

    def __init__(self, settings: Optional[GitHubSettings] = None):
        self.settings = settings or GitHubSettings()
        self.github = Github(self.settings.github_token)
        self.repo = self.github.get_repo(self.settings.github_repo)

    async def analyze_and_create_issues(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze results and create appropriate issues"""

        deps = GitHubDependencies(
            settings=self.settings,
            github_client=self.github,
            repo=self.repo
        )

        return await github_agent.run(
            "Create GitHub issues based on code analysis results",
            deps=deps,
            analysis_results=analysis_results
        )

    async def review_open_prs(self) -> List[PRReview]:
        """Review all open pull requests"""

        deps = GitHubDependencies(
            settings=self.settings,
            github_client=self.github,
            repo=self.repo
        )

        reviews = []
        open_prs = self.repo.get_pulls(state="open")

        for pr in open_prs:
            logger.info(f"Reviewing PR #{pr.number}: {pr.title}")

            review = await github_agent.run(
                f"Review pull request #{pr.number}",
                deps=deps,
                pr_number=pr.number
            )

            reviews.append(review)

            # Post the review if auto-review is enabled
            if self.settings.auto_review_prs:
                await github_agent.run(
                    f"Post review for PR #{pr.number}",
                    deps=deps,
                    review=review
                )

        return reviews

    async def handle_webhook_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook events"""

        handlers = {
            "push": self._handle_push,
            "pull_request": self._handle_pr,
            "issues": self._handle_issue,
            "workflow_run": self._handle_workflow
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(payload)

        return {"status": "unhandled", "event": event_type}

    async def _handle_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push events"""
        # Analyze pushed commits and create issues if needed
        return {"status": "processed", "action": "push_analyzed"}

    async def _handle_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request events"""
        if payload.get("action") in ["opened", "synchronize"]:
            # Review the PR
            pr_number = payload["pull_request"]["number"]
            deps = GitHubDependencies(
                settings=self.settings,
                github_client=self.github,
                repo=self.repo
            )

            review = await github_agent.run(
                f"Review pull request #{pr_number}",
                deps=deps,
                pr_number=pr_number
            )

            return {"status": "reviewed", "pr_number": pr_number}

        return {"status": "ignored", "action": payload.get("action")}

    async def _handle_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue events"""
        return {"status": "processed", "action": "issue_handled"}

    async def _handle_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow run events"""
        return {"status": "processed", "action": "workflow_handled"}


# Main execution
async def setup_github_integration():
    """Set up and test GitHub integration"""

    integration = GitHubIntegration()

    # Test by reviewing open PRs
    reviews = await integration.review_open_prs()
    logger.info(f"Reviewed {len(reviews)} pull requests")

    # Example: Create an issue from analysis
    sample_analysis = {
        "errors": [
            {
                "file": "src/main.cpp",
                "line": 42,
                "message": "Memory leak detected",
                "suggestion": "Add proper memory deallocation"
            }
        ],
        "performance_issues": [
            {
                "location": "src/algorithm.cpp:100-150",
                "description": "Inefficient sorting algorithm",
                "impact": "O(n²) complexity",
                "current": "Bubble sort",
                "expected": "Quick sort or merge sort",
                "recommendation": "Replace with std::sort or implement efficient sorting",
                "files": ["src/algorithm.cpp"]
            }
        ]
    }

    created_issues = await integration.analyze_and_create_issues(sample_analysis)
    logger.info(f"Created {len(created_issues)} issues")

    return {
        "reviews": reviews,
        "created_issues": created_issues
    }


if __name__ == "__main__":
    asyncio.run(setup_github_integration())