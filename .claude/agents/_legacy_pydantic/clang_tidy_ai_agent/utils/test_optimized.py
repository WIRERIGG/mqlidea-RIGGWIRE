#!/usr/bin/env python3
"""
Simple test script for the optimized Clang-Tidy AI Agent.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

try:
    from agent_optimized import OptimizedClangTidyAgent
    from settings_optimized import load_optimized_settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the clang_tidy_ai_agent directory")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic agent functionality."""
    print("🚀 Testing Optimized Clang-Tidy AI Agent")
    print("=" * 50)
    
    try:
        # Load settings
        print("📋 Loading configuration...")
        settings = load_optimized_settings()
        print(f"✓ Configuration loaded for project: {settings.project_root}")
        
        # Create agent
        print("🤖 Creating optimized agent...")
        agent = OptimizedClangTidyAgent(settings)
        print("✓ Agent created successfully")
        
        # Get metrics
        print("📊 Checking initial metrics...")
        metrics = agent.get_metrics()
        print(f"✓ Initial metrics: {json.dumps(metrics, indent=2)}")
        
        # Test file
        test_file = "tests/safe_test.cpp"
        if not Path(settings.project_root / test_file).exists():
            test_file = "main.cpp"
            if not Path(settings.project_root / test_file).exists():
                print(f"❌ No test files found")
                return
        
        print(f"🔍 Analyzing {test_file}...")
        start_time = time.time()
        
        # Run analysis
        result = await agent.analyze_with_fixes(test_file, auto_fix=False)
        
        execution_time = time.time() - start_time
        print(f"✓ Analysis complete in {execution_time:.2f} seconds")
        
        # Show results
        print("\n📋 Analysis Results:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"File: {result.get('file', 'unknown')}")
        print(f"Total warnings: {result.get('total_warnings', 0)}")
        print(f"Warnings found: {len(result.get('warnings', []))}")
        print(f"Explanations: {len(result.get('explanations', []))}")
        
        # Show updated metrics
        print("\n📈 Updated Metrics:")
        updated_metrics = agent.get_metrics()
        print(json.dumps(updated_metrics, indent=2))
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_performance_features():
    """Test performance features."""
    print("\n⚡ Testing Performance Features")
    print("=" * 30)
    
    try:
        settings = load_optimized_settings()
        agent = OptimizedClangTidyAgent(settings)
        
        # Test with multiple files if available
        test_files = ["tests/safe_test.cpp", "main.cpp", "src/main.cpp"]
        existing_files = [f for f in test_files if Path(settings.project_root / f).exists()]
        
        if not existing_files:
            print("❌ No test files found for performance testing")
            return
        
        print(f"📁 Found {len(existing_files)} test files")
        
        # Single file test
        if existing_files:
            print(f"🔍 Single file analysis: {existing_files[0]}")
            start_time = time.time()
            result = await agent.analyze_with_fixes(existing_files[0])
            single_time = time.time() - start_time
            print(f"✓ Single file: {single_time:.2f}s")
        
        # Project analysis test if multiple files
        if len(existing_files) > 1:
            print(f"🏢 Project analysis with {len(existing_files)} files")
            start_time = time.time()
            
            # Create file pattern list
            patterns = [f"**/{Path(f).name}" for f in existing_files[:3]]  # Limit to 3 files
            result = await agent.analyze_project(patterns)
            
            project_time = time.time() - start_time
            print(f"✓ Project analysis: {project_time:.2f}s")
            print(f"Files analyzed: {result.files_analyzed}")
            print(f"Total warnings: {result.total_warnings}")
            print(f"Cache hit rate: {result.cache_hit_rate:.1%}")
            
        print("🎯 Performance test completed!")
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        import traceback
        traceback.print_exc()


def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing Configuration")
    print("=" * 25)
    
    try:
        settings = load_optimized_settings()
        
        print("📝 Configuration Summary:")
        summary = settings.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print(f"\n🔧 Environment Validation:")
        is_valid = settings.validate_environment()
        print(f"✓ Environment valid: {is_valid}")
        
    except Exception as e:
        print(f"❌ Configuration test error: {e}")


async def main():
    """Main test function."""
    print("🧪 Clang-Tidy AI Agent Optimization Test Suite")
    print("=" * 60)
    
    # Test configuration
    test_configuration()
    
    # Test basic functionality
    await test_basic_functionality()
    
    # Test performance features
    await test_performance_features()
    
    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())