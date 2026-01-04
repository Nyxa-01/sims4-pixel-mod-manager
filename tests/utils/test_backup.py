"""Tests for backup manager."""

import json
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.exceptions import BackupError
from src.utils.backup import (
    DEFAULT_RETENTION_COUNT,
    MANIFEST_FILENAME,
    MAX_BACKUP_SIZE_WARNING,
    BackupInfo,
    BackupManager,
    get_default_backup_manager,
)


@pytest.fixture
def manager() -> BackupManager:
    """Create BackupManager instance.

    Returns:
        BackupManager instance
    """
    return BackupManager()


@pytest.fixture
def sample_files(tmp_path: Path) -> Path:
    """Create sample files for backup.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample directory
    """
    source = tmp_path / "ActiveMods"
    source.mkdir()

    # Create test files
    (source / "mod1.package").write_bytes(b"DBPF" + b"\x00" * 100)
    (source / "mod2.package").write_bytes(b"DBPF" + b"\x00" * 200)

    subfolder = source / "subfolder"
    subfolder.mkdir()
    (subfolder / "mod3.package").write_bytes(b"DBPF" + b"\x00" * 150)

    return source


class TestBackupManager:
    """Test BackupManager class."""

    def test_initialization(self, manager: BackupManager) -> None:
        """Test manager initialization."""
        assert manager.retention_count == DEFAULT_RETENTION_COUNT

    def test_initialization_custom_retention(self) -> None:
        """Test initialization with custom retention count."""
        manager = BackupManager(retention_count=5)
        assert manager.retention_count == 5

    def test_create_backup_success(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test successful backup creation."""
        backup_dir = tmp_path / "backups"

        backup_path = manager.create_backup(
            source=sample_files,
            backup_dir=backup_dir,
            game_version="1.108.329",
        )

        assert backup_path.exists()
        assert backup_path.suffix == ".zip"
        assert "backup_" in backup_path.name

        # Verify zip contents
        with zipfile.ZipFile(backup_path, "r") as zf:
            namelist = zf.namelist()
            assert MANIFEST_FILENAME in namelist
            assert "mod1.package" in namelist
            assert "mod2.package" in namelist

    def test_create_backup_with_progress(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup creation with progress callback."""
        backup_dir = tmp_path / "backups"
        progress_values: list[float] = []

        def progress_callback(pct: float) -> None:
            progress_values.append(pct)

        backup_path = manager.create_backup(
            source=sample_files,
            backup_dir=backup_dir,
            progress_callback=progress_callback,
        )

        assert backup_path.exists()
        assert len(progress_values) > 0
        assert progress_values[-1] == 100.0

    def test_create_backup_nonexistent_source(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test backup creation with nonexistent source."""
        source = tmp_path / "nonexistent"
        backup_dir = tmp_path / "backups"

        with pytest.raises(BackupError, match="does not exist"):
            manager.create_backup(source, backup_dir)

    def test_create_backup_empty_source(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test backup creation with empty source."""
        source = tmp_path / "empty"
        source.mkdir()
        backup_dir = tmp_path / "backups"

        with pytest.raises(BackupError, match="No files found"):
            manager.create_backup(source, backup_dir)

    def test_create_backup_manifest_content(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test manifest content in backup."""
        backup_dir = tmp_path / "backups"

        backup_path = manager.create_backup(
            source=sample_files,
            backup_dir=backup_dir,
            game_version="1.108.329",
        )

        # Read manifest
        with zipfile.ZipFile(backup_path, "r") as zf:
            manifest = json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))

        assert "timestamp" in manifest
        assert manifest["game_version"] == "1.108.329"
        assert manifest["total_files"] == 3
        assert "total_size_mb" in manifest
        assert len(manifest["files"]) == 3

        # Check file entries format (list of dicts with path and crc32)
        for file_entry in manifest["files"]:
            assert "path" in file_entry
            assert "crc32" in file_entry
            assert isinstance(file_entry["crc32"], int)  # CRC32 as integer

    def test_restore_backup_success(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test successful backup restoration."""
        backup_dir = tmp_path / "backups"
        restore_dir = tmp_path / "restored"

        # Create backup
        backup_path = manager.create_backup(sample_files, backup_dir)

        # Restore
        result = manager.restore_backup(backup_path, restore_dir)

        assert result is True
        assert (restore_dir / "mod1.package").exists()
        assert (restore_dir / "mod2.package").exists()
        assert (restore_dir / "subfolder" / "mod3.package").exists()

    def test_restore_backup_with_hash_verification(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test restoration with hash verification."""
        backup_dir = tmp_path / "backups"
        restore_dir = tmp_path / "restored"

        # Create backup
        backup_path = manager.create_backup(sample_files, backup_dir)

        # Restore with verification
        result = manager.restore_backup(backup_path, restore_dir, verify_hashes=True)

        assert result is True

    def test_restore_backup_nonexistent(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test restoration of nonexistent backup."""
        backup_path = tmp_path / "nonexistent.zip"
        restore_dir = tmp_path / "restored"

        with pytest.raises(BackupError, match="not found"):
            manager.restore_backup(backup_path, restore_dir)

    def test_restore_backup_corrupted_zip(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test restoration of corrupted backup."""
        backup_path = tmp_path / "corrupted.zip"
        backup_path.write_bytes(b"not a valid zip file")

        restore_dir = tmp_path / "restored"

        with pytest.raises(BackupError, match="corrupted"):
            manager.restore_backup(backup_path, restore_dir)

    def test_restore_backup_with_progress(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test restoration with progress callback."""
        backup_dir = tmp_path / "backups"
        restore_dir = tmp_path / "restored"

        backup_path = manager.create_backup(sample_files, backup_dir)

        progress_values: list[float] = []

        def progress_callback(pct: float) -> None:
            progress_values.append(pct)

        result = manager.restore_backup(
            backup_path, restore_dir, progress_callback=progress_callback
        )

        assert result is True
        assert len(progress_values) > 0

    def test_list_backups_empty(self, manager: BackupManager, tmp_path: Path) -> None:
        """Test listing backups in empty directory."""
        backup_dir = tmp_path / "backups"

        backups = manager.list_backups(backup_dir)

        assert backups == []

    def test_list_backups_multiple(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test listing multiple backups."""
        backup_dir = tmp_path / "backups"

        # Create multiple backups
        manager.create_backup(sample_files, backup_dir)
        manager.create_backup(sample_files, backup_dir)

        backups = manager.list_backups(backup_dir)

        assert len(backups) == 2
        assert all(isinstance(b, BackupInfo) for b in backups)
        assert backups[0].timestamp > backups[1].timestamp  # Newest first

    def test_list_backups_metadata(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup metadata in listing."""
        backup_dir = tmp_path / "backups"
        backup_path = manager.create_backup(sample_files, backup_dir)

        backups = manager.list_backups(backup_dir)

        assert len(backups) == 1
        backup_info = backups[0]

        assert backup_info.path == backup_path
        assert isinstance(backup_info.timestamp, datetime)
        assert backup_info.size_mb >= 0  # Small test files may round to 0.0 MB
        assert backup_info.file_count == 3
        assert backup_info.is_valid is True

    def test_delete_old_backups_none_to_delete(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test deletion when under retention limit."""
        backup_dir = tmp_path / "backups"

        # Create 2 backups (under default 10)
        manager.create_backup(sample_files, backup_dir)
        manager.create_backup(sample_files, backup_dir)

        deleted = manager.delete_old_backups(backup_dir)

        assert deleted == 0
        assert len(list(backup_dir.glob("backup_*.zip"))) == 2

    def test_delete_old_backups_exceed_retention(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test deletion when exceeding retention limit."""
        backup_dir = tmp_path / "backups"

        # Create 5 backups
        for _ in range(5):
            manager.create_backup(sample_files, backup_dir)

        # Delete oldest 2 (keep 3)
        deleted = manager.delete_old_backups(backup_dir, keep=3)

        assert deleted == 2
        assert len(list(backup_dir.glob("backup_*.zip"))) == 3

    def test_verify_backup_valid(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test verification of valid backup."""
        backup_dir = tmp_path / "backups"
        backup_path = manager.create_backup(sample_files, backup_dir)

        is_valid, error = manager.verify_backup(backup_path)

        assert is_valid is True
        assert error == ""

    def test_verify_backup_nonexistent(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test verification of nonexistent backup."""
        backup_path = tmp_path / "nonexistent.zip"

        is_valid, error = manager.verify_backup(backup_path)

        assert is_valid is False
        assert "not found" in error.lower()

    def test_verify_backup_corrupted(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test verification of corrupted backup."""
        backup_path = tmp_path / "corrupted.zip"
        backup_path.write_bytes(b"not a valid zip")

        is_valid, error = manager.verify_backup(backup_path)

        assert is_valid is False
        assert "not a valid zip" in error.lower() or "invalid" in error.lower()

    def test_verify_backup_missing_manifest(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test verification of backup without manifest."""
        backup_path = tmp_path / "no_manifest.zip"

        # Create zip without manifest
        with zipfile.ZipFile(backup_path, "w") as zf:
            zf.writestr("test.txt", "test data")

        is_valid, error = manager.verify_backup(backup_path)

        assert is_valid is False
        assert "missing manifest" in error.lower()

    def test_hash_file_consistency(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test file hashing produces consistent results."""
        test_file = tmp_path / "test.bin"
        test_data = b"test data for hashing"
        test_file.write_bytes(test_data)

        hash1 = manager._hash_file(test_file)
        hash2 = manager._hash_file(test_file)

        assert hash1 == hash2
        assert isinstance(hash1, int)

    def test_collect_files_excludes_system_files(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test file collection excludes system files."""
        source = tmp_path / "source"
        source.mkdir()

        # Create regular file
        (source / "mod.package").write_bytes(b"DBPF")

        # Create system files (should be excluded)
        (source / ".hidden").write_text("hidden")
        (source / "desktop.ini").write_text("system")

        files = manager._collect_files(source)

        assert len(files) == 1
        assert files[0].name == "mod.package"

    def test_test_zip_integrity_valid(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test zip integrity check with valid zip."""
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "test data")

        result = manager._test_zip_integrity(zip_path)

        assert result is True

    def test_test_zip_integrity_invalid(
        self,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test zip integrity check with invalid zip."""
        zip_path = tmp_path / "invalid.zip"
        zip_path.write_bytes(b"not a zip file")

        result = manager._test_zip_integrity(zip_path)

        assert result is False

    @patch("src.utils.backup.logger")
    def test_check_backup_size_warns_on_excessive_size(
        self,
        mock_logger: Mock,
        manager: BackupManager,
        tmp_path: Path,
    ) -> None:
        """Test warning when backup size exceeds limit."""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Create large fake backup
        large_backup = backup_dir / "backup_2026-01-01_120000.zip"
        large_backup.write_bytes(b"\x00" * (MAX_BACKUP_SIZE_WARNING + 1000))

        manager._check_backup_size(backup_dir)

        # Should have logged a warning
        mock_logger.warning.assert_called()

    def test_atomic_backup_creation(
        self,
        manager: BackupManager,
        sample_files: Path,
        tmp_path: Path,
    ) -> None:
        """Test that backup creation uses atomic writes."""
        backup_dir = tmp_path / "backups"

        # Should not find .tmp files after successful creation
        backup_path = manager.create_backup(sample_files, backup_dir)

        temp_files = list(backup_dir.glob("*.tmp"))
        assert len(temp_files) == 0
        assert backup_path.exists()

    def test_get_default_backup_manager(self) -> None:
        """Test getting default manager instance."""
        manager = get_default_backup_manager()

        assert isinstance(manager, BackupManager)
        assert manager.retention_count == DEFAULT_RETENTION_COUNT


class TestBackupInfo:
    """Test BackupInfo dataclass."""

    def test_backup_info_creation(self, tmp_path: Path) -> None:
        """Test BackupInfo instance creation."""
        info = BackupInfo(
            path=tmp_path / "backup.zip",
            timestamp=datetime.now(),
            size_mb=256.5,
            file_count=42,
            is_valid=True,
        )

        assert info.path == tmp_path / "backup.zip"
        assert isinstance(info.timestamp, datetime)
        assert info.size_mb == 256.5
        assert info.file_count == 42
        assert info.is_valid is True
