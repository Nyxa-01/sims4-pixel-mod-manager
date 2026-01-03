"""Additional tests for installer edge cases to reach 90%+ coverage."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.installer import ModInstaller


class TestInstallerEdgeCases:
    """Test installer edge cases and error paths."""

    def test_install_source_not_found(self, temp_mods_dir: Path) -> None:
        """Test install fails when source file doesn't exist."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = Path("/fake/nonexistent.package")

        with pytest.raises(FileNotFoundError):
            installer.install_mod(nonexistent, "CAS", 2)

    def test_install_copy_failure_cleanup(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test partial file is cleaned up when copy fails."""
        installer = ModInstaller(temp_mods_dir)

        # Mock copyfileobj to fail after creating the destination
        with patch("shutil.copyfileobj", side_effect=OSError("Disk full")):
            with pytest.raises(OSError, match="Disk full"):
                installer.install_mod(sample_package_mod, "CAS", 2)

            # Verify partial file doesn't exist
            expected_file = temp_mods_dir / "002_CAS" / sample_package_mod.name
            assert not expected_file.exists()

    def test_install_hash_mismatch_cleanup(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test corrupted file is deleted when hash doesn't match."""
        installer = ModInstaller(temp_mods_dir)

        # Mock hash_file to return different values for source and dest
        call_count = 0

        def mock_hash(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0xABCD1234  # Source hash
            else:
                return 0x12345678  # Dest hash (different)

        with patch("src.core.installer.hash_file", side_effect=mock_hash):
            with pytest.raises(ValueError, match="corruption detected"):
                installer.install_mod(sample_package_mod, "CAS", 2)

            # Verify corrupted file was deleted
            expected_file = temp_mods_dir / "002_CAS" / sample_package_mod.name
            assert not expected_file.exists()

    def test_install_duplicate_with_different_content(
        self,
        temp_mods_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test installing mod when file with same name but different content exists."""
        installer = ModInstaller(temp_mods_dir)

        # Create original mod
        original = tmp_path / "mod.package"
        original.write_bytes(b"DBPF" + b"original content")

        # Install first version
        installer.install_mod(original, "CAS", 2)

        # Create new version with same name but different content
        new_version = tmp_path / "mod.package"
        new_version.write_bytes(b"DBPF" + b"new content")

        # Install new version (should overwrite)
        result = installer.install_mod(new_version, "CAS", 2)
        assert result is True

        # Verify new content
        installed = temp_mods_dir / "002_CAS" / "mod.package"
        assert installed.read_bytes() == b"DBPF" + b"new content"

    def test_uninstall_mod_not_found(self, temp_mods_dir: Path) -> None:
        """Test uninstalling non-existent mod returns False."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = temp_mods_dir / "does_not_exist.package"

        result = installer.uninstall_mod(nonexistent)

        assert result is False

    def test_uninstall_permission_error(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test uninstall handles permission errors gracefully."""
        installer = ModInstaller(temp_mods_dir)

        # Install mod first
        installer.install_mod(sample_package_mod, "CAS", 2)
        installed_path = temp_mods_dir / "002_CAS" / sample_package_mod.name

        # Mock unlink to raise PermissionError
        with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
            result = installer.uninstall_mod(installed_path)

            assert result is False

    def test_backup_mod_not_found(self, temp_mods_dir: Path, tmp_path: Path) -> None:
        """Test backing up non-existent mod returns None."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = Path("/fake/nonexistent.package")
        backup_dir = tmp_path / "backups"

        result = installer.backup_mod(nonexistent, backup_dir)

        assert result is None

    def test_backup_mod_hash_mismatch(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup is deleted when hash verification fails."""
        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"

        # Mock hash_file to return different values
        call_count = 0

        def mock_hash(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0xABCD1234  # Source hash
            else:
                return 0x12345678  # Backup hash (different)

        with patch("src.core.installer.hash_file", side_effect=mock_hash):
            result = installer.backup_mod(sample_package_mod, backup_dir)

            assert result is None
            # Verify backup file was deleted
            backup_path = backup_dir / sample_package_mod.name
            assert not backup_path.exists()

    def test_backup_mod_copy_failure(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup handles copy errors gracefully."""
        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"

        # Mock copy2 to raise exception
        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            result = installer.backup_mod(sample_package_mod, backup_dir)

            assert result is None

    def test_backup_mod_creates_directory(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup creates backup directory if it doesn't exist."""
        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "nested" / "backup" / "dir"

        # Directory doesn't exist initially
        assert not backup_dir.exists()

        result = installer.backup_mod(sample_package_mod, backup_dir)

        # Directory should be created
        assert backup_dir.exists()
        assert result is not None
        assert result.exists()

    def test_backup_cleanup_on_exception(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test partial backup file is cleaned up when exception occurs."""
        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"
        backup_path = backup_dir / sample_package_mod.name

        # Mock hash_file to fail after copy
        def mock_hash_with_error(path):
            if path == backup_path:
                raise OSError("Read error")
            return 0xABCD1234

        with patch("src.core.installer.hash_file", side_effect=mock_hash_with_error):
            result = installer.backup_mod(sample_package_mod, backup_dir)

            assert result is None
            # Verify partial backup was cleaned up
            assert not backup_path.exists()

    def test_install_logging(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        caplog,
    ) -> None:
        """Test installer logs operations."""
        installer = ModInstaller(temp_mods_dir)

        with caplog.at_level(logging.INFO):
            installer.install_mod(sample_package_mod, "CAS", 2)

        # Check log messages
        assert "Installing mod" in caplog.text
        assert sample_package_mod.name in caplog.text
        assert "Successfully installed" in caplog.text

    def test_install_duplicate_logs_warning(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        caplog,
    ) -> None:
        """Test duplicate installation logs warning."""
        installer = ModInstaller(temp_mods_dir)

        # Install once
        installer.install_mod(sample_package_mod, "CAS", 2)

        # Install again with logging
        with caplog.at_level(logging.WARNING):
            installer.install_mod(sample_package_mod, "CAS", 2)

        assert "already exists" in caplog.text.lower()

    def test_script_mod_root_level_only(
        self,
        temp_mods_dir: Path,
        sample_script_mod: Path,
    ) -> None:
        """Test script mods are always placed at root level regardless of category."""
        installer = ModInstaller(temp_mods_dir)

        # Install with different categories - all should go to root
        result = installer.install_mod(
            sample_script_mod,
            category="DeepNestedCategory",
            slot=999,
            is_script=True,
        )

        assert result is True

        # Verify it's in root, not in 999_DeepNestedCategory/
        expected_root_file = temp_mods_dir / sample_script_mod.name
        assert expected_root_file.exists()

        # Verify category folder wasn't created
        category_folder = temp_mods_dir / "999_DeepNestedCategory"
        assert not category_folder.exists()
