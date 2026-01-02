"""Transactional mod deployment engine with ACID guarantees.

This module provides the core deployment logic with automatic rollback,
multiple deployment methods (junction/symlink/copy), and verification.
"""

import ctypes
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, Optional

import zlib

from src.core.exceptions import DeployError, HashValidationError, PathError
from src.utils.game_detector import GameDetector
from src.utils.process_manager import GameProcessManager

logger = logging.getLogger(__name__)

# Deployment method preference order
DEPLOYMENT_METHODS = ["junction", "symlink", "copy"]

# resource.cfg template
RESOURCE_CFG_TEMPLATE = """Priority 1000
PackedFile Mods/ActiveMods/*.package
DirectoryFiles Mods/ActiveMods/*.package
DirectoryFiles Mods/ActiveMods/*/*.package
DirectoryFiles Mods/ActiveMods/*/*/*.package
DirectoryFiles Mods/ActiveMods/*/*/*/*.package
DirectoryFiles Mods/ActiveMods/*/*/*/*/*.package
"""


class DeployEngine:
    """ACID-compliant mod deployment engine with transactional rollback.

    Example:
        >>> engine = DeployEngine()
        >>> with engine.transaction():
        ...     success = engine.deploy(
        ...         active_mods_path=Path("Mods/ActiveMods"),
        ...         game_mods_path=Path("Documents/EA/Mods"),
        ...         progress_callback=lambda step, pct: print(f"{step}: {pct}%")
        ...     )
    """

    def __init__(self, backup_dir: Optional[Path] = None) -> None:
        """Initialize deployment engine.

        Args:
            backup_dir: Directory for backups (auto-detect if None)
        """
        self.backup_dir = backup_dir
        self._backup_path: Optional[Path] = None
        self._deployed_path: Optional[Path] = None
        self._in_transaction = False
        self._deployment_method: Optional[str] = None

    def transaction(self):
        """Context manager for transactional deployment.

        Example:
            >>> with engine.transaction():
            ...     engine.deploy(source, target)
        """
        return self

    def __enter__(self) -> "DeployEngine":
        """Enter transaction context."""
        self._in_transaction = True
        logger.info("=== BEGIN DEPLOYMENT TRANSACTION ===")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit transaction context and handle rollback."""
        if exc_type is not None:
            logger.error(f"Transaction failed: {exc_val}")
            if self._backup_path and self._deployed_path:
                logger.warning("Initiating automatic rollback")
                try:
                    self.rollback(self._backup_path, self._deployed_path)
                except Exception as e:
                    logger.error(f"Rollback failed: {e}")

        self._in_transaction = False
        logger.info("=== END DEPLOYMENT TRANSACTION ===")

    def deploy(
        self,
        active_mods_path: Path,
        game_mods_path: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        close_game: bool = True,
    ) -> bool:
        """Deploy mods with transactional guarantees.

        Args:
            active_mods_path: Source ActiveMods folder
            game_mods_path: Target Mods folder (game documents)
            progress_callback: Optional callback(step_name, percentage)
            close_game: Whether to close game before deployment

        Returns:
            True if deployment successful

        Raises:
            DeployError: On deployment failure
            PathError: On invalid paths
        """
        if not self._in_transaction:
            raise DeployError(
                "Deploy must be called within transaction context",
                recovery_hint="Use 'with engine.transaction():' block",
            )

        # Validate paths
        if not active_mods_path.exists():
            raise PathError(
                f"Active mods path not found: {active_mods_path}",
                recovery_hint="Run SCAN first to populate ActiveMods",
            )

        self._report_progress(progress_callback, "Validating paths", 0.0)

        # Step 1: Backup current Mods folder
        self._report_progress(progress_callback, "Creating backup", 10.0)
        self._backup_path = self._backup_current_mods(game_mods_path)
        logger.info(f"Backup created: {self._backup_path}")

        # Step 2: Validate ActiveMods structure
        self._report_progress(progress_callback, "Validating source files", 20.0)
        self._validate_active_mods(active_mods_path)

        # Step 3: Generate resource.cfg
        self._report_progress(progress_callback, "Generating resource.cfg", 30.0)
        self.generate_resource_cfg(game_mods_path)

        # Step 4: Close game processes
        if close_game:
            self._report_progress(progress_callback, "Closing game", 40.0)
            self._close_game_safely()

        # Step 5: Remove old ActiveMods link/folder if exists
        self._report_progress(progress_callback, "Cleaning old deployment", 50.0)
        deployed_active = game_mods_path / "ActiveMods"
        if deployed_active.exists():
            self._remove_deployment(deployed_active)

        # Step 6: Deploy with fallback methods
        self._report_progress(progress_callback, "Deploying mods", 60.0)
        self._deployed_path = deployed_active
        success = self._deploy_with_fallback(active_mods_path, deployed_active)

        if not success:
            raise DeployError(
                "All deployment methods failed",
                recovery_hint="Check permissions and disk space",
            )

        # Step 7: Verify deployment
        self._report_progress(progress_callback, "Verifying deployment", 80.0)
        if not self.verify_deployment(active_mods_path, deployed_active):
            raise HashValidationError(
                active_mods_path,
                0,
                0,
                recovery_hint="Deployment verification failed, rolling back",
            )

        # Step 8: Final validation
        self._report_progress(progress_callback, "Finalizing", 90.0)
        self._validate_game_accessibility(game_mods_path)

        self._report_progress(progress_callback, "Complete", 100.0)
        logger.info(f"Deployment successful using method: {self._deployment_method}")

        return True

    def _backup_current_mods(self, game_mods_path: Path) -> Path:
        """Create timestamped backup of current Mods folder.

        Args:
            game_mods_path: Path to Mods folder

        Returns:
            Path to backup zip file
        """
        if self.backup_dir is None:
            # Auto-detect backup directory
            self.backup_dir = game_mods_path.parent / "ModManagerBackups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped backup name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}.zip"

        logger.info(f"Creating backup: {backup_path}")

        try:
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if game_mods_path.exists():
                    for file_path in game_mods_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(game_mods_path.parent)
                            zf.write(file_path, arcname)

            logger.info(f"Backup complete: {backup_path.stat().st_size} bytes")
            return backup_path

        except Exception as e:
            raise DeployError(
                f"Failed to create backup: {e}",
                recovery_hint="Check disk space and permissions",
            ) from e

    def _validate_active_mods(self, active_mods_path: Path) -> None:
        """Validate ActiveMods folder structure and file integrity.

        Args:
            active_mods_path: Path to ActiveMods folder

        Raises:
            PathError: If validation fails
        """
        if not active_mods_path.is_dir():
            raise PathError(
                f"ActiveMods is not a directory: {active_mods_path}",
                recovery_hint="Run SCAN to rebuild ActiveMods",
            )

        # Check for at least one mod file
        mod_files = list(active_mods_path.rglob("*.package")) + list(
            active_mods_path.rglob("*.ts4script")
        )

        if not mod_files:
            raise PathError(
                "No mod files found in ActiveMods",
                recovery_hint="Add mods to ActiveMods folder first",
            )

        logger.debug(f"Validated {len(mod_files)} mod files")

    def generate_resource_cfg(self, game_mods_path: Path) -> Path:
        """Generate resource.cfg with DirectoryFiles patterns.

        Args:
            game_mods_path: Path to Mods folder

        Returns:
            Path to created resource.cfg

        Raises:
            DeployError: On write failure
        """
        cfg_path = game_mods_path / "resource.cfg"

        try:
            game_mods_path.mkdir(parents=True, exist_ok=True)

            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(RESOURCE_CFG_TEMPLATE)

            logger.info(f"Generated resource.cfg: {cfg_path}")

            # Validate syntax
            if not self._validate_resource_cfg_syntax(cfg_path):
                raise DeployError("Generated resource.cfg has invalid syntax")

            return cfg_path

        except Exception as e:
            raise DeployError(
                f"Failed to generate resource.cfg: {e}",
                recovery_hint="Check Mods folder permissions",
            ) from e

    def _validate_resource_cfg_syntax(self, cfg_path: Path) -> bool:
        """Validate resource.cfg syntax.

        Args:
            cfg_path: Path to resource.cfg

        Returns:
            True if syntax is valid
        """
        try:
            with open(cfg_path, "r") as f:
                content = f.read()

            # Check for required directives
            required = ["Priority", "DirectoryFiles"]
            if not all(directive in content for directive in required):
                logger.warning("resource.cfg missing required directives")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate resource.cfg: {e}")
            return False

    def _close_game_safely(self) -> None:
        """Close game processes with user confirmation.

        Raises:
            DeployError: If game cannot be closed
        """
        with GameProcessManager() as gpm:
            if not gpm.is_game_running():
                logger.debug("Game not running, skipping close")
                return

            logger.info("Closing game processes")

            if not gpm.close_game_safely(timeout=10):
                raise DeployError(
                    "Failed to close game",
                    recovery_hint="Manually close game and retry",
                )

    def _deploy_with_fallback(self, source: Path, target: Path) -> bool:
        """Deploy using fallback method chain.

        Args:
            source: Source ActiveMods folder
            target: Target deployment location

        Returns:
            True if any method succeeded
        """
        for method in DEPLOYMENT_METHODS:
            try:
                logger.info(f"Attempting deployment method: {method}")

                if method == "junction":
                    if self._create_junction(source, target):
                        self._deployment_method = "junction"
                        return True

                elif method == "symlink":
                    if self._create_symlink(source, target):
                        self._deployment_method = "symlink"
                        return True

                elif method == "copy":
                    if self._copy_files(source, target):
                        self._deployment_method = "copy"
                        return True

            except Exception as e:
                logger.warning(f"Method {method} failed: {e}")
                continue

        return False

    def _create_junction(self, source: Path, target: Path) -> bool:
        """Create Windows junction point.

        Args:
            source: Source directory
            target: Junction point location

        Returns:
            True if successful
        """
        if os.name != "nt":
            logger.debug("Junctions only supported on Windows")
            return False

        try:
            # Check for admin privileges
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

            if not is_admin:
                logger.warning("Junction creation may require admin privileges")

            # Use mklink /J command
            result = subprocess.run(
                ["mklink", "/J", str(target), str(source)],
                check=True,
                capture_output=True,
                shell=True,
                text=True,
            )

            logger.info(f"Junction created: {target} -> {source}")
            return True

        except subprocess.CalledProcessError as e:
            logger.warning(f"Junction creation failed: {e.stderr}")
            return False
        except Exception as e:
            logger.warning(f"Junction creation error: {e}")
            return False

    def _create_symlink(self, source: Path, target: Path) -> bool:
        """Create symbolic link.

        Args:
            source: Source directory
            target: Symlink location

        Returns:
            True if successful
        """
        try:
            os.symlink(source, target, target_is_directory=True)
            logger.info(f"Symlink created: {target} -> {source}")
            return True

        except OSError as e:
            logger.warning(f"Symlink creation failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Symlink creation error: {e}")
            return False

    def _copy_files(self, source: Path, target: Path) -> bool:
        """Copy files (fallback method).

        Args:
            source: Source directory
            target: Target directory

        Returns:
            True if successful
        """
        try:
            shutil.copytree(source, target, dirs_exist_ok=False)
            logger.info(f"Files copied: {source} -> {target}")
            return True

        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False

    def _remove_deployment(self, deployed_path: Path) -> None:
        """Remove existing deployment (link or directory).

        Args:
            deployed_path: Path to remove
        """
        try:
            if deployed_path.is_symlink() or deployed_path.is_junction():
                # Remove link without following
                os.unlink(deployed_path)
                logger.info(f"Removed link: {deployed_path}")
            elif deployed_path.is_dir():
                shutil.rmtree(deployed_path)
                logger.info(f"Removed directory: {deployed_path}")

        except Exception as e:
            logger.warning(f"Failed to remove old deployment: {e}")

    def verify_deployment(self, source: Path, target: Path) -> bool:
        """Verify deployment integrity with hash comparison.

        Args:
            source: Source ActiveMods folder
            target: Deployed ActiveMods folder

        Returns:
            True if all hashes match
        """
        logger.info("Verifying deployment integrity")

        try:
            # Get all mod files from source
            source_files = {}
            for file_path in source.rglob("*"):
                if file_path.is_file() and file_path.suffix in [
                    ".package",
                    ".ts4script",
                    ".py",
                ]:
                    rel_path = file_path.relative_to(source)
                    source_files[rel_path] = self._hash_file(file_path)

            # Compare with target
            for rel_path, source_hash in source_files.items():
                target_file = target / rel_path

                if not target_file.exists():
                    logger.error(f"Missing file in deployment: {rel_path}")
                    return False

                target_hash = self._hash_file(target_file)

                if source_hash != target_hash:
                    logger.error(f"Hash mismatch for {rel_path}")
                    return False

            logger.info(f"Verified {len(source_files)} files successfully")
            return True

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def _hash_file(self, path: Path) -> int:
        """Calculate CRC32 hash of file.

        Args:
            path: File path

        Returns:
            CRC32 hash value
        """
        with open(path, "rb") as f:
            return zlib.crc32(f.read())

    def _validate_game_accessibility(self, game_mods_path: Path) -> None:
        """Validate that Mods folder is accessible by game.

        Args:
            game_mods_path: Path to Mods folder

        Raises:
            DeployError: If validation fails
        """
        # Check folder is readable
        if not os.access(game_mods_path, os.R_OK):
            raise DeployError(
                "Mods folder is not readable",
                recovery_hint="Check folder permissions",
            )

        # Check resource.cfg exists
        cfg_path = game_mods_path / "resource.cfg"
        if not cfg_path.exists():
            raise DeployError(
                "resource.cfg not found after deployment",
                recovery_hint="Manual resource.cfg creation may be needed",
            )

        logger.debug("Game accessibility validated")

    def rollback(self, backup_path: Path, deployed_path: Path) -> None:
        """Rollback deployment from backup.

        Args:
            backup_path: Path to backup zip
            deployed_path: Path to deployed ActiveMods

        Raises:
            DeployError: On rollback failure
        """
        logger.warning(f"Rolling back deployment from {backup_path}")

        try:
            # Remove deployed ActiveMods
            if deployed_path.exists():
                self._remove_deployment(deployed_path)

            # Restore from backup
            with zipfile.ZipFile(backup_path, "r") as zf:
                mods_parent = deployed_path.parent
                zf.extractall(mods_parent)

            logger.info("Rollback complete")

        except Exception as e:
            raise DeployError(
                f"Rollback failed: {e}",
                recovery_hint=f"Manually restore from {backup_path}",
            ) from e

    def _report_progress(
        self,
        callback: Optional[Callable[[str, float], None]],
        step: str,
        percentage: float,
    ) -> None:
        """Report progress to callback.

        Args:
            callback: Progress callback function
            step: Step name
            percentage: Progress percentage (0-100)
        """
        if callback:
            try:
                callback(step, percentage)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        logger.debug(f"Progress: {step} ({percentage:.1f}%)")


# Utility to check if path is junction
def _is_junction(path: Path) -> bool:
    """Check if path is a Windows junction.

    Args:
        path: Path to check

    Returns:
        True if path is junction
    """
    if os.name != "nt":
        return False

    try:
        return path.exists() and path.is_dir() and path.is_symlink()
    except Exception:
        return False


# Add is_junction helper to Path
Path.is_junction = lambda self: _is_junction(self)
