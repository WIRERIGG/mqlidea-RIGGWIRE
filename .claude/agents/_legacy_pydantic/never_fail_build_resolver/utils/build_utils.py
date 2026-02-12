"""Build system utilities and helpers for the never fail build resolver."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from dataclasses import dataclass
import json
import shutil
import os


class BuildSystemType(Enum):
    """Supported build system types."""
    CMAKE = "cmake"
    MAKE = "make" 
    NINJA = "ninja"
    AUTOTOOLS = "autotools"
    MESON = "meson"
    BAZEL = "bazel"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


@dataclass
class BuildTarget:
    """Information about a build target."""
    name: str
    type: str  # executable, library, custom, etc.
    sources: List[Path]
    dependencies: List[str]
    properties: Dict[str, Any]


@dataclass
class BuildSystemInfo:
    """Information about detected build system."""
    system_type: BuildSystemType
    version: Optional[str]
    config_files: List[Path]
    build_directory: Optional[Path]
    targets: List[BuildTarget]
    properties: Dict[str, Any]


class BuildSystemUtils:
    """Utilities for working with different build systems."""
    
    def __init__(self, project_root: Path, logger: logging.Logger = None):
        self.project_root = Path(project_root)
        self.logger = logger or logging.getLogger(__name__)
    
    def detect_build_system(self) -> BuildSystemInfo:
        """Detect the primary build system used in the project."""
        
        # Check for common build system files
        build_files = {
            BuildSystemType.CMAKE: ['CMakeLists.txt'],
            BuildSystemType.MAKE: ['Makefile', 'GNUmakefile'],
            BuildSystemType.NINJA: ['build.ninja'],
            BuildSystemType.AUTOTOOLS: ['configure.ac', 'configure.in', 'Makefile.am'],
            BuildSystemType.MESON: ['meson.build'],
            BuildSystemType.BAZEL: ['BUILD', 'BUILD.bazel', 'WORKSPACE']
        }
        
        detected_systems = []
        
        for system_type, filenames in build_files.items():
            for filename in filenames:
                if (self.project_root / filename).exists():
                    detected_systems.append(system_type)
                    break
        
        if not detected_systems:
            return BuildSystemInfo(
                system_type=BuildSystemType.UNKNOWN,
                version=None,
                config_files=[],
                build_directory=None,
                targets=[],
                properties={}
            )
        
        # Use the first detected system as primary
        primary_system = detected_systems[0]
        
        # Get detailed information about the primary system
        if primary_system == BuildSystemType.CMAKE:
            return self._analyze_cmake_system()
        elif primary_system == BuildSystemType.MAKE:
            return self._analyze_make_system()
        elif primary_system == BuildSystemType.NINJA:
            return self._analyze_ninja_system()
        else:
            return BuildSystemInfo(
                system_type=primary_system,
                version=None,
                config_files=[],
                build_directory=None,
                targets=[],
                properties={}
            )
    
    def _analyze_cmake_system(self) -> BuildSystemInfo:
        """Analyze CMake build system."""
        config_files = []
        
        # Find all CMakeLists.txt files
        cmake_files = list(self.project_root.rglob('CMakeLists.txt'))
        config_files.extend(cmake_files)
        
        # Find .cmake files
        cmake_module_files = list(self.project_root.rglob('*.cmake'))
        config_files.extend(cmake_module_files)
        
        # Get CMake version
        version = self._get_cmake_version()
        
        # Find build directory
        build_dir = self._find_cmake_build_directory()
        
        # Parse targets from CMakeLists.txt
        targets = self._parse_cmake_targets()
        
        properties = {
            'generator': self._get_cmake_generator(),
            'build_type': self._get_cmake_build_type(),
            'compiler': self._get_cmake_compiler_info()
        }
        
        return BuildSystemInfo(
            system_type=BuildSystemType.CMAKE,
            version=version,
            config_files=config_files,
            build_directory=build_dir,
            targets=targets,
            properties=properties
        )
    
    def _analyze_make_system(self) -> BuildSystemInfo:
        """Analyze Make build system."""
        config_files = []
        
        # Find Makefiles
        makefiles = ['Makefile', 'GNUmakefile', 'makefile']
        for makefile in makefiles:
            makefile_path = self.project_root / makefile
            if makefile_path.exists():
                config_files.append(makefile_path)
        
        # Find included makefiles
        included_makefiles = list(self.project_root.rglob('*.mk'))
        config_files.extend(included_makefiles)
        
        # Get Make version
        version = self._get_make_version()
        
        # Parse targets from Makefile
        targets = self._parse_make_targets()
        
        return BuildSystemInfo(
            system_type=BuildSystemType.MAKE,
            version=version,
            config_files=config_files,
            build_directory=None,  # Make typically builds in-place
            targets=targets,
            properties={}
        )
    
    def _analyze_ninja_system(self) -> BuildSystemInfo:
        """Analyze Ninja build system."""
        config_files = []
        
        # Find ninja files
        ninja_files = list(self.project_root.rglob('*.ninja'))
        config_files.extend(ninja_files)
        
        version = self._get_ninja_version()
        
        return BuildSystemInfo(
            system_type=BuildSystemType.NINJA,
            version=version,
            config_files=config_files,
            build_directory=self.project_root,  # Ninja files are typically in build dir
            targets=[],  # Would need to parse ninja files for targets
            properties={}
        )
    
    def _get_cmake_version(self) -> Optional[str]:
        """Get CMake version."""
        try:
            result = subprocess.run(
                ['cmake', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from output like "cmake version 3.22.1"
                match = re.search(r'cmake version (\d+\.\d+\.\d+)', result.stdout)
                return match.group(1) if match else None
        except Exception as e:
            self.logger.warning(f"Failed to get CMake version: {e}")
        return None
    
    def _get_make_version(self) -> Optional[str]:
        """Get Make version."""
        try:
            result = subprocess.run(
                ['make', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split('\n')[0]
                match = re.search(r'(\d+\.\d+(?:\.\d+)?)', first_line)
                return match.group(1) if match else None
        except Exception as e:
            self.logger.warning(f"Failed to get Make version: {e}")
        return None
    
    def _get_ninja_version(self) -> Optional[str]:
        """Get Ninja version."""
        try:
            result = subprocess.run(
                ['ninja', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.warning(f"Failed to get Ninja version: {e}")
        return None
    
    def _find_cmake_build_directory(self) -> Optional[Path]:
        """Find the CMake build directory."""
        common_build_dirs = [
            'build', 'cmake-build-debug', 'cmake-build-release',
            '_build', 'out/build', '.build'
        ]
        
        for build_dir_name in common_build_dirs:
            build_dir = self.project_root / build_dir_name
            if build_dir.exists() and (build_dir / 'CMakeCache.txt').exists():
                return build_dir
        
        return None
    
    def _get_cmake_generator(self) -> Optional[str]:
        """Get CMake generator from cache."""
        build_dir = self._find_cmake_build_directory()
        if not build_dir:
            return None
        
        cache_file = build_dir / 'CMakeCache.txt'
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    if line.startswith('CMAKE_GENERATOR:INTERNAL='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            self.logger.warning(f"Failed to read CMake generator: {e}")
        
        return None
    
    def _get_cmake_build_type(self) -> Optional[str]:
        """Get CMake build type from cache."""
        build_dir = self._find_cmake_build_directory()
        if not build_dir:
            return None
        
        cache_file = build_dir / 'CMakeCache.txt'
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    if line.startswith('CMAKE_BUILD_TYPE:STRING='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            self.logger.warning(f"Failed to read CMake build type: {e}")
        
        return None
    
    def _get_cmake_compiler_info(self) -> Dict[str, str]:
        """Get CMake compiler information."""
        build_dir = self._find_cmake_build_directory()
        if not build_dir:
            return {}
        
        cache_file = build_dir / 'CMakeCache.txt'
        if not cache_file.exists():
            return {}
        
        compiler_info = {}
        
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    if line.startswith('CMAKE_C_COMPILER:FILEPATH='):
                        compiler_info['c_compiler'] = line.split('=', 1)[1].strip()
                    elif line.startswith('CMAKE_CXX_COMPILER:FILEPATH='):
                        compiler_info['cxx_compiler'] = line.split('=', 1)[1].strip()
        except Exception as e:
            self.logger.warning(f"Failed to read CMake compiler info: {e}")
        
        return compiler_info
    
    def _parse_cmake_targets(self) -> List[BuildTarget]:
        """Parse targets from CMakeLists.txt files."""
        targets = []
        
        for cmake_file in self.project_root.rglob('CMakeLists.txt'):
            try:
                with open(cmake_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find executable targets
                exe_matches = re.findall(
                    r'add_executable\s*\(\s*(\w+)(?:\s+([^)]+))?\)',
                    content,
                    re.MULTILINE
                )
                
                for match in exe_matches:
                    target_name = match[0]
                    sources_str = match[1] if len(match) > 1 else ""
                    sources = [Path(s.strip()) for s in sources_str.split() if s.strip()]
                    
                    targets.append(BuildTarget(
                        name=target_name,
                        type='executable',
                        sources=sources,
                        dependencies=[],
                        properties={'cmake_file': cmake_file}
                    ))
                
                # Find library targets
                lib_matches = re.findall(
                    r'add_library\s*\(\s*(\w+)(?:\s+([^)]+))?\)',
                    content,
                    re.MULTILINE
                )
                
                for match in lib_matches:
                    target_name = match[0]
                    sources_str = match[1] if len(match) > 1 else ""
                    sources = [Path(s.strip()) for s in sources_str.split() if s.strip()]
                    
                    targets.append(BuildTarget(
                        name=target_name,
                        type='library',
                        sources=sources,
                        dependencies=[],
                        properties={'cmake_file': cmake_file}
                    ))
                
            except Exception as e:
                self.logger.warning(f"Failed to parse CMake file {cmake_file}: {e}")
        
        return targets
    
    def _parse_make_targets(self) -> List[BuildTarget]:
        """Parse targets from Makefile."""
        targets = []
        
        makefile_path = None
        for makefile_name in ['Makefile', 'GNUmakefile', 'makefile']:
            path = self.project_root / makefile_name
            if path.exists():
                makefile_path = path
                break
        
        if not makefile_path:
            return targets
        
        try:
            with open(makefile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find make targets (lines that end with :)
            target_matches = re.findall(r'^([^#\s][^:=]*?):', content, re.MULTILINE)
            
            for match in target_matches:
                target_name = match.strip()
                if target_name and not target_name.startswith('.'):
                    targets.append(BuildTarget(
                        name=target_name,
                        type='make_target',
                        sources=[],
                        dependencies=[],
                        properties={'makefile': makefile_path}
                    ))
        
        except Exception as e:
            self.logger.warning(f"Failed to parse Makefile {makefile_path}: {e}")
        
        return targets
    
    def get_build_command(self, target: str = None, parallel_jobs: int = None) -> str:
        """Get the appropriate build command for the detected build system."""
        system_info = self.detect_build_system()
        
        if system_info.system_type == BuildSystemType.CMAKE:
            build_dir = system_info.build_directory or (self.project_root / 'cmake-build-debug')
            cmd = f"cmake --build {build_dir}"
            
            if target:
                cmd += f" --target {target}"
            else:
                cmd += " --target all"
            
            if parallel_jobs:
                cmd += f" -j {parallel_jobs}"
            
            return cmd
        
        elif system_info.system_type == BuildSystemType.MAKE:
            cmd = "make"
            
            if target:
                cmd += f" {target}"
            
            if parallel_jobs:
                cmd += f" -j{parallel_jobs}"
            
            return cmd
        
        elif system_info.system_type == BuildSystemType.NINJA:
            cmd = "ninja"
            
            if target:
                cmd += f" {target}"
            
            if parallel_jobs:
                cmd += f" -j {parallel_jobs}"
            
            return cmd
        
        else:
            return "echo 'Unknown build system'"
    
    def get_clean_command(self) -> str:
        """Get the appropriate clean command for the detected build system."""
        system_info = self.detect_build_system()
        
        if system_info.system_type == BuildSystemType.CMAKE:
            build_dir = system_info.build_directory or (self.project_root / 'cmake-build-debug')
            return f"cmake --build {build_dir} --target clean"
        
        elif system_info.system_type == BuildSystemType.MAKE:
            return "make clean"
        
        elif system_info.system_type == BuildSystemType.NINJA:
            return "ninja clean"
        
        else:
            return "echo 'Unknown build system - cannot clean'"
    
    def get_configure_command(self, build_type: str = "Debug", extra_options: Dict[str, str] = None) -> str:
        """Get the appropriate configure command for the detected build system."""
        system_info = self.detect_build_system()
        
        if system_info.system_type == BuildSystemType.CMAKE:
            build_dir = system_info.build_directory or (self.project_root / 'cmake-build-debug')
            cmd = f"cmake -S {self.project_root} -B {build_dir} -DCMAKE_BUILD_TYPE={build_type}"
            
            if extra_options:
                for key, value in extra_options.items():
                    cmd += f" -D{key}={value}"
            
            return cmd
        
        elif system_info.system_type == BuildSystemType.AUTOTOOLS:
            return "./configure"
        
        else:
            return "echo 'No configure step needed'"
    
    def validate_build_environment(self) -> Dict[str, Any]:
        """Validate that the build environment is properly set up."""
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'system_info': {}
        }
        
        try:
            # Detect build system
            system_info = self.detect_build_system()
            validation_results['system_info'] = {
                'type': system_info.system_type.value,
                'version': system_info.version,
                'config_files': [str(f) for f in system_info.config_files],
                'targets': [t.name for t in system_info.targets]
            }
            
            if system_info.system_type == BuildSystemType.UNKNOWN:
                validation_results['valid'] = False
                validation_results['issues'].append("No supported build system detected")
                return validation_results
            
            # Check for required tools
            required_tools = self._get_required_tools(system_info.system_type)
            
            for tool in required_tools:
                if not shutil.which(tool):
                    validation_results['valid'] = False
                    validation_results['issues'].append(f"Required tool '{tool}' not found in PATH")
            
            # System-specific validations
            if system_info.system_type == BuildSystemType.CMAKE:
                self._validate_cmake_environment(system_info, validation_results)
            elif system_info.system_type == BuildSystemType.MAKE:
                self._validate_make_environment(system_info, validation_results)
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['issues'].append(f"Environment validation failed: {e}")
        
        return validation_results
    
    def _get_required_tools(self, system_type: BuildSystemType) -> List[str]:
        """Get list of required tools for the build system."""
        tool_requirements = {
            BuildSystemType.CMAKE: ['cmake'],
            BuildSystemType.MAKE: ['make'],
            BuildSystemType.NINJA: ['ninja'],
            BuildSystemType.AUTOTOOLS: ['autoconf', 'automake', 'libtool'],
            BuildSystemType.MESON: ['meson'],
            BuildSystemType.BAZEL: ['bazel']
        }
        
        return tool_requirements.get(system_type, [])
    
    def _validate_cmake_environment(self, system_info: BuildSystemInfo, results: Dict[str, Any]):
        """Validate CMake-specific environment."""
        # Check if build directory exists and is configured
        build_dir = system_info.build_directory
        
        if build_dir and build_dir.exists():
            cache_file = build_dir / 'CMakeCache.txt'
            if not cache_file.exists():
                results['warnings'].append(f"Build directory {build_dir} exists but is not configured")
        else:
            results['warnings'].append("No configured build directory found")
        
        # Check for compiler
        compiler_info = system_info.properties.get('compiler', {})
        if not compiler_info.get('cxx_compiler'):
            results['warnings'].append("No C++ compiler configured")
    
    def _validate_make_environment(self, system_info: BuildSystemInfo, results: Dict[str, Any]):
        """Validate Make-specific environment."""
        # Check if Makefile exists
        if not any('Makefile' in str(f) for f in system_info.config_files):
            results['issues'].append("No Makefile found")
        
        # Check for common make variables
        makefile_path = next((f for f in system_info.config_files if 'Makefile' in str(f)), None)
        if makefile_path:
            try:
                with open(makefile_path, 'r') as f:
                    content = f.read()
                
                if 'CXX' not in content and 'CC' not in content:
                    results['warnings'].append("No compiler variables (CC/CXX) found in Makefile")
            
            except Exception:
                pass


def detect_build_system_type(project_root: Path) -> BuildSystemType:
    """Simple build system detection utility function."""
    utils = BuildSystemUtils(project_root)
    system_info = utils.detect_build_system()
    return system_info.system_type


# Example usage and testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Use current directory or provided path
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    utils = BuildSystemUtils(project_path, logger)
    
    print(f"=== Build System Analysis for {project_path} ===")
    
    # Detect build system
    system_info = utils.detect_build_system()
    print(f"Detected build system: {system_info.system_type.value}")
    print(f"Version: {system_info.version}")
    print(f"Config files: {[str(f) for f in system_info.config_files]}")
    print(f"Build directory: {system_info.build_directory}")
    print(f"Targets: {[t.name for t in system_info.targets]}")
    
    # Get build commands
    print(f"\n=== Build Commands ===")
    print(f"Configure: {utils.get_configure_command()}")
    print(f"Build: {utils.get_build_command()}")
    print(f"Clean: {utils.get_clean_command()}")
    
    # Validate environment
    print(f"\n=== Environment Validation ===")
    validation = utils.validate_build_environment()
    print(f"Valid: {validation['valid']}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  ❌ {issue}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation['valid'] and not validation['issues']:
        print("✅ Build environment is valid!")