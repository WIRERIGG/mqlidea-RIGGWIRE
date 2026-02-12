#!/usr/bin/env python3
"""
Automatic Clang-Tidy Error Detection and Response System
Monitors build output and automatically invokes clang-tidy-fixer when issues are detected
"""

import re
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import argparse
import fnmatch

@dataclass
class ClangTidyIssue:
    """Represents a detected clang-tidy issue"""
    file_path: str
    line_number: int
    column: int
    severity: str
    check_name: str
    message: str
    full_line: str

@dataclass
class DetectionResult:
    """Results of clang-tidy detection"""
    issues_found: List[ClangTidyIssue]
    total_warnings: int
    total_errors: int
    affected_files: List[str]
    should_auto_fix: bool

class ClangTidyDetector:
    """Automatic clang-tidy issue detection and response system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = Path("/IdeaProjects/wire_ground")
        self.config = self._load_config(config_path)
        
        # Clang-tidy warning patterns
        self.warning_patterns = [
            # Standard clang-tidy format: file:line:col: warning: message [check-name]
            r"([^:]+):(\d+):(\d+):\s*(warning|error|note):\s*(.+?)\s*\[([^\]]+)\]",
            # CMake build format
            r"(.+):(\d+):(\d+):\s*(warning|error):\s*(.+)",
            # Alternative format
            r"([^:]+)\((\d+)\):\s*(warning|error):\s*(.+)",
        ]
        
        # High-priority checks that should trigger immediate fixing
        self.critical_checks = {
            'bugprone-*', 'cert-*', 'clang-analyzer-*', 'security-*',
            'modernize-use-after-move', 'readability-deleted-default',
            'performance-*', 'concurrency-*'
        }
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration for detection thresholds and behavior"""
        default_config = {
            "auto_fix_enabled": True,
            "max_warnings_threshold": 10,
            "critical_only_mode": False,
            "exclude_patterns": ["*test*", "*benchmark*"],
            "include_file_patterns": ["src/**/*.cpp", "include/**/*.hpp"],
            "auto_fix_timeout": 300,  # 5 minutes
            "session_persistence": True
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
        
        return default_config
    
    def detect_issues_from_build_output(self, build_output: str) -> DetectionResult:
        """Parse build output to detect clang-tidy issues"""
        issues = []
        
        for line in build_output.split('\n'):
            issue = self._parse_clang_tidy_line(line.strip())
            if issue:
                issues.append(issue)
        
        # Analyze results
        warnings = [i for i in issues if i.severity == 'warning']
        errors = [i for i in issues if i.severity == 'error']
        affected_files = list(set(i.file_path for i in issues))
        
        # Determine if auto-fix should be triggered
        should_auto_fix = self._should_trigger_auto_fix(issues, warnings, errors)
        
        return DetectionResult(
            issues_found=issues,
            total_warnings=len(warnings),
            total_errors=len(errors),
            affected_files=affected_files,
            should_auto_fix=should_auto_fix
        )
    
    def _parse_clang_tidy_line(self, line: str) -> Optional[ClangTidyIssue]:
        """Parse a single line to extract clang-tidy issue information"""
        for pattern in self.warning_patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                
                if len(groups) >= 6:  # Full format with check name
                    file_path, line_num, col, severity, message, check_name = groups[:6]
                elif len(groups) >= 5:  # Format without check name
                    file_path, line_num, col, severity, message = groups[:5]
                    check_name = "unknown"
                else:
                    continue
                
                # Filter out non-project files
                if not self._is_project_file(file_path):
                    continue
                
                return ClangTidyIssue(
                    file_path=file_path,
                    line_number=int(line_num),
                    column=int(col),
                    severity=severity,
                    check_name=check_name,
                    message=message,
                    full_line=line
                )
        return None
    
    def _is_project_file(self, file_path: str) -> bool:
        """Check if file is part of the project and should be processed"""
        path = Path(file_path)
        
        # Must be within project root
        try:
            relative_path = path.resolve().relative_to(self.project_root.resolve())
        except ValueError:
            return False
        
        # Convert to string for pattern matching
        relative_str = str(relative_path).replace('\\', '/')
        
        # Check include patterns with custom recursive matching
        include_patterns = self.config.get("include_file_patterns", [])
        if include_patterns:
            matched = False
            for pattern in include_patterns:
                if self._matches_pattern(relative_str, pattern):
                    matched = True
                    break
            
            if not matched:
                return False
        
        # Check exclude patterns
        exclude_patterns = self.config.get("exclude_patterns", [])
        for pattern in exclude_patterns:
            if self._matches_pattern(relative_str, pattern):
                return False
        
        return True
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if a file path matches a glob pattern, handling ** for recursive matching"""
        # Handle ** recursive patterns  
        if '**' in pattern:
            # Convert glob pattern to regex, handling both src/*/*.cpp and src/**/*.cpp
            # ** should match zero or more path components
            regex_pattern = re.escape(pattern)
            # Replace ** with pattern that matches zero or more path segments
            regex_pattern = regex_pattern.replace('\\*\\*/', '(?:[^/]+/)*')  # ** matches zero or more dirs
            regex_pattern = regex_pattern.replace('\\*\\*', '(?:[^/]+/?)*')  # ** at end
            regex_pattern = regex_pattern.replace('\\*', '[^/]*')           # * matches within segment
            regex_pattern = f'^{regex_pattern}$'
            
            result = bool(re.match(regex_pattern, file_path))
            return result
        else:
            # Use fnmatch for simple patterns
            return fnmatch.fnmatch(file_path, pattern)
    
    def _should_trigger_auto_fix(self, issues: List[ClangTidyIssue], 
                                warnings: List[ClangTidyIssue], 
                                errors: List[ClangTidyIssue]) -> bool:
        """Determine if automatic fixing should be triggered"""
        if not self.config.get("auto_fix_enabled", True):
            return False
        
        # Always trigger on errors
        if errors:
            return True
        
        # Check critical warnings
        critical_warnings = [w for w in warnings if self._is_critical_check(w.check_name)]
        if critical_warnings:
            return True
        
        # Check warning threshold
        max_warnings = self.config.get("max_warnings_threshold", 10)
        if len(warnings) > max_warnings:
            return True
        
        # In critical-only mode, only fix critical issues
        if self.config.get("critical_only_mode", False):
            return len(critical_warnings) > 0
        
        # Default: fix if any issues found
        return len(issues) > 0
    
    def _is_critical_check(self, check_name: str) -> bool:
        """Check if a clang-tidy check is considered critical"""
        for critical_pattern in self.critical_checks:
            if critical_pattern.endswith('*'):
                if check_name.startswith(critical_pattern[:-1]):
                    return True
            elif check_name == critical_pattern:
                return True
        return False
    
    def invoke_clang_tidy_fixer(self, detection_result: DetectionResult) -> Dict:
        """Automatically invoke the clang-tidy-fixer agent"""
        print("🔧 Automatic clang-tidy issue detection triggered!")
        print(f"Found {detection_result.total_warnings} warnings and {detection_result.total_errors} errors")
        print(f"Affected files: {', '.join(detection_result.affected_files[:5])}")
        if len(detection_result.affected_files) > 5:
            print(f"... and {len(detection_result.affected_files) - 5} more files")
        
        # Determine strategy based on number of affected files
        if len(detection_result.affected_files) == 1:
            # Single file - use analyze command
            file_path = detection_result.affected_files[0]
            return self._run_single_file_fix(file_path)
        elif len(detection_result.affected_files) <= 5:
            # Few files - fix each individually
            results = []
            for file_path in detection_result.affected_files:
                result = self._run_single_file_fix(file_path)
                results.append(result)
            return {"strategy": "individual_files", "results": results}
        else:
            # Many files - use project-wide analysis
            return self._run_project_fix(detection_result.affected_files)
    
    def _run_single_file_fix(self, file_path: str) -> Dict:
        """Run clang-tidy-fixer on a single file"""
        try:
            cmd = [
                str(self.project_root / "scripts" / "ai_clang_tidy.sh"),
                "analyze",
                file_path
            ]
            
            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get("auto_fix_timeout", 300),
                cwd=self.project_root
            )
            
            return {
                "file": file_path,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "file": file_path,
                "success": False,
                "error": "Timeout during analysis",
                "returncode": -1
            }
        except Exception as e:
            return {
                "file": file_path,
                "success": False,
                "error": str(e),
                "returncode": -1
            }
    
    def _run_project_fix(self, affected_files: List[str]) -> Dict:
        """Run project-wide clang-tidy-fixer analysis"""
        try:
            # Create pattern for affected files
            src_files = [f for f in affected_files if "/src/" in f]
            if src_files:
                pattern = "src/**/*.cpp"
            else:
                pattern = "**/*.cpp"
            
            cmd = [
                str(self.project_root / "scripts" / "ai_clang_tidy.sh"),
                "project",
                pattern
            ]
            
            print(f"🌟 Running project-wide analysis: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get("auto_fix_timeout", 300),
                cwd=self.project_root
            )
            
            return {
                "strategy": "project_wide",
                "pattern": pattern,
                "affected_files_count": len(affected_files),
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "strategy": "project_wide",
                "success": False,
                "error": str(e),
                "returncode": -1
            }

def main():
    """Main entry point for the clang-tidy auto-detector"""
    parser = argparse.ArgumentParser(description="Automatic Clang-Tidy Error Detection and Response")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--input", help="Input file containing build output", default="-")
    parser.add_argument("--dry-run", action="store_true", help="Detect issues but don't auto-fix")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    # Read build output
    if args.input == "-":
        build_output = sys.stdin.read()
    else:
        with open(args.input, 'r') as f:
            build_output = f.read()
    
    # Initialize detector
    detector = ClangTidyDetector(config_path=args.config)
    
    # Detect issues
    detection_result = detector.detect_issues_from_build_output(build_output)
    
    # Output results
    if args.json:
        result_data = {
            "issues_found": len(detection_result.issues_found),
            "total_warnings": detection_result.total_warnings,
            "total_errors": detection_result.total_errors,
            "affected_files": detection_result.affected_files,
            "should_auto_fix": detection_result.should_auto_fix
        }
        print(json.dumps(result_data, indent=2))
        return
    
    # Pretty print results
    print(f"📊 Clang-Tidy Detection Results:")
    print(f"  Issues found: {len(detection_result.issues_found)}")
    print(f"  Warnings: {detection_result.total_warnings}")
    print(f"  Errors: {detection_result.total_errors}")
    print(f"  Affected files: {len(detection_result.affected_files)}")
    print(f"  Auto-fix recommended: {'Yes' if detection_result.should_auto_fix else 'No'}")
    
    if detection_result.issues_found:
        print("\n🔍 Sample issues:")
        for issue in detection_result.issues_found[:3]:
            print(f"  {issue.file_path}:{issue.line_number} [{issue.check_name}] {issue.message}")
        
        if len(detection_result.issues_found) > 3:
            print(f"  ... and {len(detection_result.issues_found) - 3} more issues")
    
    # Auto-fix if recommended and not dry-run
    if detection_result.should_auto_fix and not args.dry_run:
        fix_result = detector.invoke_clang_tidy_fixer(detection_result)
        print(f"\n✅ Auto-fix completed: {fix_result.get('success', False)}")
    elif detection_result.should_auto_fix:
        print("\n💡 Auto-fix would be triggered (use without --dry-run to execute)")

if __name__ == "__main__":
    main()