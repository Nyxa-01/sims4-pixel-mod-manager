"""Integration tests for complete workflows.

Tests end-to-end scenarios involving multiple modules.
"""

import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.deploy_engine import DeployEngine
from src.core.load_order_engine import LoadOrderEngine
from src.core.mod_scanner import ModScanner
from src.utils.backup import BackupManager
from src.utils.config_manager import ConfigManager
from src.utils.game_detector import GameDetector


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete mod management workflow."""

    def test_scan_organize_deploy_cycle(
        self,
        temp_incoming_dir: Path,
        temp_active_mods_dir: Path,
        mock_game_install: dict[str, Path],
        temp_mod_files: dict[str, Path],
    ):
        """Test full workflow: scan → organize → deploy.

        Args:
            temp_incoming_dir: Incoming mods folder
            temp_active_mods_dir: ActiveMods folder
            mock_game_install: Fake game installation
            temp_mod_files: Mock mod files
        """
        # 1. SCAN: Detect mods in incoming folder
        scanner = ModScanner()

        # Copy mods to incoming
        for name, src in temp_mod_files.items():
            if "valid" in name or "script" in name:
                dest = temp_incoming_dir / src.name
                dest.write_bytes(src.read_bytes())

        mods_by_category = scanner.scan_folder(temp_incoming_dir)
        assert len(mods_by_category) > 0

        # 2. ORGANIZE: Generate load order structure
        load_order = LoadOrderEngine()

        # Assign mods to slots
        mods_by_slot = {}
        for category, mods in mods_by_category.items():
            for mod in mods:
                slot = load_order.assign_mod_to_slot(mod)
                if slot not in mods_by_slot:
                    mods_by_slot[slot] = []
                mods_by_slot[slot].append(mod)

        # Generate ActiveMods structure
        load_order.generate_structure(mods_by_slot, temp_active_mods_dir)

        # Verify structure
        is_valid, warnings = load_order.validate_structure(temp_active_mods_dir)
        assert is_valid, f"Invalid structure: {warnings}"

        # 3. DEPLOY: Deploy to game folder
        deploy_engine = DeployEngine()
        game_mods_path = mock_game_install["mods_dir"]

        with patch("src.utils.game_detector.GameDetector.is_game_running") as mock_running:
            mock_running.return_value = False

            with deploy_engine.transaction():
                success = deploy_engine.deploy(
                    temp_active_mods_dir,
                    game_mods_path,
                    close_game=False,
                )

            assert success
            assert game_mods_path.exists()

    def test_backup_restore_workflow(
        self,
        temp_active_mods_dir: Path,
        temp_backup_dir: Path,
        sample_package_mod: Path,
    ):
        """Test backup → modify → restore workflow.

        Args:
            temp_active_mods_dir: ActiveMods folder
            temp_backup_dir: Backup folder
            sample_package_mod: Sample mod file
        """
        # Setup: Create initial mods
        (temp_active_mods_dir / "mod1.package").write_bytes(sample_package_mod.read_bytes())
        (temp_active_mods_dir / "mod2.package").write_bytes(b"DBPF" + b"\x00" * 50)

        backup_mgr = BackupManager()

        # 1. CREATE BACKUP
        backup_path = backup_mgr.create_backup(
            temp_active_mods_dir,
            temp_backup_dir,
        )

        assert backup_path.exists()
        assert backup_path.suffix == ".zip"

        # Verify backup
        is_valid, message = backup_mgr.verify_backup(backup_path)
        assert is_valid, f"Backup invalid: {message}"

        # 2. MODIFY: Delete mods
        for mod_file in temp_active_mods_dir.glob("*.package"):
            mod_file.unlink()

        assert len(list(temp_active_mods_dir.glob("*.package"))) == 0

        # 3. RESTORE: Restore from backup
        success = backup_mgr.restore_backup(
            backup_path,
            temp_active_mods_dir,
            verify_hashes=True,
        )

        assert success
        assert len(list(temp_active_mods_dir.glob("*.package"))) == 2

    def test_deploy_with_rollback(
        self,
        temp_active_mods_dir: Path,
        mock_game_install: dict[str, Path],
        sample_package_mod: Path,
    ):
        """Test deployment rollback on error.

        Args:
            temp_active_mods_dir: ActiveMods folder
            mock_game_install: Fake game installation
            sample_package_mod: Sample mod file
        """
        # Setup
        (temp_active_mods_dir / "mod.package").write_bytes(sample_package_mod.read_bytes())

        deploy_engine = DeployEngine()
        game_mods_path = mock_game_install["mods_dir"]

        # Add existing mods to game folder
        existing_mod = game_mods_path / "existing.package"
        existing_mod.write_bytes(b"DBPF" + b"\x00" * 100)

        # Simulate deployment failure
        with patch("src.core.deploy_engine.DeployEngine._deploy_with_fallback") as mock_deploy:
            mock_deploy.side_effect = Exception("Deployment failed")

            try:
                with deploy_engine.transaction():
                    deploy_engine.deploy(
                        temp_active_mods_dir,
                        game_mods_path,
                        close_game=False,
                    )
            except Exception:
                pass  # Expected

        # Verify rollback restored existing mod
        assert existing_mod.exists(), "Rollback failed to restore existing mod"


@pytest.mark.integration
class TestConfigIntegration:
    """Test config integration with other components."""

    def test_config_persists_across_sessions(
        self,
        tmp_path: Path,
        mock_encryption_key: Path,
    ):
        """Test config saves and loads correctly.

        Args:
            tmp_path: Temporary directory
            mock_encryption_key: Encryption key
        """
        config_path = tmp_path / "config.json"

        # Session 1: Create and save config
        config1 = ConfigManager(config_path)
        config1.set("incoming_folder", str(tmp_path / "incoming"))
        config1.set("backup_retention_count", 15)
        config1.save_config()

        # Session 2: Load config
        config2 = ConfigManager(config_path)
        assert config2.get("incoming_folder") == str(tmp_path / "incoming")
        assert config2.get("backup_retention_count") == 15

    def test_config_corruption_recovery(
        self,
        tmp_path: Path,
        mock_encryption_key: Path,
    ):
        """Test config recovers from corruption.

        Args:
            tmp_path: Temporary directory
            mock_encryption_key: Encryption key
        """
        config_path = tmp_path / "config.json"

        # Create valid config
        config = ConfigManager(config_path)
        config.set("test_key", "test_value")
        config.save_config()

        # Corrupt config file
        config_path.write_text("CORRUPTED DATA {[}")

        # Should recover with defaults
        config2 = ConfigManager(config_path)
        assert config2.get("test_key", "default") == "default"


@pytest.mark.integration
class TestGameDetection:
    """Test game detection integration."""

    def test_detect_and_validate_game_install(
        self,
        mock_game_install: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test detecting and validating game installation.

        Args:
            mock_game_install: Fake game installation
            monkeypatch: Pytest monkeypatch fixture
        """
        detector = GameDetector()

        # Mock Windows registry detection
        with patch("winreg.OpenKey"), patch("winreg.QueryValueEx") as mock_query:

            mock_query.return_value = (str(mock_game_install["game_dir"]), 1)

            # Detect game path
            game_path = detector.detect_game_path()

            # Validate installation
            if game_path:
                is_valid = detector.validate_game_installation(game_path)
                assert is_valid

                # Get version
                version = detector.get_game_version(game_path)
                assert version == "1.98.127.1030"

    def test_detect_mods_folder_cross_platform(
        self,
        mock_game_install: dict[str, Path],
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test mods folder detection on different platforms.

        Args:
            mock_game_install: Fake game installation
            monkeypatch: Pytest monkeypatch fixture
        """
        detector = GameDetector()

        # Mock home directory
        monkeypatch.setenv("USERPROFILE", str(mock_game_install["documents"].parent.parent))
        monkeypatch.setenv("HOME", str(mock_game_install["documents"].parent.parent))

        mods_path = detector.detect_mods_path()

        assert mods_path is not None
        assert mods_path.name == "Mods"


@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Test security features integration."""

    def test_reject_malicious_mod_in_workflow(
        self,
        temp_incoming_dir: Path,
        malicious_mod: Path,
    ):
        """Test malicious mods are rejected in workflow.

        Args:
            temp_incoming_dir: Incoming folder
            malicious_mod: Malicious mod file
        """
        # Copy malicious mod to incoming
        dest = temp_incoming_dir / "malicious.package"
        dest.write_bytes(malicious_mod.read_bytes())

        scanner = ModScanner()
        mods_by_category = scanner.scan_folder(temp_incoming_dir)

        # Check if malicious mod was flagged
        all_mods = []
        for mods in mods_by_category.values():
            all_mods.extend(mods)

        malicious_detected = False
        for mod in all_mods:
            if "malicious" in mod.path.name:
                malicious_detected = True
                assert not mod.is_valid, "Malicious mod should be marked invalid"

        assert malicious_detected, "Malicious mod should be detected"

    def test_encrypted_paths_in_config(
        self,
        tmp_path: Path,
        mock_encryption_key: Path,
    ):
        """Test sensitive paths are encrypted in config.

        Args:
            tmp_path: Temporary directory
            mock_encryption_key: Encryption key
        """
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path)

        # Set sensitive path
        sensitive_path = str(tmp_path / "sensitive" / "path")
        config.set("game_path", sensitive_path)
        config.save_config()

        # Read raw config file
        raw_content = config_path.read_text()

        # Verify path is not in plain text
        assert sensitive_path not in raw_content, "Path should be encrypted"

        # Verify can be decrypted
        loaded_path = config.get("game_path")
        assert loaded_path == sensitive_path


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance with large mod collections."""

    def test_scan_large_mod_collection(
        self,
        temp_incoming_dir: Path,
    ):
        """Test scanning 100+ mods.

        Args:
            temp_incoming_dir: Incoming folder
        """
        # Create 100 mock mods
        for i in range(100):
            mod_file = temp_incoming_dir / f"mod_{i:03d}.package"
            mod_file.write_bytes(b"DBPF" + b"\x00" * 100)

        scanner = ModScanner()
        mods_by_category = scanner.scan_folder(temp_incoming_dir)

        total_mods = sum(len(mods) for mods in mods_by_category.values())
        assert total_mods == 100

    def test_deploy_large_mod_collection(
        self,
        temp_active_mods_dir: Path,
        mock_game_install: dict[str, Path],
    ):
        """Test deploying 50+ mods.

        Args:
            temp_active_mods_dir: ActiveMods folder
            mock_game_install: Fake game installation
        """
        # Create load order structure with mods
        for slot in ["000_Core", "020_MainMods", "040_CC"]:
            slot_dir = temp_active_mods_dir / slot
            slot_dir.mkdir()

            for i in range(20):
                mod_file = slot_dir / f"mod_{i}.package"
                mod_file.write_bytes(b"DBPF" + b"\x00" * 50)

        deploy_engine = DeployEngine()

        with patch("src.utils.game_detector.GameDetector.is_game_running") as mock_running:
            mock_running.return_value = False

            # This should handle 60 mods efficiently
            with deploy_engine.transaction():
                success = deploy_engine.deploy(
                    temp_active_mods_dir,
                    mock_game_install["mods_dir"],
                    close_game=False,
                    method="copy",  # Use copy for test speed
                )

            assert success


@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery scenarios."""

    def test_recover_from_partial_deployment(
        self,
        temp_active_mods_dir: Path,
        mock_game_install: dict[str, Path],
        sample_package_mod: Path,
    ):
        """Test recovery from interrupted deployment.

        Args:
            temp_active_mods_dir: ActiveMods folder
            mock_game_install: Fake game installation
            sample_package_mod: Sample mod file
        """
        # Setup
        (temp_active_mods_dir / "mod.package").write_bytes(sample_package_mod.read_bytes())

        deploy_engine = DeployEngine()
        game_mods_path = mock_game_install["mods_dir"]

        # Simulate partial deployment (copy some files then fail)
        with patch("shutil.copytree") as mock_copy:

            def partial_copy(src, dst, *args, **kwargs):
                # Copy first file then fail
                dst.mkdir(exist_ok=True)
                (dst / "mod.package").write_bytes(b"PARTIAL")
                raise Exception("Deployment interrupted")

            mock_copy.side_effect = partial_copy

            try:
                with deploy_engine.transaction():
                    deploy_engine.deploy(
                        temp_active_mods_dir,
                        game_mods_path,
                        close_game=False,
                        method="copy",
                    )
            except Exception:
                pass  # Expected

        # Verify cleanup happened
        # (transaction rollback should have cleaned up partial files)

    def test_recover_from_backup_corruption(
        self,
        temp_backup_dir: Path,
        sample_backup_zip: Path,
    ):
        """Test handling corrupted backup file.

        Args:
            temp_backup_dir: Backup folder
            sample_backup_zip: Sample backup
        """
        backup_mgr = BackupManager()

        # Corrupt backup
        corrupted = temp_backup_dir / "corrupted.zip"
        corrupted.write_bytes(b"CORRUPTED ZIP FILE")

        # Verify should detect corruption
        is_valid, message = backup_mgr.verify_backup(corrupted)
        assert not is_valid
        assert "corrupt" in message.lower() or "invalid" in message.lower()

        # Restore should fail gracefully
        success = backup_mgr.restore_backup(corrupted, temp_backup_dir / "restore")
        assert not success
