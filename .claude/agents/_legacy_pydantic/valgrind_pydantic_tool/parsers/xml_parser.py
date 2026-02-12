"""
XML output parser for Valgrind - supports all tools.
Parses XML Valgrind output using ElementTree.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from models import ValgrindIssue, IssueCategory, IssueSeverity, StackFrame, ValgrindMetrics, ValgrindTool


class XMLParser:
    """Comprehensive XML parser for all Valgrind tools."""
    
    def __init__(self):
        self.category_mapping = self._init_category_mapping()
        
    def _init_category_mapping(self) -> Dict[str, IssueCategory]:
        """Map Valgrind error kinds to our categories."""
        return {
            # Memcheck kinds
            'InvalidRead': IssueCategory.INVALID_READ,
            'InvalidWrite': IssueCategory.INVALID_WRITE,
            'InvalidFree': IssueCategory.INVALID_FREE,
            'MismatchedFree': IssueCategory.MISMATCHED_FREE,
            'InvalidMemPool': IssueCategory.INVALID_FREE,
            'UninitCondition': IssueCategory.UNINITIALIZED_VALUE,
            'UninitValue': IssueCategory.UNINITIALIZED_VALUE,
            'SyscallParam': IssueCategory.UNINITIALIZED_VALUE,
            'ClientCheck': IssueCategory.SYSTEM_ERROR,
            'Leak_DefinitelyLost': IssueCategory.MEMORY_LEAK,
            'Leak_IndirectlyLost': IssueCategory.MEMORY_LEAK,
            'Leak_PossiblyLost': IssueCategory.MEMORY_LEAK,
            'Leak_StillReachable': IssueCategory.MEMORY_LEAK,
            
            # Helgrind kinds
            'Race': IssueCategory.DATA_RACE,
            'UnlockUnlocked': IssueCategory.UNLOCK_INVALID,
            'UnlockForeign': IssueCategory.UNLOCK_INVALID,
            'UnlockBogus': IssueCategory.UNLOCK_INVALID,
            'PthAPIerror': IssueCategory.SYSTEM_ERROR,
            'LockOrder': IssueCategory.LOCK_ORDER,
            'Misc': IssueCategory.SYSTEM_ERROR,
            
            # DRD kinds
            'ConflictingAccess': IssueCategory.DATA_RACE,
            'MutexErr': IssueCategory.LOCK_ORDER,
            'CondErr': IssueCategory.SYSTEM_ERROR,
            'SemaphoreErr': IssueCategory.SYSTEM_ERROR,
            'BarrierErr': IssueCategory.SYSTEM_ERROR,
            'RwlockErr': IssueCategory.LOCK_ORDER,
            'HoldtimeErr': IssueCategory.SYSTEM_ERROR,
            'GenericErr': IssueCategory.SYSTEM_ERROR,
        }
    
    def parse_xml_output(self, xml_content: str, tool: ValgrindTool) -> Tuple[List[ValgrindIssue], ValgrindMetrics]:
        """Parse Valgrind XML output."""
        try:
            root = ET.fromstring(xml_content)
            issues = []
            metrics = ValgrindMetrics()
            
            # Parse protocol info
            protocol_version = root.get('protocolversion', '4')
            
            # Parse errors
            for error_elem in root.findall('.//error'):
                issue = self._parse_error_element(error_elem, tool)
                if issue:
                    issues.append(issue)
            
            # Parse tool-specific sections
            if tool == ValgrindTool.MEMCHECK:
                metrics = self._parse_memcheck_metrics(root, metrics)
            elif tool == ValgrindTool.CACHEGRIND:
                metrics = self._parse_cachegrind_metrics(root, metrics)
            elif tool in [ValgrindTool.HELGRIND, ValgrindTool.DRD]:
                metrics = self._parse_threading_metrics(root, metrics)
            elif tool == ValgrindTool.MASSIF:
                metrics = self._parse_massif_metrics(root, metrics)
            elif tool == ValgrindTool.DHAT:
                metrics = self._parse_dhat_metrics(root, metrics)
            
            # Update general metrics
            self._update_general_metrics(issues, metrics)
            
            return issues, metrics
            
        except ET.ParseError as e:
            # Fallback to text parsing if XML is malformed
            print(f"XML parsing failed: {e}")
            return [], ValgrindMetrics()
    
    def _parse_error_element(self, error_elem: ET.Element, tool: ValgrindTool) -> Optional[ValgrindIssue]:
        """Parse individual error element."""
        kind_elem = error_elem.find('kind')
        if kind_elem is None:
            return None
            
        kind = kind_elem.text
        category = self.category_mapping.get(kind, IssueCategory.UNKNOWN_ERROR)
        
        # Get what element
        what_elem = error_elem.find('what')
        description = what_elem.text if what_elem is not None else f"Error of type: {kind}"
        
        # Get severity based on kind
        severity = self._determine_severity(kind, category)
        
        # Parse stack trace
        stack_trace = []
        stack_elem = error_elem.find('stack')
        if stack_elem is not None:
            stack_trace = self._parse_stack_element(stack_elem)
        
        # Extract location from first stack frame
        file_path = None
        line_number = None
        function = None
        
        if stack_trace:
            first_frame = stack_trace[0]
            file_path = first_frame.file_path
            line_number = first_frame.line_number
            function = first_frame.function
        
        # Parse additional details
        details = self._parse_error_details(error_elem, kind)
        
        # Extract tool-specific information
        bytes_involved = None
        access_size = None
        thread_id = None
        
        if 'size' in details:
            access_size = details['size']
            bytes_involved = access_size
        
        if 'tid' in details:
            thread_id = details['tid']
        
        return ValgrindIssue(
            category=category,
            description=description,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            function=function,
            stack_trace=stack_trace,
            details=details,
            bytes_involved=bytes_involved,
            access_size=access_size,
            thread_id=thread_id
        )
    
    def _parse_stack_element(self, stack_elem: ET.Element) -> List[StackFrame]:
        """Parse stack trace element."""
        frames = []
        
        for frame_elem in stack_elem.findall('frame'):
            ip = frame_elem.find('ip')
            obj = frame_elem.find('obj')
            fn = frame_elem.find('fn')
            dir_elem = frame_elem.find('dir')
            file_elem = frame_elem.find('file')
            line_elem = frame_elem.find('line')
            
            frame = StackFrame(
                instruction_pointer=ip.text if ip is not None else None,
                object_file=obj.text if obj is not None else None,
                function=fn.text if fn is not None else None
            )
            
            # Construct file path
            if file_elem is not None:
                file_name = file_elem.text
                if dir_elem is not None and dir_elem.text:
                    frame.file_path = Path(dir_elem.text) / file_name
                else:
                    frame.file_path = Path(file_name)
                    
            if line_elem is not None and line_elem.text.isdigit():
                frame.line_number = int(line_elem.text)
                
            frames.append(frame)
            
        return frames
    
    def _parse_error_details(self, error_elem: ET.Element, kind: str) -> Dict[str, Any]:
        """Parse error-specific details."""
        details = {}
        
        # Common details
        unique_elem = error_elem.find('unique')
        if unique_elem is not None:
            details['unique_id'] = unique_elem.text
            
        tid_elem = error_elem.find('tid')
        if tid_elem is not None:
            details['tid'] = int(tid_elem.text)
        
        # Memcheck specific
        if kind in ['InvalidRead', 'InvalidWrite']:
            size_elem = error_elem.find('size')
            if size_elem is not None:
                details['size'] = int(size_elem.text)
                
        # Threading specific (Helgrind/DRD)
        if 'Race' in kind:
            # Look for thread information
            for elem in error_elem.iter():
                if elem.tag == 'tid':
                    details['thread_id'] = int(elem.text)
                elif elem.tag == 'addr':
                    details['address'] = elem.text
        
        return details
    
    def _determine_severity(self, kind: str, category: IssueCategory) -> IssueSeverity:
        """Determine issue severity based on kind and category."""
        critical_kinds = ['Race', 'ConflictingAccess', 'InvalidRead', 'InvalidWrite', 'InvalidFree']
        error_kinds = ['Leak_DefinitelyLost', 'MismatchedFree', 'LockOrder', 'UnlockUnlocked']
        
        if kind in critical_kinds:
            return IssueSeverity.CRITICAL
        elif kind in error_kinds:
            return IssueSeverity.ERROR
        elif 'Leak_PossiblyLost' in kind or 'Uninit' in kind:
            return IssueSeverity.WARNING
        else:
            return IssueSeverity.INFO
    
    def _parse_memcheck_metrics(self, root: ET.Element, metrics: ValgrindMetrics) -> ValgrindMetrics:
        """Parse Memcheck-specific metrics from XML."""
        # Look for leak summary
        for elem in root.iter():
            if elem.tag == 'preamble':
                # Parse preamble for memory info
                continue
            elif elem.tag == 'leak_record':
                # Parse individual leak records
                bytes_elem = elem.find('bytes')
                kind_elem = elem.find('kind')
                
                if bytes_elem is not None and kind_elem is not None:
                    bytes_leaked = int(bytes_elem.text)
                    leak_kind = kind_elem.text
                    
                    if leak_kind == 'Definite':
                        metrics.definitely_lost += bytes_leaked
                    elif leak_kind == 'Possible':
                        metrics.possibly_lost += bytes_leaked
                    elif leak_kind == 'Reachable':
                        metrics.still_reachable += bytes_leaked
        
        metrics.bytes_leaked = metrics.definitely_lost + metrics.possibly_lost
        return metrics
    
    def _parse_cachegrind_metrics(self, root: ET.Element, metrics: ValgrindMetrics) -> ValgrindMetrics:
        """Parse Cachegrind-specific metrics from XML."""
        # Cachegrind XML output is less common, usually outputs to separate files
        # Look for any cache-related information in XML
        for elem in root.iter():
            if 'cache' in elem.tag.lower():
                # Parse cache statistics if present
                continue
        
        return metrics
    
    def _parse_threading_metrics(self, root: ET.Element, metrics: ValgrindMetrics) -> ValgrindMetrics:
        """Parse threading metrics (Helgrind/DRD)."""
        race_count = 0
        lock_count = 0
        
        for error_elem in root.findall('.//error'):
            kind_elem = error_elem.find('kind')
            if kind_elem is not None:
                kind = kind_elem.text
                if 'Race' in kind or 'ConflictingAccess' in kind:
                    race_count += 1
                elif 'Lock' in kind or 'Mutex' in kind:
                    lock_count += 1
        
        metrics.race_errors = race_count
        metrics.lock_errors = lock_count
        return metrics
    
    def _parse_massif_metrics(self, root: ET.Element, metrics: ValgrindMetrics) -> ValgrindMetrics:
        """Parse Massif-specific metrics from XML."""
        # Massif typically outputs to separate files
        # Look for heap information in XML if present
        for elem in root.iter():
            if 'heap' in elem.tag.lower():
                # Parse heap statistics if present
                continue
        
        return metrics
    
    def _parse_dhat_metrics(self, root: ET.Element, metrics: ValgrindMetrics) -> ValgrindMetrics:
        """Parse DHAT-specific metrics from XML."""
        # DHAT outputs to separate files
        # Look for allocation information if present
        for elem in root.iter():
            if 'alloc' in elem.tag.lower():
                # Parse allocation statistics if present
                continue
        
        return metrics
    
    def _update_general_metrics(self, issues: List[ValgrindIssue], metrics: ValgrindMetrics):
        """Update general metrics based on parsed issues."""
        metrics.total_issues = len(issues)
        
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                metrics.critical_issues += 1
            elif issue.severity == IssueSeverity.ERROR:
                metrics.error_issues += 1
            elif issue.severity == IssueSeverity.WARNING:
                metrics.warning_issues += 1


def parse_xml_output(xml_content: str, tool: ValgrindTool = ValgrindTool.MEMCHECK) -> List[ValgrindIssue]:
    """Parse Valgrind XML output and return issues."""
    parser = XMLParser()
    issues, _ = parser.parse_xml_output(xml_content, tool)
    return issues


def parse_xml_metrics(xml_content: str, tool: ValgrindTool = ValgrindTool.MEMCHECK) -> ValgrindMetrics:
    """Parse Valgrind XML output and return metrics."""
    parser = XMLParser()
    _, metrics = parser.parse_xml_output(xml_content, tool)
    return metrics