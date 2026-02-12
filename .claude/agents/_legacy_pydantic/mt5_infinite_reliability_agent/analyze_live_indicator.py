#!/usr/bin/env python3
"""
MT5 Infinite Reliability Agent - Analysis of LeadingExtremaIndicator_LIVE.mq5
Optimized for production-ready indicator validation.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))

from mt5_infinite_reliability_agent.agent import analyze_mql5_code
from mt5_infinite_reliability_agent.dependencies import AgentDependencies


async def analyze_in_chunks(file_path: Path, chunk_size: int = 800) -> dict:
    """
    Analyze large MQL5 file in chunks to respect rate limits.

    Args:
        file_path: Path to MQL5 file
        chunk_size: Lines per chunk (default: 800 lines ≈ 10-12K tokens)

    Returns:
        Combined analysis results with reliability certification
    """
    print('=' * 80)
    print('🔍 MT5 INFINITE RELIABILITY AGENT - PRODUCTION VALIDATION')
    print('=' * 80)
    print(f'Target File:   {file_path.name}')
    print(f'File Size:     {file_path.stat().st_size:,} bytes')
    print(f'Chunk Size:    {chunk_size} lines per chunk')
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    print()

    # Read and split file into chunks
    print('📖 Reading source file...')
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f'   ✅ Total lines: {total_lines:,}')
    print()

    # Create chunks
    print('✂️  Chunking file for analysis...')
    chunks = []
    for i in range(0, total_lines, chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_text = ''.join(chunk_lines)
        chunks.append({
            'start_line': i + 1,
            'end_line': min(i + chunk_size, total_lines),
            'text': chunk_text,
            'size': len(chunk_text)
        })

    print(f'   ✅ Created {len(chunks)} chunks')
    print()

    # Analyze each chunk
    print('🚀 Beginning chunk-by-chunk analysis...')
    print('   Focus areas: Complexity, Memory Safety, Security, Robustness')
    print()

    results = []
    total_issues = 0
    critical_issues = 0

    for idx, chunk in enumerate(chunks, 1):
        print(f'📊 Chunk {idx}/{len(chunks)} (lines {chunk["start_line"]}-{chunk["end_line"]})')

        try:
            # Rate limit protection
            if idx > 1:
                delay = 65  # 65 seconds to stay under 30K tokens/min rate limit
                print(f'   ⏱️  Rate limit delay: {delay}s...')
                await asyncio.sleep(delay)

            # Analyze this chunk with comprehensive dimensions
            result = await analyze_mql5_code(
                chunk['text'],
                mode='analyze',  # Analyze only (faster than fix mode)
                proof_level='detailed',  # Detailed proof level for production code
                dimensions=['complexity', 'memory', 'security', 'robustness']
            )

            # Extract issues from result
            chunk_issues = 0
            chunk_critical = 0

            if isinstance(result, dict):
                if 'issues' in result:
                    chunk_issues = len(result['issues'])
                    chunk_critical = len([i for i in result['issues'] if i.get('severity') == 'critical'])
                elif 'analysis' in result and isinstance(result['analysis'], dict):
                    if 'issues' in result['analysis']:
                        chunk_issues = len(result['analysis']['issues'])
                        chunk_critical = len([i for i in result['analysis']['issues']
                                             if i.get('severity') == 'critical'])

            total_issues += chunk_issues
            critical_issues += chunk_critical

            results.append({
                'chunk_id': idx,
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'analysis': result,
                'issues_found': chunk_issues,
                'critical_issues': chunk_critical,
                'status': 'success'
            })

            print(f'   ✅ Analysis complete - Issues: {chunk_issues} (Critical: {chunk_critical})')
            print()

        except Exception as e:
            print(f'   ❌ Analysis failed: {e}')
            results.append({
                'chunk_id': idx,
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'error': str(e),
                'status': 'failed'
            })
            print()

    # Generate comprehensive summary
    print()
    print('=' * 80)
    print('📋 ANALYSIS RESULTS SUMMARY')
    print('=' * 80)

    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])

    print(f'Total Chunks:      {len(chunks)}')
    print(f'Analyzed:          {successful}')
    print(f'Failed:            {failed}')
    print(f'Total Issues:      {total_issues}')
    print(f'Critical Issues:   {critical_issues}')
    print()

    # Determine reliability rating
    if critical_issues == 0 and total_issues <= 5:
        rating = '✅ PRODUCTION READY - CERTIFIED'
        reliability_score = 10.0
    elif critical_issues == 0 and total_issues <= 15:
        rating = '✅ PRODUCTION READY - Minor improvements recommended'
        reliability_score = 9.0
    elif critical_issues <= 2 and total_issues <= 30:
        rating = '⚠️  NEARLY PRODUCTION READY - Address critical issues'
        reliability_score = 7.5
    else:
        rating = '❌ NOT PRODUCTION READY - Significant issues found'
        reliability_score = 5.0

    print(f'Reliability Score: {reliability_score}/10')
    print(f'Certification:     {rating}')
    print('=' * 80)
    print()

    summary = {
        'file': str(file_path),
        'analysis_timestamp': datetime.now().isoformat(),
        'file_metrics': {
            'total_lines': total_lines,
            'file_size_bytes': file_path.stat().st_size
        },
        'chunk_metrics': {
            'total_chunks': len(chunks),
            'successful_chunks': successful,
            'failed_chunks': failed,
            'chunk_size': chunk_size
        },
        'issue_summary': {
            'total_issues': total_issues,
            'critical_issues': critical_issues
        },
        'reliability': {
            'score': reliability_score,
            'rating': rating,
            'production_ready': critical_issues == 0 and total_issues <= 15
        },
        'chunk_results': results
    }

    return summary


async def main():
    """Main entry point."""
    file_path = Path('/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE/LeadingExtremaIndicator_LIVE.mq5')

    if not file_path.exists():
        print(f'❌ Error: File not found: {file_path}')
        return 1

    try:
        # Run chunked analysis
        summary = await analyze_in_chunks(file_path, chunk_size=800)

        # Save results
        output_file = agent_dir / 'live_indicator_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f'💾 Full results saved to: {output_file}')
        print()

        # Display final verdict
        print('=' * 80)
        print('🎯 FINAL VERDICT')
        print('=' * 80)
        print(f"File:              {file_path.name}")
        print(f"Reliability Score: {summary['reliability']['score']}/10")
        print(f"Status:            {summary['reliability']['rating']}")
        print(f"Production Ready:  {'YES' if summary['reliability']['production_ready'] else 'NO'}")
        print('=' * 80)

        if summary['chunk_metrics']['successful_chunks'] == summary['chunk_metrics']['total_chunks']:
            return 0
        else:
            print(f"\n⚠️  Warning: {summary['chunk_metrics']['failed_chunks']} chunks failed analysis")
            return 1

    except Exception as e:
        print(f'❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
