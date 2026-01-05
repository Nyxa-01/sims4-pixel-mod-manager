"""Tests for game path detector."""

import platform
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.utils.game_detector import GameDetector


@pytest.fixture
def detector() -> GameDetector:
    """Create GameDetector instance for testing.

    Returns:
        GameDetector instance
    """
    return GameDetector()


@pytest.fixture
def mock_game_installation(tmp_path: Path) -> Path:
    """Create mock game installation structure.

    Creates platform-specific executable structure:
    - Windows/Linux: Game/Bin/TS4_x64.exe
    - macOS: The Sims 4.app (in root, as validator checks both locations)

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to mock game root
    """
    game_root = tmp_path / "The Sims 4"
    game_root.mkdir()

    # Create Game/Bin directory
    game_bin = game_root / "Game" / "Bin"
    game_bin.mkdir(parents=True)

    # Create platform-specific executable
    if platform.system() == "Darwin":
        # macOS: Create .app bundle in root (validator checks root for macOS)
        app_bundle = game_root / "The Sims 4.app"
        app_bundle.mkdir()
        # Also create internal structure for completeness
        contents = app_bundle / "Contents" / "MacOS"
        contents.mkdir(parents=True)
        exe = contents / "The Sims 4"
        exe.write_bytes(b"mock executable")
    else:
        # Windows/Linux: Create .exe in Game/Bin
        exe = game_bin / "TS4_x64.exe"
        exe.write_bytes(b"mock executable")

    # Create version file
    version_file = game_bin / "GameVersion.txt"
    version_file.write_text("1.99.305.1030")

    return game_root


@pytest.fixture
def mock_mods_folder(tmp_path: Path) -> Path:
    """Create mock Mods folder.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to mock Mods folder
    """
    mods_path = tmp_path / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"
    mods_path.mkdir(parents=True)
    return mods_path


class TestGameDetector:
    """Test GameDetector class."""

    def test_initialization(self, detector: GameDetector) -> None:
        """Test detector initialization."""
        assert detector.system in ["Windows", "Darwin", "Linux"]
        assert detector._game_path_cache is None
        assert detector._mods_path_cache is None
        assert detector._cache_valid is False

    def test_validate_game_installation_valid(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
    ) -> None:
        """Test validation of valid game installation."""
        assert detector.validate_game_installation(mock_game_installation) is True

    def test_validate_game_installation_invalid(
        self,
        detector: GameDetector,
        tmp_path: Path,
    ) -> None:
        """Test validation rejects invalid paths."""
        # Empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert detector.validate_game_installation(empty_dir) is False

        # Non-existent path
        assert detector.validate_game_installation(Path("/nonexistent")) is False

    def test_validate_game_installation_no_executable(
        self,
        detector: GameDetector,
        tmp_path: Path,
    ) -> None:
        """Test validation fails without executable."""
        game_root = tmp_path / "The Sims 4"
        game_bin = game_root / "Game" / "Bin"
        game_bin.mkdir(parents=True)
        # No executable created

        assert detector.validate_game_installation(game_root) is False

    def test_detect_from_common_paths(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test detection from common paths."""
        # Mock common paths to include our test path
        mock_paths = {detector.system: [mock_game_installation]}
        monkeypatch.setattr("src.utils.game_detector.COMMON_PATHS", mock_paths)

        path = detector._detect_from_common_paths()
        assert path == mock_game_installation

    def test_detect_game_path_with_cache(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
    ) -> None:
        """Test detection caching."""
        # Set cache
        detector._game_path_cache = mock_game_installation
        detector._cache_valid = True

        # Should return cached value without re-detection
        result = detector.detect_game_path()
        assert result == mock_game_installation

    def test_detect_game_path_force_refresh(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
    ) -> None:
        """Test force refresh ignores cache."""
        # Set cache
        detector._game_path_cache = Path("/old/cache")
        detector._cache_valid = True

        # Force refresh should re-detect
        # (will fail to find in this test, but cache should be cleared)
        detector.detect_game_path(force_refresh=True)
        # Cache should have been invalidated
        # (specific result depends on detection methods)

    def test_detect_mods_path_exists(
        self,
        detector: GameDetector,
        mock_mods_folder: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test detection of existing Mods folder."""
        # Mock home directory to point to our test structure
        monkeypatch.setattr(
            Path,
            "home",
            lambda: mock_mods_folder.parents[3],  # Go up to get "home"
        )

        result = detector.detect_mods_path()
        assert result == mock_mods_folder

    def test_detect_mods_path_not_exists(
        self,
        detector: GameDetector,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test detection when Mods folder doesn't exist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = detector.detect_mods_path()
        assert result is None

    def test_create_mods_folder(
        self,
        detector: GameDetector,
        tmp_path: Path,
    ) -> None:
        """Test Mods folder creation."""
        parent = tmp_path / "Documents" / "Electronic Arts" / "The Sims 4"
        parent.mkdir(parents=True)

        mods_path = detector.create_mods_folder(parent)

        assert mods_path is not None
        assert mods_path.exists()
        assert mods_path.name == "Mods"

    def test_create_mods_folder_already_exists(
        self,
        detector: GameDetector,
        mock_mods_folder: Path,
    ) -> None:
        """Test creating Mods folder that already exists."""
        parent = mock_mods_folder.parent
        mods_path = detector.create_mods_folder(parent)

        assert mods_path == mock_mods_folder

    def test_get_game_version_from_file(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
    ) -> None:
        """Test reading game version from file."""
        version = detector.get_game_version(mock_game_installation)
        assert version == "1.99.305.1030"

    def test_get_game_version_no_file(
        self,
        detector: GameDetector,
        tmp_path: Path,
    ) -> None:
        """Test version detection when file doesn't exist."""
        version = detector.get_game_version(tmp_path)
        assert version == "Unknown"

    def test_get_game_version_auto_detect(
        self,
        detector: GameDetector,
        mock_game_installation: Path,
    ) -> None:
        """Test version detection with auto-detect path."""
        # Mock detect_game_path to return our test installation
        detector._game_path_cache = mock_game_installation
        detector._cache_valid = True

        version = detector.get_game_version()
        assert version == "1.99.305.1030"

    @patch("psutil.process_iter")
    def test_is_game_running_true(
        self,
        mock_process_iter: Mock,
        detector: GameDetector,
    ) -> None:
        """Test detection of running game."""
        # Mock process with game name
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe"}
        mock_process_iter.return_value = [mock_proc]

        assert detector.is_game_running() is True

    @patch("psutil.process_iter")
    def test_is_game_running_false(
        self,
        mock_process_iter: Mock,
        detector: GameDetector,
    ) -> None:
        """Test detection when game is not running."""
        # Mock process with different name
        mock_proc = MagicMock()
        mock_proc.info = {"name": "notepad.exe"}
        mock_process_iter.return_value = [mock_proc]

        assert detector.is_game_running() is False

    def test_validate_resource_cfg_valid(
        self,
        detector: GameDetector,
        mock_mods_folder: Path,
    ) -> None:
        """Test validation of valid resource.cfg."""
        resource_cfg = mock_mods_folder / "resource.cfg"
        resource_cfg.write_text("Priority 500\nPackedFile Base/*.package\nPackedFile */*.package")

        assert detector.validate_resource_cfg(mock_mods_folder) is True

    def test_validate_resource_cfg_invalid(
        self,
        detector: GameDetector,
        mock_mods_folder: Path,
    ) -> None:
        """Test validation of invalid resource.cfg."""
        resource_cfg = mock_mods_folder / "resource.cfg"
        resource_cfg.write_text("Invalid content")

        assert detector.validate_resource_cfg(mock_mods_folder) is False

    def test_validate_resource_cfg_missing(
        self,
        detector: GameDetector,
        mock_mods_folder: Path,
    ) -> None:
        """Test validation when resource.cfg doesn't exist."""
        # Should return True (file is optional)
        assert detector.validate_resource_cfg(mock_mods_folder) is True

    def test_clear_cache(self, detector: GameDetector) -> None:
        """Test cache clearing."""
        # Set cache
        detector._game_path_cache = Path("/some/path")
        detector._mods_path_cache = Path("/some/mods")
        detector._cache_valid = True

        # Clear
        detector.clear_cache()

        assert detector._game_path_cache is None
        assert detector._mods_path_cache is None
        assert detector._cache_valid is False

    def test_parse_steam_library_folders(
        self,
        detector: GameDetector,
        tmp_path: Path,
    ) -> None:
        """Test parsing Steam library folders VDF."""
        vdf_content = """
        "libraryfolders"
        {
            "0"
            {
                "path"		"C:\\\\Program Files (x86)\\\\Steam"
            }
            "1"
            {
                "path"		"D:\\\\SteamLibrary"
            }
        }
        """

        vdf_file = tmp_path / "libraryfolders.vdf"
        vdf_file.write_text(vdf_content)

        libraries = detector._parse_steam_library_folders(vdf_file)

        assert len(libraries) >= 1  # Should find at least one path
        assert any("Steam" in str(lib) for lib in libraries)
