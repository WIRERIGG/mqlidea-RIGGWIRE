#!/usr/bin/env python3
"""
Test Valgrind-Clang-Tidy Integration on safe_test.cpp
=====================================================

Direct test of the integration system on the actual safe_test.cpp file
to demonstrate memory safety + warning-free code analysis.
"""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append('/IdeaProjects/wire_ground/.claude/agents')

from valgrind_clang_tidy_integrator import ValgrindClangTidyIntegrator


async def test_safe_test_cpp():
    """Test the integration on safe_test.cpp specifically."""
    print("🧪 Testing Valgrind-Clang-Tidy Integration on safe_test.cpp")
    print("=" * 60)
    
    # Paths for safe_test.cpp
    binary_path = "/IdeaProjects/wire_ground/cmake-build-debug/wire_ground_tests"
    source_files = ["/IdeaProjects/wire_ground/tests/safe_test.cpp"]
    
    # Check if files exist
    if not Path(binary_path).exists():
        print(f"❌ Binary not found: {binary_path}")
        return False
        
    if not Path(source_files[0]).exists():
        print(f"❌ Source file not found: {source_files[0]}")
        return False
    
    print(f"✅ Binary found: {binary_path}")
    print(f"✅ Source file found: {source_files[0]}")
    
    # Initialize integrator
    integrator = ValgrindClangTidyIntegrator(
        project_root="/IdeaProjects/wire_ground",
        auto_backup=True,
        strict_mode=True
    )
    
    print(f"\n🔧 Running integrated analysis...")
    
    try:
        # Run the complete integration
        result = await integrator.fix_with_zero_warnings_guarantee(
            binary_path=binary_path,
            source_files=source_files,
            issue_description="Comprehensive analysis of safe_test.cpp for memory safety and warnings",
            force_apply=False  # Safe mode - don't auto-apply risky fixes
        )
        
        # Display results
        print(f"\n📊 Integration Results:")
        print(f"{'=' * 40}")
        print(f"Success: {result.success}")
        print(f"Integration ID: {result.integration_id}")
        print(f"Memory issues detected: {result.memory_issues_fixed}")
        print(f"Memory fixes applied: {result.memory_fixes_applied}")
        print(f"Warnings introduced: {result.warnings_introduced}")
        print(f"Warnings fixed: {result.warnings_fixed}")
        print(f"Final warning count: {result.final_warning_count}")
        print(f"Files modified: {len(result.files_modified)}")
        print(f"Backup location: {result.backup_location}")
        print(f"Integration time: {result.integration_time:.2f}s")
        
        # Show phase details
        if result.context:
            context = result.context
            print(f"\n🔍 Phase Details:")
            print(f"Final phase reached: {context.phase}")
            print(f"Memory issues found: {len(context.memory_issues)}")
            print(f"Valgrind fixes recommended: {len(context.valgrind_fixes)}")
            print(f"Applied memory fixes: {len(context.applied_memory_fixes)}")
            print(f"Detected warnings: {len(context.detected_warnings)}")
            print(f"Applied warning fixes: {len(context.applied_warning_fixes)}")
            
            # Show warnings if any were detected
            if context.detected_warnings:
                print(f"\n⚠️ Warnings detected after Valgrind fixes:")
                for i, warning in enumerate(context.detected_warnings[:3], 1):
                    print(f"{i}. {warning.get('rule', 'unknown')}: {warning.get('message', 'No message')}")
                    print(f"   Location: {warning.get('file', 'unknown')}:{warning.get('line', 0)}")
        
        # Final assessment
        if result.success:
            if result.final_warning_count == 0:
                print(f"\n🎉 SUCCESS: safe_test.cpp is memory-safe AND warning-free!")
            else:
                print(f"\n⚠️ PARTIAL SUCCESS: Memory safe but {result.final_warning_count} warnings remain")
        else:
            print(f"\n❌ FAILED: {result.error_message}")
            
        return result.success
        
    except Exception as e:
        print(f"\n❌ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_direct_valgrind_test():
    """Run a direct Valgrind test on safe_test for comparison."""
    print(f"\n🔍 Running direct Valgrind test for comparison...")
    
    try:
        import subprocess
        
        binary_path = "/IdeaProjects/wire_ground/cmake-build-debug/wire_ground_tests"
        
        # Run basic Valgrind memcheck
        cmd = [
            "valgrind",
            "--tool=memcheck",
            "--leak-check=full",
            "--show-leak-kinds=all", 
            "--track-origins=yes",
            "--xml=yes",
            f"--xml-file=/tmp/safe_test_valgrind.xml",
            binary_path,
            "--gtest_filter=SafetyTestSuite.*"
        ]
        
        print(f"Running: {' '.join(cmd[:6])} [binary] --gtest_filter=SafetyTestSuite.*")
        
        # Run with timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/IdeaProjects/wire_ground"
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            
            # Check if XML file was created
            xml_file = Path("/tmp/safe_test_valgrind.xml")
            if xml_file.exists():
                xml_content = xml_file.read_text()
                
                # Simple parsing for errors
                import re
                error_pattern = r'<error>'
                leak_pattern = r'<kind>([^<]+)</kind>'
                
                error_count = len(re.findall(error_pattern, xml_content))
                leak_types = re.findall(leak_pattern, xml_content)
                
                print(f"✅ Valgrind analysis complete:")
                print(f"   Errors detected: {error_count}")
                if leak_types:
                    print(f"   Leak types: {', '.join(set(leak_types))}")
                else:
                    print(f"   No memory leaks detected")
                    
                return error_count == 0
                
            else:
                print(f"⚠️ Valgrind XML output not found")
                return False
                
        except asyncio.TimeoutError:
            print(f"⚠️ Valgrind test timed out after 30 seconds")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Direct Valgrind test failed: {e}")
        return False


async def run_clang_tidy_test():
    """Run a direct clang-tidy test on safe_test.cpp."""
    print(f"\n🔧 Running direct clang-tidy test for comparison...")
    
    try:
        source_file = "/IdeaProjects/wire_ground/tests/safe_test.cpp"
        
        cmd = [
            "clang-tidy",
            "--checks=-*,readability-*,modernize-*,performance-*,bugprone-*",
            source_file,
            "--",
            "-I/IdeaProjects/wire_ground/include",
            "-I/usr/src/googletest/googletest/include",
            "-std=c++20"
        ]
        
        print(f"Running clang-tidy with modernize/readability checks...")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/IdeaProjects/wire_ground"
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20.0)
            
            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')
            
            # Count warnings
            warning_pattern = r': warning:'
            warning_count = len(re.findall(warning_pattern, output + error_output))
            
            print(f"✅ Clang-tidy analysis complete:")
            print(f"   Warnings detected: {warning_count}")
            
            if warning_count > 0:
                print(f"   Sample warnings:")
                lines = (output + error_output).split('\n')
                warning_lines = [line for line in lines if 'warning:' in line][:3]
                for warning in warning_lines:
                    print(f"     {warning.strip()}")
            
            return warning_count == 0
            
        except asyncio.TimeoutError:
            print(f"⚠️ Clang-tidy test timed out after 20 seconds")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Direct clang-tidy test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🚀 Comprehensive Test Suite: safe_test.cpp Integration")
    print("=" * 60)
    
    # Run tests
    integration_success = await test_safe_test_cpp()
    valgrind_clean = await run_direct_valgrind_test()
    clang_tidy_clean = await run_clang_tidy_test()
    
    # Summary
    print(f"\n📋 Test Summary:")
    print(f"=" * 30)
    print(f"Integration test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Direct Valgrind: {'✅ CLEAN' if valgrind_clean else '❌ ISSUES'}")
    print(f"Direct clang-tidy: {'✅ CLEAN' if clang_tidy_clean else '❌ WARNINGS'}")
    
    if integration_success and valgrind_clean and clang_tidy_clean:
        print(f"\n🎉 EXCELLENT: safe_test.cpp is memory-safe and warning-free!")
    elif integration_success:
        print(f"\n✅ GOOD: Integration system working properly")
    else:
        print(f"\n⚠️ Integration system needs refinement")
    
    return integration_success


if __name__ == '__main__':
    import re
    success = asyncio.run(main())
    exit(0 if success else 1)