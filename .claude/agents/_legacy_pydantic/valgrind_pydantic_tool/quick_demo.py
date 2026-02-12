#!/usr/bin/env python3
"""
Quick demonstration of the ValgrindAnalyzer tool.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from valgrind_tool import ValgrindAnalyzer
from models import ValgrindConfig, ValgrindTool, AnalysisMode

def main():
    print("🚀 ValgrindAnalyzer Quick Demo")
    print("=" * 40)
    
    project_root = "/IdeaProjects/wire_ground"
    binary_path = f"{project_root}/cmake-build-debug/wire_ground_tests"
    
    print(f"Target: {binary_path}")
    
    if not Path(binary_path).exists():
        print(f"❌ Binary not found: {binary_path}")
        return 1
    
    try:
        # Initialize analyzer
        analyzer = ValgrindAnalyzer(project_root)
        print("✅ Analyzer initialized")
        
        # Quick Memcheck analysis
        print("\n📋 Running Memcheck analysis...")
        config = ValgrindConfig(
            tool=ValgrindTool.MEMCHECK,
            leak_check="summary",  # Quick mode
            track_origins=False,   # Faster
            timeout=120           # 2 minutes max
        )
        
        result = analyzer(binary_path, config, ai_analyze=False, mode=AnalysisMode.QUICK)
        
        print(f"✅ Analysis completed in {result.execution_time:.2f}s")
        print(f"Tool: {result.tool_used.value}")
        print(f"Issues: {len(result.issues)}")
        print(f"Safety Score: {result.metrics.get_safety_score()}/100")
        
        if result.issues:
            print("\n🔍 Issues found:")
            for i, issue in enumerate(result.issues[:5], 1):
                print(f"  {i}. {issue.category.value}: {issue.description}")
                if issue.file_path:
                    print(f"     Location: {issue.file_path}:{issue.line_number}")
        else:
            print("🌟 No issues detected!")
        
        # Memory metrics
        print(f"\n📊 Memory Metrics:")
        print(f"  Bytes leaked: {result.metrics.bytes_leaked}")
        print(f"  Definitely lost: {result.metrics.definitely_lost}")
        print(f"  Possibly lost: {result.metrics.possibly_lost}")
        print(f"  Still reachable: {result.metrics.still_reachable}")
        
        # Show command used
        print(f"\n🔧 Command executed:")
        print(f"  {' '.join(result.command_used)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())