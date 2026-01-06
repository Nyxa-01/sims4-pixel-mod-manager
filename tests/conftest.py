"""Pytest configuration and shared fixtures.

Comprehensive fixtures for all test modules with 95%+ code coverage support.
"""

import logging
import os
import platform
import zipfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock

import pytest


# =============================================================================
# LOGGING
# =============================================================================


@pytest.fixture
def disable_logging() -> Generator[None, None, None]:
    """Disable logging during tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# =============================================================================
# FILE SYSTEM FIXTURES
# =============================================================================


@pytest.fixture
def temp_mods_dir(tmp_path: Path) -> Path:
    """Create temporary mods directory for testing.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary mods directory
    """
    mods_dir = tmp_path / "Mods"
    mods_dir.mkdir()
    return mods_dir


@pytest.fixture
def temp_incoming_dir(tmp_path: Path) -> Path:
    """Create temporary incoming mods directory.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to incoming directory
    """
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    return incoming


@pytest.fixture
def temp_active_mods_dir(tmp_path: Path) -> Path:
    """Create temporary ActiveMods directory.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to ActiveMods directory
    """
    active = tmp_path / "ActiveMods"
    active.mkdir()
    return active


@pytest.fixture
def temp_backup_dir(tmp_path: Path) -> Path:
    """Create temporary backup directory.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to backup directory
    """
    backup = tmp_path / "backups"
    backup.mkdir()
    return backup


# =============================================================================
# MOD FILE FIXTURES
# =============================================================================


@pytest.fixture
def sample_package_mod(tmp_path: Path) -> Path:
    """Create sample .package mod file with valid DBPF header.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample mod file
    """
    mod_file = tmp_path / "sample_mod.package"
    # DBPF header with minimal structure
    header = b"DBPF"  # Magic
    header += b"\x02\x00\x00\x00"  # Major version 2
    header += b"\x01\x00\x00\x00"  # Minor version 1
    header += b"\x00" * 28  # Reserved/padding
    header += b"\x30\x00\x00\x00"  # Index offset (48)
    header += b"\x01\x00\x00\x00"  # Index count (1)
    header += b"\x00" * 100  # Padding/data
    mod_file.write_bytes(header)
    return mod_file


@pytest.fixture
def sample_script_mod(tmp_path: Path) -> Path:
    """Create sample .ts4script mod file.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample script mod
    """
    mod_file = tmp_path / "sample_script.ts4script"
    mod_file.write_bytes(b"# Python script mod\nimport sims4\n")
    return mod_file


@pytest.fixture
def sample_python_mod(tmp_path: Path) -> Path:
    """Create sample .py mod file.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to sample Python mod
    """
    mod_file = tmp_path / "sample_mod.py"
    mod_file.write_text("# Sims 4 Python mod\ndef main():\n    pass\n")
    return mod_file


@pytest.fixture
def temp_mod_files(tmp_path: Path) -> dict[str, Path]:
    """Create multiple mock mod files of different types.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Dictionary mapping mod type to file path
    """
    files = {}

    # Valid package mod
    package = tmp_path / "valid.package"
    package.write_bytes(b"DBPF" + b"\x00" * 200)
    files["valid_package"] = package

    # Script mod
    script = tmp_path / "script.ts4script"
    script.write_bytes(b"# Script mod")
    files["script"] = script

    # Python mod
    python_mod = tmp_path / "python_mod.py"
    python_mod.write_text("def test(): pass")
    files["python"] = python_mod

    # Invalid package (wrong magic)
    invalid = tmp_path / "invalid.package"
    invalid.write_bytes(b"XXXX" + b"\x00" * 200)
    files["invalid_package"] = invalid

    # Oversized mod (over 500MB)
    # Note: Don't actually write 500MB in tests
    oversized = tmp_path / "oversized.package"
    oversized.write_bytes(b"DBPF" + b"\x00" * 1000)
    files["oversized"] = oversized

    # Nested structure
    nested_dir = tmp_path / "nested" / "deep" / "path"
    nested_dir.mkdir(parents=True)
    nested_mod = nested_dir / "nested.package"
    nested_mod.write_bytes(b"DBPF" + b"\x00" * 100)
    files["nested"] = nested_mod

    return files


@pytest.fixture
def malicious_mod(tmp_path: Path) -> Path:
    """Create a mock malicious mod file for security testing.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to malicious mod file
    """
    mal_file = tmp_path / "malicious.package"
    # High entropy data (appears encrypted/packed)
    import random

    random.seed(42)  # Reproducible
    mal_file.write_bytes(bytes([random.randint(0, 255) for _ in range(1000)]))
    return mal_file


# =============================================================================
# GAME INSTALLATION FIXTURES
# =============================================================================


@pytest.fixture
def mock_game_install(tmp_path: Path) -> dict[str, Path]:
    """Create fake Sims 4 installation structure.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Dictionary with game paths
    """
    # Game install directory
    game_dir = tmp_path / "The Sims 4"
    game_dir.mkdir()

    # Executable
    game_exe = game_dir / "Game" / "Bin" / "TS4_x64.exe"
    game_exe.parent.mkdir(parents=True)
    game_exe.write_bytes(b"MZ")  # Minimal PE header

    # Game version file
    version_file = game_dir / "Game" / "Bin" / "GameVersion.txt"
    version_file.write_text("1.98.127.1030")

    # Documents directory
    documents = tmp_path / "Documents" / "Electronic Arts" / "The Sims 4"
    documents.mkdir(parents=True)

    # Mods folder
    mods_dir = documents / "Mods"
    mods_dir.mkdir()

    # Resource.cfg
    resource_cfg = mods_dir / "Resource.cfg"
    resource_cfg.write_text("Priority 500\nDirectoryFiles */*.package 5\n")

    # Tray folder
    tray = documents / "Tray"
    tray.mkdir()

    return {
        "game_dir": game_dir,
        "game_exe": game_exe,
        "version_file": version_file,
        "documents": documents,
        "mods_dir": mods_dir,
        "resource_cfg": resource_cfg,
        "tray": tray,
    }


# =============================================================================
# CONFIG FIXTURES
# =============================================================================


@pytest.fixture
def mock_config(tmp_path: Path) -> dict:
    """Create mock configuration dictionary.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Mock config dictionary
    """
    return {
        "incoming_folder": str(tmp_path / "incoming"),
        "active_mods_folder": str(tmp_path / "ActiveMods"),
        "backup_folder": str(tmp_path / "backups"),
        "game_path": str(tmp_path / "The Sims 4"),
        "mods_path": str(tmp_path / "Documents" / "Electronic Arts" / "The Sims 4" / "Mods"),
        "max_mod_size_mb": 500,
        "backup_retention_count": 10,
        "scan_timeout_seconds": 30,
    }


@pytest.fixture
def mock_encryption_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create mock encryption key for testing.

    Args:
        tmp_path: Pytest tmp_path fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Path to mock encryption key
    """
    key_dir = tmp_path / "config"
    key_dir.mkdir()
    key_file = key_dir / ".encryption.key"

    # Generate test key
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    key_file.write_bytes(key)

    # Monkeypatch config path if needed
    return key_file


# =============================================================================
# BACKUP FIXTURES
# =============================================================================


@pytest.fixture
def sample_backup_zip(tmp_path: Path) -> Path:
    """Create sample backup ZIP file with manifest.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to backup ZIP
    """
    backup_path = tmp_path / "backup_2026-01-01_120000.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Create manifest
        manifest = {
            "timestamp": "2026-01-01T12:00:00",
            "game_version": "1.98.127.1030",
            "files": {
                "test.package": "A1B2C3D4",
                "nested/mod.package": "E5F6G7H8",
            },
        }
        import json

        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Add mock mod files
        zf.writestr("test.package", b"DBPF" + b"\x00" * 100)
        zf.writestr("nested/mod.package", b"DBPF" + b"\x00" * 50)

    return backup_path


# =============================================================================
# LOAD ORDER FIXTURES
# =============================================================================


@pytest.fixture
def load_order_structure(tmp_path: Path) -> Path:
    """Create sample load order directory structure.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to load order root
    """
    root = tmp_path / "LoadOrder"
    root.mkdir()

    # Create slots
    slots = [
        "000_Core",
        "010_Libraries",
        "020_MainMods",
        "030_Tuning",
        "040_CC",
        "ZZZ_Overrides",
    ]

    for slot in slots:
        slot_dir = root / slot
        slot_dir.mkdir()
        # Add sample mod
        (slot_dir / f"{slot}_sample.package").write_bytes(b"DBPF" + b"\x00" * 50)

    return root


# =============================================================================
# PROCESS/SYSTEM FIXTURES
# =============================================================================


@pytest.fixture
def mock_game_process() -> Mock:
    """Create mock game process object.

    Returns:
        Mock psutil.Process object
    """
    process = Mock()
    process.name.return_value = "TS4_x64.exe"
    process.pid = 12345
    process.is_running.return_value = True
    process.terminate.return_value = None
    process.kill.return_value = None
    process.wait.return_value = 0
    return process


# =============================================================================
# PLATFORM FIXTURES
# =============================================================================


@pytest.fixture
def mock_windows_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Windows platform for cross-platform testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(os, "name", "nt")


@pytest.fixture
def mock_macos_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock macOS platform for cross-platform testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(os, "name", "posix")


@pytest.fixture
def mock_linux_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Linux platform for cross-platform testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(os, "name", "posix")
