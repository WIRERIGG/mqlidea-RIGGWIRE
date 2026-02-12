#!/usr/bin/env python3
"""
Validate that awareness_orchestrator can access all agents in the agents directory.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_integrations():
    """Validate all agent integrations."""

    print("=" * 70)
    print("🔗 AWARENESS ORCHESTRATOR - AGENT INTEGRATION VALIDATION")
    print("=" * 70)
    print()

    results = {
        "internal_agents": {},
        "external_agents": {},
        "tools": {}
    }

    # Check internal agents
    print("📦 Checking Internal Agents...")
    try:
        from awareness_orchestrator.agent import (
            AnalysisAgent,
            ArchitectureAgent,
            ValidationAgent,
            awareness_orchestrator
        )
        results["internal_agents"]["AnalysisAgent"] = "✅ Available"
        results["internal_agents"]["ArchitectureAgent"] = "✅ Available"
        results["internal_agents"]["ValidationAgent"] = "✅ Available"
        results["internal_agents"]["awareness_orchestrator"] = "✅ Available"
        print("  ✅ All internal agents loaded successfully")
    except Exception as e:
        print(f"  ❌ Error loading internal agents: {e}")
        results["internal_agents"]["error"] = str(e)

    print()
    print("🔧 Checking Orchestrator Tools...")

    try:
        from awareness_orchestrator.agent import awareness_orchestrator

        # Get tools via toolsets
        tool_count = 0
        if hasattr(awareness_orchestrator, 'toolsets') and awareness_orchestrator.toolsets:
            for toolset in awareness_orchestrator.toolsets:
                if hasattr(toolset, 'function_tools'):
                    for tool in toolset.function_tools:
                        if hasattr(tool, 'name'):
                            results["tools"][tool.name] = "✅ Registered"
                            tool_count += 1

        print(f"  ✅ Found {tool_count} registered tools")
    except Exception as e:
        print(f"  ❌ Error checking tools: {e}")

    print()
    print("🌐 Checking External Agent Imports...")

    external_agents = [
        ("blitzfire_code_agent", "blitzfire_code_agent.agent", "quick_analyze"),
        ("blitzfire_cpp_optimizer", "blitzfire_cpp_optimizer.agent", "analyze_cpp_performance"),
        ("clang_tidy_ai_agent", "clang_tidy_ai_agent.agent", "analyze_cpp_file"),
        ("mt5_infinite_reliability_agent", "mt5_infinite_reliability_agent.agent", "optimize_mql5_code"),
        ("multi_agent_debugging_system", "multi_agent_debugging_system.agent", "analyze_cpp_code"),
        ("never_fail_build_resolver", "never_fail_build_resolver.agent", "resolve_build_fast"),
    ]

    for name, module, func in external_agents:
        try:
            mod = __import__(module, fromlist=[func])
            if hasattr(mod, func):
                results["external_agents"][name] = "✅ Available"
                print(f"  ✅ {name}: {func}() accessible")
            else:
                results["external_agents"][name] = f"⚠️ Module loaded but {func}() not found"
                print(f"  ⚠️ {name}: Module loaded but {func}() not found")
        except ImportError as e:
            results["external_agents"][name] = f"❌ Import error: {e}"
            print(f"  ❌ {name}: Import error - {e}")
        except Exception as e:
            results["external_agents"][name] = f"❌ Error: {e}"
            print(f"  ❌ {name}: Error - {e}")

    # Summary
    print()
    print("=" * 70)
    print("📊 INTEGRATION SUMMARY")
    print("=" * 70)

    internal_ok = sum(1 for v in results["internal_agents"].values() if "✅" in str(v))
    external_ok = sum(1 for v in results["external_agents"].values() if "✅" in str(v))
    tools_ok = len(results["tools"])

    print(f"""
Internal Agents: {internal_ok}/4 available
External Agents: {external_ok}/{len(external_agents)} available
Orchestrator Tools: {tools_ok} registered

TOOLS AVAILABLE TO ORCHESTRATOR:
""")

    # List all tools
    expected_tools = [
        "run_analysis_agent",
        "run_architecture_agent",
        "run_validation_agent",
        "record_results",
        "show_dashboard",
        "run_blitzfire_code_agent",
        "run_blitzfire_cpp_optimizer",
        "run_clang_tidy_ai_agent",
        "run_mt5_optimizer_agent",
        "run_multi_agent_debugger",
        "run_never_fail_build_resolver",
        "list_available_agents",
        "run_agent_chain"
    ]

    for tool in expected_tools:
        status = "✅" if tool in results["tools"] else "❌"
        print(f"  {status} {tool}")

    print()

    # Final status
    all_internal = internal_ok == 4
    all_tools = tools_ok >= 13

    if all_internal and all_tools:
        print("🚀 AWARENESS ORCHESTRATOR: FULLY INTEGRATED WITH ALL AGENTS")
        return 0
    else:
        print("⚠️ AWARENESS ORCHESTRATOR: SOME INTEGRATIONS MISSING")
        return 1


if __name__ == "__main__":
    sys.exit(validate_integrations())
