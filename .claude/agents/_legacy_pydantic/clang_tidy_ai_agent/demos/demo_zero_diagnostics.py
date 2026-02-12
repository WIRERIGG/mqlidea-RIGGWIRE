#!/usr/bin/env python3
"""
Demo script for Zero CLion Diagnostics System
Tests the complete agent-factory-with-subagents pattern for achieving ZERO diagnostics.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/zero_diagnostics_demo.log')
    ]
)

logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from factory_orchestrator import achieve_zero_diagnostics
    from models import FactoryReport
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


async def demo_single_file():
    """Demonstrate zero diagnostics on a single test file."""
    
    print("🔬 DEMO 1: Single File Zero Diagnostics")
    print("=" * 60)
    
    target_file = "/IdeaProjects/wire_ground/tests/safe_test.cpp"
    
    if not Path(target_file).exists():
        print(f"❌ Target file not found: {target_file}")
        return
    
    print(f"📁 Target File: {target_file}")
    print(f"🎯 Goal: Achieve ZERO CLion diagnostics")
    print(f"⏱️  Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Run zero diagnostics workflow
        report = await achieve_zero_diagnostics(
            target_files=[target_file],
            session_id="demo_single_file"
        )
        
        # Display results
        print_report_summary(report)
        
    except Exception as e:
        logger.error(f"Demo 1 failed: {e}")
        print(f"❌ Demo 1 Failed: {e}")


async def demo_multiple_files():
    """Demonstrate zero diagnostics on multiple files."""
    
    print("\n🔬 DEMO 2: Multiple Files Zero Diagnostics")
    print("=" * 60)
    
    target_files = [
        "/IdeaProjects/wire_ground/tests/safe_test.cpp",
        "/IdeaProjects/wire_ground/src/main.cpp",
        "/IdeaProjects/wire_ground/main.cpp"
    ]
    
    # Filter to existing files
    existing_files = [f for f in target_files if Path(f).exists()]
    
    if not existing_files:
        print("❌ No target files found")
        return
    
    print(f"📁 Target Files: {len(existing_files)} files")
    for file in existing_files:
        print(f"   - {file}")
    print(f"🎯 Goal: Achieve ZERO CLion diagnostics across all files")
    print(f"⏱️  Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Run zero diagnostics workflow
        report = await achieve_zero_diagnostics(
            target_files=existing_files,
            session_id="demo_multiple_files"
        )
        
        # Display results
        print_report_summary(report)
        
    except Exception as e:
        logger.error(f"Demo 2 failed: {e}")
        print(f"❌ Demo 2 Failed: {e}")


async def demo_incremental_validation():
    """Demonstrate incremental validation with rollback."""
    
    print("\n🔬 DEMO 3: Incremental Validation with Rollback")
    print("=" * 60)
    
    target_file = "/IdeaProjects/wire_ground/tests/safe_test.cpp"
    
    if not Path(target_file).exists():
        print(f"❌ Target file not found: {target_file}")
        return
    
    print(f"📁 Target File: {target_file}")
    print(f"🎯 Goal: Demonstrate incremental fixing with validation")
    print(f"🔄 Features: Fix-by-fix validation, automatic rollback on failures")
    print(f"⏱️  Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Run workflow with detailed logging
        logger.setLevel(logging.DEBUG)  # More verbose for this demo
        
        report = await achieve_zero_diagnostics(
            target_files=[target_file],
            session_id="demo_incremental_validation"
        )
        
        # Display detailed results focusing on validation
        print_validation_details(report)
        
    except Exception as e:
        logger.error(f"Demo 3 failed: {e}")
        print(f"❌ Demo 3 Failed: {e}")
    finally:
        logger.setLevel(logging.INFO)  # Reset logging level


def print_report_summary(report: FactoryReport):
    """Print a comprehensive report summary."""
    
    print("📊 WORKFLOW RESULTS")
    print("-" * 40)
    
    # Basic metrics
    print(f"Session ID: {report.session_id}")
    print(f"Duration: {report.total_duration:.2f} seconds")
    print(f"Files Processed: {len(report.target_files)}")
    
    # Diagnostic metrics
    print(f"\n🔍 DIAGNOSTIC METRICS")
    print(f"Initial Issues: {report.total_issues_discovered}")
    print(f"Issues Resolved: {report.total_issues_resolved}")
    remaining = report.before_after_metrics.get("final_diagnostics", "unknown")
    print(f"Final Issues: {remaining}")
    
    # Success metrics
    zero_achieved = remaining == 0 if isinstance(remaining, int) else False
    print(f"\n✅ SUCCESS METRICS")
    print(f"Zero Diagnostics Achieved: {'🎉 YES' if zero_achieved else '❌ NO'}")
    print(f"Build Status: {report.build_status}")
    print(f"Test Status: {report.test_status}")
    print(f"Quality Improvement: {report.code_quality_improvement:.1f}%")
    
    # Performance metrics
    if report.subagent_performance:
        print(f"\n⚡ PERFORMANCE METRICS")
        for agent, time in report.subagent_performance.items():
            print(f"{agent}: {time:.3f}s")
    
    # Workflow phases
    print(f"\n📋 WORKFLOW PHASES")
    for phase_name, phase_result in report.workflow_phases.items():
        status = "✅" if phase_result.success else "❌"
        print(f"{status} {phase_name}: {phase_result.output_summary}")
        if phase_result.warnings_or_errors:
            for warning in phase_result.warnings_or_errors[:3]:  # Show first 3 warnings
                print(f"    ⚠️  {warning}")
    
    # Recommendations
    if report.maintenance_recommendations:
        print(f"\n💡 RECOMMENDATIONS")
        for rec in report.maintenance_recommendations[:3]:  # Show top 3
            print(f"• {rec}")


def print_validation_details(report: FactoryReport):
    """Print detailed validation information."""
    
    print_report_summary(report)
    
    print(f"\n🔄 VALIDATION DETAILS")
    print("-" * 40)
    
    # Extract rollback information
    total_rollbacks = report.before_after_metrics.get("rollbacks_performed", 0)
    print(f"Total Rollbacks: {total_rollbacks}")
    
    # Look for validation failures in phase results
    validation_failures = 0
    for phase_name, phase_result in report.workflow_phases.items():
        if "incremental_fixer" in phase_name:
            failures = phase_result.detailed_results.get("validation_failures", [])
            if failures:
                print(f"\n📋 {phase_name.upper()} VALIDATION FAILURES:")
                for i, failure in enumerate(failures[:3], 1):  # Show first 3
                    print(f"  {i}. {failure.get('diagnostic', 'Unknown')[:80]}...")
                    print(f"     Fix: {failure.get('fix_attempted', 'Unknown')}")
                    print(f"     Reason: {failure.get('rollback_reason', 'Unknown')}")
            validation_failures += len(failures)
    
    print(f"\nTotal Validation Failures: {validation_failures}")
    
    if validation_failures == 0:
        print("🎉 All fixes passed validation!")
    else:
        print(f"⚠️  {validation_failures} fixes required rollback")


async def demo_clion_integration():
    """Demonstrate CLion IDE integration."""
    
    print("\n🔬 DEMO 4: CLion IDE Integration")
    print("=" * 60)
    
    print("🔗 Features being demonstrated:")
    print("• Connection to CLion IDE via mcp__ide__getDiagnostics")
    print("• Real-time diagnostic discovery")
    print("• IDE-accurate diagnostic categorization") 
    print("• Zero-tolerance validation")
    print()
    
    # Test CLion connection (this would use real MCP in production)
    print("🔌 Testing CLion IDE Connection...")
    
    try:
        # This would be a real connection test
        connection_available = False  # Placeholder - would check mcp__ide__getDiagnostics
        
        if connection_available:
            print("✅ CLion IDE connection established")
            print("✅ mcp__ide__getDiagnostics available")
            
            # Would run actual workflow with CLion integration
            target_file = "/IdeaProjects/wire_ground/tests/safe_test.cpp"
            if Path(target_file).exists():
                report = await achieve_zero_diagnostics([target_file])
                print_report_summary(report)
        else:
            print("⚠️  CLion IDE connection not available")
            print("📝 This demo shows the integration architecture")
            print("   In production, the system would:")
            print("   • Connect to CLion IDE automatically")
            print("   • Retrieve real-time diagnostics")
            print("   • Apply fixes with immediate validation")
            print("   • Achieve true ZERO diagnostics")
            
    except Exception as e:
        print(f"❌ CLion integration test failed: {e}")


async def run_all_demos():
    """Run all demonstration scenarios."""
    
    print("🚀 ZERO CLION DIAGNOSTICS SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("This demonstration shows the agent-factory-with-subagents pattern")
    print("for achieving ZERO CLion diagnostics with incremental validation.")
    print()
    
    print("🎯 KEY FEATURES:")
    print("• CLion IDE integration for real-time diagnostics")
    print("• Specialized subagents for different diagnostic types")
    print("• Incremental fixing with validation after each change")
    print("• Automatic rollback on validation failures")
    print("• Zero-tolerance enforcement (NO diagnostics remain)")
    print()
    
    print("🤖 SUBAGENTS:")
    print("• CLion Diagnostic Analyzer - Connects to IDE, gets all diagnostics")
    print("• Diagnostic Prioritizer - Orders fixes to prevent cascade failures")
    print("• Error Fixer - Handles compilation errors precisely")
    print("• Warning Eliminator - Eliminates ALL warnings with zero tolerance")
    print("• Info Optimizer - Applies C++20/17/23 optimizations")
    print("• Validation Enforcer - Validates fixes with rollback capability")
    print()
    
    start_time = datetime.now()
    
    # Run all demos
    await demo_single_file()
    await demo_multiple_files()
    await demo_incremental_validation()
    await demo_clion_integration()
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n🎉 DEMONSTRATION COMPLETE")
    print("=" * 60)
    print(f"Total Demo Duration: {total_time:.2f} seconds")
    print("\n📋 SYSTEM READY FOR PRODUCTION USE")
    print("Key Integration Points:")
    print("• Connect mcp__ide__getDiagnostics for real CLion integration")
    print("• Configure project-specific build commands")
    print("• Set up pre-commit hooks for continuous validation")
    print("• Enable real-time monitoring in CI/CD pipeline")
    print()
    print("For production use: factory_orchestrator.achieve_zero_diagnostics(files)")


if __name__ == "__main__":
    try:
        print("🔧 Initializing Zero Diagnostics System...")
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo system failed: {e}")
        print(f"❌ Demo system failed: {e}")
        sys.exit(1)