"""Tests for mod scanner."""

from pathlib import Path

import pytest

from src.core.scanner import ModFile, ModScanner


class TestModFile:
    """Test ModFile class."""

    def test_init_valid_package(self, sample_package_mod: Path) -> None:
        """Test ModFile initialization with valid .package file."""
        mod = ModFile(sample_package_mod)
        assert mod.name == "sample_mod"
        assert mod.extension == ".package"
        assert mod.mod_type == "package"

    def test_init_valid_script(self, sample_script_mod: Path) -> None:
        """Test ModFile initialization with valid .ts4script file."""
        mod = ModFile(sample_script_mod)
        assert mod.name == "sample_script"
        assert mod.extension == ".ts4script"
        assert mod.mod_type == "script"

    def test_init_file_not_found(self) -> None:
        """Test ModFile raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            ModFile(Path("/nonexistent/file.package"))

    def test_init_invalid_extension(self, tmp_path: Path) -> None:
        """Test ModFile raises ValueError for invalid extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("test")

        with pytest.raises(ValueError, match="Invalid mod file type"):
            ModFile(invalid_file)

    def test_hash_calculation(self, sample_package_mod: Path) -> None:
        """Test CRC32 hash calculation."""
        mod = ModFile(sample_package_mod)
        hash1 = mod.hash
        hash2 = mod.hash  # Should be cached
        assert hash1 == hash2
        assert isinstance(hash1, int)


class TestModScanner:
    """Test ModScanner class."""

    def test_scan_empty_directory(self, temp_mods_dir: Path) -> None:
        """Test scanning empty directory."""
        scanner = ModScanner()
        result = scanner.scan_directory(temp_mods_dir)

        assert result["package"] == []
        assert result["script"] == []
        assert result["project"] == []

    def test_scan_with_mods(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
        sample_script_mod: Path,
    ) -> None:
        """Test scanning directory with mods."""
        # Copy mods to temp directory
        import shutil

        shutil.copy(sample_package_mod, temp_mods_dir)
        shutil.copy(sample_script_mod, temp_mods_dir)

        scanner = ModScanner()
        result = scanner.scan_directory(temp_mods_dir)

        assert len(result["package"]) == 1
        assert len(result["script"]) == 1
        assert result["package"][0].name == "sample_mod"
        assert result["script"][0].name == "sample_script"

    def test_scan_directory_not_found(self) -> None:
        """Test scanner raises FileNotFoundError for missing directory."""
        scanner = ModScanner()
        with pytest.raises(FileNotFoundError):
            scanner.scan_directory(Path("/nonexistent"))

    def test_scan_file_size_limit(self, temp_mods_dir: Path) -> None:
        """Test scanner respects file size limit."""
        # Create oversized mod
        large_mod = temp_mods_dir / "large.package"
        large_mod.write_bytes(b"x" * (501 * 1024 * 1024))  # 501MB

        scanner = ModScanner(max_size_mb=500)
        result = scanner.scan_directory(temp_mods_dir)

        assert len(result["package"]) == 0  # Should be skipped

    def test_validate_mod(self, sample_package_mod: Path) -> None:
        """Test mod validation."""
        mod = ModFile(sample_package_mod)
        scanner = ModScanner()

        assert scanner.validate_mod(mod) is True

    def test_validate_mod_missing_file(self, tmp_path: Path) -> None:
        """Test validation fails for missing file."""
        mod_path = tmp_path / "deleted.package"
        mod_path.write_bytes(b"test")
        mod = ModFile(mod_path)

        # Delete file after creation
        mod_path.unlink()

        scanner = ModScanner()
        assert scanner.validate_mod(mod) is False
