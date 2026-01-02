"""Production-grade backup manager with CRC32 integrity verification.

This module provides comprehensive backup and restore functionality with
integrity checking, retention policies, and progress reporting.
"""

import json
import logging
import zipfile
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.exceptions import BackupError, HashValidationError

logger = logging.getLogger(__name__)

# Backup configuration
DEFAULT_RETENTION_COUNT = 10
MAX_BACKUP_SIZE_WARNING = 5 * 1024 * 1024 * 1024  # 5GB

MANIFEST_FILENAME = "manifest.json"


@dataclass
class BackupInfo:
    """Backup metadata container.

    Attributes:
        path: Path to backup zip file
        timestamp: Backup creation time
        size_mb: Backup size in megabytes
        file_count: Number of files in backup
        is_valid: Whether backup passes integrity checks
    """

    path: Path
    timestamp: datetime
    size_mb: float
    file_count: int
    is_valid: bool


class BackupManager:
    """Production-grade backup system with integrity verification.

    Example:
        >>> manager = BackupManager()
        >>> backup_path = manager.create_backup(
        ...     source=Path("ActiveMods"),
        ...     backup_dir=Path("backups"),
        ...     progress_callback=lambda pct: print(f"{pct}%")
        ... )
        >>> if manager.verify_backup(backup_path):
        ...     print("Backup is valid")
    """

    def __init__(self, retention_count: int = DEFAULT_RETENTION_COUNT) -> None:
        """Initialize backup manager.

        Args:
            retention_count: Number of backups to keep
        """
        self.retention_count = retention_count

    def create_backup(
        self,
        source: Path,
        backup_dir: Path,
        game_version: str = "Unknown",
        progress_callback: Callable[[float], None] | None = None,
    ) -> Path:
        """Create timestamped backup with integrity manifest.

        Args:
            source: Source directory to backup (ActiveMods)
            backup_dir: Backup storage directory
            game_version: Game version string for manifest
            progress_callback: Optional callback(percentage)

        Returns:
            Path to created backup zip

        Raises:
            BackupError: On backup creation failure
        """
        if not source.exists():
            raise BackupError(
                f"Source path does not exist: {source}",
                recovery_hint="Ensure ActiveMods folder exists",
            )

        # Create backup directory
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise BackupError(
                f"Failed to create backup directory: {e}",
                recovery_hint="Check permissions",
            ) from e

        # Generate timestamped filename
        timestamp = datetime.now()
        filename = f"backup_{timestamp.strftime('%Y-%m-%d_%H%M%S')}.zip"
        backup_path = backup_dir / filename
        temp_path = backup_dir / f"{filename}.tmp"

        logger.info(f"Creating backup: {backup_path}")

        try:
            # Collect files to backup
            files_to_backup = self._collect_files(source)
            total_files = len(files_to_backup)

            if total_files == 0:
                raise BackupError(
                    "No files found to backup",
                    recovery_hint="Source directory is empty",
                )

            # Calculate file hashes and build manifest
            manifest = {
                "timestamp": timestamp.isoformat(),
                "game_version": game_version,
                "total_files": total_files,
                "total_size_mb": 0.0,
                "files": {},
            }

            total_size = 0

            # Create backup zip (atomic write to temp file)
            with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, file_path in enumerate(files_to_backup):
                    try:
                        # Calculate hash
                        file_hash = self._hash_file(file_path)
                        relative_path = file_path.relative_to(source)

                        # Add to manifest
                        manifest["files"][str(relative_path)] = f"{file_hash:08x}"

                        # Add to zip
                        zf.write(file_path, relative_path)

                        total_size += file_path.stat().st_size

                        # Report progress
                        if progress_callback:
                            progress = ((idx + 1) / total_files) * 90  # 0-90%
                            progress_callback(progress)

                    except Exception as e:
                        logger.warning(f"Failed to backup file {file_path}: {e}")
                        continue

                # Update manifest with total size
                manifest["total_size_mb"] = round(total_size / (1024 * 1024), 2)

                # Add manifest to zip
                zf.writestr(MANIFEST_FILENAME, json.dumps(manifest, indent=2))

            # Verify backup integrity
            if progress_callback:
                progress_callback(95)

            if not self._test_zip_integrity(temp_path):
                raise BackupError(
                    "Backup integrity check failed",
                    recovery_hint="Retry backup creation",
                )

            # Atomic rename (temp → final)
            temp_path.rename(backup_path)

            if progress_callback:
                progress_callback(100)

            logger.info(
                f"Backup created: {backup_path} "
                f"({manifest['total_size_mb']} MB, {total_files} files)"
            )

            # Apply retention policy
            self.delete_old_backups(backup_dir)

            # Check total backup size
            self._check_backup_size(backup_dir)

            return backup_path

        except Exception as e:
            # Cleanup temp file on failure
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            raise BackupError(
                f"Backup creation failed: {e}",
                recovery_hint="Check disk space and permissions",
            ) from e

    def restore_backup(
        self,
        backup_path: Path,
        target: Path,
        verify_hashes: bool = True,
        progress_callback: Callable[[float], None] | None = None,
    ) -> bool:
        """Restore backup with integrity verification.

        Args:
            backup_path: Path to backup zip
            target: Target restoration directory
            verify_hashes: Whether to verify CRC32 hashes
            progress_callback: Optional callback(percentage)

        Returns:
            True if restoration successful

        Raises:
            BackupError: On restoration failure
        """
        if not backup_path.exists():
            raise BackupError(
                f"Backup file not found: {backup_path}",
                recovery_hint="Check backup path",
            )

        logger.info(f"Restoring backup: {backup_path}")

        try:
            # Verify backup integrity first
            if not self._test_zip_integrity(backup_path):
                raise BackupError(
                    "Backup file is corrupted",
                    recovery_hint="Try a different backup",
                )

            # Create target directory
            target.mkdir(parents=True, exist_ok=True)

            # Extract backup
            with zipfile.ZipFile(backup_path, "r") as zf:
                # Read manifest
                manifest = json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))
                total_files = manifest["total_files"]

                # Extract all files except manifest
                file_list = [f for f in zf.namelist() if f != MANIFEST_FILENAME]

                for idx, filename in enumerate(file_list):
                    zf.extract(filename, target)

                    # Verify hash if requested
                    if verify_hashes and filename in manifest["files"]:
                        restored_file = target / filename
                        expected_hash = int(manifest["files"][filename], 16)
                        actual_hash = self._hash_file(restored_file)

                        if expected_hash != actual_hash:
                            raise HashValidationError(
                                restored_file,
                                expected_hash,
                                actual_hash,
                                recovery_hint="Backup may be corrupted",
                            )

                    # Report progress
                    if progress_callback:
                        progress = ((idx + 1) / total_files) * 100
                        progress_callback(progress)

            logger.info(f"Restored {total_files} files to {target}")
            return True

        except Exception as e:
            raise BackupError(
                f"Restoration failed: {e}",
                recovery_hint="Check target path permissions",
            ) from e

    def list_backups(self, backup_dir: Path) -> list[BackupInfo]:
        """List all backups with metadata.

        Args:
            backup_dir: Backup storage directory

        Returns:
            List of BackupInfo objects, sorted newest first
        """
        if not backup_dir.exists():
            return []

        backups: list[BackupInfo] = []

        for backup_file in backup_dir.glob("backup_*.zip"):
            try:
                # Parse timestamp from filename
                timestamp_str = backup_file.stem.replace("backup_", "")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")

                # Get file size
                size_mb = round(backup_file.stat().st_size / (1024 * 1024), 2)

                # Read manifest to get file count
                file_count = 0
                is_valid = False

                try:
                    with zipfile.ZipFile(backup_file, "r") as zf:
                        manifest = json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))
                        file_count = manifest["total_files"]
                        is_valid = self._test_zip_integrity(backup_file)
                except Exception:
                    is_valid = False

                backups.append(
                    BackupInfo(
                        path=backup_file,
                        timestamp=timestamp,
                        size_mb=size_mb,
                        file_count=file_count,
                        is_valid=is_valid,
                    )
                )

            except Exception as e:
                logger.warning(f"Failed to read backup {backup_file}: {e}")
                continue

        # Sort newest first
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    def delete_old_backups(self, backup_dir: Path, keep: int | None = None) -> int:
        """Delete old backups according to retention policy.

        Args:
            backup_dir: Backup storage directory
            keep: Number of backups to keep (uses default if None)

        Returns:
            Number of backups deleted
        """
        if keep is None:
            keep = self.retention_count

        backups = self.list_backups(backup_dir)

        if len(backups) <= keep:
            return 0

        # Delete oldest backups
        backups_to_delete = backups[keep:]
        deleted_count = 0

        for backup in backups_to_delete:
            try:
                backup.path.unlink()
                logger.info(f"Deleted old backup: {backup.path.name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete backup {backup.path}: {e}")

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old backup(s)")

        return deleted_count

    def verify_backup(self, backup_path: Path) -> tuple[bool, str]:
        """Verify backup integrity using CRC32 manifest.

        Args:
            backup_path: Path to backup ZIP file

        Returns:
            Tuple of (is_valid, error_message)
            - (True, "") if backup is valid
            - (False, "reason") if backup is corrupted
        """
        if not backup_path.exists():
            return (False, f"Backup not found: {backup_path}")

        if not zipfile.is_zipfile(backup_path):
            return (False, "Not a valid ZIP file")

        try:
            # Test zip integrity
            if not self._test_zip_integrity(backup_path):
                return (False, "ZIP file is corrupted")

            # Read and validate manifest
            with zipfile.ZipFile(backup_path, "r") as zf:
                if MANIFEST_FILENAME not in zf.namelist():
                    return (False, "Missing manifest.json")

                manifest_data = zf.read(MANIFEST_FILENAME)
                manifest = json.loads(manifest_data.decode("utf-8"))

                # Validate manifest structure
                required_keys = ["timestamp", "total_files", "files"]
                if not all(key in manifest for key in required_keys):
                    return (False, "Manifest has invalid structure")

                # Verify each file's CRC32 hash
                for filepath, expected_crc_hex in manifest.get("files", {}).items():
                    expected_crc = int(expected_crc_hex, 16)

                    # Normalize path separators - zipfile uses forward slashes
                    normalized_path = filepath.replace("\\", "/")

                    if normalized_path not in zf.namelist():
                        return (False, f"Missing file in backup: {filepath}")

                    # Calculate actual CRC32
                    file_data = zf.read(normalized_path)
                    actual_crc = zlib.crc32(file_data) & 0xFFFFFFFF

                    if actual_crc != expected_crc:
                        return (False, f"CRC mismatch for {filepath}")

            logger.debug(f"Backup verified: {backup_path}")
            return (True, "")

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return (False, f"Verification failed: {str(e)}")

    def _collect_files(self, source: Path) -> list[Path]:
        """Collect all files to backup.

        Args:
            source: Source directory

        Returns:
            List of file paths
        """
        files: list[Path] = []

        for file_path in source.rglob("*"):
            if file_path.is_file():
                # Skip system files
                if file_path.name.startswith(".") or file_path.name == "desktop.ini":
                    continue
                files.append(file_path)

        return files

    def _hash_file(self, path: Path) -> int:
        """Calculate CRC32 hash of file.

        Args:
            path: File path

        Returns:
            CRC32 hash value
        """
        with open(path, "rb") as f:
            return zlib.crc32(f.read())

    def _test_zip_integrity(self, zip_path: Path) -> bool:
        """Test zip file integrity.

        Args:
            zip_path: Path to zip file

        Returns:
            True if zip is valid
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # testzip() returns None if no errors
                result = zf.testzip()
                return result is None
        except Exception as e:
            logger.error(f"Zip integrity test failed: {e}")
            return False

    def _check_backup_size(self, backup_dir: Path) -> None:
        """Check total backup size and warn if excessive.

        Args:
            backup_dir: Backup storage directory
        """
        total_size = sum(f.stat().st_size for f in backup_dir.glob("backup_*.zip") if f.is_file())

        if total_size > MAX_BACKUP_SIZE_WARNING:
            size_gb = round(total_size / (1024 * 1024 * 1024), 2)
            logger.warning(f"Total backup size ({size_gb} GB) exceeds recommended limit (5 GB)")


def get_default_backup_manager() -> BackupManager:
    """Get default backup manager instance.

    Returns:
        Configured BackupManager
    """
    return BackupManager()
