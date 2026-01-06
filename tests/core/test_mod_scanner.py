"""Tests for secure mod scanner."""

import zipfile
from pathlib import Path

import pytest

from src.core.exceptions import SecurityError
from src.core.mod_scanner import ModFile, ModScanner


@pytest.fixture
def scanner() -> ModScanner:
    """Create ModScanner instance for testing.

    Returns:
        ModScanner with default settings
    """
    return ModScanner(max_file_size_mb=500, scan_timeout_seconds=5)


@pytest.fixture
def sample_package_file(tmp_path: Path) -> Path:
    """Create sample .package file with DBPF header.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample package file
    """
    package = tmp_path / "test_mod.package"
    # DBPF header + some content
    package.write_bytes(b"DBPF" + b"\x00" * 100)
    return package


@pytest.fixture
def sample_script_file(tmp_path: Path) -> Path:
    """Create sample .py script file.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample script file
    """
    script = tmp_path / "test_script.py"
    script.write_text("# Test script\nprint('Hello, World!')")
    return script


@pytest.fixture
def sample_ts4script_file(tmp_path: Path) -> Path:
    """Create sample .ts4script file (ZIP with Python).

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample ts4script file
    """
    ts4script = tmp_path / "test_mod.ts4script"

    # Create valid ZIP with Python file
    with zipfile.ZipFile(ts4script, "w") as zf:
        zf.writestr("mod_script.py", "# Script mod\nprint('Loaded')")

    return ts4script


@pytest.fixture
def incoming_folder(
    tmp_path: Path,
    sample_package_file: Path,
    sample_script_file: Path,
    sample_ts4script_file: Path,
) -> Path:
    """Create incoming folder with sample mods.

    Args:
        tmp_path: Pytest tmp_path fixture
        sample_package_file: Sample package fixture
        sample_script_file: Sample script fixture
        sample_ts4script_file: Sample ts4script fixture

    Returns:
        Path to incoming folder
    """
    incoming = tmp_path / "incoming"
    incoming.mkdir()

    # Copy sample files
    import shutil

    shutil.copy(sample_package_file, incoming)
    shutil.copy(sample_script_file, incoming)
    shutil.copy(sample_ts4script_file, incoming)

    return incoming


class TestModFile:
    """Test ModFile dataclass."""

    def test_mod_file_creation(self) -> None:
        """Test ModFile initialization."""
        mod = ModFile(
            path=Path("test.package"),
            size=1024,
            hash="ABCD1234",
            mod_type="package",
            category="Main Mods",
            is_valid=True,
        )

        assert mod.path == Path("test.package")
        assert mod.size == 1024
        assert mod.hash == "ABCD1234"
        assert mod.mod_type == "package"
        assert mod.category == "Main Mods"
        assert mod.is_valid is True
        assert len(mod.validation_errors) == 0

    def test_mod_file_repr(self) -> None:
        """Test ModFile string representation."""
        mod = ModFile(
            path=Path("test.package"),
            size=1024,
            hash="ABCD1234",
            mod_type="package",
            category="Main Mods",
            is_valid=True,
        )

        repr_str = repr(mod)
        assert "test.package" in repr_str
        assert "package" in repr_str


class TestModScanner:
    """Test ModScanner class."""

    def test_scanner_initialization(self) -> None:
        """Test scanner initialization with custom settings."""
        scanner = ModScanner(
            max_file_size_mb=100,
            scan_timeout_seconds=10,
            min_entropy_threshold=7.0,
        )

        assert scanner.max_file_size_bytes == 100 * 1024 * 1024
        assert scanner.scan_timeout == 10
        assert scanner.min_entropy_threshold == 7.0

    def test_scan_folder_not_found(self, scanner: ModScanner) -> None:
        """Test scanning non-existent folder raises error."""
        with pytest.raises(FileNotFoundError):
            scanner.scan_folder(Path("/nonexistent"))

    def test_scan_folder_not_directory(
        self,
        scanner: ModScanner,
        sample_package_file: Path,
    ) -> None:
        """Test scanning a file (not directory) raises error."""
        with pytest.raises(NotADirectoryError):
            scanner.scan_folder(sample_package_file)

    def test_scan_folder_success(
        self,
        scanner: ModScanner,
        incoming_folder: Path,
    ) -> None:
        """Test successful folder scan."""
        results = scanner.scan_folder(incoming_folder)

        # Check categories exist
        assert "Core Scripts" in results
        assert "Main Mods" in results
        assert "Invalid" in results

        # Check files were scanned
        total_valid = sum(len(mods) for category, mods in results.items() if category != "Invalid")
        assert total_valid > 0

    def test_scan_package_file(
        self,
        scanner: ModScanner,
        sample_package_file: Path,
    ) -> None:
        """Test scanning .package file."""
        mod = scanner._scan_file(sample_package_file)

        assert mod.path == sample_package_file
        assert mod.mod_type == "package"
        assert mod.is_valid is True
        assert mod.size > 0
        assert len(mod.hash) == 8  # CRC32 hex string

    def test_scan_script_file(
        self,
        scanner: ModScanner,
        sample_script_file: Path,
    ) -> None:
        """Test scanning .py script file."""
        mod = scanner._scan_file(sample_script_file)

        assert mod.path == sample_script_file
        assert mod.mod_type == "script"
        assert mod.is_valid is True
        assert mod.category in ["Core Scripts", "Libraries"]

    def test_scan_ts4script_file(
        self,
        scanner: ModScanner,
        sample_ts4script_file: Path,
    ) -> None:
        """Test scanning .ts4script file."""
        mod = scanner._scan_file(sample_ts4script_file)

        assert mod.path == sample_ts4script_file
        assert mod.mod_type == "ts4script"
        assert mod.is_valid is True
        assert mod.category == "Core Scripts"

    def test_file_size_validation(self, scanner: ModScanner, tmp_path: Path) -> None:
        """Test file size limit validation."""
        # Create oversized file
        large_file = tmp_path / "large.package"
        large_file.write_bytes(b"DBPF" + b"x" * (501 * 1024 * 1024))

        mod = scanner._scan_file(large_file)

        assert mod.is_valid is False
        assert any("too large" in err.lower() for err in mod.validation_errors)

    def test_invalid_signature(self, scanner: ModScanner, tmp_path: Path) -> None:
        """Test invalid file signature detection (enforced as SecurityError)."""
        # Create .package without DBPF header
        invalid_pkg = tmp_path / "invalid.package"
        invalid_pkg.write_bytes(b"INVALID_HEADER" + b"\x00" * 100)

        # Security enforcement: should raise SecurityError, not mark as invalid
        with pytest.raises(SecurityError, match="Invalid .package signature"):
            scanner._scan_file(invalid_pkg)

    def test_invalid_python_syntax(self, scanner: ModScanner, tmp_path: Path) -> None:
        """Test Python syntax validation (enforced as SecurityError)."""
        invalid_py = tmp_path / "invalid.py"
        invalid_py.write_text("def broken syntax here\nprint('invalid')")

        # Security enforcement: should raise SecurityError for syntax errors
        with pytest.raises(SecurityError, match="Invalid Python syntax"):
            scanner._scan_file(invalid_py)

    def test_invalid_ts4script_not_zip(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test .ts4script must be valid ZIP (enforced as SecurityError)."""
        invalid_ts4 = tmp_path / "invalid.ts4script"
        invalid_ts4.write_bytes(b"Not a ZIP file")

        # Security enforcement: should raise SecurityError for invalid ZIP
        with pytest.raises(SecurityError, match="Invalid .ts4script signature"):
            scanner._scan_file(invalid_ts4)

    def test_entropy_calculation(
        self,
        scanner: ModScanner,
        sample_package_file: Path,
    ) -> None:
        """Test entropy calculation."""
        entropy = scanner.calculate_entropy(sample_package_file)

        assert 0.0 <= entropy <= 8.0
        assert entropy > 0.0  # File has some data

    def test_high_entropy_detection(self, scanner: ModScanner, tmp_path: Path) -> None:
        """Test high entropy (potential malware) detection (enforced as SecurityError)."""
        # Create file with high entropy (random data)
        import os

        high_entropy = tmp_path / "suspicious.package"
        high_entropy.write_bytes(b"DBPF" + os.urandom(8192))

        # Security enforcement: entropy >7.5 should raise SecurityError
        with pytest.raises(SecurityError, match="entropy too high"):
            scanner._scan_file(high_entropy)

    def test_hash_calculation(
        self,
        scanner: ModScanner,
        sample_package_file: Path,
    ) -> None:
        """Test CRC32 hash calculation."""
        hash1 = scanner._calculate_hash(sample_package_file)
        hash2 = scanner._calculate_hash(sample_package_file)

        assert hash1 == hash2  # Consistent
        assert len(hash1) == 8  # Hex format
        assert hash1.upper() == hash1  # Uppercase

    def test_categorization_core_scripts(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of core script mods."""
        mccc = tmp_path / "mc_command_center.ts4script"
        with zipfile.ZipFile(mccc, "w") as zf:
            zf.writestr("script.py", "# MCCC")

        mod = scanner._scan_file(mccc)
        assert mod.category == "Core Scripts"

    def test_categorization_cc_large_file(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of large CC files."""
        large_cc = tmp_path / "big_mesh.package"
        large_cc.write_bytes(b"DBPF" + b"x" * (15 * 1024 * 1024))

        mod = scanner._scan_file(large_cc)
        assert mod.category == "CC"

    def test_categorization_cc_cas(self, scanner: ModScanner, tmp_path: Path) -> None:
        """Test categorization of CAS items."""
        cas_folder = tmp_path / "CAS"
        cas_folder.mkdir()
        cas_item = cas_folder / "hair.package"
        cas_item.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file(cas_item)
        assert mod.category == "CC"

    def test_validate_file_method(
        self,
        scanner: ModScanner,
        sample_package_file: Path,
    ) -> None:
        """Test validate_file convenience method."""
        is_valid, errors = scanner.validate_file(sample_package_file)

        assert is_valid is True
        assert len(errors) == 0

    def test_scan_timeout_protection(self, tmp_path: Path) -> None:
        """Test timeout protection for slow scans."""
        # Create scanner with very short timeout
        scanner = ModScanner(scan_timeout_seconds=1)

        # This test is tricky - we'd need to mock a slow operation
        # For now, just verify normal files don't timeout
        fast_file = tmp_path / "fast.package"
        fast_file.write_bytes(b"DBPF" + b"\x00" * 1024)

        mod = scanner._scan_file_with_timeout(fast_file)
        assert mod.is_valid is True

    def test_thread_safety(
        self,
        scanner: ModScanner,
        incoming_folder: Path,
    ) -> None:
        """Test thread-safe operations."""
        import threading

        results = []
        lock = threading.Lock()

        def scan_worker() -> None:
            result = scanner.scan_folder(incoming_folder)
            with lock:
                results.append(result)

        threads = [threading.Thread(target=scan_worker) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should complete successfully
        assert len(results) == 3

    def test_scan_folder_skips_non_files(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test that scan skips directories."""
        incoming = tmp_path / "incoming"
        incoming.mkdir()

        # Create a subdirectory (not a file)
        subdir = incoming / "subdir"
        subdir.mkdir()

        # Create a valid file
        valid = incoming / "test.package"
        valid.write_bytes(b"DBPF" + b"\x00" * 100)

        results = scanner.scan_folder(incoming)

        # Should have scanned the file, not the directory
        all_mods = []
        for mods in results.values():
            all_mods.extend(mods)
        assert len(all_mods) == 1

    def test_scan_folder_skips_unsupported_extensions(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test that scan skips unsupported file types."""
        incoming = tmp_path / "incoming"
        incoming.mkdir()

        # Create unsupported file types
        (incoming / "readme.txt").write_text("readme")
        (incoming / "image.png").write_bytes(b"\x89PNG")
        (incoming / "valid.package").write_bytes(b"DBPF" + b"\x00" * 100)

        results = scanner.scan_folder(incoming)

        # Only the .package file should be scanned
        all_mods = []
        for mods in results.values():
            all_mods.extend(mods)
        assert len(all_mods) == 1
        assert all_mods[0].path.suffix == ".package"

    def test_scan_folder_handles_invalid_mod(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test that invalid mods are placed in Invalid category."""
        incoming = tmp_path / "incoming"
        incoming.mkdir()

        # Create oversized file (will be invalid)
        oversized = incoming / "oversized.package"
        oversized.write_bytes(b"DBPF" + b"x" * (501 * 1024 * 1024))

        results = scanner.scan_folder(incoming)

        # File should be in Invalid category due to size
        assert len(results["Invalid"]) == 1
        assert "too large" in results["Invalid"][0].validation_errors[0].lower()

    def test_scan_folder_handles_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test that exceptions during scan are handled gracefully."""
        from unittest.mock import patch

        incoming = tmp_path / "incoming"
        incoming.mkdir()
        (incoming / "test.package").write_bytes(b"DBPF" + b"\x00" * 100)

        with patch.object(
            scanner, "_scan_file_with_timeout", side_effect=RuntimeError("Test error")
        ):
            results = scanner.scan_folder(incoming)

        # Error should result in invalid entry
        assert len(results["Invalid"]) == 1
        assert "Test error" in results["Invalid"][0].validation_errors[0]

    def test_scan_file_stat_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test scan handles file stat exception."""
        from unittest.mock import patch

        from src.core.exceptions import ModScanError

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch.object(Path, "stat", side_effect=PermissionError("Access denied")):
            with pytest.raises(ModScanError, match="Cannot access file"):
                scanner._scan_file(test_file)

    def test_calculate_hash_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test hash calculation returns zeros on exception."""
        from unittest.mock import patch

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch("builtins.open", side_effect=OSError("Read error")):
            hash_result = scanner._calculate_hash(test_file)

        assert hash_result == "00000000"

    def test_calculate_entropy_empty_file(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test entropy calculation for empty file."""
        empty_file = tmp_path / "empty.bin"
        empty_file.write_bytes(b"")

        entropy = scanner.calculate_entropy(empty_file)

        assert entropy == 0.0

    def test_calculate_entropy_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test entropy calculation handles exception gracefully."""
        from unittest.mock import patch

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch("builtins.open", side_effect=OSError("Read error")):
            entropy = scanner.calculate_entropy(test_file)

        assert entropy == 0.0

    def test_verify_signature_python_unicode_error(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test Python verification raises SecurityError on UnicodeDecodeError."""
        invalid_encoding = tmp_path / "bad_encoding.py"
        # Write bytes that aren't valid UTF-8
        invalid_encoding.write_bytes(b"\xff\xfe Invalid UTF-8")

        with pytest.raises(SecurityError, match="not valid UTF-8"):
            scanner.verify_signature(invalid_encoding)

    def test_verify_signature_python_generic_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test Python verification raises SecurityError on generic exception."""
        from unittest.mock import patch

        test_py = tmp_path / "test.py"
        test_py.write_text("print('hello')")

        with patch("ast.parse", side_effect=RuntimeError("Parser error")):
            with pytest.raises(SecurityError, match="Python validation failed"):
                scanner.verify_signature(test_py)

    def test_verify_signature_cfg_file(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test cfg files pass signature verification (no magic bytes check)."""
        cfg_file = tmp_path / "resource.cfg"
        cfg_file.write_text("Priority 1000")

        result = scanner.verify_signature(cfg_file)

        assert result == (True, None)

    def test_verify_signature_ts4script_no_python(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test ts4script without Python files raises SecurityError."""
        ts4script = tmp_path / "no_python.ts4script"

        # Create ZIP without any .py files
        with zipfile.ZipFile(ts4script, "w") as zf:
            zf.writestr("readme.txt", "No Python here")
            zf.writestr("data.bin", b"\x00" * 100)

        with pytest.raises(SecurityError, match="must contain Python files"):
            scanner.verify_signature(ts4script)

    def test_verify_signature_permission_error(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test signature verification raises SecurityError on permission denied."""
        from unittest.mock import patch

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(SecurityError, match="Permission denied"):
                scanner.verify_signature(test_file)

    def test_verify_signature_generic_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test signature verification raises SecurityError on generic exception."""
        from unittest.mock import patch

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch("builtins.open", side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(SecurityError, match="Signature verification failed"):
                scanner.verify_signature(test_file)

    def test_categorization_library_util(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of library/utility scripts."""
        # Use a Python file to test lib/util categorization
        # (ts4script always contains "script" keyword which overrides)
        util_py = tmp_path / "my_lib_helpers.py"
        util_py.write_text("# Utility library")

        mod = scanner._scan_file(util_py)
        assert mod.category == "Libraries"

    def test_categorization_build_buy(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of build/buy items."""
        build_folder = tmp_path / "Build_Mode"
        build_folder.mkdir()
        build_item = build_folder / "furniture_set.package"
        build_item.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file(build_item)
        assert mod.category == "CC"

    def test_categorization_core_keyword_package(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of package files with core keywords."""
        mccc_pkg = tmp_path / "mccc_tuner.package"
        mccc_pkg.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file(mccc_pkg)
        assert mod.category == "Core Scripts"

    def test_categorization_config_file(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test categorization of config files."""
        cfg_file = tmp_path / "settings.cfg"
        cfg_file.write_text("Config content")

        mod = scanner._scan_file(cfg_file)
        assert mod.category == "Libraries"

    def test_validate_file_exception(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test validate_file returns error on exception."""
        from unittest.mock import patch

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch.object(scanner, "_scan_file", side_effect=RuntimeError("Error")):
            is_valid, errors = scanner.validate_file(test_file)

        assert is_valid is False
        assert "Error" in errors[0]

    def test_scan_file_with_timeout_returns_none(
        self,
        scanner: ModScanner,
        tmp_path: Path,
    ) -> None:
        """Test scan returns error when worker returns None."""
        from unittest.mock import patch

        from src.core.exceptions import ModScanError

        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"\x00" * 100)

        # Make the scan worker return None instead of a result
        with patch.object(scanner, "_scan_file", return_value=None):
            with pytest.raises(ModScanError, match="Scan returned no result"):
                scanner._scan_file_with_timeout(test_file)
