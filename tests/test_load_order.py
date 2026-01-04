"""Tests for load order manager."""

from pathlib import Path

import pytest

from src.core.load_order import (
    LoadOrderManager,
    format_load_order,
    is_script_mod,
    validate_script_placement,
)


class TestLoadOrderHelpers:
    """Test helper functions."""

    def test_format_load_order(self) -> None:
        """Test load order prefix formatting."""
        assert format_load_order("CAS", 1) == "001_CAS"
        assert format_load_order("BuildBuy", 42) == "042_BuildBuy"
        assert format_load_order("Overrides", 999) == "999_Overrides"

    def test_format_load_order_invalid_slot(self) -> None:
        """Test format_load_order raises ValueError for invalid slot."""
        with pytest.raises(ValueError, match="Slot must be 1-999"):
            format_load_order("Test", 0)

        with pytest.raises(ValueError, match="Slot must be 1-999"):
            format_load_order("Test", 1000)

    def test_is_script_mod(self, tmp_path: Path) -> None:
        """Test script mod detection."""
        script = tmp_path / "test.ts4script"
        package = tmp_path / "test.package"

        assert is_script_mod(script) is True
        assert is_script_mod(package) is False

    def test_validate_script_placement(self, temp_mods_dir: Path) -> None:
        """Test script placement validation."""
        # Script at root (valid)
        root_script = temp_mods_dir / "script.ts4script"
        assert validate_script_placement(root_script, temp_mods_dir) is True

        # Script in subfolder (invalid)
        subfolder = temp_mods_dir / "Scripts"
        subfolder.mkdir()
        nested_script = subfolder / "script.ts4script"
        assert validate_script_placement(nested_script, temp_mods_dir) is False

        # Package can be anywhere
        nested_package = subfolder / "mod.package"
        assert validate_script_placement(nested_package, temp_mods_dir) is True


class TestLoadOrderManager:
    """Test LoadOrderManager class."""

    def test_init(self, temp_mods_dir: Path) -> None:
        """Test manager initialization."""
        manager = LoadOrderManager(temp_mods_dir)
        assert manager.mods_folder == temp_mods_dir
        assert "ScriptMods" in manager.categories
        assert manager.categories["ScriptMods"] == 1

    def test_add_category(self, temp_mods_dir: Path) -> None:
        """Test adding custom category."""
        manager = LoadOrderManager(temp_mods_dir)
        manager.add_category("Custom", 50)

        assert manager.categories["Custom"] == 50
        assert manager.get_category_slot("Custom") == 50

    def test_add_category_duplicate_slot(self, temp_mods_dir: Path) -> None:
        """Test adding category with duplicate slot raises error."""
        manager = LoadOrderManager(temp_mods_dir)

        with pytest.raises(ValueError, match="Slot 1 already used"):
            manager.add_category("Duplicate", 1)  # ScriptMods uses slot 1

    def test_assign_mod_category_script(
        self,
        temp_mods_dir: Path,
        sample_script_mod: Path,
    ) -> None:
        """Test mod category assignment for script mod."""
        manager = LoadOrderManager(temp_mods_dir)
        category, slot = manager.assign_mod_category(sample_script_mod)

        assert category == "ScriptMods"
        assert slot == 1

    def test_assign_mod_category_package(
        self,
        temp_mods_dir: Path,
        sample_package_mod: Path,
    ) -> None:
        """Test mod category assignment for package mod."""
        manager = LoadOrderManager(temp_mods_dir)
        category, slot = manager.assign_mod_category(sample_package_mod)

        assert category == "Gameplay"  # Default for packages
        assert slot == 4

    def test_sort_mods_alphabetically(self, temp_mods_dir: Path) -> None:
        """Test alphabetical sorting within categories."""
        manager = LoadOrderManager(temp_mods_dir)

        # Create test mod paths
        mods = [
            temp_mods_dir / "zebra.package",
            temp_mods_dir / "alpha.package",
            temp_mods_dir / "beta.ts4script",
            temp_mods_dir / "charlie.package",
        ]

        sorted_mods = manager.sort_mods_alphabetically(mods)

        # Scripts should come first (slot 1), then packages (slot 4)
        assert sorted_mods[0].name == "beta.ts4script"
        # Packages should be alphabetical
        package_names = [m.stem for m in sorted_mods[1:]]
        assert package_names == ["alpha", "charlie", "zebra"]

    def test_generate_load_order_paths(self, temp_mods_dir: Path) -> None:
        """Test generating target paths with prefixes."""
        manager = LoadOrderManager(temp_mods_dir)

        mods = [
            temp_mods_dir / "script.ts4script",
            temp_mods_dir / "mod.package",
        ]

        mapping = manager.generate_load_order_paths(mods)

        # Script should go to root
        script_target = mapping[mods[0]]
        assert script_target == temp_mods_dir / "script.ts4script"

        # Package should go to category folder
        package_target = mapping[mods[1]]
        assert "004_Gameplay" in str(package_target)
        assert package_target.name == "mod.package"
