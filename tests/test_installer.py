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
