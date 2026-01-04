"""Secure mod file scanner with validation and categorization.

This module provides enterprise-grade file scanning with:
- Security validation (size limits, entropy analysis, signature verification)
- Automatic categorization based on file type and content
- Timeout protection for malicious files
- Thread-safe operations
"""

import ast
import logging
import math
import threading
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from ..core.exceptions import ModScanError, SecurityError
from ..utils.timeout import timeout

logger = logging.getLogger(__name__)

# File type detection
SUPPORTED_EXTENSIONS = {".package", ".py", ".ts4script", ".cfg", ".bpi"}

# Magic bytes for signature verification
MAGIC_BYTES = {
    ".package": b"DBPF",  # DBPF header
    ".ts4script": b"PK\x03\x04",  # ZIP file header
}

# Keywords for categorization
CORE_MOD_KEYWORDS = {
    "mccc",
    "ui_cheats",
    "mc_command",
    "xml_injector",
    "better_exceptions",
    "tmex",
    "pose_player",
}

SCRIPT_KEYWORDS = {"script", "tuning", "injector"}


@dataclass
class ModFile:
    """Represents a scanned mod file with validation results.

    Attributes:
        path: Absolute path to mod file
        size: File size in bytes
        hash: CRC32 hash as hex string
        mod_type: File type classification
        category: Suggested load order category
        is_valid: Whether file passed all validation checks
        validation_errors: List of validation error messages
        entropy: File entropy score (0.0-8.0, higher = more random)
    """

    path: Path
    size: int
    hash: str
    mod_type: str
    category: str
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    entropy: float = 0.0

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.is_valid else "✗"
        return f"ModFile({status} {self.path.name}, {self.mod_type}, {self.category})"


class ModScanner:
    """Secure scanner for mod files with validation and categorization.

    Example:
        >>> scanner = ModScanner(max_file_size_mb=500)
        >>> results = scanner.scan_folder(Path("incoming"))
        >>> for category, mods in results.items():
        ...     print(f"{category}: {len(mods)} mods")
    """

    def __init__(
        self,
        max_file_size_mb: int = 500,
        scan_timeout_seconds: int = 30,
        min_entropy_threshold: float = 7.5,
    ) -> None:
        """Initialize mod scanner.

        Args:
            max_file_size_mb: Maximum allowed file size in MB
            scan_timeout_seconds: Timeout per file in seconds
            min_entropy_threshold: Entropy threshold for malware detection
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.scan_timeout = scan_timeout_seconds
        self.min_entropy_threshold = min_entropy_threshold
        self._scan_lock = threading.Lock()

    @timeout(30)  # 30-second timeout for entire folder scan
    def scan_folder(self, incoming_path: Path) -> dict[str, list[ModFile]]:
        """Scan folder for mod files with validation.

        Args:
            incoming_path: Path to folder containing mods to scan

        Returns:
            Dictionary mapping categories to lists of ModFile objects

        Raises:
            FileNotFoundError: If incoming_path doesn't exist
            NotADirectoryError: If incoming_path is not a directory
            TimeoutError: If scan exceeds 30 seconds
        """
        if not incoming_path.exists():
            raise FileNotFoundError(f"Incoming folder not found: {incoming_path}")

        if not incoming_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {incoming_path}")

        logger.info(f"Scanning folder: {incoming_path}")

        results: dict[str, list[ModFile]] = {
            "Core Scripts": [],
            "Libraries": [],
            "CC": [],  # Custom Content
            "Main Mods": [],
            "Invalid": [],
        }

        scanned_count = 0
        skipped_count = 0

        for file_path in incoming_path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:
                # Validate with timeout protection
                mod_file = self._scan_file_with_timeout(file_path)

                if mod_file.is_valid:
                    results[mod_file.category].append(mod_file)
                    scanned_count += 1
                else:
                    results["Invalid"].append(mod_file)
                    skipped_count += 1
                    logger.warning(
                        f"Invalid mod: {file_path.name} - "
                        f"{', '.join(mod_file.validation_errors)}"
                    )

            except Exception as e:
                logger.error(f"Error scanning {file_path.name}: {e}")
                skipped_count += 1
                # Create invalid entry
                results["Invalid"].append(
                    ModFile(
                        path=file_path,
                        size=0,
                        hash="",
                        mod_type="unknown",
                        category="Invalid",
                        is_valid=False,
                        validation_errors=[str(e)],
                    )
                )

        logger.info(f"Scan complete: {scanned_count} valid, {skipped_count} invalid/skipped")

        return results

    def _scan_file_with_timeout(self, path: Path) -> ModFile:
        """Scan single file with timeout protection.

        Args:
            path: Path to file

        Returns:
            ModFile object with validation results

        Raises:
            TimeoutError: If scan exceeds timeout
        """
        result: ModFile | None = None
        exception: Exception | None = None

        def scan_worker() -> None:
            nonlocal result, exception
            try:
                result = self._scan_file(path)
            except Exception as e:
                exception = e

        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()
        thread.join(timeout=self.scan_timeout)

        if thread.is_alive():
            logger.error(f"Scan timeout for {path.name}")
            raise SecurityError(
                "SCAN_TIMEOUT",
                path,
                severity="HIGH",
                details=f"Exceeded {self.scan_timeout}s timeout",
            )

        if exception:
            raise exception

        if result is None:
            raise ModScanError(path, "Scan returned no result")

        return result

    def _scan_file(self, path: Path) -> ModFile:
        """Scan and validate single mod file.

        Args:
            path: Path to file

        Returns:
            ModFile object with validation results
        """
        errors: list[str] = []

        # Get basic file info
        try:
            size = path.stat().st_size
        except (OSError, PermissionError) as e:
            raise ModScanError(path, f"Cannot access file: {e}") from e

        # Validate size
        if size > self.max_file_size_bytes:
            errors.append(
                f"File too large: {size / 1024 / 1024:.1f}MB "
                f"(max: {self.max_file_size_bytes / 1024 / 1024:.0f}MB)"
            )

        # Calculate hash
        hash_value = self._calculate_hash(path)

        # Validate file signature (raises SecurityError on failure)
        try:
            self.verify_signature(path)
        except SecurityError:
            # Security errors are fatal - re-raise immediately
            raise

        # Calculate entropy (raises SecurityError if >7.5)
        try:
            entropy = self.calculate_entropy(path)
        except SecurityError:
            # Security errors are fatal - re-raise immediately
            raise

        # Determine mod type
        mod_type = self._determine_mod_type(path)

        # Categorize
        category = self._categorize_mod(path, size, mod_type)

        is_valid = len(errors) == 0

        return ModFile(
            path=path,
            size=size,
            hash=hash_value,
            mod_type=mod_type,
            category=category,
            is_valid=is_valid,
            validation_errors=errors,
            entropy=entropy,
        )

    def _calculate_hash(self, path: Path) -> str:
        """Calculate CRC32 hash of file.

        Args:
            path: Path to file

        Returns:
            CRC32 hash as hex string
        """
        try:
            with open(path, "rb") as f:
                data = f.read()
                crc = zlib.crc32(data)
                return f"{crc:08X}"
        except Exception as e:
            logger.warning(f"Hash calculation failed for {path.name}: {e}")
            return "00000000"

    def calculate_entropy(self, path: Path) -> float:
        """Calculate Shannon entropy of file (malware detection).

        High entropy (>7.5) suggests encryption/packing, potential malware.

        Args:
            path: Path to file

        Returns:
            Entropy value (0.0-8.0)
        """
        try:
            with open(path, "rb") as f:
                # Read first 8KB for analysis (performance)
                data = f.read(8192)

            if not data:
                return 0.0

            # Calculate byte frequency
            frequency = [0] * 256
            for byte in data:
                frequency[byte] += 1

            # Calculate Shannon entropy
            entropy = 0.0
            data_len = len(data)

            for count in frequency:
                if count == 0:
                    continue
                probability = count / data_len
                entropy -= probability * math.log2(probability)

            # ENFORCE: Block files with suspiciously high entropy (>7.5)
            if entropy > 7.5:
                raise SecurityError(
                    message=f"File entropy too high ({entropy:.2f} > 7.5)",
                    file_path=path,
                    reason=f"Entropy {entropy:.2f} suggests encryption/packing (malware indicator)",
                    recovery_hint="File may be packed or malicious. Manual review required.",
                )

            return entropy

        except SecurityError:
            # Re-raise security errors
            raise
        except Exception as e:
            logger.warning(f"Entropy calculation failed for {path.name}: {e}")
            return 0.0

    def verify_signature(self, path: Path) -> tuple[bool, str | None]:
        """Verify file signature (magic bytes) and Python syntax.

        Args:
            path: Path to file

        Returns:
            Tuple of (is_valid, error_message)
        """
        extension = path.suffix.lower()

        # Special case: Python files - validate syntax (no magic bytes)
        if extension == ".py":
            try:
                with open(path, encoding="utf-8") as f:
                    code = f.read()
                ast.parse(code)  # Parse without executing - safe validation
                return True, None
            except SyntaxError as e:
                raise SecurityError(
                    message=f"Invalid Python syntax: {e}",
                    file_path=path,
                    reason=f"Syntax error at line {e.lineno}: {e.msg}",
                    recovery_hint="Fix syntax errors or remove file",
                ) from e
            except UnicodeDecodeError as e:
                raise SecurityError(
                    message="File is not valid UTF-8 text",
                    file_path=path,
                    reason="File encoding not UTF-8",
                    recovery_hint="Convert file to UTF-8 encoding",
                ) from e
            except Exception as e:
                raise SecurityError(
                    message=f"Python validation failed: {e}",
                    file_path=path,
                    reason=str(e),
                    recovery_hint="Check file integrity",
                ) from e

        # Only validate types with known magic byte signatures
        if extension not in MAGIC_BYTES:
            return True, None

        try:
            with open(path, "rb") as f:
                header = f.read(4)

            expected = MAGIC_BYTES[extension]

            if not header.startswith(expected):
                # ENFORCE: Block files with invalid magic bytes
                raise SecurityError(
                    message=f"Invalid {extension} signature",
                    file_path=path,
                    reason=f"Expected {expected.hex()}, got {header.hex()}",
                    recovery_hint="File may be corrupted or renamed. Verify source.",
                )

            # Additional validation for specific types
            if extension == ".ts4script":
                # ENFORCE: Verify it's a valid ZIP file with Python content
                try:
                    with zipfile.ZipFile(path, "r") as zf:
                        # Check for Python files inside
                        has_py = any(name.endswith(".py") for name in zf.namelist())
                        if not has_py:
                            raise SecurityError(
                                message=".ts4script must contain Python files",
                                file_path=path,
                                reason="No .py files found in ZIP archive",
                                recovery_hint="Script mods require Python files inside .ts4script ZIP",
                            )
                except zipfile.BadZipFile as e:
                    raise SecurityError(
                        message=".ts4script is not a valid ZIP file",
                        file_path=path,
                        reason="ZIP header corrupted or invalid",
                        recovery_hint="Re-download the mod from trusted source",
                    ) from e

            return True, None

        except SecurityError:
            # Re-raise security errors (already have full context)
            raise
        except PermissionError as e:
            raise SecurityError(
                message="Permission denied",
                file_path=path,
                reason="Cannot read file (insufficient permissions)",
                recovery_hint="Run as administrator or change file permissions",
            ) from e
        except Exception as e:
            raise SecurityError(
                message=f"Signature verification failed: {e}",
                file_path=path,
                reason=str(e),
                recovery_hint="File may be corrupted. Verify integrity.",
            ) from e

    def _determine_mod_type(self, path: Path) -> str:
        """Determine mod type from extension.

        Args:
            path: Path to file

        Returns:
            Mod type classification
        """
        extension = path.suffix.lower()

        type_map = {
            ".package": "package",
            ".ts4script": "ts4script",
            ".py": "script",
            ".cfg": "config",
            ".bpi": "project",
        }

        return type_map.get(extension, "unknown")

    def _categorize_mod(self, path: Path, size: int, mod_type: str) -> str:
        """Categorize mod based on file characteristics.

        Args:
            path: Path to file
            size: File size in bytes
            mod_type: Mod type classification

        Returns:
            Category name for load order
        """
        name_lower = path.name.lower()
        path_lower = str(path).lower()

        # Core script mods (high priority)
        if mod_type in ["ts4script", "script"]:
            # Check for "script" in name or known core mods
            if any(keyword in name_lower for keyword in SCRIPT_KEYWORDS):
                return "Core Scripts"

            if any(keyword in name_lower for keyword in CORE_MOD_KEYWORDS):
                return "Core Scripts"

            # Python libraries
            if "lib" in name_lower or "util" in name_lower:
                return "Libraries"

            return "Core Scripts"  # Default for scripts

        # Custom Content (CC) detection
        if mod_type == "package":
            # Large files are likely CC (meshes/textures)
            if size > 10 * 1024 * 1024:  # >10MB
                return "CC"

            # CAS (Create-a-Sim) items
            if "cas" in path_lower or "create" in path_lower:
                return "CC"

            # Build/Buy mode items
            if any(kw in path_lower for kw in ["build", "buy", "furniture", "decor"]):
                return "CC"

            # Core gameplay mods
            if any(keyword in name_lower for keyword in CORE_MOD_KEYWORDS):
                return "Core Scripts"

        # Config files
        if mod_type == "config":
            return "Libraries"

        # Default category
        return "Main Mods"

    def validate_file(self, path: Path) -> tuple[bool, list[str]]:
        """Validate single file without full scan.

        Args:
            path: Path to file to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            mod_file = self._scan_file(path)
            return mod_file.is_valid, mod_file.validation_errors
        except Exception as e:
            return False, [str(e)]
