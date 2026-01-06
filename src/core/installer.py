"""Mod installation with CRC32 verification."""

import logging
import shutil
import zlib
from pathlib import Path


logger = logging.getLogger(__name__)


def hash_file(path: Path) -> int:
    """Calculate CRC32 hash of file.

    Args:
        path: File to hash

    Returns:
        CRC32 hash as integer

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "rb") as f:
        return zlib.crc32(f.read())


class ModInstaller:
    """Handles secure mod installation with verification."""

    def __init__(self, mods_folder: Path) -> None:
        """Initialize installer.

        Args:
            mods_folder: Target Sims 4 Mods directory

        Raises:
            FileNotFoundError: If mods folder doesn't exist
        """
        if not mods_folder.exists():
            raise FileNotFoundError(f"Mods folder not found: {mods_folder}")

        self.mods_folder = mods_folder

    def install_mod(
        self,
        source: Path,
        category: str,
        slot: int,
        is_script: bool = False,
    ) -> bool:
        """Install mod with load order prefix.

        Args:
            source: Source mod file path
            category: Load order category name
            slot: Slot number (001-999)
            is_script: True if .ts4script (must be root-level)

        Returns:
            True if installation successful

        Raises:
            FileNotFoundError: If source doesn't exist
            ValueError: If validation fails
        """
        if not source.exists():
            raise FileNotFoundError(f"Source mod not found: {source}")

        logger.info(f"Installing mod: {source.name}")

        # Hash source file
        source_hash = hash_file(source)
        logger.debug(f"Source hash: {source_hash:08X}")

        # Determine destination
        if is_script:
            # Scripts MUST be in root Mods/ folder
            dest_file = self.mods_folder / source.name
        else:
            # Use slot-based category folder
            category_folder = self.mods_folder / f"{slot:03d}_{category}"
            category_folder.mkdir(exist_ok=True)
            dest_file = category_folder / source.name

        # Check if already exists
        if dest_file.exists():
            logger.warning(f"Mod already exists: {dest_file.name}")
            existing_hash = hash_file(dest_file)
            if existing_hash == source_hash:
                logger.info("Identical file already installed, skipping")
                return True

        # Copy file
        try:
            with open(source, "rb") as src, open(dest_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            if dest_file.exists():
                dest_file.unlink()  # Cleanup partial file
            raise

        # Verify hash post-copy
        dest_hash = hash_file(dest_file)
        if dest_hash != source_hash:
            logger.error(
                f"Hash mismatch after copy! Source: {source_hash:08X}, Dest: {dest_hash:08X}"
            )
            dest_file.unlink()  # Delete corrupted file
            raise ValueError("File corruption detected during copy")

        logger.info(f"Successfully installed: {dest_file.name}")
        return True

    def uninstall_mod(self, mod_path: Path) -> bool:
        """Uninstall mod by removing file.

        Args:
            mod_path: Installed mod path to remove

        Returns:
            True if removal successful
        """
        if not mod_path.exists():
            logger.warning(f"Mod not found: {mod_path}")
            return False

        try:
            mod_path.unlink()
            logger.info(f"Uninstalled: {mod_path.name}")
            return True
        except Exception as e:
            logger.error(f"Uninstall failed: {e}")
            return False

    def backup_mod(self, mod_path: Path, backup_dir: Path) -> Path | None:
        """Create backup of mod file.

        Args:
            mod_path: Mod to backup
            backup_dir: Backup destination directory

        Returns:
            Path to backup file, or None if failed
        """
        if not mod_path.exists():
            logger.error(f"Mod not found: {mod_path}")
            return None

        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / mod_path.name

        try:
            source_hash = hash_file(mod_path)
            shutil.copy2(mod_path, backup_path)
            backup_hash = hash_file(backup_path)

            if source_hash != backup_hash:
                logger.error("Backup hash mismatch")
                backup_path.unlink()
                return None

            logger.info(f"Backed up: {mod_path.name}")
            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None
