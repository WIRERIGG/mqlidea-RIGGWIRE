#!/usr/bin/env python3
"""
Comprehensive demonstration of the ValgrindAnalyzer tool.
Runs ALL Valgrind tools on the safe_test.cpp binary and generates complete report.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from valgrind_tool import ValgrindAnalyzer, comprehensive_analysis
from models import ValgrindTool, ValgrindConfig, AnalysisMode


def main():
    """Run comprehensive Valgrind analysis demonstration."""
    print("🚀 Valgrind Pydantic Tool - Comprehensive Analysis Demo")
    print("=" * 70)
    
    # Configuration
    project_root = "/IdeaProjects/wire_ground"
    binary_path = f"{project_root}/cmake-build-debug/wire_ground_tests"
    
    print(f"Project Root: {project_root}")
    print(f"Target Binary: {binary_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Validate binary exists
    if not Path(binary_path).exists():
        print(f"❌ Error: Binary not found at {binary_path}")
        print("Please build the project first:")
        print("  cd /IdeaProjects/wire_ground")
        print("  cmake --build cmake-build-debug --target wire_ground_tests")
        return 1
    
    try:
        # Initialize analyzer
        print("🔧 Initializing ValgrindAnalyzer...")
        analyzer = ValgrindAnalyzer(
            project_root=project_root,
            config_path=f"{Path(__file__).parent}/valgrind_config.json"
        )
        print("✅ Analyzer initialized successfully")
        print()
        
        # Check Valgrind installation
        print("🔍 Verifying Valgrind installation...")
        runner_info = analyzer.runner.check_valgrind_installation()
        print(f"✅ Valgrind found: {runner_info['version']}")
        print(f"Available tools: {', '.join(runner_info['available_tools'])}")
        print()
        
        # Phase 1: Quick analysis with Memcheck
        print("📋 Phase 1: Quick Memcheck Analysis")
        print("-" * 40)
        quick_result = analyzer(
            binary_path=binary_path,
            config=ValgrindConfig(tool=ValgrindTool.MEMCHECK),
            ai_analyze=False,
            mode=AnalysisMode.QUICK
        )
        
        print(f"✅ Quick analysis completed in {quick_result.execution_time:.2f}s")
        print(f"Issues found: {len(quick_result.issues)}")
        print(f"Safety score: {quick_result.metrics.get_safety_score()}/100")
        
        if quick_result.issues:
            print("\nTop issues:")
            for i, issue in enumerate(quick_result.issues[:3], 1):
                print(f"  {i}. {issue.category.value}: {issue.description}")
        print()
        
        # Phase 2: Individual tool demonstration
        print("🛠️  Phase 2: Individual Tool Analysis")
        print("-" * 40)
        
        core_tools = [
            (ValgrindTool.MEMCHECK, "Memory safety analysis"),
            (ValgrindTool.HELGRIND, "Thread race detection"), 
            (ValgrindTool.CACHEGRIND, "Cache performance profiling"),
            (ValgrindTool.CALLGRIND, "Function call profiling")
        ]
        
        individual_results = {}
        
        for tool, description in core_tools:
            print(f"Running {tool.value} - {description}...")
            try:
                config = ValgrindConfig(tool=tool, timeout=300)  # 5 minute timeout
                result = analyzer(binary_path, config, ai_analyze=False)
                
                individual_results[tool] = result
                print(f"✅ {tool.value}: {len(result.issues)} issues, {result.execution_time:.2f}s")
                
            except Exception as e:
                print(f"❌ {tool.value} failed: {e}")
                individual_results[tool] = None
        
        print()
        
        # Phase 3: Multi-tool parallel analysis
        print("⚡ Phase 3: Multi-Tool Analysis")
        print("-" * 40)
        
        multi_tools = [ValgrindTool.MEMCHECK, ValgrindTool.HELGRIND, ValgrindTool.DRD]
        print(f"Running parallel analysis with: {', '.join(t.value for t in multi_tools)}")
        
        multi_results = analyzer.run_multi_tool_analysis(
            binary_path=binary_path,
            tools=multi_tools,
            ai_analyze=False,
            parallel=False  # Sequential for stability
        )
        
        print(f"✅ Multi-tool analysis completed")
        for tool, result in multi_results.items():
            print(f"  {tool.value}: {len(result.issues)} issues, {result.execution_time:.2f}s")
        print()
        
        # Phase 4: Comprehensive analysis with all tools
        print("🎯 Phase 4: Comprehensive Analysis (All Tools)")
        print("-" * 50)
        
        print("Running comprehensive analysis with ALL supported tools...")
        print("This may take several minutes...")
        
        comprehensive_report = analyzer.run_comprehensive_analysis(
            binary_path=binary_path,
            ai_analyze=False  # Disable AI for demo due to API requirements
        )
        
        print("✅ Comprehensive analysis completed!")
        print()
        
        # Phase 5: Results summary
        print("📊 Phase 5: Results Summary")
        print("-" * 30)
        
        summary = comprehensive_report["summary"]
        print(f"Total tools run: {summary['total_tools']}")
        print(f"Successful runs: {summary['successful_runs']}")
        print(f"Total execution time: {summary['total_execution_time']:.2f}s")
        print(f"Total issues found: {summary['total_issues']}")
        print(f"Overall safety score: {summary['safety_score']}/100")
        print()
        
        # Display tool-by-tool results
        print("Tool-by-tool results:")
        for tool, result_info in comprehensive_report["results_by_tool"].items():
            status = "✅" if result_info["success"] else "❌"
            print(f"  {status} {tool:12} - {result_info['issues']:3} issues, "
                  f"{result_info['execution_time']:6.2f}s, score: {result_info['safety_score']:5.1f}")
        print()
        
        # Show insights
        if "insights" in comprehensive_report:
            insights = comprehensive_report["insights"]
            print("🔍 Key Insights:")
            
            if insights.get("critical_findings"):
                print("  Critical findings:")
                for finding in insights["critical_findings"]:
                    print(f"    - {finding}")
            
            if insights.get("most_effective_tools"):
                print(f"  Most effective tools: {', '.join(insights['most_effective_tools'])}")
            
            perf = insights.get("performance_impact", {})
            if "overhead_factor" in perf:
                print(f"  Performance overhead range: {perf['overhead_factor']:.1f}x")
        
        print()
        
        # Phase 6: Generate reports
        print("📝 Phase 6: Report Generation")
        print("-" * 30)
        
        # Save comprehensive report
        report_file = Path("comprehensive_valgrind_report.json")
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        print(f"✅ Comprehensive report saved to: {report_file}")
        
        # Save individual tool results
        results_dir = Path("valgrind_results")
        results_dir.mkdir(exist_ok=True)
        
        for tool, result in multi_results.items():
            result_file = results_dir / f"{tool.value}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
        
        print(f"✅ Individual results saved to: {results_dir}/")
        
        # Generate markdown report
        markdown_report = generate_markdown_report(comprehensive_report, quick_result)
        md_file = Path("VALGRIND_ANALYSIS_REPORT.md")
        with open(md_file, 'w') as f:
            f.write(markdown_report)
        print(f"✅ Markdown report saved to: {md_file}")
        print()
        
        # Final summary
        print("🎉 Analysis Complete!")
        print("=" * 30)
        print(f"✅ {summary['successful_runs']}/{summary['total_tools']} tools completed successfully")
        print(f"⚡ Total execution time: {summary['total_execution_time']:.2f} seconds")
        print(f"🛡️  Overall safety score: {summary['safety_score']}/100")
        
        if summary['total_issues'] == 0:
            print("🌟 No issues found - excellent code safety!")
        else:
            print(f"⚠️  {summary['total_issues']} issues identified - review recommendations")
        
        print()
        print("Generated files:")
        print(f"  📊 {report_file}")
        print(f"  📁 {results_dir}/")
        print(f"  📝 {md_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def generate_markdown_report(comprehensive_report, quick_result):
    """Generate markdown analysis report."""
    
    report = f"""# Valgrind Comprehensive Analysis Report

**Generated**: {datetime.now().isoformat()}
**Tool**: ValgrindAnalyzer v1.0.0

## Executive Summary

- **Total Tools**: {comprehensive_report['summary']['total_tools']}
- **Successful Runs**: {comprehensive_report['summary']['successful_runs']}
- **Total Issues**: {comprehensive_report['summary']['total_issues']}
- **Safety Score**: {comprehensive_report['summary']['safety_score']}/100
- **Execution Time**: {comprehensive_report['summary']['total_execution_time']:.2f}s

## Tool Results

| Tool | Status | Issues | Time (s) | Safety Score |
|------|--------|--------|----------|--------------|
"""
    
    for tool, result_info in comprehensive_report["results_by_tool"].items():
        status = "✅ Success" if result_info["success"] else "❌ Failed"
        report += f"| {tool} | {status} | {result_info['issues']} | {result_info['execution_time']:.2f} | {result_info['safety_score']:.1f} |\n"
    
    report += "\n## Key Findings\n\n"
    
    if comprehensive_report.get("insights", {}).get("critical_findings"):
        report += "### Critical Issues\n\n"
        for finding in comprehensive_report["insights"]["critical_findings"]:
            report += f"- {finding}\n"
        report += "\n"
    
    if comprehensive_report.get("recommendations"):
        report += "### Recommendations\n\n"
        for i, rec in enumerate(comprehensive_report["recommendations"], 1):
            report += f"{i}. {rec}\n"
        report += "\n"
    
    report += "## Performance Analysis\n\n"
    
    metrics = comprehensive_report.get("aggregated_metrics", {})
    if metrics:
        report += f"- **Memory Leaks**: {metrics.get('bytes_leaked', 0)} bytes\n"
        report += f"- **Race Conditions**: {metrics.get('race_errors', 0)} detected\n"
        report += f"- **Cache Miss Rate**: {metrics.get('d1_miss_rate', 0):.2f}%\n"
    
    report += "\n## Tool Coverage\n\n"
    report += "This analysis utilized the following Valgrind tools:\n\n"
    
    tools_used = comprehensive_report.get("tools_used", [])
    tool_descriptions = {
        "memcheck": "Memory error detection and leak checking",
        "helgrind": "Thread race detection and synchronization analysis", 
        "cachegrind": "Cache profiling and performance analysis",
        "callgrind": "Call-graph profiling and optimization",
        "drd": "Alternative thread error detection",
        "massif": "Heap profiling and memory usage analysis",
        "dhat": "Dynamic heap analysis tool",
        "lackey": "Basic example tool for development",
        "none": "Null tool for performance baseline",
        "exp-bbv": "Experimental basic block vector tool"
    }
    
    for tool in tools_used:
        desc = tool_descriptions.get(tool, "Advanced analysis tool")
        report += f"- **{tool}**: {desc}\n"
    
    report += f"""
## Conclusion

The comprehensive analysis using {len(tools_used)} Valgrind tools has completed with a safety score of **{comprehensive_report['summary']['safety_score']}/100**.

{
"🌟 **Excellent!** No critical issues found. Code demonstrates good safety practices." 
if comprehensive_report['summary']['total_issues'] == 0 
else f"⚠️  **Action Required**: {comprehensive_report['summary']['total_issues']} issues identified that should be addressed."
}

---
*Report generated by ValgrindAnalyzer - Making unsafe C++ impossible*
"""
    
    return report


if __name__ == "__main__":
    sys.exit(main())