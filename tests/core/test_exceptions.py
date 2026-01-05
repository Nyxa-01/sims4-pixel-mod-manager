"""Tests for exception hierarchy and error handling."""

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

    def test_basic_exception(self) -> None:
        """Test basic exception creation."""
        exc = ModManagerException("Test error")

        assert str(exc) == "[UNKNOWN] Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "UNKNOWN"
        assert exc.recovery_hint is None

    def test_exception_with_code(self) -> None:
        """Test exception with error code."""
        exc = ModManagerException("Test error", error_code="TEST001")

        assert "[TEST001]" in str(exc)
        assert exc.error_code == "TEST001"

    def test_exception_with_recovery_hint(self) -> None:
        """Test exception with recovery hint."""
        exc = ModManagerException("Test error", recovery_hint="Try restarting the application")

        assert "Suggestion: Try restarting" in str(exc)
        assert exc.recovery_hint == "Try restarting the application"

    def test_exception_with_context(self) -> None:
        """Test exception with additional context."""
        exc = ModManagerException("Test error", extra_info="some value", another_key=123)

        assert exc.context["extra_info"] == "some value"
        assert exc.context["another_key"] == 123

    def test_exception_is_catchable(self) -> None:
        """Test exception can be caught as Exception."""
        with pytest.raises(Exception):
            raise ModManagerException("Test")

    def test_exception_inheritance(self) -> None:
        """Test exception inherits from Exception."""
        exc = ModManagerException("Test")
        assert isinstance(exc, Exception)


class TestModScanError:
    """Test mod scanning error."""

    def test_mod_scan_error_creation(self, tmp_path: Path) -> None:
        """Test ModScanError creation."""
        mod_path = tmp_path / "test.package"
        exc = ModScanError(mod_path, "Invalid DBPF header")

        assert mod_path.name in str(exc)
        assert "Invalid DBPF header" in str(exc)
        assert exc.path == mod_path
        assert exc.reason == "Invalid DBPF header"

    def test_mod_scan_error_default_hint(self, tmp_path: Path) -> None:
        """Test default recovery hint."""
        exc = ModScanError(tmp_path / "test.package", "Test reason")

        assert "rescan" in exc.recovery_hint.lower()

    def test_mod_scan_error_custom_code(self, tmp_path: Path) -> None:
        """Test custom error code."""
        exc = ModScanError(tmp_path / "test.package", "Reason", error_code="SCAN002")

        assert exc.error_code == "SCAN002"


class TestDeployError:
    """Test deployment error."""

    def test_deploy_error_simple(self) -> None:
        """Test simple deploy error."""
        exc = DeployError("copy")

        assert "copy" in str(exc)
        assert exc.operation == "copy"
        assert exc.affected_mods == []

    def test_deploy_error_with_affected_mods(self, tmp_path: Path) -> None:
        """Test deploy error with affected mods."""
        mods = [tmp_path / "mod1.package", tmp_path / "mod2.package"]
        exc = DeployError("move", affected_mods=mods)

        assert "2 mods" in str(exc)
        assert len(exc.affected_mods) == 2

    def test_deploy_error_single_mod(self, tmp_path: Path) -> None:
        """Test deploy error with single mod."""
        mods = [tmp_path / "mod1.package"]
        exc = DeployError("link", affected_mods=mods)

        assert "1 mod)" in str(exc)  # Note: no 's' plural

    def test_deploy_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = DeployError("copy")

        assert "backup" in exc.recovery_hint.lower()


class TestBackupError:
    """Test backup error."""

    def test_backup_error_with_path(self, tmp_path: Path) -> None:
        """Test backup error with path."""
        backup_path = tmp_path / "backup.zip"
        exc = BackupError(
            backup_path=backup_path,
            operation_type="create",
            reason="Disk full",
        )

        assert "create" in str(exc).lower()
        assert exc.backup_path == backup_path

    def test_backup_error_restore(self, tmp_path: Path) -> None:
        """Test backup error for restore operation."""
        exc = BackupError(
            backup_path=tmp_path / "backup.zip",
            operation_type="restore",
            reason="Corrupted archive",
        )

        assert "restore" in str(exc).lower()
        assert exc.operation_type == "restore"

    def test_backup_error_message_override(self) -> None:
        """Test backup error with direct message."""
        exc = BackupError(message="Custom backup error message")

        assert "Custom backup error message" in str(exc)

    def test_backup_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = BackupError(reason="Test")

        assert "disk space" in exc.recovery_hint.lower()


class TestSecurityError:
    """Test security error."""

    def test_security_error_path_traversal(self, tmp_path: Path) -> None:
        """Test security error for path traversal."""
        exc = SecurityError(
            threat_type="PATH_TRAVERSAL",
            affected_path=tmp_path / "../etc/passwd",
            severity="CRITICAL",
        )

        assert "PATH_TRAVERSAL" in str(exc)
        assert exc.severity == "CRITICAL"
        assert "CRITICAL" in str(exc)

    def test_security_error_hash_mismatch(self, tmp_path: Path) -> None:
        """Test security error for hash mismatch."""
        exc = SecurityError(
            threat_type="HASH_MISMATCH",
            affected_path=tmp_path / "suspicious.package",
            severity="HIGH",
            details="Expected 0xABCD, got 0x1234",
        )

        assert "HASH_MISMATCH" in str(exc)
        assert exc.details is not None

    def test_security_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = SecurityError(threat_type="TEST", affected_path=Path("/test"))

        assert "malware" in exc.recovery_hint.lower()

    def test_security_error_custom_message(self) -> None:
        """Test security error with custom message."""
        exc = SecurityError(message="Custom security warning")

        assert "Custom security warning" in str(exc)

    def test_security_error_severity_levels(self) -> None:
        """Test different severity levels."""
        for severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            exc = SecurityError(
                threat_type="TEST",
                affected_path=Path("/test"),
                severity=severity,
            )
            assert exc.severity == severity


class TestGameProcessError:
    """Test game process error."""

    def test_game_process_error_detect(self) -> None:
        """Test game process detection error."""
        exc = GameProcessError(
            process_name="TS4_x64.exe",
            action="detect",
            reason="Process not found",
        )

        assert "TS4_x64.exe" in str(exc)
        assert "detect" in str(exc)
        assert exc.process_name == "TS4_x64.exe"

    def test_game_process_error_terminate(self) -> None:
        """Test game process termination error."""
        exc = GameProcessError(
            process_name="TS4_x64.exe",
            action="terminate",
            reason="Access denied",
        )

        assert "terminate" in str(exc)
        assert exc.action == "terminate"

    def test_game_process_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = GameProcessError()

        assert "close" in exc.recovery_hint.lower()

    def test_game_process_error_message_override(self) -> None:
        """Test custom message."""
        exc = GameProcessError(message="Custom game error")

        assert "Custom game error" in str(exc)


class TestPathError:
    """Test path error."""

    def test_path_error_missing_mods(self, tmp_path: Path) -> None:
        """Test path error for missing mods folder."""
        exc = PathError(
            path=tmp_path / "Mods",
            path_type="mods_folder",
            reason="Directory does not exist",
        )

        assert "mods_folder" in str(exc)
        assert exc.path_type == "mods_folder"

    def test_path_error_permissions(self, tmp_path: Path) -> None:
        """Test path error for permission issues."""
        exc = PathError(
            path=tmp_path,
            path_type="game_install",
            reason="Insufficient permissions",
        )

        assert "permissions" in str(exc).lower()

    def test_path_error_default_hint(self) -> None:
        """Test default recovery hint includes path type."""
        exc = PathError(path_type="backup_folder")

        assert "backup_folder" in exc.recovery_hint

    def test_path_error_message_override(self) -> None:
        """Test custom message."""
        exc = PathError(message="Custom path error")

        assert "Custom path error" in str(exc)


class TestLoadOrderError:
    """Test load order error."""

    def test_load_order_error_invalid_slot(self) -> None:
        """Test load order error for invalid slot."""
        exc = LoadOrderError(
            validation_failure="Slot number out of range",
            category="Core",
            slot=1001,
        )

        assert "slot=1001" in str(exc)
        assert exc.slot == 1001

    def test_load_order_error_duplicate_category(self) -> None:
        """Test load order error for duplicate category."""
        exc = LoadOrderError(
            validation_failure="Duplicate category name",
            category="Mods",
            slot=100,  # Both category and slot needed for them to appear in str
        )

        assert "Mods" in str(exc)
        assert exc.category == "Mods"

    def test_load_order_error_simple(self) -> None:
        """Test simple load order error."""
        exc = LoadOrderError(validation_failure="Invalid prefix format")

        assert "Invalid prefix format" in str(exc)
        assert exc.category is None
        assert exc.slot is None

    def test_load_order_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = LoadOrderError(validation_failure="Test")

        assert "load order" in exc.recovery_hint.lower()


class TestConflictError:
    """Test conflict error."""

    def test_conflict_error_two_mods(self) -> None:
        """Test conflict between two mods."""
        exc = ConflictError(
            resource_id="0x12345678",
            conflicting_mods=["ModA", "ModB"],
            conflict_type="tuning",
        )

        assert "ModA" in str(exc)
        assert "ModB" in str(exc)
        assert "tuning" in str(exc).lower()

    def test_conflict_error_multiple_mods(self) -> None:
        """Test conflict among multiple mods."""
        exc = ConflictError(
            resource_id="0xABCDEF00",
            conflicting_mods=["Mod1", "Mod2", "Mod3"],
        )

        assert len(exc.conflicting_mods) == 3

    def test_conflict_error_resource_id(self) -> None:
        """Test resource ID is included."""
        exc = ConflictError(
            resource_id="0xDEADBEEF",
            conflicting_mods=["TestMod"],
        )

        assert "0xDEADBEEF" in str(exc)
        assert exc.resource_id == "0xDEADBEEF"

    def test_conflict_error_default_hint(self) -> None:
        """Test default recovery hint."""
        exc = ConflictError(
            resource_id="0x00000000",
            conflicting_mods=["A", "B"],
        )

        assert "load order" in exc.recovery_hint.lower()


class TestEncryptionError:
    """Test encryption error."""

    def test_encryption_error_encrypt(self) -> None:
        """Test encryption operation error."""
        exc = EncryptionError(operation="encrypt", reason="Invalid key")

        assert "encrypt" in str(exc)
        assert exc.operation == "encrypt"

    def test_encryption_error_decrypt(self, tmp_path: Path) -> None:
        """Test decryption operation error."""
        key_path = tmp_path / ".encryption.key"
        exc = EncryptionError(
            operation="decrypt",
            key_path=key_path,
            reason="Corrupted data",
        )

        assert "decrypt" in str(exc)
        assert str(key_path) in str(exc)

    def test_encryption_error_recovery_hint(self) -> None:
        """Test recovery hint mentions backup."""
        exc = EncryptionError(operation="encrypt")

        assert "BACKUP" in exc.recovery_hint


class TestHashValidationError:
    """Test hash validation error."""

    def test_hash_validation_error(self, tmp_path: Path) -> None:
        """Test hash validation error creation."""
        file_path = tmp_path / "test.package"
        exc = HashValidationError(
            file_path=file_path,
            expected_hash=0xABCD1234,
            actual_hash=0x5678EFAB,
        )

        assert "ABCD1234" in str(exc)
        assert "5678EFAB" in str(exc)
        assert exc.expected_hash == 0xABCD1234
        assert exc.actual_hash == 0x5678EFAB

    def test_hash_validation_error_message(self, tmp_path: Path) -> None:
        """Test error message includes corruption warning."""
        exc = HashValidationError(
            file_path=tmp_path / "test.package",
            expected_hash=0,
            actual_hash=1,
        )

        assert "corrupted" in str(exc).lower()

    def test_hash_validation_error_hint(self, tmp_path: Path) -> None:
        """Test recovery hint suggests re-download."""
        exc = HashValidationError(
            file_path=tmp_path / "test.package",
            expected_hash=0,
            actual_hash=1,
        )

        assert "download" in exc.recovery_hint.lower()


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test all custom exceptions inherit from ModManagerException."""
        exception_classes = [
            ModScanError,
            DeployError,
            BackupError,
            SecurityError,
            GameProcessError,
            PathError,
            LoadOrderError,
            ConflictError,
            EncryptionError,
            HashValidationError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, ModManagerException)

    def test_can_catch_all_with_base(self, tmp_path: Path) -> None:
        """Test catching all exceptions with base class."""
        exceptions_to_test = [
            ModScanError(tmp_path / "test.package", "reason"),
            DeployError("copy"),
            BackupError(reason="test"),
            SecurityError(message="test"),
            GameProcessError(reason="test"),
            PathError(reason="test"),
            LoadOrderError("test"),
            ConflictError("0x00", ["mod"]),
            EncryptionError("encrypt"),
            HashValidationError(tmp_path / "test", 0, 1),
        ]

        for exc in exceptions_to_test:
            try:
                raise exc
            except ModManagerException as caught:
                assert caught is exc

    def test_exception_string_representation(self, tmp_path: Path) -> None:
        """Test all exceptions have proper string representation."""
        exceptions = [
            ModScanError(tmp_path / "test.package", "reason"),
            DeployError("copy"),
            BackupError(reason="test"),
            SecurityError(message="test"),
        ]

        for exc in exceptions:
            str_repr = str(exc)
            assert len(str_repr) > 0
            assert "[" in str_repr  # Has error code
