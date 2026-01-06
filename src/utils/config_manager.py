"""Encrypted configuration manager with secure path storage.

This module provides a singleton ConfigManager that handles:
- Fernet encryption for sensitive paths
- Atomic file writes for data integrity
- Graceful fallback to defaults on corruption
- Platform-aware default paths
"""

import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Literal, Optional

from cryptography.fernet import Fernet, InvalidToken

from ..core.exceptions import EncryptionError, PathError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Singleton configuration manager with encrypted storage.

    Manages application configuration with Fernet encryption for sensitive
    paths, atomic writes for data integrity, and automatic validation.

    Example:
        >>> config = ConfigManager.get_instance()
        >>> game_path = config.get("game_path")
        >>> config.set("max_mod_size_mb", 750)
        >>> with config:
        ...     config.set("theme", "light")
        ...     config.set("backup_retention", 5)
    """

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False
    _lock: Any = None  # Will be initialized as threading.Lock

    # Default configuration structure
    DEFAULT_CONFIG = {
        "game_path": "",  # Will be auto-detected or user-configured
        "mods_path": "",  # Will be auto-detected or user-configured
        "app_data_path": "",  # Platform-specific, set on init
        "max_mod_size_mb": 500,
        "backup_retention": 10,
        "deploy_method": "junction",  # junction|symlink|copy
        "theme": "dark",
        "check_updates": True,
        "log_level": "INFO",
    }

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize configuration manager (private - use get_instance() instead).

        Args:
            config_dir: Optional custom config directory (for testing)
        """
        # Allow re-initialization only during get_instance() call
        # Check if this is being called directly (not from get_instance)
        # by checking if _instance is None

        self.config_dir = config_dir if config_dir is not None else self._get_config_dir()
        self.config_path = self.config_dir / "config.json"
        self.key_path = self.config_dir / ".encryption.key"
        self.log_path = self.config_dir / "logs" / "config.log"

        # Setup logging
        self._setup_logging()

        # Load or generate encryption key
        self._fernet: Optional[Fernet] = None
        self._load_encryption_key()

        # Current config state
        self._config: dict[str, Any] = {}
        self._in_transaction = False
        self._transaction_backup: Optional[dict[str, Any]] = None

        # Load configuration
        self._load_or_create_config()

        ConfigManager._initialized = True

    @classmethod
    def get_instance(cls, config_dir: Optional[Path] = None) -> "ConfigManager":
        """Get singleton instance (thread-safe).

        Args:
            config_dir: Config directory (only used on first call)

        Returns:
            ConfigManager singleton instance
        """
        if cls._lock is None:
            import threading

            cls._lock = threading.Lock()

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = cls.__new__(cls)
                    cls._instance.__init__(config_dir)  # type: ignore[misc]
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        if cls._lock is None:
            import threading

            cls._lock = threading.Lock()

        with cls._lock:
            cls._instance = None
            cls._initialized = False

    def _get_config_dir(self) -> Path:
        """Get platform-specific configuration directory.

        Returns:
            Path to config directory
        """
        system = platform.system()

        if system == "Windows":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        elif system == "Darwin":  # macOS
            base = Path.home() / "Library" / "Application Support"
        else:  # Linux
            base = Path.home() / ".config"

        config_dir = base / "Sims4ModManager"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _setup_logging(self) -> None:
        """Configure logging for config changes."""
        log_dir = self.config_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(self.log_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        config_logger = logging.getLogger("config")
        config_logger.addHandler(file_handler)
        config_logger.setLevel(logging.INFO)

    def _load_encryption_key(self) -> None:
        """Load or generate Fernet encryption key."""
        if self.key_path.exists():
            try:
                with open(self.key_path, "rb") as f:
                    key = f.read()
                self._fernet = Fernet(key)
                logger.debug("Loaded existing encryption key")
            except Exception as e:
                logger.error(f"Failed to load encryption key: {e}")
                raise EncryptionError("decrypt", self.key_path, str(e))
        else:
            # Generate new key
            key = Fernet.generate_key()
            try:
                with open(self.key_path, "wb") as f:
                    f.write(key)

                # Set restrictive permissions on Unix systems
                if platform.system() != "Windows":
                    os.chmod(self.key_path, 0o600)

                self._fernet = Fernet(key)
                logger.warning(
                    f"Generated new encryption key: {self.key_path}\n"
                    "IMPORTANT: Backup this file to prevent data loss!"
                )
            except Exception as e:
                logger.error(f"Failed to create encryption key: {e}")
                raise EncryptionError("encrypt", self.key_path, str(e))

    def _encrypt_path(self, path: str) -> str:
        """Encrypt a path string.

        Args:
            path: Path string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if self._fernet is None:
            raise EncryptionError("encrypt", reason="Fernet not initialized")

        try:
            encrypted = self._fernet.encrypt(path.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Path encryption failed: {e}")
            raise EncryptionError("encrypt", reason=str(e))

    def _decrypt_path(self, encrypted: str) -> str:
        """Decrypt an encrypted path string.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted path string
        """
        if self._fernet is None:
            raise EncryptionError("decrypt", reason="Fernet not initialized")

        try:
            decrypted = self._fernet.decrypt(encrypted.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Invalid encryption token (corrupted or wrong key)")
            raise EncryptionError("decrypt", reason="Invalid token")
        except Exception as e:
            logger.error(f"Path decryption failed: {e}")
            raise EncryptionError("decrypt", reason=str(e))

    def _load_or_create_config(self) -> None:
        """Load existing config or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    raw_config = json.load(f)

                # Decrypt paths
                self._config = self._decrypt_config(raw_config)
                logger.info("Loaded configuration")

            except json.JSONDecodeError as e:
                logger.error(f"Config JSON corrupted: {e}, using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
                self._set_default_paths()
                self._save_config()

            except (EncryptionError, InvalidToken) as e:
                logger.error(f"Config decryption failed: {e}, using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
                self._set_default_paths()
                self._save_config()

        else:
            logger.info("No config found, creating defaults")
            self._config = self.DEFAULT_CONFIG.copy()
            self._set_default_paths()
            self._save_config()

    def _set_default_paths(self) -> None:
        """Set platform-specific default paths."""
        if platform.system() == "Windows":
            docs = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"
            self._config["game_path"] = str(docs)
            self._config["mods_path"] = str(docs / "Mods")
        else:
            # Mac/Linux defaults
            self._config["game_path"] = ""
            self._config["mods_path"] = ""

        self._config["app_data_path"] = str(self.config_dir)

    def _decrypt_config(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        """Decrypt path values in config.

        Args:
            raw_config: Raw config with encrypted paths

        Returns:
            Config with decrypted paths
        """
        decrypted = raw_config.copy()
        path_keys = ["game_path", "mods_path", "app_data_path"]

        for key in path_keys:
            if key in decrypted and decrypted[key]:
                try:
                    decrypted[key] = self._decrypt_path(decrypted[key])
                except EncryptionError:
                    logger.warning(f"Failed to decrypt {key}, using empty")
                    decrypted[key] = ""

        return decrypted

    def _encrypt_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Encrypt path values in config.

        Args:
            config: Config with plain paths

        Returns:
            Config with encrypted paths
        """
        encrypted = config.copy()
        path_keys = ["game_path", "mods_path", "app_data_path"]

        for key in path_keys:
            if key in encrypted and encrypted[key]:
                try:
                    encrypted[key] = self._encrypt_path(encrypted[key])
                except EncryptionError:
                    logger.error(f"Failed to encrypt {key}")
                    raise

        return encrypted

    def _save_config(self) -> None:
        """Save configuration with atomic write."""
        try:
            # Encrypt paths
            encrypted_config = self._encrypt_config(self._config)

            # Atomic write: write to temp file first
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(encrypted_config, f, indent=2)

            # Rename to actual config (atomic on most systems)
            temp_path.replace(self.config_path)

            logging.getLogger("config").info("Configuration saved")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_config(self) -> dict[str, Any]:
        """Load and return current configuration.

        Returns:
            Configuration dictionary with decrypted paths
        """
        return self._config.copy()

    def save_config(self, config: dict[str, Any]) -> None:
        """Save configuration.

        Args:
            config: Configuration dictionary to save
        """
        self._config = config.copy()
        self._save_config()
        logging.getLogger("config").info("Configuration updated")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            PathError: If path validation fails for path keys
        """
        # Validate paths
        if key in ["game_path", "mods_path", "app_data_path"]:
            if value and not Path(value).parent.exists():
                raise PathError(
                    message=f"Parent directory does not exist for {key}",
                    path=Path(value),
                    path_type=key,
                    reason="Parent directory does not exist",
                )

        self._config[key] = value

        # Auto-save unless in transaction
        if not self._in_transaction:
            self._save_config()
            logging.getLogger("config").info(f"Set {key}={value}")

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        logger.warning("Resetting configuration to defaults")
        self._config = self.DEFAULT_CONFIG.copy()
        self._set_default_paths()
        self._save_config()
        logging.getLogger("config").info("Configuration reset to defaults")

    def validate_paths(self) -> bool:
        """Validate that configured paths exist.

        Returns:
            True if all paths are valid
        """
        path_keys = ["game_path", "mods_path", "app_data_path"]

        for key in path_keys:
            path_str = self._config.get(key)
            if not path_str:
                logger.warning(f"{key} is not configured")
                return False

            path = Path(path_str)
            if not path.exists():
                logger.warning(f"{key} does not exist: {path}")
                return False

        return True

    # Context manager support for transactional updates
    def __enter__(self) -> "ConfigManager":
        """Enter transaction context."""
        self._in_transaction = True
        self._transaction_backup = self._config.copy()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> Literal[False]:
        """Exit transaction context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        Returns:
            False to propagate exceptions
        """
        self._in_transaction = False

        if exc_type is None:
            # Success: save changes
            self._save_config()
            logging.getLogger("config").info("Transaction committed")
        else:
            # Failure: rollback
            logger.warning(f"Transaction rolled back due to {exc_type.__name__}")
            self._config = self._transaction_backup or {}

        self._transaction_backup = None
        return False  # Don't suppress exceptions
