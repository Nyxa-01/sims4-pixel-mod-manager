"""Load order management with alphabetical slot-based sorting."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def format_load_order(category: str, slot: int) -> str:
    """Format load order prefix.

    Args:
        category: Category name (e.g., "ScriptMods", "CAS")
        slot: Slot number (1-999)

    Returns:
        Formatted prefix like "001_ScriptMods"

    Raises:
        ValueError: If slot is out of range
    """
    if not 1 <= slot <= 999:
        raise ValueError(f"Slot must be 1-999, got {slot}")

    return f"{slot:03d}_{category}"


def is_script_mod(path: Path) -> bool:
    """Check if mod is a script mod.

    Args:
        path: Mod file path

    Returns:
        True if .ts4script file
    """
    return path.suffix.lower() == ".ts4script"


def validate_script_placement(path: Path, mods_root: Path) -> bool:
    """Validate script mod is at root level.

    Args:
        path: Mod file path
        mods_root: Mods folder root path

    Returns:
        True if placement is valid
    """
    if is_script_mod(path):
        return path.parent == mods_root
    return True


class LoadOrderManager:
    """Manages alphabetical load order with slot-based categories."""

    # Default category slots
    DEFAULT_CATEGORIES = {
        "ScriptMods": 1,
        "CAS": 2,
        "BuildBuy": 3,
        "Gameplay": 4,
        "UI": 5,
        "Overrides": 999,
    }

    def __init__(self, mods_folder: Path) -> None:
        """Initialize load order manager.

        Args:
            mods_folder: Sims 4 Mods directory
        """
        self.mods_folder = mods_folder
        self.categories: dict[str, int] = self.DEFAULT_CATEGORIES.copy()

    def add_category(self, name: str, slot: int) -> None:
        """Add custom load order category.

        Args:
            name: Category name
            slot: Slot number (1-999)

        Raises:
            ValueError: If slot is already taken
        """
        if slot in self.categories.values():
            existing = [k for k, v in self.categories.items() if v == slot]
            raise ValueError(f"Slot {slot} already used by: {existing[0]}")

        self.categories[name] = slot
        logger.info(f"Added category: {name} (slot {slot})")

    def get_category_slot(self, category: str) -> Optional[int]:
        """Get slot number for category.

        Args:
            category: Category name

        Returns:
            Slot number, or None if not found
        """
        return self.categories.get(category)

    def assign_mod_category(self, mod_path: Path) -> tuple[str, int]:
        """Assign mod to appropriate category based on type.

        Args:
            mod_path: Mod file path

        Returns:
            Tuple of (category_name, slot_number)
        """
        if is_script_mod(mod_path):
            return ("ScriptMods", 1)

        # Default to Gameplay for .package files
        # TODO: Implement DBPF parsing to detect actual type
        return ("Gameplay", 4)

    def sort_mods_alphabetically(self, mods: list[Path]) -> list[Path]:
        """Sort mods alphabetically within their categories.

        Args:
            mods: List of mod file paths

        Returns:
            Sorted list of mod paths
        """
        # Group by category
        categorized: dict[str, list[Path]] = {}
        for mod in mods:
            category, _ = self.assign_mod_category(mod)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(mod)

        # Sort within each category
        sorted_mods = []
        for category in sorted(categorized.keys(), key=lambda c: self.categories.get(c, 999)):
            category_mods = sorted(categorized[category], key=lambda p: p.stem.lower())
            sorted_mods.extend(category_mods)

        return sorted_mods

    def generate_load_order_paths(self, mods: list[Path]) -> dict[Path, Path]:
        """Generate target paths with load order prefixes.

        Args:
            mods: List of source mod paths

        Returns:
            Dictionary mapping source paths to target paths
        """
        mapping: dict[Path, Path] = {}

        for mod in mods:
            category, slot = self.assign_mod_category(mod)

            if is_script_mod(mod):
                # Scripts go to root
                target = self.mods_folder / mod.name
            else:
                # Other mods go to category folder
                category_folder = self.mods_folder / format_load_order(category, slot)
                target = category_folder / mod.name

            mapping[mod] = target

        return mapping
