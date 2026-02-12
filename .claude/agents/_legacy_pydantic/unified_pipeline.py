#!/usr/bin/env python3
"""
Unified Pipeline Orchestrator for Clang-Tidy + BLITZFIRE Integration
====================================================================

This is the permanent integration point between:
- clang_tidy_ai_agent: Code quality, safety, and compliance
- blitzfire_cpp_optimizer: Performance optimization and speed improvements

Usage:
    python3 unified_pipeline.py fix-and-optimize --file src/main.cpp --level advanced
    python3 unified_pipeline.py analyze --file src/main.cpp
    python3 unified_pipeline.py benchmark --before original.cpp --after optimized.cpp

The pipeline ensures:
1. Zero clang-tidy warnings before optimization
2. Performance improvements without breaking quality
3. Complete validation and reporting
4. Automatic backup and rollback capabilities
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the shared integration
sys.path.append('/IdeaProjects/wire_ground/.claude/agents')
from shared_integration import (
    PipelineConfig,
    PipelineResult,
    IntegratedPipeline,
    optimize_with_quality,
    optimize_with_quality_sync,
    INTEGRATION_ENABLED
)


class UnifiedPipelineCLI:
    """CLI interface for the unified Clang-Tidy + BLITZFIRE pipeline."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Unified Clang-Tidy + BLITZFIRE C++ Optimization Pipeline",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Complete fix and optimization workflow
  python3 unified_pipeline.py fix-and-optimize --file src/main.cpp --level advanced
  
  # Quick optimization only
  python3 unified_pipeline.py fix-and-optimize --file src/main.cpp --level quick_wins
  
  # Analysis only (no modifications)
  python3 unified_pipeline.py analyze --file src/main.cpp
  
  # Benchmark performance comparison
  python3 unified_pipeline.py benchmark --before backup.cpp --after optimized.cpp
  
  # Batch process multiple files
  python3 unified_pipeline.py fix-and-optimize --files src/*.cpp --level advanced
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Fix and optimize command
        fix_parser = subparsers.add_parser(
            'fix-and-optimize',
            help='Complete pipeline: fix clang-tidy warnings then optimize performance'
        )
        fix_parser.add_argument('--file', type=str, help='Single C++ source file')
        fix_parser.add_argument('--files', type=str, help='Pattern for multiple files (e.g., src/*.cpp)')
        fix_parser.add_argument('--level', type=str, default='advanced',
                              choices=['quick_wins', 'algorithmic', 'advanced', 'extreme'],
                              help='BLITZFIRE optimization level')
        fix_parser.add_argument('--output-dir', type=str, default='.claude/agents/pipeline_output',
                              help='Output directory for reports and backups')
        fix_parser.add_argument('--strict', action='store_true', default=True,
                              help='Fail if any warnings remain (default: true)')
        fix_parser.add_argument('--no-backup', action='store_true',
                              help='Skip backing up original files')
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Analyze code quality and optimization potential without modifications'
        )
        analyze_parser.add_argument('--file', type=str, required=True, help='C++ source file')
        analyze_parser.add_argument('--checks', type=str, 
                                  default='concurrency-*,cert-*,performance-*,readability-*',
                                  help='Clang-tidy checks to run')
        analyze_parser.add_argument('--report', type=str, help='Output report file (JSON)')
        
        # Benchmark command
        benchmark_parser = subparsers.add_parser(
            'benchmark',
            help='Compare performance between two versions of code'
        )
        benchmark_parser.add_argument('--before', type=str, required=True,
                                    help='Original C++ file (before optimization)')
        benchmark_parser.add_argument('--after', type=str, required=True,
                                    help='Optimized C++ file (after optimization)')
        benchmark_parser.add_argument('--iterations', type=int, default=10,
                                    help='Number of benchmark iterations')
        
        # Status command
        status_parser = subparsers.add_parser(
            'status',
            help='Show integration status and available agents'
        )
        
        return parser
    
    async def cmd_fix_and_optimize(self, args) -> int:
        """Execute the complete fix and optimize pipeline."""
        if not args.file and not args.files:
            logger.error("Must specify either --file or --files")
            return 1
        
        files_to_process = []
        
        if args.file:
            files_to_process = [args.file]
        elif args.files:
            import glob
            files_to_process = glob.glob(args.files)
            if not files_to_process:
                logger.error(f"No files found matching pattern: {args.files}")
                return 1
        
        logger.info(f"🚀 Processing {len(files_to_process)} file(s) with {args.level} optimization")
        
        all_results = {}
        success_count = 0
        
        for file_path in files_to_process:
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                continue
                
            logger.info(f"📁 Processing: {file_path}")
            
            try:
                config = PipelineConfig(
                    source_file=file_path,
                    output_dir=args.output_dir,
                    optimization_level=args.level,
                    strict_mode=args.strict,
                    backup_original=not args.no_backup,
                    generate_report=True
                )
                
                pipeline = IntegratedPipeline(config)
                result = await pipeline.run_pipeline()
                
                all_results[file_path] = {
                    "success": result.success,
                    "warnings_fixed": result.warnings_fixed,
                    "performance_improvement": result.performance_improvement,
                    "stage_completed": result.stage_completed.value,
                    "errors": result.errors
                }
                
                if result.success:
                    success_count += 1
                    logger.info(f"✅ {file_path}: Success - {result.warnings_fixed} warnings fixed, {result.performance_improvement}% faster")
                else:
                    logger.error(f"❌ {file_path}: Failed - {', '.join(result.errors)}")
                    
            except Exception as e:
                logger.error(f"❌ {file_path}: Exception - {e}")
                all_results[file_path] = {"success": False, "error": str(e)}
        
        # Summary
        total_files = len(files_to_process)
        logger.info(f"""
🎯 Pipeline Summary
==================
✅ Successful: {success_count}/{total_files}
❌ Failed: {total_files - success_count}/{total_files}
📁 Output: {args.output_dir}
""")
        
        # Save comprehensive results
        results_file = f"{args.output_dir}/unified_pipeline_results.json"
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "command": "fix-and-optimize",
                "optimization_level": args.level,
                "files_processed": total_files,
                "successful": success_count,
                "results": all_results
            }, f, indent=2)
        
        logger.info(f"📋 Detailed results saved to: {results_file}")
        
        return 0 if success_count == total_files else 1
    
    async def cmd_analyze(self, args) -> int:
        """Analyze code without making modifications."""
        if not Path(args.file).exists():
            logger.error(f"File not found: {args.file}")
            return 1
        
        logger.info(f"🔍 Analyzing: {args.file}")
        
        try:
            # Import clang-tidy agent for analysis
            sys.path.append('/IdeaProjects/wire_ground/.claude/agents')
            from clang_tidy_ai_agent.agent import ClangTidyFactoryOrchestrator
            from clang_tidy_ai_agent.models import ClangTidyDependencies
            
            deps = ClangTidyDependencies(
                source_file=args.file,
                clang_tidy_checks=args.checks
            )
            
            orchestrator = ClangTidyFactoryOrchestrator(deps)
            analysis = await orchestrator.analyze_file_simple(args.file)
            
            # Also get BLITZFIRE potential
            from blitzfire_cpp_optimizer.agent import analyze_cpp_performance
            
            with open(args.file, 'r') as f:
                code = f.read()
            
            blitzfire_analysis = await analyze_cpp_performance(
                ctx=None,
                code=code,
                optimization_level="advanced"
            )
            
            # Combined report
            report = {
                "file": args.file,
                "timestamp": datetime.now().isoformat(),
                "clang_tidy_analysis": analysis,
                "blitzfire_potential": blitzfire_analysis,
                "integration_available": INTEGRATION_ENABLED
            }
            
            print(analysis)
            print("\n🚀 BLITZFIRE Optimization Potential:")
            print(f"  - Bottlenecks Found: {blitzfire_analysis['analysis']['optimization_opportunities']}")
            print(f"  - Complexity Analysis: {blitzfire_analysis['analysis']['complexity_analysis']}")
            
            if args.report:
                with open(args.report, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"📋 Report saved to: {args.report}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return 1
    
    async def cmd_benchmark(self, args) -> int:
        """Benchmark performance comparison."""
        if not Path(args.before).exists():
            logger.error(f"Before file not found: {args.before}")
            return 1
        
        if not Path(args.after).exists():
            logger.error(f"After file not found: {args.after}")
            return 1
        
        logger.info(f"⚡ Benchmarking: {args.before} vs {args.after}")
        
        try:
            # Import benchmark tools
            from blitzfire_cpp_optimizer.agent import generate_performance_benchmark
            
            with open(args.before, 'r') as f:
                before_code = f.read()
            
            with open(args.after, 'r') as f:
                after_code = f.read()
            
            # Generate benchmark
            benchmark_result = await generate_performance_benchmark(
                ctx=None,
                original_code=before_code,
                optimized_code=after_code,
                iterations=args.iterations
            )
            
            print(f"""
⚡ Performance Benchmark Results
================================
📁 Before: {args.before}
📁 After:  {args.after}
🔄 Iterations: {args.iterations}

{benchmark_result.get('benchmark_report', 'Benchmark results not available')}
""")
            
            return 0
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return 1
    
    async def cmd_status(self, args) -> int:
        """Show integration status."""
        print(f"""
🔗 Unified Pipeline Status
=========================
📊 Integration Enabled: {INTEGRATION_ENABLED}
🔧 Clang-Tidy Agent: Available
🚀 BLITZFIRE Optimizer: Available
📋 Shared Pipeline: Available

🎯 Available Commands:
  fix-and-optimize  - Complete quality + optimization pipeline
  analyze          - Code analysis without modifications
  benchmark        - Performance comparison
  status          - This status information

🔍 Quick Start:
  python3 unified_pipeline.py fix-and-optimize --file src/main.cpp --level advanced
""")
        return 0
    
    async def run(self, args=None) -> int:
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        # Dispatch to command handlers
        if parsed_args.command == 'fix-and-optimize':
            return await self.cmd_fix_and_optimize(parsed_args)
        elif parsed_args.command == 'analyze':
            return await self.cmd_analyze(parsed_args)
        elif parsed_args.command == 'benchmark':
            return await self.cmd_benchmark(parsed_args)
        elif parsed_args.command == 'status':
            return await self.cmd_status(parsed_args)
        else:
            logger.error(f"Unknown command: {parsed_args.command}")
            return 1


def main():
    """Main entry point."""
    cli = UnifiedPipelineCLI()
    
    try:
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()