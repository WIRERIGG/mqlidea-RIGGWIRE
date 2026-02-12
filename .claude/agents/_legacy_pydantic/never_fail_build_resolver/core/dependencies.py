"""Dependency injection and build system integration for Never Fail Build Resolver."""

import sqlite3
import logging
import subprocess
import shutil
import os
import psutil
import platform
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import hashlib
import uuid

from .settings import BuildResolverSettings
from .models import (
    BuildContext, SystemDiagnostics, BuildConfiguration, 
    BackupInfo, PerformanceMetrics, BuildMonitoringEvent,
    BuildSystem
)

@dataclass
class BuildResolverDependencies:
    """Dependency container for the Never Fail Build Resolver Agent."""
    
    # Core dependencies
    settings: BuildResolverSettings
    db_connection: sqlite3.Connection
    logger: logging.Logger
    
    # Build system interfaces
    cmake_interface: 'CMakeInterface'
    make_interface: 'MakeInterface'
    ninja_interface: 'NinjaInterface'
    
    # System interfaces
    system_monitor: 'SystemMonitor'
    backup_manager: 'BackupManager'
    performance_tracker: 'PerformanceTracker'
    
    # Learning and caching
    learning_database: 'LearningDatabase'
    cache_manager: 'CacheManager'
    
    # Session management
    session_id: str
    build_context: BuildContext

class CMakeInterface:
    """Interface for CMake build system operations."""
    
    def __init__(self, settings: BuildResolverSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.cmake_binary = str(settings.cmake_binary_path)
    
    def get_version(self) -> Optional[str]:
        """Get CMake version."""
        try:
            result = subprocess.run(
                [self.cmake_binary, "--version"], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.split('\n')[0].split()[-1]
        except Exception as e:
            self.logger.warning(f"Failed to get CMake version: {e}")
        return None
    
    def configure_project(self, source_dir: Path, build_dir: Path, options: Dict[str, str] = None) -> bool:
        """Configure CMake project."""
        try:
            cmd = [
                self.cmake_binary,
                "-S", str(source_dir),
                "-B", str(build_dir)
            ]
            
            # Add configuration options
            if options:
                for key, value in options.items():
                    cmd.append(f"-D{key}={value}")
            
            self.logger.info(f"Running CMake configure: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("CMake configuration succeeded")
                return True
            else:
                self.logger.error(f"CMake configuration failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"CMake configure exception: {e}")
            return False
    
    def build_project(self, build_dir: Path, target: str = "all", parallel_jobs: int = None) -> tuple[bool, str]:
        """Build CMake project."""
        try:
            cmd = [
                self.cmake_binary,
                "--build", str(build_dir),
                "--target", target
            ]
            
            if parallel_jobs:
                cmd.extend(["-j", str(parallel_jobs)])
            
            self.logger.info(f"Running CMake build: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except Exception as e:
            self.logger.error(f"CMake build exception: {e}")
            return False, str(e)
    
    def get_cache_variables(self, build_dir: Path) -> Dict[str, str]:
        """Get CMake cache variables."""
        cache_file = build_dir / "CMakeCache.txt"
        cache_vars = {}
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key_type, value = line.split('=', 1)
                            if ':' in key_type:
                                key = key_type.split(':', 1)[0]
                                cache_vars[key] = value
            except Exception as e:
                self.logger.warning(f"Failed to read CMake cache: {e}")
        
        return cache_vars
    
    def clean_build(self, build_dir: Path) -> bool:
        """Clean CMake build directory."""
        try:
            if build_dir.exists():
                shutil.rmtree(build_dir)
                self.logger.info(f"Cleaned build directory: {build_dir}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to clean build directory: {e}")
        return False

class MakeInterface:
    """Interface for Make build system operations."""
    
    def __init__(self, settings: BuildResolverSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.make_binary = str(settings.make_binary_path)
    
    def build_project(self, build_dir: Path, target: str = "all", parallel_jobs: int = None) -> tuple[bool, str]:
        """Build with Make."""
        try:
            cmd = [self.make_binary, "-C", str(build_dir), target]
            
            if parallel_jobs:
                cmd.append(f"-j{parallel_jobs}")
            
            self.logger.info(f"Running Make: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except Exception as e:
            self.logger.error(f"Make build exception: {e}")
            return False, str(e)
    
    def clean_build(self, build_dir: Path) -> bool:
        """Clean Make build."""
        try:
            result = subprocess.run(
                [self.make_binary, "-C", str(build_dir), "clean"],
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Make clean exception: {e}")
            return False

class NinjaInterface:
    """Interface for Ninja build system operations."""
    
    def __init__(self, settings: BuildResolverSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.ninja_binary = str(settings.ninja_binary_path)
    
    def build_project(self, build_dir: Path, target: str = "", parallel_jobs: int = None) -> tuple[bool, str]:
        """Build with Ninja."""
        try:
            cmd = [self.ninja_binary, "-C", str(build_dir)]
            
            if target:
                cmd.append(target)
            
            if parallel_jobs:
                cmd.extend(["-j", str(parallel_jobs)])
            
            self.logger.info(f"Running Ninja: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            return result.returncode == 0, result.stdout + result.stderr
            
        except Exception as e:
            self.logger.error(f"Ninja build exception: {e}")
            return False, str(e)
    
    def clean_build(self, build_dir: Path) -> bool:
        """Clean Ninja build."""
        try:
            result = subprocess.run(
                [self.ninja_binary, "-C", str(build_dir), "clean"],
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Ninja clean exception: {e}")
            return False

class SystemMonitor:
    """Monitor system resources and health."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def get_system_diagnostics(self) -> SystemDiagnostics:
        """Get comprehensive system diagnostic information."""
        try:
            # OS information
            os_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
            
            # Disk space information
            disk_usage = psutil.disk_usage('/')
            disk_space = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percent_used": round((disk_usage.used / disk_usage.total) * 100, 1)
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
                "swap_total_gb": round(psutil.swap_memory().total / (1024**3), 2)
            }
            
            # Compiler versions
            compiler_versions = self._get_compiler_versions()
            
            # Tool versions  
            tool_versions = self._get_tool_versions()
            
            # Environment variables
            env_vars = {k: v for k, v in os.environ.items() 
                       if any(keyword in k.upper() for keyword in 
                             ['PATH', 'CMAKE', 'CC', 'CXX', 'LD', 'PKG', 'LIBRARY'])}
            
            return SystemDiagnostics(
                os_info=os_info,
                disk_space=disk_space,
                memory_info=memory_info,
                compiler_versions=compiler_versions,
                tool_versions=tool_versions,
                environment_variables=env_vars,
                recent_system_changes=[]  # TODO: Implement system change detection
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get system diagnostics: {e}")
            return SystemDiagnostics()
    
    def _get_compiler_versions(self) -> Dict[str, str]:
        """Get versions of available compilers."""
        compilers = {}
        compiler_commands = {
            "gcc": ["gcc", "--version"],
            "g++": ["g++", "--version"],
            "clang": ["clang", "--version"],
            "clang++": ["clang++", "--version"]
        }
        
        for name, cmd in compiler_commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extract version from first line
                    first_line = result.stdout.split('\n')[0]
                    compilers[name] = first_line
            except Exception:
                compilers[name] = "not available"
        
        return compilers
    
    def _get_tool_versions(self) -> Dict[str, str]:
        """Get versions of build tools."""
        tools = {}
        tool_commands = {
            "cmake": ["cmake", "--version"],
            "make": ["make", "--version"],
            "ninja": ["ninja", "--version"],
            "pkg-config": ["pkg-config", "--version"]
        }
        
        for name, cmd in tool_commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extract version from first line
                    first_line = result.stdout.split('\n')[0]
                    tools[name] = first_line
            except Exception:
                tools[name] = "not available"
        
        return tools
    
    def check_disk_space(self, required_gb: float = 1.0) -> bool:
        """Check if sufficient disk space is available."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            return free_gb >= required_gb
        except Exception:
            return True  # Assume OK if can't check

class BackupManager:
    """Manage backups before applying resolutions."""
    
    def __init__(self, settings: BuildResolverSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.backup_dir = settings.get_backup_directory_path()
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def create_backup(self, items: List[Path], backup_name: str = None) -> BackupInfo:
        """Create backup of specified files/directories."""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_id = str(uuid.uuid4())[:8]
        backup_path = self.backup_dir / f"{backup_name}_{backup_id}"
        backup_path.mkdir(exist_ok=True)
        
        backed_up_items = []
        total_size = 0
        
        try:
            for item in items:
                if item.exists():
                    dest = backup_path / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                        total_size += item.stat().st_size
                    elif item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                        total_size += sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    
                    backed_up_items.append(str(item))
                    self.logger.info(f"Backed up: {item} -> {dest}")
            
            # Create restore script
            restore_script = backup_path / "restore.sh"
            with open(restore_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# Restore script created {datetime.now()}\n")
                for item in backed_up_items:
                    item_path = Path(item)
                    backup_item = backup_path / item_path.name
                    f.write(f"cp -r '{backup_item}' '{item_path.parent}'\n")
            
            restore_script.chmod(0o755)
            
            return BackupInfo(
                backup_id=backup_id,
                backup_path=backup_path,
                backed_up_items=backed_up_items,
                size_bytes=total_size,
                restore_command=f"bash {restore_script}",
                expiry_date=datetime.now() + timedelta(days=30)
            )
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise
    
    def cleanup_old_backups(self):
        """Clean up old backups beyond retention limit."""
        try:
            backups = sorted(self.backup_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime)
            
            # Remove backups beyond retention limit
            if len(backups) > self.settings.max_backups_retained:
                for backup in backups[:-self.settings.max_backups_retained]:
                    shutil.rmtree(backup)
                    self.logger.info(f"Removed old backup: {backup}")
        
        except Exception as e:
            self.logger.warning(f"Backup cleanup failed: {e}")

class PerformanceTracker:
    """Track performance metrics for resolution operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = []
    
    def record_metrics(self, operation_name: str, duration: float, 
                      memory_usage: float = 0, cpu_usage: float = 0) -> PerformanceMetrics:
        """Record performance metrics for an operation."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            duration_seconds=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success_rate=1.0  # Will be updated based on historical data
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def get_average_metrics(self, operation_name: str) -> Optional[PerformanceMetrics]:
        """Get average metrics for an operation."""
        operation_metrics = [m for m in self.metrics if m.operation_name == operation_name]
        
        if not operation_metrics:
            return None
        
        count = len(operation_metrics)
        return PerformanceMetrics(
            operation_name=operation_name,
            duration_seconds=sum(m.duration_seconds for m in operation_metrics) / count,
            memory_usage_mb=sum(m.memory_usage_mb for m in operation_metrics) / count,
            cpu_usage_percent=sum(m.cpu_usage_percent for m in operation_metrics) / count,
            success_rate=sum(m.success_rate for m in operation_metrics) / count
        )

class LearningDatabase:
    """Database for storing learning data from successful resolutions."""
    
    def __init__(self, db_connection: sqlite3.Connection, logger: logging.Logger):
        self.db = db_connection
        self.logger = logger
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize learning database tables."""
        try:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS problem_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern_hash TEXT UNIQUE,
                    pattern_description TEXT,
                    error_category TEXT,
                    success_count INTEGER DEFAULT 0,
                    total_attempts INTEGER DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS successful_resolutions (
                    id INTEGER PRIMARY KEY,
                    problem_pattern_id INTEGER,
                    strategy_id TEXT,
                    success_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolution_time_seconds INTEGER,
                    context_factors TEXT,
                    FOREIGN KEY (problem_pattern_id) REFERENCES problem_patterns(id)
                );
                
                CREATE TABLE IF NOT EXISTS prevention_rules (
                    id INTEGER PRIMARY KEY,
                    rule_id TEXT UNIQUE,
                    rule_data TEXT,
                    effectiveness_score REAL,
                    last_triggered TIMESTAMP,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize learning database: {e}")
    
    def record_successful_resolution(self, problem_pattern: str, strategy_id: str, 
                                   resolution_time: int, context: Dict[str, Any]):
        """Record a successful resolution for learning."""
        try:
            pattern_hash = hashlib.md5(problem_pattern.encode(), usedforsecurity=False).hexdigest()
            
            # Insert or update problem pattern
            self.db.execute("""
                INSERT OR IGNORE INTO problem_patterns (pattern_hash, pattern_description, error_category)
                VALUES (?, ?, ?)
            """, (pattern_hash, problem_pattern, "general"))
            
            self.db.execute("""
                UPDATE problem_patterns 
                SET success_count = success_count + 1, last_seen = CURRENT_TIMESTAMP
                WHERE pattern_hash = ?
            """, (pattern_hash,))
            
            # Get pattern ID
            pattern_id = self.db.execute("""
                SELECT id FROM problem_patterns WHERE pattern_hash = ?
            """, (pattern_hash,)).fetchone()[0]
            
            # Record successful resolution
            self.db.execute("""
                INSERT INTO successful_resolutions 
                (problem_pattern_id, strategy_id, resolution_time_seconds, context_factors)
                VALUES (?, ?, ?, ?)
            """, (pattern_id, strategy_id, resolution_time, json.dumps(context)))
            
            self.db.commit()
            self.logger.info(f"Recorded successful resolution: {strategy_id} for pattern {pattern_hash}")
            
        except Exception as e:
            self.logger.error(f"Failed to record successful resolution: {e}")
    
    def get_best_strategy(self, problem_pattern: str) -> Optional[str]:
        """Get the best strategy for a problem pattern based on historical data."""
        try:
            pattern_hash = hashlib.md5(problem_pattern.encode(), usedforsecurity=False).hexdigest()
            
            result = self.db.execute("""
                SELECT sr.strategy_id, COUNT(*) as success_count,
                       AVG(sr.resolution_time_seconds) as avg_time
                FROM successful_resolutions sr
                JOIN problem_patterns pp ON sr.problem_pattern_id = pp.id
                WHERE pp.pattern_hash = ?
                GROUP BY sr.strategy_id
                ORDER BY success_count DESC, avg_time ASC
                LIMIT 1
            """, (pattern_hash,)).fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get best strategy: {e}")
            return None

class CacheManager:
    """Manage caching of analysis results and build data."""
    
    def __init__(self, settings: BuildResolverSettings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.cache_dir = settings.project_root / ".build_resolver_cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cached_analysis(self, problem_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        if not self.settings.cache_build_analysis:
            return None
        
        cache_file = self.cache_dir / f"{problem_hash}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if cache is still valid (24 hours)
                cached_time = datetime.fromisoformat(data.get('timestamp', ''))
                if datetime.now() - cached_time < timedelta(hours=24):
                    return data.get('analysis')
                
            except Exception as e:
                self.logger.warning(f"Failed to read cache: {e}")
        
        return None
    
    def cache_analysis(self, problem_hash: str, analysis: Dict[str, Any]):
        """Cache analysis result."""
        if not self.settings.cache_build_analysis:
            return
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis
            }
            
            cache_file = self.cache_dir / f"{problem_hash}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to cache analysis: {e}")

def create_dependencies(session_id: str = None) -> BuildResolverDependencies:
    """Create and initialize all dependencies for the build resolver."""
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    # Load settings
    from .settings import load_settings
    settings = load_settings()
    
    # Setup logging
    logger = logging.getLogger(f"build_resolver_{session_id}")
    logger.setLevel(getattr(logging, settings.build_resolver_log_level.upper()))
    
    # Create database connection
    db_path = settings.project_root / settings.build_resolver_db_path
    db_connection = sqlite3.connect(str(db_path))
    
    # Initialize interfaces
    cmake_interface = CMakeInterface(settings, logger)
    make_interface = MakeInterface(settings, logger)
    ninja_interface = NinjaInterface(settings, logger)
    
    # Initialize system components
    system_monitor = SystemMonitor(logger)
    backup_manager = BackupManager(settings, logger)
    performance_tracker = PerformanceTracker(logger)
    
    # Initialize learning and caching
    learning_database = LearningDatabase(db_connection, logger)
    cache_manager = CacheManager(settings, logger)
    
    # Create build context
    build_context = BuildContext(
        session_id=session_id,
        project_root=settings.project_root,
        current_working_directory=Path.cwd(),
        build_system=BuildSystem.CMAKE,  # Default to CMake
        active_build_configuration="Debug",
        environment_backup=dict(os.environ)
    )
    
    return BuildResolverDependencies(
        settings=settings,
        db_connection=db_connection,
        logger=logger,
        cmake_interface=cmake_interface,
        make_interface=make_interface,
        ninja_interface=ninja_interface,
        system_monitor=system_monitor,
        backup_manager=backup_manager,
        performance_tracker=performance_tracker,
        learning_database=learning_database,
        cache_manager=cache_manager,
        session_id=session_id,
        build_context=build_context
    )