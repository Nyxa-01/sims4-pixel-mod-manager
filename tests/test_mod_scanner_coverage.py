"""Extended coverage tests for ModScanner targeting uncovered lines."""

import zipfile
import math
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import threading
import time

import pytest

from src.core.exceptions import ModScanError, SecurityError
from src.core.mod_scanner import (
    ModFile,
    ModScanner,
    SUPPORTED_EXTENSIONS,
    MAGIC_BYTES,
    CORE_MOD_KEYWORDS,
)


class TestModScannerCoverageExtended:
    """Additional tests targeting uncovered lines in ModScanner."""

    @pytest.fixture
    def scanner(self):
        """Create ModScanner instance."""
        return ModScanner(max_file_size_mb=500, scan_timeout_seconds=5)

    def test_scan_file_too_large(self, scanner, tmp_path):
        """Test scanning file that exceeds size limit."""
        # Create scanner with very small size limit
        small_scanner = ModScanner(max_file_size_mb=0)  # 0 MB limit
        
        package = tmp_path / "large_mod.package"
        package.write_bytes(b"DBPF" + b"\x00" * 1000)

        mod = small_scanner._scan_file(package)

        assert not mod.is_valid
        assert any("too large" in err.lower() for err in mod.validation_errors)

    def test_scan_file_permission_error(self, scanner, tmp_path):
        """Test scanning file with permission error."""
        package = tmp_path / "protected.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch("pathlib.Path.stat", side_effect=PermissionError("Access denied")):
            with pytest.raises(ModScanError, match="Cannot access"):
                scanner._scan_file(package)

    def test_calculate_hash_success(self, scanner, tmp_path):
        """Test CRC32 hash calculation."""
        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"test content")

        hash_value = scanner._calculate_hash(test_file)

        assert len(hash_value) == 8  # CRC32 hex string
        assert hash_value.isalnum()

    def test_calculate_hash_error(self, scanner, tmp_path):
        """Test hash calculation failure handling."""
        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"content")

        with patch("builtins.open", side_effect=IOError("Read error")):
            hash_value = scanner._calculate_hash(test_file)

        assert hash_value == "00000000"

    def test_calculate_entropy_empty_file(self, scanner, tmp_path):
        """Test entropy calculation on empty file."""
        empty_file = tmp_path / "empty.package"
        empty_file.write_bytes(b"")

        entropy = scanner.calculate_entropy(empty_file)

        assert entropy == 0.0

    def test_calculate_entropy_uniform_content(self, scanner, tmp_path):
        """Test entropy calculation on uniform content (low entropy)."""
        uniform_file = tmp_path / "uniform.package"
        uniform_file.write_bytes(b"\x00" * 1000)

        entropy = scanner.calculate_entropy(uniform_file)

        assert entropy == 0.0  # All same bytes = 0 entropy

    def test_calculate_entropy_random_content(self, scanner, tmp_path):
        """Test entropy calculation on random-like content (high entropy)."""
        import os
        random_file = tmp_path / "random.package"
        random_file.write_bytes(os.urandom(8192))

        # Random data will have high entropy and raise SecurityError
        with pytest.raises(SecurityError, match="entropy"):
            scanner.calculate_entropy(random_file)

    def test_calculate_entropy_exceeds_threshold(self, scanner, tmp_path):
        """Test entropy exceeding threshold raises SecurityError."""
        import os
        suspicious_file = tmp_path / "suspicious.package"
        suspicious_file.write_bytes(os.urandom(8192))

        with pytest.raises(SecurityError, match="entropy too high"):
            scanner.calculate_entropy(suspicious_file)

    def test_calculate_entropy_io_error(self, scanner, tmp_path):
        """Test entropy calculation handles IO errors."""
        test_file = tmp_path / "test.package"
        test_file.write_bytes(b"DBPF" + b"content")

        with patch("builtins.open", side_effect=IOError("Read error")):
            entropy = scanner.calculate_entropy(test_file)

        assert entropy == 0.0

    def test_verify_signature_package_valid(self, scanner, tmp_path):
        """Test valid .package file signature."""
        package = tmp_path / "valid.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        result, error = scanner.verify_signature(package)

        assert result is True
        assert error is None

    def test_verify_signature_package_invalid(self, scanner, tmp_path):
        """Test invalid .package file signature."""
        package = tmp_path / "invalid.package"
        package.write_bytes(b"FAKE" + b"\x00" * 100)

        with pytest.raises(SecurityError):
            scanner.verify_signature(package)

    def test_verify_signature_ts4script_valid(self, scanner, tmp_path):
        """Test valid .ts4script file signature (ZIP)."""
        ts4script = tmp_path / "valid.ts4script"
        with zipfile.ZipFile(ts4script, "w") as zf:
            zf.writestr("script.py", "print('hello')")

        result, error = scanner.verify_signature(ts4script)

        assert result is True

    def test_verify_signature_ts4script_invalid(self, scanner, tmp_path):
        """Test invalid .ts4script file signature."""
        ts4script = tmp_path / "invalid.ts4script"
        ts4script.write_bytes(b"NOT_ZIP" + b"\x00" * 100)

        with pytest.raises(SecurityError):
            scanner.verify_signature(ts4script)

    def test_verify_signature_python_valid(self, scanner, tmp_path):
        """Test valid Python file syntax."""
        py_file = tmp_path / "valid.py"
        py_file.write_text("def hello():\n    print('world')")

        result, error = scanner.verify_signature(py_file)

        assert result is True

    def test_verify_signature_python_syntax_error(self, scanner, tmp_path):
        """Test Python file with syntax error."""
        py_file = tmp_path / "invalid.py"
        py_file.write_text("def hello(\n    print('broken'")

        with pytest.raises(SecurityError, match="Invalid Python syntax"):
            scanner.verify_signature(py_file)

    def test_verify_signature_python_unicode_error(self, scanner, tmp_path):
        """Test Python file with invalid encoding."""
        py_file = tmp_path / "bad_encoding.py"
        py_file.write_bytes(b"\xff\xfe" + b"\x80\x81\x82")  # Invalid UTF-8

        with pytest.raises(SecurityError, match="not valid UTF-8"):
            scanner.verify_signature(py_file)

    def test_verify_signature_unsupported_extension(self, scanner, tmp_path):
        """Test file with unsupported extension (no signature check)."""
        cfg_file = tmp_path / "config.cfg"
        cfg_file.write_text("[settings]\nvalue=1")

        result, error = scanner.verify_signature(cfg_file)

        assert result is True  # Unsupported extensions pass

    def test_scan_file_with_timeout_success(self, scanner, tmp_path):
        """Test scan with timeout completing successfully."""
        package = tmp_path / "test.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file_with_timeout(package)

        assert mod.is_valid

    def test_scan_file_with_timeout_exception(self, scanner, tmp_path):
        """Test scan with timeout when exception occurs."""
        package = tmp_path / "error.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch.object(scanner, "_scan_file", side_effect=ValueError("Test error")):
            with pytest.raises(ValueError, match="Test error"):
                scanner._scan_file_with_timeout(package)

    def test_scan_folder_skips_non_supported_extensions(self, scanner, tmp_path):
        """Test that non-supported file extensions are skipped."""
        incoming = tmp_path / "incoming"
        incoming.mkdir()

        # Create non-supported file
        txt_file = incoming / "readme.txt"
        txt_file.write_text("Not a mod")

        # Create supported file
        package = incoming / "mod.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        results = scanner.scan_folder(incoming)

        # Only the package should be scanned
        total_mods = sum(len(mods) for mods in results.values())
        assert total_mods == 1

    def test_scan_folder_handles_scan_error(self, scanner, tmp_path):
        """Test folder scan handles individual file errors gracefully."""
        incoming = tmp_path / "incoming"
        incoming.mkdir()

        package = incoming / "error.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        with patch.object(scanner, "_scan_file_with_timeout", side_effect=Exception("Scan failed")):
            results = scanner.scan_folder(incoming)

        # Error file should be in Invalid category
        assert len(results["Invalid"]) == 1
        assert "Scan failed" in results["Invalid"][0].validation_errors[0]


class TestModScannerCategorization:
    """Tests for mod categorization logic."""

    @pytest.fixture
    def scanner(self):
        """Create ModScanner instance."""
        return ModScanner()

    def test_categorize_core_mod(self, scanner, tmp_path):
        """Test categorization of core script mod."""
        # MCCC-like mod
        package = tmp_path / "mc_command_center.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file(package)

        assert mod.category in ["Core Scripts", "Main Mods", "Libraries"]

    def test_categorize_ts4script(self, scanner, tmp_path):
        """Test categorization of .ts4script files."""
        ts4script = tmp_path / "mod.ts4script"
        with zipfile.ZipFile(ts4script, "w") as zf:
            zf.writestr("script.py", "print('hello')")

        mod = scanner._scan_file(ts4script)

        assert mod.mod_type == "ts4script"

    def test_categorize_python_file(self, scanner, tmp_path):
        """Test categorization of Python files."""
        py_file = tmp_path / "helper.py"
        py_file.write_text("def helper(): pass")

        mod = scanner._scan_file(py_file)

        assert mod.mod_type == "script"

    def test_categorize_regular_package(self, scanner, tmp_path):
        """Test categorization of regular package mod."""
        package = tmp_path / "my_custom_mod.package"
        package.write_bytes(b"DBPF" + b"\x00" * 100)

        mod = scanner._scan_file(package)

        assert mod.mod_type == "package"


class TestModFileDataclass:
    """Additional tests for ModFile dataclass."""

    def test_mod_file_with_validation_errors(self):
        """Test ModFile with validation errors."""
        mod = ModFile(
            path=Path("broken.package"),
            size=999999999,
            hash="00000000",
            mod_type="package",
            category="Invalid",
            is_valid=False,
            validation_errors=["File too large", "Invalid signature"],
            entropy=8.0,
        )

        assert len(mod.validation_errors) == 2
        assert mod.entropy == 8.0
        assert "✗" in repr(mod)

    def test_mod_file_repr_valid(self):
        """Test valid ModFile string representation."""
        mod = ModFile(
            path=Path("good.package"),
            size=1024,
            hash="12345678",
            mod_type="package",
            category="Main Mods",
            is_valid=True,
        )

        assert "✓" in repr(mod)
        assert "good.package" in repr(mod)

    def test_mod_file_default_values(self):
        """Test ModFile default values."""
        mod = ModFile(
            path=Path("test.package"),
            size=100,
            hash="ABCD",
            mod_type="package",
            category="Main Mods",
            is_valid=True,
        )

        assert mod.validation_errors == []
        assert mod.entropy == 0.0


class TestScannerThreadSafety:
    """Tests for thread safety in scanner."""

    @pytest.fixture
    def scanner(self):
        """Create ModScanner instance."""
        return ModScanner()

    def test_concurrent_hash_calculations(self, scanner, tmp_path):
        """Test concurrent hash calculations are thread-safe."""
        # Create multiple files
        files = []
        for i in range(5):
            f = tmp_path / f"mod_{i}.package"
            f.write_bytes(b"DBPF" + bytes([i]) * 100)
            files.append(f)

        results = []
        errors = []

        def calc_hash(path):
            try:
                h = scanner._calculate_hash(path)
                results.append((path.name, h))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=calc_hash, args=(f,)) for f in files]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
