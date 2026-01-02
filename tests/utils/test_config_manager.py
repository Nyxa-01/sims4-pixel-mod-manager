"""Tests for configuration manager."""

import json
from pathlib import Path
from typing import Generator

import pytest

from src.core.exceptions import EncryptionError, PathError
from src.utils.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create temporary config directory and monkeypatch.

    Args:
        tmp_path: Pytest tmp_path fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Path to temporary config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Monkeypatch _get_config_dir to use temp directory
    def mock_get_config_dir(self: ConfigManager) -> Path:
        return config_dir

    monkeypatch.setattr(ConfigManager, "_get_config_dir", mock_get_config_dir)

    # Reset singleton
    ConfigManager._instance = None
    ConfigManager._initialized = False

    return config_dir


@pytest.fixture
def config_manager(temp_config_dir: Path) -> Generator[ConfigManager, None, None]:
    """Create ConfigManager instance for testing.

    Args:
        temp_config_dir: Temporary config directory

    Yields:
        ConfigManager instance
    """
    manager = ConfigManager.get_instance()
    yield manager

    # Cleanup singleton
    ConfigManager._instance = None
    ConfigManager._initialized = False


class TestConfigManager:
    """Test ConfigManager class."""

    def test_singleton_pattern(self, config_manager: ConfigManager) -> None:
        """Test singleton pattern enforcement."""
        instance1 = ConfigManager.get_instance()
        instance2 = ConfigManager.get_instance()

        assert instance1 is instance2
        assert instance1 is config_manager

    def test_init_creates_default_config(self, config_manager: ConfigManager) -> None:
        """Test initialization creates default configuration."""
        config = config_manager.load_config()

        assert config["max_mod_size_mb"] == 500
        assert config["backup_retention"] == 10
        assert config["deploy_method"] == "junction"
        assert config["theme"] == "dark"

    def test_encryption_key_generation(self, temp_config_dir: Path) -> None:
        """Test encryption key is generated on first run."""
        manager = ConfigManager.get_instance()
        key_path = manager.key_path

        assert key_path.exists()
        assert key_path.stat().st_size > 0

    def test_get_value(self, config_manager: ConfigManager) -> None:
        """Test getting configuration values."""
        assert config_manager.get("max_mod_size_mb") == 500
        assert config_manager.get("theme") == "dark"
        assert config_manager.get("nonexistent", "default") == "default"

    def test_set_value(self, config_manager: ConfigManager) -> None:
        """Test setting configuration values."""
        config_manager.set("max_mod_size_mb", 750)
        assert config_manager.get("max_mod_size_mb") == 750

        config_manager.set("theme", "light")
        assert config_manager.get("theme") == "light"

    def test_set_path_validation(
        self,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        """Test path validation when setting path values."""
        # Valid path (parent exists)
        valid_path = tmp_path / "mods"
        tmp_path.mkdir(exist_ok=True)
        config_manager.set("mods_path", str(valid_path))
        assert config_manager.get("mods_path") == str(valid_path)

        # Invalid path (parent doesn't exist)
        invalid_path = Path("/nonexistent/path/mods")
        with pytest.raises(PathError):
            config_manager.set("mods_path", str(invalid_path))

    def test_reset_to_defaults(self, config_manager: ConfigManager) -> None:
        """Test resetting configuration to defaults."""
        # Modify config
        config_manager.set("max_mod_size_mb", 1000)
        config_manager.set("theme", "light")

        # Reset
        config_manager.reset_to_defaults()

        # Check defaults restored
        assert config_manager.get("max_mod_size_mb") == 500
        assert config_manager.get("theme") == "dark"

    def test_validate_paths(
        self,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        """Test path validation."""
        # Create valid paths
        game_path = tmp_path / "game"
        mods_path = tmp_path / "mods"
        app_data = tmp_path / "appdata"

        game_path.mkdir()
        mods_path.mkdir()
        app_data.mkdir()

        config_manager.set("game_path", str(game_path))
        config_manager.set("mods_path", str(mods_path))
        config_manager.set("app_data_path", str(app_data))

        assert config_manager.validate_paths() is True

        # Invalid path
        config_manager.set("game_path", "/nonexistent")
        assert config_manager.validate_paths() is False

    def test_config_persistence(
        self,
        temp_config_dir: Path,
        config_manager: ConfigManager,
    ) -> None:
        """Test configuration persists across instances."""
        # Set values
        config_manager.set("max_mod_size_mb", 600)
        config_manager.set("theme", "light")

        # Reset singleton and create new instance
        ConfigManager._instance = None
        ConfigManager._initialized = False

        new_manager = ConfigManager.get_instance()

        # Check values persisted
        assert new_manager.get("max_mod_size_mb") == 600
        assert new_manager.get("theme") == "light"

    def test_transaction_context_success(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test transaction context commits on success."""
        with config_manager:
            config_manager.set("max_mod_size_mb", 700)
            config_manager.set("theme", "light")

        # Changes should be saved
        assert config_manager.get("max_mod_size_mb") == 700
        assert config_manager.get("theme") == "light"

    def test_transaction_context_rollback(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test transaction context rolls back on exception."""
        original_size = config_manager.get("max_mod_size_mb")

        try:
            with config_manager:
                config_manager.set("max_mod_size_mb", 999)
                raise ValueError("Test error")
        except ValueError:
            pass

        # Changes should be rolled back
        assert config_manager.get("max_mod_size_mb") == original_size

    def test_corrupted_config_fallback(
        self,
        temp_config_dir: Path,
        config_manager: ConfigManager,
    ) -> None:
        """Test fallback to defaults on corrupted config."""
        # Corrupt the config file
        config_path = config_manager.config_path
        with open(config_path, "w") as f:
            f.write("{ invalid json }")

        # Reset and reload
        ConfigManager._instance = None
        ConfigManager._initialized = False

        new_manager = ConfigManager.get_instance()

        # Should fallback to defaults
        assert new_manager.get("max_mod_size_mb") == 500

    def test_path_encryption(
        self,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        """Test paths are encrypted in saved config file."""
        test_path = tmp_path / "test"
        test_path.mkdir()

        config_manager.set("mods_path", str(test_path))

        # Read raw config file
        with open(config_manager.config_path, "r") as f:
            raw_config = json.load(f)

        # Path should be encrypted (not plain text)
        assert str(test_path) not in raw_config["mods_path"]
        assert len(raw_config["mods_path"]) > len(str(test_path))

        # But decrypted value should match
        assert config_manager.get("mods_path") == str(test_path)
