"""
Text output parser for Valgrind - supports all tools.
Parses plain text Valgrind output using regex patterns.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from models import ValgrindIssue, IssueCategory, IssueSeverity, StackFrame, ValgrindMetrics, ValgrindTool


class TextParser:
    """Comprehensive text parser for all Valgrind tools."""
    
    def __init__(self):
        self.patterns = self._init_patterns()
        
    def _init_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """Initialize regex patterns for all tools."""
        return {
            'memcheck': {
                'invalid_read': re.compile(
                    r'Invalid read of size (\d+)\s+at 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'
                ),
                'invalid_write': re.compile(
                    r'Invalid write of size (\d+)\s+at 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'  
                ),
                'uninitialized_value': re.compile(
                    r'Conditional jump or move depends on uninitialised value\(s\)\s+at 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'
                ),
                'invalid_free': re.compile(
                    r'Invalid free\(\) / delete / delete\[\]\s+at 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'
                ),
                'mismatched_free': re.compile(
                    r'Mismatched free\(\) / delete / delete \[\]\s+at 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'
                ),
                'definitely_lost': re.compile(
                    r'(\d+) bytes in (\d+) blocks are definitely lost'
                ),
                'possibly_lost': re.compile(
                    r'(\d+) bytes in (\d+) blocks are possibly lost'  
                ),
                'still_reachable': re.compile(
                    r'(\d+) bytes in (\d+) blocks are still reachable'
                ),
                'suppressed': re.compile(
                    r'(\d+) bytes in (\d+) blocks are suppressed'
                ),
                'leak_summary': re.compile(
                    r'LEAK SUMMARY:'
                )
            },
            
            'helgrind': {
                'data_race': re.compile(
                    r'Possible data race during (?:read|write) of size (\d+) at 0x[0-9A-F]+ by thread #(\d+):'
                ),
                'lock_order': re.compile(
                    r'Thread #(\d+): lock order "([^"]*)" violated'
                ),
                'unlock_invalid': re.compile(
                    r'Thread #(\d+): Exiting thread still holds (\d+) locks?'
                )
            },
            
            'drd': {
                'data_race': re.compile(
                    r'Conflicting (?:load|store) by thread (\d+) at 0x[0-9A-F]+ size (\d+)'
                ),
                'lock_order': re.compile(
                    r'Acquired lock order violation detected'
                ),
                'destroy_locked': re.compile(
                    r'Destroying locked mutex'
                )
            },
            
            'cachegrind': {
                'cache_summary': re.compile(
                    r'I   refs:\s+([0-9,]+)'
                ),
                'i1_misses': re.compile(
                    r'I1  misses:\s+([0-9,]+)'
                ),
                'll_misses': re.compile(
                    r'LLi misses:\s+([0-9,]+)'
                ),
                'd1_misses': re.compile(
                    r'D1  misses:\s+([0-9,]+)'
                ),
                'data_refs': re.compile(
                    r'D   refs:\s+([0-9,]+)'
                )
            },
            
            'callgrind': {
                'events_recorded': re.compile(
                    r'Events    : (.+)'
                ),
                'collected': re.compile(
                    r'Collected : (\d+)'
                )
            },
            
            'massif': {
                'heap_peak': re.compile(
                    r'peak_snapshot=(\d+)'
                ),
                'heap_tree': re.compile(
                    r'(\d+\.\d+)% \(([0-9,]+)B\) (.+?)$'
                )
            },
            
            'dhat': {
                'total_allocations': re.compile(
                    r'Total:     ([0-9,]+) bytes in ([0-9,]+) blocks'
                ),
                'at_t_peak': re.compile(
                    r'At t-peak: ([0-9,]+) bytes in ([0-9,]+) blocks'
                )
            },
            
            'common': {
                'stack_frame': re.compile(
                    r'(?:by|at) 0x[0-9A-F]+: (.+?) \((.+?):(\d+)\)'
                ),
                'object_frame': re.compile(
                    r'(?:by|at) 0x[0-9A-F]+: (.+?) \(in (.+?)\)'
                ),
                'error_summary': re.compile(
                    r'ERROR SUMMARY: (\d+) errors from (\d+) contexts'
                )
            }
        }
    
    def parse_output(self, output: str, tool: ValgrindTool) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Valgrind text output for specific tool."""
        issues = []
        metrics = ValgrindMetrics()
        
        if tool == ValgrindTool.MEMCHECK:
            issues, metrics = self._parse_memcheck(output)
        elif tool == ValgrindTool.HELGRIND:
            issues, metrics = self._parse_helgrind(output)
        elif tool == ValgrindTool.DRD:
            issues, metrics = self._parse_drd(output)
        elif tool == ValgrindTool.CACHEGRIND:
            issues, metrics = self._parse_cachegrind(output)
        elif tool == ValgrindTool.CALLGRIND:
            issues, metrics = self._parse_callgrind(output)
        elif tool == ValgrindTool.MASSIF:
            issues, metrics = self._parse_massif(output)
        elif tool == ValgrindTool.DHAT:
            issues, metrics = self._parse_dhat(output)
        else:
            # For other tools, extract basic error information
            issues, metrics = self._parse_generic(output)
            
        return issues, metrics
    
    def _parse_memcheck(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Memcheck output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Parse memory errors
        for pattern_name, pattern in self.patterns['memcheck'].items():
            if pattern_name in ['invalid_read', 'invalid_write']:
                for match in pattern.finditer(output):
                    size, func, file_path, line = match.groups()
                    category = IssueCategory.INVALID_READ if 'read' in pattern_name else IssueCategory.INVALID_WRITE
                    
                    issue = ValgrindIssue(
                        category=category,
                        description=f"Invalid {'read' if 'read' in pattern_name else 'write'} of {size} bytes",
                        severity=IssueSeverity.ERROR,
                        file_path=Path(file_path) if file_path != '???' else None,
                        line_number=int(line) if line.isdigit() else None,
                        function=func,
                        access_size=int(size),
                        stack_trace=self._extract_stack_trace(output, match.start())
                    )
                    issues.append(issue)
                    
            elif pattern_name == 'uninitialized_value':
                for match in pattern.finditer(output):
                    func, file_path, line = match.groups()
                    
                    issue = ValgrindIssue(
                        category=IssueCategory.UNINITIALIZED_VALUE,
                        description="Use of uninitialized value",
                        severity=IssueSeverity.WARNING,
                        file_path=Path(file_path) if file_path != '???' else None,
                        line_number=int(line) if line.isdigit() else None,
                        function=func,
                        stack_trace=self._extract_stack_trace(output, match.start())
                    )
                    issues.append(issue)
                    
            elif pattern_name in ['invalid_free', 'mismatched_free']:
                for match in pattern.finditer(output):
                    func, file_path, line = match.groups()
                    category = IssueCategory.INVALID_FREE if 'invalid' in pattern_name else IssueCategory.MISMATCHED_FREE
                    
                    issue = ValgrindIssue(
                        category=category,
                        description=f"{'Invalid' if 'invalid' in pattern_name else 'Mismatched'} free operation",
                        severity=IssueSeverity.ERROR,
                        file_path=Path(file_path) if file_path != '???' else None,
                        line_number=int(line) if line.isdigit() else None,
                        function=func,
                        stack_trace=self._extract_stack_trace(output, match.start())
                    )
                    issues.append(issue)
        
        # Parse leak information
        definitely_lost = self.patterns['memcheck']['definitely_lost'].search(output)
        if definitely_lost:
            bytes_lost, blocks_lost = definitely_lost.groups()
            metrics.definitely_lost = int(bytes_lost.replace(',', ''))
            metrics.bytes_leaked += metrics.definitely_lost
            
            if metrics.definitely_lost > 0:
                issue = ValgrindIssue(
                    category=IssueCategory.MEMORY_LEAK,
                    description=f"Definitely lost: {bytes_lost} bytes in {blocks_lost} blocks",
                    severity=IssueSeverity.ERROR,
                    bytes_involved=metrics.definitely_lost
                )
                issues.append(issue)
        
        possibly_lost = self.patterns['memcheck']['possibly_lost'].search(output)
        if possibly_lost:
            bytes_lost, blocks_lost = possibly_lost.groups()
            metrics.possibly_lost = int(bytes_lost.replace(',', ''))
            
            if metrics.possibly_lost > 0:
                issue = ValgrindIssue(
                    category=IssueCategory.MEMORY_LEAK,
                    description=f"Possibly lost: {bytes_lost} bytes in {blocks_lost} blocks",
                    severity=IssueSeverity.WARNING,
                    bytes_involved=metrics.possibly_lost
                )
                issues.append(issue)
        
        still_reachable = self.patterns['memcheck']['still_reachable'].search(output)
        if still_reachable:
            bytes_reachable, blocks_reachable = still_reachable.groups()
            metrics.still_reachable = int(bytes_reachable.replace(',', ''))
        
        suppressed = self.patterns['memcheck']['suppressed'].search(output)
        if suppressed:
            bytes_suppressed, blocks_suppressed = suppressed.groups()
            metrics.suppressed_bytes = int(bytes_suppressed.replace(',', ''))
        
        return issues, metrics
    
    def _parse_helgrind(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Helgrind output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Data races
        for match in self.patterns['helgrind']['data_race'].finditer(output):
            size, thread_id = match.groups()
            
            issue = ValgrindIssue(
                category=IssueCategory.DATA_RACE,
                description=f"Data race detected: {size} byte access by thread #{thread_id}",
                severity=IssueSeverity.CRITICAL,
                access_size=int(size),
                thread_id=int(thread_id),
                stack_trace=self._extract_stack_trace(output, match.start())
            )
            issues.append(issue)
            metrics.race_errors += 1
        
        # Lock order violations
        for match in self.patterns['helgrind']['lock_order'].finditer(output):
            thread_id, lock_order = match.groups()
            
            issue = ValgrindIssue(
                category=IssueCategory.LOCK_ORDER,
                description=f"Lock order violation in thread #{thread_id}: {lock_order}",
                severity=IssueSeverity.ERROR,
                thread_id=int(thread_id),
                stack_trace=self._extract_stack_trace(output, match.start())
            )
            issues.append(issue)
            metrics.lock_errors += 1
        
        return issues, metrics
    
    def _parse_drd(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse DRD output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Data races
        for match in self.patterns['drd']['data_race'].finditer(output):
            thread_id, size = match.groups()
            
            issue = ValgrindIssue(
                category=IssueCategory.DATA_RACE,
                description=f"Conflicting access by thread {thread_id}, size {size} bytes",
                severity=IssueSeverity.CRITICAL,
                access_size=int(size),
                thread_id=int(thread_id),
                stack_trace=self._extract_stack_trace(output, match.start())
            )
            issues.append(issue)
            metrics.race_errors += 1
        
        return issues, metrics
    
    def _parse_cachegrind(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Cachegrind output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Extract cache statistics
        i_refs = self.patterns['cachegrind']['cache_summary'].search(output)
        if i_refs:
            metrics.instruction_refs = int(i_refs.group(1).replace(',', ''))
        
        i1_misses = self.patterns['cachegrind']['i1_misses'].search(output)
        if i1_misses:
            metrics.i1_misses = int(i1_misses.group(1).replace(',', ''))
        
        d_refs = self.patterns['cachegrind']['data_refs'].search(output)
        if d_refs:
            metrics.data_refs = int(d_refs.group(1).replace(',', ''))
        
        d1_misses = self.patterns['cachegrind']['d1_misses'].search(output)
        if d1_misses:
            metrics.d1_misses = int(d1_misses.group(1).replace(',', ''))
            
            # Calculate miss rates
            if metrics.data_refs > 0:
                metrics.d1_miss_rate = (metrics.d1_misses / metrics.data_refs) * 100
                
            # Create issues for high miss rates
            if metrics.d1_miss_rate > 10.0:  # Threshold: 10% miss rate
                issue = ValgrindIssue(
                    category=IssueCategory.CACHE_MISS,
                    description=f"High D1 cache miss rate: {metrics.d1_miss_rate:.2f}%",
                    severity=IssueSeverity.WARNING if metrics.d1_miss_rate < 20 else IssueSeverity.ERROR,
                    details={"miss_rate": metrics.d1_miss_rate, "misses": metrics.d1_misses}
                )
                issues.append(issue)
        
        return issues, metrics
    
    def _parse_callgrind(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Callgrind output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Callgrind typically outputs to separate files
        # Text output is minimal, mainly status information
        events = self.patterns['callgrind']['events_recorded'].search(output)
        if events:
            # Create informational issue about profiling
            issue = ValgrindIssue(
                category=IssueCategory.FUNCTION_COST,
                description=f"Profiling data collected: {events.group(1)}",
                severity=IssueSeverity.INFO
            )
            issues.append(issue)
        
        return issues, metrics
    
    def _parse_massif(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Massif output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Massif outputs to separate files, text output has minimal info
        # Look for heap usage patterns
        peak_match = self.patterns['massif']['heap_peak'].search(output)
        if peak_match:
            metrics.peak_heap = int(peak_match.group(1))
            
            issue = ValgrindIssue(
                category=IssueCategory.HEAP_USAGE,
                description=f"Peak heap usage recorded: snapshot {peak_match.group(1)}",
                severity=IssueSeverity.INFO,
                details={"peak_snapshot": metrics.peak_heap}
            )
            issues.append(issue)
        
        return issues, metrics
    
    def _parse_dhat(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse DHAT output."""
        issues = []
        metrics = ValgrindMetrics()
        
        total_alloc = self.patterns['dhat']['total_allocations'].search(output)
        if total_alloc:
            bytes_total, blocks_total = total_alloc.groups()
            metrics.total_allocations = int(blocks_total.replace(',', ''))
            
            issue = ValgrindIssue(
                category=IssueCategory.MEMORY_ALLOCATION,
                description=f"Total allocations: {bytes_total} bytes in {blocks_total} blocks",
                severity=IssueSeverity.INFO,
                details={"total_bytes": int(bytes_total.replace(',', '')), "total_blocks": metrics.total_allocations}
            )
            issues.append(issue)
        
        return issues, metrics
    
    def _parse_generic(self, output: str) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse generic Valgrind output."""
        issues = []
        metrics = ValgrindMetrics()
        
        # Look for error summary
        error_summary = self.patterns['common']['error_summary'].search(output)
        if error_summary:
            total_errors, contexts = error_summary.groups()
            metrics.error_issues = int(total_errors)
            
            if metrics.error_issues > 0:
                issue = ValgrindIssue(
                    category=IssueCategory.SYSTEM_ERROR,
                    description=f"Total errors: {total_errors} from {contexts} contexts",
                    severity=IssueSeverity.ERROR,
                    details={"total_errors": metrics.error_issues, "contexts": int(contexts)}
                )
                issues.append(issue)
        
        return issues, metrics
    
    def _extract_stack_trace(self, output: str, start_pos: int) -> List[StackFrame]:
        """Extract stack trace from output starting at position."""
        stack_frames = []
        lines = output[start_pos:].split('\n')
        
        for line in lines[1:10]:  # Look at next 10 lines for stack trace
            if not line.strip():
                break
                
            # Try stack frame pattern
            frame_match = self.patterns['common']['stack_frame'].search(line)
            if frame_match:
                func, file_path, line_num = frame_match.groups()
                frame = StackFrame(
                    function=func,
                    file_path=Path(file_path) if file_path != '???' else None,
                    line_number=int(line_num) if line_num.isdigit() else None
                )
                stack_frames.append(frame)
                continue
            
            # Try object file pattern
            obj_match = self.patterns['common']['object_frame'].search(line)
            if obj_match:
                func, obj_file = obj_match.groups()
                frame = StackFrame(
                    function=func,
                    object_file=obj_file
                )
                stack_frames.append(frame)
                continue
                
            # Stop if no more stack frames
            if not any(pattern in line for pattern in ['by 0x', 'at 0x']):
                break
        
        return stack_frames


def parse_text_output(output: str, tool: ValgrindTool = ValgrindTool.MEMCHECK) -> List[ValgrindIssue]:
    """Parse Valgrind text output and return issues."""
    parser = TextParser()
    issues, _ = parser.parse_output(output, tool)
    return issues


def parse_text_metrics(output: str, tool: ValgrindTool = ValgrindTool.MEMCHECK) -> ValgrindMetrics:
    """Parse Valgrind text output and return metrics."""
    parser = TextParser()
    _, metrics = parser.parse_output(output, tool)
    return metrics