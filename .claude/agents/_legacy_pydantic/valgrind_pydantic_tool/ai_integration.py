"""
AI integration for Valgrind issue analysis and fix suggestions.
Supports OpenAI and Anthropic APIs for generating code fixes.
"""

import json
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from models import ValgrindIssue, IssueCategory, LearningDatabase, ValgrindTool


class AIAnalyzer:
    """AI-powered analysis for Valgrind issues."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4"):
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.client = None
        
        if api_key:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AI client based on provider."""
        try:
            if self.provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            else:
                print(f"Warning: Unsupported AI provider: {self.provider}")
        except ImportError as e:
            print(f"Warning: AI client not available: {e}")
            self.client = None
    
    def generate_ai_prompt(self, issues: List[ValgrindIssue], learning_db: LearningDatabase, tool: ValgrindTool) -> str:
        """Generate comprehensive AI prompt for issue analysis."""
        
        prompt = f"""You are an expert C++ safety engineer analyzing Valgrind output from the {tool.value} tool.

## Analysis Context
- Tool: {tool.value}
- Total Issues: {len(issues)}
- Focus: Memory safety, thread safety, and performance optimization

## Issues Found:

"""
        
        for i, issue in enumerate(issues, 1):
            prompt += f"""### Issue {i}: {issue.category.value}
**Severity**: {issue.severity.value}
**Description**: {issue.description}
**Location**: {issue.file_path}:{issue.line_number}
**Function**: {issue.function}

"""
            if issue.stack_trace:
                prompt += "**Stack Trace**:\n"
                for frame in issue.stack_trace[:3]:  # Limit to top 3 frames
                    prompt += f"- {frame.function} ({frame.file_path}:{frame.line_number})\n"
                prompt += "\n"
            
            if issue.details:
                prompt += f"**Additional Details**: {json.dumps(issue.details, indent=2)}\n\n"
        
        # Add learning database insights
        if learning_db.pairs:
            prompt += "## Previously Successful Solutions:\n\n"
            
            categories_seen = set(issue.category for issue in issues)
            for category in categories_seen:
                suggestions = learning_db.get_suggestions(category, limit=2)
                if suggestions:
                    prompt += f"**{category.value}** patterns:\n"
                    for suggestion in suggestions:
                        prompt += f"- {suggestion}\n"
                    prompt += "\n"
        
        # Add tool-specific guidance
        tool_guidance = self._get_tool_specific_guidance(tool)
        if tool_guidance:
            prompt += f"## {tool.value} Specific Guidance:\n{tool_guidance}\n\n"
        
        prompt += """## Required Response Format:

For each issue, provide:

1. **Root Cause Analysis**: Technical explanation of why this issue occurs
2. **Risk Assessment**: Potential impact on program safety and performance
3. **C++ Code Fix**: Specific, compilable C++ code changes with before/after examples
4. **Prevention Strategy**: How to prevent similar issues in the future
5. **Testing Approach**: How to verify the fix works

Focus on:
- Modern C++ best practices (C++17/20/23)
- RAII principles and smart pointers
- Thread-safe programming patterns
- Performance optimization
- Memory safety guarantees

Provide concrete, actionable fixes that can be implemented immediately."""

        return prompt
    
    def _get_tool_specific_guidance(self, tool: ValgrindTool) -> str:
        """Get tool-specific guidance for AI analysis."""
        guidance = {
            ValgrindTool.MEMCHECK: """
- Focus on memory leaks, invalid accesses, and uninitialized values
- Prioritize RAII and smart pointer solutions
- Consider static analysis alternatives (AddressSanitizer)
- Suggest valgrind suppressions only as last resort
""",
            ValgrindTool.HELGRIND: """
- Focus on data races and lock ordering issues
- Suggest atomic operations, mutexes, and condition variables
- Consider lock-free algorithms where appropriate
- Recommend thread-safe design patterns
""",
            ValgrindTool.DRD: """
- Alternative thread error detection to Helgrind
- Focus on race conditions and synchronization primitives
- Suggest std::shared_mutex for reader-writer scenarios
- Consider task-based parallelism (std::async, thread pools)
""",
            ValgrindTool.CACHEGRIND: """
- Focus on cache performance optimization
- Suggest data structure layout improvements
- Recommend memory access pattern optimizations
- Consider SIMD and vectorization opportunities
""",
            ValgrindTool.CALLGRIND: """
- Focus on function call overhead and hot paths
- Suggest inlining strategies and template optimizations
- Recommend profile-guided optimization (PGO)
- Consider algorithmic complexity improvements
""",
            ValgrindTool.MASSIF: """
- Focus on heap usage patterns and memory allocation
- Suggest object pooling and custom allocators
- Recommend stack allocation alternatives
- Consider memory mapping for large data
""",
            ValgrindTool.DHAT: """
- Focus on dynamic heap analysis and fragmentation
- Suggest allocation strategies and memory pools
- Recommend RAII for automatic cleanup
- Consider placement new and custom allocators
"""
        }
        
        return guidance.get(tool, "")
    
    def call_llm_api(self, prompt: str) -> List[str]:
        """Call LLM API for analysis."""
        if not self.client or not self.api_key:
            return self._generate_fallback_suggestions(prompt)
        
        try:
            start_time = time.time()
            
            if self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                return self._generate_fallback_suggestions(prompt)
            
            execution_time = time.time() - start_time
            print(f"AI analysis completed in {execution_time:.2f}s")
            
            return self._parse_ai_response(response)
            
        except Exception as e:
            print(f"AI API call failed: {e}")
            return self._generate_fallback_suggestions(prompt)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert C++ safety engineer specializing in Valgrind analysis and memory safety optimization."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    def _parse_ai_response(self, response: str) -> List[str]:
        """Parse AI response into actionable suggestions."""
        suggestions = []
        
        # Split by issue sections
        sections = response.split("Issue")
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            current_suggestion = ""
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['fix:', 'solution:', 'recommendation:', 'suggestion:']):
                    if current_suggestion:
                        suggestions.append(current_suggestion.strip())
                    current_suggestion = line.strip()
                elif current_suggestion and line.strip():
                    current_suggestion += " " + line.strip()
            
            if current_suggestion:
                suggestions.append(current_suggestion.strip())
        
        # If parsing failed, treat whole response as one suggestion
        if not suggestions and response.strip():
            suggestions = [response.strip()]
        
        return suggestions
    
    def _generate_fallback_suggestions(self, prompt: str) -> List[str]:
        """Generate fallback suggestions when AI is not available."""
        # Extract issue categories from prompt
        suggestions = []
        
        if "MEMORY_LEAK" in prompt or "definitely lost" in prompt:
            suggestions.append("Replace raw pointers with smart pointers (std::unique_ptr, std::shared_ptr)")
            suggestions.append("Implement RAII pattern for automatic resource management")
            suggestions.append("Use containers instead of manual memory allocation")
        
        if "INVALID_READ" in prompt or "INVALID_WRITE" in prompt:
            suggestions.append("Add bounds checking before array/pointer access")
            suggestions.append("Use std::vector with at() method for safe access")
            suggestions.append("Consider using std::span for safe array views")
        
        if "DATA_RACE" in prompt:
            suggestions.append("Protect shared data with std::mutex and std::lock_guard")
            suggestions.append("Use std::atomic for simple shared variables")
            suggestions.append("Consider lock-free algorithms or thread-local storage")
        
        if "UNINITIALIZED_VALUE" in prompt:
            suggestions.append("Initialize all variables at declaration")
            suggestions.append("Use brace initialization to catch uninitialized values")
            suggestions.append("Consider std::optional for potentially unset values")
        
        if "CACHE_MISS" in prompt:
            suggestions.append("Improve data locality by reorganizing structures")
            suggestions.append("Use cache-friendly algorithms and access patterns")
            suggestions.append("Consider structure-of-arrays instead of array-of-structures")
        
        if not suggestions:
            suggestions.append("Review code for modern C++ best practices")
            suggestions.append("Add comprehensive unit tests to catch regressions")
            suggestions.append("Consider static analysis tools as complement to Valgrind")
        
        return suggestions


def generate_ai_prompt(issues: List[ValgrindIssue], learning_db: LearningDatabase, tool: ValgrindTool = ValgrindTool.MEMCHECK) -> str:
    """Generate AI prompt for issue analysis."""
    analyzer = AIAnalyzer()
    return analyzer.generate_ai_prompt(issues, learning_db, tool)


def call_llm(prompt: str, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4") -> List[str]:
    """Call LLM for analysis and return suggestions."""
    analyzer = AIAnalyzer(api_key, provider, model)
    return analyzer.call_llm_api(prompt)


class IssuePatternMatcher:
    """Pattern matching for common C++ safety issues."""
    
    @staticmethod
    def get_fix_templates() -> Dict[IssueCategory, List[str]]:
        """Get template fixes for common issue categories."""
        return {
            IssueCategory.MEMORY_LEAK: [
                "Replace 'new' with std::make_unique<T>()",
                "Use std::vector instead of manual array allocation",
                "Implement RAII wrapper class for resource management",
                "Add destructor to properly clean up resources"
            ],
            
            IssueCategory.INVALID_READ: [
                "Add bounds checking: if (index < container.size())",
                "Use container.at(index) instead of container[index]",
                "Check pointer validity: if (ptr != nullptr)",
                "Use std::span for safe array access"
            ],
            
            IssueCategory.INVALID_WRITE: [
                "Validate write bounds before assignment",
                "Use std::vector::resize() to ensure capacity",
                "Check pointer validity before dereferencing",
                "Use placement new for controlled memory writes"
            ],
            
            IssueCategory.DATA_RACE: [
                "Protect with std::lock_guard<std::mutex>",
                "Use std::atomic<T> for simple shared variables", 
                "Implement reader-writer lock with std::shared_mutex",
                "Consider lock-free algorithms or thread-local storage"
            ],
            
            IssueCategory.UNINITIALIZED_VALUE: [
                "Initialize variable at declaration: int x = 0;",
                "Use brace initialization: int x{};",
                "Consider std::optional<T> for potentially unset values",
                "Add constructor initialization list"
            ],
            
            IssueCategory.CACHE_MISS: [
                "Reorganize struct members by access frequency",
                "Use structure-of-arrays pattern for better locality",
                "Prefetch data with __builtin_prefetch()",
                "Align data structures to cache line boundaries"
            ]
        }
    
    @staticmethod
    def get_prevention_strategies() -> Dict[IssueCategory, List[str]]:
        """Get prevention strategies for issue categories."""
        return {
            IssueCategory.MEMORY_LEAK: [
                "Always use RAII principle",
                "Prefer stack allocation over heap",
                "Use smart pointers exclusively",
                "Enable compiler warnings for resource management"
            ],
            
            IssueCategory.DATA_RACE: [
                "Design thread-safe interfaces from start",
                "Minimize shared mutable state",
                "Use message passing between threads",
                "Apply ThreadSanitizer in development"
            ],
            
            IssueCategory.INVALID_READ: [
                "Enable runtime bounds checking",
                "Use containers with safe access methods",
                "Validate all inputs and parameters",
                "Add comprehensive unit tests"
            ]
        }