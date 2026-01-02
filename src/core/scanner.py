"""Mod detection and cataloging with hash validation."""

import logging
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported mod file extensions
MOD_EXTENSIONS = {".package", ".ts4script", ".bpi"}


class ModFile:
    """Represents a detected mod file with metadata."""

    def __init__(self, path: Path) -> None:
        """Initialize mod file.

        Args:
            path: Absolute path to mod file

        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If file is not a valid mod type
        """
        if not path.exists():
            raise FileNotFoundError(f"Mod file not found: {path}")

        if path.suffix.lower() not in MOD_EXTENSIONS:
            raise ValueError(f"Invalid mod file type: {path.suffix}")

        self.path = path
        self.name = path.stem
        self.extension = path.suffix.lower()
        self.size = path.stat().st_size
        self._hash: int | None = None

    @property
    def hash(self) -> int:
        """Get CRC32 hash of file contents."""
        if self._hash is None:
            self._hash = self._calculate_hash()
        return self._hash

    def _calculate_hash(self) -> int:
        """Calculate CRC32 hash of file.

        Returns:
            CRC32 hash as integer
        """
        with open(self.path, "rb") as f:
            return zlib.crc32(f.read())

    @property
    def mod_type(self) -> str:
        """Determine mod type from extension.

        Returns:
            "script" for .ts4script, "package" for .package, "project" for .bpi
        """
        type_map = {
            ".ts4script": "script",
            ".package": "package",
            ".bpi": "project",
        }
        return type_map.get(self.extension, "unknown")

    def __repr__(self) -> str:
        """String representation."""
        return f"ModFile(name='{self.name}', type={self.mod_type}, size={self.size})"


class ModScanner:
    """Scans directories for Sims 4 mod files."""

    def __init__(self, max_size_mb: int = 500) -> None:
        """Initialize scanner.

        Args:
            max_size_mb: Maximum allowed mod file size in megabytes
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def scan_directory(self, path: Path) -> dict[str, list[ModFile]]:
        """Scan directory for mod files.

        Args:
            path: Directory to scan

        Returns:
            Dictionary mapping mod types to lists of ModFile objects

        Raises:
            FileNotFoundError: If path doesn't exist
            NotADirectoryError: If path is not a directory
        """
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        mods: dict[str, list[ModFile]] = {
            "script": [],
            "package": [],
            "project": [],
        }

        logger.info(f"Scanning directory: {path}")

        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in MOD_EXTENSIONS:
                continue

            try:
                # Check size limit
                if file_path.stat().st_size > self.max_size_bytes:
                    logger.warning(
                        f"Skipping oversized mod: {file_path.name} "
                        f"({file_path.stat().st_size / 1024 / 1024:.1f}MB)"
                    )
                    continue

                mod = ModFile(file_path)
                mods[mod.mod_type].append(mod)
                logger.debug(f"Found mod: {mod}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        total = sum(len(mod_list) for mod_list in mods.values())
        logger.info(f"Scan complete: {total} mods found")

        return mods

    def validate_mod(self, mod: ModFile) -> bool:
        """Validate mod file integrity.

        Args:
            mod: ModFile to validate

        Returns:
            True if validation passes
        """
        if not mod.path.exists():
            logger.error(f"Mod file missing: {mod.path}")
            return False

        if mod.path.stat().st_size != mod.size:
            logger.error(f"Mod file size mismatch: {mod.path}")
            return False

        # Recalculate hash to verify
        current_hash = mod._calculate_hash()
        if current_hash != mod.hash:
            logger.error(f"Mod file hash mismatch: {mod.path}")
            return False

        return True
