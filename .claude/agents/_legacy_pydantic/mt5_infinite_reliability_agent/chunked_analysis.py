#!/usr/bin/env python3
"""
Chunked MT5 Analysis - Process large files in rate-limit-friendly chunks.
Handles files that exceed API rate limits by analyzing in sections.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import json

# Add parent directory to path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))

from mt5_infinite_reliability_agent.agent import agent, analyze_mql5_code
from mt5_infinite_reliability_agent.dependencies import AgentDependencies


async def analyze_in_chunks(file_path: Path, chunk_size: int = 1000) -> Dict:
    """
    Analyze large MQL5 file in chunks to respect rate limits.

    Args:
        file_path: Path to MQL5 file
        chunk_size: Lines per chunk (default: 1000 lines ≈ 10-15K tokens)

    Returns:
        Combined analysis results
    """
    print('=' * 70)
    print('🔍 MT5 INFINITE RELIABILITY AGENT - CHUNKED ANALYSIS')
    print('=' * 70)
    print(f'File: {file_path.name}')
    print(f'Size: {file_path.stat().st_size:,} bytes')
    print(f'Chunk Size: {chunk_size} lines')
    print('=' * 70)
    print()

    # Read and split file into chunks
    print('📖 Reading and chunking file...')
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f'✅ Total lines: {total_lines:,}')

    # Create chunks
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

    print(f'✅ Created {len(chunks)} chunks')
    print()

    # Analyze each chunk
    results = []
    for idx, chunk in enumerate(chunks, 1):
        print(f'🚀 Analyzing chunk {idx}/{len(chunks)} (lines {chunk["start_line"]}-{chunk["end_line"]})...')

        try:
            # Add delay between chunks to respect rate limits
            if idx > 1:
                delay = 65  # 65 seconds to stay under 30K tokens/min
                print(f'   ⏱️  Waiting {delay}s for rate limit...')
                await asyncio.sleep(delay)

            # Analyze this chunk
            result = await analyze_mql5_code(
                chunk['text'],
                mode='analyze',  # Just analyze, don't fix (faster)
                proof_level='basic',  # Basic proof for chunks
                dimensions=['complexity', 'memory', 'security', 'robustness']
            )

            results.append({
                'chunk_id': idx,
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'analysis': result,
                'status': 'success'
            })

            print(f'   ✅ Chunk {idx} analyzed')
            print()

        except Exception as e:
            print(f'   ❌ Chunk {idx} failed: {e}')
            results.append({
                'chunk_id': idx,
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'error': str(e),
                'status': 'failed'
            })

    # Combine results
    print()
    print('=' * 70)
    print('📊 ANALYSIS COMPLETE')
    print('=' * 70)
    print(f'Chunks analyzed: {len([r for r in results if r["status"] == "success"])}/{len(chunks)}')
    print(f'Chunks failed: {len([r for r in results if r["status"] == "failed"])}/{len(chunks)}')
    print()

    # Generate summary
    summary = {
        'file': str(file_path),
        'total_lines': total_lines,
        'total_chunks': len(chunks),
        'successful_chunks': len([r for r in results if r['status'] == 'success']),
        'failed_chunks': len([r for r in results if r['status'] == 'failed']),
        'chunk_results': results
    }

    return summary


async def main():
    """Main entry point."""
    file_path = Path('/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/LeadingExtremaIndicator_FIXED.mq5')

    try:
        # Analyze in chunks
        summary = await analyze_in_chunks(file_path, chunk_size=800)  # ~800 lines ≈ 10K tokens

        # Save results
        output_file = agent_dir / 'chunked_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f'📄 Results saved to: {output_file}')
        print()

        print('=' * 70)
        print('🎯 SUMMARY')
        print('=' * 70)
        print(f"File: {file_path.name}")
        print(f"Total Lines: {summary['total_lines']:,}")
        print(f"Chunks Processed: {summary['successful_chunks']}/{summary['total_chunks']}")
        print()

        if summary['successful_chunks'] == summary['total_chunks']:
            print('✅ All chunks analyzed successfully!')
            return 0
        else:
            print(f"⚠️  {summary['failed_chunks']} chunks failed")
            return 1

    except Exception as e:
        print(f'❌ Analysis failed: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
