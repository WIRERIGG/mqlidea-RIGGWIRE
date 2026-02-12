"""Safe file operations with rollback capabilities for build resolver."""

import shutil
import os
import hashlib
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import uuid


@dataclass
class FileOperationRecord:
    """Record of a file operation for rollback purposes."""
    operation_id: str
    operation_type: str  # 'create', 'modify', 'delete', 'copy', 'move'
    target_path: Path
    backup_path: Optional[Path]
    original_exists: bool
    original_hash: Optional[str]
    timestamp: datetime
    success: bool = False


class SafeFileOperations:
    """Safe file operations with automatic rollback capabilities."""
    
    def __init__(self, backup_dir: Path = None, logger: logging.Logger = None):
        self.backup_dir = backup_dir or Path(tempfile.gettempdir()) / "build_resolver_backups"
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logger or logging.getLogger(__name__)
        self.operations: List[FileOperationRecord] = []
        self.transaction_id = str(uuid.uuid4())[:8]
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Get SHA256 hash of file contents."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash file {file_path}: {e}")
            return None
    
    def _create_backup(self, source_path: Path) -> Optional[Path]:
        """Create backup of a file or directory."""
        if not source_path.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.name}_{self.transaction_id}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            if source_path.is_file():
                shutil.copy2(source_path, backup_path)
            elif source_path.is_dir():
                shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
            
            self.logger.debug(f"Created backup: {source_path} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {source_path}: {e}")
            return None
    
    def safe_write_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """Safely write content to a file with rollback support."""
        file_path = Path(file_path)
        operation_id = str(uuid.uuid4())[:8]
        
        # Record original state
        original_exists = file_path.exists()
        original_hash = self._get_file_hash(file_path) if original_exists else None
        backup_path = self._create_backup(file_path) if original_exists else None
        
        operation = FileOperationRecord(
            operation_id=operation_id,
            operation_type='modify' if original_exists else 'create',
            target_path=file_path,
            backup_path=backup_path,
            original_exists=original_exists,
            original_hash=original_hash,
            timestamp=datetime.now()
        )
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Atomic move to final location
            temp_path.replace(file_path)
            
            operation.success = True
            self.operations.append(operation)
            
            self.logger.debug(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            operation.success = False
            self.operations.append(operation)
            return False
    
    def safe_copy_file(self, source_path: Path, dest_path: Path, preserve_metadata: bool = True) -> bool:
        """Safely copy a file with rollback support."""
        source_path = Path(source_path)
        dest_path = Path(dest_path)
        operation_id = str(uuid.uuid4())[:8]
        
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {source_path}")
            return False
        
        # Record original state
        original_exists = dest_path.exists()
        original_hash = self._get_file_hash(dest_path) if original_exists else None
        backup_path = self._create_backup(dest_path) if original_exists else None
        
        operation = FileOperationRecord(
            operation_id=operation_id,
            operation_type='copy',
            target_path=dest_path,
            backup_path=backup_path,
            original_exists=original_exists,
            original_hash=original_hash,
            timestamp=datetime.now()
        )
        
        try:
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            
            operation.success = True
            self.operations.append(operation)
            
            self.logger.debug(f"Successfully copied file: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {source_path} -> {dest_path}: {e}")
            operation.success = False
            self.operations.append(operation)
            return False
    
    def safe_move_file(self, source_path: Path, dest_path: Path) -> bool:
        """Safely move a file with rollback support."""
        source_path = Path(source_path)
        dest_path = Path(dest_path)
        operation_id = str(uuid.uuid4())[:8]
        
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {source_path}")
            return False
        
        # Record original state
        source_hash = self._get_file_hash(source_path)
        dest_exists = dest_path.exists()
        dest_backup = self._create_backup(dest_path) if dest_exists else None
        
        # Create backup of source (for rollback)
        source_backup = self._create_backup(source_path)
        
        operation = FileOperationRecord(
            operation_id=operation_id,
            operation_type='move',
            target_path=dest_path,
            backup_path=source_backup,  # Source backup for rollback
            original_exists=True,  # Source always exists for move
            original_hash=source_hash,
            timestamp=datetime.now()
        )
        
        try:
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(dest_path))
            
            operation.success = True
            self.operations.append(operation)
            
            self.logger.debug(f"Successfully moved file: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move file {source_path} -> {dest_path}: {e}")
            operation.success = False
            self.operations.append(operation)
            return False
    
    def safe_delete_file(self, file_path: Path) -> bool:
        """Safely delete a file with rollback support."""
        file_path = Path(file_path)
        operation_id = str(uuid.uuid4())[:8]
        
        if not file_path.exists():
            self.logger.warning(f"File does not exist (already deleted?): {file_path}")
            return True
        
        # Record original state and create backup
        original_hash = self._get_file_hash(file_path)
        backup_path = self._create_backup(file_path)
        
        operation = FileOperationRecord(
            operation_id=operation_id,
            operation_type='delete',
            target_path=file_path,
            backup_path=backup_path,
            original_exists=True,
            original_hash=original_hash,
            timestamp=datetime.now()
        )
        
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            operation.success = True
            self.operations.append(operation)
            
            self.logger.debug(f"Successfully deleted: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            operation.success = False
            self.operations.append(operation)
            return False
    
    def create_directory(self, dir_path: Path, parents: bool = True) -> bool:
        """Safely create directory with rollback support."""
        dir_path = Path(dir_path)
        operation_id = str(uuid.uuid4())[:8]
        
        original_exists = dir_path.exists()
        
        operation = FileOperationRecord(
            operation_id=operation_id,
            operation_type='create_dir',
            target_path=dir_path,
            backup_path=None,
            original_exists=original_exists,
            original_hash=None,
            timestamp=datetime.now()
        )
        
        try:
            dir_path.mkdir(parents=parents, exist_ok=original_exists)
            
            operation.success = True
            self.operations.append(operation)
            
            self.logger.debug(f"Successfully created directory: {dir_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create directory {dir_path}: {e}")
            operation.success = False
            self.operations.append(operation)
            return False
    
    def rollback_operations(self, operation_limit: Optional[int] = None) -> bool:
        """Rollback file operations in reverse order."""
        if not self.operations:
            self.logger.info("No operations to rollback")
            return True
        
        # Get operations to rollback (in reverse order)
        ops_to_rollback = list(reversed(self.operations))
        if operation_limit:
            ops_to_rollback = ops_to_rollback[:operation_limit]
        
        rollback_success = True
        
        for operation in ops_to_rollback:
            self.logger.debug(f"Rolling back operation {operation.operation_id}: {operation.operation_type} on {operation.target_path}")
            
            try:
                if operation.operation_type == 'create':
                    # Remove created file
                    if operation.target_path.exists():
                        if operation.target_path.is_file():
                            operation.target_path.unlink()
                        elif operation.target_path.is_dir():
                            shutil.rmtree(operation.target_path)
                
                elif operation.operation_type == 'create_dir':
                    # Remove created directory if it wasn't there originally
                    if not operation.original_exists and operation.target_path.exists():
                        shutil.rmtree(operation.target_path)
                
                elif operation.operation_type in ['modify', 'copy']:
                    # Restore from backup or delete if didn't exist
                    if operation.original_exists and operation.backup_path:
                        if operation.backup_path.exists():
                            if operation.backup_path.is_file():
                                shutil.copy2(operation.backup_path, operation.target_path)
                            elif operation.backup_path.is_dir():
                                if operation.target_path.exists():
                                    shutil.rmtree(operation.target_path)
                                shutil.copytree(operation.backup_path, operation.target_path)
                    elif not operation.original_exists and operation.target_path.exists():
                        # File was created, so delete it
                        if operation.target_path.is_file():
                            operation.target_path.unlink()
                        elif operation.target_path.is_dir():
                            shutil.rmtree(operation.target_path)
                
                elif operation.operation_type == 'move':
                    # Restore source from backup
                    if operation.backup_path and operation.backup_path.exists():
                        # Calculate original source path (this is tricky for moves)
                        # For now, we'll restore to the backup location
                        self.logger.warning(f"Move rollback is complex - backup preserved at {operation.backup_path}")
                
                elif operation.operation_type == 'delete':
                    # Restore from backup
                    if operation.backup_path and operation.backup_path.exists():
                        if operation.backup_path.is_file():
                            shutil.copy2(operation.backup_path, operation.target_path)
                        elif operation.backup_path.is_dir():
                            shutil.copytree(operation.backup_path, operation.target_path)
                
                self.logger.debug(f"Successfully rolled back operation {operation.operation_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to rollback operation {operation.operation_id}: {e}")
                rollback_success = False
        
        if rollback_success:
            self.logger.info(f"Successfully rolled back {len(ops_to_rollback)} operations")
        else:
            self.logger.error(f"Rollback completed with some failures")
        
        return rollback_success
    
    def cleanup_backups(self, keep_count: int = 5):
        """Clean up old backup files."""
        try:
            # Get all backup files sorted by modification time
            backup_files = sorted(
                self.backup_dir.glob(f"*_{self.transaction_id}_*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups beyond keep_count
            for backup_file in backup_files[keep_count:]:
                if backup_file.is_file():
                    backup_file.unlink()
                elif backup_file.is_dir():
                    shutil.rmtree(backup_file)
                
                self.logger.debug(f"Cleaned up old backup: {backup_file}")
        
        except Exception as e:
            self.logger.warning(f"Failed to clean up backups: {e}")
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of all operations performed."""
        summary = {
            'transaction_id': self.transaction_id,
            'total_operations': len(self.operations),
            'successful_operations': sum(1 for op in self.operations if op.success),
            'failed_operations': sum(1 for op in self.operations if not op.success),
            'operations_by_type': {},
            'operations': []
        }
        
        # Count by type
        for operation in self.operations:
            op_type = operation.operation_type
            if op_type not in summary['operations_by_type']:
                summary['operations_by_type'][op_type] = {'total': 0, 'successful': 0}
            
            summary['operations_by_type'][op_type]['total'] += 1
            if operation.success:
                summary['operations_by_type'][op_type]['successful'] += 1
        
        # Add operation details (convert to dict for JSON serialization)
        for operation in self.operations:
            op_dict = asdict(operation)
            # Convert Path objects to strings
            op_dict['target_path'] = str(op_dict['target_path'])
            if op_dict['backup_path']:
                op_dict['backup_path'] = str(op_dict['backup_path'])
            op_dict['timestamp'] = op_dict['timestamp'].isoformat()
            summary['operations'].append(op_dict)
        
        return summary


@contextmanager
def safe_file_transaction(backup_dir: Path = None, logger: logging.Logger = None):
    """Context manager for safe file operations with automatic rollback on failure."""
    file_ops = SafeFileOperations(backup_dir, logger)
    
    try:
        yield file_ops
        
        # If we get here, transaction was successful
        if logger:
            summary = file_ops.get_operation_summary()
            logger.info(f"File transaction completed successfully: {summary['successful_operations']}/{summary['total_operations']} operations")
        
    except Exception as e:
        if logger:
            logger.error(f"File transaction failed, rolling back: {e}")
        
        # Rollback operations on failure
        file_ops.rollback_operations()
        raise
    
    finally:
        # Clean up old backups
        file_ops.cleanup_backups()


# Utility functions for common operations

def create_backup(source_path: Path, backup_dir: Path = None) -> Optional[Path]:
    """Create a backup of a file or directory."""
    if backup_dir is None:
        backup_dir = Path(tempfile.gettempdir()) / "build_resolver_backups"
    
    backup_dir.mkdir(exist_ok=True, parents=True)
    
    if not source_path.exists():
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        if source_path.is_file():
            shutil.copy2(source_path, backup_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, backup_path)
        
        return backup_path
        
    except Exception:
        return None


def restore_backup(backup_path: Path, target_path: Path) -> bool:
    """Restore a file or directory from backup."""
    try:
        if not backup_path.exists():
            return False
        
        # Ensure target parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing target if it exists
        if target_path.exists():
            if target_path.is_file():
                target_path.unlink()
            elif target_path.is_dir():
                shutil.rmtree(target_path)
        
        # Restore from backup
        if backup_path.is_file():
            shutil.copy2(backup_path, target_path)
        elif backup_path.is_dir():
            shutil.copytree(backup_path, target_path)
        
        return True
        
    except Exception:
        return False


def atomic_write(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Atomically write content to a file."""
    file_path = Path(file_path)
    temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
    
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file
        with open(temp_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Atomic move to final location
        temp_path.replace(file_path)
        return True
        
    except Exception:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        return False


def safe_read_file(file_path: Path, encoding: str = 'utf-8', default: Optional[str] = None) -> Optional[str]:
    """Safely read file content with error handling."""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return default


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    test_dir = Path("/tmp/file_ops_test")
    test_dir.mkdir(exist_ok=True)
    
    # Test safe file transaction
    try:
        with safe_file_transaction(logger=logger) as file_ops:
            # Create a test file
            test_file = test_dir / "test.txt"
            file_ops.safe_write_file(test_file, "Hello, world!")
            
            # Copy it
            copy_file = test_dir / "test_copy.txt"
            file_ops.safe_copy_file(test_file, copy_file)
            
            # Modify original
            file_ops.safe_write_file(test_file, "Modified content!")
            
            # Create directory
            new_dir = test_dir / "subdir"
            file_ops.create_directory(new_dir)
            
            # Print summary
            summary = file_ops.get_operation_summary()
            print(f"Operations summary: {summary}")
            
            # Uncomment to test rollback
            # raise Exception("Test rollback")
            
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
    
    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)