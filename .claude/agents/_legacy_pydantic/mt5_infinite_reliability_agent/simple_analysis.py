#!/usr/bin/env python3
"""
Simplified MT5 Analysis - Direct tool usage without agent framework
Analyzes LeadingExtremaIndicator_LIVE.mq5 for reliability metrics.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import re
import hashlib

# Add parent directory to path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir.parent))


def parse_mql5_code(code: str) -> dict:
    """Parse MQL5 source code into structured analysis."""
    functions = []
    variables = []
    patterns = {"loops": 0, "conditions": 0, "indicators": 0, "arrays": 0}

    # Extract functions
    func_pattern = r'(?:void|int|double|string|bool|datetime)\s+(\w+)\s*\([^)]*\)\s*\{'
    functions = re.findall(func_pattern, code)

    # Extract global variables
    var_pattern = r'(?:input|static|extern|const)\s+(?:int|double|string|bool|datetime|color)\s+(\w+)'
    variables = re.findall(var_pattern, code)

    # Count patterns
    patterns["loops"] = len(re.findall(r'\b(for|while)\b', code))
    patterns["conditions"] = len(re.findall(r'\bif\b', code))
    patterns["indicators"] = len(re.findall(r'i(?:MA|RSI|MACD|Stochastic|ATR|Bands)', code))
    patterns["arrays"] = len(re.findall(r'\w+\s*\[\s*\]', code))

    # Check for error handling
    error_handling = len(re.findall(r'GetLastError\(\)', code))

    # Check for memory operations
    array_operations = len(re.findall(r'ArrayResize|ArrayCopy|ArrayFree', code))

    # Check for buffer safety
    buffer_checks = len(re.findall(r'ArraySize|ArrayRange|Bars', code))

    return {
        "ast": {
            "type": "Program",
            "functions": functions[:20],  # First 20 for readability
            "variables": variables[:20]
        },
        "stats": {
            "function_count": len(functions),
            "variable_count": len(variables),
            "line_count": len(code.split('\n'))
        },
        "patterns": patterns,
        "safety": {
            "error_handling_count": error_handling,
            "array_operations": array_operations,
            "buffer_checks": buffer_checks
        },
        "hash": hashlib.sha256(code.encode()).hexdigest()[:16]
    }


def analyze_complexity(parsed: dict) -> dict:
    """Analyze code complexity metrics."""
    stats = parsed["stats"]
    patterns = parsed["patterns"]

    # Calculate cyclomatic complexity estimate
    total_decision_points = patterns["loops"] + patterns["conditions"]
    avg_complexity_per_func = total_decision_points / max(stats["function_count"], 1)

    # Complexity rating
    if avg_complexity_per_func <= 10:
        complexity_rating = "Low"
        score = 10
    elif avg_complexity_per_func <= 20:
        complexity_rating = "Moderate"
        score = 7
    else:
        complexity_rating = "High"
        score = 4

    return {
        "dimension": "complexity",
        "metrics": {
            "total_functions": stats["function_count"],
            "total_decision_points": total_decision_points,
            "avg_complexity_per_function": round(avg_complexity_per_func, 2),
            "lines_of_code": stats["line_count"]
        },
        "rating": complexity_rating,
        "score": score,
        "issues": [] if score >= 7 else [
            {
                "severity": "medium",
                "message": f"Average cyclomatic complexity is {avg_complexity_per_func:.1f}, consider refactoring complex functions"
            }
        ]
    }


def analyze_memory_safety(parsed: dict, code: str) -> dict:
    """Analyze memory safety and buffer handling."""
    safety = parsed["safety"]
    patterns = parsed["patterns"]

    issues = []
    score = 10

    # Check array usage vs safety checks
    if patterns["arrays"] > 0:
        safety_ratio = safety["buffer_checks"] / patterns["arrays"]
        if safety_ratio < 0.5:
            issues.append({
                "severity": "high",
                "message": f"Low buffer safety check ratio: {safety_ratio:.2f} (found {safety['buffer_checks']} checks for {patterns['arrays']} arrays)"
            })
            score -= 3

    # Check for ArraySetAsSeries usage (important for correct buffer indexing)
    if 'ArraySetAsSeries' not in code:
        issues.append({
            "severity": "low",
            "message": "ArraySetAsSeries not found - ensure indicator buffers are indexed correctly"
        })
        score -= 1

    # Check for memory management
    if safety["array_operations"] > 0:
        score += 1  # Bonus for proper memory management

    rating = "Excellent" if score >= 9 else "Good" if score >= 7 else "Fair" if score >= 5 else "Poor"

    return {
        "dimension": "memory_safety",
        "metrics": {
            "array_count": patterns["arrays"],
            "buffer_checks": safety["buffer_checks"],
            "array_operations": safety["array_operations"],
            "safety_ratio": round(safety["buffer_checks"] / max(patterns["arrays"], 1), 2)
        },
        "rating": rating,
        "score": min(score, 10),
        "issues": issues
    }


def analyze_security(parsed: dict, code: str) -> dict:
    """Analyze security and input validation."""
    issues = []
    score = 10

    # Check for input validation
    has_input_validation = 'OnInit' in code and ('return(INIT_' in code)
    if has_input_validation:
        score += 1
    else:
        issues.append({
            "severity": "medium",
            "message": "No explicit input validation found in OnInit"
        })
        score -= 2

    # Check for error handling
    error_handling = parsed["safety"]["error_handling_count"]
    if error_handling < 3:
        issues.append({
            "severity": "low",
            "message": f"Limited error handling found ({error_handling} GetLastError calls)"
        })
        score -= 1

    # Check for dangerous functions
    dangerous_patterns = ['system(', 'exec(', 'FileDelete(']
    for pattern in dangerous_patterns:
        if pattern in code:
            issues.append({
                "severity": "critical",
                "message": f"Potentially dangerous function found: {pattern}"
            })
            score -= 5

    rating = "Excellent" if score >= 9 else "Good" if score >= 7 else "Fair" if score >= 5 else "Poor"

    return {
        "dimension": "security",
        "metrics": {
            "input_validation": has_input_validation,
            "error_handling_points": error_handling
        },
        "rating": rating,
        "score": max(min(score, 10), 0),
        "issues": issues
    }


def analyze_robustness(parsed: dict, code: str) -> dict:
    """Analyze code robustness and edge case handling."""
    issues = []
    score = 10

    # Check for division operations (potential divide-by-zero)
    divisions = len(re.findall(r'\w+\s*/\s*\w+', code))
    zero_checks = len(re.findall(r'(?:if|while)\s*\([^)]*(?:!=|>)\s*0', code))

    if divisions > zero_checks * 2:
        issues.append({
            "severity": "medium",
            "message": f"Potential divide-by-zero risk: {divisions} divisions, {zero_checks} zero checks"
        })
        score -= 2

    # Check for Bars validation
    if 'Bars' in code and 'rates_total' in code:
        score += 1  # Good practice for OnCalculate

    # Check for proper OnCalculate signature
    if 'OnCalculate' in code:
        if 'prev_calculated' in code:
            score += 1  # Proper indicator state management
        else:
            issues.append({
                "severity": "medium",
                "message": "OnCalculate doesn't use prev_calculated for optimization"
            })
            score -= 1

    rating = "Excellent" if score >= 9 else "Good" if score >= 7 else "Fair" if score >= 5 else "Poor"

    return {
        "dimension": "robustness",
        "metrics": {
            "division_operations": divisions,
            "zero_checks": zero_checks,
            "has_bars_validation": 'Bars' in code
        },
        "rating": rating,
        "score": min(score, 10),
        "issues": issues
    }


def generate_reliability_report(file_path: Path) -> dict:
    """Generate comprehensive reliability report."""
    print('=' * 80)
    print('MT5 INFINITE RELIABILITY AGENT - DIRECT ANALYSIS')
    print('=' * 80)
    print(f'Target File:   {file_path.name}')
    print(f'File Size:     {file_path.stat().st_size:,} bytes')
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    print()

    # Read code
    print('Reading source code...')
    code = file_path.read_text(encoding='utf-8')
    print(f'✅ Loaded {len(code):,} characters')
    print()

    # Parse code
    print('Parsing MQL5 structure...')
    parsed = parse_mql5_code(code)
    print(f'✅ Found {parsed["stats"]["function_count"]} functions, {parsed["stats"]["variable_count"]} variables')
    print()

    # Run analyses
    print('Running multi-dimensional analysis...')
    analyses = {
        'complexity': analyze_complexity(parsed),
        'memory_safety': analyze_memory_safety(parsed, code),
        'security': analyze_security(parsed, code),
        'robustness': analyze_robustness(parsed, code)
    }
    print('✅ Analysis complete')
    print()

    # Calculate overall scores
    total_issues = sum(len(a['issues']) for a in analyses.values())
    critical_issues = sum(len([i for i in a['issues'] if i['severity'] == 'critical']) for a in analyses.values())
    avg_score = sum(a['score'] for a in analyses.values()) / len(analyses)

    # Determine certification
    if critical_issues == 0 and avg_score >= 9.0:
        certification = '✅ PRODUCTION READY - CERTIFIED'
        production_ready = True
    elif critical_issues == 0 and avg_score >= 7.5:
        certification = '✅ PRODUCTION READY - Minor improvements recommended'
        production_ready = True
    elif critical_issues <= 1 and avg_score >= 6.0:
        certification = '⚠️  NEARLY PRODUCTION READY - Address issues before deployment'
        production_ready = False
    else:
        certification = '❌ NOT PRODUCTION READY - Significant issues found'
        production_ready = False

    # Build report
    report = {
        'file': str(file_path),
        'analysis_timestamp': datetime.now().isoformat(),
        'file_metrics': {
            'total_lines': parsed['stats']['line_count'],
            'file_size_bytes': file_path.stat().st_size,
            'function_count': parsed['stats']['function_count'],
            'variable_count': parsed['stats']['variable_count']
        },
        'code_patterns': parsed['patterns'],
        'dimensional_analysis': analyses,
        'summary': {
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'average_score': round(avg_score, 2),
            'certification': certification,
            'production_ready': production_ready
        }
    }

    return report


def main():
    """Main entry point."""
    file_path = Path('/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE/LeadingExtremaIndicator_LIVE.mq5')

    if not file_path.exists():
        print(f'❌ Error: File not found: {file_path}')
        return 1

    try:
        # Generate report
        report = generate_reliability_report(file_path)

        # Display results
        print('=' * 80)
        print('ANALYSIS RESULTS')
        print('=' * 80)
        print()

        for dimension, analysis in report['dimensional_analysis'].items():
            print(f'{dimension.upper().replace("_", " ")}:')
            print(f'  Rating: {analysis["rating"]}')
            print(f'  Score:  {analysis["score"]}/10')
            if analysis['issues']:
                print(f'  Issues: {len(analysis["issues"])}')
                for issue in analysis['issues']:
                    print(f'    - [{issue["severity"].upper()}] {issue["message"]}')
            else:
                print('  Issues: None')
            print()

        print('=' * 80)
        print('FINAL VERDICT')
        print('=' * 80)
        print(f'Average Score:     {report["summary"]["average_score"]}/10')
        print(f'Total Issues:      {report["summary"]["total_issues"]}')
        print(f'Critical Issues:   {report["summary"]["critical_issues"]}')
        print(f'Certification:     {report["summary"]["certification"]}')
        print(f'Production Ready:  {"YES" if report["summary"]["production_ready"] else "NO"}')
        print('=' * 80)
        print()

        # Save report
        output_file = agent_dir / 'reliability_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f'💾 Full report saved to: {output_file}')

        return 0 if report['summary']['production_ready'] else 1

    except Exception as e:
        print(f'❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
