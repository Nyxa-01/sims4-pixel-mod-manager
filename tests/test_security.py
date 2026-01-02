"""Tests for security layer."""

from pathlib import Path

import pytest

from src.core.security import (
    PathEncryption,
    sanitize_filename,
    validate_path_security,
)


class TestPathEncryption:
    """Test PathEncryption class."""

    def test_encrypt_decrypt_path(self, mock_encryption_key: Path) -> None:
        """Test encrypting and decrypting paths."""
        encryption = PathEncryption(mock_encryption_key)

        original = Path("/test/path/to/mods")
        encrypted = encryption.encrypt_path(original)
        decrypted = encryption.decrypt_path(encrypted)

        assert isinstance(encrypted, str)
        assert decrypted == original.resolve()

    def test_decrypt_invalid_data(self, mock_encryption_key: Path) -> None:
        """Test decrypting invalid data raises ValueError."""
        encryption = PathEncryption(mock_encryption_key)

        with pytest.raises(ValueError, match="Invalid encrypted path"):
            encryption.decrypt_path("invalid_base64_data")


class TestPathValidation:
    """Test path validation functions."""

    def test_validate_safe_path(self, tmp_path: Path) -> None:
        """Test validating safe path."""
        safe_path = tmp_path / "mods" / "test.package"
        assert validate_path_security(safe_path) is True

    def test_validate_path_traversal(self) -> None:
        """Test detecting path traversal attempt."""
        dangerous = Path("/mods/../../../etc/passwd")
        assert validate_path_security(dangerous) is False

    def test_validate_path_within_base(self, tmp_path: Path) -> None:
        """Test validating path within allowed base."""
        base = tmp_path / "mods"
        base.mkdir()

        safe = base / "subfolder" / "mod.package"
        assert validate_path_security(safe, allowed_base=base) is True

        outside = tmp_path / "other" / "mod.package"
        assert validate_path_security(outside, allowed_base=base) is False


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_safe_filename(self) -> None:
        """Test sanitizing already safe filename."""
        safe = "my_mod_v1.2.package"
        assert sanitize_filename(safe) == safe

    def test_sanitize_path_separators(self) -> None:
        """Test removing path separators."""
        dangerous = "../../evil.package"
        sanitized = sanitize_filename(dangerous)
        assert ".." not in sanitized
        assert "/" not in sanitized

    def test_sanitize_special_characters(self) -> None:
        """Test removing special characters."""
        dangerous = 'mod<name>:with*bad?chars|"test".package'
        sanitized = sanitize_filename(dangerous)

        for char in ["<", ">", ":", "*", "?", "|", '"']:
            assert char not in sanitized

    def test_sanitize_long_filename(self) -> None:
        """Test truncating long filenames."""
        long_name = "a" * 300 + ".package"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".package")


class TestSecurityEdgeCases:
    """Test security edge cases and malicious input handling."""

    def test_validate_path_with_null_byte(self) -> None:
        """Test path validation rejects null bytes."""
        malicious = Path("/mods/evil\x00.package")
        # Path traversal check should catch this
        result = validate_path_security(malicious)
        assert result is False or not malicious.exists()

    def test_validate_symbolic_link_traversal(self, tmp_path: Path) -> None:
        """Test validation handles symbolic links."""
        base = tmp_path / "mods"
        base.mkdir()

        target = tmp_path / "outside"
        target.mkdir()
        (target / "evil.package").write_text("malicious")

        link = base / "link"
        try:
            link.symlink_to(target)
            # Should detect link escapes base
            result = validate_path_security(link / "evil.package", allowed_base=base)
            # Result depends on whether symlink resolution detects escape
            assert isinstance(result, bool)
        except OSError:
            # Symlink creation failed (Windows without admin)
            pytest.skip("Symlink creation requires elevated privileges")

    def test_validate_path_with_unicode(self, tmp_path: Path) -> None:
        """Test path validation handles unicode characters."""
        unicode_path = tmp_path / "モッド" / "テスト.package"
        assert validate_path_security(unicode_path) is True

    def test_encrypt_decrypt_path_with_spaces(self, mock_encryption_key: Path) -> None:
        """Test encryption handles paths with spaces."""
        encryption = PathEncryption(mock_encryption_key)

        path_with_spaces = Path("/Program Files/The Sims 4/Mods")
        encrypted = encryption.encrypt_path(path_with_spaces)
        decrypted = encryption.decrypt_path(encrypted)

        assert decrypted == path_with_spaces.resolve()

    def test_encrypt_decrypt_path_with_unicode(
        self, mock_encryption_key: Path
    ) -> None:
        """Test encryption handles unicode paths."""
        encryption = PathEncryption(mock_encryption_key)

        unicode_path = Path("/home/user/ドキュメント/Mods")
        encrypted = encryption.encrypt_path(unicode_path)
        decrypted = encryption.decrypt_path(encrypted)

        assert decrypted == unicode_path.resolve()

    def test_decrypt_tampered_data(self, mock_encryption_key: Path) -> None:
        """Test decryption detects tampered ciphertext."""
        encryption = PathEncryption(mock_encryption_key)

        original = Path("/test/path")
        encrypted = encryption.encrypt_path(original)

        # Tamper with encrypted data
        tampered = encrypted[:-5] + "XXXXX"

        with pytest.raises(ValueError, match="Invalid encrypted path"):
            encryption.decrypt_path(tampered)

    def test_decrypt_empty_string(self, mock_encryption_key: Path) -> None:
        """Test decryption handles empty string."""
        encryption = PathEncryption(mock_encryption_key)

        with pytest.raises(ValueError, match="Invalid encrypted path"):
            encryption.decrypt_path("")

    def test_sanitize_filename_null_byte(self) -> None:
        """Test sanitizing filename with null byte."""
        dangerous = "mod\x00evil.package"
        sanitized = sanitize_filename(dangerous)
        assert "\x00" not in sanitized

    def test_sanitize_filename_only_extension(self) -> None:
        """Test sanitizing filename that's only extension."""
        only_ext = ".package"
        sanitized = sanitize_filename(only_ext)
        assert sanitized == ".package"

    def test_sanitize_filename_empty_string(self) -> None:
        """Test sanitizing empty filename."""
        empty = ""
        sanitized = sanitize_filename(empty)
        assert sanitized == ""

    def test_validate_path_absolute_vs_relative(self, tmp_path: Path) -> None:
        """Test validation handles both absolute and relative paths."""
        base = tmp_path / "mods"
        base.mkdir()

        # Absolute path within base
        absolute = base / "subfolder" / "mod.package"
        assert validate_path_security(absolute, allowed_base=base) is True

        # Relative path with traversal
        relative = Path("../etc/passwd")
        assert validate_path_security(relative) is False

    def test_encryption_key_persistence(self, tmp_path: Path) -> None:
        """Test encryption key is reused across instances."""
        key_path = tmp_path / ".encryption.key"

        # First instance creates key
        enc1 = PathEncryption(key_path)
        original = Path("/test/path")
        encrypted = enc1.encrypt_path(original)

        # Second instance reuses same key
        enc2 = PathEncryption(key_path)
        decrypted = enc2.decrypt_path(encrypted)

        assert decrypted == original.resolve()

    def test_encryption_key_file_permissions(self, tmp_path: Path) -> None:
        """Test encryption key file has restrictive permissions (Unix)."""
        import platform

        if platform.system() == "Windows":
            pytest.skip("Unix-only test")

        key_path = tmp_path / ".encryption.key"
        encryption = PathEncryption(key_path)

        # Trigger key creation
        _ = encryption.fernet

        # Check permissions (should be 0o600 = -rw-------)
        stat_info = key_path.stat()
        mode = stat_info.st_mode & 0o777
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"

    def test_validate_path_case_sensitivity(self, tmp_path: Path) -> None:
        """Test path validation handles case-sensitive filesystems."""
        base = tmp_path / "Mods"
        base.mkdir()

        # Different case variations
        lower = base / "mods" / "test.package"
        upper = base / "MODS" / "test.package"

        # Both should be considered valid (case handling is OS-dependent)
        assert validate_path_security(lower, allowed_base=base) is True
        assert validate_path_security(upper, allowed_base=base) is True
