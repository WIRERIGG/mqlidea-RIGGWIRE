"""
Subprocess execution wrapper for Valgrind commands.
Handles timeout, error handling, and process management.
"""

import subprocess
import shutil
import time
import signal
import os
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from models import ValgrindError


class ValgrindRunner:
    """Subprocess runner for Valgrind with comprehensive error handling."""
    
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout
        self.valgrind_path = self._find_valgrind()
        
    def _find_valgrind(self) -> str:
        """Find Valgrind executable."""
        valgrind_path = shutil.which('valgrind')
        if not valgrind_path:
            raise ValgrindError("Valgrind not found in PATH")
        return valgrind_path
    
    def check_valgrind_installation(self) -> Dict[str, str]:
        """Check Valgrind installation and return version info."""
        try:
            result = subprocess.run(
                [self.valgrind_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise ValgrindError(f"Valgrind version check failed: {result.stderr}")
            
            version_info = {
                'path': self.valgrind_path,
                'version': result.stdout.strip(),
                'available_tools': self._get_available_tools()
            }
            
            return version_info
            
        except subprocess.TimeoutExpired:
            raise ValgrindError("Valgrind version check timed out")
        except subprocess.SubprocessError as e:
            raise ValgrindError(f"Failed to check Valgrind installation: {e}")
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available Valgrind tools."""
        try:
            result = subprocess.run(
                [self.valgrind_path, '--tool=help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            tools = []
            for line in result.stderr.split('\n'):
                line = line.strip()
                if line and not line.startswith('valgrind:') and '--tool=' not in line:
                    # Extract tool names from help output
                    if any(tool in line for tool in ['memcheck', 'cachegrind', 'callgrind', 'helgrind', 'drd', 'massif', 'dhat', 'lackey', 'none']):
                        tool_name = line.split()[0] if line.split() else None
                        if tool_name and tool_name not in tools:
                            tools.append(tool_name)
            
            # Add common tools if not detected
            common_tools = ['memcheck', 'cachegrind', 'callgrind', 'helgrind', 'drd', 'massif', 'dhat', 'lackey', 'none']
            for tool in common_tools:
                if tool not in tools:
                    tools.append(tool)
                    
            return tools
            
        except Exception:
            # Return default tools if detection fails
            return ['memcheck', 'cachegrind', 'callgrind', 'helgrind', 'drd', 'massif', 'dhat', 'lackey', 'none']
    
    def run_valgrind(self, command: List[str], working_dir: Optional[Path] = None) -> Tuple[str, str, int, float]:
        """
        Run Valgrind command with comprehensive error handling.
        
        Returns:
            Tuple of (stdout, stderr, return_code, execution_time)
        """
        start_time = time.time()
        
        try:
            # Validate binary exists
            if len(command) > 1:
                binary_path = None
                # Find the binary in the command (after valgrind and its flags)
                for i, arg in enumerate(command):
                    if not arg.startswith('-') and arg != 'valgrind' and i > 0:
                        binary_path = Path(arg)
                        break
                
                if binary_path and not binary_path.exists():
                    raise ValgrindError(f"Target binary not found: {binary_path}")
            
            # Set up environment
            env = os.environ.copy()
            
            # Run the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=working_dir,
                env=env
            )
            
            execution_time = time.time() - start_time
            
            # For Valgrind, stderr often contains the analysis output
            stdout = result.stdout
            stderr = result.stderr
            
            # Valgrind returns 0 even when it finds errors, so don't treat non-zero as failure
            # unless it's a real execution error
            return stdout, stderr, result.returncode, execution_time
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            raise ValgrindError(
                f"Valgrind execution timed out after {self.timeout} seconds",
                exit_code=-1,
                stderr=f"Timeout after {execution_time:.2f}s"
            )
            
        except subprocess.SubprocessError as e:
            execution_time = time.time() - start_time
            raise ValgrindError(
                f"Subprocess error: {e}",
                exit_code=-1,
                stderr=str(e)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise ValgrindError(
                f"Unexpected error running Valgrind: {e}",
                exit_code=-1,
                stderr=str(e)
            )
    
    def run_parallel_tools(self, base_command: List[str], tools: List[str], working_dir: Optional[Path] = None) -> Dict[str, Tuple[str, str, int, float]]:
        """
        Run multiple Valgrind tools in parallel (not truly parallel due to resource constraints).
        
        Returns:
            Dictionary mapping tool names to (stdout, stderr, return_code, execution_time)
        """
        results = {}
        
        for tool in tools:
            try:
                # Replace tool in command
                tool_command = base_command.copy()
                for i, arg in enumerate(tool_command):
                    if arg.startswith('--tool='):
                        tool_command[i] = f'--tool={tool}'
                        break
                else:
                    # Add tool if not present
                    tool_command.insert(1, f'--tool={tool}')
                
                print(f"Running Valgrind with {tool}...")
                result = self.run_valgrind(tool_command, working_dir)
                results[tool] = result
                
            except ValgrindError as e:
                # Store error information
                results[tool] = ("", str(e), e.exit_code or -1, 0.0)
                print(f"Error running {tool}: {e}")
                
        return results
    
    def validate_binary(self, binary_path: Path) -> bool:
        """Validate that the binary is suitable for Valgrind analysis."""
        if not binary_path.exists():
            raise ValgrindError(f"Binary not found: {binary_path}")
        
        if not binary_path.is_file():
            raise ValgrindError(f"Path is not a file: {binary_path}")
        
        if not os.access(binary_path, os.X_OK):
            raise ValgrindError(f"Binary is not executable: {binary_path}")
        
        # Check if it's a valid ELF binary (Linux)
        try:
            with open(binary_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'\x7fELF':
                    print(f"Warning: {binary_path} may not be a valid ELF binary")
        except IOError:
            print(f"Warning: Could not read binary {binary_path}")
        
        return True
    
    def create_suppressions_file(self, suppressions: List[str], output_path: Path) -> Path:
        """Create Valgrind suppressions file."""
        with open(output_path, 'w') as f:
            f.write("# Valgrind suppressions file\n")
            f.write("# Auto-generated\n\n")
            
            for i, suppression in enumerate(suppressions):
                f.write(f"# Suppression {i+1}\n")
                f.write(f"{suppression}\n\n")
        
        return output_path
    
    def get_tool_help(self, tool: str) -> str:
        """Get help information for specific Valgrind tool."""
        try:
            result = subprocess.run(
                [self.valgrind_path, f'--tool={tool}', '--help'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout + result.stderr
            
        except Exception as e:
            return f"Failed to get help for {tool}: {e}"


# Convenience functions
def check_valgrind_installed() -> bool:
    """Check if Valgrind is installed and available."""
    try:
        runner = ValgrindRunner()
        runner.check_valgrind_installation()
        return True
    except ValgrindError:
        return False


def get_valgrind_version() -> str:
    """Get Valgrind version string."""
    try:
        runner = ValgrindRunner()
        info = runner.check_valgrind_installation()
        return info['version']
    except ValgrindError as e:
        return f"Error: {e}"


def validate_tool_availability(tools: List[str]) -> Dict[str, bool]:
    """Check which tools are available."""
    try:
        runner = ValgrindRunner()
        available_tools = runner._get_available_tools()
        return {tool: tool in available_tools for tool in tools}
    except Exception:
        return {tool: False for tool in tools}