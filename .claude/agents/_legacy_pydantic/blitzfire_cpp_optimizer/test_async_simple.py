"""Simple tests for async dependency methods to improve coverage."""

import pytest
import asyncio
import os
import tempfile
from dependencies import BlitzfireDependencies, create_dependencies


@pytest.mark.asyncio
async def test_dependencies_lifecycle():
    """Test BlitzfireDependencies full lifecycle - initialize, health_check, cleanup."""
    deps = BlitzfireDependencies()
    
    # Test initial state
    if deps.initialized:
        pytest.fail("Should not be initialized by default")
    
    # Test initialization
    await deps.initialize()
    
    if not deps.initialized:
        pytest.fail("Should be initialized after initialize()")
    
    # Test health check
    health = await deps.health_check()
    
    if not isinstance(health, dict):
        pytest.fail("Health check should return dict")
    if "initialized" not in health:
        pytest.fail("Health check should include initialized status")
    if "archon_available" not in health:
        pytest.fail("Health check should include archon_available status")
    
    # Test cleanup
    await deps.cleanup()
    
    if deps.initialized:
        pytest.fail("Should not be initialized after cleanup")


@pytest.mark.asyncio
async def test_create_dependencies_function():
    """Test create_dependencies function."""
    deps = await create_dependencies(debug_mode=True)
    
    if not isinstance(deps, BlitzfireDependencies):
        pytest.fail("Should return BlitzfireDependencies instance")
    if not deps.initialized:
        pytest.fail("Should be initialized")
    
    # Test with custom wire_ground_root
    custom_root = "/tmp/test_wire_ground"
    deps2 = await create_dependencies(wire_ground_root=custom_root)
    
    if deps2.wire_ground_root != custom_root:
        pytest.fail("Should use custom wire_ground_root")


@pytest.mark.asyncio 
async def test_dependencies_temp_directory_creation():
    """Test that temp directory is created during initialization."""
    deps = BlitzfireDependencies()
    
    # Use a unique temp directory for testing
    test_temp = tempfile.gettempdir() + "/test_blitzfire_" + str(os.getpid())
    deps.temp_dir = test_temp
    
    # Ensure it doesn't exist initially
    if os.path.exists(test_temp):
        os.rmdir(test_temp)
    
    # Initialize should create the directory
    await deps.initialize()
    
    if not os.path.exists(test_temp):
        pytest.fail("Temp directory should be created during initialization")
    
    # Cleanup
    await deps.cleanup()
    if os.path.exists(test_temp):
        os.rmdir(test_temp)


@pytest.mark.asyncio
async def test_concurrent_initialization():
    """Test concurrent initialization calls."""
    deps = BlitzfireDependencies()
    
    # Multiple concurrent initialization calls should be safe
    tasks = [
        deps.initialize(),
        deps.initialize(),
        deps.initialize()
    ]
    
    await asyncio.gather(*tasks)
    
    if not deps.initialized:
        pytest.fail("Should be initialized after concurrent calls")


@pytest.mark.asyncio
async def test_dependencies_components_after_init():
    """Test that all components are available after initialization."""
    deps = BlitzfireDependencies()
    await deps.initialize()
    
    # Check that core components are created
    component_names = ['archon_client', 'cpp_analyzer', 'compiler_optimizer', 
                      'benchmark_generator', 'safety_validator']
    
    for component_name in component_names:
        component = getattr(deps, component_name, None)
        if component is None:
            pytest.fail(f"Component {component_name} should be created during initialization")


@pytest.mark.asyncio
async def test_archon_availability_check():
    """Test archon availability checking during initialization."""
    deps = BlitzfireDependencies()
    await deps.initialize()
    
    # archon_available should be set (True or False depending on server availability)
    if not hasattr(deps, 'archon_available'):
        pytest.fail("Should have archon_available attribute")
    
    # It should be a boolean
    if not isinstance(deps.archon_available, bool):
        pytest.fail("archon_available should be boolean")


@pytest.mark.asyncio
async def test_dependencies_settings_and_config():
    """Test that dependencies have proper settings and config."""
    deps = BlitzfireDependencies()
    
    # Test default settings
    if not isinstance(deps.settings, dict):
        pytest.fail("Settings should be dict")
    if "optimization_level" not in deps.settings:
        pytest.fail("Settings should include optimization_level")
    
    # Test default config
    if not isinstance(deps.config, dict):
        pytest.fail("Config should be dict")
    if "compiler" not in deps.config:
        pytest.fail("Config should include compiler")
    
    # Test session_id
    if not isinstance(deps.session_id, str):
        pytest.fail("Session ID should be string")
    if len(deps.session_id) == 0:
        pytest.fail("Session ID should not be empty")


@pytest.mark.asyncio
async def test_dependencies_error_handling():
    """Test error handling in dependencies."""
    deps = BlitzfireDependencies()
    
    # Test that cleanup doesn't fail on uninitialized dependencies
    await deps.cleanup()  # Should not raise exception
    
    # Test that double initialization is safe
    await deps.initialize()
    await deps.initialize()  # Should not raise exception
    
    if not deps.initialized:
        pytest.fail("Should remain initialized after double init")


@pytest.mark.asyncio
async def test_dependencies_state_consistency():
    """Test state consistency across async operations."""
    deps = BlitzfireDependencies()
    
    # Test initial state
    if deps.initialized != False:
        pytest.fail("Initial state should be not initialized")
    
    # Initialize
    await deps.initialize()
    if deps.initialized != True:
        pytest.fail("Should be initialized after init")
    
    # Health check should work when initialized
    health = await deps.health_check()
    if "initialized" not in health:
        pytest.fail("Health check should include initialized status")
    if not health["initialized"]:
        pytest.fail("Health check should show initialized as True")
    
    # Cleanup
    await deps.cleanup()
    if deps.initialized != False:
        pytest.fail("Should not be initialized after cleanup")


@pytest.mark.asyncio
async def test_async_pattern_compliance():
    """Test that async methods follow proper async patterns."""
    deps = BlitzfireDependencies()
    
    # All async methods should be awaitable
    init_coroutine = deps.initialize()
    if not hasattr(init_coroutine, '__await__'):
        pytest.fail("initialize() should return awaitable")
    await init_coroutine
    
    cleanup_coroutine = deps.cleanup()
    if not hasattr(cleanup_coroutine, '__await__'):
        pytest.fail("cleanup() should return awaitable")
    await cleanup_coroutine
    
    health_coroutine = deps.health_check()
    if not hasattr(health_coroutine, '__await__'):
        pytest.fail("health_check() should return awaitable")
    await health_coroutine