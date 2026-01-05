"""Tests for security module coverage."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.security import (
    PathEncryption,
    sanitize_filename,
    validate_path_security,
)


class TestPathEncryption:
    """Test PathEncryption class."""

    def test_init_with_custom_key_path(self, tmp_path: Path) -> None:
        """Test initialization with custom key path."""
        key_path = tmp_path / ".custom.key"
        enc = PathEncryption(key_path=key_path)

        assert enc.key_path == key_path

    def test_init_with_default_key_path(self) -> None:
        """Test initialization with default key path."""
        enc = PathEncryption()

        assert enc.key_path is not None
        assert ".encryption.key" in str(enc.key_path)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only test")
    @patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"})
    def test_default_key_path_windows(self) -> None:
        """Test default key path on Windows."""
        enc = PathEncryption()
        key_path = enc._get_default_key_path()

        assert "Sims4ModManager" in str(key_path)

    @patch("os.name", "posix")
    @patch("platform.system", return_value="Darwin")
    def test_default_key_path_macos(self, mock_system: Mock) -> None:
        """Test default key path on macOS."""
        enc = PathEncryption()
        key_path = enc._get_default_key_path()

        assert "Sims4ModManager" in str(key_path)

    @patch("os.name", "posix")
    @patch("platform.system", return_value="Linux")
    def test_default_key_path_linux(self, mock_system: Mock) -> None:
        """Test default key path on Linux."""
        enc = PathEncryption()
        key_path = enc._get_default_key_path()

        assert "Sims4ModManager" in str(key_path)

    def test_encrypt_decrypt_roundtrip(self, tmp_path: Path) -> None:
        """Test encryption and decryption roundtrip."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)

        original_path = Path("/home/user/mods/test.package")
        encrypted = enc.encrypt_path(original_path)
        decrypted = enc.decrypt_path(encrypted)

        assert decrypted == original_path.resolve()

    def test_encrypt_path_returns_string(self, tmp_path: Path) -> None:
        """Test encrypt_path returns string."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)

        encrypted = enc.encrypt_path(Path("/test/path"))

        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_decrypt_invalid_data_raises(self, tmp_path: Path) -> None:
        """Test decryption of invalid data raises ValueError."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)
        # Initialize the key
        _ = enc.fernet

        with pytest.raises(ValueError, match="Invalid encrypted path"):
            enc.decrypt_path("invalid_encrypted_data")

    def test_key_loaded_once(self, tmp_path: Path) -> None:
        """Test key is loaded/created only once (lazy loading)."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)

        # Access fernet property multiple times
        fernet1 = enc.fernet
        fernet2 = enc.fernet

        assert fernet1 is fernet2

    def test_key_file_created(self, tmp_path: Path) -> None:
        """Test key file is created if not exists."""
        key_path = tmp_path / ".new.key"
        assert not key_path.exists()

        enc = PathEncryption(key_path=key_path)
        _ = enc.fernet  # Trigger key creation

        assert key_path.exists()

    def test_key_file_reused(self, tmp_path: Path) -> None:
        """Test existing key file is reused."""
        key_path = tmp_path / ".existing.key"

        # Create first instance
        enc1 = PathEncryption(key_path=key_path)
        encrypted1 = enc1.encrypt_path(Path("/test"))

        # Create second instance with same key
        enc2 = PathEncryption(key_path=key_path)
        encrypted2 = enc2.encrypt_path(Path("/test"))

        # Both should produce same encryption (deterministic key)
        # Note: Fernet encryption includes timestamp, so values differ
        # But decryption should work
        decrypted1 = enc1.decrypt_path(encrypted1)
        decrypted2 = enc2.decrypt_path(encrypted2)

        assert decrypted1 == decrypted2

    @patch("os.name", "posix")
    @patch("os.chmod")
    def test_key_permissions_set_unix(self, mock_chmod: Mock, tmp_path: Path) -> None:
        """Test restrictive permissions set on Unix."""
        key_path = tmp_path / ".secure.key"
        enc = PathEncryption(key_path=key_path)
        _ = enc.fernet

        # chmod should be called with 0o600
        mock_chmod.assert_called_once_with(key_path, 0o600)


class TestValidatePathSecurity:
    """Test path security validation."""

    def test_valid_path(self, tmp_path: Path) -> None:
        """Test valid path passes validation."""
        valid_path = tmp_path / "mods" / "test.package"

        result = validate_path_security(valid_path)

        assert result is True

    def test_path_traversal_detected(self, tmp_path: Path) -> None:
        """Test path traversal is detected."""
        traversal_path = tmp_path / ".." / ".." / "etc" / "passwd"

        result = validate_path_security(traversal_path)

        assert result is False

    def test_path_traversal_in_string(self, tmp_path: Path) -> None:
        """Test path traversal in path string."""
        traversal_path = Path(str(tmp_path) + "/../../../etc/passwd")

        result = validate_path_security(traversal_path)

        assert result is False

    def test_allowed_base_valid(self, tmp_path: Path) -> None:
        """Test path within allowed base passes."""
        base = tmp_path / "allowed"
        base.mkdir()
        valid_path = base / "subdir" / "file.txt"

        result = validate_path_security(valid_path, allowed_base=base)

        assert result is True

    def test_allowed_base_escape(self, tmp_path: Path) -> None:
        """Test path escaping allowed base fails."""
        base = tmp_path / "allowed"
        base.mkdir()
        escape_path = tmp_path / "other" / "file.txt"

        result = validate_path_security(escape_path, allowed_base=base)

        assert result is False

    def test_allowed_base_with_traversal(self, tmp_path: Path) -> None:
        """Test path with traversal that stays in base."""
        base = tmp_path / "allowed"
        base.mkdir()
        (base / "subdir").mkdir()

        # This resolves to within base but contains ..
        path_with_dots = base / "subdir" / ".." / "file.txt"

        # Should fail because of ".." detection
        result = validate_path_security(path_with_dots, allowed_base=base)

        assert result is False

    def test_exception_handling(self) -> None:
        """Test exception handling in validation."""
        # Create a mock path that raises on resolve
        mock_path = MagicMock(spec=Path)
        mock_path.resolve.side_effect = OSError("Permission denied")
        mock_path.__str__ = Mock(return_value="/test")

        result = validate_path_security(mock_path)

        assert result is False


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_clean_filename_unchanged(self) -> None:
        """Test clean filename passes through."""
        result = sanitize_filename("valid_mod_name.package")

        assert result == "valid_mod_name.package"

    def test_forward_slash_removed(self) -> None:
        """Test forward slash is replaced."""
        result = sanitize_filename("path/to/file.package")

        assert "/" not in result
        assert "_" in result

    def test_backslash_removed(self) -> None:
        """Test backslash is replaced."""
        result = sanitize_filename("path\\to\\file.package")

        assert "\\" not in result

    def test_double_dots_removed(self) -> None:
        """Test double dots are replaced."""
        result = sanitize_filename("..\\..\\etc\\passwd")

        assert ".." not in result

    def test_null_byte_removed(self) -> None:
        """Test null byte is replaced."""
        result = sanitize_filename("test\x00.package")

        assert "\x00" not in result

    def test_colon_removed(self) -> None:
        """Test colon is replaced (Windows drive letters)."""
        result = sanitize_filename("C:\\file.package")

        assert ":" not in result

    def test_windows_special_chars_removed(self) -> None:
        """Test Windows special characters are replaced."""
        result = sanitize_filename('file<>:"|?*.package')

        for char in ["<", ">", ":", '"', "|", "?", "*"]:
            assert char not in result

    def test_max_length_enforced(self) -> None:
        """Test filename is truncated to 255 chars."""
        long_name = "a" * 300 + ".package"

        result = sanitize_filename(long_name)

        assert len(result) <= 255

    def test_extension_preserved_on_truncation(self) -> None:
        """Test file extension is preserved when truncating."""
        long_name = "a" * 300 + ".package"

        result = sanitize_filename(long_name)

        assert result.endswith(".package")

    def test_multiple_dangerous_chars(self) -> None:
        """Test multiple dangerous characters are all replaced."""
        dangerous = "../path/to\\..\\file:name?.package"

        result = sanitize_filename(dangerous)

        for char in ["/", "\\", "..", ":", "?"]:
            assert char not in result

    def test_empty_filename(self) -> None:
        """Test empty filename handling."""
        result = sanitize_filename("")

        assert result == ""

    def test_only_dangerous_chars(self) -> None:
        """Test filename with only dangerous chars."""
        result = sanitize_filename("../")

        assert ".." not in result
        assert "/" not in result


class TestSecurityIntegration:
    """Integration tests for security module."""

    def test_encrypted_path_is_sanitized(self, tmp_path: Path) -> None:
        """Test that decrypted paths can be validated."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)

        # Encrypt a valid path
        original = tmp_path / "mods" / "valid.package"
        encrypted = enc.encrypt_path(original)
        decrypted = enc.decrypt_path(encrypted)

        # Validate the decrypted path
        is_valid = validate_path_security(decrypted, allowed_base=tmp_path)

        assert is_valid is True

    def test_sanitize_before_path_operations(self, tmp_path: Path) -> None:
        """Test sanitizing filename before creating path."""
        dangerous_name = "../../../etc/passwd"
        safe_name = sanitize_filename(dangerous_name)
        safe_path = tmp_path / safe_name

        is_valid = validate_path_security(safe_path, allowed_base=tmp_path)

        assert is_valid is True

    def test_full_security_chain(self, tmp_path: Path) -> None:
        """Test complete security validation chain."""
        key_path = tmp_path / ".test.key"
        enc = PathEncryption(key_path=key_path)

        # Start with user input (potentially dangerous)
        user_input = "malicious/../../../mod.package"

        # Step 1: Sanitize filename
        safe_name = sanitize_filename(user_input)

        # Step 2: Create path within allowed base
        safe_path = tmp_path / "mods" / safe_name

        # Step 3: Validate path security
        is_valid = validate_path_security(safe_path, allowed_base=tmp_path)
        assert is_valid is True

        # Step 4: Encrypt for storage
        encrypted = enc.encrypt_path(safe_path)
        assert len(encrypted) > 0

        # Step 5: Decrypt for use
        decrypted = enc.decrypt_path(encrypted)
        assert decrypted == safe_path.resolve()
