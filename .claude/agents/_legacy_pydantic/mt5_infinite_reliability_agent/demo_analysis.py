#!/usr/bin/env python3
"""
Demo MT5 Infinite Reliability Agent using TestModel (no API calls required).
This demonstrates the workflow without requiring a valid Anthropic API key.
"""

import asyncio
import sys
from pathlib import Path
from pydantic_ai.models.test import TestModel

# Add parent directory to path for proper module imports
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))

from mt5_infinite_reliability_agent.agent import agent
from mt5_infinite_reliability_agent.dependencies import AgentDependencies


async def demo_analysis():
    """Run demo analysis using TestModel."""

    file_path = Path('/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/LeadingExtremaIndicator_FIXED.mq5')

    print('=' * 70)
    print('🔍 MT5 INFINITE RELIABILITY AGENT - DEMO ANALYSIS')
    print('=' * 70)
    print(f'File: {file_path.name}')
    print(f'Size: {file_path.stat().st_size:,} bytes')
    print()
    print('⚠️  DEMO MODE: Using TestModel (no actual Claude API calls)')
    print('=' * 70)
    print()

    # Read the MQL5 file
    print('📖 Reading MQL5 source code...')
    code = file_path.read_text(encoding='utf-8')
    code_preview = code[:500] + '...' if len(code) > 500 else code
    print(f'✅ Read {len(code):,} characters')
    print()

    # Set up dependencies
    print('⚙️  Configuring dependencies...')
    deps = AgentDependencies(
        source_code_path=file_path,
        analysis_mode='full',  # analyze → fix → certify
        proof_level='detailed',
        dimensions=['complexity', 'memory', 'security', 'robustness'],
        debug=True
    )

    # Add snapshot for rollback
    deps.add_snapshot(code)
    print(f'✅ Added code snapshot ({len(code):,} chars)')
    print()

    # Run analysis
    print('🚀 Running agent analysis with TestModel...')
    print()

    try:
        # Use TestModel context manager
        with agent.override(model=TestModel()):
            result = await agent.run(
                f"Analyze this MQL5 Expert Advisor code in full mode (analyze → fix → certify):\n\n"
                f"File: {file_path.name}\n"
                f"Size: {len(code):,} characters\n\n"
                f"Preview:\n{code_preview}",
                deps=deps
            )

        print()
        print('=' * 70)
        print('✅ DEMO ANALYSIS COMPLETE')
        print('=' * 70)
        print()

        # Show workflow demonstration
        print('📊 WORKFLOW DEMONSTRATION:')
        print()
        print('Phase 1: PARSE & ANALYZE')
        print('  ✓ Parse MQL5 code into AST')
        print('  ✓ Analyze complexity, memory, security, robustness')
        print('  ✓ Identify issues and improvement opportunities')
        print()

        print('Phase 2: SUGGEST & TRANSFORM')
        print('  ✓ Generate transformation suggestions')
        print('  ✓ Apply atomic transformations')
        print('  ✓ Maintain rollback capability')
        print()

        print('Phase 3: VERIFY & CERTIFY')
        print('  ✓ Verify transformations are correct')
        print('  ✓ Check all safety properties hold')
        print('  ✓ Generate cryptographic proof certificate')
        print()

        # Show message exchange
        messages = result.all_messages()
        print(f'📨 Agent exchanged {len(messages)} messages')
        print()

        # Show result structure
        print('📋 RESULT OBJECT:')
        print(f'  • Messages exchanged: {len(messages)}')
        print(f'  • Workflow completed: ✓')
        print(f'  • Tools were invoked to process the code')
        print()

        print('⚠️  NOTE: TestModel returns mock data, not real analysis.')
        print('   For real analysis results, configure API key and use run_analysis.py')
        print()

        # Demo the tools that would be called
        print('🔧 TOOLS AVAILABLE TO AGENT:')
        print('  1. parse_mql5      - Parse MQL5 code into AST')
        print('  2. analyze_code    - 4D static analysis')
        print('  3. transform_code  - Apply transformations')
        print('  4. verify_transformation - Verify correctness')
        print('  5. generate_certificate  - Create proof certificate')
        print()

        print('=' * 70)
        print('🎯 NEXT STEPS FOR PRODUCTION USE:')
        print('=' * 70)
        print()
        print('1. Configure your Anthropic API key:')
        print('   echo "ANTHROPIC_API_KEY=sk-ant-api03-xxxxx" > .env')
        print()
        print('2. Run with real Claude Opus 4.5:')
        print('   python3 run_analysis.py')
        print()
        print('3. Or use programmatically:')
        print('   from mt5_infinite_reliability_agent import analyze_mql5_file')
        print('   result = await analyze_mql5_file("your_file.mq5")')
        print()

        return 0

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ DEMO FAILED')
        print('=' * 70)
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(demo_analysis())
    sys.exit(exit_code)
