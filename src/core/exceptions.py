"""Exception hierarchy for Sims 4 Pixel Mod Manager.

This module defines all custom exceptions used throughout the application,
providing detailed error context and recovery hints for robust error handling.
"""

from pathlib import Path
from typing import Optional


class ModManagerException(Exception):
    """Base exception for all mod manager errors.

    All custom exceptions inherit from this base class, allowing for
    broad exception handling when needed.

    Attributes:
        message: Human-readable error message
        error_code: Unique error code for logging/tracking
        recovery_hint: Optional suggestion for resolving the error
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        recovery_hint: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        """Initialize base exception.

        Args:
            message: Error message describing what went wrong
            error_code: Unique error code (e.g., "SCAN001")
            recovery_hint: Optional hint for user to resolve issue
            **kwargs: Additional context (stored in self.context)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.recovery_hint = recovery_hint
        # Store additional context from kwargs
        self.context = kwargs

    def __str__(self) -> str:
        """User-friendly string representation."""
        base = f"[{self.error_code}] {self.message}"
        if self.recovery_hint:
            base += f"\nSuggestion: {self.recovery_hint}"
        return base


class ModScanError(ModManagerException):
    """Raised when mod file scanning fails validation.

    This exception is raised during the mod detection phase when a file
    cannot be properly scanned, validated, or cataloged.

    Attributes:
        path: Path to the mod file that failed scanning
        reason: Specific reason for scan failure
    """

    def __init__(
        self,
        path: Path,
        reason: str,
        error_code: str = "SCAN001",
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize mod scan error.

        Args:
            path: Path to problematic mod file
            reason: Detailed reason for failure
            error_code: Error code (default: SCAN001)
            recovery_hint: Optional recovery suggestion
        """
        self.path = path
        self.reason = reason

        message = f"Scan failed for '{path.name}': {reason}"
        if recovery_hint is None:
            recovery_hint = "Check file integrity and try rescanning"

        super().__init__(message, error_code, recovery_hint)


class DeployError(ModManagerException):
    """Raised when mod deployment fails.

    Deployment failures can occur during file copying, permission issues,
    or when applying load order changes to the Mods folder.

    Attributes:
        operation: The deployment operation that failed
        affected_mods: List of mod paths affected by failure
    """

    def __init__(
        self,
        operation: str,
        affected_mods: Optional[list[Path]] = None,
        error_code: str = "DEPLOY001",
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize deployment error.

        Args:
            operation: Operation that failed (e.g., "copy", "move", "link")
            affected_mods: Optional list of affected mod paths
            error_code: Error code (default: DEPLOY001)
            recovery_hint: Optional recovery suggestion
        """
        self.operation = operation
        self.affected_mods = affected_mods or []

        mod_count = len(self.affected_mods)
        message = f"Deployment failed during '{operation}'"
        if mod_count > 0:
            message += f" (affected: {mod_count} mod{'s' if mod_count != 1 else ''})"

        if recovery_hint is None:
            recovery_hint = "Restore from backup and check folder permissions"

        super().__init__(message, error_code, recovery_hint)


class BackupError(ModManagerException):
    """Raised when backup or restore operations fail.

    Critical for data safety - this exception indicates problems with
    creating backups before deployment or restoring after failures.

    Attributes:
        backup_path: Path to the backup location
        operation_type: Whether this was a "create" or "restore" operation
    """

    def __init__(
        self,
        message: Optional[str] = None,
        backup_path: Optional[Path] = None,
        operation_type: str = "unknown",
        reason: str = "Unknown error",
        error_code: str = "BACKUP001",
        recovery_hint: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        """Initialize backup error.

        Args:
            backup_path: Path to backup location
            operation_type: "create" or "restore"
            reason: Detailed reason for failure
            error_code: Error code (default: BACKUP001)
            recovery_hint: Optional recovery suggestion
        """
        self.backup_path = backup_path
        self.operation_type = operation_type
        self.reason = reason

        # If message not provided, build it from parameters
        if message is None:
            if backup_path:
                message = f"Backup {operation_type} failed for '{backup_path}': {reason}"
            else:
                message = reason

        if recovery_hint is None:
            recovery_hint = "Ensure sufficient disk space and write permissions"

        super().__init__(message, error_code, recovery_hint, **kwargs)


class SecurityError(ModManagerException):
    """Raised when security validation fails or malicious content detected.

    This is a CRITICAL exception indicating potential security threats such as:
    - Path traversal attempts
    - Oversized files (>500MB)
    - Invalid file signatures
    - Hash mismatches after copy operations

    Attributes:
        threat_type: Type of security threat detected
        affected_path: Path to the suspicious file
        severity: Threat severity level
    """

    def __init__(
        self,
        threat_type: Optional[str] = None,
        affected_path: Optional[Path] = None,
        severity: str = "HIGH",
        details: Optional[str] = None,
        error_code: str = "SECURITY001",
        message: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        """Initialize security error.

        Args:
            threat_type: Type of threat (e.g., "PATH_TRAVERSAL", "HASH_MISMATCH")
            affected_path: Path to suspicious file
            severity: Threat level ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            details: Optional additional details
            error_code: Error code (default: SECURITY001)
            message: Optional direct message (overrides default construction)
            **kwargs: Additional context (e.g., file_path, reason, recovery_hint)
        """
        self.threat_type = threat_type
        self.affected_path = affected_path
        self.severity = severity
        self.details = details

        # Allow direct message or construct from parameters
        if message is None:
            if threat_type and affected_path:
                message = f"[{severity}] Security threat detected: {threat_type}"
                if details:
                    message += f" - {details}"
                message += f"\nAffected file: {affected_path}"
            else:
                message = "Security validation failed"

        # Extract recovery_hint from kwargs or use default
        recovery_hint_val = kwargs.pop("recovery_hint", None)
        recovery_hint: Optional[str] = (
            str(recovery_hint_val)
            if recovery_hint_val is not None
            else "Do not proceed. Review file source and scan for malware."
        )

        super().__init__(message, error_code, recovery_hint, **kwargs)


class GameProcessError(ModManagerException):
    """Raised when Sims 4 game process interaction fails.

    This exception handles errors related to:
    - Detecting running Sims 4 instances
    - Killing game processes before deployment
    - Game installation path detection
    - Save file validation

    Attributes:
        process_name: Name of the game process
        action: Action that was being performed
    """

    def __init__(
        self,
        message: Optional[str] = None,
        process_name: str = "unknown",
        action: str = "unknown",
        reason: str = "Unknown error",
        error_code: str = "GAME001",
        recovery_hint: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        """Initialize game process error.

        Args:
            process_name: Game process name (e.g., "TS4_x64.exe")
            action: Action being performed (e.g., "detect", "terminate")
            reason: Detailed reason for failure
            error_code: Error code (default: GAME001)
            recovery_hint: Optional recovery suggestion
        """
        self.process_name = process_name
        self.action = action
        self.reason = reason

        # If message not provided, build it from parameters
        if message is None:
            message = f"Game process '{process_name}' {action} failed: {reason}"

        if recovery_hint is None:
            recovery_hint = "Close The Sims 4 manually and try again"

        super().__init__(message, error_code, recovery_hint, **kwargs)


class PathError(ModManagerException):
    """Raised when game or mod paths are invalid or inaccessible.

    Common scenarios:
    - Mods folder doesn't exist
    - Game installation not found
    - Insufficient permissions
    - Path too long (Windows MAX_PATH)

    Attributes:
        path: The problematic path
        path_type: Type of path (e.g., "mods_folder", "game_install")
        reason: Specific validation failure reason
    """

    def __init__(
        self,
        message: Optional[str] = None,
        path: Optional[Path] = None,
        path_type: str = "unknown",
        reason: str = "Unknown error",
        error_code: str = "PATH001",
        recovery_hint: Optional[str] = None,
        **kwargs: object,
    ) -> None:
        """Initialize path error.

        Args:
            path: Invalid path
            path_type: Type of path being validated
            reason: Why validation failed
            error_code: Error code (default: PATH001)
            recovery_hint: Optional recovery suggestion
        """
        self.path = path
        self.path_type = path_type
        self.reason = reason

        # If message not provided, build it from parameters
        if message is None:
            if path:
                message = f"Invalid {path_type} path '{path}': {reason}"
            else:
                message = reason

        if recovery_hint is None:
            recovery_hint = f"Configure valid {path_type} path in Settings"

        super().__init__(message, error_code, recovery_hint, **kwargs)


class LoadOrderError(ModManagerException):
    """Raised when load order validation or sorting fails.

    This exception handles errors in the slot-based prefix system:
    - Invalid slot numbers (not 1-999)
    - Duplicate category slots
    - Script mods in nested folders
    - Prefix format validation failures

    Attributes:
        category: Load order category name
        slot: Slot number (if applicable)
        validation_failure: Specific validation that failed
    """

    def __init__(
        self,
        validation_failure: str,
        category: Optional[str] = None,
        slot: Optional[int] = None,
        error_code: str = "LOADORDER001",
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize load order error.

        Args:
            validation_failure: What validation check failed
            category: Optional category name
            slot: Optional slot number
            error_code: Error code (default: LOADORDER001)
            recovery_hint: Optional recovery suggestion
        """
        self.category = category
        self.slot = slot
        self.validation_failure = validation_failure

        message = f"Load order validation failed: {validation_failure}"
        if category and slot:
            message += f" (category='{category}', slot={slot})"

        if recovery_hint is None:
            recovery_hint = "Review load order configuration and try again"

        super().__init__(message, error_code, recovery_hint)


class ConflictError(ModManagerException):
    """Raised when mod conflicts are detected and cannot be auto-resolved.

    Occurs when multiple mods modify the same game resources (DBPF resource IDs)
    and the conflict resolution strategy fails or is rejected by the user.

    Attributes:
        resource_id: Conflicting DBPF resource ID
        conflicting_mods: List of mod names that conflict
        conflict_type: Type of conflict (e.g., "tuning", "script", "cas")
    """

    def __init__(
        self,
        resource_id: str,
        conflicting_mods: list[str],
        conflict_type: str = "resource",
        error_code: str = "CONFLICT001",
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize conflict error.

        Args:
            resource_id: DBPF resource ID that conflicts
            conflicting_mods: Names of conflicting mods
            conflict_type: Type of resource conflict
            error_code: Error code (default: CONFLICT001)
            recovery_hint: Optional recovery suggestion
        """
        self.resource_id = resource_id
        self.conflicting_mods = conflicting_mods
        self.conflict_type = conflict_type

        mod_list = ", ".join(conflicting_mods)
        message = (
            f"{conflict_type.capitalize()} conflict detected in resource {resource_id}\n"
            f"Conflicting mods: {mod_list}"
        )

        if recovery_hint is None:
            recovery_hint = (
                "Choose which mod to prioritize using load order, " "or remove conflicting mods"
            )

        super().__init__(message, error_code, recovery_hint)


class EncryptionError(ModManagerException):
    """Raised when config encryption/decryption fails.

    Critical for secure path storage - indicates problems with Fernet
    encryption key management or corrupted encrypted data.

    Attributes:
        operation: Encryption operation that failed
        key_path: Path to encryption key file
    """

    def __init__(
        self,
        operation: str,
        key_path: Optional[Path] = None,
        reason: Optional[str] = None,
        error_code: str = "ENCRYPT001",
    ) -> None:
        """Initialize encryption error.

        Args:
            operation: Operation that failed ("encrypt" or "decrypt")
            key_path: Optional path to encryption key
            reason: Optional detailed reason
            error_code: Error code (default: ENCRYPT001)
        """
        self.operation = operation
        self.key_path = key_path
        self.reason = reason

        message = f"Encryption {operation} failed"
        if reason:
            message += f": {reason}"
        if key_path:
            message += f"\nKey location: {key_path}"

        recovery_hint = (
            "If encryption key is lost, you'll need to reconfigure all paths. "
            "BACKUP YOUR KEY at: %LOCALAPPDATA%\\Sims4ModManager\\.encryption.key"
        )

        super().__init__(message, error_code, recovery_hint)


class HashValidationError(ModManagerException):
    """Raised when CRC32 hash validation fails during file operations.

    Critical security check - indicates file corruption or tampering during:
    - Mod installation (pre/post-copy hash mismatch)
    - Backup creation
    - File downloads

    Attributes:
        file_path: Path to file with hash mismatch
        expected_hash: Expected CRC32 hash
        actual_hash: Actual calculated hash
    """

    def __init__(
        self,
        file_path: Path,
        expected_hash: int,
        actual_hash: int,
        error_code: str = "HASH001",
    ) -> None:
        """Initialize hash validation error.

        Args:
            file_path: Path to corrupted file
            expected_hash: Expected CRC32 hash value
            actual_hash: Actual calculated hash value
            error_code: Error code (default: HASH001)
        """
        self.file_path = file_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash

        message = (
            f"Hash validation failed for '{file_path.name}'\n"
            f"Expected: {expected_hash:08X}, Got: {actual_hash:08X}\n"
            f"File may be corrupted or tampered with."
        )

        recovery_hint = "Delete corrupted file and re-download from trusted source"

        super().__init__(message, error_code, recovery_hint)
