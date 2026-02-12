"""Comprehensive tests for Never Fail Build Resolver tools to achieve 95%+ coverage."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import json
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    analyze_build_error, suggest_build_fixes, apply_build_fix,
    detect_build_system, run_build_command, validate_fix,
    backup_files, restore_backup, clean_build,
    check_dependencies, install_missing_dependencies
)
from dependencies import BuildResolverDependencies
from models import BuildSystem, ErrorType


class TestAnalyzeBuildError:
    """Test analyze_build_error tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.build_system = "cmake"
        deps.max_retry_attempts = 3
        deps.enable_logging = True
        return deps
    
    @pytest.mark.asyncio
    async def test_analyze_cmake_error(self, mock_deps):
        """Test analyzing CMake build error."""
        mock_ctx = Mock()
        error_log = """
        CMake Error at CMakeLists.txt:5 (add_executable):
          Cannot find source file: main.cpp
        """
        
        result = await analyze_build_error(
            mock_ctx,
            error_log=error_log,
            build_system="cmake",
            deps=mock_deps
        )
        
        assert "analysis" in result
        assert result["analysis"]["error_type"] == "missing_source_file"
        assert "main.cpp" in result["analysis"]["missing_files"]
        assert result["analysis"]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_analyze_compiler_error(self, mock_deps):
        """Test analyzing compiler error."""
        mock_ctx = Mock()
        error_log = """
        main.cpp:5:5: error: 'cout' was not declared in this scope
        main.cpp:5:5: note: suggested alternative: include <iostream>
        """
        
        result = await analyze_build_error(
            mock_ctx,
            error_log=error_log,
            build_system="cmake",
            deps=mock_deps
        )
        
        assert result["analysis"]["error_type"] == "missing_include"
        assert "iostream" in result["analysis"]["missing_includes"]
        assert result["analysis"]["file_path"] == "main.cpp"
        assert result["analysis"]["line_number"] == 5
    
    @pytest.mark.asyncio
    async def test_analyze_linker_error(self, mock_deps):
        """Test analyzing linker error."""
        mock_ctx = Mock()
        error_log = """
        /usr/bin/ld: main.o: undefined reference to `pthread_create'
        collect2: error: ld returned 1 exit status
        """
        
        result = await analyze_build_error(
            mock_ctx,
            error_log=error_log,
            build_system="cmake",
            deps=mock_deps
        )
        
        assert result["analysis"]["error_type"] == "missing_library"
        assert "pthread" in result["analysis"]["missing_libraries"]
        assert result["analysis"]["severity"] == "high"


class TestSuggestBuildFixes:
    """Test suggest_build_fixes tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.enable_automatic_fixes = True
        deps.safety_checks = True
        return deps
    
    @pytest.mark.asyncio
    async def test_suggest_missing_file_fix(self, mock_deps):
        """Test suggesting fix for missing source file."""
        mock_ctx = Mock()
        error_analysis = {
            "error_type": "missing_source_file",
            "missing_files": ["main.cpp"],
            "severity": "high"
        }
        
        result = await suggest_build_fixes(
            mock_ctx,
            error_analysis=error_analysis,
            deps=mock_deps
        )
        
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert any("create" in str(s).lower() for s in result["suggestions"])
        assert result["fix_priority"] == "high"
    
    @pytest.mark.asyncio
    async def test_suggest_include_fix(self, mock_deps):
        """Test suggesting fix for missing include."""
        mock_ctx = Mock()
        error_analysis = {
            "error_type": "missing_include",
            "missing_includes": ["iostream"],
            "file_path": "main.cpp",
            "line_number": 5
        }
        
        result = await suggest_build_fixes(
            mock_ctx,
            error_analysis=error_analysis,
            deps=mock_deps
        )
        
        assert "suggestions" in result
        assert any("#include <iostream>" in str(s) for s in result["suggestions"])
        assert result["automated_fix_available"] is True
    
    @pytest.mark.asyncio
    async def test_suggest_library_fix(self, mock_deps):
        """Test suggesting fix for missing library."""
        mock_ctx = Mock()
        error_analysis = {
            "error_type": "missing_library",
            "missing_libraries": ["pthread"],
            "severity": "high"
        }
        
        result = await suggest_build_fixes(
            mock_ctx,
            error_analysis=error_analysis,
            deps=mock_deps
        )
        
        assert "suggestions" in result
        assert any("pthread" in str(s).lower() for s in result["suggestions"])
        assert any("target_link_libraries" in str(s) for s in result["suggestions"])


class TestApplyBuildFix:
    """Test apply_build_fix tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.backup_enabled = True
        deps.safety_checks = True
        deps.record_fix = Mock()
        return deps
    
    @pytest.mark.asyncio
    async def test_apply_missing_file_fix(self, mock_deps):
        """Test applying fix for missing file."""
        mock_ctx = Mock()
        
        with patch('builtins.open', mock=Mock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await apply_build_fix(
                mock_ctx,
                fix_type="create_missing_file",
                file_path="/test/project/main.cpp",
                content="int main() { return 0; }",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert "main.cpp" in result["files_modified"]
            mock_deps.record_fix.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_apply_include_fix(self, mock_deps):
        """Test applying include fix."""
        mock_ctx = Mock()
        
        with patch('builtins.open', mock=Mock()) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "#include <iostream>\nint main() { return 0; }"
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await apply_build_fix(
                mock_ctx,
                fix_type="add_include",
                file_path="/test/project/main.cpp",
                include_directive="#include <vector>",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert "include added" in result["description"].lower()
    
    @pytest.mark.asyncio
    async def test_apply_cmake_fix(self, mock_deps):
        """Test applying CMake configuration fix."""
        mock_ctx = Mock()
        
        with patch('builtins.open', mock=Mock()) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "add_executable(app main.cpp)"
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await apply_build_fix(
                mock_ctx,
                fix_type="add_library_link",
                cmake_file="/test/project/CMakeLists.txt",
                library="pthread",
                target="app",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert "library link added" in result["description"].lower()


class TestDetectBuildSystem:
    """Test detect_build_system tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        return deps
    
    @pytest.mark.asyncio
    async def test_detect_cmake_system(self, mock_deps):
        """Test detecting CMake build system."""
        mock_ctx = Mock()
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = lambda path: str(path).endswith('CMakeLists.txt')
            
            result = await detect_build_system(
                mock_ctx,
                project_path="/test/project",
                deps=mock_deps
            )
            
            assert result["build_system"] == "cmake"
            assert "CMakeLists.txt" in result["detected_files"]
    
    @pytest.mark.asyncio
    async def test_detect_make_system(self, mock_deps):
        """Test detecting Make build system."""
        mock_ctx = Mock()
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = lambda path: str(path).endswith('Makefile')
            
            result = await detect_build_system(
                mock_ctx,
                project_path="/test/project",
                deps=mock_deps
            )
            
            assert result["build_system"] == "make"
            assert "Makefile" in result["detected_files"]
    
    @pytest.mark.asyncio
    async def test_detect_multiple_systems(self, mock_deps):
        """Test detecting multiple build systems."""
        mock_ctx = Mock()
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = await detect_build_system(
                mock_ctx,
                project_path="/test/project",
                deps=mock_deps
            )
            
            assert result["build_system"] == "cmake"  # CMake takes priority
            assert len(result["detected_files"]) >= 2


class TestRunBuildCommand:
    """Test run_build_command tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.build_timeout = 300
        deps.parallel_jobs = 4
        return deps
    
    @pytest.mark.asyncio
    async def test_run_cmake_build_success(self, mock_deps):
        """Test successful CMake build."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Build succeeded",
                stderr=""
            )
            
            result = await run_build_command(
                mock_ctx,
                build_system="cmake",
                command="build",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert result["exit_code"] == 0
            assert "succeeded" in result["stdout"].lower()
    
    @pytest.mark.asyncio
    async def test_run_build_failure(self, mock_deps):
        """Test build failure handling."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Build failed: missing file"
            )
            
            result = await run_build_command(
                mock_ctx,
                build_system="cmake",
                command="build",
                deps=mock_deps
            )
            
            assert result["success"] is False
            assert result["exit_code"] == 1
            assert "missing file" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_build_timeout(self, mock_deps):
        """Test build timeout handling."""
        mock_ctx = Mock()
        mock_deps.build_timeout = 1  # 1 second timeout
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('cmake', 1)
            
            result = await run_build_command(
                mock_ctx,
                build_system="cmake",
                command="build",
                deps=mock_deps
            )
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()


class TestValidateFix:
    """Test validate_fix tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.validation_enabled = True
        return deps
    
    @pytest.mark.asyncio
    async def test_validate_successful_fix(self, mock_deps):
        """Test validation of successful fix."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Build successful",
                stderr=""
            )
            
            result = await validate_fix(
                mock_ctx,
                fix_applied=True,
                test_build=True,
                deps=mock_deps
            )
            
            assert result["validation"]["success"] is True
            assert result["validation"]["build_successful"] is True
    
    @pytest.mark.asyncio
    async def test_validate_failed_fix(self, mock_deps):
        """Test validation of failed fix."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Build still fails"
            )
            
            result = await validate_fix(
                mock_ctx,
                fix_applied=True,
                test_build=True,
                deps=mock_deps
            )
            
            assert result["validation"]["success"] is False
            assert result["validation"]["build_successful"] is False
            assert "still fails" in result["validation"]["error"]


class TestBackupAndRestore:
    """Test backup_files and restore_backup tools."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.backup_directory = Path("/test/project/.backups")
        deps.backup_enabled = True
        return deps
    
    @pytest.mark.asyncio
    async def test_backup_files(self, mock_deps):
        """Test file backup functionality."""
        mock_ctx = Mock()
        
        with patch('shutil.copy2') as mock_copy, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            result = await backup_files(
                mock_ctx,
                files_to_backup=["/test/project/main.cpp", "/test/project/CMakeLists.txt"],
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert len(result["backed_up_files"]) == 2
            assert mock_copy.call_count == 2
    
    @pytest.mark.asyncio
    async def test_restore_backup(self, mock_deps):
        """Test backup restoration functionality."""
        mock_ctx = Mock()
        
        with patch('shutil.copy2') as mock_copy, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_exists.return_value = True
            
            result = await restore_backup(
                mock_ctx,
                backup_id="backup_20230901_120000",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert "restored" in result["message"].lower()


class TestCleanBuild:
    """Test clean_build tool."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.build_directory = Path("/test/project/build")
        return deps
    
    @pytest.mark.asyncio
    async def test_clean_cmake_build(self, mock_deps):
        """Test CMake build cleaning."""
        mock_ctx = Mock()
        
        with patch('shutil.rmtree') as mock_rmtree, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_exists.return_value = True
            
            result = await clean_build(
                mock_ctx,
                build_system="cmake",
                clean_type="full",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert "cleaned" in result["message"].lower()
            mock_rmtree.assert_called()
    
    @pytest.mark.asyncio
    async def test_clean_make_build(self, mock_deps):
        """Test Make build cleaning."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            result = await clean_build(
                mock_ctx,
                build_system="make",
                clean_type="standard",
                deps=mock_deps
            )
            
            assert result["success"] is True


class TestDependencyManagement:
    """Test check_dependencies and install_missing_dependencies tools."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.package_manager = "apt"
        deps.auto_install_dependencies = True
        return deps
    
    @pytest.mark.asyncio
    async def test_check_dependencies_all_present(self, mock_deps):
        """Test dependency checking when all dependencies are present."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            result = await check_dependencies(
                mock_ctx,
                required_packages=["cmake", "gcc"],
                deps=mock_deps
            )
            
            assert result["all_present"] is True
            assert len(result["missing_packages"]) == 0
    
    @pytest.mark.asyncio
    async def test_check_dependencies_missing(self, mock_deps):
        """Test dependency checking with missing packages."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            # cmake present, gcc missing
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),  # cmake found
                Mock(returncode=1, stdout="", stderr="command not found")  # gcc not found
            ]
            
            result = await check_dependencies(
                mock_ctx,
                required_packages=["cmake", "gcc"],
                deps=mock_deps
            )
            
            assert result["all_present"] is False
            assert "gcc" in result["missing_packages"]
    
    @pytest.mark.asyncio
    async def test_install_missing_dependencies(self, mock_deps):
        """Test installation of missing dependencies."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            result = await install_missing_dependencies(
                mock_ctx,
                missing_packages=["gcc", "g++"],
                package_manager="apt",
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert len(result["installed_packages"]) == 2
            assert "gcc" in result["installed_packages"]
    
    @pytest.mark.asyncio
    async def test_install_dependencies_failure(self, mock_deps):
        """Test handling of dependency installation failure."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Package not found"
            )
            
            result = await install_missing_dependencies(
                mock_ctx,
                missing_packages=["nonexistent-package"],
                package_manager="apt",
                deps=mock_deps
            )
            
            assert result["success"] is False
            assert "not found" in result["error"].lower()


class TestErrorRecovery:
    """Test error recovery and retry mechanisms."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = Mock(spec=BuildResolverDependencies)
        deps.project_root = Path("/test/project")
        deps.max_retry_attempts = 3
        deps.retry_delay = 1
        return deps
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_success(self, mock_deps):
        """Test retry mechanism with eventual success."""
        mock_ctx = Mock()
        
        call_count = 0
        def mock_subprocess(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Mock(returncode=1, stdout="", stderr="Temporary error")
            else:
                return Mock(returncode=0, stdout="Success", stderr="")
        
        with patch('subprocess.run', side_effect=mock_subprocess):
            result = await run_build_command(
                mock_ctx,
                build_system="cmake",
                command="build",
                retry_on_failure=True,
                deps=mock_deps
            )
            
            assert result["success"] is True
            assert result["retry_attempts"] >= 2
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_max_attempts(self, mock_deps):
        """Test retry mechanism reaching max attempts."""
        mock_ctx = Mock()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Persistent error"
            )
            
            result = await run_build_command(
                mock_ctx,
                build_system="cmake",
                command="build",
                retry_on_failure=True,
                deps=mock_deps
            )
            
            assert result["success"] is False
            assert result["retry_attempts"] == mock_deps.max_retry_attempts
            assert "max attempts" in result["error"].lower()