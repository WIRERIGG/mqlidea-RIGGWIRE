#!/usr/bin/env python3
"""
Simple test to validate BLITZFIRE implementation works correctly.
"""

import asyncio
import tempfile
import time
from pathlib import Path

try:
    from blitzfire_agent import BlitzfireClangTidyAgent
    from settings_optimized import load_optimized_settings
    from blitzfire_tools import BlitzfirePerformanceProfiler
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the correct directory")
    exit(1)


def create_test_cpp_file(file_path: Path):
    """Create a simple C++ test file with some clang-tidy issues."""
    
    content = '''#include <iostream>
#include <vector>

int main() {
    // Performance issue: should use reserve()
    std::vector<int> vec;
    for (int i = 0; i < 100; ++i) {
        vec.push_back(i);
    }
    
    // Modernization issue: should use nullptr
    char* ptr = NULL;
    
    // Readability issue: should use braces
    for (int i = 0; i < vec.size(); i++)
        std::cout << vec[i] << "\\n";
    
    delete ptr;  // This will be nullptr, so safe
    return 0;
}
'''
    
    file_path.write_text(content)


async def test_blitzfire_basic():
    """Test basic BLITZFIRE functionality."""
    
    print("🧪 Testing BLITZFIRE basic functionality...")
    
    # Create test file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test.cpp"
        create_test_cpp_file(test_file)
        
        try:
            # Create BLITZFIRE agent
            settings = load_optimized_settings()
            
            # Update project root for test
            settings.project_root = temp_path
            
            agent = BlitzfireClangTidyAgent(settings)
            
            # Test analysis
            print("  📁 Running BLITZFIRE analysis...")
            start_time = time.time()
            
            result = await agent.analyze_project_blitzfire(["*.cpp"])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"  ✅ Analysis completed in {execution_time:.3f} seconds")
            print(f"  📊 Files processed: {result['files_processed']}")
            print(f"  ⚠️  Warnings found: {result['total_warnings']}")
            print(f"  🚀 Speedup: {result.get('speedup_achieved', 'N/A')}")
            
            # Get metrics
            metrics = await agent.get_blitzfire_metrics()
            cache_stats = metrics.get("cache_statistics", {})
            
            print(f"  🎯 Cache hit rate: {cache_stats.get('total_hit_rate', 0):.1%}")
            
            # Cleanup
            await agent.cleanup_blitzfire()
            
            return True
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            return False


async def test_blitzfire_performance():
    """Test BLITZFIRE performance with multiple files."""
    
    print("\n🚀 Testing BLITZFIRE performance...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create multiple test files
        num_files = 10
        test_files = []
        
        for i in range(num_files):
            test_file = temp_path / f"test_{i:02d}.cpp"
            create_test_cpp_file(test_file)
            test_files.append(test_file)
        
        try:
            settings = load_optimized_settings()
            settings.project_root = temp_path
            
            agent = BlitzfireClangTidyAgent(settings)
            
            print(f"  📁 Processing {num_files} files...")
            start_time = time.time()
            
            result = await agent.analyze_project_blitzfire(["*.cpp"])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            files_per_second = result['files_processed'] / max(execution_time, 0.001)
            
            print(f"  ✅ Processed {result['files_processed']} files in {execution_time:.3f}s")
            print(f"  ⚡ Throughput: {files_per_second:.1f} files/second")
            print(f"  ⚠️  Total warnings: {result['total_warnings']}")
            
            # Check if we're getting reasonable performance
            if files_per_second > 10:
                print("  🎯 Performance looks good!")
            else:
                print("  ⚠️  Performance could be better")
            
            await agent.cleanup_blitzfire()
            return True
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            return False


async def test_blitzfire_memory():
    """Test BLITZFIRE memory management."""
    
    print("\n🧠 Testing BLITZFIRE memory management...")
    
    try:
        from blitzfire_agent import BlitzfireMemoryManager
        
        # Test memory manager
        memory_manager = BlitzfireMemoryManager()
        
        # Test object pooling
        analyses = []
        for i in range(100):
            analysis = memory_manager.get_analysis(f"test_{i}.cpp")
            analyses.append(analysis)
        
        print(f"  ✅ Allocated {len(analyses)} analysis objects")
        
        # Return objects to pool
        for analysis in analyses:
            memory_manager.return_analysis(analysis)
        
        print("  ♻️  Returned all objects to pool")
        
        # Check stats
        stats = memory_manager.allocation_stats
        print(f"  📊 Allocation stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Memory test failed: {e}")
        return False


async def test_blitzfire_cache():
    """Test BLITZFIRE caching system."""
    
    print("\n💾 Testing BLITZFIRE cache system...")
    
    try:
        from blitzfire_agent import BlitzfireCache
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = BlitzfireCache(cache_dir)
            
            # Test cache operations
            test_data = {"test": "value", "number": 42}
            
            # Store data
            await cache.put("test_key", test_data)
            print("  ✅ Stored data in cache")
            
            # Retrieve data
            retrieved = await cache.get("test_key")
            
            if retrieved == test_data:
                print("  ✅ Retrieved data correctly")
            else:
                print("  ❌ Cache data mismatch")
                return False
            
            # Test cache miss
            missing = await cache.get("nonexistent_key")
            if missing is None:
                print("  ✅ Cache miss handled correctly")
            else:
                print("  ❌ Cache should return None for missing keys")
                return False
            
            # Get stats
            stats = cache.get_stats()
            print(f"  📊 Cache stats: {stats}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Cache test failed: {e}")
        return False


async def main():
    """Run all BLITZFIRE tests."""
    
    print("🚀 BLITZFIRE Simple Test Suite")
    print("=" * 40)
    
    tests = [
        test_blitzfire_basic,
        test_blitzfire_performance,  
        test_blitzfire_memory,
        test_blitzfire_cache
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📋 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test.__name__}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! BLITZFIRE is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))