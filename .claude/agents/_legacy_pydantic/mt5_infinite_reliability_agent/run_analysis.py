#!/usr/bin/env python3
"""
Run MT5 Infinite Reliability Agent on LeadingExtremaIndicator_FIXED.mq5
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for proper module imports
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))

from mt5_infinite_reliability_agent.agent import analyze_mql5_file


async def main():
    """Run the analysis."""
    file_path = Path('/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/LeadingExtremaIndicator_FIXED.mq5')

    print('=' * 70)
    print('🔍 MT5 INFINITE RELIABILITY AGENT - ANALYSIS')
    print('=' * 70)
    print(f'File: {file_path.name}')
    print(f'Size: {file_path.stat().st_size:,} bytes')
    print('=' * 70)
    print()

    # Run analysis
    try:
        print('🚀 Starting full analysis with detailed proof level...')
        print()

        result = await analyze_mql5_file(
            str(file_path),
            mode='full',  # analyze → fix → certify
            proof_level='detailed',
            dimensions=['complexity', 'memory', 'security', 'robustness']
        )

        print()
        print('=' * 70)
        print('✅ ANALYSIS COMPLETE')
        print('=' * 70)
        print()

        # Display result
        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(result)

        return 0

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ ANALYSIS FAILED')
        print('=' * 70)
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
