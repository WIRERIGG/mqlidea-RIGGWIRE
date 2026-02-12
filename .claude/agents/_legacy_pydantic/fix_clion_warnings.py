#!/usr/bin/env python3
"""
CLion Warnings Fix Generator

This script analyzes the CLion warnings from the build output and generates specific fixes
for each warning type, leveraging the existing valgrind_pydantic_tool infrastructure for validation.

Focus on the specific warnings we identified:
- misc-include-cleaner: Remove unused includes
- misc-use-anonymous-namespace: Use anonymous namespace instead of static
- modernize-use-ranges: Use modern C++ ranges
- bugprone-easily-swappable-parameters: Fix parameter confusion
- readability-identifier-length: Use descriptive variable names
- cppcoreguidelines-pro-bounds-constant-array-index: Safe array access
- misc-const-correctness: Add const qualifiers
- etc.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


class CLionWarningFixer:
    """Fix generator for specific CLion warnings."""
    
    def __init__(self):
        """Initialize the warning fixer."""
        self.project_root = Path("/IdeaProjects/wire_ground")
        self.fixes_applied = []
        
    def parse_build_warnings(self, build_output: str) -> List[Dict[str, Any]]:
        """Parse CLion warnings from build output."""
        warnings = []
        lines = build_output.split('\n')
        
        for line in lines:
            # Pattern: /path/file.cpp:line:col: warning: message [check-name]
            warning_match = re.search(r'(/[^:]+):(\d+):\d+: warning: (.+) \\[([^\\]]+)\\]', line)
            if warning_match:
                warnings.append({
                    'file_path': warning_match.group(1),
                    'line_number': int(warning_match.group(2)),
                    'description': warning_match.group(3),
                    'check_name': warning_match.group(4)
                })
        
        return warnings
    
    def generate_fixes(self, warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific fixes for each warning."""
        fixes = []
        
        # Group warnings by file for efficient processing
        warnings_by_file = {}
        for warning in warnings:
            file_path = warning['file_path']
            if file_path not in warnings_by_file:
                warnings_by_file[file_path] = []
            warnings_by_file[file_path].append(warning)
        
        # Generate fixes for each file
        for file_path, file_warnings in warnings_by_file.items():
            file_fixes = self._generate_file_fixes(file_path, file_warnings)
            fixes.extend(file_fixes)
        
        return fixes
    
    def _generate_file_fixes(self, file_path: str, warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fixes for warnings in a specific file."""
        fixes = []
        
        # Read the file content
        try:
            path = Path(file_path)
            if not path.exists():
                return []
            content = path.read_text()
            lines = content.split('\\n')
        except Exception as e:
            print(f"Could not read file {file_path}: {e}")
            return []
        
        for warning in warnings:
            fix = self._generate_specific_fix(file_path, warning, lines)
            if fix:
                fixes.append(fix)
        
        return fixes
    
    def _generate_specific_fix(self, file_path: str, warning: Dict[str, Any], lines: List[str]) -> Dict[str, Any]:
        """Generate a specific fix for a warning."""
        check_name = warning['check_name']
        line_num = warning['line_number'] - 1  # Convert to 0-based indexing
        
        if line_num >= len(lines):
            return None
            
        original_line = lines[line_num]
        fix_info = {
            'file_path': file_path,
            'line_number': warning['line_number'],
            'check_name': check_name,
            'original_line': original_line,
            'description': warning['description'],
            'fix_type': 'unknown',
            'suggested_fix': '',
            'explanation': ''
        }
        
        # Generate fixes based on warning type
        if check_name == 'misc-include-cleaner':
            return self._fix_include_cleaner(fix_info, warning)
        elif check_name == 'misc-use-anonymous-namespace':
            return self._fix_use_anonymous_namespace(fix_info, warning)
        elif check_name == 'modernize-use-ranges':
            return self._fix_use_ranges(fix_info, warning)
        elif check_name == 'bugprone-easily-swappable-parameters':
            return self._fix_swappable_parameters(fix_info, warning)
        elif check_name == 'readability-identifier-length':
            return self._fix_identifier_length(fix_info, warning)
        elif check_name == 'cppcoreguidelines-pro-bounds-constant-array-index':
            return self._fix_bounds_checking(fix_info, warning)
        elif check_name == 'misc-const-correctness':
            return self._fix_const_correctness(fix_info, warning)
        elif check_name == 'cppcoreguidelines-pro-type-reinterpret-cast':
            return self._fix_reinterpret_cast(fix_info, warning)
        elif check_name == 'portability-simd-intrinsics':
            return self._fix_simd_intrinsics(fix_info, warning)
        elif check_name == 'readability-container-data-pointer':
            return self._fix_container_data_pointer(fix_info, warning)
        elif check_name == 'cppcoreguidelines-avoid-non-const-global-variables':
            return self._fix_non_const_global(fix_info, warning)
        elif check_name == 'readability-container-contains':
            return self._fix_container_contains(fix_info, warning)
        
        return fix_info
    
    def _fix_include_cleaner(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        """Fix include cleaner warnings."""
        if 'not used directly' in warning['description']:
            # Remove unused include
            fix_info['fix_type'] = 'remove_line'
            fix_info['suggested_fix'] = '// ' + fix_info['original_line']  # Comment out
            fix_info['explanation'] = 'Comment out unused include (or remove if confirmed unused)'
        elif 'no header providing' in warning['description']:
            # Add missing include
            symbol_match = re.search(r'no header providing \"([^\"]+)\"', warning['description'])
            if symbol_match:
                symbol = symbol_match.group(1)
                if symbol in ['size_t', 'std::int64_t', 'std::uint8_t']:
                    fix_info['fix_type'] = 'add_include'
                    fix_info['suggested_fix'] = '#include <cstdint>'
                    fix_info['explanation'] = f'Add #include <cstdint> for {symbol}'
                elif 'std::setprecision' in symbol:
                    fix_info['fix_type'] = 'add_include'
                    fix_info['suggested_fix'] = '#include <iomanip>'
                    fix_info['explanation'] = 'Add #include <iomanip> for std::setprecision'
        
        return fix_info
    
    def _fix_use_anonymous_namespace(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix static function warnings.\"\"\"
        fix_info['fix_type'] = 'replace_static_with_namespace'
        
        # Extract function name
        func_match = re.search(r'static\\s+\\w+\\s+(\\w+)\\s*\\(', fix_info['original_line'])
        if func_match:
            func_name = func_match.group(1)
            new_line = fix_info['original_line'].replace('static ', '')
            fix_info['suggested_fix'] = f\"\"\"namespace {{
{new_line}
}} // anonymous namespace\"\"\"
            fix_info['explanation'] = f'Move {func_name} to anonymous namespace instead of using static'
        
        return fix_info
    
    def _fix_use_ranges(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix modernize-use-ranges warnings.\"\"\"
        fix_info['fix_type'] = 'modernize_ranges'
        
        if 'std::iota' in fix_info['original_line']:
            # Convert std::iota(container.begin(), container.end(), value) to std::ranges::iota(container, value)
            iota_match = re.search(r'std::iota\\(([^,]+)\\.begin\\(\\),\\s*([^,]+)\\.end\\(\\),\\s*([^)]+)\\)', fix_info['original_line'])
            if iota_match:
                container = iota_match.group(1)
                value = iota_match.group(3)
                new_line = fix_info['original_line'].replace(
                    f'std::iota({container}.begin(), {container}.end(), {value})',
                    f'std::ranges::iota({container}, {value})'
                )
                fix_info['suggested_fix'] = new_line
                fix_info['explanation'] = 'Use std::ranges::iota instead of iterator-based std::iota'
        
        return fix_info
    
    def _fix_swappable_parameters(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix easily swappable parameters.\"\"\"
        fix_info['fix_type'] = 'parameter_typing'
        fix_info['suggested_fix'] = '// Consider using different types or named parameters'
        fix_info['explanation'] = 'Use strong types or named parameters to prevent parameter swapping'
        return fix_info
    
    def _fix_identifier_length(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix short identifier names.\"\"\"
        fix_info['fix_type'] = 'rename_identifier'
        
        # Extract short identifier
        name_match = re.search(r'name \\'([^']+)\\' is too short', warning['description'])
        if name_match:
            short_name = name_match.group(1)
            # Suggest better names based on context
            better_names = {
                'i': 'index',
                'j': 'inner_index', 
                'k': 'key_index',
                'n': 'count',
                'a': 'first_matrix',
                'b': 'second_matrix', 
                'c': 'result_matrix'
            }
            better_name = better_names.get(short_name, f'{short_name}_value')
            fix_info['suggested_fix'] = fix_info['original_line'].replace(short_name, better_name)
            fix_info['explanation'] = f'Rename {short_name} to {better_name} for better readability'
        
        return fix_info
    
    def _fix_bounds_checking(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix array bounds checking warnings.\"\"\"
        fix_info['fix_type'] = 'bounds_checking'
        
        # Look for array access patterns
        if '[' in fix_info['original_line'] and ']' in fix_info['original_line']:
            # Suggest using .at() method or bounds checking
            fix_info['suggested_fix'] = '// Use .at() method or add bounds checking'
            fix_info['explanation'] = 'Use container.at(index) for bounds checking or add manual bounds validation'
        
        return fix_info
    
    def _fix_const_correctness(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix const correctness warnings.\"\"\"
        fix_info['fix_type'] = 'add_const'
        
        # Add const to variable declarations
        if 'can be declared' in warning['description']:
            new_line = fix_info['original_line']
            # Add const after type declaration
            if '__m256i' in new_line:
                new_line = new_line.replace('__m256i ', 'const __m256i ')
            elif 'auto ' in new_line:
                new_line = new_line.replace('auto ', 'const auto ')
            
            fix_info['suggested_fix'] = new_line
            fix_info['explanation'] = 'Add const qualifier to variable that is never modified'
        
        return fix_info
    
    def _fix_reinterpret_cast(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix reinterpret_cast warnings.\"\"\"
        fix_info['fix_type'] = 'safer_cast'
        fix_info['suggested_fix'] = '// Consider using static_cast, std::bit_cast, or memcpy for safer type conversion'
        fix_info['explanation'] = 'Replace reinterpret_cast with safer alternatives when possible'
        return fix_info
    
    def _fix_simd_intrinsics(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix SIMD intrinsics portability warnings.\"\"\"
        fix_info['fix_type'] = 'portability'
        fix_info['suggested_fix'] = '// Wrap in #ifdef __AVX2__ or use portable SIMD library'
        fix_info['explanation'] = 'Wrap SIMD intrinsics in platform-specific #ifdef blocks'
        return fix_info
    
    def _fix_container_data_pointer(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix container data pointer warnings.\"\"\"
        fix_info['fix_type'] = 'use_data_method'
        
        # Replace &container[0] with container.data()
        new_line = fix_info['original_line']
        data_pattern = r'&([\\w.]+)\\[0\\]'
        new_line = re.sub(data_pattern, r'\\1.data()', new_line)
        
        fix_info['suggested_fix'] = new_line
        fix_info['explanation'] = 'Use container.data() instead of &container[0]'
        return fix_info
    
    def _fix_non_const_global(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix non-const global variable warnings.\"\"\"
        fix_info['fix_type'] = 'make_const'
        
        if 'thread_local' in fix_info['original_line']:
            new_line = fix_info['original_line'].replace('thread_local', 'const thread_local')
            fix_info['suggested_fix'] = new_line
            fix_info['explanation'] = 'Make thread_local variable const if it is not modified'
        
        return fix_info
    
    def _fix_container_contains(self, fix_info: Dict[str, Any], warning: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Fix container.contains() warnings.\"\"\"
        fix_info['fix_type'] = 'use_contains'
        
        # Replace find() != end() with contains()
        new_line = fix_info['original_line']
        contains_pattern = r'([\\w.]+)\\.find\\(([^)]+)\\)\\s*!=\\s*([\\w.]+)\\.end\\(\\)'
        new_line = re.sub(contains_pattern, r'\\1.contains(\\2)', new_line)
        
        fix_info['suggested_fix'] = new_line
        fix_info['explanation'] = 'Use container.contains() instead of find() != end()'
        return fix_info
    
    def generate_fix_report(self, fixes: List[Dict[str, Any]]) -> str:
        \"\"\"Generate a comprehensive fix report.\"\"\"
        report = []
        report.append('# CLion Warnings Fix Report')
        report.append('=' * 50)
        report.append('')
        
        # Group fixes by file
        fixes_by_file = {}
        for fix in fixes:
            file_path = fix['file_path']
            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = []
            fixes_by_file[file_path].append(fix)
        
        # Generate report for each file
        for file_path, file_fixes in fixes_by_file.items():
            report.append(f'## File: {file_path}')
            report.append(f'Fixes needed: {len(file_fixes)}')
            report.append('')
            
            for i, fix in enumerate(file_fixes, 1):
                report.append(f'### Fix {i}: {fix['check_name']}')
                report.append(f'**Line {fix['line_number']}**: {fix['description']}')
                report.append('')
                report.append('**Original:**')
                report.append(f'```cpp')
                report.append(fix['original_line'])
                report.append('```')
                report.append('')
                report.append('**Suggested Fix:**')
                report.append(f'```cpp')
                report.append(fix['suggested_fix'])
                report.append('```')
                report.append('')
                report.append(f'**Explanation:** {fix['explanation']}')
                report.append('')
                report.append('---')
                report.append('')
        
        # Summary
        report.append('## Summary')
        fix_types = {}
        for fix in fixes:
            fix_type = fix['fix_type']
            fix_types[fix_type] = fix_types.get(fix_type, 0) + 1
        
        report.append(f'Total fixes needed: {len(fixes)}')
        report.append('Fix types:')
        for fix_type, count in sorted(fix_types.items()):
            report.append(f'- {fix_type}: {count}')
        
        return '\\n'.join(report)


def main():
    \"\"\"Main entry point.\"\"\"
    print('CLion Warnings Fix Generator')
    print('=' * 40)
    
    # Get build output with warnings
    print('Running build to collect warnings...')
    import subprocess
    
    try:
        result = subprocess.run([
            '/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake',
            '--build', 'cmake-build-debug', '--target', 'wire_ground_tests'
        ], capture_output=True, text=True, cwd='/IdeaProjects/wire_ground')
        build_output = result.stdout + result.stderr
        print(f'Build completed with {result.returncode} exit code')
    except Exception as e:
        print(f'Failed to run build: {e}')
        return 1
    
    # Initialize fixer and process warnings
    fixer = CLionWarningFixer()
    warnings = fixer.parse_build_warnings(build_output)
    print(f'Found {len(warnings)} warnings')
    
    if not warnings:
        print('No warnings found!')
        return 0
    
    # Generate fixes
    print('Generating fixes...')
    fixes = fixer.generate_fixes(warnings)
    print(f'Generated {len(fixes)} fixes')
    
    # Generate report
    report = fixer.generate_fix_report(fixes)
    
    # Save report
    report_file = Path('/IdeaProjects/wire_ground/clion_fixes_report.md')
    report_file.write_text(report)
    print(f'Fix report saved to: {report_file}')
    
    print('\\nTop 5 fixes needed:')
    for i, fix in enumerate(fixes[:5], 1):
        print(f'{i}. {fix['check_name']}: {fix['description'][:60]}...')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())