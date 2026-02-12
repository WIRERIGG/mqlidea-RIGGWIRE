#!/usr/bin/env python3
"""Test Report Generator for Pydantic AI Agents

This script generates comprehensive test reports from CI/CD artifacts.
"""

import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys


class TestReportGenerator:
    """Generate comprehensive test reports from CI/CD artifacts."""
    
    def __init__(self, artifacts_dir: Path, output_dir: Path):
        self.artifacts_dir = Path(artifacts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'agents': {},
            'summary': {
                'total_agents': 0,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'coverage_percent': 0.0,
                'performance_issues': 0
            }
        }
    
    def parse_junit_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML test results."""
        if not xml_file.exists():
            return {}
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Handle both 'testsuites' and 'testsuite' root elements
            if root.tag == 'testsuites':
                testsuites = root.findall('testsuite')
            else:
                testsuites = [root]
            
            results = {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'error_tests': 0,
                'execution_time': 0.0,
                'test_cases': []
            }
            
            for testsuite in testsuites:
                results['total_tests'] += int(testsuite.get('tests', 0))
                results['failed_tests'] += int(testsuite.get('failures', 0))
                results['error_tests'] += int(testsuite.get('errors', 0))
                results['skipped_tests'] += int(testsuite.get('skipped', 0))
                results['execution_time'] += float(testsuite.get('time', 0))
                
                for testcase in testsuite.findall('testcase'):
                    case_data = {
                        'name': testcase.get('name'),
                        'classname': testcase.get('classname'),
                        'time': float(testcase.get('time', 0)),
                        'status': 'passed'
                    }
                    
                    if testcase.find('failure') is not None:
                        case_data['status'] = 'failed'
                        case_data['failure'] = testcase.find('failure').text
                    elif testcase.find('error') is not None:
                        case_data['status'] = 'error'
                        case_data['error'] = testcase.find('error').text
                    elif testcase.find('skipped') is not None:
                        case_data['status'] = 'skipped'
                    
                    results['test_cases'].append(case_data)
            
            results['passed_tests'] = (results['total_tests'] - 
                                     results['failed_tests'] - 
                                     results['error_tests'] - 
                                     results['skipped_tests'])
            
            return results
            
        except ET.ParseError as e:
            print(f"Error parsing {xml_file}: {e}")
            return {}
    
    def parse_coverage_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse coverage XML report."""
        if not xml_file.exists():
            return {}
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            coverage_data = {
                'line_rate': float(root.get('line-rate', 0)) * 100,
                'branch_rate': float(root.get('branch-rate', 0)) * 100,
                'lines_covered': int(root.get('lines-covered', 0)),
                'lines_valid': int(root.get('lines-valid', 0)),
                'branches_covered': int(root.get('branches-covered', 0)),
                'branches_valid': int(root.get('branches-valid', 0)),
                'packages': []
            }
            
            packages = root.find('packages')
            if packages is not None:
                for package in packages.findall('package'):
                    package_data = {
                        'name': package.get('name'),
                        'line_rate': float(package.get('line-rate', 0)) * 100,
                        'branch_rate': float(package.get('branch-rate', 0)) * 100,
                        'classes': []
                    }
                    
                    classes = package.find('classes')
                    if classes is not None:
                        for cls in classes.findall('class'):
                            class_data = {
                                'name': cls.get('name'),
                                'filename': cls.get('filename'),
                                'line_rate': float(cls.get('line-rate', 0)) * 100,
                                'branch_rate': float(cls.get('branch-rate', 0)) * 100
                            }
                            package_data['classes'].append(class_data)
                    
                    coverage_data['packages'].append(package_data)
            
            return coverage_data
            
        except ET.ParseError as e:
            print(f"Error parsing coverage {xml_file}: {e}")
            return {}
    
    def parse_benchmark_json(self, json_file: Path) -> Dict[str, Any]:
        """Parse benchmark JSON results."""
        if not json_file.exists():
            return {}
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract relevant benchmark information
            benchmark_data = {
                'benchmarks': [],
                'machine_info': data.get('machine_info', {}),
                'commit_info': data.get('commit_info', {})
            }
            
            for benchmark in data.get('benchmarks', []):
                bench_info = {
                    'name': benchmark.get('name'),
                    'fullname': benchmark.get('fullname'),
                    'min': benchmark.get('stats', {}).get('min'),
                    'max': benchmark.get('stats', {}).get('max'),
                    'mean': benchmark.get('stats', {}).get('mean'),
                    'stddev': benchmark.get('stats', {}).get('stddev'),
                    'rounds': benchmark.get('stats', {}).get('rounds'),
                    'iterations': benchmark.get('stats', {}).get('iterations')
                }
                benchmark_data['benchmarks'].append(bench_info)
            
            return benchmark_data
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing benchmark {json_file}: {e}")
            return {}
    
    def collect_agent_data(self, agent_name: str):
        """Collect all test data for a specific agent."""
        agent_data = {
            'name': agent_name,
            'unit_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'e2e_tests': {},
            'coverage': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'coverage_percent': 0.0
            }
        }
        
        # Look for test result files
        for artifact_dir in self.artifacts_dir.rglob(f"*{agent_name}*"):
            if not artifact_dir.is_dir():
                continue
                
            # Unit test results
            unit_xml = artifact_dir / "test_results_unit.xml"
            if unit_xml.exists():
                agent_data['unit_tests'] = self.parse_junit_xml(unit_xml)
            
            # Integration test results
            integration_xml = artifact_dir / "test_results_integration.xml"
            if integration_xml.exists():
                agent_data['integration_tests'] = self.parse_junit_xml(integration_xml)
            
            # E2E test results
            e2e_xml = artifact_dir / "test_results_e2e.xml"
            if e2e_xml.exists():
                agent_data['e2e_tests'] = self.parse_junit_xml(e2e_xml)
            
            # Performance test results
            benchmark_json = artifact_dir / "benchmark_results.json"
            if benchmark_json.exists():
                agent_data['performance_tests'] = self.parse_benchmark_json(benchmark_json)
            
            # Coverage results
            coverage_xml = artifact_dir / "coverage.xml"
            if coverage_xml.exists():
                agent_data['coverage'] = self.parse_coverage_xml(coverage_xml)
        
        # Calculate summary
        for test_type in ['unit_tests', 'integration_tests', 'e2e_tests']:
            test_data = agent_data[test_type]
            if test_data:
                agent_data['summary']['total_tests'] += test_data.get('total_tests', 0)
                agent_data['summary']['passed_tests'] += test_data.get('passed_tests', 0)
                agent_data['summary']['failed_tests'] += test_data.get('failed_tests', 0)
        
        if agent_data['coverage']:
            agent_data['summary']['coverage_percent'] = agent_data['coverage'].get('line_rate', 0)
        
        return agent_data
    
    def generate_html_report(self):
        """Generate HTML test report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pydantic AI Agents Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 15px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .summary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
        .summary-card .value { font-size: 32px; font-weight: bold; margin: 0; }
        .agent-section { margin-bottom: 40px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .agent-header { background: #333; color: white; padding: 15px; font-size: 20px; font-weight: bold; }
        .agent-content { padding: 20px; }
        .test-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .test-section { border: 1px solid #eee; border-radius: 6px; padding: 15px; }
        .test-section h4 { margin: 0 0 15px 0; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-skipped { color: #ffc107; font-weight: bold; }
        .coverage-bar { background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .coverage-fill { height: 100%; background: linear-gradient(90deg, #ff4444 0%, #ffff44 50%, #44ff44 100%); transition: width 0.3s; }
        .benchmark-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .benchmark-table th, .benchmark-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .benchmark-table th { background: #f8f9fa; font-weight: bold; }
        .timestamp { text-align: center; color: #666; font-style: italic; margin-top: 30px; }
        .performance-issue { color: #dc3545; }
        .performance-good { color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Pydantic AI Agents Test Report</h1>
            <p>Comprehensive test results for production readiness validation</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Agents</h3>
                <p class="value">{total_agents}</p>
            </div>
            <div class="summary-card">
                <h3>Total Tests</h3>
                <p class="value">{total_tests}</p>
            </div>
            <div class="summary-card">
                <h3>Passed Tests</h3>
                <p class="value">{passed_tests}</p>
            </div>
            <div class="summary-card">
                <h3>Average Coverage</h3>
                <p class="value">{coverage_percent:.1f}%</p>
            </div>
        </div>
        
        {agents_content}
        
        <div class="timestamp">
            <p>Report generated on {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
        
        agents_html = ""
        for agent_name, agent_data in self.report_data['agents'].items():
            agent_html = f"""
        <div class="agent-section">
            <div class="agent-header">
                {agent_name.replace('_', ' ').title()}
            </div>
            <div class="agent-content">
                <div class="test-grid">
"""
            
            # Unit Tests
            unit_data = agent_data['unit_tests']
            if unit_data:
                agent_html += f"""
                    <div class="test-section">
                        <h4>Unit Tests</h4>
                        <p>Total: {unit_data.get('total_tests', 0)}</p>
                        <p class="status-passed">Passed: {unit_data.get('passed_tests', 0)}</p>
                        <p class="status-failed">Failed: {unit_data.get('failed_tests', 0)}</p>
                        <p>Execution Time: {unit_data.get('execution_time', 0):.2f}s</p>
                    </div>
"""
            
            # Integration Tests
            integration_data = agent_data['integration_tests']
            if integration_data:
                agent_html += f"""
                    <div class="test-section">
                        <h4>Integration Tests</h4>
                        <p>Total: {integration_data.get('total_tests', 0)}</p>
                        <p class="status-passed">Passed: {integration_data.get('passed_tests', 0)}</p>
                        <p class="status-failed">Failed: {integration_data.get('failed_tests', 0)}</p>
                        <p>Execution Time: {integration_data.get('execution_time', 0):.2f}s</p>
                    </div>
"""
            
            # Coverage
            coverage_data = agent_data['coverage']
            if coverage_data:
                coverage_percent = coverage_data.get('line_rate', 0)
                agent_html += f"""
                    <div class="test-section">
                        <h4>Code Coverage</h4>
                        <p>Line Coverage: {coverage_percent:.1f}%</p>
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: {coverage_percent}%"></div>
                        </div>
                        <p>Lines Covered: {coverage_data.get('lines_covered', 0)} / {coverage_data.get('lines_valid', 0)}</p>
                        <p>Branch Coverage: {coverage_data.get('branch_rate', 0):.1f}%</p>
                    </div>
"""
            
            # Performance Tests
            perf_data = agent_data['performance_tests']
            if perf_data and perf_data.get('benchmarks'):
                agent_html += f"""
                    <div class="test-section">
                        <h4>Performance Benchmarks</h4>
                        <table class="benchmark-table">
                            <tr><th>Benchmark</th><th>Mean (s)</th><th>Min (s)</th><th>Max (s)</th><th>Rounds</th></tr>
"""
                for benchmark in perf_data['benchmarks'][:5]:  # Show top 5
                    mean = benchmark.get('mean', 0)
                    status_class = "performance-good" if mean < 1.0 else "performance-issue"
                    agent_html += f"""
                            <tr>
                                <td>{benchmark.get('name', 'Unknown')}</td>
                                <td class="{status_class}">{mean:.4f}</td>
                                <td>{benchmark.get('min', 0):.4f}</td>
                                <td>{benchmark.get('max', 0):.4f}</td>
                                <td>{benchmark.get('rounds', 0)}</td>
                            </tr>
"""
                agent_html += """
                        </table>
                    </div>
"""
            
            agent_html += """
                </div>
            </div>
        </div>
"""
            agents_html += agent_html
        
        # Fill in the template
        html_content = html_template.format(
            total_agents=self.report_data['summary']['total_agents'],
            total_tests=self.report_data['summary']['total_tests'],
            passed_tests=self.report_data['summary']['passed_tests'],
            coverage_percent=self.report_data['summary']['coverage_percent'],
            timestamp=self.report_data['timestamp'],
            agents_content=agents_html
        )
        
        # Write HTML report
        html_file = self.output_dir / "test_report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {html_file}")
    
    def generate_json_report(self):
        """Generate JSON test report."""
        json_file = self.output_dir / "test_report.json"
        with open(json_file, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        print(f"JSON report generated: {json_file}")
    
    def generate_reports(self, agents: List[str]):
        """Generate all reports for the specified agents."""
        print(f"Generating test reports for agents: {agents}")
        
        # Collect data for each agent
        for agent_name in agents:
            print(f"Collecting data for {agent_name}...")
            self.report_data['agents'][agent_name] = self.collect_agent_data(agent_name)
        
        # Calculate overall summary
        self.report_data['summary']['total_agents'] = len(agents)
        
        total_tests = 0
        total_passed = 0
        total_coverage = 0.0
        coverage_count = 0
        
        for agent_data in self.report_data['agents'].values():
            summary = agent_data['summary']
            total_tests += summary['total_tests']
            total_passed += summary['passed_tests']
            
            if summary['coverage_percent'] > 0:
                total_coverage += summary['coverage_percent']
                coverage_count += 1
        
        self.report_data['summary']['total_tests'] = total_tests
        self.report_data['summary']['passed_tests'] = total_passed
        self.report_data['summary']['failed_tests'] = total_tests - total_passed
        self.report_data['summary']['coverage_percent'] = (
            total_coverage / coverage_count if coverage_count > 0 else 0.0
        )
        
        # Generate reports
        self.generate_html_report()
        self.generate_json_report()
        
        print(f"Reports generated in {self.output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate comprehensive test reports")
    parser.add_argument("--artifacts-dir", required=True, help="Directory containing test artifacts")
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")
    parser.add_argument("--agents", required=True, help="JSON list of agent names")
    
    args = parser.parse_args()
    
    try:
        agents = json.loads(args.agents)
    except json.JSONDecodeError:
        print("Error: --agents must be a valid JSON list")
        sys.exit(1)
    
    generator = TestReportGenerator(args.artifacts_dir, args.output_dir)
    generator.generate_reports(agents)


if __name__ == "__main__":
    main()