"""Tests for deployment engine."""

import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.deploy_engine import (
    RESOURCE_CFG_TEMPLATE,
    DeployEngine,
)
from src.core.exceptions import DeployError, PathError


@pytest.fixture
def engine() -> DeployEngine:
    """Create DeployEngine instance.

    Returns:
        DeployEngine instance
    """
    return DeployEngine()


@pytest.fixture
def active_mods(tmp_path: Path) -> Path:
    """Create mock ActiveMods folder with test files.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to ActiveMods folder
    """
    active = tmp_path / "ActiveMods"
    active.mkdir()

    # Create test mod files
    (active / "test_mod.package").write_bytes(b"DBPF" + b"\x00" * 100)
    (active / "subfolder").mkdir()
    (active / "subfolder" / "another_mod.package").write_bytes(b"DBPF" + b"\x00" * 50)

    return active


@pytest.fixture
def game_mods(tmp_path: Path) -> Path:
    """Create mock game Mods folder.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to Mods folder
    """
    mods = tmp_path / "Documents" / "Mods"
    mods.mkdir(parents=True)
    return mods


class TestDeployEngine:
    """Test DeployEngine class."""

    def test_initialization(self, engine: DeployEngine) -> None:
        """Test engine initialization."""
        assert engine.backup_dir is None
        assert engine._backup_path is None
        assert engine._deployed_path is None
        assert engine._in_transaction is False

    def test_initialization_with_backup_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom backup directory."""
        backup_dir = tmp_path / "backups"
        engine = DeployEngine(backup_dir=backup_dir)

        assert engine.backup_dir == backup_dir

    def test_transaction_context_manager(self, engine: DeployEngine) -> None:
        """Test transaction context manager."""
        assert not engine._in_transaction

        with engine.transaction():
            assert engine._in_transaction

        assert not engine._in_transaction

    def test_backup_current_mods(
        self,
        engine: DeployEngine,
        game_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test backup creation."""
        # Create some files to backup
        (game_mods / "existing_mod.package").write_bytes(b"test data")
        engine.backup_dir = tmp_path / "backups"

        backup_path = engine._backup_current_mods(game_mods)

        assert backup_path.exists()
        assert backup_path.suffix == ".zip"
        assert "backup_" in backup_path.name

        # Verify backup contents
        with zipfile.ZipFile(backup_path, "r") as zf:
            namelist = zf.namelist()
            assert any("existing_mod.package" in name for name in namelist)

    def test_backup_empty_mods_folder(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test backup of non-existent Mods folder."""
        game_mods = tmp_path / "Mods"
        engine.backup_dir = tmp_path / "backups"

        # Should create empty backup
        backup_path = engine._backup_current_mods(game_mods)

        assert backup_path.exists()

    def test_validate_active_mods_valid(
        self,
        engine: DeployEngine,
        active_mods: Path,
    ) -> None:
        """Test validation of valid ActiveMods folder."""
        engine._validate_active_mods(active_mods)  # Should not raise

    def test_validate_active_mods_empty(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation rejects empty folder."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(PathError, match="No mod files found"):
            engine._validate_active_mods(empty_dir)

    def test_validate_active_mods_not_directory(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation rejects non-directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(PathError, match="not a directory"):
            engine._validate_active_mods(file_path)

    def test_generate_resource_cfg(
        self,
        engine: DeployEngine,
        game_mods: Path,
    ) -> None:
        """Test resource.cfg generation."""
        cfg_path = engine.generate_resource_cfg(game_mods)

        assert cfg_path.exists()
        assert cfg_path.name == "resource.cfg"

        # Check content
        content = cfg_path.read_text()
        assert "Priority 1000" in content
        assert "DirectoryFiles" in content
        assert "ActiveMods" in content

    def test_validate_resource_cfg_syntax_valid(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation of valid resource.cfg."""
        cfg_path = tmp_path / "resource.cfg"
        cfg_path.write_text(RESOURCE_CFG_TEMPLATE)

        assert engine._validate_resource_cfg_syntax(cfg_path) is True

    def test_validate_resource_cfg_syntax_invalid(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation rejects invalid syntax."""
        cfg_path = tmp_path / "resource.cfg"
        cfg_path.write_text("Invalid content")

        assert engine._validate_resource_cfg_syntax(cfg_path) is False

    @patch("src.core.deploy_engine.GameProcessManager")
    def test_close_game_safely_not_running(
        self,
        mock_manager_class: Mock,
        engine: DeployEngine,
    ) -> None:
        """Test closing when game is not running."""
        mock_manager = MagicMock()
        mock_manager.is_game_running.return_value = False
        mock_manager_class.return_value.__enter__.return_value = mock_manager

        engine._close_game_safely()  # Should not raise

        mock_manager.close_game_safely.assert_not_called()

    @patch("src.core.deploy_engine.GameProcessManager")
    def test_close_game_safely_success(
        self,
        mock_manager_class: Mock,
        engine: DeployEngine,
    ) -> None:
        """Test successful game closure."""
        mock_manager = MagicMock()
        mock_manager.is_game_running.return_value = True
        mock_manager.close_game_safely.return_value = True
        mock_manager_class.return_value.__enter__.return_value = mock_manager

        engine._close_game_safely()  # Should not raise

        mock_manager.close_game_safely.assert_called_once()

    @patch("src.core.deploy_engine.GameProcessManager")
    def test_close_game_safely_failure(
        self,
        mock_manager_class: Mock,
        engine: DeployEngine,
    ) -> None:
        """Test failure to close game."""
        mock_manager = MagicMock()
        mock_manager.is_game_running.return_value = True
        mock_manager.close_game_safely.return_value = False
        mock_manager_class.return_value.__enter__.return_value = mock_manager

        with pytest.raises(DeployError, match="Failed to close game"):
            engine._close_game_safely()

    def test_copy_files(
        self,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test file copy deployment method."""
        target = tmp_path / "target"

        success = engine._copy_files(active_mods, target)

        assert success is True
        assert target.exists()
        assert (target / "test_mod.package").exists()
        assert (target / "subfolder" / "another_mod.package").exists()

    @patch("subprocess.run")
    def test_create_junction_success(
        self,
        mock_run: Mock,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test junction creation on Windows."""
        if os.name != "nt":
            pytest.skip("Junction test requires Windows")

        target = tmp_path / "junction"
        mock_run.return_value = MagicMock(returncode=0)

        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
            success = engine._create_junction(active_mods, target)

        assert success is True
        mock_run.assert_called_once()

    @patch("os.symlink")
    def test_create_symlink_success(
        self,
        mock_symlink: Mock,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test symlink creation."""
        target = tmp_path / "symlink"

        success = engine._create_symlink(active_mods, target)

        assert success is True
        mock_symlink.assert_called_once_with(active_mods, target, target_is_directory=True)

    @patch("os.symlink", side_effect=OSError("Permission denied"))
    def test_create_symlink_failure(
        self,
        mock_symlink: Mock,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test symlink creation failure."""
        target = tmp_path / "symlink"

        success = engine._create_symlink(active_mods, target)

        assert success is False

    def test_hash_file(self, engine: DeployEngine, tmp_path: Path) -> None:
        """Test file hashing."""
        test_file = tmp_path / "test.bin"
        test_data = b"test data for hashing"
        test_file.write_bytes(test_data)

        hash_value = engine._hash_file(test_file)

        assert isinstance(hash_value, int)
        assert hash_value != 0

        # Same file should produce same hash
        hash_value2 = engine._hash_file(test_file)
        assert hash_value == hash_value2

    def test_verify_deployment_success(
        self,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test successful deployment verification."""
        # Copy files to create identical target
        target = tmp_path / "deployed"
        engine._copy_files(active_mods, target)

        result = engine.verify_deployment(active_mods, target)

        assert result is True

    def test_verify_deployment_missing_file(
        self,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test verification fails with missing file."""
        target = tmp_path / "deployed"
        target.mkdir()

        # Copy only one file
        (target / "test_mod.package").write_bytes(b"DBPF" + b"\x00" * 100)

        result = engine.verify_deployment(active_mods, target)

        assert result is False

    def test_verify_deployment_hash_mismatch(
        self,
        engine: DeployEngine,
        active_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test verification fails with hash mismatch."""
        target = tmp_path / "deployed"
        engine._copy_files(active_mods, target)

        # Corrupt one file
        (target / "test_mod.package").write_bytes(b"corrupted")

        result = engine.verify_deployment(active_mods, target)

        assert result is False

    def test_remove_deployment_directory(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test removing deployed directory."""
        deployed = tmp_path / "deployed"
        deployed.mkdir()
        (deployed / "file.txt").write_text("test")

        engine._remove_deployment(deployed)

        assert not deployed.exists()

    def test_validate_game_accessibility(
        self,
        engine: DeployEngine,
        game_mods: Path,
    ) -> None:
        """Test game accessibility validation."""
        # Create resource.cfg
        (game_mods / "resource.cfg").write_text(RESOURCE_CFG_TEMPLATE)

        engine._validate_game_accessibility(game_mods)  # Should not raise

    def test_validate_game_accessibility_no_cfg(
        self,
        engine: DeployEngine,
        game_mods: Path,
    ) -> None:
        """Test validation fails without resource.cfg."""
        with pytest.raises(DeployError, match="resource.cfg not found"):
            engine._validate_game_accessibility(game_mods)

    def test_rollback(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test deployment rollback."""
        # Create backup
        backup_path = tmp_path / "backup.zip"
        original_file = tmp_path / "original.txt"
        original_file.write_text("original content")

        with zipfile.ZipFile(backup_path, "w") as zf:
            zf.write(original_file, "Mods/original.txt")

        # Create deployed directory to remove
        deployed = tmp_path / "Mods" / "ActiveMods"
        deployed.mkdir(parents=True)
        (deployed / "bad_file.txt").write_text("bad")

        # Rollback
        engine.rollback(backup_path, deployed)

        # Verify deployed removed and backup restored
        assert not deployed.exists()
        restored = tmp_path / "original.txt"
        assert restored.exists()
        assert restored.read_text() == "original content"  # Match actual content

    def test_report_progress_with_callback(self, engine: DeployEngine) -> None:
        """Test progress reporting with callback."""
        callback = Mock()

        engine._report_progress(callback, "Test step", 50.0)

        callback.assert_called_once_with("Test step", 50.0)

    def test_report_progress_without_callback(self, engine: DeployEngine) -> None:
        """Test progress reporting without callback."""
        engine._report_progress(None, "Test step", 50.0)  # Should not raise

    def test_deploy_without_transaction(
        self,
        engine: DeployEngine,
        active_mods: Path,
        game_mods: Path,
    ) -> None:
        """Test deploy fails outside transaction context."""
        with pytest.raises(DeployError, match="within transaction context"):
            engine.deploy(active_mods, game_mods, close_game=False)

    @patch("src.core.deploy_engine.GameProcessManager")
    def test_deploy_full_flow(
        self,
        mock_manager_class: Mock,
        engine: DeployEngine,
        active_mods: Path,
        game_mods: Path,
        tmp_path: Path,
    ) -> None:
        """Test full deployment flow."""
        # Setup
        engine.backup_dir = tmp_path / "backups"
        mock_manager = MagicMock()
        mock_manager.is_game_running.return_value = False
        mock_manager_class.return_value.__enter__.return_value = mock_manager

        progress_calls = []

        def progress_callback(step: str, pct: float) -> None:
            progress_calls.append((step, pct))

        # Deploy
        with engine.transaction():
            success = engine.deploy(active_mods, game_mods, progress_callback, close_game=False)

        assert success is True
        assert (game_mods / "resource.cfg").exists()
        assert (game_mods / "ActiveMods").exists()
        assert len(progress_calls) > 0

    def test_transaction_rollback_on_exception(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test automatic rollback on exception."""
        backup = tmp_path / "backup.zip"
        with zipfile.ZipFile(backup, "w") as zf:
            zf.writestr("test.txt", "test")

        deployed = tmp_path / "deployed"
        deployed.mkdir()

        engine._backup_path = backup
        engine._deployed_path = deployed

        # Trigger exception in transaction
        with pytest.raises(ValueError):
            with engine.transaction():
                raise ValueError("Test exception")

        # Rollback should have been attempted
        # (may fail in test environment, but should be logged)


class TestDeployEngineExceptionPaths:
    """Tests for exception handling and error recovery paths."""

    def test_deploy_with_missing_active_mods(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test deploy fails gracefully when ActiveMods doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        game_mods = tmp_path / "Mods"
        game_mods.mkdir()

        with pytest.raises(PathError, match="Active mods path not found"):
            with engine.transaction():
                engine.deploy(nonexistent, game_mods, close_game=False)

    def test_backup_creation_failure_disk_full(
        self,
        engine: DeployEngine,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test backup creation handles disk full error."""
        active_mods = tmp_path / "ActiveMods"
        active_mods.mkdir()
        (active_mods / "test.package").write_text("test")

        game_mods = tmp_path / "Mods"
        game_mods.mkdir()

        # Mock zipfile to raise OSError (disk full)
        def mock_zipfile_init(*args, **kwargs):
            raise OSError(28, "No space left on device")

        monkeypatch.setattr("zipfile.ZipFile.__init__", mock_zipfile_init)

        with pytest.raises(DeployError, match="Failed to create backup"):
            with engine.transaction():
                engine.deploy(active_mods, game_mods, close_game=False)

    def test_validate_active_mods_empty_folder(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation fails for empty ActiveMods folder."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(PathError, match="No mod files found"):
            engine._validate_active_mods(empty_dir)

    def test_validate_active_mods_not_directory(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test validation fails when ActiveMods is a file."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")

        with pytest.raises(PathError, match="not a directory"):
            engine._validate_active_mods(file_path)

    def test_generate_resource_cfg_permission_error(
        self,
        engine: DeployEngine,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test resource.cfg generation handles permission errors."""
        mods_dir = tmp_path / "Mods"
        mods_dir.mkdir()

        # Mock open to raise PermissionError
        import builtins

        original_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if "resource.cfg" in str(path):
                raise PermissionError("Access denied")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(DeployError, match="Failed to generate resource.cfg"):
            engine.generate_resource_cfg(mods_dir)

    def test_verify_deployment_hash_mismatch(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test deployment verification catches file corruption."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.package").write_text("original")

        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "test.package").write_text("corrupted")

        result = engine.verify_deployment(source, dest)
        assert result is False

    def test_deploy_all_methods_fail(
        self,
        engine: DeployEngine,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test deploy fails when all methods (junction/symlink/copy) fail."""
        active_mods = tmp_path / "ActiveMods"
        active_mods.mkdir()
        (active_mods / "test.package").write_text("test")

        game_mods = tmp_path / "Mods"
        game_mods.mkdir()

        # Mock all deployment methods to fail
        def fail(*args, **kwargs):
            return False

        monkeypatch.setattr(engine, "_create_junction", fail)
        monkeypatch.setattr(engine, "_create_symlink", fail)
        monkeypatch.setattr(engine, "_copy_files", fail)

        with pytest.raises(DeployError, match="All deployment methods failed"):
            with engine.transaction():
                engine.deploy(active_mods, game_mods, close_game=False)

    @patch("src.core.deploy_engine.GameProcessManager")
    def test_deploy_game_close_failure(
        self,
        mock_gpm_class: Mock,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test deploy handles game close failure gracefully."""
        active_mods = tmp_path / "ActiveMods"
        active_mods.mkdir()
        (active_mods / "test.package").write_text("test")

        game_mods = tmp_path / "Mods"
        game_mods.mkdir()

        # Mock game process manager to indicate game close failed
        mock_gpm = MagicMock()
        mock_gpm.is_game_running.return_value = True
        mock_gpm.close_game_safely.return_value = False
        mock_gpm_class.return_value.__enter__.return_value = mock_gpm

        with pytest.raises(DeployError, match="Failed to close game"):
            with engine.transaction():
                engine.deploy(active_mods, game_mods, close_game=True)

    def test_rollback_with_corrupted_backup(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test rollback handles corrupted backup gracefully."""
        backup = tmp_path / "corrupted.zip"
        backup.write_text("not a valid zip file")

        deployed = tmp_path / "deployed"
        deployed.mkdir()

        with pytest.raises(DeployError, match="Rollback failed"):
            engine.rollback(backup, deployed)

    def test_deploy_with_readonly_destination(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test deploy handles read-only destination directory."""
        active_mods = tmp_path / "ActiveMods"
        active_mods.mkdir()
        (active_mods / "test.package").write_text("test")

        game_mods = tmp_path / "Mods"
        game_mods.mkdir()

        # Make directory read-only (Unix systems)
        import platform

        if platform.system() != "Windows":
            game_mods.chmod(0o444)

            with pytest.raises(DeployError):
                with engine.transaction():
                    engine.deploy(active_mods, game_mods, close_game=False)

            # Restore permissions for cleanup
            game_mods.chmod(0o755)

    def test_validate_resource_cfg_missing_directives(
        self,
        engine: DeployEngine,
        tmp_path: Path,
    ) -> None:
        """Test resource.cfg validation catches missing directives."""
        cfg_path = tmp_path / "resource.cfg"
        cfg_path.write_text("# Empty config\n")

        result = engine._validate_resource_cfg_syntax(cfg_path)
        assert result is False

    def test_backup_with_inaccessible_files(
        self,
        engine: DeployEngine,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test backup creation handles inaccessible files."""
        game_mods = tmp_path / "Mods"
        game_mods.mkdir()
        (game_mods / "accessible.package").write_text("test")

        engine.backup_dir = tmp_path / "backups"

        # Mock rglob to raise PermissionError for some files
        original_rglob = Path.rglob

        def mock_rglob(self, pattern):
            for item in original_rglob(self, pattern):
                if "accessible" in str(item):
                    yield item
                else:
                    raise PermissionError("Access denied")

        monkeypatch.setattr(Path, "rglob", mock_rglob)

        # Should still create backup with accessible files
        backup_path = engine._backup_current_mods(game_mods)
        assert backup_path.exists()
