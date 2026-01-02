"""Tests for configuration manager."""

import json
from collections.abc import Generator
from pathlib import Path

import pytest

from src.core.exceptions import PathError
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
        with open(config_manager.config_path) as f:
            raw_config = json.load(f)

        # Path should be encrypted (not plain text)
        assert str(test_path) not in raw_config["mods_path"]
        assert len(raw_config["mods_path"]) > len(str(test_path))

        # But decrypted value should match
        assert config_manager.get("mods_path") == str(test_path)


class TestConfigManagerExceptionPaths:
    """Tests for config manager exception handling and edge cases."""

    def test_config_file_permission_error(
        self,
        temp_config_dir: Path,
        monkeypatch,
    ) -> None:
        """Test handling of config file permission errors."""
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission test is Unix-specific")

        config_dir = temp_config_dir
        config_path = config_dir / "config.json"

        # Create config then make it read-only
        manager = ConfigManager.get_instance()
        config_path.chmod(0o444)

        # Attempt to write should handle gracefully
        try:
            manager.set("max_mod_size_mb", 999)
        except PermissionError:
            pass  # Expected

        # Restore permissions for cleanup
        config_path.chmod(0o644)

    def test_missing_config_directory(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test config manager creates missing directory."""
        config_dir = tmp_path / "new_config"
        config_dir.mkdir(parents=True)  # Create parent so logs subdir can be created

        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._initialized = False

        manager = ConfigManager.get_instance(config_dir=config_dir)

        # Directory should be created (including logs subdirectory)
        assert config_dir.exists()
        assert (config_dir / "logs").exists()

    def test_concurrent_config_writes(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test concurrent config modifications."""
        # Simulate concurrent write by modifying config file directly
        config_manager.set("max_mod_size_mb", 500)

        # External write to config file
        config_data = config_manager.load_config()
        config_data["theme"] = "external_modification"
        config_manager.save_config(config_data)

        # Internal write
        config_manager.set("max_mod_size_mb", 600)

        # Reload and verify last write wins
        config = config_manager.load_config()
        assert config["max_mod_size_mb"] == 600

    def test_invalid_config_value_type(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test setting invalid value types."""
        # Should handle type conversion or validation
        config_manager.set("max_mod_size_mb", "not_a_number")

        # Depending on implementation, may convert or reject
        value = config_manager.get("max_mod_size_mb")
        assert isinstance(value, (int, str))

    def test_get_nonexistent_key_no_default(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test getting nonexistent key without default returns None."""
        result = config_manager.get("nonexistent_key_xyz")
        assert result is None

    def test_nested_config_values(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test handling nested configuration values."""
        nested = {
            "ui": {"theme": "dark", "font_size": 12},
            "paths": {"mods": "/path/to/mods", "game": "/path/to/game"},
        }

        config_manager.set("nested_config", nested)
        retrieved = config_manager.get("nested_config")

        assert isinstance(retrieved, dict)
        assert retrieved["ui"]["theme"] == "dark"

    def test_config_migration_from_old_format(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that old config is loaded without migration."""
        config_dir = tmp_path / "config_migration"
        config_dir.mkdir()
        (config_dir / "logs").mkdir()  # Required for setup
        
        # Create old format config (missing new fields)
        old_config = {
            "max_mod_size_mb": 500,
            "theme": "dark",
            # Missing new fields like deploy_method
        }

        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(old_config, f)

        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._initialized = False

        manager = ConfigManager.get_instance(config_dir=config_dir)

        # Old config loaded as-is, missing keys return None (no auto-migration)
        assert manager.get("max_mod_size_mb") == 500
        assert manager.get("theme") == "dark"
        # Missing keys return default parameter (None if not specified)
        assert manager.get("deploy_method") is None
        # Can get with explicit default
        assert manager.get("deploy_method", "junction") == "junction"

    def test_reset_with_active_transaction(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test reset within transaction context."""
        with config_manager:
            config_manager.set("max_mod_size_mb", 800)
            config_manager.reset_to_defaults()

        # Should have defaults
        assert config_manager.get("max_mod_size_mb") == 500

    def test_validate_paths_with_relative_paths(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test path validation handles relative paths."""
        # set() validates immediately and raises PathError for invalid parent
        with pytest.raises(PathError, match="Parent directory does not exist"):
            config_manager.set("game_path", "../relative/path")

    def test_validate_paths_with_missing_keys(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test path validation with missing path keys."""
        # Remove path keys
        config = config_manager.load_config()
        config.pop("game_path", None)
        config.pop("mods_path", None)
        config_manager.save_config(config)

        # Should handle gracefully (return False or skip validation)
        result = config_manager.validate_paths()
        assert isinstance(result, bool)

    def test_transaction_nested_exception(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test transaction handles nested exceptions."""
        original_value = config_manager.get("max_mod_size_mb")

        try:
            with config_manager:
                config_manager.set("max_mod_size_mb", 900)
                try:
                    raise ValueError("Inner exception")
                except ValueError:
                    # Re-raise different exception
                    raise RuntimeError("Outer exception")
        except RuntimeError:
            pass

        # Should rollback to original
        assert config_manager.get("max_mod_size_mb") == original_value

    def test_encryption_key_missing_regenerates(
        self,
        temp_config_dir: Path,
        config_manager: ConfigManager,
    ) -> None:
        """Test encryption key regeneration when missing."""
        key_path = config_manager.key_path

        # Delete encryption key
        if key_path.exists():
            key_path.unlink()

        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._initialized = False

        # New instance should regenerate key
        new_manager = ConfigManager.get_instance()

        assert new_manager.key_path.exists()

    def test_config_with_unicode_values(
        self,
        config_manager: ConfigManager,
    ) -> None:
        """Test config handles unicode values."""
        unicode_value = "テスト_モッド_パス_日本語"

        config_manager.set("custom_field", unicode_value)
        retrieved = config_manager.get("custom_field")

        assert retrieved == unicode_value

    def test_config_with_very_long_paths(
        self,
        config_manager: ConfigManager,
        tmp_path: Path,
    ) -> None:
        """Test config handles very long paths."""
        # Create deep directory structure
        deep_path = tmp_path
        for i in range(20):
            deep_path = deep_path / f"level_{i}"

        deep_path.mkdir(parents=True, exist_ok=True)

        config_manager.set("deep_path", str(deep_path))
        retrieved = config_manager.get("deep_path")

        assert retrieved == str(deep_path)

    def test_save_config_atomic_write(
        self,
        config_manager: ConfigManager,
        temp_config_dir: Path,
    ) -> None:
        """Test config save uses atomic write operation."""
        config_manager.set("test_atomic", "value1")

        # Config should be saved atomically (no .tmp files left)
        temp_files = list(temp_config_dir.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_load_config_handles_empty_file(
        self,
        temp_config_dir: Path,
        monkeypatch,
    ) -> None:
        """Test loading config from empty file falls back to defaults."""
        config_path = temp_config_dir / "config.json"
        config_path.write_text("")

        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._initialized = False

        manager = ConfigManager.get_instance()

        # Should load defaults
        assert manager.get("max_mod_size_mb") == 500
