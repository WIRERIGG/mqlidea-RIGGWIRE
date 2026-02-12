"""
Valgrind Pydantic Tool - Comprehensive C++ Safety Analysis with AI Integration.

A self-contained, Pydantic-based Python tool that integrates directly with ALL Valgrind 
features for dynamic analysis of C++ programs, with AI-powered issue analysis and 
self-improvement capabilities.

Key Features:
- Complete support for ALL 10 Valgrind tools (Memcheck, Cachegrind, Callgrind, 
  Helgrind, DRD, Massif, DHAT, Lackey, Nulgrind, BBV)
- Pydantic models for robust configuration validation and output parsing
- AI integration for automated issue analysis and fix suggestions
- Self-improvement through learning databases
- Callable interface via __call__ method for easy integration
- Comprehensive parsing of both text and XML Valgrind outputs
- Performance optimization modes (quick/thorough/profile)
- Enterprise-grade error handling and reporting

Usage:
    from valgrind_pydantic_tool import ValgrindAnalyzer, ValgrindConfig, ValgrindTool
    
    # Quick analysis
    analyzer = ValgrindAnalyzer("/path/to/project")
    result = analyzer("/path/to/binary")
    
    # Comprehensive analysis with AI
    config = ValgrindConfig(tool=ValgrindTool.MEMCHECK, track_origins=True)
    result = analyzer("/path/to/binary", config=config, ai_analyze=True)
    
    # Multi-tool analysis
    report = analyzer.run_comprehensive_analysis("/path/to/binary", ai_analyze=True)

Mission: Make unsafe C++ impossible by combining Valgrind's comprehensive analysis 
with AI-powered remediation.
"""

from .valgrind_tool import ValgrindAnalyzer, analyze_binary, comprehensive_analysis
from .models import (
    ValgrindConfig, ValgrindTool, ValgrindResult, ValgrindState, ValgrindError,
    IssueCategory, IssueSeverity, ValgrindIssue, ValgrindMetrics, AnalysisMode,
    StackFrame, LearningDatabase
)
from .ai_integration import AIAnalyzer, generate_ai_prompt, call_llm
from .tools import (
    ValgrindRunner, LearningSystem, check_valgrind_installed, 
    get_valgrind_version, validate_tool_availability
)
from .parsers import (
    parse_text_output, parse_xml_output, TextParser, XMLParser
)

__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Comprehensive Valgrind Integration Tool with AI-Powered Analysis"

# Main exports
__all__ = [
    # Core analyzer
    'ValgrindAnalyzer',
    'analyze_binary', 
    'comprehensive_analysis',
    
    # Models
    'ValgrindConfig',
    'ValgrindTool', 
    'ValgrindResult',
    'ValgrindState',
    'ValgrindError',
    'IssueCategory',
    'IssueSeverity',
    'ValgrindIssue',
    'ValgrindMetrics',
    'AnalysisMode',
    'StackFrame',
    'LearningDatabase',
    
    # AI Integration
    'AIAnalyzer',
    'generate_ai_prompt',
    'call_llm',
    
    # Tools
    'ValgrindRunner',
    'LearningSystem',
    'check_valgrind_installed',
    'get_valgrind_version',
    'validate_tool_availability',
    
    # Parsers
    'parse_text_output',
    'parse_xml_output', 
    'TextParser',
    'XMLParser'
]

# Convenience constants
DEFAULT_CONFIG_PATH = "valgrind_config.json"
DEFAULT_LEARNING_DB = "valgrind_learning.json"

# Supported tool matrix
SUPPORTED_TOOLS = {
    ValgrindTool.MEMCHECK: "Memory error detection and leak checking",
    ValgrindTool.CACHEGRIND: "Cache profiling and performance analysis", 
    ValgrindTool.CALLGRIND: "Call-graph profiling and optimization",
    ValgrindTool.HELGRIND: "Thread race detection and synchronization analysis",
    ValgrindTool.DRD: "Alternative thread error detection",
    ValgrindTool.MASSIF: "Heap profiling and memory usage analysis",
    ValgrindTool.DHAT: "Dynamic heap analysis tool",
    ValgrindTool.LACKEY: "Basic example tool for development",
    ValgrindTool.NULGRIND: "Null tool for performance baseline",
    ValgrindTool.BBV: "Experimental basic block vector tool"
}

def print_tool_info():
    """Print information about supported Valgrind tools."""
    print("Valgrind Pydantic Tool - Supported Analysis Tools:")
    print("=" * 60)
    
    for tool, description in SUPPORTED_TOOLS.items():
        print(f"{tool.value:12} - {description}")
    
    print(f"\nTotal tools supported: {len(SUPPORTED_TOOLS)}")
    print("All tools support both text and XML output parsing.")


def quick_demo(binary_path: str):
    """
    Quick demonstration of the Valgrind analyzer.
    
    Args:
        binary_path: Path to binary to analyze
    """
    print("Valgrind Pydantic Tool - Quick Demo")
    print("=" * 40)
    
    try:
        # Initialize analyzer
        analyzer = ValgrindAnalyzer(".")
        
        # Quick analysis
        print(f"Analyzing: {binary_path}")
        result = analyzer(binary_path)
        
        print(f"Analysis completed in {result.execution_time:.2f}s")
        print(f"Issues found: {len(result.issues)}")
        print(f"Safety score: {result.metrics.get_safety_score()}/100")
        
        if result.issues:
            print("\nTop issues:")
            for i, issue in enumerate(result.issues[:3], 1):
                print(f"{i}. {issue.category.value}: {issue.description}")
        
        return result
        
    except Exception as e:
        print(f"Demo failed: {e}")
        return None