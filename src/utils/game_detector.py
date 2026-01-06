"""Cross-platform Sims 4 game installation detector.

This module provides intelligent path discovery for The Sims 4 across
Windows, macOS, and Linux with multiple detection methods and validation.
"""

import logging
import platform
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)

# Game executable names by platform
GAME_EXECUTABLES = {
    "Windows": ["TS4_x64.exe", "TS4.exe"],
    "Darwin": ["The Sims 4.app"],  # macOS
    "Linux": ["TS4_x64.exe", "TS4.exe"],  # Via Proton
}

# Common installation paths by platform
COMMON_PATHS = {
    "Windows": [
        Path.home() / "Documents" / "Electronic Arts" / "The Sims 4",
        Path("C:/Program Files/EA Games/The Sims 4"),
        Path("C:/Program Files (x86)/EA Games/The Sims 4"),
        Path("C:/Program Files/Origin Games/The Sims 4"),
        Path("C:/Program Files (x86)/Origin Games/The Sims 4"),
        Path("C:/Program Files (x86)/Steam/steamapps/common/The Sims 4"),
    ],
    "Darwin": [
        Path.home() / "Documents" / "Electronic Arts" / "The Sims 4",
        Path.home() / "Library" / "Application Support" / "EA" / "The Sims 4",
        Path("/Applications/The Sims 4.app"),
    ],
    "Linux": [
        Path.home() / "Documents" / "Electronic Arts" / "The Sims 4",
        Path.home() / ".steam" / "steam" / "steamapps" / "common" / "The Sims 4",
        Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common" / "The Sims 4",
    ],
}


class GameDetector:
    """Intelligent Sims 4 installation detector with caching.

    Example:
        >>> detector = GameDetector()
        >>> game_path = detector.detect_game_path()
        >>> if game_path:
        ...     print(f"Found game at: {game_path}")
        >>> mods_path = detector.detect_mods_path()
    """

    def __init__(self) -> None:
        """Initialize game detector with caching."""
        self.system = platform.system()
        self._game_path_cache: Path | None = None
        self._mods_path_cache: Path | None = None
        self._cache_valid = False

    def detect_game_path(self, force_refresh: bool = False) -> Path | None:
        """Detect Sims 4 installation path.

        Tries multiple detection methods in priority order:
        1. Windows Registry (Windows only)
        2. Documents folder
        3. Steam libraries
        4. EA App / Origin folders

        Args:
            force_refresh: Force re-detection, ignore cache

        Returns:
            Path to game installation, or None if not found
        """
        # Return cached result if valid
        if self._cache_valid and not force_refresh and self._game_path_cache:
            return self._game_path_cache

        logger.info(f"Detecting Sims 4 installation on {self.system}")

        # Try detection methods in order
        detection_methods = [
            self._detect_from_registry,
            self._detect_from_documents,
            self._detect_from_steam,
            self._detect_from_common_paths,
        ]

        for method in detection_methods:
            try:
                path = method()
                if path and self.validate_game_installation(path):
                    logger.info(f"Found game installation: {path}")
                    self._game_path_cache = path
                    self._cache_valid = True
                    return path
            except Exception as e:
                logger.debug(f"Detection method {method.__name__} failed: {e}")

        logger.warning("Could not detect Sims 4 installation")
        return None

    def _detect_from_registry(self) -> Path | None:
        """Detect from Windows Registry (Windows only).

        Returns:
            Path from registry, or None
        """
        if self.system != "Windows":
            return None

        try:
            import winreg

            # Try HKEY_LOCAL_MACHINE first
            reg_paths: list[tuple[int, str]] = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Maxis\The Sims 4"),  # type: ignore[attr-defined]
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Maxis\The Sims 4"),  # type: ignore[attr-defined]
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Maxis\The Sims 4"),  # type: ignore[attr-defined]
            ]

            for hkey, subkey in reg_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:  # type: ignore[attr-defined]
                        install_dir, _ = winreg.QueryValueEx(key, "Install Dir")  # type: ignore[attr-defined]
                        path = Path(install_dir)
                        logger.debug(f"Registry found: {path}")
                        return path
                except FileNotFoundError:
                    continue

        except ImportError:
            logger.debug("winreg not available (not Windows)")
        except Exception as e:
            logger.debug(f"Registry detection failed: {e}")

        return None

    def _detect_from_documents(self) -> Path | None:
        """Detect from Documents folder.

        Returns:
            Path to game in Documents, or None
        """
        if self.system == "Windows":
            docs = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"
        elif self.system == "Darwin":
            docs = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"
        else:  # Linux
            docs = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"

        if docs.exists():
            logger.debug(f"Found documents folder: {docs}")
            # Documents folder contains saves/mods, not the game itself
            # Try to find game installation from here
            return docs

        return None

    def _detect_from_steam(self) -> Path | None:
        """Detect from Steam library folders.

        Returns:
            Path to game in Steam, or None
        """
        steam_paths: list[Path] = []

        if self.system == "Windows":
            # Common Steam paths on Windows
            steam_paths.extend(
                [
                    Path("C:/Program Files (x86)/Steam"),
                    Path("C:/Program Files/Steam"),
                ]
            )
        elif self.system == "Darwin":
            steam_paths.append(Path.home() / "Library" / "Application Support" / "Steam")
        else:  # Linux
            steam_paths.extend(
                [
                    Path.home() / ".steam" / "steam",
                    Path.home() / ".local" / "share" / "Steam",
                ]
            )

        for steam_root in steam_paths:
            if not steam_root.exists():
                continue

            # Check steamapps/common
            game_path = steam_root / "steamapps" / "common" / "The Sims 4"
            if game_path.exists():
                logger.debug(f"Found Steam installation: {game_path}")
                return game_path

            # Check libraryfolders.vdf for additional libraries
            library_file = steam_root / "steamapps" / "libraryfolders.vdf"
            if library_file.exists():
                additional_paths = self._parse_steam_library_folders(library_file)
                for lib_path in additional_paths:
                    game_path = lib_path / "steamapps" / "common" / "The Sims 4"
                    if game_path.exists():
                        logger.debug(f"Found Steam installation: {game_path}")
                        return game_path

        return None

    def _parse_steam_library_folders(self, vdf_path: Path) -> list[Path]:
        """Parse Steam libraryfolders.vdf for additional library paths.

        Args:
            vdf_path: Path to libraryfolders.vdf

        Returns:
            List of additional library paths
        """
        libraries: list[Path] = []

        try:
            with open(vdf_path, encoding="utf-8") as f:
                content = f.read()

            # Simple parsing: look for "path" entries
            for line in content.split("\n"):
                if '"path"' in line:
                    # Extract path value
                    parts = line.split('"')
                    if len(parts) >= 4:
                        path_str = parts[3].replace("\\\\", "/")
                        libraries.append(Path(path_str))

        except Exception as e:
            logger.debug(f"Failed to parse Steam library folders: {e}")

        return libraries

    def _detect_from_common_paths(self) -> Path | None:
        """Check common installation paths.

        Returns:
            Path from common locations, or None
        """
        paths = COMMON_PATHS.get(self.system, [])

        for path in paths:
            if path.exists():
                logger.debug(f"Found at common path: {path}")
                return path

        return None

    def validate_game_installation(self, path: Path) -> bool:
        """Validate that path contains a valid game installation.

        Args:
            path: Path to check

        Returns:
            True if valid game installation
        """
        if not path.exists():
            return False

        # Check for game executable
        executables = GAME_EXECUTABLES.get(self.system, [])

        for exe_name in executables:
            exe_path = path / "Game" / "Bin" / exe_name
            if exe_path.exists():
                logger.debug(f"Found game executable: {exe_path}")
                return True

            # Also check root for macOS .app
            if self.system == "Darwin" and (path / exe_name).exists():
                return True

        logger.debug(f"No game executable found in: {path}")
        return False

    def detect_mods_path(self) -> Path | None:
        """Detect Mods folder path.

        Returns:
            Path to Mods folder, or None if not found
        """
        # Return cached result if valid
        if self._cache_valid and self._mods_path_cache:
            return self._mods_path_cache

        # Mods folder is typically in Documents
        if self.system == "Windows":
            mods_path = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"
        elif self.system == "Darwin":
            mods_path = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"
        else:  # Linux
            mods_path = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"

        if mods_path.exists():
            logger.info(f"Found Mods folder: {mods_path}")
            self._mods_path_cache = mods_path
            return mods_path

        logger.warning(f"Mods folder not found: {mods_path}")
        return None

    def create_mods_folder(self, parent_path: Path | None = None) -> Path | None:
        """Create Mods folder if it doesn't exist.

        Args:
            parent_path: Parent directory (defaults to Documents)

        Returns:
            Path to created Mods folder, or None on failure
        """
        if parent_path is None:
            parent_path = Path.home() / "Documents" / "Electronic Arts" / "The Sims 4"

        mods_path = parent_path / "Mods"

        try:
            mods_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created Mods folder: {mods_path}")
            self._mods_path_cache = mods_path
            return mods_path
        except Exception as e:
            logger.error(f"Failed to create Mods folder: {e}")
            return None

    def get_game_version(self, path: Path | None = None) -> str:
        """Get game version from installation.

        Args:
            path: Game installation path (auto-detect if None)

        Returns:
            Version string, or "Unknown" if not found
        """
        if path is None:
            path = self.detect_game_path()
            if path is None:
                return "Unknown"

        # Try to read version from GameVersion.txt
        version_file = path / "Game" / "Bin" / "GameVersion.txt"
        if version_file.exists():
            try:
                with open(version_file) as f:
                    version = f.read().strip()
                    logger.debug(f"Game version: {version}")
                    return version
            except Exception as e:
                logger.warning(f"Failed to read version file: {e}")

        return "Unknown"

    def is_game_running(self) -> bool:
        """Check if The Sims 4 is currently running.

        Returns:
            True if game process is detected
        """
        process_names = [
            "TS4_x64.exe",
            "TS4.exe",
            "The Sims 4",
        ]

        try:
            for proc in psutil.process_iter(["name"]):
                proc_name = proc.info.get("name", "")
                if any(name.lower() in proc_name.lower() for name in process_names):
                    logger.info(f"Game is running: {proc_name}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to check running processes: {e}")

        return False

    def validate_resource_cfg(self, mods_path: Path | None = None) -> bool:
        """Validate resource.cfg syntax in Mods folder.

        Args:
            mods_path: Path to Mods folder (auto-detect if None)

        Returns:
            True if resource.cfg is valid or doesn't exist
        """
        if mods_path is None:
            mods_path = self.detect_mods_path()
            if mods_path is None:
                return False

        resource_cfg = mods_path / "resource.cfg"
        if not resource_cfg.exists():
            logger.debug("resource.cfg not found (optional)")
            return True

        try:
            with open(resource_cfg) as f:
                content = f.read()

            # Basic validation: check for required directives
            required = ["Priority", "PackedFile"]
            valid = all(directive in content for directive in required)

            if valid:
                logger.debug("resource.cfg is valid")
            else:
                logger.warning("resource.cfg is missing required directives")

            return valid

        except Exception as e:
            logger.error(f"Failed to validate resource.cfg: {e}")
            return False

    def clear_cache(self) -> None:
        """Clear detection cache."""
        self._game_path_cache = None
        self._mods_path_cache = None
        self._cache_valid = False
        logger.debug("Detection cache cleared")
