"""DBPF parser for conflict detection in .package files."""

import logging
from pathlib import Path
from struct import unpack
from typing import Optional

logger = logging.getLogger(__name__)


class DBPFParser:
    """Parse Sims 4 .package files (DBPF format) for resource IDs."""

    DBPF_MAGIC = b"DBPF"  # File signature

    @staticmethod
    def parse_package(path: Path) -> set[tuple[int, int, int]]:
        """Extract resource IDs from .package file.

        Args:
            path: Path to .package file

        Returns:
            Set of (type_id, group_id, instance_id) tuples

        Raises:
            ValueError: If file is not valid DBPF format
            FileNotFoundError: If file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Package file not found: {path}")

        with open(path, "rb") as f:
            # Verify DBPF header
            magic = f.read(4)
            if magic != DBPFParser.DBPF_MAGIC:
                raise ValueError(f"Invalid .package file (bad magic): {path}")

            # Read header
            version = unpack("<I", f.read(4))[0]
            logger.debug(f"DBPF version: {version}")

            # Skip to index position (offset 36)
            f.seek(36)
            index_pos = unpack("<I", f.read(4))[0]
            index_count = unpack("<I", f.read(4))[0]

            logger.debug(f"Index: {index_count} entries at position {index_pos}")

            # Jump to resource index
            f.seek(index_pos)
            resources: set[tuple[int, int, int]] = set()

            for _ in range(index_count):
                type_id = unpack("<I", f.read(4))[0]
                group_id = unpack("<I", f.read(4))[0]
                instance_id = unpack("<Q", f.read(8))[0]  # 64-bit

                resources.add((type_id, group_id, instance_id))

                # Skip position and size fields
                f.read(8)

            return resources


class ConflictDetector:
    """Detect conflicts between mods using resource ID analysis."""

    def __init__(self) -> None:
        """Initialize conflict detector."""
        self.resource_map: dict[tuple[int, int, int], list[str]] = {}

    def scan_mod(self, mod_path: Path) -> Optional[set[tuple[int, int, int]]]:
        """Scan single mod for resource IDs.

        Args:
            mod_path: Path to .package file

        Returns:
            Set of resource IDs, or None if parsing failed
        """
        if mod_path.suffix.lower() != ".package":
            logger.debug(f"Skipping non-package file: {mod_path}")
            return None

        try:
            resources = DBPFParser.parse_package(mod_path)
            logger.debug(f"Found {len(resources)} resources in {mod_path.name}")
            return resources
        except Exception as e:
            logger.warning(f"Failed to parse {mod_path.name}: {e}")
            return None

    def build_resource_map(self, mods: list[Path]) -> None:
        """Build map of resources to mods.

        Args:
            mods: List of mod file paths
        """
        self.resource_map.clear()

        for mod_path in mods:
            resources = self.scan_mod(mod_path)
            if resources is None:
                continue

            for resource_id in resources:
                if resource_id not in self.resource_map:
                    self.resource_map[resource_id] = []
                self.resource_map[resource_id].append(mod_path.name)

    def get_conflicts(self) -> dict[str, list[str]]:
        """Get conflicts (resources touched by multiple mods).

        Returns:
            Dictionary mapping resource IDs to conflicting mod names
        """
        conflicts: dict[str, list[str]] = {}

        for resource_id, mod_names in self.resource_map.items():
            if len(mod_names) > 1:
                # Format resource ID as hex string
                type_id, group_id, instance_id = resource_id
                resource_str = f"{type_id:08X}_{group_id:08X}_{instance_id:016X}"
                conflicts[resource_str] = mod_names

        logger.info(f"Found {len(conflicts)} resource conflicts")
        return conflicts

    def check_mod_conflicts(self, mod_path: Path, existing_mods: list[Path]) -> list[str]:
        """Check if new mod conflicts with existing mods.

        Args:
            mod_path: New mod to check
            existing_mods: List of currently installed mods

        Returns:
            List of conflicting mod names
        """
        new_resources = self.scan_mod(mod_path)
        if new_resources is None:
            return []

        # Build resource map from existing mods
        existing_resources: dict[tuple[int, int, int], str] = {}
        for existing_mod in existing_mods:
            resources = self.scan_mod(existing_mod)
            if resources:
                for resource_id in resources:
                    existing_resources[resource_id] = existing_mod.name

        # Find conflicts
        conflicts = []
        for resource_id in new_resources:
            if resource_id in existing_resources:
                conflicting_mod = existing_resources[resource_id]
                if conflicting_mod not in conflicts:
                    conflicts.append(conflicting_mod)

        if conflicts:
            logger.warning(
                f"{mod_path.name} conflicts with: {', '.join(conflicts)}"
            )

        return conflicts
