"""
Comprehensive Multi-Agent Analysis for RIGGWIRE-EA-FTMO-LIVE
Analyzes all MQL5 files for unused logic, dead code, and issues
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from tools import (
        parse_mql5_code,
        analyze_code_quality,
        detect_dead_code,
        find_unused_functions
    )
except ImportError as e:
    print(f"Warning: Could not import tools: {e}")
    print("Running in analysis-only mode...")

# Target directory - use absolute path for Windows
if os.name == 'nt':
    FTMO_LIVE_DIR = Path(r"C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO-LIVE")
else:
    FTMO_LIVE_DIR = Path(__file__).parent.parent.parent / "RIGGWIRE-EA-FTMO-LIVE"

class FTMOLiveAnalyzer:
    """Comprehensive analyzer for FTMO-LIVE directory"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "directory": str(FTMO_LIVE_DIR),
            "files_analyzed": [],
            "total_issues": 0,
            "unused_logic": [],
            "dead_code": [],
            "all_findings": []
        }

    def find_all_mql5_files(self):
        """Find all .mq5 and .mqh files"""
        mq5_files = list(FTMO_LIVE_DIR.glob("*.mq5"))
        mqh_files = list(FTMO_LIVE_DIR.glob("*.mqh"))
        return sorted(mq5_files + mqh_files)

    def detect_unused_logic(self, file_path):
        """Detect unused logic patterns in MQL5 code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            unused_patterns = []

            # Pattern 1: Commented out code blocks
            lines = content.split('\n')
            comment_block_start = None
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('//') and len(stripped) > 3:
                    # Check if it looks like commented code
                    code_like = any(keyword in stripped for keyword in [
                        'if(', 'for(', 'while(', 'int ', 'double ', 'bool ',
                        'void ', 'return', '==', '!=', '&&', '||'
                    ])
                    if code_like:
                        unused_patterns.append({
                            "type": "commented_code",
                            "line": i,
                            "content": line.strip()[:100],
                            "severity": "low"
                        })

            # Pattern 2: Unused variables (declared but never used)
            # Simple heuristic: look for variable declarations
            import re
            var_declarations = re.findall(r'(int|double|bool|string|datetime)\s+(\w+)\s*=', content)
            for var_type, var_name in var_declarations:
                # Count occurrences (simple check)
                if content.count(var_name) <= 2:  # Only declaration and maybe one more
                    unused_patterns.append({
                        "type": "potentially_unused_variable",
                        "variable": var_name,
                        "var_type": var_type,
                        "severity": "medium"
                    })

            # Pattern 3: Empty functions
            empty_funcs = re.findall(r'(\w+\s+\w+\([^)]*\)\s*\{\s*\})', content)
            for func in empty_funcs:
                unused_patterns.append({
                    "type": "empty_function",
                    "content": func[:100],
                    "severity": "medium"
                })

            # Pattern 4: Unreachable code after return
            unreachable = re.findall(r'return[^;]*;[^}]+\n\s+\w+', content)
            for code in unreachable:
                unused_patterns.append({
                    "type": "unreachable_code",
                    "content": code[:100],
                    "severity": "high"
                })

            return unused_patterns

        except Exception as e:
            return [{"type": "error", "message": str(e), "severity": "error"}]

    def analyze_file(self, file_path):
        """Analyze a single file"""
        print(f"\n{'='*60}")
        print(f"Analyzing: {file_path.name}")
        print(f"{'='*60}")

        file_result = {
            "file": str(file_path),
            "file_name": file_path.name,
            "size_kb": file_path.stat().st_size / 1024,
            "issues": [],
            "unused_logic": []
        }

        # Detect unused logic
        unused = self.detect_unused_logic(file_path)
        file_result["unused_logic"] = unused

        print(f"  Unused logic patterns found: {len(unused)}")
        for pattern in unused:
            print(f"    - {pattern['type']}: {pattern.get('content', pattern.get('variable', 'N/A'))[:60]}")

        # Try to parse and analyze
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Count lines
            lines = len(code.split('\n'))
            file_result["lines"] = lines

            # Look for specific patterns
            patterns = {
                "TODO": code.count("TODO"),
                "FIXME": code.count("FIXME"),
                "XXX": code.count("XXX"),
                "HACK": code.count("HACK"),
                "BUG": code.count("BUG"),
                "deprecated": code.lower().count("deprecated"),
                "magic_numbers": len([1 for line in code.split('\n')
                                     if any(num in line for num in ['100', '1000', '999', '9999'])]),
            }
            file_result["patterns"] = patterns

            print(f"  Lines: {lines}")
            print(f"  Patterns: {patterns}")

        except Exception as e:
            file_result["error"] = str(e)
            print(f"  Error: {e}")

        self.results["files_analyzed"].append(file_result)
        return file_result

    def analyze_all(self):
        """Analyze all files in the directory"""
        files = self.find_all_mql5_files()

        print(f"\n{'#'*60}")
        print(f"# MT5 INFINITE RELIABILITY AGENT")
        print(f"# FTMO-LIVE COMPREHENSIVE ANALYSIS")
        print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")
        print(f"\nFound {len(files)} MQL5 files to analyze\n")

        for file_path in files:
            self.analyze_file(file_path)

        # Generate summary
        self.generate_summary()

        # Save results
        self.save_results()

    def generate_summary(self):
        """Generate analysis summary"""
        print(f"\n{'='*60}")
        print(f"ANALYSIS SUMMARY")
        print(f"{'='*60}")

        total_unused = sum(len(f["unused_logic"]) for f in self.results["files_analyzed"])
        total_lines = sum(f.get("lines", 0) for f in self.results["files_analyzed"])

        print(f"\nFiles Analyzed: {len(self.results['files_analyzed'])}")
        print(f"Total Lines: {total_lines:,}")
        print(f"Total Unused Logic Patterns: {total_unused}")

        # Break down by file
        print(f"\n{'File':<40} {'Lines':>8} {'Unused':>8}")
        print(f"{'-'*60}")
        for file_result in self.results["files_analyzed"]:
            name = file_result["file_name"]
            lines = file_result.get("lines", 0)
            unused = len(file_result["unused_logic"])
            print(f"{name:<40} {lines:>8} {unused:>8}")

        # Summary statistics
        self.results["summary"] = {
            "total_files": len(self.results["files_analyzed"]),
            "total_lines": total_lines,
            "total_unused_patterns": total_unused,
            "files_with_issues": sum(1 for f in self.results["files_analyzed"] if len(f["unused_logic"]) > 0)
        }

    def save_results(self):
        """Save results to JSON file"""
        output_file = Path(__file__).parent / "ftmo_live_analysis_results.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}\n")

        # Also create markdown report
        self.create_markdown_report()

    def create_markdown_report(self):
        """Create comprehensive markdown report"""
        report_file = Path(__file__).parent / "FTMO_LIVE_ANALYSIS_REPORT.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# RIGGWIRE-EA-FTMO-LIVE Comprehensive Analysis\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")
            f.write(f"**Directory:** `{self.results['directory']}`\n\n")

            f.write("## Executive Summary\n\n")
            summary = self.results["summary"]
            f.write(f"- **Files Analyzed:** {summary['total_files']}\n")
            f.write(f"- **Total Lines:** {summary['total_lines']:,}\n")
            f.write(f"- **Unused Logic Patterns:** {summary['total_unused_patterns']}\n")
            f.write(f"- **Files with Issues:** {summary['files_with_issues']}\n\n")

            f.write("## Files Analyzed\n\n")
            f.write("| File | Lines | Size (KB) | Unused Patterns |\n")
            f.write("|------|-------|-----------|------------------|\n")

            for file_result in self.results["files_analyzed"]:
                name = file_result["file_name"]
                lines = file_result.get("lines", 0)
                size = file_result.get("size_kb", 0)
                unused = len(file_result["unused_logic"])
                f.write(f"| {name} | {lines} | {size:.1f} | {unused} |\n")

            f.write("\n## Detailed Findings\n\n")

            for file_result in self.results["files_analyzed"]:
                if len(file_result["unused_logic"]) > 0:
                    f.write(f"### {file_result['file_name']}\n\n")

                    # Group by type
                    by_type = {}
                    for pattern in file_result["unused_logic"]:
                        ptype = pattern["type"]
                        if ptype not in by_type:
                            by_type[ptype] = []
                        by_type[ptype].append(pattern)

                    for ptype, patterns in by_type.items():
                        f.write(f"#### {ptype.replace('_', ' ').title()} ({len(patterns)})\n\n")
                        for pattern in patterns[:10]:  # Limit to first 10
                            f.write(f"- **Severity:** {pattern['severity']}\n")
                            if 'line' in pattern:
                                f.write(f"  - **Line:** {pattern['line']}\n")
                            if 'content' in pattern:
                                f.write(f"  - **Content:** `{pattern['content'][:80]}...`\n")
                            if 'variable' in pattern:
                                f.write(f"  - **Variable:** `{pattern['variable']}`\n")
                            f.write("\n")

                    f.write("\n")

        print(f"Markdown report saved to: {report_file}\n")

def main():
    """Main entry point"""
    analyzer = FTMOLiveAnalyzer()
    analyzer.analyze_all()

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Review ftmo_live_analysis_results.json for raw data")
    print("2. Review FTMO_LIVE_ANALYSIS_REPORT.md for detailed findings")
    print("3. Address high-severity unused logic patterns")
    print("4. Remove dead code and commented code blocks")
    print("\n")

if __name__ == "__main__":
    main()
