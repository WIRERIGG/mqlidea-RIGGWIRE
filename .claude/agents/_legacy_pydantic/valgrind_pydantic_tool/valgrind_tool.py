#!/usr/bin/env python3
"""
Comprehensive Valgrind analyzer tool with Pydantic integration.
Main ValgrindAnalyzer class implementing the callable interface for C++ safety analysis.
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .models import (
    ValgrindConfig, ValgrindResult, ValgrindTool, ValgrindState,
    ValgrindError, ValgrindMetrics, LearningDatabase,
    IssueCategory, ValgrindIssue
)
from .parsers.xml_parser import parse_xml_output as parse_xml
from .parsers.text_parser import parse_text_output as parse_text


class ValgrindAnalyzer:
    """
    Comprehensive Valgrind analyzer with Pydantic validation and AI integration.
    
    This class provides a callable interface for running Valgrind analysis on C++
    binaries with comprehensive configuration, parsing, and learning capabilities.
    
    Features:
    - Supports all Valgrind tools (Memcheck, Helgrind, Cachegrind, etc.)
    - Pydantic validation for all configurations and results
    - XML and text output parsing
    - AI-powered fix suggestions (optional)
    - Learning database for improvement over time
    - Comprehensive metrics extraction
    - Self-contained operation
    """
    
    def __init__(self, 
                 project_root: str = ".",
                 config_path: Optional[str] = None,
                 learning_db_path: str = "valgrind_learning.json"):
        """
        Initialize the ValgrindAnalyzer.
        
        Args:
            project_root: Root directory of the project
            config_path: Path to configuration file (optional)
            learning_db_path: Path to learning database file
        """
        self.project_root = Path(project_root).resolve()
        self.learning_db_path = Path(learning_db_path)
        
        # Initialize state
        self.state = ValgrindState(project_root=self.project_root)
        
        # Load or create default configuration
        self.default_config = self._load_default_config(config_path)
        
        # Load or create learning database
        self.learning_db = self._load_learning_db()
        
        # Setup logging
        self._setup_logging()
        
        # Validate Valgrind installation
        self._validate_valgrind_installation()
        
        logging.info(f"ValgrindAnalyzer initialized for project: {self.project_root}")
    
    def __call__(self, 
                 binary_path: str,
                 config: Optional[ValgrindConfig] = None,
                 ai_analyze: bool = False,
                 timeout: Optional[int] = None) -> ValgrindResult:
        """
        Run Valgrind analysis on the specified binary.
        
        Args:
            binary_path: Path to the binary to analyze
            config: Valgrind configuration (uses default if not provided)
            ai_analyze: Whether to run AI analysis on results
            timeout: Override timeout in seconds
            
        Returns:
            ValgrindResult containing all analysis results
        """
        start_time = time.time()
        
        try:
            # Use provided config or default
            analysis_config = config or self.default_config
            if timeout:
                analysis_config.timeout = timeout
            
            # Validate binary exists
            binary_path = Path(binary_path).resolve()
            if not binary_path.exists():
                raise ValgrindError(f"Binary not found: {binary_path}")
            
            # Update state
            self.state.analysis_start = datetime.now()
            self.state.current_tool = analysis_config.tool
            
            logging.info(f"Starting {analysis_config.tool} analysis of {binary_path}")
            
            # Build and execute Valgrind command
            command = self._build_command(binary_path, analysis_config)
            raw_output, xml_output = self._run_valgrind(command, analysis_config)
            
            # Parse output
            issues, metrics = self._parse_output(
                raw_output, xml_output, analysis_config.tool, analysis_config.xml_output
            )
            
            # Update state with results
            self.state.issues = issues
            self.state.metrics = metrics
            self.state.analysis_end = datetime.now()
            
            execution_time = time.time() - start_time
            
            # AI analysis if requested
            suggestions = None
            if ai_analyze and analysis_config.ai_analyze and analysis_config.llm_api_key:
                suggestions = self._ai_analyze_issues(issues)
                self.state.suggestions = suggestions
                self._learn_from_analysis(issues, suggestions)
            
            # Determine success
            success = len(issues) == 0 or all(
                issue.category in [IssueCategory.MEMORY_LEAK] and 
                issue.severity.value in ['warning', 'info'] 
                for issue in issues
            )
            
            result = ValgrindResult(
                success=success,
                tool_used=analysis_config.tool,
                binary_path=str(binary_path),
                config=analysis_config,
                issues=issues,
                metrics=metrics,
                suggestions=suggestions,
                raw_output=raw_output,
                xml_output=xml_output,
                execution_time=execution_time
            )
            
            logging.info(f"Analysis completed in {execution_time:.2f}s: {len(issues)} issues found")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Analysis failed after {execution_time:.2f}s: {e}")
            
            # Return failed result
            return ValgrindResult(
                success=False,
                tool_used=config.tool if config else ValgrindTool.MEMCHECK,
                binary_path=str(binary_path),
                config=config or self.default_config,
                issues=[],
                metrics=ValgrindMetrics(),
                raw_output=str(e),
                execution_time=execution_time
            )
    
    def run_multi_tool_analysis(self, 
                               binary_path: str,
                               tools: List[ValgrindTool],
                               base_config: Optional[ValgrindConfig] = None) -> List[ValgrindResult]:
        """
        Run analysis with multiple Valgrind tools.
        
        Args:
            binary_path: Path to binary to analyze
            tools: List of Valgrind tools to run
            base_config: Base configuration (tool will be overridden)
            
        Returns:
            List of ValgrindResult objects, one per tool
        """
        results = []
        base_config = base_config or self.default_config
        
        for tool in tools:
            # Create tool-specific config
            tool_config = base_config.copy()
            tool_config.tool = tool
            
            # Adjust tool-specific settings
            if tool == ValgrindTool.HELGRIND:
                tool_config.history_level = "full"
                tool_config.check_stack_refs = True
            elif tool == ValgrindTool.DRD:
                tool_config.free_is_write = False
                tool_config.segment_merging = True
            elif tool == ValgrindTool.CACHEGRIND:
                tool_config.cache_sim = True
                tool_config.branch_sim = True
            elif tool == ValgrindTool.MASSIF:
                tool_config.heap = True
                tool_config.stacks = False
            
            logging.info(f"Running {tool.value} analysis...")
            result = self(binary_path, tool_config)
            results.append(result)
        
        return results
    
    def _build_command(self, binary_path: Path, config: ValgrindConfig) -> List[str]:
        """Build Valgrind command line from configuration."""
        command = ["valgrind"]
        
        # Tool selection
        command.extend(["--tool=" + config.tool.value])
        
        # Output format
        if config.xml_output:
            command.append("--xml=yes")
            if config.xml_file:
                command.append(f"--xml-file={config.xml_file}")
        
        # General flags
        if config.leak_check and config.tool == ValgrindTool.MEMCHECK:
            command.append(f"--leak-check={config.leak_check}")
        
        if config.show_reachable is not None and config.tool == ValgrindTool.MEMCHECK:
            command.append(f"--show-reachable={'yes' if config.show_reachable else 'no'}")
        
        if config.track_origins is not None and config.tool == ValgrindTool.MEMCHECK:
            command.append(f"--track-origins={'yes' if config.track_origins else 'no'}")
        
        if config.track_fds is not None:
            command.append(f"--track-fds={'yes' if config.track_fds else 'no'}")
        
        if config.num_callers is not None:
            command.append(f"--num-callers={config.num_callers}")
        
        # Tool-specific flags
        if config.tool == ValgrindTool.HELGRIND:
            if config.history_level:
                command.append(f"--history-level={config.history_level}")
            if config.check_stack_refs is not None:
                command.append(f"--check-stack-refs={'yes' if config.check_stack_refs else 'no'}")
        
        elif config.tool == ValgrindTool.DRD:
            if config.free_is_write is not None:
                command.append(f"--free-is-write={'yes' if config.free_is_write else 'no'}")
            if config.segment_merging is not None:
                command.append(f"--segment-merging={'yes' if config.segment_merging else 'no'}")
        
        elif config.tool in [ValgrindTool.CACHEGRIND, ValgrindTool.CALLGRIND]:
            if config.cache_sim is not None:
                command.append(f"--cache-sim={'yes' if config.cache_sim else 'no'}")
            if config.branch_sim is not None:
                command.append(f"--branch-sim={'yes' if config.branch_sim else 'no'}")
            
            # Cache configuration
            if config.I1:
                command.append(f"--I1={config.I1}")
            if config.D1:
                command.append(f"--D1={config.D1}")
            if config.LL:
                command.append(f"--LL={config.LL}")
        
        elif config.tool == ValgrindTool.MASSIF:
            if config.heap is not None:
                command.append(f"--heap={'yes' if config.heap else 'no'}")
            if config.stacks is not None:
                command.append(f"--stacks={'yes' if config.stacks else 'no'}")
            if config.depth is not None:
                command.append(f"--depth={config.depth}")
        
        # Suppressions
        for suppression in (config.suppressions or []):
            command.append(f"--suppressions={suppression}")
        
        # Binary and arguments
        command.append(str(binary_path))
        if config.binary_args:
            command.extend(config.binary_args)
        
        return command
    
    def _run_valgrind(self, command: List[str], config: ValgrindConfig) -> Tuple[str, Optional[str]]:
        """Execute Valgrind command and capture output."""
        try:
            logging.debug(f"Executing: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=config.timeout,
                cwd=self.project_root
            )
            
            raw_output = result.stdout or ""
            xml_output = None
            
            # If XML output was requested and written to file, read it
            if config.xml_output and config.xml_file:
                xml_file = Path(config.xml_file)
                if xml_file.exists():
                    xml_output = xml_file.read_text()
            elif config.xml_output and raw_output.strip().startswith('<?xml'):
                xml_output = raw_output
            
            # Valgrind returns non-zero for errors found, not execution failure
            # Only raise exception for actual execution problems
            if result.returncode < 0:
                raise ValgrindError(f"Valgrind killed by signal {-result.returncode}")
            
            return raw_output, xml_output
            
        except subprocess.TimeoutExpired:
            raise ValgrindError(f"Valgrind timed out after {config.timeout} seconds")
        except FileNotFoundError:
            raise ValgrindError("Valgrind not found in PATH")
        except Exception as e:
            raise ValgrindError(f"Failed to run Valgrind: {e}")
    
    def _parse_output(self, raw_output: str, xml_output: Optional[str], 
                     tool: ValgrindTool, use_xml: bool) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Valgrind output and extract issues and metrics."""
        try:
            if use_xml and xml_output:
                return parse_xml(xml_output, tool)
            else:
                return parse_text(raw_output, tool)
        except Exception as e:
            logging.warning(f"Failed to parse output with preferred parser: {e}")
            # Fallback to text parsing
            return parse_text(raw_output, tool)
    
    def _ai_analyze_issues(self, issues: List[ValgrindIssue]) -> List[str]:
        """Generate AI-powered fix suggestions for issues."""
        if not issues:
            return []
        
        try:
            # Generate prompt based on issues and learning database
            prompt = self._generate_ai_prompt(issues)
            
            # Call LLM API (would need actual implementation)
            # For now, return learning database suggestions
            suggestions = []
            for issue in issues:
                learned_suggestions = self.learning_db.get_suggestions(issue.category)
                if learned_suggestions:
                    suggestions.extend(learned_suggestions[:2])  # Top 2 suggestions
            
            # Add generic suggestions if no learned ones
            if not suggestions:
                suggestions = self._get_generic_suggestions(issues)
            
            return suggestions
            
        except Exception as e:
            logging.warning(f"AI analysis failed: {e}")
            return self._get_generic_suggestions(issues)
    
    def _generate_ai_prompt(self, issues: List[ValgrindIssue]) -> str:
        """Generate AI prompt for issue analysis."""
        prompt = "Analyze these Valgrind issues in C++ code and provide fix suggestions:\n\n"
        
        for i, issue in enumerate(issues[:10], 1):  # Limit to 10 issues
            prompt += f"{i}. {issue.category.value}: {issue.description}\n"
            if issue.file_path and issue.line_number:
                prompt += f"   Location: {issue.file_path}:{issue.line_number}\n"
            if issue.function_name:
                prompt += f"   Function: {issue.function_name}\n"
            prompt += "\n"
        
        # Add context from learning database
        categories = {issue.category for issue in issues}
        for category in categories:
            learned = self.learning_db.get_suggestions(category)
            if learned:
                prompt += f"Previous successful fixes for {category.value}:\n"
                for suggestion in learned[:3]:
                    prompt += f"- {suggestion}\n"
                prompt += "\n"
        
        prompt += "Provide specific C++ code fixes and RAII recommendations for safety."
        
        return prompt
    
    def _get_generic_suggestions(self, issues: List[ValgrindIssue]) -> List[str]:
        """Get generic fix suggestions for common issue categories."""
        suggestions = []
        categories = {issue.category for issue in issues}
        
        generic_fixes = {
            IssueCategory.MEMORY_LEAK: [
                "Use RAII: Replace raw pointers with std::unique_ptr or std::shared_ptr",
                "Ensure every 'new' has a matching 'delete' in the same scope",
                "Consider using std::vector or std::string instead of manual memory management"
            ],
            IssueCategory.INVALID_READ: [
                "Check array bounds before access using .at() or range checks",
                "Initialize pointers to nullptr and check before dereferencing",
                "Use std::span or gsl::span for safe array access"
            ],
            IssueCategory.INVALID_WRITE: [
                "Validate buffer sizes before writing",
                "Use std::vector::resize() instead of manual buffer management",
                "Check iterator validity before use"
            ],
            IssueCategory.UNINITIALIZED_VALUE: [
                "Initialize all variables at declaration",
                "Use constructor initializer lists",
                "Consider default member initializers in classes"
            ],
            IssueCategory.DATA_RACE: [
                "Use std::mutex with std::lock_guard for thread safety",
                "Consider std::atomic for simple shared variables",
                "Apply thread-safe design patterns like message passing"
            ],
            IssueCategory.DOUBLE_FREE: [
                "Use smart pointers to prevent double free",
                "Set pointers to nullptr after delete",
                "Implement proper copy/move constructors and destructors"
            ]
        }
        
        for category in categories:
            if category in generic_fixes:
                suggestions.extend(generic_fixes[category])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _learn_from_analysis(self, issues: List[ValgrindIssue], suggestions: List[str]):
        """Update learning database with new issue-suggestion pairs."""
        if not issues or not suggestions:
            return
        
        try:
            # Associate suggestions with issue categories
            categories = [issue.category for issue in issues]
            
            # Simple heuristic: distribute suggestions among categories
            suggestions_per_category = max(1, len(suggestions) // len(set(categories)))
            
            category_suggestions = {}
            for i, category in enumerate(set(categories)):
                start_idx = i * suggestions_per_category
                end_idx = start_idx + suggestions_per_category
                category_suggestions[category] = suggestions[start_idx:end_idx]
            
            # Update learning database
            for category, category_sugs in category_suggestions.items():
                for suggestion in category_sugs:
                    self.learning_db.add_suggestion(category, suggestion)
            
            # Save updated database
            self._save_learning_db()
            
        except Exception as e:
            logging.warning(f"Failed to update learning database: {e}")
    
    def _load_default_config(self, config_path: Optional[str]) -> ValgrindConfig:
        """Load default configuration from file or create default."""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                return ValgrindConfig(**config_data)
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")
        
        # Create default configuration
        return ValgrindConfig(
            tool=ValgrindTool.MEMCHECK,
            leak_check="full",
            track_origins=True,
            show_reachable=True,
            num_callers=12,
            xml_output=True,
            timeout=1800  # 30 minutes
        )
    
    def _load_learning_db(self) -> LearningDatabase:
        """Load learning database from file or create new."""
        if self.learning_db_path.exists():
            try:
                with open(self.learning_db_path, 'r') as f:
                    data = json.load(f)
                return LearningDatabase(**data)
            except Exception as e:
                logging.warning(f"Failed to load learning database: {e}")
        
        return LearningDatabase()
    
    def _save_learning_db(self):
        """Save learning database to file."""
        try:
            with open(self.learning_db_path, 'w') as f:
                json.dump(self.learning_db.dict(), f, indent=2, default=str)
        except Exception as e:
            logging.warning(f"Failed to save learning database: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.project_root / 'valgrind_analyzer.log')
            ]
        )
    
    def _validate_valgrind_installation(self):
        """Validate that Valgrind is installed and accessible."""
        try:
            result = subprocess.run(
                ["valgrind", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise ValgrindError("Valgrind not working properly")
            
            version = result.stdout.strip()
            logging.info(f"Valgrind detected: {version}")
            
        except FileNotFoundError:
            raise ValgrindError("Valgrind not found. Please install Valgrind.")
        except subprocess.TimeoutExpired:
            raise ValgrindError("Valgrind version check timed out")
        except Exception as e:
            raise ValgrindError(f"Failed to validate Valgrind: {e}")


# CLI interface for direct execution
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Comprehensive Valgrind analyzer")
    parser.add_argument("binary", help="Binary to analyze")
    parser.add_argument("--tool", choices=[t.value for t in ValgrindTool], 
                       default="memcheck", help="Valgrind tool to use")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--ai-analyze", action="store_true", 
                       help="Enable AI analysis")
    parser.add_argument("--timeout", type=int, default=3600,
                       help="Analysis timeout in seconds")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = ValgrindAnalyzer(config_path=args.config)
        
        # Create configuration
        config = ValgrindConfig(
            tool=ValgrindTool(args.tool),
            timeout=args.timeout,
            ai_analyze=args.ai_analyze
        )
        
        # Run analysis
        result = analyzer(args.binary, config, ai_analyze=args.ai_analyze)
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result.model_dump_json(indent=2))
        else:
            print(result.get_summary())
            if result.suggestions:
                print("\nSuggestions:")
                for suggestion in result.suggestions:
                    print(f"- {suggestion}")
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)