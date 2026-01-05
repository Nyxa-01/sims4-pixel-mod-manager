"""Tests for mod installer."""

from pathlib import Path

import pytest

from src.core.installer import ModInstaller, hash_file


class TestHashFile:
    """Test hash_file function."""

    def test_hash_file(self, tmp_path: Path) -> None:
        """Test file hashing."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        hash1 = hash_file(test_file)
        hash2 = hash_file(test_file)

        assert hash1 == hash2
        assert isinstance(hash1, int)

    def test_hash_file_not_found(self) -> None:
        """Test hash_file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            hash_file(Path("/nonexistent/file.txt"))


class TestModInstaller:
    """Test ModInstaller class."""

    def test_init(self, temp_mods_dir: Path) -> None:
        """Test installer initialization."""
        installer = ModInstaller(temp_mods_dir)
        assert installer.mods_folder == temp_mods_dir

    def test_init_mods_folder_not_found(self) -> None:
        """Test installer raises FileNotFoundError for missing folder."""
        with pytest.raises(FileNotFoundError):
            ModInstaller(Path("/nonexistent"))

    def test_install_package_mod(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test installing .package mod with category."""
        installer = ModInstaller(temp_mods_dir)

        result = installer.install_mod(
            sample_package_mod,
            category="CAS",
            slot=2,
            is_script=False,
        )

        assert result is True

        # Check file exists in category folder
        expected_dir = temp_mods_dir / "002_CAS"
        expected_file = expected_dir / "sample_mod.package"
        assert expected_file.exists()

        # Verify hash
        source_hash = hash_file(sample_package_mod)
        dest_hash = hash_file(expected_file)
        assert source_hash == dest_hash

    def test_install_script_mod_root_placement(
        self,
        temp_mods_dir: Path,
        sample_script_mod: Path,
    ) -> None:
        """Test script mod is installed to root level."""
        installer = ModInstaller(temp_mods_dir)

        result = installer.install_mod(
            sample_script_mod,
            category="ScriptMods",
            slot=1,
            is_script=True,
        )

        assert result is True

        # Check file is in root, not in category folder
        expected_file = temp_mods_dir / "sample_script.ts4script"
        assert expected_file.exists()

    def test_install_duplicate_mod(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test installing duplicate mod skips if identical."""
        installer = ModInstaller(temp_mods_dir)

        # Install once
        installer.install_mod(sample_package_mod, "CAS", 2)

        # Install again (should skip)
        result = installer.install_mod(sample_package_mod, "CAS", 2)
        assert result is True

    def test_uninstall_mod(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test uninstalling mod."""
        installer = ModInstaller(temp_mods_dir)

        # Install first
        installer.install_mod(sample_package_mod, "CAS", 2)
        installed_path = temp_mods_dir / "002_CAS" / "sample_mod.package"
        assert installed_path.exists()

        # Uninstall
        result = installer.uninstall_mod(installed_path)
        assert result is True
        assert not installed_path.exists()

    def test_backup_mod(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backing up mod."""
        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"

        backup_path = installer.backup_mod(sample_package_mod, backup_dir)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name == sample_package_mod.name

        # Verify hash
        source_hash = hash_file(sample_package_mod)
        backup_hash = hash_file(backup_path)
        assert source_hash == backup_hash

    def test_install_mod_source_not_found(self, temp_mods_dir: Path) -> None:
        """Test install_mod raises FileNotFoundError when source doesn't exist."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = temp_mods_dir / "nonexistent.package"

        with pytest.raises(FileNotFoundError, match="Source mod not found"):
            installer.install_mod(nonexistent, category="CAS", slot=2)

    def test_uninstall_mod_not_found(self, temp_mods_dir: Path) -> None:
        """Test uninstall_mod returns False when mod doesn't exist."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = temp_mods_dir / "nonexistent.package"

        result = installer.uninstall_mod(nonexistent)

        assert result is False

    def test_uninstall_mod_exception(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test uninstall_mod returns False on exception."""
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)

        # Install mod first
        installer.install_mod(sample_package_mod, "CAS", 2)
        installed_path = temp_mods_dir / "002_CAS" / "sample_mod.package"
        assert installed_path.exists()

        # Mock unlink to raise exception
        with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
            result = installer.uninstall_mod(installed_path)

        assert result is False

    def test_backup_mod_not_found(self, temp_mods_dir: Path, tmp_path: Path) -> None:
        """Test backup_mod returns None when mod doesn't exist."""
        installer = ModInstaller(temp_mods_dir)
        nonexistent = temp_mods_dir / "nonexistent.package"
        backup_dir = tmp_path / "backups"

        result = installer.backup_mod(nonexistent, backup_dir)

        assert result is None

    def test_backup_mod_exception(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup_mod returns None on copy exception."""
        import shutil
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"

        # Mock shutil.copy2 to raise exception
        with patch.object(shutil, "copy2", side_effect=PermissionError("Access denied")):
            result = installer.backup_mod(sample_package_mod, backup_dir)

        assert result is None

    def test_backup_mod_exception_with_cleanup(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup_mod cleans up partial backup file on exception."""
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir(parents=True)
        expected_backup = backup_dir / sample_package_mod.name

        # Create a partial backup file to simulate interrupted copy
        expected_backup.write_bytes(b"partial data")
        assert expected_backup.exists()

        # Mock hash_file to fail on the backup file
        original_hash_file = hash_file
        call_count = 0

        def mock_hash_file(path: Path) -> int:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_hash_file(path)  # Source hash succeeds
            raise IOError("Disk read error")  # Backup hash fails

        with patch("src.core.installer.hash_file", side_effect=mock_hash_file):
            result = installer.backup_mod(sample_package_mod, backup_dir)

        assert result is None
        # Verify partial file was cleaned up
        assert not expected_backup.exists()

    def test_backup_mod_hash_mismatch(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup_mod returns None when hash mismatch detected."""
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)
        backup_dir = tmp_path / "backups"

        # Mock hash_file to return different values
        call_count = 0
        original_hash = hash_file(sample_package_mod)

        def mock_hash_file(path: Path) -> int:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_hash  # First call (source)
            return original_hash + 1  # Second call (backup) - different hash

        with patch("src.core.installer.hash_file", side_effect=mock_hash_file):
            result = installer.backup_mod(sample_package_mod, backup_dir)

        assert result is None

    def test_install_mod_copy_exception(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test install_mod raises exception and cleans up on copy failure."""
        import shutil
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)

        # Mock copyfileobj to raise exception
        with (
            patch.object(shutil, "copyfileobj", side_effect=IOError("Disk full")),
            pytest.raises(IOError, match="Disk full"),
        ):
            installer.install_mod(sample_package_mod, category="CAS", slot=2)

        # Verify partial file was cleaned up
        expected_file = temp_mods_dir / "002_CAS" / "sample_mod.package"
        assert not expected_file.exists()

    def test_install_mod_hash_mismatch_after_copy(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test install_mod detects hash mismatch after copy."""
        from unittest.mock import patch

        installer = ModInstaller(temp_mods_dir)
        original_hash = hash_file(sample_package_mod)

        call_count = 0

        def mock_hash_file(path: Path) -> int:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_hash  # First call (source before copy)
            return original_hash + 1  # Second call (dest after copy) - different

        with patch("src.core.installer.hash_file", side_effect=mock_hash_file):
            with pytest.raises(ValueError, match="File corruption detected"):
                installer.install_mod(sample_package_mod, category="CAS", slot=2)
