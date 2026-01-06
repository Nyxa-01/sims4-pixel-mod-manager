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
