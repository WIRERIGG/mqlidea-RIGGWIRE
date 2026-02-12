"""Error pattern recognition and classification for build failures."""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging


class ErrorCategory(str, Enum):
    """Categories of build errors."""
    COMPILATION = "compilation"
    LINKING = "linking"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    TOOLCHAIN = "toolchain"
    ENVIRONMENT = "environment"
    PERMISSION = "permission"
    DISK_SPACE = "disk_space"
    NETWORK = "network"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    TEMPLATE = "template"
    PREPROCESSOR = "preprocessor"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Severity levels for build errors."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ErrorPattern:
    """Definition of an error pattern for recognition."""
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    patterns: List[str]  # Regex patterns
    description: str
    common_causes: List[str]
    suggested_fixes: List[str]
    confidence_factors: List[str]  # Additional text that increases confidence


@dataclass
class ErrorMatch:
    """Result of matching an error against patterns."""
    pattern_name: str
    category: ErrorCategory
    severity: ErrorSeverity
    confidence_score: float
    matched_text: str
    description: str
    common_causes: List[str]
    suggested_fixes: List[str]
    context: Dict[str, Any]


class ErrorPatternMatcher:
    """Advanced error pattern matching for build failures."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> List[ErrorPattern]:
        """Initialize comprehensive error pattern database."""
        patterns = []
        
        # ====================================================================
        # C++ Compilation Errors
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="missing_include",
            category=ErrorCategory.COMPILATION,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"fatal error: ['\"]([^'\"]+)['\"]:\s*No such file or directory",
                r"error: ['\"]([^'\"]+)['\"]:\s*No such file or directory",
                r"Cannot open include file: ['\"]([^'\"]+)['\"]"
            ],
            description="Missing header file or include path",
            common_causes=[
                "Header file not installed",
                "Incorrect include path",
                "Missing dependency",
                "Case sensitivity issue on Linux"
            ],
            suggested_fixes=[
                "Install missing development package",
                "Add include directory to build configuration",
                "Check header file spelling and case",
                "Verify dependency is properly configured"
            ],
            confidence_factors=["#include", "header", "include"]
        ))
        
        patterns.append(ErrorPattern(
            name="undefined_reference",
            category=ErrorCategory.LINKING,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"undefined reference to [`']([^'`]+)[`']",
                r"unresolved external symbol ([^\s]+)",
                r"ld: symbol\(s\) not found for architecture"
            ],
            description="Undefined symbol during linking",
            common_causes=[
                "Missing library",
                "Incorrect library order",
                "Library not linked",
                "Missing object file",
                "Name mangling mismatch"
            ],
            suggested_fixes=[
                "Link required library (-l flag)",
                "Add library directory (-L flag)",
                "Check library dependencies order",
                "Verify all object files are included",
                "Check C++ vs C linkage (extern \"C\")"
            ],
            confidence_factors=["link", "ld:", "collect2"]
        ))
        
        patterns.append(ErrorPattern(
            name="template_error",
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.MEDIUM,
            patterns=[
                r"error: template argument [^\n]+",
                r"error: no matching function for call to [^\n]+<[^>]*>",
                r"error: incomplete type ['\"]([^'\"]+<[^>]*>)['\"]",
                r"error: template instantiation depth exceeds maximum"
            ],
            description="Template compilation error",
            common_causes=[
                "Incorrect template arguments",
                "Missing template specialization",
                "Circular template dependency",
                "SFINAE error",
                "Template recursion limit exceeded"
            ],
            suggested_fixes=[
                "Check template parameter types",
                "Provide explicit template specialization",
                "Review template constraints",
                "Use concepts (C++20) for better errors",
                "Increase template depth limit"
            ],
            confidence_factors=["template", "instantiation", "SFINAE"]
        ))
        
        patterns.append(ErrorPattern(
            name="syntax_error",
            category=ErrorCategory.SYNTAX,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"error: expected ['\"]([^'\"]+)['\"] before",
                r"error: expected ['\"]([^'\"]+)['\"] at end of input",
                r"syntax error before ['\"]([^'\"]+)['\"]",
                r"error: stray ['\"]([^'\"]+)['\"] in program"
            ],
            description="C++ syntax error",
            common_causes=[
                "Missing semicolon",
                "Mismatched brackets/braces",
                "Invalid character in source",
                "Incorrect use of keywords",
                "Macro expansion issue"
            ],
            suggested_fixes=[
                "Check for missing semicolons",
                "Balance all brackets and braces",
                "Remove invalid characters",
                "Review macro definitions",
                "Use IDE syntax highlighting"
            ],
            confidence_factors=["syntax", "expected", "before"]
        ))
        
        # ====================================================================
        # Build System Errors
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="cmake_config_error",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"CMake Error at ([^:]+):(\d+)",
                r"CMake Error: (.+)",
                r"Could not find a package configuration file provided by ['\"]([^'\"]+)['\"]"
            ],
            description="CMake configuration error",
            common_causes=[
                "Missing CMake package",
                "Incorrect CMakeLists.txt syntax",
                "Missing dependency",
                "Wrong CMake version",
                "Path configuration error"
            ],
            suggested_fixes=[
                "Install missing CMake package",
                "Check CMakeLists.txt syntax",
                "Set CMAKE_PREFIX_PATH",
                "Update CMake version",
                "Verify package installation"
            ],
            confidence_factors=["CMake", "CMakeLists.txt", "find_package"]
        ))
        
        patterns.append(ErrorPattern(
            name="make_error",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"make: \*\*\* No rule to make target ['\"]([^'\"]+)['\"]",
                r"make: \*\*\* \[([^\]]+)\] Error (\d+)",
                r"make: \*\*\* (.+) Stop\."
            ],
            description="Make build error",
            common_causes=[
                "Missing makefile target",
                "Incorrect dependency specification",
                "Command execution failed",
                "Missing source file",
                "Circular dependency"
            ],
            suggested_fixes=[
                "Check makefile targets",
                "Verify file paths in makefile",
                "Review dependency chain",
                "Ensure all source files exist",
                "Fix circular dependencies"
            ],
            confidence_factors=["make", "Makefile", "target"]
        ))
        
        # ====================================================================
        # Dependency and Library Errors
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="pkg_config_error",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"Package ([^\s]+) was not found in the pkg-config search path",
                r"No package ['\"]([^'\"]+)['\"] found",
                r"pkg-config: command not found"
            ],
            description="pkg-config dependency error",
            common_causes=[
                "Missing development package",
                "Package not installed",
                "pkg-config not installed",
                "PKG_CONFIG_PATH not set"
            ],
            suggested_fixes=[
                "Install development package (e.g., libX-dev)",
                "Install pkg-config tool",
                "Set PKG_CONFIG_PATH environment variable",
                "Use package manager to find package name"
            ],
            confidence_factors=["pkg-config", "development", ".pc"]
        ))
        
        patterns.append(ErrorPattern(
            name="library_not_found",
            category=ErrorCategory.LINKING,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"ld: cannot find -l([^\s]+)",
                r"ld: library not found for -l([^\s]+)",
                r"/usr/bin/ld: cannot find -l([^\s]+)"
            ],
            description="Library not found during linking",
            common_causes=[
                "Library not installed",
                "Library in non-standard location",
                "Incorrect library name",
                "Missing symbolic link"
            ],
            suggested_fixes=[
                "Install library development package",
                "Add library path with -L flag",
                "Check correct library name",
                "Create symbolic link if needed",
                "Use ldconfig to update library cache"
            ],
            confidence_factors=["library", "link", "-l"]
        ))
        
        # ====================================================================
        # Environment and System Errors
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="compiler_not_found",
            category=ErrorCategory.TOOLCHAIN,
            severity=ErrorSeverity.CRITICAL,
            patterns=[
                r"([^\s]+): command not found",
                r"No such file or directory.*gcc|g\+\+|clang|clang\+\+",
                r"The C compiler ['\"]([^'\"]+)['\"] is not able to compile"
            ],
            description="Compiler or build tool not found",
            common_causes=[
                "Compiler not installed",
                "Compiler not in PATH",
                "Wrong compiler specified",
                "Missing build-essential package"
            ],
            suggested_fixes=[
                "Install compiler (gcc, clang, etc.)",
                "Install build-essential package",
                "Add compiler to PATH",
                "Specify correct compiler in build config",
                "Set CC and CXX environment variables"
            ],
            confidence_factors=["compiler", "build-essential", "toolchain"]
        ))
        
        patterns.append(ErrorPattern(
            name="permission_denied",
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            patterns=[
                r"Permission denied.*",
                r"cannot create regular file.*Permission denied",
                r"mkdir: cannot create directory.*Permission denied"
            ],
            description="Insufficient permissions for build operation",
            common_causes=[
                "No write permission in build directory",
                "No execute permission",
                "SELinux/AppArmor restriction",
                "Directory owned by different user"
            ],
            suggested_fixes=[
                "Change directory permissions (chmod)",
                "Change directory ownership (chown)",
                "Run build in writable directory",
                "Check SELinux/AppArmor policies",
                "Use sudo if appropriate (not recommended for builds)"
            ],
            confidence_factors=["permission", "chmod", "chown"]
        ))
        
        patterns.append(ErrorPattern(
            name="disk_space_full",
            category=ErrorCategory.DISK_SPACE,
            severity=ErrorSeverity.CRITICAL,
            patterns=[
                r"No space left on device",
                r"write error: No space left on device",
                r"cannot create temp file.*No space left on device"
            ],
            description="Insufficient disk space for build",
            common_causes=[
                "Build directory full",
                "/tmp directory full",
                "Disk quota exceeded",
                "Very large object files"
            ],
            suggested_fixes=[
                "Clean build directory",
                "Remove temporary files",
                "Free up disk space",
                "Use different build directory",
                "Increase disk quota if applicable"
            ],
            confidence_factors=["disk", "space", "quota"]
        ))
        
        # ====================================================================
        # Network and Download Errors
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="download_failed",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            patterns=[
                r"Failed to download ([^\s]+)",
                r"Could not resolve host: ([^\s]+)",
                r"Connection timed out.*download",
                r"SSL certificate problem"
            ],
            description="Failed to download dependency or resource",
            common_causes=[
                "Network connectivity issue",
                "DNS resolution failure",
                "SSL certificate issue",
                "Proxy configuration",
                "Firewall blocking connection"
            ],
            suggested_fixes=[
                "Check internet connection",
                "Verify DNS settings",
                "Update CA certificates",
                "Configure proxy settings",
                "Check firewall rules"
            ],
            confidence_factors=["download", "network", "SSL", "certificate"]
        ))
        
        # ====================================================================
        # Warning Patterns
        # ====================================================================
        
        patterns.append(ErrorPattern(
            name="deprecated_warning",
            category=ErrorCategory.SEMANTIC,
            severity=ErrorSeverity.WARNING,
            patterns=[
                r"warning: ['\"]([^'\"]+)['\"] is deprecated",
                r"warning: deprecated conversion from",
                r"DeprecationWarning: ([^\n]+)"
            ],
            description="Use of deprecated features",
            common_causes=[
                "Old API usage",
                "Deprecated compiler feature",
                "Legacy code patterns",
                "Outdated library version"
            ],
            suggested_fixes=[
                "Update to modern API",
                "Check library documentation",
                "Use newer language features",
                "Update deprecated code patterns"
            ],
            confidence_factors=["deprecated", "legacy", "old"]
        ))
        
        return patterns
    
    def classify_error(self, error_text: str, context: Dict[str, Any] = None) -> List[ErrorMatch]:
        """Classify build error text against known patterns."""
        error_text = error_text.strip()
        if not error_text:
            return []
        
        matches = []
        context = context or {}
        
        for pattern in self.patterns:
            for regex_pattern in pattern.patterns:
                try:
                    regex_match = re.search(regex_pattern, error_text, re.IGNORECASE | re.MULTILINE)
                    if regex_match:
                        # Calculate confidence score
                        confidence = self._calculate_confidence(
                            pattern, regex_match, error_text, context
                        )
                        
                        match = ErrorMatch(
                            pattern_name=pattern.name,
                            category=pattern.category,
                            severity=pattern.severity,
                            confidence_score=confidence,
                            matched_text=regex_match.group(0),
                            description=pattern.description,
                            common_causes=pattern.common_causes,
                            suggested_fixes=pattern.suggested_fixes,
                            context=context
                        )
                        
                        matches.append(match)
                        break  # Only match first pattern for each error pattern
                        
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern in {pattern.name}: {e}")
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return matches
    
    def _calculate_confidence(
        self, 
        pattern: ErrorPattern, 
        regex_match: re.Match, 
        full_text: str, 
        context: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for a pattern match."""
        base_confidence = 0.7  # Base confidence for regex match
        
        # Boost confidence based on confidence factors
        confidence_boost = 0.0
        for factor in pattern.confidence_factors:
            if factor.lower() in full_text.lower():
                confidence_boost += 0.05
        
        # Additional context-based confidence adjustments
        if context:
            # Build tool context
            build_tool = context.get('build_tool', '').lower()
            if 'cmake' in build_tool and pattern.category == ErrorCategory.CONFIGURATION:
                confidence_boost += 0.1
            elif 'make' in build_tool and 'make' in pattern.name:
                confidence_boost += 0.1
            
            # File extension context
            source_file = context.get('source_file', '')
            if source_file:
                if source_file.endswith(('.cpp', '.cxx', '.cc')) and pattern.category == ErrorCategory.COMPILATION:
                    confidence_boost += 0.05
                elif source_file.endswith('.h') and 'include' in pattern.name:
                    confidence_boost += 0.1
        
        # Length and specificity of match
        match_length = len(regex_match.group(0))
        if match_length > 50:  # Longer, more specific matches are more confident
            confidence_boost += 0.05
        
        return min(1.0, base_confidence + confidence_boost)
    
    def get_best_match(self, error_text: str, context: Dict[str, Any] = None) -> Optional[ErrorMatch]:
        """Get the best (highest confidence) match for error text."""
        matches = self.classify_error(error_text, context)
        return matches[0] if matches else None
    
    def analyze_build_log(self, log_text: str) -> Dict[str, Any]:
        """Analyze entire build log and categorize all errors."""
        lines = log_text.split('\n')
        
        analysis = {
            'total_lines': len(lines),
            'error_lines': [],
            'matches': [],
            'categories': {},
            'severity_counts': {},
            'summary': {
                'total_errors': 0,
                'critical_errors': 0,
                'high_errors': 0,
                'warnings': 0
            }
        }
        
        # Process each line that looks like an error
        error_indicators = ['error:', 'fatal:', 'Error', 'FAILED:', 'make: ***']
        warning_indicators = ['warning:', 'Warning:', 'deprecated']
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains error or warning indicators
            is_error_line = any(indicator in line for indicator in error_indicators)
            is_warning_line = any(indicator in line for indicator in warning_indicators)
            
            if is_error_line or is_warning_line:
                analysis['error_lines'].append({
                    'line_number': line_num,
                    'text': line,
                    'type': 'error' if is_error_line else 'warning'
                })
                
                # Try to classify this error
                context = {
                    'line_number': line_num,
                    'build_tool': self._detect_build_tool_from_line(line)
                }
                
                matches = self.classify_error(line, context)
                if matches:
                    best_match = matches[0]
                    analysis['matches'].append({
                        'line_number': line_num,
                        'line_text': line,
                        'match': best_match
                    })
                    
                    # Update category counts
                    category = best_match.category.value
                    analysis['categories'][category] = analysis['categories'].get(category, 0) + 1
                    
                    # Update severity counts
                    severity = best_match.severity.value
                    analysis['severity_counts'][severity] = analysis['severity_counts'].get(severity, 0) + 1
                    
                    # Update summary
                    analysis['summary']['total_errors'] += 1
                    if severity == 'critical':
                        analysis['summary']['critical_errors'] += 1
                    elif severity == 'high':
                        analysis['summary']['high_errors'] += 1
                    elif severity == 'warning':
                        analysis['summary']['warnings'] += 1
        
        return analysis
    
    def _detect_build_tool_from_line(self, line: str) -> str:
        """Detect build tool from error line."""
        line_lower = line.lower()
        
        if 'cmake' in line_lower:
            return 'cmake'
        elif 'make[' in line_lower or 'make:' in line_lower:
            return 'make'  
        elif 'ninja:' in line_lower:
            return 'ninja'
        elif 'gcc' in line_lower or 'g++' in line_lower:
            return 'gcc'
        elif 'clang' in line_lower:
            return 'clang'
        
        return 'unknown'
    
    def get_resolution_suggestions(self, matches: List[ErrorMatch]) -> List[str]:
        """Get prioritized resolution suggestions based on error matches."""
        if not matches:
            return ["No specific suggestions - check build log for details"]
        
        # Group suggestions by category and priority
        suggestions = []
        seen_fixes = set()
        
        # Prioritize by severity (critical, high, medium, low, warning)
        severity_order = ['critical', 'high', 'medium', 'low', 'warning']
        
        for severity in severity_order:
            for match in matches:
                if match.severity.value == severity:
                    for fix in match.suggested_fixes:
                        if fix not in seen_fixes:
                            suggestions.append(f"[{match.category.value.upper()}] {fix}")
                            seen_fixes.add(fix)
        
        return suggestions[:10]  # Limit to top 10 suggestions


def classify_build_error(error_text: str, context: Dict[str, Any] = None) -> Optional[ErrorMatch]:
    """Utility function to classify a single build error."""
    matcher = ErrorPatternMatcher()
    return matcher.get_best_match(error_text, context)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    matcher = ErrorPatternMatcher(logger)
    
    # Test error messages
    test_errors = [
        "fatal error: 'iostream': No such file or directory",
        "undefined reference to `std::cout'",
        "CMake Error: Could not find a package configuration file provided by \"Qt5\"",
        "make: *** No rule to make target 'all'",
        "/usr/bin/ld: cannot find -lboost_system",
        "Permission denied: cannot create directory 'build'",
        "No space left on device",
        "error: expected ';' before '}' token",
        "warning: 'auto_ptr' is deprecated"
    ]
    
    print("=== Error Classification Test ===")
    
    for i, error in enumerate(test_errors, 1):
        print(f"\nTest {i}: {error}")
        matches = matcher.classify_error(error)
        
        if matches:
            best_match = matches[0]
            print(f"  Category: {best_match.category.value}")
            print(f"  Severity: {best_match.severity.value}")
            print(f"  Confidence: {best_match.confidence_score:.2f}")
            print(f"  Description: {best_match.description}")
            print(f"  Top fix: {best_match.suggested_fixes[0] if best_match.suggested_fixes else 'No suggestions'}")
        else:
            print("  No matches found")
    
    # Test full build log analysis
    sample_log = """
make[2]: Entering directory '/project/build'
/usr/bin/c++ -o main main.cpp
fatal error: 'boost/algorithm/string.hpp': No such file or directory
#include <boost/algorithm/string.hpp>
         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~
compilation terminated.
make[2]: *** [CMakeFiles/main.dir/build.make:63: CMakeFiles/main.dir/main.cpp.o] Error 1
make[1]: *** [CMakeFiles/Makefile2:76: CMakeFiles/main.dir/all] Error 2
make: *** [Makefile:84: all] Error 2
"""
    
    print(f"\n=== Build Log Analysis ===")
    analysis = matcher.analyze_build_log(sample_log)
    print(f"Total errors found: {analysis['summary']['total_errors']}")
    print(f"Categories: {analysis['categories']}")
    print(f"Severities: {analysis['severity_counts']}")
    
    # Get resolution suggestions
    matches = [match['match'] for match in analysis['matches']]
    suggestions = matcher.get_resolution_suggestions(matches)
    print(f"\nResolution suggestions:")
    for suggestion in suggestions:
        print(f"  • {suggestion}")