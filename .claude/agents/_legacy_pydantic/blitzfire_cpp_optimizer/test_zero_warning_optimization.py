#!/usr/bin/env python3
"""
BLITZFIRE Zero-Warning Optimization Workflow Test

This script tests the complete zero-warning optimization workflow
using the integrated BLITZFIRE optimizer with zero-warning enforcement subagent.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agent import BlitzfireAgent, ZERO_WARNING_ENFORCER_AVAILABLE
    from tools import ZERO_WARNING_TOOLS_AVAILABLE
    from dependencies import BlitzfireDependencies
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all BLITZFIRE components are properly installed")
    sys.exit(1)

# Test cases with varying levels of warning complexity
TEST_CASES = {
    "simple_warnings": """
#include <iostream>
#include <vector>

void test_function(int unused_param) {
    std::vector<double> data = {1.0, 2.0, 3.0};
    int sum = 0;
    for (int i = 0; i < data.size(); ++i) {  // size_t vs int comparison
        sum += (int)data[i];  // old-style cast
    }
    std::cout << sum << std::endl;  // std::endl instead of '\\n'
}
""",
    
    "performance_bottleneck": """
#include <iostream>
#include <vector>
#include <cmath>

// Slow nested loop with expensive operations
double slow_computation(const std::vector<double>& data) {
    double result = 0.0;
    for (int i = 0; i < data.size(); ++i) {
        for (int j = 0; j < data.size(); ++j) {
            result += data[i] * data[j] * sin(data[i]);  // O(n²) + expensive sin()
        }
    }
    return result;
}
""",
    
    "simd_opportunity": """
// Prime candidate for SIMD optimization with warnings
void vector_add(const float* a, const float* b, float* result, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        result[i] = a[i] + b[i];
    }
}
""",
    
    "complex_warnings": """
#include <iostream>
#include <memory>
#include <vector>

struct Base {
    virtual void process() = 0;  // Missing virtual destructor
};

struct Derived : public Base {
    void process() {  // Missing override
        std::cout << "Processing" << std::endl;
    }
};

void problematic_function() {
    auto ptr = std::make_unique<Derived>();
    bool const ptr_is_null = (ptr == nullptr);  // Redundant - make_unique never returns null
    
    std::vector<int> data = {1, 2, 3};
    for (int i = 0; i < data.size(); ++i) {  // size_t vs int
        data[i] = (int)(data[i] * 2.0);  // old-style cast, implicit conversion
    }
}
"""
}

class ZeroWarningOptimizationTester:
    """Comprehensive tester for BLITZFIRE zero-warning optimization."""
    
    def __init__(self):
        self.agent = BlitzfireAgent()
        self.dependencies = BlitzfireDependencies()
        self.test_results = {}
    
    async def run_comprehensive_test(self):
        """Run comprehensive zero-warning optimization tests."""
        
        print("🔥" * 50)
        print("🚀 BLITZFIRE ZERO-WARNING OPTIMIZATION TEST SUITE")
        print("🔥" * 50)
        print()
        
        # Check availability of zero-warning enforcement
        print("📋 System Capability Check:")
        print(f"  Zero-Warning Enforcer Available: {'✅ YES' if ZERO_WARNING_ENFORCER_AVAILABLE else '❌ NO'}")
        print(f"  Zero-Warning Tools Available: {'✅ YES' if ZERO_WARNING_TOOLS_AVAILABLE else '❌ NO'}")
        print(f"  Total BLITZFIRE Tools: {len(self.agent.tools)}")
        print()
        
        if not ZERO_WARNING_ENFORCER_AVAILABLE:
            print("⚠️ Zero-warning enforcer not available - testing standard optimization only")
            print()
        
        # Run tests for each test case
        for test_name, test_code in TEST_CASES.items():
            print(f"🧪 Testing: {test_name.replace('_', ' ').title()}")
            print("=" * 60)
            
            result = await self.test_optimization_workflow(test_name, test_code)
            self.test_results[test_name] = result
            
            self.print_test_result(test_name, result)
            print()
        
        # Generate comprehensive report
        await self.generate_final_report()
    
    async def test_optimization_workflow(self, test_name: str, code: str) -> dict:
        """Test the complete optimization workflow for a single test case."""
        
        result = {
            "success": False,
            "original_code": code,
            "optimized_code": None,
            "optimizations_applied": [],
            "zero_warning_enforcement": False,
            "warning_enforcement_report": None,
            "performance_analysis": None,
            "validation_status": None,
            "error": None
        }
        
        try:
            # Step 1: Analyze original code performance
            print("  📊 Analyzing performance bottlenecks...")
            from agent import analyze_cpp_performance
            perf_analysis = await analyze_cpp_performance(
                self.dependencies, 
                code, 
                optimization_level="advanced"
            )
            result["performance_analysis"] = perf_analysis
            
            # Step 2: Apply optimization with zero-warning enforcement
            print("  🔧 Applying BLITZFIRE optimization with zero-warning enforcement...")
            optimization_result = await self.agent.optimize_cpp_code(
                self.dependencies,
                code,
                optimization_level="advanced",
                safety_mode=True,
                target_speedup="10x",
                enforce_zero_warnings=True
            )
            
            if optimization_result["success"]:
                result.update({
                    "success": True,
                    "optimized_code": optimization_result["optimized_code"],
                    "optimizations_applied": optimization_result["optimizations_applied"],
                    "zero_warning_enforcement": optimization_result.get("zero_warning_enforcement", False),
                    "warning_enforcement_report": optimization_result.get("warning_enforcement_report"),
                    "compiler_flags": optimization_result.get("compiler_flags", [])
                })
                
                # Step 3: Validate the optimization
                print("  ✅ Validating optimization safety...")
                validation = await self.agent.validate_optimization_safety(
                    self.dependencies,
                    optimization_result["optimized_code"],
                    code
                )
                result["validation_status"] = validation
                
            else:
                result["error"] = "Optimization failed"
                
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Test error: {e}")
        
        return result
    
    def print_test_result(self, test_name: str, result: dict):
        """Print detailed test results."""
        
        print(f"  📋 Results for {test_name}:")
        print(f"    Success: {'✅ YES' if result['success'] else '❌ NO'}")
        
        if result["success"]:
            print(f"    Optimizations Applied: {len(result['optimizations_applied'])}")
            for opt in result['optimizations_applied']:
                print(f"      • {opt}")
            
            print(f"    Zero-Warning Enforcement: {'✅ ACTIVE' if result['zero_warning_enforcement'] else '⚠️ NOT AVAILABLE'}")
            
            if result.get("performance_analysis") and result["performance_analysis"].get("success"):
                bottlenecks = result["performance_analysis"].get("analysis", {}).get("bottlenecks", [])
                print(f"    Bottlenecks Identified: {len(bottlenecks)}")
                for bottleneck in bottlenecks:
                    print(f"      • {bottleneck.get('issue', 'Unknown')} ({bottleneck.get('estimated_speedup', 'Unknown speedup')})")
            
            if result.get("validation_status"):
                validation = result["validation_status"]
                print(f"    Validation: Memory Safe: {validation.get('memory_safe', 'Unknown')}")
                print(f"               Thread Safe: {validation.get('thread_safe', 'Unknown')}")
                print(f"               Warnings: {validation.get('compiler_warnings', 'Unknown')}")
            
            if result.get("warning_enforcement_report"):
                print(f"    Warning Report: Available")
                print(f"      Report Length: {len(result['warning_enforcement_report'])} characters")
            
        else:
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    async def generate_final_report(self):
        """Generate final comprehensive report."""
        
        print("🎯" * 50)
        print("📊 FINAL BLITZFIRE ZERO-WARNING OPTIMIZATION REPORT")
        print("🎯" * 50)
        print()
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        zero_warning_tests = sum(1 for result in self.test_results.values() if result.get("zero_warning_enforcement", False))
        
        print(f"📈 Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"  Zero-Warning Enforced: {zero_warning_tests}/{total_tests} ({zero_warning_tests/total_tests*100:.1f}%)")
        print()
        
        print(f"🔥 BLITZFIRE Capabilities Demonstrated:")
        
        # Collect all optimizations applied
        all_optimizations = []
        for result in self.test_results.values():
            if result["success"]:
                all_optimizations.extend(result.get("optimizations_applied", []))
        
        unique_optimizations = list(set(all_optimizations))
        for opt in unique_optimizations:
            print(f"  ✅ {opt}")
        
        print()
        
        # Performance analysis summary
        total_bottlenecks = 0
        for result in self.test_results.values():
            if result.get("performance_analysis") and result["performance_analysis"].get("success"):
                bottlenecks = result["performance_analysis"].get("analysis", {}).get("bottlenecks", [])
                total_bottlenecks += len(bottlenecks)
        
        print(f"📊 Analysis Results:")
        print(f"  Total Performance Bottlenecks Identified: {total_bottlenecks}")
        print(f"  Average per Test Case: {total_bottlenecks/total_tests:.1f}")
        print()
        
        # System status
        print(f"🏆 BLITZFIRE Zero-Warning System Status:")
        if ZERO_WARNING_ENFORCER_AVAILABLE and successful_tests == total_tests:
            print(f"  ✅ FULLY OPERATIONAL - Zero-warning enforcement active")
            print(f"  🚀 Ready for production C++ optimization with zero-tolerance policy")
        elif successful_tests == total_tests:
            print(f"  ✅ OPTIMIZATION OPERATIONAL - Standard BLITZFIRE working")
            print(f"  ⚠️ Zero-warning enforcement not available but optimization successful")
        else:
            print(f"  ⚠️ PARTIAL OPERATION - Some tests failed")
            print(f"  🔧 Review configuration and dependencies")
        
        print()
        print(f"🔥 BLITZFIRE C++ Optimizer: Blazingly Fast Code with Zero-Warning Quality! 🔥")

async def main():
    """Main test execution."""
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    tester = ZeroWarningOptimizationTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())