"""Intelligent load order management with slot-based organization.

This module provides alphabetical load order enforcement through folder
prefixes, automatic categorization, and validation of file placement rules.
"""

import logging
import re
from pathlib import Path

from src.core.exceptions import LoadOrderError, PathError
from src.core.mod_scanner import ModFile

logger = logging.getLogger(__name__)

# Fixed load order slots (immutable)
LOAD_ORDER_SLOTS = [
    ("000_Core", "Core Scripts/Frameworks", ["mccc", "ui_cheats", "wickedwhims"]),
    ("010_Libraries", "Shared Dependencies", ["library", "lib_", "framework"]),
    ("020_MainMods", "Gameplay Overhauls", []),
    ("030_Tuning", "XML Tuning Mods", ["tuning", "xml"]),
    ("040_CC", "Custom Content", ["cas", "hair", "clothes", "skin"]),
    ("ZZZ_Overrides", "Override Mods (Load Last)", ["override", "override_"]),
]

# Prefix validation regex
PREFIX_PATTERN = re.compile(r"^\d{3}_\w+$")

# Windows MAX_PATH limit
MAX_PATH_LENGTH = 260

# Script file extensions (must be in root)
SCRIPT_EXTENSIONS = {".py", ".ts4script"}

# Maximum nesting depth for packages
MAX_PACKAGE_DEPTH = 5


class LoadOrderEngine:
    """Intelligent load order manager with automatic categorization.

    Example:
        >>> engine = LoadOrderEngine()
        >>> structure = engine.generate_structure(
        ...     mods={"Core Scripts": [mod1, mod2], "CC": [mod3]},
        ...     output=Path("ActiveMods")
        ... )
    """

    def __init__(self) -> None:
        """Initialize load order engine."""
        self.slots = LOAD_ORDER_SLOTS

    def generate_structure(
        self,
        mods: dict[str, list[ModFile]],
        output: Path,
    ) -> dict[str, Path]:
        """Generate organized folder structure with load order prefixes.

        Args:
            mods: Dictionary mapping categories to mod lists
            output: Output directory (ActiveMods folder)

        Returns:
            Dictionary mapping slot prefixes to created paths

        Raises:
            LoadOrderError: On structure generation failure
        """
        logger.info(f"Generating load order structure in {output}")

        try:
            output.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise LoadOrderError(
                f"Failed to create output directory: {e}",
                recovery_hint="Check permissions and disk space",
            ) from e

        created_paths: dict[str, Path] = {}

        # Create slot folders
        for prefix, description, _ in self.slots:
            slot_path = output / prefix
            try:
                slot_path.mkdir(exist_ok=True)
                created_paths[prefix] = slot_path
                logger.debug(f"Created slot: {prefix} ({description})")
            except Exception as e:
                logger.error(f"Failed to create slot {prefix}: {e}")
                raise LoadOrderError(f"Failed to create slot folder: {prefix}") from e

        # Place mods in appropriate slots
        for category, mod_list in mods.items():
            for mod in mod_list:
                try:
                    self._place_mod_file(mod, output)
                except Exception as e:
                    logger.error(f"Failed to place mod {mod.path.name}: {e}")
                    raise LoadOrderError(
                        f"Failed to place mod: {mod.path.name}",
                        recovery_hint="Check mod file integrity",
                    ) from e

        logger.info(f"Structure generated with {len(mods)} categories")
        return created_paths

    def assign_mod_to_slot(self, mod: ModFile) -> str:
        """Automatically assign mod to appropriate load order slot.

        Uses keyword matching and file characteristics to categorize.

        Args:
            mod: Mod file to categorize

        Returns:
            Slot prefix (e.g., "000_Core", "040_CC")
        """
        mod_name = mod.path.name.lower()
        mod_category = mod.category.lower() if mod.category else ""

        # Check each slot's keywords
        for prefix, description, keywords in self.slots:
            # Skip ZZZ_Overrides (only for explicit overrides)
            if prefix == "ZZZ_Overrides":
                continue

            # Match against keywords
            if any(keyword in mod_name for keyword in keywords):
                logger.debug(f"Assigned {mod.path.name} to {prefix} (keyword match)")
                return prefix

            # Match category
            if any(keyword in mod_category for keyword in keywords):
                logger.debug(f"Assigned {mod.path.name} to {prefix} (category match)")
                return prefix

        # Special cases
        if mod.mod_type == "ts4script" or mod.path.suffix == ".py":
            return "000_Core"  # Scripts are core functionality

        if mod.size > 10_000_000:  # >10MB likely CC
            return "040_CC"

        if "cas" in str(mod.path).lower():
            return "040_CC"

        # Default to MainMods
        logger.debug(f"Assigned {mod.path.name} to 020_MainMods (default)")
        return "020_MainMods"

    def _place_mod_file(self, mod: ModFile, output: Path) -> Path:
        """Place mod file in appropriate slot folder.

        Args:
            mod: Mod file to place
            output: Output directory (ActiveMods)

        Returns:
            Path where mod was placed

        Raises:
            PathError: On invalid placement
        """
        slot = self.assign_mod_to_slot(mod)
        slot_path = output / slot

        # Script files MUST go in root ActiveMods
        if mod.path.suffix in SCRIPT_EXTENSIONS:
            target = output / mod.path.name
            logger.debug(f"Placing script in root: {mod.path.name}")
        else:
            # Package files go in slot folder
            target = slot_path / mod.path.name
            logger.debug(f"Placing package in {slot}: {mod.path.name}")

        # Check path length
        if len(str(target)) > MAX_PATH_LENGTH:
            raise PathError(
                f"Path exceeds Windows limit ({MAX_PATH_LENGTH} chars): {target}",
                recovery_hint="Use shorter mod names or reduce nesting",
            )

        return target

    def move_mod(
        self,
        mod: ModFile,
        from_slot: str,
        to_slot: str,
        base_path: Path,
    ) -> bool:
        """Move mod from one slot to another.

        Args:
            mod: Mod file to move
            from_slot: Source slot prefix
            to_slot: Destination slot prefix
            base_path: Base ActiveMods path

        Returns:
            True if moved successfully

        Raises:
            LoadOrderError: On move failure
        """
        # Validate slots
        valid_slots = [prefix for prefix, _, _ in self.slots]
        if from_slot not in valid_slots or to_slot not in valid_slots:
            raise LoadOrderError(
                f"Invalid slot: {from_slot} or {to_slot}",
                recovery_hint=f"Valid slots: {', '.join(valid_slots)}",
            )

        # Scripts cannot be moved (always root)
        if mod.path.suffix in SCRIPT_EXTENSIONS:
            raise LoadOrderError(
                "Script files must remain in root ActiveMods",
                recovery_hint="Only .package files can be moved between slots",
            )

        source = base_path / from_slot / mod.path.name
        target = base_path / to_slot / mod.path.name

        if not source.exists():
            raise LoadOrderError(
                f"Source mod not found: {source}",
                recovery_hint="Mod may have already been moved",
            )

        try:
            # Move file
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            logger.info(f"Moved {mod.path.name}: {from_slot} → {to_slot}")
            return True

        except Exception as e:
            raise LoadOrderError(
                f"Failed to move mod: {e}",
                recovery_hint="Check file permissions and disk space",
            ) from e

    def validate_structure(self, path: Path) -> tuple[bool, list[str]]:
        """Validate load order structure and file placement.

        Args:
            path: Path to ActiveMods folder

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings: list[str] = []

        if not path.exists():
            return False, ["ActiveMods path does not exist"]

        # Check for required slots
        valid_slots = [prefix for prefix, _, _ in self.slots]
        for prefix in valid_slots:
            slot_path = path / prefix
            if not slot_path.exists():
                warnings.append(f"Missing slot folder: {prefix}")

        # Validate script placement (must be in root)
        nested_scripts = self._find_nested_scripts(path)
        if nested_scripts:
            for script in nested_scripts:
                warnings.append(f"Script file nested (must be in root): {script.relative_to(path)}")

        # Check path lengths
        for file_path in path.rglob("*"):
            if file_path.is_file():
                if len(str(file_path)) > MAX_PATH_LENGTH:
                    warnings.append(f"Path exceeds Windows limit: {file_path.relative_to(path)}")

        # Check package nesting depth
        for file_path in path.rglob("*.package"):
            depth = len(file_path.relative_to(path).parts) - 1  # Exclude filename
            if depth > MAX_PACKAGE_DEPTH:
                warnings.append(
                    f"Package nested too deep ({depth} levels): " f"{file_path.relative_to(path)}"
                )

        # Validate prefix format
        for item in path.iterdir():
            if item.is_dir() and not PREFIX_PATTERN.match(item.name):
                # Skip if it's a script file directory or special folder
                if item.name not in ["__pycache__", ".git"]:
                    warnings.append(f"Invalid prefix format: {item.name}")

        is_valid = len(warnings) == 0
        return is_valid, warnings

    def _find_nested_scripts(self, path: Path) -> list[Path]:
        """Find script files that are nested in subdirectories.

        Args:
            path: ActiveMods root path

        Returns:
            List of nested script paths
        """
        nested: list[Path] = []

        for ext in SCRIPT_EXTENSIONS:
            for script in path.rglob(f"*{ext}"):
                # Check if script is not in root
                if script.parent != path:
                    nested.append(script)

        return nested

    def get_load_order(self, path: Path) -> list[str]:
        """Get alphabetically sorted load order list.

        Args:
            path: ActiveMods folder path

        Returns:
            List of mod names in load order
        """
        if not path.exists():
            return []

        load_order: list[str] = []

        # Get all slot folders in alphabetical order
        slot_folders = sorted(
            [d for d in path.iterdir() if d.is_dir() and PREFIX_PATTERN.match(d.name)]
        )

        # Scripts in root (load first)
        for ext in SCRIPT_EXTENSIONS:
            for script in path.glob(f"*{ext}"):
                load_order.append(script.name)

        # Then slot folders
        for slot_folder in slot_folders:
            # Add all mods in slot (alphabetically)
            for mod_file in sorted(slot_folder.rglob("*.package")):
                rel_path = mod_file.relative_to(path)
                load_order.append(str(rel_path))

        logger.debug(f"Load order contains {len(load_order)} items")
        return load_order

    def validate_prefix(self, prefix: str) -> bool:
        """Validate slot prefix format.

        Args:
            prefix: Prefix to validate (e.g., "000_Core")

        Returns:
            True if valid format
        """
        return PREFIX_PATTERN.match(prefix) is not None

    def get_slot_description(self, prefix: str) -> str | None:
        """Get description for a slot prefix.

        Args:
            prefix: Slot prefix

        Returns:
            Description string, or None if not found
        """
        for slot_prefix, description, _ in self.slots:
            if slot_prefix == prefix:
                return description
        return None

    def reorganize_slot(
        self,
        slot: str,
        path: Path,
        sort_alphabetically: bool = True,
    ) -> bool:
        """Reorganize mods within a slot.

        Args:
            slot: Slot prefix to reorganize
            path: ActiveMods base path
            sort_alphabetically: Whether to sort mods alphabetically

        Returns:
            True if reorganization successful
        """
        slot_path = path / slot

        if not slot_path.exists():
            logger.warning(f"Slot does not exist: {slot}")
            return False

        try:
            # Get all package files
            packages = list(slot_path.rglob("*.package"))

            if sort_alphabetically:
                packages.sort(key=lambda p: p.name.lower())

            logger.info(f"Reorganized {len(packages)} mods in {slot}")
            return True

        except Exception as e:
            logger.error(f"Failed to reorganize slot {slot}: {e}")
            return False

    def detect_conflicts(self, path: Path) -> list[tuple[str, str]]:
        """Detect duplicate mod files (same name in multiple slots).

        Args:
            path: ActiveMods base path

        Returns:
            List of tuples (mod_name, slot_locations)
        """
        mod_locations: dict[str, list[str]] = {}

        # Scan all slots
        for slot, _, _ in self.slots:
            slot_path = path / slot
            if not slot_path.exists():
                continue

            for mod_file in slot_path.rglob("*.package"):
                mod_name = mod_file.name
                if mod_name not in mod_locations:
                    mod_locations[mod_name] = []
                mod_locations[mod_name].append(slot)

        # Find duplicates
        conflicts = [
            (name, ", ".join(locations))
            for name, locations in mod_locations.items()
            if len(locations) > 1
        ]

        if conflicts:
            logger.warning(f"Detected {len(conflicts)} duplicate mod names")

        return conflicts

    def export_load_order(self, path: Path, output_file: Path) -> bool:
        """Export load order to text file.

        Args:
            path: ActiveMods base path
            output_file: Output file path

        Returns:
            True if export successful
        """
        try:
            load_order = self.get_load_order(path)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Sims 4 Mod Load Order\n")
                f.write(f"# Generated: {Path.cwd()}\n")
                f.write(f"# Total mods: {len(load_order)}\n\n")

                for idx, mod in enumerate(load_order, 1):
                    f.write(f"{idx:03d}. {mod}\n")

            logger.info(f"Exported load order to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export load order: {e}")
            return False


def get_default_engine() -> LoadOrderEngine:
    """Get default load order engine instance.

    Returns:
        Configured LoadOrderEngine
    """
    return LoadOrderEngine()
