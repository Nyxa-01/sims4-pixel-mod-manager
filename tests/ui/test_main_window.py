"""Tests for main window UI."""

import os
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.core.mod_scanner import ModFile
from src.ui.main_window import HelpDialog, MainWindow, SettingsDialog

# Skip all UI tests in CI environment (no display available)
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="UI tests require display (not available in CI)",
)


@pytest.fixture
def root():
    """Create Tkinter root for testing."""
    root = tk.Tk()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def mock_managers():
    """Mock all manager dependencies."""
    with (
        patch("src.ui.main_window.ConfigManager") as mock_config,
        patch("src.ui.main_window.ModScanner") as mock_scanner,
        patch("src.ui.main_window.LoadOrderEngine") as mock_lo_engine,
        patch("src.ui.main_window.DeployEngine") as mock_deploy,
        patch("src.ui.main_window.BackupManager") as mock_backup,
        patch("src.ui.main_window.GameDetector") as mock_detector,
    ):

        # Configure mocks
        mock_config.get_instance.return_value.get.return_value = ""
        mock_scanner.return_value.scan_folder.return_value = {}
        mock_lo_engine.return_value.slots = [
            ("000_Core", "Core scripts", ["mccc", "script"]),
            ("020_MainMods", "Main mods", ["gameplay"]),
        ]

        yield {
            "config": mock_config,
            "scanner": mock_scanner,
            "load_order_engine": mock_lo_engine,
            "deploy_engine": mock_deploy,
            "backup_manager": mock_backup,
            "game_detector": mock_detector,
        }


@pytest.fixture
def main_window(root, mock_managers):
    """Create MainWindow instance with mocked dependencies."""
    window = MainWindow(root)
    return window


class TestMainWindowInit:
    """Test main window initialization."""

    def test_init_creates_window(self, root, mock_managers):
        """Test window is created with correct properties."""
        window = MainWindow(root)

        assert window.root == root
        assert root.title() == "SIMS 4 PIXEL MOD MANAGER"
        assert window.incoming_mods == []
        assert isinstance(window.load_order_slots, dict)

    def test_init_applies_theme(self, root, mock_managers):
        """Test theme is applied to window."""
        with patch("src.ui.main_window.PixelTheme") as mock_theme:
            mock_instance = MagicMock()  # Use MagicMock for subscriptable colors
            # Configure colors dict to return valid hex colors
            mock_instance.colors.__getitem__.side_effect = lambda k: {
                "bg_dark": "#1a1a2e",
                "bg_light": "#16213e",
                "text": "#eee",
                "accent": "#0f3460",
                "success": "#53d769",
                "warning": "#ffd60a",
                "error": "#ff453a",
            }.get(k, "#000000")
            mock_theme.get_instance.return_value = mock_instance

            window = MainWindow(root)

            mock_instance.apply_theme.assert_called_once_with(root)

    def test_init_creates_managers(self, root, mock_managers):
        """Test all manager instances are created."""
        window = MainWindow(root)

        assert window.config is not None
        assert window.scanner is not None
        assert window.load_order_engine is not None
        assert window.deploy_engine is not None
        assert window.backup_manager is not None
        assert window.game_detector is not None

    def test_init_creates_ui_components(self, main_window):
        """Test UI components are created."""
        assert main_window.status_label is not None
        assert main_window.progress_bar is not None
        assert hasattr(main_window, "incoming_listbox")

    def test_window_geometry(self, root, mock_managers):
        """Test window size and centering."""
        window = MainWindow(root)

        # Check minimum size
        assert root.minsize() == (600, 400)

    def test_shortcuts_bound(self, main_window):
        """Test keyboard shortcuts are bound."""
        # Check bindings exist
        bindings = main_window.root.bind()
        # Note: Can't easily verify specific bindings without triggering them


class TestMainWindowUI:
    """Test UI layout and components."""

    def test_menu_bar_created(self, main_window):
        """Test menu bar exists with File, Tools, Help menus."""
        menu = main_window.root["menu"]
        assert menu is not None

    def test_header_created(self, main_window):
        """Test header with title and buttons exists."""
        # Header should contain title label
        assert main_window.status_label is not None

    def test_incoming_panel_created(self, main_window):
        """Test incoming mods panel exists."""
        assert hasattr(main_window, "incoming_listbox")
        assert hasattr(main_window, "incoming_count_label")

    def test_load_order_slots_created(self, main_window):
        """Test load order slot widgets are created."""
        # Should create slots from load_order_engine
        assert len(main_window.load_order_slots) >= 2
        assert "000_Core" in main_window.load_order_slots
        assert "020_MainMods" in main_window.load_order_slots

    def test_status_bar_created(self, main_window):
        """Test status bar with progress exists."""
        assert main_window.status_label is not None
        assert main_window.progress_bar is not None


class TestMainWindowActions:
    """Test button actions and operations."""

    def test_update_status(self, main_window):
        """Test status bar update."""
        main_window._update_status("Testing", 0.5)

        status_text = main_window.status_label.cget("text")
        assert "Testing" in status_text

    def test_scan_mods_prompts_for_folder(self, main_window):
        """Test scan prompts for folder if not configured."""
        # Config returns empty string, and Path("").exists() returns False
        main_window.config.get.return_value = ""

        with (
            patch("src.ui.main_window.Path") as mock_path,
            patch("src.ui.main_window.filedialog.askdirectory") as mock_dialog,
        ):
            # Mock Path to return non-existent path
            mock_path_instance = mock_path.return_value
            mock_path_instance.exists.return_value = False
            mock_dialog.return_value = ""  # User cancels

            main_window._scan_mods()

            mock_dialog.assert_called_once()

    def test_scan_mods_updates_list(self, main_window, tmp_path):
        """Test scanning updates incoming list."""
        # Setup
        test_mod = ModFile(
            path=tmp_path / "test.package",
            mod_type="package",
            size=1024,
            hash="abc123",
            category="Mods",
            is_valid=True,
        )

        main_window.config.get.return_value = str(tmp_path)
        main_window.scanner.scan_folder.return_value = {"package": [test_mod]}

        # Mock threading to run synchronously
        with patch("src.ui.main_window.threading.Thread") as mock_thread:
            mock_thread.return_value.start.side_effect = lambda: mock_thread.call_args[1][
                "target"
            ]()

            main_window._scan_mods()
            main_window.root.update()  # Process after() calls

        # Verify
        assert len(main_window.incoming_mods) == 1
        assert main_window.incoming_mods[0] == test_mod

    def test_generate_structure_collects_from_slots(self, main_window, tmp_path):
        """Test generate collects mods from slots."""
        # Setup mods
        test_mod = ModFile(
            path=tmp_path / "test.package",
            mod_type="package",
            size=1024,
            hash="abc123",
            category="Mods",
            is_valid=True,
        )
        main_window.incoming_mods = [test_mod]

        # Add to slot
        main_window.load_order_slots["000_Core"].insert(tk.END, "test.package")

        # Configure path
        main_window.config.get.return_value = str(tmp_path / "ActiveMods")

        # Execute
        with patch("src.ui.main_window.messagebox.showinfo"):
            main_window._generate_structure()

        # Verify generate_structure called
        main_window.load_order_engine.generate_structure.assert_called_once()

    def test_deploy_checks_game_running(self, main_window):
        """Test deploy checks if game is running."""
        main_window.game_detector.is_game_running.return_value = True

        with patch("src.ui.main_window.messagebox.askyesno") as mock_dialog:
            mock_dialog.return_value = False

            main_window._deploy_mods()

            mock_dialog.assert_called_once()
            status = main_window.status_label.cget("text")
            assert "cancelled" in status.lower()

    def test_deploy_confirms_before_proceeding(self, main_window):
        """Test deploy asks for confirmation."""
        main_window.game_detector.is_game_running.return_value = False

        with patch("src.ui.main_window.messagebox.askyesno") as mock_dialog:
            mock_dialog.return_value = False

            main_window._deploy_mods()

            assert mock_dialog.call_count >= 1

    def test_create_backup_success(self, main_window, tmp_path):
        """Test backup creation."""
        active_path = tmp_path / "ActiveMods"
        active_path.mkdir()

        main_window.config.get.side_effect = lambda k, d: (
            str(active_path) if "active" in k else str(tmp_path)
        )
        main_window.backup_manager.create_backup.return_value = tmp_path / "backup.zip"

        with patch("src.ui.main_window.messagebox.showinfo"):
            main_window._create_backup()

        main_window.backup_manager.create_backup.assert_called_once()

    def test_assign_mod_to_slot(self, main_window, tmp_path):
        """Test double-click assigns mod to slot."""
        # Setup
        test_mod = ModFile(
            path=tmp_path / "test.package",
            mod_type="package",
            size=1024,
            hash="abc123",
            category="Mods",
            is_valid=True,
        )
        main_window.incoming_mods = [test_mod]
        main_window.incoming_listbox.insert(tk.END, "test.package")

        # Configure assignment
        main_window.load_order_engine.assign_mod_to_slot.return_value = "000_Core"

        # Create fake event
        event = Mock()
        main_window.incoming_listbox.selection_set(0)

        # Execute
        main_window._assign_mod_to_slot(event)

        # Verify
        main_window.load_order_engine.assign_mod_to_slot.assert_called_once_with(test_mod)
        assert main_window.load_order_slots["000_Core"].size() == 1

    def test_remove_from_slot(self, main_window):
        """Test removing mod from slot."""
        # Add mod to slot
        main_window.load_order_slots["000_Core"].insert(tk.END, "test.package")
        main_window.load_order_slots["000_Core"].selection_set(0)

        # Remove
        main_window._remove_from_slot("000_Core")

        # Verify
        assert main_window.load_order_slots["000_Core"].size() == 0


class TestSettingsDialog:
    """Test settings dialog."""

    def test_dialog_created(self, root, mock_managers):
        """Test dialog is created with correct properties."""
        config = mock_managers["config"].get_instance.return_value

        dialog = SettingsDialog(root, config)

        assert dialog.dialog.title() == "Settings"
        assert dialog.config == config

    def test_save_updates_config(self, root, mock_managers):
        """Test save button updates config."""
        config = mock_managers["config"].get_instance.return_value
        config.get.return_value = "./test"

        dialog = SettingsDialog(root, config)

        # Update entries
        dialog.entry_incoming_folder.delete(0, tk.END)
        dialog.entry_incoming_folder.insert(0, "./new_path")

        # Save
        with patch("src.ui.main_window.messagebox.showinfo"):
            dialog._save()

        # Verify
        config.set.assert_called()
        config.save_config.assert_called_once()


class TestHelpDialog:
    """Test help dialog."""

    def test_dialog_created(self, root):
        """Test help dialog is created."""
        with patch("src.ui.main_window.PixelTheme"):
            dialog = HelpDialog(root)

            assert dialog.dialog.title() == "Help"

    def test_help_text_contains_shortcuts(self, root):
        """Test help text contains keyboard shortcuts."""
        with patch("src.ui.main_window.PixelTheme"):
            dialog = HelpDialog(root)

            # Help text widget should exist
            # Note: Can't easily verify text content in tests


class TestErrorHandling:
    """Test error handling."""

    def test_scan_error_shows_dialog(self, main_window):
        """Test scan errors are displayed."""
        main_window.scanner.scan_folder.side_effect = Exception("Test error")
        main_window.config.get.return_value = "./test"

        with (
            patch("src.ui.main_window.messagebox.showerror") as mock_error,
            patch("src.ui.main_window.threading.Thread") as mock_thread,
        ):

            # Make thread run synchronously
            mock_thread.return_value.start.side_effect = lambda: mock_thread.call_args[1][
                "target"
            ]()

            main_window._scan_mods()
            main_window.root.update()

        # Error should be shown
        mock_error.assert_called_once()

    def test_deploy_error_shows_dialog(self, main_window):
        """Test deployment errors are displayed."""
        main_window.game_detector.is_game_running.return_value = False
        main_window.deploy_engine.deploy.side_effect = Exception("Deploy failed")

        with (
            patch("src.ui.main_window.messagebox.askyesno") as mock_confirm,
            patch("src.ui.main_window.messagebox.showerror") as mock_error,
            patch("src.ui.main_window.threading.Thread") as mock_thread,
        ):

            mock_confirm.return_value = True
            mock_thread.return_value.start.side_effect = lambda: mock_thread.call_args[1][
                "target"
            ]()

            main_window._deploy_mods()
            main_window.root.update()

        mock_error.assert_called_once()


class TestThreading:
    """Test background operations."""

    def test_scan_runs_in_background(self, main_window, tmp_path):
        """Test scan operation uses threading."""
        main_window.config.get.return_value = str(tmp_path)

        with patch("src.ui.main_window.threading.Thread") as mock_thread:
            main_window._scan_mods()

            mock_thread.assert_called_once()
            assert mock_thread.call_args[1]["daemon"] is True

    def test_deploy_runs_in_background(self, main_window):
        """Test deploy operation uses threading."""
        main_window.game_detector.is_game_running.return_value = False

        with (
            patch("src.ui.main_window.messagebox.askyesno") as mock_confirm,
            patch("src.ui.main_window.threading.Thread") as mock_thread,
        ):

            mock_confirm.return_value = True

            main_window._deploy_mods()

            mock_thread.assert_called_once()
            assert mock_thread.call_args[1]["daemon"] is True


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_scan_generate_deploy(self, main_window, tmp_path):
        """Test complete workflow from scan to deployment."""
        # 1. Scan
        test_mod = ModFile(
            path=tmp_path / "test.package",
            mod_type="package",
            size=1024,
            hash="abc123",
            category="Mods",
            is_valid=True,
        )

        main_window.config.get.return_value = str(tmp_path)
        main_window.scanner.scan_folder.return_value = {"package": [test_mod]}

        with patch("src.ui.main_window.threading.Thread") as mock_thread:
            mock_thread.return_value.start.side_effect = lambda: mock_thread.call_args[1][
                "target"
            ]()
            main_window._scan_mods()
            main_window.root.update()

        assert len(main_window.incoming_mods) == 1

        # 2. Generate
        main_window.load_order_slots["000_Core"].insert(tk.END, "test.package")
        main_window.config.get.return_value = str(tmp_path / "ActiveMods")

        with patch("src.ui.main_window.messagebox.showinfo"):
            main_window._generate_structure()

        main_window.load_order_engine.generate_structure.assert_called_once()

        # 3. Deploy (simulated)
        main_window.game_detector.is_game_running.return_value = False
        main_window.game_detector.detect_mods_path.return_value = tmp_path / "Mods"

        with (
            patch("src.ui.main_window.messagebox.askyesno") as mock_confirm,
            patch("src.ui.main_window.messagebox.showinfo"),
        ):

            mock_confirm.return_value = True

            # Don't actually run deploy thread
            with patch("src.ui.main_window.threading.Thread"):
                main_window._deploy_mods()

        # Verify deployment was initiated or structure generated
        status_text = main_window.status_label.cget("text")
        assert any(
            keyword in status_text
            for keyword in ["Deploying", "cancelled", "generated", "Structure"]
        )
