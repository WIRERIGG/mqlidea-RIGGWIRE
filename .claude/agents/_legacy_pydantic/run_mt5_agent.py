#!/usr/bin/env python3
"""Run MT5 Infinite Reliability Agent to validate the ST1 buffer fix."""

import asyncio
import sys
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    try:
        from mt5_infinite_reliability_agent.agent import mt5_optimizer
        from mt5_infinite_reliability_agent.dependencies import AgentDependencies
        from mt5_infinite_reliability_agent.settings import settings

        print("=" * 60)
        print("MT5 INFINITE RELIABILITY AGENT - VALIDATION RUN")
        print("=" * 60)

        # Read the fixed file
        lei_path = Path("/Users/shemarrigg/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE/LEIlight.mq5")
        code = lei_path.read_text()

        # Create dependencies
        deps = AgentDependencies.from_settings(settings, analysis_mode="analyze")
        deps.add_snapshot(code)

        print("\nAnalyzing LEIlight.mq5 v3.30 fix for empty ST1/ST2 buffers...")
        print("-" * 60)

        # Run validation
        result = await mt5_optimizer.run(
            """Validate the v3.30 fix for empty ST1/ST2 buffers on M15/H1 charts.

            The fix added need_trend_init flag to CalculateST1/CalculateST2 functions.

            PROBLEM: When MAX_CALC_BARS optimization started the loop at bar 1500+,
            the trend was never initialized because it only happened when i == ATR_Period.

            FIX APPLIED:
            ```mql5
            bool need_trend_init = (prev_calculated == 0 || start_pos == g_Active_ST1_ATR_Period);

            for(int i = start_pos; i < rates_total; i++)
            {
                if(need_trend_init)
                {
                    ST1_Trend[i] = (close[i] > ST1_Dn[i]) ? 1 : -1;
                    need_trend_init = false;
                }
            }
            ```

            Validate:
            1. Is this fix correct for the MAX_CALC_BARS issue?
            2. Will ST1_Buffer now populate correctly on M15/H1 charts?
            3. Are there any edge cases we missed?
            """,
            deps=deps
        )

        print("\n" + "=" * 60)
        print("AGENT VALIDATION RESULT")
        print("=" * 60)

        if hasattr(result.data, 'success'):
            print(f"Success: {result.data.success}")
        if hasattr(result.data, 'summary'):
            print(f"Summary: {result.data.summary}")
        if hasattr(result.data, 'recommendations'):
            print(f"Recommendations: {result.data.recommendations}")

        print("\nFull result:")
        print(result.data)

    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
