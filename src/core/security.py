"""Security layer for path encryption, validation, and sandboxing."""

import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class PathEncryption:
    """Handles encryption/decryption of file paths in config."""

    def __init__(self, key_path: Optional[Path] = None) -> None:
        """Initialize encryption.

        Args:
            key_path: Path to encryption key file. If None, uses default location.
        """
        if key_path is None:
            key_path = self._get_default_key_path()

        self.key_path = key_path
        self._fernet: Optional[Fernet] = None

    def _get_default_key_path(self) -> Path:
        """Get platform-specific default key location.

        Returns:
            Path to .encryption.key file
        """
        if os.name == "nt":  # Windows
            base = Path(os.getenv("LOCALAPPDATA", ""))
        elif os.name == "posix":  # Mac/Linux
            import platform

            if platform.system() == "Darwin":
                base = Path.home() / "Library" / "Application Support"
            else:
                base = Path.home() / ".config"
        else:
            base = Path.home()

        config_dir = base / "Sims4ModManager"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / ".encryption.key"

    def _load_or_create_key(self) -> Fernet:
        """Load existing key or create new one.

        Returns:
            Fernet cipher instance
        """
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                key = f.read()
            logger.debug("Loaded existing encryption key")
        else:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            # Set restrictive permissions on Unix systems
            if os.name == "posix":
                os.chmod(self.key_path, 0o600)
            logger.info(f"Generated new encryption key: {self.key_path}")
            logger.warning("BACKUP YOUR ENCRYPTION KEY - stored at: %s", self.key_path)

        return Fernet(key)

    @property
    def fernet(self) -> Fernet:
        """Get Fernet cipher instance, initializing if needed."""
        if self._fernet is None:
            self._fernet = self._load_or_create_key()
        return self._fernet

    def encrypt_path(self, path: Path) -> str:
        """Encrypt file path.

        Args:
            path: Path to encrypt

        Returns:
            Base64-encoded encrypted path string
        """
        path_str = str(path.resolve())
        encrypted = self.fernet.encrypt(path_str.encode())
        return encrypted.decode()

    def decrypt_path(self, encrypted: str) -> Path:
        """Decrypt file path.

        Args:
            encrypted: Base64-encoded encrypted path

        Returns:
            Decrypted Path object

        Raises:
            ValueError: If decryption fails
        """
        try:
            decrypted = self.fernet.decrypt(encrypted.encode())
            return Path(decrypted.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid encrypted path") from e


def validate_path_security(path: Path, allowed_base: Optional[Path] = None) -> bool:
    """Validate path doesn't escape allowed directory.

    Args:
        path: Path to validate
        allowed_base: Base directory to restrict to (optional)

    Returns:
        True if path is safe
    """
    try:
        resolved = path.resolve()

        # Check for path traversal
        if ".." in str(path):
            logger.warning(f"Path traversal detected: {path}")
            return False

        # Check if within allowed base
        if allowed_base is not None:
            allowed_resolved = allowed_base.resolve()
            try:
                resolved.relative_to(allowed_resolved)
            except ValueError:
                logger.warning(f"Path outside allowed directory: {path}")
                return False

        return True

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename (max 255 chars)
    """
    # Remove path separators and dangerous characters
    dangerous = ["/", "\\", "..", "\x00", ":", "*", "?", '"', "<", ">", "|"]
    sanitized = filename
    for char in dangerous:
        sanitized = sanitized.replace(char, "_")

    # Limit length to 255 chars total
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        # Reserve space for extension
        max_name_len = 255 - len(ext)
        sanitized = name[:max_name_len] + ext

    return sanitized
