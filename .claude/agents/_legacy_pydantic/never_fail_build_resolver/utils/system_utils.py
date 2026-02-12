"""System utilities and resource monitoring for build resolver."""

import os
import platform
import subprocess
import psutil
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import json


@dataclass
class SystemRequirement:
    """Definition of a system requirement."""
    name: str
    requirement_type: str  # 'command', 'library', 'version', 'resource'
    check_command: Optional[str] = None
    min_version: Optional[str] = None
    min_memory_gb: Optional[float] = None
    min_disk_gb: Optional[float] = None
    required: bool = True
    description: str = ""


@dataclass 
class SystemResource:
    """Current system resource information."""
    cpu_count: int
    cpu_usage_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_usage_percent: float
    disk_total_gb: float
    disk_free_gb: float
    disk_usage_percent: float
    load_average: Tuple[float, float, float]  # 1m, 5m, 15m
    boot_time: datetime
    uptime_seconds: float


class SystemUtils:
    """Comprehensive system utilities for build environment monitoring."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self._cache = {}
        self._cache_timeout = 60  # Cache for 60 seconds
    
    def get_system_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive system information."""
        cache_key = 'system_info'
        
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            info = {
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'architecture': platform.architecture(),
                    'hostname': socket.gethostname(),
                    'python_version': platform.python_version(),
                },
                'resources': self._get_resource_info(),
                'environment': self._get_environment_info(),
                'network': self._get_network_info(),
                'processes': self._get_process_info(),
                'timestamp': datetime.now().isoformat()
            }
            
            self._update_cache(cache_key, info)
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def _get_resource_info(self) -> SystemResource:
        """Get current system resource information."""
        try:
            # CPU information
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            memory_usage_percent = memory.percent
            
            # Disk information (root filesystem)
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                load_avg = (0.0, 0.0, 0.0)  # Windows doesn't have load average
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = time.time() - psutil.boot_time()
            
            return SystemResource(
                cpu_count=cpu_count,
                cpu_usage_percent=cpu_usage,
                memory_total_gb=memory_total_gb,
                memory_available_gb=memory_available_gb,
                memory_usage_percent=memory_usage_percent,
                disk_total_gb=disk_total_gb,
                disk_free_gb=disk_free_gb,
                disk_usage_percent=disk_usage_percent,
                load_average=load_avg,
                boot_time=boot_time,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get resource info: {e}")
            # Return minimal info on error
            return SystemResource(
                cpu_count=1, cpu_usage_percent=0, memory_total_gb=0, memory_available_gb=0,
                memory_usage_percent=0, disk_total_gb=0, disk_free_gb=0, disk_usage_percent=0,
                load_average=(0, 0, 0), boot_time=datetime.now(), uptime_seconds=0
            )
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get build-relevant environment information."""
        env_info = {
            'shell': os.environ.get('SHELL', 'unknown'),
            'user': os.environ.get('USER', 'unknown'),
            'home': os.environ.get('HOME', 'unknown'),
            'path_entries': len(os.environ.get('PATH', '').split(os.pathsep)),
        }
        
        # Build-relevant environment variables
        build_env_vars = [
            'CC', 'CXX', 'CMAKE_ROOT', 'CMAKE_PREFIX_PATH', 'CMAKE_MODULE_PATH',
            'PKG_CONFIG_PATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH', 'C_INCLUDE_PATH',
            'CPLUS_INCLUDE_PATH', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS'
        ]
        
        env_info['build_variables'] = {
            var: os.environ.get(var) for var in build_env_vars if var in os.environ
        }
        
        return env_info
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get basic network connectivity information."""
        try:
            # Check if we can resolve DNS
            socket.gethostbyname('google.com')
            dns_working = True
        except socket.error:
            dns_working = False
        
        # Get network interfaces
        interfaces = []
        try:
            net_if_addrs = psutil.net_if_addrs()
            for interface, addrs in net_if_addrs.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interfaces.append({
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
                        break
        except Exception:
            pass
        
        return {
            'dns_working': dns_working,
            'interfaces': interfaces
        }
    
    def _get_process_info(self) -> Dict[str, Any]:
        """Get information about running processes."""
        try:
            # Count processes by name that might be relevant to builds
            relevant_processes = ['cmake', 'make', 'ninja', 'gcc', 'g++', 'clang', 'clang++']
            process_counts = {}
            
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    for relevant in relevant_processes:
                        if relevant in proc_name:
                            process_counts[relevant] = process_counts.get(relevant, 0) + 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'total_processes': len(psutil.pids()),
                'build_related_processes': process_counts
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get process info: {e}")
            return {}
    
    def check_command_available(self, command: str, timeout: float = 5.0) -> Tuple[bool, str]:
        """Check if a command is available and get its version."""
        try:
            # Try --version first
            for version_flag in ['--version', '-version', '-V', '/version']:
                try:
                    result = subprocess.run(
                        [command, version_flag],
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    if result.returncode == 0:
                        return True, result.stdout.strip().split('\n')[0]
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Try just running the command
            try:
                result = subprocess.run(
                    [command],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                # Command exists if it doesn't give "command not found" error
                return True, f"Available (exit code: {result.returncode})"
            except FileNotFoundError:
                return False, "Command not found"
            
        except Exception as e:
            return False, f"Error checking command: {e}"
    
    def get_compiler_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about available compilers."""
        compilers = {
            'gcc': ['gcc', 'g++'],
            'clang': ['clang', 'clang++'], 
            'msvc': ['cl', 'link']
        }
        
        compiler_info = {}
        
        for compiler_family, commands in compilers.items():
            family_info = {}
            
            for command in commands:
                available, version_info = self.check_command_available(command)
                family_info[command] = {
                    'available': available,
                    'version': version_info,
                    'path': shutil.which(command) if available else None
                }
            
            compiler_info[compiler_family] = family_info
        
        return compiler_info
    
    def get_build_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available build tools."""
        build_tools = [
            'cmake', 'make', 'ninja', 'pkg-config', 'git',
            'clang-tidy', 'cppcheck', 'valgrind', 'gdb'
        ]
        
        tools_info = {}
        
        for tool in build_tools:
            available, version_info = self.check_command_available(tool)
            tools_info[tool] = {
                'available': available,
                'version': version_info,
                'path': shutil.which(tool) if available else None
            }
        
        return tools_info
    
    def check_system_requirements(self, requirements: List[SystemRequirement]) -> Dict[str, Any]:
        """Check if system meets specified requirements."""
        results = {
            'all_met': True,
            'required_met': True,
            'checks': [],
            'summary': {
                'total': len(requirements),
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        resources = self._get_resource_info()
        
        for req in requirements:
            check_result = {
                'name': req.name,
                'required': req.required,
                'passed': False,
                'message': '',
                'details': {}
            }
            
            try:
                if req.requirement_type == 'command':
                    if req.check_command:
                        available, version = self.check_command_available(req.check_command)
                        check_result['passed'] = available
                        check_result['message'] = f"Command '{req.check_command}': {version}" if available else f"Command '{req.check_command}' not available"
                        check_result['details'] = {'available': available, 'version': version}
                
                elif req.requirement_type == 'memory':
                    if req.min_memory_gb:
                        check_result['passed'] = resources.memory_available_gb >= req.min_memory_gb
                        check_result['message'] = f"Memory: {resources.memory_available_gb:.1f}GB available, need {req.min_memory_gb}GB"
                        check_result['details'] = {
                            'available_gb': resources.memory_available_gb,
                            'required_gb': req.min_memory_gb
                        }
                
                elif req.requirement_type == 'disk':
                    if req.min_disk_gb:
                        check_result['passed'] = resources.disk_free_gb >= req.min_disk_gb
                        check_result['message'] = f"Disk: {resources.disk_free_gb:.1f}GB free, need {req.min_disk_gb}GB"
                        check_result['details'] = {
                            'free_gb': resources.disk_free_gb,
                            'required_gb': req.min_disk_gb
                        }
                
                elif req.requirement_type == 'version':
                    if req.check_command and req.min_version:
                        available, version = self.check_command_available(req.check_command)
                        if available:
                            # Simple version comparison (not robust, but works for basic cases)
                            version_met = self._compare_versions(version, req.min_version)
                            check_result['passed'] = version_met
                            check_result['message'] = f"Version check for {req.check_command}: {version} (need {req.min_version})"
                        else:
                            check_result['passed'] = False
                            check_result['message'] = f"Command {req.check_command} not available for version check"
                        
                        check_result['details'] = {
                            'available': available,
                            'version': version,
                            'min_version': req.min_version
                        }
                
            except Exception as e:
                check_result['passed'] = False
                check_result['message'] = f"Error checking requirement: {e}"
                self.logger.error(f"Error checking requirement {req.name}: {e}")
            
            # Update summary
            if check_result['passed']:
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1
                results['all_met'] = False
                if req.required:
                    results['required_met'] = False
                else:
                    results['summary']['warnings'] += 1
            
            results['checks'].append(check_result)
        
        return results
    
    def _compare_versions(self, version_str: str, min_version: str) -> bool:
        """Simple version comparison. Returns True if version_str >= min_version."""
        try:
            # Extract just the version numbers (remove text)
            import re
            version_match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', version_str)
            min_match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', min_version)
            
            if not version_match or not min_match:
                return False
            
            # Convert to tuples for comparison
            version_tuple = tuple(int(x) if x else 0 for x in version_match.groups())
            min_tuple = tuple(int(x) if x else 0 for x in min_match.groups())
            
            return version_tuple >= min_tuple
            
        except Exception:
            return False
    
    def monitor_resource_usage(self, duration_seconds: float = 60.0, interval: float = 1.0) -> Dict[str, Any]:
        """Monitor system resource usage over time."""
        samples = []
        start_time = time.time()
        
        self.logger.info(f"Starting resource monitoring for {duration_seconds}s")
        
        try:
            while time.time() - start_time < duration_seconds:
                sample_time = time.time()
                resources = self._get_resource_info()
                
                sample = {
                    'timestamp': sample_time,
                    'cpu_usage': resources.cpu_usage_percent,
                    'memory_usage': resources.memory_usage_percent,
                    'disk_usage': resources.disk_usage_percent,
                    'load_average_1m': resources.load_average[0]
                }
                
                samples.append(sample)
                time.sleep(interval)
            
            # Calculate statistics
            if samples:
                cpu_values = [s['cpu_usage'] for s in samples]
                memory_values = [s['memory_usage'] for s in samples]
                load_values = [s['load_average_1m'] for s in samples]
                
                stats = {
                    'duration_seconds': time.time() - start_time,
                    'sample_count': len(samples),
                    'cpu_usage': {
                        'min': min(cpu_values),
                        'max': max(cpu_values),
                        'avg': sum(cpu_values) / len(cpu_values)
                    },
                    'memory_usage': {
                        'min': min(memory_values),
                        'max': max(memory_values),
                        'avg': sum(memory_values) / len(memory_values)
                    },
                    'load_average': {
                        'min': min(load_values),
                        'max': max(load_values),
                        'avg': sum(load_values) / len(load_values)
                    },
                    'samples': samples
                }
                
                return stats
            
        except KeyboardInterrupt:
            self.logger.info("Resource monitoring interrupted")
        except Exception as e:
            self.logger.error(f"Error during resource monitoring: {e}")
        
        return {'error': 'Monitoring failed', 'samples': samples}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        
        cache_time = self._cache[key]['timestamp']
        return time.time() - cache_time < self._cache_timeout
    
    def _update_cache(self, key: str, data: Any):
        """Update cache with new data."""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }


def check_system_requirements(
    project_root: Path = None,
    logger: logging.Logger = None
) -> Dict[str, Any]:
    """Check system requirements for wire_ground build environment."""
    
    # Define requirements for wire_ground project
    requirements = [
        SystemRequirement(
            name="CMake",
            requirement_type="version",
            check_command="cmake",
            min_version="3.20",
            required=True,
            description="CMake build system"
        ),
        SystemRequirement(
            name="C++ Compiler (GCC)",
            requirement_type="command",
            check_command="g++",
            required=True,
            description="GCC C++ compiler"
        ),
        SystemRequirement(
            name="C++ Compiler (Clang)",
            requirement_type="command",
            check_command="clang++",
            required=False,
            description="Clang C++ compiler (alternative)"
        ),
        SystemRequirement(
            name="Make",
            requirement_type="command",
            check_command="make",
            required=True,
            description="Make build tool"
        ),
        SystemRequirement(
            name="Git",
            requirement_type="command",
            check_command="git",
            required=True,
            description="Git version control"
        ),
        SystemRequirement(
            name="Available Memory",
            requirement_type="memory",
            min_memory_gb=2.0,
            required=True,
            description="Minimum available memory for builds"
        ),
        SystemRequirement(
            name="Free Disk Space",
            requirement_type="disk",
            min_disk_gb=5.0,
            required=True,
            description="Minimum free disk space for builds"
        ),
        SystemRequirement(
            name="clang-tidy",
            requirement_type="command",
            check_command="clang-tidy",
            required=False,
            description="Static analysis tool"
        ),
        SystemRequirement(
            name="Ninja",
            requirement_type="command",
            check_command="ninja",
            required=False,
            description="Ninja build system (optional)"
        )
    ]
    
    system_utils = SystemUtils(logger)
    return system_utils.check_system_requirements(requirements)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    system_utils = SystemUtils(logger)
    
    # Get system info
    print("=== System Information ===")
    sys_info = system_utils.get_system_info()
    print(json.dumps(sys_info, indent=2, default=str))
    
    # Check compilers
    print("\n=== Compiler Information ===")
    compiler_info = system_utils.get_compiler_info()
    print(json.dumps(compiler_info, indent=2))
    
    # Check build tools
    print("\n=== Build Tools Information ===")
    tools_info = system_utils.get_build_tools_info()
    print(json.dumps(tools_info, indent=2))
    
    # Check system requirements
    print("\n=== System Requirements Check ===")
    req_results = check_system_requirements(logger=logger)
    print(f"All requirements met: {req_results['all_met']}")
    print(f"Required requirements met: {req_results['required_met']}")
    print(f"Summary: {req_results['summary']}")
    
    for check in req_results['checks']:
        status = "✓" if check['passed'] else ("⚠" if not check['required'] else "✗")
        req_type = "REQUIRED" if check['required'] else "OPTIONAL"
        print(f"{status} {req_type:8} | {check['name']:20} | {check['message']}")
    
    # Optional: Resource monitoring (uncomment to test)
    # print("\n=== Resource Monitoring (10 seconds) ===")
    # monitoring_result = system_utils.monitor_resource_usage(10.0, 2.0)
    # if 'cpu_usage' in monitoring_result:
    #     print(f"CPU Usage: {monitoring_result['cpu_usage']['avg']:.1f}% avg")
    #     print(f"Memory Usage: {monitoring_result['memory_usage']['avg']:.1f}% avg")
    #     print(f"Load Average: {monitoring_result['load_average']['avg']:.2f}")