#!/usr/bin/env python3
"""
Multi-tool demonstration of the ValgrindAnalyzer.
Shows ALL 10 Valgrind tools in action.
"""

import sys
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from valgrind_tool import ValgrindAnalyzer
from models import ValgrindTool, ValgrindConfig

def main():
    print("🛠️  ValgrindAnalyzer Multi-Tool Demo")
    print("=" * 50)
    
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
        
        # Define all tools with descriptions
        all_tools = [
            (ValgrindTool.MEMCHECK, "Memory error detection and leak checking"),
            (ValgrindTool.CACHEGRIND, "Cache profiling and performance analysis"), 
            (ValgrindTool.CALLGRIND, "Call-graph profiling and optimization"),
            (ValgrindTool.HELGRIND, "Thread race detection and synchronization"),
            (ValgrindTool.DRD, "Alternative thread error detection"),
            (ValgrindTool.MASSIF, "Heap profiling and memory usage analysis"),
            (ValgrindTool.DHAT, "Dynamic heap analysis tool"),
            (ValgrindTool.LACKEY, "Basic example tool for development"),
            (ValgrindTool.NULGRIND, "Null tool for performance baseline"),
            (ValgrindTool.BBV, "Experimental basic block vector tool")
        ]
        
        results = {}
        total_issues = 0
        total_time = 0
        
        print(f"\n🚀 Running analysis with ALL {len(all_tools)} Valgrind tools:")
        print("-" * 70)
        
        for i, (tool, description) in enumerate(all_tools, 1):
            print(f"\n[{i:2}/{len(all_tools)}] {tool.value:12} - {description}")
            print("    " + "-" * 50)
            
            try:
                # Create tool-specific configuration
                config = ValgrindConfig(
                    tool=tool,
                    timeout=180,  # 3 minutes per tool
                    quiet=True    # Reduce noise
                )
                
                # Special configurations for specific tools
                if tool == ValgrindTool.MEMCHECK:
                    config.leak_check = "summary"
                    config.track_origins = False  # Faster
                elif tool == ValgrindTool.CACHEGRIND:
                    config.cache_sim = True
                    config.branch_sim = True
                elif tool == ValgrindTool.MASSIF:
                    config.heap = True
                    config.stacks = False  # Faster
                    config.depth = 10     # Reduce depth for speed
                
                result = analyzer(binary_path, config, ai_analyze=False)
                results[tool] = result
                
                # Print results
                status = "✅" if result.success else "⚠️"
                print(f"    {status} Status: {'Success' if result.success else 'Issues found'}")
                print(f"    ⏱️  Time: {result.execution_time:.2f}s")
                print(f"    🔍 Issues: {len(result.issues)}")
                print(f"    📊 Safety Score: {result.metrics.get_safety_score()}/100")
                
                if result.issues:
                    print(f"    📋 Top issues:")
                    for issue in result.issues[:2]:
                        print(f"      - {issue.category.value}: {issue.description}")
                
                total_issues += len(result.issues)
                total_time += result.execution_time
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[tool] = None
        
        # Summary
        print(f"\n🎉 Multi-Tool Analysis Summary")
        print("=" * 40)
        successful = len([r for r in results.values() if r is not None and r.success])
        print(f"✅ Tools completed: {successful}/{len(all_tools)}")
        print(f"⏱️  Total execution time: {total_time:.2f}s")
        print(f"🔍 Total issues found: {total_issues}")
        print(f"⚡ Average time per tool: {total_time/len([r for r in results.values() if r is not None]):.2f}s")
        
        # Tool effectiveness ranking
        print(f"\n🏆 Tool Effectiveness Ranking:")
        effective_tools = [(tool, result) for tool, result in results.items() 
                          if result is not None]
        effective_tools.sort(key=lambda x: (len(x[1].issues), -x[1].execution_time), reverse=True)
        
        for i, (tool, result) in enumerate(effective_tools[:5], 1):
            print(f"  {i}. {tool.value:12} - {len(result.issues):2} issues, {result.execution_time:5.2f}s")
        
        # Performance analysis
        if results:
            fastest = min(results.values(), key=lambda r: r.execution_time if r else float('inf'))
            slowest = max(results.values(), key=lambda r: r.execution_time if r else 0)
            
            print(f"\n⚡ Performance Analysis:")
            print(f"  Fastest tool: {[k.value for k, v in results.items() if v == fastest][0]} ({fastest.execution_time:.2f}s)")
            print(f"  Slowest tool: {[k.value for k, v in results.items() if v == slowest][0]} ({slowest.execution_time:.2f}s)")
            print(f"  Speed ratio: {slowest.execution_time / fastest.execution_time:.1f}x")
        
        # Save results
        summary_file = "multi_tool_results.json"
        summary_data = {
            "timestamp": results[ValgrindTool.MEMCHECK].timestamp.isoformat() if results.get(ValgrindTool.MEMCHECK) else None,
            "binary_analyzed": binary_path,
            "total_tools": len(all_tools),
            "successful_tools": successful,
            "total_execution_time": total_time,
            "total_issues": total_issues,
            "tool_results": {
                tool.value: {
                    "success": result.success if result else False,
                    "issues": len(result.issues) if result else 0,
                    "execution_time": result.execution_time if result else 0,
                    "safety_score": result.metrics.get_safety_score() if result else 0
                }
                for tool, result in results.items()
            }
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {summary_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())