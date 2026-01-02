"""Comprehensive tests for exception hierarchy to achieve 85%+ coverage."""

from pathlib import Path

import pytest

from src.core.exceptions import (
    BackupError,
    ConflictError,
    DeployError,
    EncryptionError,
    GameProcessError,
    HashValidationError,
    LoadOrderError,
    ModManagerException,
    ModScanError,
    PathError,
    SecurityError,
)


class TestModManagerException:
    """Test base exception class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = ModManagerException("Test error")
        assert str(exc) == "[UNKNOWN] Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "UNKNOWN"
        assert exc.recovery_hint is None

    def test_exception_with_code(self):
        """Test exception with custom error code."""
        exc = ModManagerException("Test error", error_code="TEST001")
        assert exc.error_code == "TEST001"
        assert "[TEST001]" in str(exc)

    def test_exception_with_recovery_hint(self):
        """Test exception with recovery suggestion."""
        exc = ModManagerException("Test error", error_code="TEST002", recovery_hint="Try again")
        assert "Try again" in str(exc)
        assert exc.recovery_hint == "Try again"

    def test_exception_with_context(self):
        """Test exception with additional context kwargs."""
        exc = ModManagerException(
            "Test error", error_code="TEST003", user_id=123, file_name="test.txt"
        )
        assert exc.context["user_id"] == 123
        assert exc.context["file_name"] == "test.txt"


class TestModScanError:
    """Test mod scanning error."""

    def test_basic_scan_error(self):
        """Test basic scan error creation."""
        path = Path("test_mod.package")
        exc = ModScanError(path, "Invalid signature")
        assert "test_mod.package" in str(exc)
        assert "Invalid signature" in str(exc)
        assert exc.error_code == "SCAN001"
        assert exc.path == path
        assert exc.reason == "Invalid signature"

    def test_scan_error_with_custom_code(self):
        """Test scan error with custom error code."""
        path = Path("corrupted.package")
        exc = ModScanError(path, "Corrupted data", error_code="SCAN999")
        assert exc.error_code == "SCAN999"

    def test_scan_error_with_recovery_hint(self):
        """Test scan error with custom recovery hint."""
        path = Path("missing.package")
        exc = ModScanError(path, "File not found", recovery_hint="Re-download mod")
        assert "Re-download mod" in str(exc)

    def test_scan_error_default_recovery_hint(self):
        """Test scan error uses default recovery hint."""
        path = Path("test.package")
        exc = ModScanError(path, "Unknown issue")
        assert "Check file integrity" in str(exc)


class TestDeployError:
    """Test deployment error."""

    def test_basic_deploy_error(self):
        """Test basic deployment error."""
        exc = DeployError("copy")
        assert "copy" in str(exc)
        assert exc.operation == "copy"
        assert exc.affected_mods == []

    def test_deploy_error_with_affected_mods(self):
        """Test deployment error with affected mods list."""
        mods = [Path("mod1.package"), Path("mod2.package")]
        exc = DeployError("move", affected_mods=mods)
        assert "2 mods" in str(exc)
        assert len(exc.affected_mods) == 2

    def test_deploy_error_singular_mod(self):
        """Test deployment error with single affected mod."""
        mods = [Path("single.package")]
        exc = DeployError("link", affected_mods=mods)
        assert "1 mod" in str(exc)
        assert "mods" not in str(exc)  # Should be "mod" not "mods"

    def test_deploy_error_default_recovery_hint(self):
        """Test deployment error has default recovery hint."""
        exc = DeployError("validate")
        assert "backup" in str(exc).lower()


class TestBackupError:
    """Test backup/restore error."""

    def test_backup_error_with_message(self):
        """Test backup error with explicit message."""
        exc = BackupError(message="Custom backup failure")
        assert "Custom backup failure" in str(exc)

    def test_backup_error_auto_message(self):
        """Test backup error builds message from parameters."""
        path = Path("C:/backups/mod_backup.zip")
        exc = BackupError(backup_path=path, operation_type="create", reason="Disk full")
        assert "create" in str(exc)
        assert "Disk full" in str(exc)
        assert exc.backup_path == path
        assert exc.operation_type == "create"

    def test_backup_error_restore_operation(self):
        """Test backup error for restore operation."""
        path = Path("backup_20260102.zip")
        exc = BackupError(backup_path=path, operation_type="restore", reason="Corrupted")
        assert "restore" in str(exc)
        assert "Corrupted" in str(exc)

    def test_backup_error_default_recovery_hint(self):
        """Test backup error has default recovery hint."""
        exc = BackupError(reason="Unknown")
        assert "disk space" in str(exc).lower()

    def test_backup_error_with_kwargs(self):
        """Test backup error accepts additional kwargs."""
        exc = BackupError(reason="Test", size=1024, timestamp="2026-01-02")
        assert exc.context["size"] == 1024
        assert exc.context["timestamp"] == "2026-01-02"


class TestSecurityError:
    """Test security validation error."""

    def test_security_error_basic(self):
        """Test basic security error."""
        exc = SecurityError(threat_type="path_traversal")
        assert "Security" in str(exc)
        assert exc.severity == "HIGH"

    def test_security_error_with_path(self):
        """Test security error with affected path."""
        path = Path("../../etc/passwd")
        exc = SecurityError(threat_type="path_traversal", affected_path=path)
        assert str(path) in str(exc)
        assert exc.affected_path == path

    def test_security_error_severity_levels(self):
        """Test security error with different severity levels."""
        low = SecurityError(threat_type="suspicious", severity="LOW")
        assert low.severity == "LOW"

        critical = SecurityError(threat_type="malware", severity="CRITICAL")
        assert critical.severity == "CRITICAL"

    def test_security_error_with_details(self):
        """Test security error with additional details."""
        exc = SecurityError(
            threat_type="oversized_file",
            affected_path=Path("huge.package"),
            details="File exceeds 500MB limit",
        )
        assert "oversized_file" in str(exc) or "500MB" in str(exc) or "exceeds" in str(exc)

    def test_security_error_custom_message(self):
        """Test security error with custom message."""
        exc = SecurityError(message="Custom security alert")
        assert "Custom security alert" in str(exc)

    def test_security_error_with_kwargs(self):
        """Test security error stores additional context."""
        exc = SecurityError(threat_type="hash_mismatch", file_size=1024, expected_hash="abc123")
        assert exc.context["file_size"] == 1024
        assert exc.context["expected_hash"] == "abc123"


class TestGameProcessError:
    """Test game process management error."""

    def test_game_process_error_basic(self):
        """Test basic game process error."""
        exc = GameProcessError(process_name="TS4_x64.exe", reason="Access denied")
        assert "TS4_x64.exe" in str(exc)
        assert "Access denied" in str(exc)
        assert exc.process_name == "TS4_x64.exe"

    def test_game_process_error_with_action(self):
        """Test game process error with action."""
        exc = GameProcessError(process_name="TS4.exe", action="terminate", reason="Timeout")
        assert "terminate" in str(exc)

    def test_game_process_error_default_recovery_hint(self):
        """Test game process error has default recovery hint."""
        exc = GameProcessError(process_name="TS4.exe", reason="Frozen")
        assert "Sims 4" in str(exc) or "manually" in str(exc).lower()


class TestPathError:
    """Test path validation error."""

    def test_path_error_basic(self):
        """Test basic path error."""
        path = Path("C:/invalid/../../../path")
        exc = PathError(path=path, reason="Path traversal detected")
        assert str(path) in str(exc)
        assert "traversal" in str(exc)
        assert exc.path == path

    def test_path_error_with_type(self):
        """Test path error with path type."""
        path = Path("/missing/folder")
        exc = PathError(path=path, path_type="mods_folder", reason="Does not exist")
        assert "mods_folder" in str(exc)

    def test_path_error_default_recovery_hint(self):
        """Test path error has default recovery hint."""
        path = Path("test.txt")
        exc = PathError(path=path, reason="Invalid")
        assert "Configure" in str(exc) or "Settings" in str(exc)


class TestLoadOrderError:
    """Test load order management error."""

    def test_load_order_error_basic(self):
        """Test basic load order error."""
        exc = LoadOrderError(validation_failure="Circular dependency detected")
        assert "Circular dependency" in str(exc)
        assert exc.validation_failure == "Circular dependency detected"

    def test_load_order_error_with_category(self):
        """Test load order error with category and slot."""
        exc = LoadOrderError(validation_failure="Invalid slot", category="CoreScripts", slot=1)
        assert "CoreScripts" in str(exc)
        assert "slot=1" in str(exc)

    def test_load_order_error_default_recovery_hint(self):
        """Test load order error has default recovery hint."""
        exc = LoadOrderError(validation_failure="Invalid priority")
        assert "configuration" in str(exc).lower()


class TestConflictError:
    """Test mod conflict detection error."""

    def test_conflict_error_basic(self):
        """Test basic conflict error."""
        exc = ConflictError(resource_id="0x12345678", conflicting_mods=["ModA", "ModB"])
        assert "ModA" in str(exc)
        assert "ModB" in str(exc)
        assert "0x12345678" in str(exc)
        assert len(exc.conflicting_mods) == 2

    def test_conflict_error_with_type(self):
        """Test conflict error with conflict type."""
        exc = ConflictError(
            resource_id="0xABCDEF", conflicting_mods=["ModX", "ModY"], conflict_type="tuning"
        )
        assert "tuning" in str(exc).lower()

    def test_conflict_error_multiple_conflicts(self):
        """Test conflict error with many mods."""
        mods = [f"Mod{i}" for i in range(10)]
        exc = ConflictError(resource_id="0x99999999", conflicting_mods=mods)
        assert "Mod0" in str(exc)
        assert "Mod9" in str(exc)

    def test_conflict_error_default_recovery_hint(self):
        """Test conflict error has default recovery hint."""
        exc = ConflictError(resource_id="0x11111111", conflicting_mods=["A", "B"])
        assert "load order" in str(exc).lower() or "remove" in str(exc).lower()


class TestEncryptionError:
    """Test encryption/decryption error."""

    def test_encryption_error_basic(self):
        """Test basic encryption error."""
        exc = EncryptionError(operation="encrypt")
        assert "encrypt" in str(exc)
        assert exc.operation == "encrypt"

    def test_encryption_error_decrypt(self):
        """Test decryption error."""
        exc = EncryptionError(operation="decrypt", reason="Corrupted data")
        assert "decrypt" in str(exc)
        assert "Corrupted" in str(exc)

    def test_encryption_error_with_key_path(self):
        """Test encryption error with key path."""
        key_path = Path("C:/keys/encryption.key")
        exc = EncryptionError(operation="encrypt", key_path=key_path)
        assert str(key_path) in str(exc)

    def test_encryption_error_default_recovery_hint(self):
        """Test encryption error has default recovery hint."""
        exc = EncryptionError(operation="encrypt")
        assert "key" in str(exc).lower() or "BACKUP" in str(exc)


class TestHashValidationError:
    """Test hash validation error."""

    def test_hash_validation_error_basic(self):
        """Test basic hash validation error."""
        path = Path("corrupted.package")
        exc = HashValidationError(path, expected_hash=0xABC123, actual_hash=0xDEF456)
        assert "ABC123" in str(exc)
        assert "DEF456" in str(exc)
        assert exc.file_path == path
        assert exc.expected_hash == 0xABC123
        assert exc.actual_hash == 0xDEF456

    def test_hash_validation_error_displays_hex(self):
        """Test hash validation error displays hex values."""
        path = Path("file.txt")
        exc = HashValidationError(path, expected_hash=255, actual_hash=256)
        # Check hex format (000000FF and 00000100)
        assert "FF" in str(exc).upper()
        assert "100" in str(exc).upper()

    def test_hash_validation_error_default_recovery_hint(self):
        """Test hash validation error has default recovery hint."""
        path = Path("test.package")
        exc = HashValidationError(path, expected_hash=111, actual_hash=222)
        assert "re-download" in str(exc).lower() or "Delete" in str(exc)


class TestExceptionInheritance:
    """Test exception inheritance and polymorphism."""

    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from ModManagerException."""
        exceptions = [
            ModScanError(Path("test"), "test"),
            DeployError("test"),
            BackupError(reason="test"),
            SecurityError(threat_type="test"),
            GameProcessError(process_name="test", reason="test"),
            PathError(path=Path("test"), reason="test"),
            LoadOrderError(validation_failure="test"),
            ConflictError(resource_id="0x00000000", conflicting_mods=["test"]),
            EncryptionError(operation="test"),
            HashValidationError(Path("test"), expected_hash=1, actual_hash=2),
        ]

        for exc in exceptions:
            assert isinstance(exc, ModManagerException)
            assert isinstance(exc, Exception)

    def test_exception_catch_polymorphism(self):
        """Test catching specific exceptions with base class."""
        try:
            raise DeployError("test")
        except ModManagerException as e:
            assert isinstance(e, DeployError)
            assert e.error_code == "DEPLOY001"

    def test_exception_hierarchy_catch(self):
        """Test catching any mod manager exception."""
        exceptions_to_test = [
            ModScanError(Path("test"), "test"),
            SecurityError(threat_type="test"),
            PathError(path=Path("test"), reason="test"),
        ]

        for exc_instance in exceptions_to_test:
            try:
                raise exc_instance
            except ModManagerException:
                pass  # Successfully caught via base class
            else:
                pytest.fail(f"Failed to catch {type(exc_instance).__name__}")
